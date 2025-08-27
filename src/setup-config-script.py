#!/usr/bin/env python3
# 
# ===========================================================
# setup-config-script.py
# Part of the DOCUFIND Project (MCP-based Document Processor)
#
# Author: Gabriel Mauricio Cortés
# Created on: 24/12/2024
# License: MIT
# Description:
#   This module is part of an academic extracurricular project
#   that demonstrates the use of Model Context Protocol (MCP)
#   for intelligent document processing and cloud integration.
# ===========================================================

"""
Script de configuración inicial para DOCUFIND
Ayuda a configurar las credenciales de forma segura
"""

import json
import os
import sys
from pathlib import Path
import getpass
from typing import Dict, Any

def print_header():
    """Imprime el header del configurador"""
    print("=" * 60)
    print("🚀 DOCUFIND - Configuración Inicial")
    print("=" * 60)
    print()

def create_directory_structure():
    """Crea la estructura de directorios necesaria"""
    directories = [
        'config',
        'logs',
        'temp',
        'reports'
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Directorio creado/verificado: {directory}/")

def get_email_config() -> Dict[str, Any]:
    """Obtiene la configuración de email del usuario"""
    print("\n📧 CONFIGURACIÓN DE EMAIL")
    print("-" * 40)
    
    providers = {
        '1': ('Gmail', 'imap.gmail.com', 993),
        '2': ('Outlook/Hotmail', 'outlook.office365.com', 993),
        '3': ('Yahoo', 'imap.mail.yahoo.com', 993),
        '4': ('Otro', '', 993)
    }
    
    print("\nSelecciona tu proveedor de email:")
    for key, (name, _, _) in providers.items():
        print(f"  {key}. {name}")
    
    choice = input("\nOpción (1-4): ").strip()
    
    if choice not in providers:
        print("❌ Opción inválida")
        return get_email_config()
    
    provider_name, imap_server, imap_port = providers[choice]
    
    if choice == '4':
        imap_server = input("Servidor IMAP: ").strip()
        imap_port = int(input("Puerto IMAP (993): ").strip() or "993")
    
    email = input(f"\nTu email de {provider_name}: ").strip()
    
    print("\n⚠️  IMPORTANTE para Gmail:")
    print("  - Debes usar una 'Contraseña de aplicación'")
    print("  - Ve a: https://myaccount.google.com/apppasswords")
    print("  - Genera una contraseña específica para DOCUFIND")
    
    password = getpass.getpass("Contraseña o App Password: ")
    
    # Filtros de búsqueda
    print("\n🔍 Filtros de búsqueda (opcional)")
    subject_filters = input("Palabras clave en asunto (separadas por coma): ").strip()
    subject_filters = [f.strip() for f in subject_filters.split(',')] if subject_filters else ["factura", "invoice", "bill", "recibo"]
    
    senders = input("Remitentes específicos (emails separados por coma): ").strip()
    senders = [s.strip() for s in senders.split(',')] if senders else []
    
    return {
        "provider": provider_name.lower().replace('/', '_'),
        "username": email,
        "password": password,
        "imap_server": imap_server,
        "imap_port": imap_port,
        "use_ssl": True,
        "folder": "INBOX",
        "mark_as_read": False,
        "download_attachments": True,
        "max_results": 100,
        "senders": senders,
        "subject_filters": subject_filters,
        "has_attachments": True
    }

def get_google_drive_config() -> Dict[str, Any]:
    """Obtiene la configuración de Google Drive"""
    print("\n📁 CONFIGURACIÓN DE GOOGLE DRIVE")
    print("-" * 40)
    
    print("\n⚠️  Necesitas el archivo credentials.json de Google Cloud Console")
    print("  1. Ve a: https://console.cloud.google.com/")
    print("  2. Crea un proyecto o selecciona uno existente")
    print("  3. Habilita Google Drive API y Google Sheets API")
    print("  4. Crea credenciales OAuth 2.0")
    print("  5. Descarga el archivo credentials.json")
    
    credentials_path = input("\nRuta a credentials.json (Enter para 'config/credentials.json'): ").strip()
    credentials_path = credentials_path or "config/credentials.json"
    
    if not os.path.exists(credentials_path):
        print(f"⚠️  Archivo no encontrado: {credentials_path}")
        print("  Asegúrate de colocar el archivo antes de ejecutar el programa")
    
    root_folder = input("Carpeta raíz en Drive (Enter para 'DOCUFIND'): ").strip() or "DOCUFIND"
    
    return {
        "credentials_path": credentials_path,
        "token_path": "config/token.json",
        "scopes": [
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets"
        ],
        "root_folder": root_folder,
        "create_year_folders": True,
        "create_month_folders": True,
        "upload_reports": True
    }

def get_notification_config() -> Dict[str, Any]:
    """Obtiene la configuración de notificaciones"""
    print("\n📬 CONFIGURACIÓN DE NOTIFICACIONES")
    print("-" * 40)
    
    enable = input("\n¿Habilitar notificaciones por email? (s/n): ").strip().lower() == 's'
    
    if not enable:
        return {
            "enabled": False,
            "recipients": [],
            "send_on_success": False,
            "send_on_error": False,
            "include_summary": False
        }
    
    recipients = input("Emails para notificaciones (separados por coma): ").strip()
    recipients = [r.strip() for r in recipients.split(',')] if recipients else []
    
    return {
        "enabled": True,
        "recipients": recipients,
        "send_on_success": True,
        "send_on_error": True,
        "include_summary": True
    }

def save_config(config: Dict[str, Any]):
    """Guarda la configuración en config.json"""
    config_path = Path("config/config.json")
    
    # Hacer backup si existe
    if config_path.exists():
        backup_path = config_path.with_suffix('.json.backup')
        config_path.rename(backup_path)
        print(f"\n📋 Backup creado: {backup_path}")
    
    # Guardar nueva configuración
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuración guardada en: {config_path}")

def create_env_file():
    """Crea archivo .env de ejemplo"""
    env_content = """# DOCUFIND Environment Variables
# Copiar a .env y completar con tus datos

# Email Configuration
EMAIL_USERNAME=tu_email@gmail.com
EMAIL_PASSWORD=tu_app_password

# Google Drive
GOOGLE_CREDENTIALS_PATH=config/credentials.json

# Optional
DEBUG_MODE=False
MAX_WORKERS=4
"""
    
    env_path = Path(".env.template")
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print(f"📄 Plantilla .env creada: {env_path}")

def test_email_connection(config: Dict[str, Any]) -> bool:
    """Prueba la conexión de email"""
    print("\n🧪 Probando conexión de email...")
    
    try:
        import imaplib
        
        # Intentar conectar
        if config['email']['use_ssl']:
            mail = imaplib.IMAP4_SSL(
                config['email']['imap_server'],
                config['email']['imap_port']
            )
        else:
            mail = imaplib.IMAP4(
                config['email']['imap_server'],
                config['email']['imap_port']
            )
        
        # Intentar login
        mail.login(
            config['email']['username'],
            config['email']['password']
        )
        
        mail.logout()
        print("✅ Conexión de email exitosa!")
        return True
        
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\nPosibles soluciones:")
        print("  - Verifica tu usuario y contraseña")
        print("  - Para Gmail, usa una App Password")
        print("  - Verifica que IMAP esté habilitado en tu cuenta")
        return False

def main():
    """Función principal"""
    print_header()
    
    # Crear estructura de directorios
    print("📁 Creando estructura de directorios...")
    create_directory_structure()
    
    # Configuración base
    config = {
        "extraction": {
            "extract_amounts": True,
            "extract_dates": True,
            "extract_vendors": True,
            "extract_invoice_numbers": True,
            "extract_tax_info": True,
            "confidence_threshold": 0.6,
            "supported_formats": [".pdf", ".xml", ".txt", ".html"],
            "ocr_enabled": False
        },
        "processing": {
            "batch_size": 10,
            "parallel_processing": False,
            "retry_failed": True,
            "max_retries": 3,
            "timeout_seconds": 30
        },
        "reports": {
            "generate_report": True,
            "report_format": "json",
            "upload_to_drive": True,
            "include_statistics": True,
            "include_errors": True
        },
        "logging": {
            "level": "INFO",
            "file_logging": True,
            "console_logging": True,
            "log_directory": "logs",
            "max_log_size_mb": 10,
            "backup_count": 5
        },
        "filters": {
            "date_range_days": 30,
            "skip_processed": True,
            "min_attachment_size_kb": 1,
            "max_attachment_size_mb": 10,
            "allowed_extensions": [
                ".pdf", ".xml", ".xlsx", ".xls",
                ".doc", ".docx", ".txt", ".csv"
            ]
        },
        "categories": {
            "auto_categorize": True,
            "categories": {
                "utilities": ["electricidad", "gas", "agua", "luz"],
                "telecommunications": ["internet", "telefono", "movil"],
                "software": ["software", "licencia", "suscripcion"],
                "hosting": ["hosting", "dominio", "servidor"],
                "office": ["oficina", "papeleria", "suministros"],
                "transport": ["transporte", "envio", "mensajeria"],
                "professional": ["servicios", "consultoria", "honorarios"]
            }
        }
    }
    
    # Obtener configuraciones del usuario
    config['email'] = get_email_config()
    config['google_drive'] = get_google_drive_config()
    config['notifications'] = get_notification_config()
    
    # Guardar configuración
    print("\n💾 Guardando configuración...")
    save_config(config)
    
    # Crear archivo .env de ejemplo
    create_env_file()
    
    # Probar conexión
    if test_email_connection(config):
        print("\n✅ ¡Configuración completada exitosamente!")
        print("\nAhora puedes ejecutar:")
        print("  python src/find_documents_main.py")
    else:
        print("\n⚠️  Configuración guardada pero la conexión falló")
        print("Revisa tus credenciales en: config/config.json")
    
    print("\n" + "=" * 60)
    print("📚 Documentación:")
    print("  - README.md para instrucciones generales")
    print("  - config/config.json para ajustar configuración")
    print("  - logs/ para ver los registros de actividad")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuración cancelada por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)