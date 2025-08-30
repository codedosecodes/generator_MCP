#!/usr/bin/env python3
# 
# ===========================================================
# find_documents_main.py
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


import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import time
import re


# Añadir el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from src.email_processor import EmailProcessor
    from src.google_drive_client import GoogleDriveClient
    from src.invoice_extractor import InvoiceExtractor
    from src.config_manager import ConfigManager
except ImportError as e:
    print(f"Error importando módulos: {e}")
    print("Asegúrate de ejecutar desde el directorio raíz del proyecto")
    sys.exit(1)



logger = logging.getLogger(__name__)


# Configuración de logging
def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """Configura el sistema de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Crear formato de log
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Logger principal
    logger = logging.getLogger('DOCUFIND')
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Handler para archivo
    file_handler = logging.FileHandler(
        log_dir / f'docufind_{datetime.now().strftime("%Y%m%d")}.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    return logger

class DocuFindProcessor:
    """Clase principal para procesar documentos y facturas"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el procesador de documentos
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.logger = setup_logging()
        self.logger.info("🚀 Iniciando DOCUFIND - Procesador Inteligente de Correos y Facturas")
        
        # Cargar configuración
        try:
            self.config_manager = ConfigManager(config_path)
            self.config = self.config_manager.load_config()
            self.logger.info("✅ Configuración cargada exitosamente")
        except Exception as e:
            self.logger.error(f"❌ Error cargando configuración: {e}")
            raise
        
        # Inicializar componentes
        self._initialize_components()
        
        # 🔧 CORRECCIÓN: Agregar las estadísticas faltantes
        
           # 🔧 INICIALIZAR ESTADÍSTICAS COMPLETAS
        self.stats = {
            'tiempo_inicio': datetime.now(),
            'tiempo_fin': None,
            'emails_procesados': 0,
            'emails_encontrados': 0,
            'facturas_extraidas': 0,
            'archivos_subidos': 0,
            'errores': 0,
            # 🔧 AGREGAR ESTAS LÍNEAS:
            'emails_sin_adjuntos': 0,
            'emails_con_adjuntos': 0
        }
        
    
    def _initialize_components(self):
        """Inicializa los componentes del sistema"""
        try:
            # Procesador de emails
            self.email_processor = EmailProcessor(
                self.config.get('email', {})
            )
            self.logger.info("📧 Procesador de emails inicializado")
            
            # Cliente de Google Drive
            self.drive_client = GoogleDriveClient(
                credentials_path=self.config.get('google_drive', {}).get('credentials_path'),
                token_path=self.config.get('google_drive', {}).get('token_path')
            )
            self.logger.info("📁 Cliente de Google Drive inicializado")
            
            # Extractor de facturas
            self.invoice_extractor = InvoiceExtractor(
                self.config.get('extraction', {})
            )
            self.logger.info("🤖 Extractor de facturas inicializado")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando componentes: {e}")
            raise
         
    def process_emails(self, 
                    date_from: Optional[datetime] = None,
                    date_to: Optional[datetime] = None,
                    query: Optional[str] = None,
                    limit: Optional[int] = None) -> Dict[str, Any]:
        """
        Procesa correos electrónicos según los filtros especificados
        
        Args:
            date_from: Fecha inicial para buscar correos
            date_to: Fecha final para buscar correos
            query: Query adicional para filtrar correos
            limit: Límite de correos a procesar
            
        Returns:
            Diccionario con resultados del procesamiento
        """
        self.stats['tiempo_inicio'] = datetime.now()
        self.logger.info("=" * 60)
        self.logger.info("📬 INICIANDO PROCESAMIENTO DE CORREOS")
        self.logger.info("=" * 60)
        print('0-',date_from,'-',date_to)
        
        # CORRECCIÓN: Usar fechas del config si no se especifican
        if not date_from or not date_to:
            # Intentar obtener fechas del config
            filters_config = self.config.get('filters', {})
            
            # Buscar en filters primero
            config_start = filters_config.get('start_date')
            config_end = filters_config.get('end_date')
            
            # Si no están en filters, buscar en search_parameters (tu estructura)
            if not config_start or not config_end:
                search_params = self.config.get('search_parameters', {})
                config_start = search_params.get('start_date')
                config_end = search_params.get('end_date')
            
            # Parsear fechas del config si existen
            if config_start and not date_from:
                try:
                    date_from = datetime.strptime(config_start, '%Y-%m-%d')
                    self.logger.info(f"📅 Usando fecha inicial del config: {config_start}")
                except ValueError:
                    self.logger.warning(f"⚠️ Fecha inicial inválida en config: {config_start}")
                    date_from = datetime.now() - timedelta(days=60)
            
            if config_end and not date_to:
                try:
                    date_to = datetime.strptime(config_end, '%Y-%m-%d')
                    self.logger.info(f"📅 Usando fecha final del config: {config_end}")
                except ValueError:
                    self.logger.warning(f"⚠️ Fecha final inválida en config: {config_end}")
                    date_to = datetime.now()
        
        # Si aún no hay fechas, usar valores por defecto
        if not date_from:
            date_from = datetime.now() - timedelta(days=60)
            self.logger.info("📅 Usando fecha por defecto: últimos 60 días")
        
        if not date_to:
            date_to = datetime.now()
        
        self.logger.info(f"📅 Periodo: {date_from.strftime('%Y-%m-%d')} a {date_to.strftime('%Y-%m-%d')}")
    
        
        results = {
            'success': [],
            'failed': [],
            'summary': {}
        }
        
        try:
            # Paso 1: Buscar correos
            self.logger.info("\n📧 PASO 1: Buscando correos...")
            search_params = self._build_search_params(date_from, date_to, query)
            emails = self.email_processor.search_emails(**search_params)
            
            if not emails:
                self.logger.warning("⚠️ No se encontraron correos con los criterios especificados")
                return results
            
            self.logger.info(f"✅ Se encontraron {len(emails)} correos")
            
            # Aplicar límite si se especificó
            if limit and limit > 0:
                emails = emails[:limit]
                self.logger.info(f"📊 Procesando los primeros {limit} correos")
            
            # Paso 2: Procesar cada correo
            self.logger.info("\n🔄 PASO 2: Procesando correos...")
            for idx, email in enumerate(emails, 1):
                self._process_single_email(email, idx, len(emails), results)
            
            # Paso 3: Generar reporte
            self.logger.info("\n📊 PASO 3: Generando reporte...")
            self._generate_report(results)
            
            # Paso 4: Enviar notificación si está configurado
            if self.config.get('notifications', {}).get('enabled', False):
                self.logger.info("\n📬 PASO 4: Enviando notificación...")
                self._send_notification(results)
            
        except Exception as e:
            self.logger.error(f"❌ Error durante el procesamiento: {e}")
            self.stats['errores'] += 1
            raise
        finally:
            self.stats['tiempo_fin'] = datetime.now()
            self._print_summary()
        
        return results
    
    def _build_search_params(self, date_from: datetime, date_to: datetime, query: Optional[str]) -> Dict:
        """Construye los parámetros de búsqueda para correos"""
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        
        # Agregar query adicional si existe
        if query:
            params['query'] = query
        
        # Agregar filtros de configuración
        email_config = self.config.get('email', {})
        if 'senders' in email_config:
            params['senders'] = email_config['senders']
        if 'subject_filters' in email_config:
            params['subject_filters'] = email_config['subject_filters']
        if 'has_attachments' in email_config:
            params['has_attachments'] = email_config['has_attachments']
        
        return params
    
    
    def _process_single_email(self, email: Dict, idx: int, total: int, results: Dict):
        """
        🔧 MÉTODO CORREGIDO: Procesa un correo individual
        Maneja correctamente emails con y sin adjuntos
        """
        try:
            self.logger.info(f"\n[{idx}/{total}] Procesando: {email.get('subject', 'Sin asunto')}")
            self.logger.info(f"  De: {email.get('sender', 'Desconocido')}")
            self.logger.info(f"  Fecha: {email.get('date', 'Sin fecha')}")
            
            # Incrementar contador de emails procesados
            self.stats['emails_procesados'] += 1
            
            # IMPORTANTE: Guardar contexto del email actual
            self.current_email = email
            
            # Extraer adjuntos
            attachments = self.email_processor.get_attachments(email['id'])
            self.current_attachments = attachments
            
            if not attachments:
                self.logger.info("  ⚠️ No se encontraron adjuntos")
                
                # 🔧 PROCESAR EMAILS SIN ADJUNTOS
                self._process_email_without_attachments(email, results)
                
                # Incrementar contador defensivamente
                if 'emails_sin_adjuntos' not in self.stats:
                    self.stats['emails_sin_adjuntos'] = 0
                self.stats['emails_sin_adjuntos'] += 1
                
            else:
                self.logger.info(f"  📎 Encontrados {len(attachments)} adjuntos")
                
                # 🔧 PROCESAR EMAILS CON ADJUNTOS
                for attachment in attachments:
                    self._process_attachment(email, attachment, results)
                
                # Incrementar contador defensivamente
                if 'emails_con_adjuntos' not in self.stats:
                    self.stats['emails_con_adjuntos'] = 0
                self.stats['emails_con_adjuntos'] += 1
                
        except Exception as e:
            self.logger.error(f"    ❌ Error procesando email: {e}")
            # Debug adicional
            import traceback
            traceback.print_exc()
            self.stats['errores'] += 1
            
    def _process_email_without_attachments(self, email: Dict, results: Dict):
        """
        🔧 NUEVO MÉTODO: Procesa emails que no tienen adjuntos
        Extrae datos del contenido del email y los guarda en la hoja
        """
        try:
            self.logger.info("    📧 Procesando email sin adjuntos...")
            
            # 🔧 Obtener contenido completo del email
            email_body = self._get_complete_email_content(email)
            
            # 🔧 Crear contexto completo del email
            email_context = {
                'sender': email.get('sender', ''),
                'subject': email.get('subject', ''),
                'date': email.get('date', ''),
                'body': email_body,
                'recipient': email.get('to', ''),
                'filename': 'email_content'  # Identificador para emails sin adjuntos
            }
            
            # 🔧 Crear datos de factura usando solo el contenido del email
            invoice_data = self._create_invoice_data_for_email_only(email_context)
            
            self.logger.info(f"    ✅ Datos extraídos del email:")
            self.logger.info(f"       - Fecha: {invoice_data.get('invoice_date')}")
            self.logger.info(f"       - Proveedor: {invoice_data.get('vendor')}")
            self.logger.info(f"       - Concepto: {invoice_data.get('concept', '')[:50]}...")
            
            # 🔧 Actualizar hoja de cálculo directamente
            self._update_spreadsheet_for_email_only(email, invoice_data, results)
            
            self.logger.info("    ✅ Email sin adjuntos procesado correctamente")
            
        except Exception as e:
            self.logger.error(f"    ❌ Error procesando email sin adjuntos: {e}")
            import traceback
            traceback.print_exc()
            raise
     
     
    def _parse_email_date_safe(self, date_string: str) -> str:
        """
        🔧 NUEVO MÉTODO: Parsea fechas de email de forma segura
        Maneja diferentes formatos incluyendo zona horaria
        """
        if not date_string:
            return datetime.now().strftime('%Y-%m-%d')
        
        try:
            # Si ya está en formato YYYY-MM-DD, devolverlo
            if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
                return date_string
            
            # Si tiene espacios, tomar solo la primera parte
            if ' ' in date_string:
                date_part = date_string.split(' ')[0]
                if re.match(r'^\d{4}-\d{2}-\d{2}$', date_part):
                    return date_part
            
            # Intentar parsear con email.utils (maneja zona horaria)
            from email.utils import parsedate_to_datetime
            try:
                parsed_date = parsedate_to_datetime(date_string)
                return parsed_date.strftime('%Y-%m-%d')
            except (ValueError, TypeError):
                pass
            
            # 🔧 SOLUCIÓN AL ERROR: Limpiar zona horaria manualmente
            # Eliminar información de zona horaria problemática
            clean_date = date_string.strip()
            
            # Patrones comunes de zona horaria a eliminar
            timezone_patterns = [
                r'\s*\+\d{4}$',           # +0300
                r'\s*-\d{4}$',            # -0500  
                r'\s*\([^)]+\)$',         # (EST)
                r'\s*[A-Z]{3,4}$',        # GMT, EST, PST, etc.
                r'\s*\d{2}:\d{2}:\d{2}$'  # 03:00:02 (el que causa el error)
            ]
            
            for pattern in timezone_patterns:
                clean_date = re.sub(pattern, '', clean_date)
            
            # Intentar parsear la fecha limpia con diferentes formatos
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',  
                '%Y-%m-%d',
                '%d/%m/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M',
                '%d/%m/%Y',
                '%m/%d/%Y %H:%M:%S', 
                '%m/%d/%Y %H:%M',
                '%m/%d/%Y',
                '%d-%m-%Y %H:%M:%S',
                '%d-%m-%Y %H:%M',
                '%d-%m-%Y',
                '%Y/%m/%d %H:%M:%S',
                '%Y/%m/%d %H:%M',
                '%Y/%m/%d'
            ]
            
            for fmt in date_formats:
                try:
                    parsed = datetime.strptime(clean_date.strip(), fmt)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            # Si nada funciona, usar fecha actual
            self.logger.warning(f"⚠️ No se pudo parsear fecha '{date_string}', usando fecha actual")
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            self.logger.error(f"❌ Error parseando fecha '{date_string}': {e}")
            return datetime.now().strftime('%Y-%m-%d')
    
           
    def _create_invoice_data_for_email_only(self, email_context: Dict) -> Dict[str, Any]:
        """
        🔧 MÉTODO CORREGIDO: Crea datos de factura para emails SIN adjuntos
        """
        try:
            # 🔧 CORRECCIÓN: Usar el nuevo método de parseo de fechas
            email_date = email_context.get('date', '')
            invoice_date = self._parse_email_date_safe(email_date)
            
            # 🔧 CONCEPTO: Usar contenido del email o asunto
            email_body = email_context.get('body', '')
            subject = email_context.get('subject', '')
            
            if email_body and len(email_body.strip()) > 10:
                # Limpiar el cuerpo del email
                clean_body = self._clean_email_body(email_body)
                if len(clean_body) > 300:
                    concept = clean_body[:297] + '...'
                else:
                    concept = clean_body if clean_body else subject
            else:
                # Si no hay cuerpo, usar el asunto
                concept = subject[:300] if subject else 'Email sin contenido'
            
            # 🔧 PROVEEDOR: Usar el método de extracción limpia
            sender = email_context.get('sender', '')
            vendor = self._extract_clean_vendor(sender, subject)
            
            # 🔧 Crear datos de factura completos
            invoice_data = {
                'invoice_date': invoice_date,
                'concept': concept,
                'vendor': vendor,
                'invoice_number': f"EMAIL-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'amount': '',  # No hay monto en emails sin adjuntos normalmente
                'currency': 'N/A',
                'confidence': 0.6,  # Confianza media para emails sin adjuntos
                'extraction_method': 'email_content_only',
                'date': invoice_date,  # Alias por compatibilidad
                'total': '',  # Alias por compatibilidad
                'subtotal': '',
                'tax_amount': '',
                'payment_method': '',
                'category': 'Email sin adjuntos'
            }
            
            return invoice_data
            
        except Exception as e:
            self.logger.error(f"❌ Error creando datos para email sin adjuntos: {e}")  # ← 🔧 self.logger
            # Datos de fallback
            return {
                'invoice_date': datetime.now().strftime('%Y-%m-%d'),
                'concept': 'Error procesando contenido del email',
                'vendor': 'Error en extracción',
                'invoice_number': f"ERR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                'amount': '',
                'currency': 'N/A',
                'confidence': 0.0,
                'extraction_method': 'error',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'total': '',
                'subtotal': '',
                'tax_amount': '',
                'payment_method': '',
                'category': 'Error'
            }
            
                
    def _extract_clean_vendor(self, sender: str, subject: str = '') -> str:
        """
        🔧 MÉTODO CORREGIDO: Extrae el proveedor limpiando correctamente la codificación
        """
        if not sender:
            return 'Remitente desconocido'
        
        try:
            import re
            
            # 🔧 PASO 1: Limpiar caracteres no printables agresivamente
            clean_sender = re.sub(r'[^\w\s\-.,@<>áéíóúñü]', '', sender, flags=re.IGNORECASE)
            
            # 🔧 PASO 2: Extraer email de forma más robusta
            email_pattern = r'[\w\.-]+@([\w\.-]+\.\w+)'
            email_match = re.search(email_pattern, clean_sender)
            
            if email_match:
                domain = email_match.group(1).lower()
                
                # 🔧 PASO 3: Extraer nombre del remitente
                name_pattern = r'^([^<]+?)\s*<'
                name_match = re.match(name_pattern, clean_sender.strip())
                
                if name_match:
                    sender_name = name_match.group(1).strip().strip('"\'')
                    
                    # Limpiar el nombre más agresivamente
                    sender_name = re.sub(r'[^\w\s\-áéíóúñü]', ' ', sender_name, flags=re.IGNORECASE)
                    sender_name = ' '.join(sender_name.split())  # Normalizar espacios
                    
                    if sender_name and len(sender_name) > 2 and sender_name.lower() != domain:
                        # Limitar longitud del nombre
                        if len(sender_name) > 30:
                            sender_name = sender_name[:27] + '...'
                        return f"{domain} - {sender_name}"
                
                # Si no hay nombre limpio, usar dominio + parte del asunto
                if subject:
                    # Tomar las primeras palabras del asunto (máximo 3)
                    subject_words = subject.split()[:3]
                    clean_subject = ' '.join(subject_words)
                    
                    # Limpiar el asunto
                    clean_subject = re.sub(r'[^\w\s\-áéíóúñü]', ' ', clean_subject, flags=re.IGNORECASE)
                    clean_subject = ' '.join(clean_subject.split())
                    
                    if clean_subject and len(clean_subject) > 3:
                        if len(clean_subject) > 30:
                            clean_subject = clean_subject[:27] + '...'
                        return f"{domain} - {clean_subject}"
                
                # Solo el dominio
                return domain
            
            # 🔧 FALLBACK: Limpiar el sender completo
            clean_sender = re.sub(r'[^\w\s\-.,áéíóúñü]', ' ', clean_sender, flags=re.IGNORECASE)
            clean_sender = ' '.join(clean_sender.split())
            
            if clean_sender and len(clean_sender) > 3:
                return clean_sender[:50]
            
            return 'Remitente no identificado'
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error extrayendo proveedor de '{sender}': {e}")  # ← 🔧 self.logger
            return 'Error en proveedor'

    
    
    def _process_attachment(self, email: Dict, attachment: Dict, results: Dict):
        """Procesa un adjunto individual con contexto mejorado"""
        try:
            filename = attachment.get('filename', 'archivo_sin_nombre')
            self.logger.info(f"    📄 Procesando: {filename}")
            
            # Verificar si es una factura
            if self._is_invoice(filename):
                # 🔧 CORRECCIÓN 3: Obtener TODO el contenido del email
                email_body = self._get_complete_email_content(email)
                
                # NUEVO: Pasar contexto completo del email al extractor
                email_context = {
                    'sender': email.get('sender', ''),
                    'subject': email.get('subject', ''),
                    'date': email.get('date', ''),
                    'body': email_body,  # 🔧 CONTENIDO COMPLETO DEL EMAIL
                    'filename': filename
                }
                
                # Extraer datos de la factura CON CONTEXTO COMPLETO
                invoice_data = self._extract_invoice_with_context(
                    attachment['content'], 
                    email_context
                )
                
                if invoice_data:
                    self.logger.info(f"      ✅ Datos extraídos: {invoice_data.get('invoice_number', 'N/A')}")
                    self.stats['facturas_extraidas'] += 1
                    
                    # Organizar en Google Drive
                    self._organize_in_drive(email, attachment, invoice_data)
                else:
                    self.logger.warning(f"      ⚠️ No se pudieron extraer datos")
                    # Aún así procesar con datos mínimos
                    minimal_data = self._create_minimal_invoice_data(email, attachment)
                    self._organize_in_drive(email, attachment, minimal_data)
            else:
                # Subir archivo tal cual
                self._upload_to_drive(email, attachment)
                
        except Exception as e:
            self.logger.error(f"    ❌ Error procesando adjunto: {e}")
            self.stats['errores'] += 1
    
    def process_attachment_to_drive(self, attachment_data, email_date, email_id):
        """
        Procesa un adjunto y lo sube a Google Drive
        
        Args:
            attachment_data: Datos del adjunto
            email_date: Fecha del email
            email_id: ID del email
        
        Returns:
            dict: Información del procesamiento
        """
        try:
            filename = attachment_data.get('filename', 'attachment')
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Filtrar archivos de imagen que son logos o elementos de diseño
            skip_patterns = [
                'email_body', 'logo', 'signature', 'header', 'footer',
                'banner', 'icon', 'badge', 'folio_email_body'
            ]
            
            if any(pattern in filename.lower() for pattern in skip_patterns):
                # Para archivos de diseño de email, procesarlos diferente
                if 'folio_email_body' in filename.lower():
                    self.logger.info(f"⚠️ Omitiendo imagen de diseño de email: {filename}")
                    return {
                        'status': 'skipped',
                        'reason': 'email_design_element',
                        'filename': filename
                    }
            
            # Crear carpeta temporal si no existe
            temp_dir = "temp"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # Guardar archivo temporalmente
            temp_path = os.path.join(temp_dir, f"{email_id}_{filename}")
            
            # Escribir contenido del adjunto
            with open(temp_path, 'wb') as f:
                f.write(attachment_data['content'])
            
            # Determinar carpeta de destino según el tipo de archivo
            if file_extension in ['.pdf', '.doc', '.docx']:
                folder_type = 'Facturas'
            elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
                folder_type = 'Imagenes'
            elif file_extension in ['.xls', '.xlsx', '.csv']:
                folder_type = 'Hojas_Calculo'
            else:
                folder_type = 'Otros'
            
            # Crear estructura de carpetas
            year = email_date.year
            month = email_date.strftime('%m_%B')
            day = email_date.strftime('%d')
            
            # Crear carpetas en Drive
            folder_path = f"DOCUFIND/{year}/{month}/{day}/{folder_type}"
            folder_id = self.create_folder_structure(folder_path)
            
            # Subir archivo a Drive
            uploaded_file = self.upload_file(temp_path, folder_id, email_date)
            
            # Limpiar archivo temporal
            try:
                os.remove(temp_path)
            except:
                pass
            
            if uploaded_file:
                return {
                    'status': 'success',
                    'file_id': uploaded_file['id'],
                    'file_name': uploaded_file['name'],
                    'folder_path': folder_path,
                    'web_link': uploaded_file.get('webViewLink')
                }
            else:
                return {
                    'status': 'error',
                    'reason': 'upload_failed',
                    'filename': filename
                }
                
        except Exception as e:
            self.logger.error(f"Error procesando adjunto: {str(e)}")
            return {
                'status': 'error',
                'reason': str(e),
                'filename': filename
            }
    
        
    def _extract_invoice_with_context(self, content: bytes, email_context: Dict) -> Dict[str, Any]:
        """
        Extrae datos de factura usando el contexto del email
        CORREGIDO: SIEMPRE usa la fecha del correo
        """
        # Primero intentar extracción normal
        invoice_data = self.invoice_extractor.extract(content)
        
        if not invoice_data:
            invoice_data = {}
        
        # MEJORA 1: CONCEPTO - Usar el cuerpo del email
        if not invoice_data.get('concept') or invoice_data.get('concept') == 'Documento adjunto':
            # Obtener el cuerpo del email
            email_body = email_context.get('body', '')
            
            if email_body:
                # Limpiar el cuerpo del email
                clean_body = self._clean_email_body(email_body)
                
                # Tomar los primeros 500 caracteres del cuerpo limpio
                if len(clean_body) > 500:
                    invoice_data['concept'] = clean_body[:497] + '...'
                else:
                    invoice_data['concept'] = clean_body if clean_body else f"Adjunto: {email_context.get('filename', 'documento')}"
            else:
                # Si no hay cuerpo, usar el asunto
                subject = email_context.get('subject', '')
                invoice_data['concept'] = subject[:500] if subject else f"Adjunto: {email_context.get('filename', 'documento')}"
        
        # 🔧 CORRECCIÓN 1: FECHA FACTURA - SIEMPRE usar fecha del email
        email_date = email_context.get('date', '')
        if email_date:
            # Tomar solo la parte de la fecha (sin hora)
            if ' ' in email_date:
                email_date = email_date.split(' ')[0]
            invoice_data['invoice_date'] = email_date
        else:
            invoice_data['invoice_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # 🔧 CORRECCIÓN 2: PROVEEDOR - Usar dominio del remitente + resumen
        if not invoice_data.get('vendor') or invoice_data.get('vendor') == 'No identificado':
            sender = email_context.get('sender', '')
            
            if sender:
                # Extraer dominio del email
                domain = self._extract_domain_from_sender(sender)
                
                # Intentar obtener nombre del remitente
                sender_name = self._extract_sender_name(sender)
                
                # Crear resumen del proveedor
                if domain:
                    # Formato: "dominio.com - Nombre o Asunto"
                    if sender_name and sender_name != domain:
                        invoice_data['vendor'] = f"{domain} - {sender_name}"
                    else:
                        # Usar parte del asunto si no hay nombre
                        subject = email_context.get('subject', '')
                        if subject:
                            # Tomar las primeras palabras del asunto
                            subject_summary = ' '.join(subject.split()[:5])
                            invoice_data['vendor'] = f"{domain} - {subject_summary}"
                        else:
                            invoice_data['vendor'] = domain
                else:
                    invoice_data['vendor'] = sender[:100] if sender else 'Remitente desconocido'
        
        # Limpiar todos los valores de caracteres especiales
        for key, value in invoice_data.items():
            if isinstance(value, str):
                invoice_data[key] = self._clean_special_chars(value)
        
        return invoice_data
        
    def _clean_email_body(self, body: str) -> str:
        """
        Limpia el cuerpo del email de HTML, caracteres especiales y formato
        """
        if not body:
            return ""
        
        # Eliminar tags HTML
        import re
        clean = re.sub(r'<[^>]+>', '', body)
        
        # Eliminar URLs
        clean = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', clean)
        
        # Eliminar caracteres XML/RDF
        clean = re.sub(r'xmlns:[^=]+=\\"[^\\"]+\\"', '', clean)
        clean = re.sub(r'rdf:[^=]+=\\"[^\\"]+\\"', '', clean)
        clean = re.sub(r'</?rdf:[^>]+>', '', clean)
        clean = re.sub(r'</?pdf:[^>]+>', '', clean)
        
        # Eliminar caracteres no imprimibles
        clean = ''.join(char for char in clean if char.isprintable() or char in '\\n\\r\\t ')
        
        # Normalizar espacios en blanco
        clean = re.sub(r'\\s+', ' ', clean)
        
        # Eliminar líneas vacías múltiples
        clean = re.sub(r'\\n\\s*\\n', '\\n', clean)
        
        # Limitar longitud y limpiar
        clean = clean.strip()
        
        return clean

    def _has_special_chars(self, text: str) -> bool:
        """
        Verifica si el texto tiene caracteres especiales problemáticos
        """
        if not text:
            return False
        
        # Buscar patrones problemáticos
        problematic_patterns = [
            'rdf:', 'xmlns:', 'pdf:', 'http://', '<', '>', '<?xml'
        ]
        
        text_lower = text.lower()
        return any(pattern in text_lower for pattern in problematic_patterns)

    def _extract_domain_from_sender(self, sender: str) -> str:
        """
        Extrae el dominio del email del remitente
        """
        import re
        
        # Buscar email en el sender
        email_pattern = r'[a-zA-Z0-9._%+-]+@([a-zA-Z0-9.-]+\\.[a-zA-Z]{2,})'
        match = re.search(email_pattern, sender)
        
        if match:
            domain = match.group(1)
            # Limpiar el dominio
            domain = domain.lower()
            # Remover subdominios comunes
            for prefix in ['mail.', 'email.', 'smtp.', 'imap.', 'pop.', 'no-reply.', 'noreply.']:
                if domain.startswith(prefix):
                    domain = domain[len(prefix):]
            return domain
        
        return ""

    def _extract_sender_name(self, sender: str) -> str:
        """
        Extrae el nombre del remitente
        """
        import re
        
        # Formato: "Nombre" <email@domain.com>
        match = re.match(r'^"?([^"<]+)"?\\s*<?[^>]*>?', sender)
        if match:
            name = match.group(1).strip()
            # Limpiar el nombre
            name = name.replace('"', '').strip()
            if name and not '@' in name:
                return name[:50]  # Limitar longitud
        
        # Si no hay nombre, intentar obtener la parte antes del @
        if '@' in sender:
            local_part = sender.split('@')[0]
            # Limpiar y capitalizar
            local_part = local_part.replace('.', ' ').replace('_', ' ').replace('-', ' ')
            local_part = ' '.join(word.capitalize() for word in local_part.split())
            return local_part[:50]
        
        return ""

    def _clean_special_chars(self, text: str) -> str:
        """
        🔧 MÉTODO MEJORADO: Limpia caracteres especiales y ilegibles de forma agresiva
        """
        if not text:
            return text
        
        try:
            # 🔧 PASO 1: Eliminar caracteres no ASCII problemáticos
            # Solo mantener caracteres alfanuméricos, espacios y puntuación básica
            import re
            
            # Permitir solo caracteres seguros
            clean_text = re.sub(r'[^\w\s\-.,@áéíóúñü]', ' ', text, flags=re.IGNORECASE)
            
            # 🔧 PASO 2: Normalizar espacios
            clean_text = ' '.join(clean_text.split())
            
            # 🔧 PASO 3: Limitar longitud
            clean_text = clean_text[:500]
            
            # 🔧 PASO 4: Verificar que el resultado sea legible
            if len(clean_text.strip()) < 2:
                return 'Texto no legible'
            
            return clean_text.strip()
            
        except Exception as e:
            self.logger.warning(f"      ⚠️ Error en limpieza de texto: {e}")
            return 'Error de codificación'




    def _update_spreadsheet_for_email_only(self, email: Dict, invoice_data: Dict, results: Dict):
        """
        🔧 NUEVO MÉTODO: Actualiza la hoja de cálculo para emails SIN adjuntos
        """
        try:
            spreadsheet_id = results.get('spreadsheet_id')
            if not spreadsheet_id:
                self.logger.warning("      ⚠️ No hay ID de hoja de cálculo")
                return
            
            def clean_value(value, default=''):
                """Limpia valores para la hoja de cálculo"""
                if value is None:
                    return default
                # Aplicar limpieza de caracteres especiales
                clean_val = self._clean_special_chars(str(value))
                return clean_val[:500]  # Limitar longitud
            
            # Construir fila para la hoja de cálculo
            row_data = [
                # 1. ID del Email
                str(email.get('id', '')),
                
                # 2. Fecha Procesamiento
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # 3. 🔧 CORRECCIÓN: Fecha Email
                clean_value(email.get('date', '').split(' ')[0] if email.get('date') else ''),
                
                # 4. 🔧 CORRECCIÓN: Remitente limpio
                clean_value(email.get('sender', '')),
                
                # 5. Destinatario
                clean_value(email.get('recipient', email.get('to', ''))),
                
                # 6. Asunto
                clean_value(email.get('subject', '')),
                
                # 7. Tiene Adjuntos
                'No',
                
                # 8. Cantidad Adjuntos
                '0',
                
                # 9. Nombres Adjuntos
                '',
                
                # 10. Rutas Adjuntos
                '',
                
                # 11. 🔧 CORRECCIÓN: Fecha Factura (fecha del email)
                clean_value(invoice_data.get('invoice_date', '')),
                
                # 12. 🔧 CORRECCIÓN: Proveedor limpio
                clean_value(invoice_data.get('vendor', 'No identificado')),
                
                # 13. Número Factura
                clean_value(invoice_data.get('invoice_number', '')),
                
                # 14. 🔧 CORRECCIÓN: Concepto del email
                clean_value(invoice_data.get('concept', 'Sin contenido')),
                
                # 15. Monto
                '',
                
                # 16. Moneda
                'N/A',
                
                # 17. Impuestos
                '',
                
                # 18. Método Extracción
                clean_value(invoice_data.get('extraction_method', 'email_content_only')),
                
                # 19. Confianza
                f"{invoice_data.get('confidence', 0):.1%}",
                
                # 20. Longitud Contenido
                str(len(email.get('body', ''))),
                
                # 21. Estado
                'Email sin adjuntos procesado'
            ]
            
            # Verificar que tenemos el número correcto de campos
            if len(row_data) != 21:
                self.logger.warning(f"      ⚠️ Número de campos incorrecto: {len(row_data)}, esperado: 21")
                # Ajustar a 21 campos
                while len(row_data) < 21:
                    row_data.append('')
                row_data = row_data[:21]
            
            # Agregar fila a la hoja
            if self.drive_client.append_to_spreadsheet(spreadsheet_id, row_data):
                self.logger.info(f"        ✅ Email sin adjuntos agregado a hoja de cálculo")
            else:
                self.logger.error(f"        ❌ Error agregando email sin adjuntos a hoja")
                
        except Exception as e:
            self.logger.error(f"        ⚠️ Error actualizando hoja para email sin adjuntos: {e}")
            import traceback
            traceback.print_exc()
    
    
    
    def _create_minimal_invoice_data(self, email: Dict, attachment: Dict) -> Dict[str, Any]:
        """
        Crea datos mínimos de factura cuando no se puede extraer nada
        """
        sender = email.get('sender', '')
        domain = self._extract_domain_from_sender(sender) if sender else 'desconocido'
        
        # Usar el cuerpo del email para el concepto
        body = email.get('body', '')
        clean_body = self._clean_email_body(body) if body else email.get('subject', 'Documento adjunto')
        
        return {
            'invoice_number': f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'vendor': domain,
            'concept': clean_body[:500],
            'invoice_date': email.get('date', '').split(' ')[0] if email.get('date') else datetime.now().strftime('%Y-%m-%d'),
            'amount': '',
            'currency': 'MXN',
            'confidence': 0.1,
            'category': 'documento'
        }
    
    
    
    
    def _is_invoice(self, filename: str) -> bool:
        """Determina si un archivo es una factura"""
        invoice_keywords = ['factura', 'invoice', 'bill', 'receipt', 'recibo']
        invoice_extensions = ['.pdf', '.xml', '.xlsx', '.xls']
        
        filename_lower = filename.lower()
        
        # Verificar palabras clave
        has_keyword = any(keyword in filename_lower for keyword in invoice_keywords)
        
        # Verificar extensión
        has_valid_extension = any(filename_lower.endswith(ext) for ext in invoice_extensions)
        
        return has_keyword or has_valid_extension
    

 
    def _organize_in_drive(self, email: Dict, attachment: Dict, invoice_data: Dict):
        """
        Organiza una factura en Google Drive con estructura Año/Mes/Día
        """
        try:
            # Corregir el parseo de fecha - manejar fecha con hora
            date_str = email.get('date', '')
            
            # Si la fecha tiene formato "YYYY-MM-DD HH:MM:SS", tomar solo la parte de fecha
            if ' ' in date_str:
                date_str = date_str.split(' ')[0]  # Tomar solo "YYYY-MM-DD"
            
            # Ahora parsear la fecha
            try:
                from datetime import datetime
                date = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                # Si falla, usar fecha actual
                date = datetime.now()
                self.logger.warning(f"⚠️ No se pudo parsear fecha: {email.get('date', '')}, usando fecha actual")
                
                
                
            # NUEVA ESTRUCTURA: Año/Mes/Día
            # Formato: DOCUFIND/2024/08_Agosto/26
            month_name = date.strftime('%m_%B')  # 08_August
            day_str = date.strftime('%d')        # 26
            
            # Crear estructura de carpetas
            folder_path = f"DOCUFIND/{date.year}/{month_name}/{day_str}/Facturas"
            
            # Crear carpetas si no existen
            folder_id = self.drive_client.create_folder_path(folder_path)
            
            if not folder_id:
                self.logger.error(f"❌ No se pudo crear carpeta: {folder_path}")
                return
            
            # NUEVO: Agregar ID del email al nombre del archivo
            email_id = email.get('id', 'no_id')
            original_filename = attachment.get('filename', 'archivo_sin_nombre')
            
            # Generar nuevo nombre con ID del email
            # Formato: [EmailID]_[NombreArchivo]
            new_filename = f"[{email_id}]_{original_filename}"
            
            # Si hay datos de factura, agregar número de factura
            if invoice_data and invoice_data.get('invoice_number'):
                # Limpiar número de factura
                inv_num = str(invoice_data['invoice_number']).replace('/', '-').replace('\\\\', '-')
                name_parts = new_filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_filename = f"{name_parts[0]}_INV-{inv_num}.{name_parts[1]}"
                else:
                    new_filename = f"{new_filename}_INV-{inv_num}"
            
            self.logger.info(f"      📁 Carpeta: {folder_path}")
            self.logger.info(f"      📄 Archivo: {new_filename}")
            
            # Subir archivo con el nuevo nombre
            file_id = self.drive_client.upload_file(
                attachment['content'],
                new_filename,
                folder_id,
                None  # No enviar metadata para evitar error de 124 bytes
            )
            
            if file_id:
                self.logger.info(f"      ✅ Subido a Drive: {new_filename}")
                self.stats['archivos_subidos'] += 1
                
                # CORRECCIÓN: Usar _update_spreadsheet (no _update_spreadsheet_with_id)
                # Guardar el email actual en contexto antes de actualizar
                self.current_email = email
                self.current_attachments = [attachment]
                
                # Llamar al método correcto
                self._update_spreadsheet(invoice_data, file_id)
            else:
                self.logger.error(f"      ❌ Error subiendo archivo")
                
        except Exception as e:
            self.logger.error(f"      ❌ Error organizando en Drive: {e}")
            import traceback
            traceback.print_exc()
            raise
            
     
           
    def _upload_to_drive(self, email: Dict, attachment: Dict):
        """Sube un archivo no-factura a Google Drive"""
        try:
            # Crear estructura básica de carpetas
            date = datetime.strptime(email.get('date', ''), '%Y-%m-%d')
            folder_path = f"DOCUFIND/{date.year}/{date.strftime('%m-%B')}/Otros"
            
            # Crear carpetas si no existen
            folder_id = self.drive_client.create_folder_path(folder_path)
            
            # Subir archivo
            file_id = self.drive_client.upload_file(
                attachment['content'],
                attachment['filename'],
                folder_id
            )
            
            if file_id:
                self.logger.info(f"      ✅ Subido a Drive: {attachment['filename']}")
                self.stats['archivos_subidos'] += 1
            
        except Exception as e:
            self.logger.error(f"      ❌ Error subiendo a Drive: {e}")
            raise
    
    def _generate_filename(self, invoice_data: Dict, original_filename: str) -> str:
        """Genera un nombre de archivo descriptivo para la factura"""
        parts = []
        
        # Fecha
        if invoice_data.get('date'):
            parts.append(invoice_data['date'].replace('/', '-'))
        
        # Proveedor
        if invoice_data.get('vendor'):
            parts.append(invoice_data['vendor'].replace(' ', '_')[:20])
        
        # Número de factura
        if invoice_data.get('invoice_number'):
            parts.append(f"F{invoice_data['invoice_number']}")
        
        # Total
        if invoice_data.get('total'):
            parts.append(f"${invoice_data['total']}")
        
        # Si no hay datos, usar nombre original
        if not parts:
            return original_filename
        
        # Obtener extensión
        extension = os.path.splitext(original_filename)[1]
        
        return f"{'_'.join(parts)}{extension}"
    
    
    
    



    def _update_spreadsheet(self, invoice_data: Dict, file_id: str):
        """Actualiza la hoja de cálculo con los datos de la factura"""
        try:
            # Buscar o crear hoja de cálculo
            drive_config = self.config.get('google_drive', {})
            google_services = self.config.get('google_services', {})
            
            # Obtener nombre del spreadsheet desde config
            spreadsheet_name = (
                drive_config.get('spreadsheet_name') or 
                google_services.get('spreadsheet_name')
            )
            
            # Si no hay nombre configurado, usar defecto
            if not spreadsheet_name:
                prefix = google_services.get('spreadsheet_prefix', 'DOCUFIND_Facturas')
                spreadsheet_name = f"{prefix}_{datetime.now().year}"
            
            self.logger.info(f"        📊 Usando hoja: {spreadsheet_name}")
            

            # Primero crear carpeta DOCUFIND si no existe
            root_folder_id = self.drive_client.create_folder("DOCUFIND")
            if not root_folder_id:
                self.logger.error("❌ No se pudo crear carpeta DOCUFIND")
                return
            
            # Crear o obtener spreadsheet
            spreadsheet_id = self.drive_client.get_or_create_spreadsheet(
                spreadsheet_name,
                root_folder_id
            )
            
            if not spreadsheet_id:
                self.logger.error("❌ No se pudo crear/obtener hoja de cálculo")
                return
            
            # Obtener información del email si está disponible
            email_info = getattr(self, 'current_email', {})
            attachments_info = getattr(self, 'current_attachments', [])
            
            # IMPORTANTE: Obtener ID del email
            email_id = email_info.get('id', 'NO_ID')
            
            # Preparar lista de nombres de adjuntos
            attachment_names = []
            if attachments_info:
                for att in attachments_info:
                    if isinstance(att, dict):
                        attachment_names.append(att.get('filename', ''))
                    else:
                        attachment_names.append(str(att))
                        
            # Limpiar datos de factura de caracteres extraños
            def clean_value(value):
                if value is None:
                    return ''
                if isinstance(value, str):
                    # Eliminar caracteres no imprimibles
                    value = ''.join(c for c in value if c.isprintable() or c == ' ')
                    # Limpiar espacios múltiples
                    value = ' '.join(value.split())
                    # Limitar longitud
                    if len(value) > 200:
                        value = value[:197] + '...'
                    return value
                return str(value)
            
            # IMPORTANTE: Preparar exactamente 21 campos en orden
            row_data = [
                # 1. ID del Email
                str(email_id),
                
                # 2. Fecha Procesamiento
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # 3. Fecha Email
                email_info.get('date', '').split(' ')[0] if email_info.get('date') else '',
                
                # 4. Remitente
                clean_value(email_info.get('sender', '')),
                
                # 5. Asunto
                clean_value(email_info.get('subject', '')),
                
                # 6. Tiene Adjuntos
                'Sí' if attachments_info else 'No',
                
                # 7. Cantidad Adjuntos
                str(len(attachments_info)) if attachments_info else '0',
                
                # 8. Nombres Adjuntos
                clean_value(', '.join(attachment_names)[:500]) if attachment_names else '',
                
                # 9. Fecha Factura
                clean_value(invoice_data.get('invoice_date', invoice_data.get('date', ''))),
                
                # 10. Proveedor
                clean_value(invoice_data.get('vendor', 'No identificado')),
                
                # 11. Número Factura
                clean_value(invoice_data.get('invoice_number', f"DOC-{datetime.now().strftime('%Y%m%d%H%M%S')}")),
                
                # 12. Concepto
                clean_value(invoice_data.get('concept', 'Documento adjunto')),
                
                # 13. Subtotal
                clean_value(invoice_data.get('subtotal', '')),
                
                # 14. Impuestos
                clean_value(invoice_data.get('tax_amount', invoice_data.get('tax', ''))),
                
                # 15. Total
                clean_value(invoice_data.get('amount', invoice_data.get('total', ''))),
                
                # 16. Moneda
                clean_value(invoice_data.get('currency', 'MXN')),
                
                # 17. Método Pago
                clean_value(invoice_data.get('payment_method', '')),
                
                # 18. Categoría
                clean_value(invoice_data.get('category', 'Compras')),
                
                # 19. Estado
                'Procesado',
                
                # 20. Confianza
                f"{invoice_data.get('confidence', 0):.1%}" if invoice_data.get('confidence') else 'N/A',
                
                # 21. Link Archivo
                f"https://drive.google.com/file/d/{file_id}/view" if file_id else ''
            ]
            
            # Verificar que tenemos exactamente 21 campos
            if len(row_data) != 21:
                self.logger.warning(f"⚠️ Número de campos incorrecto: {len(row_data)}, esperado: 21")
                # Ajustar a 21 campos
                while len(row_data) < 21:
                    row_data.append('')
                row_data = row_data[:21]
            
            # Agregar fila a la hoja
            if self.drive_client.append_to_spreadsheet(spreadsheet_id, row_data):
                self.logger.info(f"        ✅ Datos agregados a hoja de cálculo")
            else:
                self.logger.error(f"        ❌ Error agregando datos a hoja")
                
        except Exception as e:
            self.logger.error(f"        ⚠️ Error actualizando hoja de cálculo: {e}")
            import traceback
            traceback.print_exc()
        
    
    def _generate_report(self, results: Dict):
        """Genera un reporte del procesamiento"""
        try:
            report = {
                'fecha_procesamiento': datetime.now().isoformat(),
                'estadisticas': self.stats,
                'exitosos': len(results['success']),
                'fallidos': len(results['failed']),
                'detalles': results
            }
            
            # Guardar reporte en JSON
            report_path = Path('logs') / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"📊 Reporte guardado en: {report_path}")
            
            # Subir reporte a Drive si está configurado
            if self.config.get('reports', {}).get('upload_to_drive', False):
                self._upload_report_to_drive(report_path)
            
        except Exception as e:
            self.logger.error(f"❌ Error generando reporte: {e}")
    
    def _upload_report_to_drive(self, report_path: Path):
        """Sube el reporte a Google Drive"""
        try:
            folder_path = f"DOCUFIND/Reportes/{datetime.now().year}"
            folder_id = self.drive_client.create_folder_path(folder_path)
            
            with open(report_path, 'rb') as f:
                file_id = self.drive_client.upload_file(
                    f.read(),
                    report_path.name,
                    folder_id
                )
            
            if file_id:
                self.logger.info(f"✅ Reporte subido a Drive")
        except Exception as e:
            self.logger.error(f"⚠️ Error subiendo reporte a Drive: {e}")
    
    def _send_notification(self, results: Dict):
        """Envía notificación por email del procesamiento"""
        try:
            subject = f"DOCUFIND - Procesamiento Completado - {datetime.now().strftime('%Y-%m-%d')}"
            
            body = f"""
            <html>
            <body>
                <h2>🚀 DOCUFIND - Reporte de Procesamiento</h2>
                
                <h3>📊 Estadísticas:</h3>
                <ul>
                    <li>📧 Correos procesados: {self.stats['emails_procesados']}</li>
                    <li>📄 Facturas extraídas: {self.stats['facturas_extraidas']}</li>
                    <li>☁️ Archivos subidos: {self.stats['archivos_subidos']}</li>
                    <li>❌ Errores: {self.stats['errores']}</li>
                </ul>
                
                <h3>✅ Procesados exitosamente: {len(results['success'])}</h3>
                <h3>❌ Fallidos: {len(results['failed'])}</h3>
                
                <p>Tiempo de procesamiento: {self._calculate_duration()}</p>
                
                <hr>
                <p><small>Este es un mensaje automático de DOCUFIND</small></p>
            </body>
            </html>
            """
            
            recipients = self.config.get('notifications', {}).get('recipients', [])
            for recipient in recipients:
                self.email_processor.send_notification(recipient, subject, body)
                self.logger.info(f"📬 Notificación enviada a: {recipient}")
            
        except Exception as e:
            self.logger.error(f"⚠️ Error enviando notificación: {e}")
    
    def _calculate_duration(self) -> str:
        """Calcula la duración del procesamiento"""
        if self.stats['tiempo_inicio'] and self.stats['tiempo_fin']:
            duration = self.stats['tiempo_fin'] - self.stats['tiempo_inicio']
            minutes, seconds = divmod(duration.total_seconds(), 60)
            return f"{int(minutes)} minutos, {int(seconds)} segundos"
        return "N/A"
    
    def _print_summary(self):
        """Imprime resumen del procesamiento"""
        self.logger.info("\n" + "=" * 60)
        self.logger.info("📊 RESUMEN DE PROCESAMIENTO")
        self.logger.info("=" * 60)
        self.logger.info(f"📧 Correos procesados: {self.stats['emails_procesados']}")
        self.logger.info(f"📄 Facturas extraídas: {self.stats['facturas_extraidas']}")
        self.logger.info(f"☁️ Archivos subidos: {self.stats['archivos_subidos']}")
        self.logger.info(f"❌ Errores encontrados: {self.stats['errores']}")
        self.logger.info(f"⏱️ Duración: {self._calculate_duration()}")
        self.logger.info("=" * 60)
        
        if self.stats['errores'] == 0:
            self.logger.info("✅ ¡Procesamiento completado exitosamente!")
        else:
            self.logger.warning(f"⚠️ Procesamiento completado con {self.stats['errores']} errores")
            
            

    def _get_complete_email_content(self, email: Dict) -> str:
        """
        🔧 MÉTODO CORREGIDO: Obtiene TODO el contenido disponible del email
        """
        content_parts = []
        
        try:
            # 1. Contenido del cuerpo principal
            body_content = email.get('body', '')
            if body_content:
                clean_body = self._clean_email_body(body_content)
                if clean_body:
                    content_parts.append(clean_body)
            
            # 2. Otros campos de contenido posibles
            for field in ['text_content', 'plain_content', 'message_body', 'content']:
                field_content = email.get(field, '')
                if field_content and field_content not in content_parts:
                    clean_content = self._clean_email_body(str(field_content))
                    if clean_content:
                        content_parts.append(clean_content)
            
            # 3. Si no hay contenido del cuerpo, usar el asunto como contexto
            if not content_parts:
                subject = email.get('subject', '')
                if subject:
                    content_parts.append(f"Asunto del correo: {subject}")
            
            # Combinar todo el contenido
            if content_parts:
                complete_content = '\n\n'.join(content_parts)
                # Limitar longitud total
                if len(complete_content) > 2000:
                    complete_content = complete_content[:1997] + '...'
                return complete_content
            
            return email.get('subject', 'Sin contenido')
            
        except Exception as e:
            self.logger.warning(f"⚠️ Error obteniendo contenido completo: {e}")  # ← 🔧 self.logger
            return email.get('subject', 'Error obteniendo contenido')



def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description='DOCUFIND - Procesador Inteligente de Correos y Facturas',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python find_documents_main.py                     # Procesar últimos 30 días
  python find_documents_main.py --days 7            # Procesar últimos 7 días
  python find_documents_main.py --from 2024-01-01 --to 2024-01-31
  python find_documents_main.py --query "factura"   # Buscar correos con "factura"
  python find_documents_main.py --limit 10          # Procesar solo 10 correos
  python find_documents_main.py --test              # Modo de prueba
        """
    )
    
    # Argumentos de fecha
    parser.add_argument('--from', '--date-from', dest='date_from',
                       help='Fecha inicial (YYYY-MM-DD)')
    parser.add_argument('--to', '--date-to', dest='date_to',
                       help='Fecha final (YYYY-MM-DD)')
    parser.add_argument('--days', type=int,
                       help='Procesar últimos N días')
    
    # Argumentos de filtrado
    parser.add_argument('--query', '-q',
                       help='Query de búsqueda adicional')
    parser.add_argument('--limit', '-l', type=int,
                       help='Límite de correos a procesar')
    
    # Argumentos de configuración
    parser.add_argument('--config', '-c', default='config/config.json',
                       help='Ruta al archivo de configuración')
    parser.add_argument('--test', action='store_true',
                       help='Ejecutar en modo de prueba (no hace cambios)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Mostrar información detallada')
    
    args = parser.parse_args()
    
    try:
        # Configurar fechas
        date_from = None
        date_to = datetime.now()
        
        if args.date_from:
            date_from = datetime.strptime(args.date_from, '%Y-%m-%d')
        elif args.days:
            date_from = datetime.now() - timedelta(days=args.days)
        else:
            date_from = datetime.now() - timedelta(days=30)
        
        if args.date_to:
            date_to = datetime.strptime(args.date_to, '%Y-%m-%d')
        
        # Modo de prueba
        if args.test:
            print("🧪 MODO DE PRUEBA ACTIVADO - No se realizarán cambios")
            print(f"  Periodo: {date_from.strftime('%Y-%m-%d')} a {date_to.strftime('%Y-%m-%d')}")
            print(f"  Query: {args.query or 'Sin filtro adicional'}")
            print(f"  Límite: {args.limit or 'Sin límite'}")
            response = input("\n¿Continuar? (s/n): ")
            if response.lower() != 's':
                print("Operación cancelada")
                return
        
        # Crear y ejecutar procesador
        processor = DocuFindProcessor(args.config)
        print('Parametros: ',date_from,'-',date_to)
        results = processor.process_emails(
            date_from=date_from,
            date_to=date_to,
            query=args.query,
            limit=args.limit
        )
        
        # Código de salida basado en errores
        if processor.stats['errores'] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Procesamiento interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()