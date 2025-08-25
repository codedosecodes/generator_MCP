# src/find_documents_main.py
# FIND_DOCUMENTS – Orquestador principal
# Autor: Gabriel Mauricio Cortés
# Descripción: Lee correos filtrados, extrae datos de facturas, guarda adjuntos en Google Drive
# y consolida todo en una hoja de cálculo. Al final envía un resumen por correo.

from __future__ import annotations
import os
import sys
import time
import traceback
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Módulos locales (asegúrate de que existan)
from config_manager import ConfigManager
from email_processor import EmailProcessor
from google_drive_client import GoogleDriveClient
from invoice_extractor import InvoiceExtractor

# Opcional: barra de progreso si tienes tqdm instalado
try:
    from tqdm import tqdm
except Exception:
    tqdm = None



def fmt_pct(numer: int, denom: int) -> str:
    if denom <= 0:
        return "0.0%"
    return f"{(100.0 * numer / denom):.1f}%"


def build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="find_documents_main",
        description="Procesa correos, extrae facturas y organiza en Google Drive/Sheets."
    )
    p.add_argument("--config", default="config/config.json", help="Ruta al config.json")
    p.add_argument("--start", help="YYYY-MM-DD (prioriza sobre el config)")
    p.add_argument("--end", help="YYYY-MM-DD (prioriza sobre el config)")
    p.add_argument("--keywords", nargs="*", help="Palabras clave para asunto/contenido")
    p.add_argument("--folder", help="Nombre de carpeta destino (bajo FIND_DOCUMENTS)")
    p.add_argument("--max-emails", type=int, help="Límite de correos a procesar")
    p.add_argument("--dry-run", action="store_true", help="No sube a Drive/Sheets (solo simula)")
    return p


def main() -> int:
    args = build_cli().parse_args()

    print("🔧 Cargando configuración...")
    cfg = ConfigManager(args.config)
    cfg.load()

    # Overwrites por CLI
    if args.start:
        cfg.data["search_parameters"]["start_date"] = args.start
    if args.end:
        cfg.data["search_parameters"]["end_date"] = args.end
    if args.keywords is not None:
        cfg.data["search_parameters"]["keywords"] = args.keywords
    if args.folder:
        cfg.data["search_parameters"]["folder_name"] = args.folder
    if args.max_emails:
        cfg.data.setdefault("processing_options", {})["max_emails"] = args.max_emails

    # Lectura de parámetros
    email_conf = cfg.data.get("email_credentials", {})
    search = cfg.data.get("search_parameters", {})
    gconf = cfg.data.get("google_services", {})
    opts = cfg.data.get("processing_options", {})
    notify = cfg.data.get("notification_settings", {})

    start_date = search.get("start_date")
    end_date = search.get("end_date")
    keywords = search.get("keywords", [])
    folder_name = search.get("folder_name", "Lote_Sin_Nombre")
    max_emails = int(opts.get("max_emails", 1000))
    enable_ai = bool(opts.get("enable_ai_extraction", True))
    send_completion_report = bool(opts.get("send_completion_report", True))
    drive_root = gconf.get("drive_folder_root", "FIND_DOCUMENTS")

    print(f"📅 Rango: {start_date} → {end_date}")
    print(f"🔎 Keywords: {keywords}")
    print(f"🗂  Carpeta raíz: {drive_root} / {folder_name}")
    if args.dry_run:
        print("🧪 MODO DRY-RUN: no se subirá nada a Drive/Sheets.")

    # 1) Email
    print("\n📫 Conectando al correo...")
    mail = EmailProcessor(
        server=email_conf.get("server", "imap.gmail.com"),
        port=int(email_conf.get("port", 993)),
        username=email_conf.get("username"),
        password=email_conf.get("password"),
    )
    mail.connect()

    # 2) Google Drive / Sheets
    print("☁️  Inicializando Google Drive/Sheets...")
    drive = GoogleDriveClient(
        credentials_path=gconf.get("credentials_path", "./config/credentials.json"),
        token_path=gconf.get("token_path", "./config/token.json"),
        dry_run=args.dry_run,
    )
    drive.init()

    # Asegurar estructura: /FIND_DOCUMENTS/<folder_name>/
    root_id = drive.ensure_folder(drive_root, parent_id=None)
    batch_folder_id = drive.ensure_folder(folder_name, parent_id=root_id)

    # Crear/abrir hoja de cálculo
    sheet_title = f"{folder_name}_Resumen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    sheet_id = drive.ensure_sheet(sheet_title, parent_folder_id=batch_folder_id)

    # Encabezados de la hoja
    headers = [
        "email_date", "from", "to", "subject", "has_attachments",
        "attachment_drive_path", "invoice_value", "invoice_concept",
        "invoice_vendor", "email_id", "processing_status", "notes"
    ]
    if not args.dry_run:
        drive.append_rows(sheet_id, [headers])

    # 3) Buscar correos
    print("\n🔍 Buscando correos con filtros...")
    email_ids = mail.search(
        start_date=start_date,
        end_date=end_date,
        keywords=keywords,
        limit=max_emails
    )
    total = len(email_ids)
    print(f"📬 Correos encontrados: {total}")

    processed = 0
    successes = 0
    failures = 0
    rows_buffer: List[List[Any]] = []

    extractor = InvoiceExtractor(enable_ai=enable_ai)

    iterator = email_ids
    if tqdm:
        iterator = tqdm(email_ids, desc="Procesando", unit="email")

    for eid in iterator:
        try:
            meta, body, attachments = mail.fetch_email(eid)
            # Meta esperada: date, from, to, subject
            date_obj: datetime = meta.get("date_dt") or datetime.utcnow()
            year = str(date_obj.year)
            month = f"{date_obj.month:02d}"

            # Crear árbol en Drive: /root/folder/year/month/email_id/
            year_id = drive.ensure_folder(year, parent_id=batch_folder_id)
            month_id = drive.ensure_folder(month, parent_id=year_id)
            email_node_id = drive.ensure_folder(str(eid), parent_id=month_id)

            has_atts = bool(attachments)
            atts_path = f"{drive_root}/{folder_name}/{year}/{month}/{eid}"

            # Subir adjuntos (si no es dry-run)
            if has_atts and not args.dry_run:
                for att in attachments:
                    # att: dict con filename, content_bytes, mimetype
                    drive.upload_bytes(
                        parent_id=email_node_id,
                        filename=att["filename"],
                        content=att["content"],
                        mimetype=att.get("mimetype", "application/octet-stream")
                    )

            # Extraer datos de factura (del cuerpo y/o adjuntos)
            inv = extractor.extract(
                email_subject=meta.get("subject", ""),
                email_body=body or "",
                attachments=attachments or []
            )
            invoice_value = inv.get("value")
            invoice_concept = inv.get("concept")
            invoice_vendor = inv.get("vendor")

            row = [
                meta.get("date_str") or date_obj.isoformat(),
                meta.get("from", ""),
                meta.get("to", ""),
                meta.get("subject", ""),
                "YES" if has_atts else "NO",
                atts_path if has_atts else "",
                invoice_value if invoice_value is not None else "",
                invoice_concept or "",
                invoice_vendor or "",
                str(eid),
                "OK",
                ""
            ]
            rows_buffer.append(row)
            successes += 1
        except Exception as ex:
            failures += 1
            err_row = [
                "", "", "", "", "", "",
                "", "", "", str(eid),
                "ERROR",
                str(ex)[:300]
            ]
            rows_buffer.append(err_row)
        finally:
            processed += 1

            # Escribir en lotes para reducir llamadas
            if len(rows_buffer) >= 50 and not args.dry_run:
                drive.append_rows(sheet_id, rows_buffer)
                rows_buffer.clear()

            # Progreso en consola
            if not tqdm:
                pct = fmt_pct(processed, total)
                ok = fmt_pct(successes, processed)
                print(f"➡️  Avance {processed}/{total} ({pct}) | Éxito: {ok}", end="\r")

    # Vaciar buffer final
    if rows_buffer and not args.dry_run:
        drive.append_rows(sheet_id, rows_buffer)

    # 4) Resumen
    success_rate = fmt_pct(successes, processed)
    print("\n\n✅ Proceso finalizado")
    print(f"   Total:       {total}")
    print(f"   Procesados:  {processed}")
    print(f"   Exitosos:    {successes}")
    print(f"   Fallidos:    {failures}")
    print(f"   Éxito:       {success_rate}")
    print(f"   Hoja:        {sheet_title} (id: {sheet_id})")

    # 5) Reporte por correo (opcional)
    if send_completion_report:
        try:
            summary_html = f"""
            <h2>FIND_DOCUMENTS – Resumen</h2>
            <ul>
              <li><b>Total:</b> {total}</li>
              <li><b>Procesados:</b> {processed}</li>
              <li><b>Exitosos:</b> {successes}</li>
              <li><b>Fallidos:</b> {failures}</li>
              <li><b>Tasa de éxito:</b> {success_rate}</li>
              <li><b>Carpeta:</b> {drive_root}/{folder_name}</li>
              <li><b>Sheet:</b> {sheet_title}</li>
            </ul>
            """
            mail.send_email_to_self(
                subject=f"[FIND_DOCUMENTS] Resumen {folder_name} – {success_rate}",
                html_body=summary_html
            )
            print("📨 Resumen enviado a tu correo.")
        except Exception:
            print("⚠️ No se pudo enviar el correo de resumen.")
            traceback.print_exc()

    # Cierre
    try:
        mail.close()
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⛔ Cancelado por el usuario.")
        sys.exit(130)
    except Exception as e:
        print("\n💥 Error fatal en ejecución:")
        traceback.print_exc()
        sys.exit(1)
