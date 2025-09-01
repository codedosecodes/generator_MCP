#!/usr/bin/env python3
"""
DOCUFIND - Procesador Inteligente de Correos y Facturas
Punto de entrada principal de la aplicación
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import time

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
        
        # Estadísticas de procesamiento
        self.stats = {
            'emails_procesados': 0,
            'facturas_extraidas': 0,
            'archivos_subidos': 0,
            'errores': 0,
            'tiempo_inicio': None,
            'tiempo_fin': None
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
        
        # Configurar fechas por defecto
        if not date_from:
            date_from = datetime.now() - timedelta(days=30)
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
        """Procesa un correo individual - TODOS los emails se registran en la hoja"""
        try:
            self.logger.info(f"\\n[{idx}/{total}] Procesando: {email.get('subject', 'Sin asunto')}")
            self.logger.info(f"  De: {email.get('sender', 'Desconocido')}")
            self.logger.info(f"  Fecha: {email.get('date', 'Sin fecha')}")
            
            self.stats['emails_procesados'] += 1
            
            # IMPORTANTE: Guardar contexto del email actual
            self.current_email = email
            
            # Agregar el cuerpo del email al contexto si no está
            if 'body' not in email and hasattr(self.email_processor, '_get_email_body'):
                # Intentar obtener el cuerpo del email
                try:
                    # Este método ya debería existir en email_processor
                    email['body'] = self.email_processor._get_email_body_by_id(email['id'])
                except:
                    email['body'] = email.get('subject', '')  # Usar asunto como fallback
            
            # Extraer adjuntos
            attachments = self.email_processor.get_attachments(email['id'])
            
            # Guardar contexto de adjuntos
            self.current_attachments = attachments
            
            if not attachments:
                self.logger.info("  ⚠️ No se encontraron adjuntos")
                # IMPORTANTE: Registrar TODOS los emails, incluso sin adjuntos
                self._update_spreadsheet({}, None)
            else:
                self.logger.info(f"  📎 {len(attachments)} adjuntos encontrados")
                
                # Variable para rastrear si se procesó alguna factura
                invoice_processed = False
                
                # Procesar cada adjunto
                for attachment in attachments:
                    if self._is_invoice(attachment.get('filename', '')):
                        # Intentar extraer datos de factura
                        invoice_data = self.invoice_extractor.extract(attachment['content'])
                        if invoice_data:
                            # Organizar en Drive y actualizar spreadsheet
                            self._organize_in_drive(email, attachment, invoice_data)
                            invoice_processed = True
                            break  # Solo procesar la primera factura encontrada
                        
                # Si no se procesó ninguna factura pero hay adjuntos
                if not invoice_processed:
                    # Subir primer adjunto a Drive sin datos de factura
                    if attachments:
                        first_attachment = attachments[0]
                        try:
                            # Subir a Drive en carpeta "Otros"
                            date_str = email.get('date', '')
                            if ' ' in date_str:
                                date_str = date_str.split(' ')[0]
                            
                            try:
                                date = datetime.strptime(date_str, '%Y-%m-%d')
                            except:
                                date = datetime.now()
                            
                            folder_path = f"DOCUFIND/{date.year}/{date.strftime('%m-%B')}/Otros"
                            folder_id = self.drive_client.create_folder_path(folder_path)
                            
                            file_id = self.drive_client.upload_file(
                                first_attachment['content'],
                                first_attachment['filename'],
                                folder_id
                            )
                            
                            # Actualizar spreadsheet con archivo pero sin datos de factura
                            self._update_spreadsheet({}, file_id)
                        except Exception as e:
                            self.logger.error(f"  ❌ Error subiendo adjunto: {e}")
                            # Aún así registrar en spreadsheet
                            self._update_spreadsheet({}, None)
            
            # Agregar a resultados exitosos
            results['success'].append({
                'email_id': email['id'],
                'subject': email.get('subject'),
                'sender': email.get('sender'),
                'date': email.get('date'),
                'attachments_processed': len(attachments) if attachments else 0
            })
            
        except Exception as e:
            self.logger.error(f"  ❌ Error procesando correo: {e}")
            self.stats['errores'] += 1
            
            # Incluso con error, intentar registrar en spreadsheet
            try:
                self._update_spreadsheet({}, None)
            except:
                pass
            
            results['failed'].append({
                'email_id': email.get('id'),
                'subject': email.get('subject'),
                'error': str(e)
            })
            
    def _process_attachment(self, email: Dict, attachment: Dict, results: Dict):
        """Procesa un adjunto individual"""
        try:
            filename = attachment.get('filename', 'archivo_sin_nombre')
            self.logger.info(f"    📄 Procesando: {filename}")
            
            # Recopilar info de adjuntos
            attachments_info = {
                'has_attachments': True,
                'count': 1,
                'names': [filename]
            }
            
            if self._is_invoice(filename):
                invoice_data = self.invoice_extractor.extract(attachment['content'])
                
                if invoice_data:
                    # Agregar info del email a los datos
                    invoice_data['email_date'] = email.get('date', '')
                    invoice_data['email_sender'] = email.get('sender', '')
                    invoice_data['email_subject'] = email.get('subject', '')
                    
                    self._organize_in_drive(email, attachment, invoice_data)
        except Exception as e:
            self.logger.error(f"    ❌ Error procesando adjunto: {e}")
            self.stats['errores'] += 1
                
    #def _process_attachment(self, email: Dict, attachment: Dict, results: Dict):
    #    """Procesa un adjunto individual"""
    #    try:
    #        filename = attachment.get('filename', 'archivo_sin_nombre')
    #        self.logger.info(f"    📄 Procesando: {filename}")
    #        
    #        # Verificar si es una factura
    #        if self._is_invoice(filename):
    #            # Extraer datos de la factura
    #            invoice_data = self.invoice_extractor.extract(attachment['content'])
    #            
    #            if invoice_data:
    #                self.logger.info(f"      ✅ Datos extraídos: {invoice_data.get('invoice_number', 'N/A')}")
    #                self.stats['facturas_extraidas'] += 1
    #                
    #                # Organizar en Google Drive
    #                self._organize_in_drive(email, attachment, invoice_data)
    #            else:
    #                self.logger.warning(f"      ⚠️ No se pudieron extraer datos")
    #        else:
    #            # Subir archivo tal cual
    #            self._upload_to_drive(email, attachment)
    #        
    #    except Exception as e:
    #        self.logger.error(f"    ❌ Error procesando adjunto: {e}")
    #        self.stats['errores'] += 1
    
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
        """Organiza una factura en Google Drive"""
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
            
            # Crear estructura de carpetas basada en fecha
            folder_path = f"DOCUFIND/{date.year}/{date.strftime('%m-%B')}/Facturas"
            # Crear carpetas si no existen
            folder_id = self.drive_client.create_folder_path(folder_path)
            
            # Renombrar archivo con datos de factura
            new_filename = self._generate_filename(invoice_data, attachment['filename'])
            
            # Subir archivo
            file_id = self.drive_client.upload_file(
                attachment['content'],
                new_filename,
                folder_id,
                invoice_data
            )
            
            if file_id:
                self.logger.info(f"      ✅ Subido a Drive: {new_filename}")
                self.stats['archivos_subidos'] += 1
                
                # Actualizar hoja de cálculo
                self._update_spreadsheet(invoice_data, file_id)
            
        except Exception as e:
           self.logger.error(f"      ❌ Error organizando en Drive: {e}")
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
        """Actualiza la hoja de cálculo con los datos de la factura y email"""
        try:
            # Buscar o crear hoja de cálculo
            spreadsheet_name = f"DOCUFIND_Facturas_{datetime.now().year}"
            
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
            
            # Obtener información del email SIEMPRE disponible
            email_info = getattr(self, 'current_email', {})
            attachments_info = getattr(self, 'current_attachments', [])
            
            # === CORRECCIÓN 1: Fecha Factura ===
            # Siempre usar la fecha del email como fecha de factura
            email_date = email_info.get('date', '')
            if ' ' in email_date:
                fecha_factura = email_date.split(' ')[0]  # Tomar solo fecha sin hora
            else:
                fecha_factura = email_date
            
            # === CORRECCIÓN 2: Proveedor ===
            # Extraer dominio del remitente como proveedor
            sender = email_info.get('sender', '')
            proveedor = self._extract_clean_domain(sender)
            
            # === CORRECCIÓN 3: Concepto ===
            # Extraer primeros 500 caracteres del cuerpo del email
            concepto = self._extract_email_concept(email_info)
            
            # Preparar lista de nombres de adjuntos
            attachment_names = []
            if attachments_info:
                for att in attachments_info:
                    if isinstance(att, dict):
                        attachment_names.append(att.get('filename', ''))
                    else:
                        attachment_names.append(str(att))
            
            # IMPORTANTE: Preparar exactamente 20 campos en orden
            row_data = [
                # 1. Fecha Procesamiento
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                
                # 2. Fecha Email
                email_date.split(' ')[0] if ' ' in email_date else email_date,
                
                # 3. Remitente (completo)
                self._clean_text(sender)[:200],
                
                # 4. Asunto
                self._clean_text(email_info.get('subject', ''))[:200],
                
                # 5. Tiene Adjuntos
                'Sí' if attachments_info else 'No',
                
                # 6. Cantidad Adjuntos
                str(len(attachments_info)) if attachments_info else '0',
                
                # 7. Nombres Adjuntos
                ', '.join(attachment_names)[:1000] if attachment_names else '',
                
                # 8. Fecha Factura (SIEMPRE la fecha del email)
                fecha_factura,
                
                # 9. Proveedor (SIEMPRE el dominio del remitente)
                proveedor,
                
                # 10. Número Factura
                str(invoice_data.get('invoice_number', ''))[:50] if invoice_data else '',
                
                # 11. Concepto (SIEMPRE primeros 500 caracteres del email)
                concepto,
                
                # 12. Subtotal
                str(invoice_data.get('subtotal', '')) if invoice_data else '',
                
                # 13. Impuestos
                str(invoice_data.get('tax_amount', invoice_data.get('tax', ''))) if invoice_data else '',
                
                # 14. Total
                str(invoice_data.get('amount', invoice_data.get('total', ''))) if invoice_data else '',
                
                # 15. Moneda
                invoice_data.get('currency', 'N/A') if invoice_data else 'N/A',
                
                # 16. Método Pago
                invoice_data.get('payment_method', '') if invoice_data else '',
                
                # 17. Categoría
                invoice_data.get('category', 'Email') if invoice_data else 'Email',
                
                # 18. Estado
                'Procesado',
                
                # 19. Confianza
                f"{invoice_data.get('confidence', 0):.1%}" if invoice_data and invoice_data.get('confidence') else 'N/A',
                
                # 20. Link Archivo
                f"https://drive.google.com/file/d/{file_id}/view" if file_id else ''
            ]
            
            # Verificar que tenemos exactamente 20 campos
            if len(row_data) != 20:
                self.logger.warning(f"⚠️ Número de campos incorrecto: {len(row_data)}, esperado: 20")
                # Ajustar a 20 campos
                while len(row_data) < 20:
                    row_data.append('')
                row_data = row_data[:20]
            
            # Agregar fila a la hoja
            if self.drive_client.append_to_spreadsheet(spreadsheet_id, row_data):
                self.logger.info(f"        ✅ Datos agregados a hoja de cálculo")
            else:
                self.logger.error(f"        ❌ Error agregando datos a hoja")
                
        except Exception as e:
            self.logger.error(f"        ⚠️ Error actualizando hoja de cálculo: {e}")
            import traceback
            traceback.print_exc()
            
            
            
    def _extract_clean_domain(self, sender: str) -> str:
        """
        Extrae y limpia el dominio del remitente
        
        Args:
            sender: String del remitente (puede incluir nombre y email)
        
        Returns:
            Dominio limpio sin caracteres especiales
        """
        import re
        
        if not sender:
            return "Desconocido"
        
        # Buscar email en el string
        email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
        email_match = re.search(email_pattern, sender)
        
        if email_match:
            email = email_match.group(0)
            # Extraer dominio
            domain = email.split('@')[1] if '@' in email else email
            # Remover extensión común
            domain_parts = domain.split('.')
            if len(domain_parts) > 2:
                # Caso como mail.empresa.com -> empresa
                domain_clean = domain_parts[-2]
            else:
                # Caso como empresa.com -> empresa
                domain_clean = domain_parts[0]
            
            # Limpiar caracteres especiales y capitalizar
            domain_clean = re.sub(r'[^a-zA-Z0-9]', '', domain_clean)
            return domain_clean.capitalize()
        else:
            # Si no hay email, intentar limpiar el nombre
            # Tomar primeras palabras antes de caracteres especiales
            name = re.sub(r'[<>"\']', ' ', sender)
            name = name.split()[0] if name.split() else sender
            name = re.sub(r'[^a-zA-Z0-9\s]', '', name)
            return name.strip()[:50] if name.strip() else "Desconocido"  
        
    def _extract_email_concept(self, email_info: Dict) -> str:
        """
        Extrae un concepto legible del email limpiando HTML/CSS
        
        Args:
            email_info: Información del email
        
        Returns:
            Concepto de máximo 1000 caracteres sin HTML/CSS
        """
        import re
        from html.parser import HTMLParser
        
        class HTMLTextExtractor(HTMLParser):
            """Parser para extraer solo texto de HTML"""
            def __init__(self):
                super().__init__()
                self.text_parts = []
                self.skip_tags = {'script', 'style', 'meta', 'link'}
                self.current_tag = None
                
            def handle_starttag(self, tag, attrs):
                self.current_tag = tag.lower()
                
            def handle_endtag(self, tag):
                self.current_tag = None
                
            def handle_data(self, data):
                if self.current_tag not in self.skip_tags:
                    text = data.strip()
                    if text:
                        self.text_parts.append(text)
            
            def get_text(self):
                return ' '.join(self.text_parts)
        
        # Prioridad 1: Asunto del email (limpio)
        subject = email_info.get('subject', '')
        
        # Prioridad 2: Cuerpo del email
        body = email_info.get('body', '')
        
        # Si el cuerpo parece tener HTML, extraer solo el texto
        if '<' in body and '>' in body:
            try:
                # Usar el parser HTML para extraer texto
                parser = HTMLTextExtractor()
                parser.feed(body)
                body_text = parser.get_text()
            except:
                # Si falla el parser, usar método de respaldo
                body_text = body
        else:
            body_text = body
        
        # Combinar asunto y cuerpo
        full_text = f"{subject}. {body_text}"
        
        # === LIMPIEZA PROFUNDA ===
        
        # 1. Remover estilos CSS inline y clases
        full_text = re.sub(r'\.custom-[a-z0-9]+\{[^}]*\}', '', full_text)
        full_text = re.sub(r'style="[^"]*"', '', full_text)
        full_text = re.sub(r'style=\'[^\']*\'', '', full_text)
        full_text = re.sub(r'class="[^"]*"', '', full_text)
        full_text = re.sub(r'class=\'[^\']*\'', '', full_text)
        
        # 2. Remover todas las etiquetas HTML restantes
        full_text = re.sub(r'<script[^>]*>.*?</script>', '', full_text, flags=re.DOTALL)
        full_text = re.sub(r'<style[^>]*>.*?</style>', '', full_text, flags=re.DOTALL)
        full_text = re.sub(r'<[^>]+>', '', full_text)
        
        # 3. Decodificar entidades HTML
        html_entities = {
            '&nbsp;': ' ', '&amp;': '&', '&lt;': '<', '&gt;': '>',
            '&quot;': '"', '&#39;': "'", '&apos;': "'",
            '&ndash;': '-', '&mdash;': '-', '&hellip;': '...',
            '&copy;': '©', '&reg;': '®', '&trade;': '™'
        }
        for entity, char in html_entities.items():
            full_text = full_text.replace(entity, char)
        
        # 4. Remover URLs
        full_text = re.sub(r'https?://[^\s]+', '', full_text)
        full_text = re.sub(r'www\.[^\s]+', '', full_text)
        
        # 5. Remover emails
        full_text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', full_text)
        
        # 6. Remover selectores CSS y propiedades
        # Patrones como: margin:20px; font-family:system-ui; etc.
        full_text = re.sub(r'[a-z-]+:\s*[^;]+;', '', full_text)
        full_text = re.sub(r'[a-z-]+:\s*[^,\s]+(?:,|\s)', '', full_text)
        
        # 7. Remover valores CSS sueltos
        # Patrones como: rgb(51, 51, 51), #027eff, 20px, etc.
        full_text = re.sub(r'rgb\([^)]+\)', '', full_text)
        full_text = re.sub(r'rgba\([^)]+\)', '', full_text)
        full_text = re.sub(r'#[0-9a-fA-F]{3,6}\b', '', full_text)
        full_text = re.sub(r'\b\d+px\b', '', full_text)
        full_text = re.sub(r'\b\d+em\b', '', full_text)
        full_text = re.sub(r'\b\d+%\b', '', full_text)
        
        # 8. Remover nombres de fuentes y valores CSS comunes
        css_values = [
            'sans-serif', 'serif', 'monospace', 'Arial', 'Helvetica',
            'system-ui', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto',
            'bold', 'italic', 'normal', 'underline', 'none',
            'block', 'inline', 'flex', 'grid', 'absolute', 'relative',
            'auto', 'inherit', 'initial', 'unset'
        ]
        for value in css_values:
            full_text = re.sub(r'\b' + re.escape(value) + r'\b', '', full_text, flags=re.IGNORECASE)
        
        # 9. Remover caracteres especiales de programación/markup
        full_text = re.sub(r'[{}()\[\];:<>]', ' ', full_text)
        
        # 10. Remover múltiples espacios, tabs y saltos de línea
        full_text = re.sub(r'\s+', ' ', full_text)
        
        # 11. Remover espacios alrededor de puntuación
        full_text = re.sub(r'\s+([.,!?])', r'\1', full_text)
        full_text = re.sub(r'([.,!?])\s+', r'\1 ', full_text)
        
        # 12. Limpiar principio y final
        full_text = full_text.strip()
        
        # 13. Remover puntos y comas consecutivos
        full_text = re.sub(r'[.,]{2,}', '.', full_text)
        
        # 14. Si después de toda la limpieza queda muy poco texto, intentar método alternativo
        if len(full_text) < 50:
            # Intentar extraer solo el asunto y las primeras palabras del body original
            simple_text = subject
            if body:
                # Tomar solo texto alfanumérico del body
                body_words = re.findall(r'\b[A-Za-z0-9]+\b', body)
                if body_words:
                    simple_text += '. ' + ' '.join(body_words[:100])
            full_text = simple_text
        
        # 15. Asegurar que no hay caracteres no imprimibles
        full_text = ''.join(char for char in full_text if char.isprintable() or char == ' ')
        
        # Tomar primeros 1000 caracteres (aumentado de 500)
        concept = full_text[:1000]
        
        # Si está vacío o muy corto, usar valores por defecto
        if not concept or len(concept) < 10:
            if subject:
                concept = f"Email: {subject}"
            else:
                concept = "Email sin contenido extraíble"
        
        # Asegurar que termina en un punto o espacio (no cortar palabras)
        if len(concept) == 1000:
            last_space = concept.rfind(' ', 950, 1000)
            if last_space > 0:
                concept = concept[:last_space] + '...'
        
        return concept
    
    def _clean_text(self, text: str) -> str:
        """
        Limpia texto removiendo caracteres problemáticos
        
        Args:
            text: Texto a limpiar
        
        Returns:
            Texto limpio
        """
        import re
        
        if not text:
            return ""
        
        # Convertir a string si no lo es
        text = str(text)
        
        # Remover caracteres de control y no imprimibles
        text = ''.join(char for char in text if char.isprintable() or char.isspace())
        
        # Remover saltos de línea múltiples
        text = re.sub(r'\n+', ' ', text)
        text = re.sub(r'\r+', ' ', text)
        
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        
        # Remover comillas problemáticas
        text = text.replace('"', "'").replace('"', "'").replace('"', "'")
        
        return text.strip()
    
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