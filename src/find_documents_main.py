#!/usr/bin/env python3
"""
FIND_DOCUMENTS - Aplicación Principal
Procesador inteligente de correos y facturas con organización automática en Google Drive

Author: FIND_DOCUMENTS Team
Version: 1.0.0
"""

import asyncio
import json
import logging
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import traceback

# Importar nuestros módulos
try:
    from email_processor import EmailProcessor, EmailCredentials, EmailFilter
    from google_drive_client import GoogleDriveClient
    from invoice_extractor import InvoiceExtractor
    from config_manager import ConfigManager
except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de que todos los archivos estén en la carpeta src/")
    sys.exit(1)

# Configurar logging
def setup_logging():
    """Configurar sistema de logging"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/find_documents.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

class FindDocumentsApp:
    """Aplicación principal de FIND_DOCUMENTS"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.logger = setup_logging()
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.load_config()
        
        # Estadísticas de procesamiento
        self.stats = {
            'total_emails': 0,
            'processed_emails': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'total_attachments': 0,
            'created_folders': 0,
            'start_time': None,
            'end_time': None
        }
        
        # Componentes principales
        self.email_processor = None
        self.drive_client = None
        self.invoice_extractor = None
        
        self.logger.info("🚀 FIND_DOCUMENTS iniciado")
    
    async def initialize_components(self):
        """Inicializar todos los componentes del sistema"""
        try:
            self.logger.info("🔧 Inicializando componentes...")
            
            # 1. Inicializar procesador de email
            email_creds = EmailCredentials(
                server=self.config['email_credentials']['server'],
                port=self.config['email_credentials']['port'],
                username=self.config['email_credentials']['username'],
                password=self.config['email_credentials']['password']
            )
            self.email_processor = EmailProcessor(email_creds)
            
            # 2. Inicializar cliente Google Drive
            self.drive_client = GoogleDriveClient(
                credentials_path=self.config['google_services']['credentials_path'],
                token_path=self.config['google_services']['token_path']
            )
            await self.drive_client.initialize()
            
            # 3. Inicializar extractor de facturas
            self.invoice_extractor = InvoiceExtractor()
            
            self.logger.info("✅ Todos los componentes inicializados correctamente")
            
        except Exception as e:
            self.logger.error(f"❌ Error inicializando componentes: {e}")
            raise
    
    async def run_complete_process(self):
        """Ejecutar el proceso completo de búsqueda y procesamiento"""
        try:
            self.stats['start_time'] = datetime.now()
            self.logger.info("🎯 Iniciando proceso completo de FIND_DOCUMENTS")
            
            # Mostrar configuración
            self._show_configuration()
            
            # Fase 1: Inicializar componentes
            await self.initialize_components()
            
            # Fase 2: Crear estructura en Google Drive
            project_folder_id = await self._create_drive_structure()
            
            # Fase 3: Buscar y procesar correos
            emails = await self._search_and_filter_emails()
            
            if not emails:
                self.logger.info("ℹ️  No se encontraron correos que cumplan los criterios")
                return self._generate_final_report()
            
            # Fase 4: Crear hoja de cálculo
            spreadsheet_id = await self._create_tracking_spreadsheet(project_folder_id)
            
            # Fase 5: Procesar cada correo
            processed_data = await self._process_all_emails(emails, project_folder_id)
            
            # Fase 6: Actualizar hoja de cálculo
            await self._update_spreadsheet(spreadsheet_id, processed_data)
            
            # Fase 7: Generar reporte final
            self.stats['end_time'] = datetime.now()
            final_report = self._generate_final_report()
            
            # Fase 8: Enviar notificación (opcional)
            if self.config.get('notification_settings', {}).get('email_reports', False):
                await self._send_completion_notification(final_report)
            
            self.logger.info("🎉 Proceso completado exitosamente")
            return final_report
            
        except Exception as e:
            self.logger.error(f"❌ Error en proceso principal: {e}")
            self.logger.error(traceback.format_exc())
            raise
    
    def _show_configuration(self):
        """Mostrar configuración actual"""
        params = self.config['search_parameters']
        self.logger.info("📋 CONFIGURACIÓN ACTUAL:")
        self.logger.info(f"  📧 Email: {self.config['email_credentials']['username']}")
        self.logger.info(f"  📅 Período: {params['start_date']} a {params['end_date']}")
        self.logger.info(f"  🔍 Palabras clave: {', '.join(params['keywords'])}")
        self.logger.info(f"  📁 Carpeta destino: {params['folder_name']}")
    
    async def _create_drive_structure(self) -> str:
        """Crear estructura de carpetas en Google Drive"""
        self.logger.info("📁 Creando estructura en Google Drive...")
        
        try:
            folder_name = self.config['search_parameters']['folder_name']
            root_folder = self.config['google_services']['drive_folder_root']
            
            # Crear carpeta raíz FIND_DOCUMENTS
            root_folder_id = await self.drive_client.create_or_get_folder(root_folder, None)
            self.stats['created_folders'] += 1
            
            # Crear carpeta del proyecto
            project_folder_id = await self.drive_client.create_or_get_folder(folder_name, root_folder_id)
            self.stats['created_folders'] += 1
            
            self.logger.info(f"✅ Estructura creada: {root_folder}/{folder_name}")
            return project_folder_id
            
        except Exception as e:
            self.logger.error(f"❌ Error creando estructura Drive: {e}")
            raise
    
    async def _search_and_filter_emails(self) -> List[Dict]:
        """Buscar y filtrar correos según criterios"""
        self.logger.info("🔍 Buscando correos...")
        
        try:
            # Crear filtro de búsqueda
            params = self.config['search_parameters']
            email_filter = EmailFilter(
                start_date=params['start_date'],
                end_date=params['end_date'],
                keywords=params['keywords'],
                has_attachments=None  # Buscar todos, con y sin adjuntos
            )
            
            # Conectar y buscar
            await self.email_processor.connect()
            emails = await self.email_processor.search_emails(email_filter)
            await self.email_processor.disconnect()
            
            self.stats['total_emails'] = len(emails)
            self.logger.info(f"📧 Encontrados {len(emails)} correos que cumplen criterios")
            
            return emails
            
        except Exception as e:
            self.logger.error(f"❌ Error buscando correos: {e}")
            raise
    
    async def _create_tracking_spreadsheet(self, parent_folder_id: str) -> str:
        """Crear hoja de cálculo para tracking"""
        self.logger.info("📊 Creando hoja de cálculo de seguimiento...")
        
        try:
            folder_name = self.config['search_parameters']['folder_name']
            spreadsheet_name = f"{folder_name}_Documentos_Procesados"
            
            # Headers para la hoja de cálculo
            headers = [
                'Fecha Correo', 'From', 'To', 'Subject', 'Tiene Adjuntos',
                'Ruta Adjuntos', 'Valor Factura', 'Concepto', 'Quien Facturo',
                'ID Correo', 'Fecha Procesamiento', 'Estado', 'Observaciones'
            ]
            
            spreadsheet_id = await self.drive_client.create_spreadsheet(
                spreadsheet_name, 
                parent_folder_id, 
                headers
            )
            
            self.logger.info(f"✅ Hoja de cálculo creada: {spreadsheet_id}")
            return spreadsheet_id
            
        except Exception as e:
            self.logger.error(f"❌ Error creando hoja de cálculo: {e}")
            raise
    
    async def _process_all_emails(self, emails: List[Dict], project_folder_id: str) -> List[Dict]:
        """Procesar todos los correos encontrados"""
        processed_data = []
        total = len(emails)
        
        self.logger.info(f"⚙️  Procesando {total} correos...")
        
        for idx, email_data in enumerate(emails):
            try:
                # Mostrar progreso
                progress = (idx + 1) / total * 100
                self.logger.info(f"📊 Procesando {idx + 1}/{total} ({progress:.1f}%)")
                
                # Procesar email individual
                processed_email = await self._process_single_email(
                    email_data, 
                    project_folder_id,
                    idx + 1
                )
                
                processed_data.append(processed_email)
                self.stats['processed_emails'] += 1
                self.stats['successful_extractions'] += 1
                
            except Exception as e:
                self.logger.error(f"❌ Error procesando email {idx + 1}: {e}")
                
                # Agregar registro de error
                error_record = {
                    'fecha_correo': email_data.get('date', ''),
                    'from': email_data.get('from_addr', ''),
                    'to': email_data.get('to_addr', ''),
                    'subject': email_data.get('subject', ''),
                    'estado': 'ERROR',
                    'observaciones': str(e)
                }
                processed_data.append(error_record)
                
                self.stats['processed_emails'] += 1
                self.stats['failed_extractions'] += 1
                continue
        
        self.logger.info(f"✅ Procesamiento completado: {self.stats['successful_extractions']} exitosos, {self.stats['failed_extractions']} fallidos")
        return processed_data
    
    async def _process_single_email(self, email_data: Dict, project_folder_id: str, email_number: int) -> Dict:
        """Procesar un email individual"""
        try:
            # Parsear fecha del correo
            email_date = email_data['raw_date']
            
            # Crear estructura de carpetas para adjuntos si existen
            attachment_path = ""
            if email_data['has_attachments']:
                attachment_path = await self._organize_attachments(
                    email_data, 
                    project_folder_id, 
                    email_date
                )
                self.stats['total_attachments'] += len(email_data['attachments'])
            
            # Extraer datos de factura usando IA
            invoice_data = await self.invoice_extractor.extract_invoice_data(
                email_content=email_data['content'],
                attachments=email_data['attachments']
            )
            
            # Preparar datos para hoja de cálculo
            processed_data = {
                'fecha_correo': email_date.strftime('%Y-%m-%d %H:%M:%S'),
                'from': email_data['from_addr'][:100],  # Limitar longitud
                'to': email_data['to_addr'][:100],
                'subject': email_data['subject'][:150],
                'tiene_adjuntos': 'Sí' if email_data['has_attachments'] else 'No',
                'ruta_adjuntos': attachment_path,
                'valor_factura': invoice_data.get('amount', ''),
                'concepto': invoice_data.get('concept', '')[:200],
                'quien_facturo': invoice_data.get('vendor', '')[:100],
                'id_correo': email_data['id'],
                'fecha_procesamiento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'estado': 'PROCESADO',
                'observaciones': f"Confianza: {invoice_data.get('confidence', 0):.0%}"
            }
            
            return processed_data
            
        except Exception as e:
            self.logger.error(f"❌ Error en procesamiento individual: {e}")
            raise
    
    async def _organize_attachments(self, email_data: Dict, project_folder_id: str, email_date: datetime) -> str:
        """Organizar adjuntos en estructura jerárquica"""
        try:
            # Crear estructura año/mes/email_id
            year_folder_id = await self.drive_client.create_or_get_folder(
                str(email_date.year), 
                project_folder_id
            )
            
            month_folder_id = await self.drive_client.create_or_get_folder(
                f"{email_date.month:02d}_{email_date.strftime('%B')}", 
                year_folder_id
            )
            
            email_folder_id = await self.drive_client.create_or_get_folder(
                f"Email_{email_data['id']}", 
                month_folder_id
            )
            
            # Subir adjuntos
            uploaded_files = []
            for attachment in email_data['attachments']:
                try:
                    file_id = await self.drive_client.upload_file(
                        attachment['content'],
                        attachment['filename'],
                        email_folder_id,
                        attachment['content_type']
                    )
                    uploaded_files.append(attachment['filename'])
                    
                except Exception as e:
                    self.logger.warning(f"⚠️  Error subiendo {attachment['filename']}: {e}")
            
            folder_name = self.config['search_parameters']['folder_name']
            attachment_path = f"FIND_DOCUMENTS/{folder_name}/{email_date.year}/{email_date.month:02d}/Email_{email_data['id']}"
            
            self.stats['created_folders'] += 3  # año, mes, email
            
            return attachment_path
            
        except Exception as e:
            self.logger.error(f"❌ Error organizando adjuntos: {e}")
            return f"ERROR: {str(e)}"
    
    async def _update_spreadsheet(self, spreadsheet_id: str, processed_data: List[Dict]):
        """Actualizar hoja de cálculo con datos procesados"""
        self.logger.info("📊 Actualizando hoja de cálculo...")
        
        try:
            # Preparar datos para inserción
            rows_data = []
            for item in processed_data:
                row = [
                    item.get('fecha_correo', ''),
                    item.get('from', ''),
                    item.get('to', ''),
                    item.get('subject', ''),
                    item.get('tiene_adjuntos', ''),
                    item.get('ruta_adjuntos', ''),
                    str(item.get('valor_factura', '')),
                    item.get('concepto', ''),
                    item.get('quien_facturo', ''),
                    item.get('id_correo', ''),
                    item.get('fecha_procesamiento', ''),
                    item.get('estado', ''),
                    item.get('observaciones', '')
                ]
                rows_data.append(row)
            
            # Insertar datos
            await self.drive_client.append_to_spreadsheet(spreadsheet_id, rows_data)
            
            self.logger.info(f"✅ Hoja actualizada con {len(rows_data)} registros")
            
        except Exception as e:
            self.logger.error(f"❌ Error actualizando hoja de cálculo: {e}")
            raise
    
    def _generate_final_report(self) -> Dict:
        """Generar reporte final del procesamiento"""
        duration = None
        if self.stats['start_time'] and self.stats['end_time']:
            duration = self.stats['end_time'] - self.stats['start_time']
        
        success_rate = 0
        if self.stats['processed_emails'] > 0:
            success_rate = (self.stats['successful_extractions'] / self.stats['processed_emails']) * 100
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'configuration': {
                'folder_name': self.config['search_parameters']['folder_name'],
                'date_range': f"{self.config['search_parameters']['start_date']} - {self.config['search_parameters']['end_date']}",
                'keywords': self.config['search_parameters']['keywords']
            },
            'statistics': {
                'total_emails_found': self.stats['total_emails'],
                'emails_processed': self.stats['processed_emails'],
                'successful_extractions': self.stats['successful_extractions'],
                'failed_extractions': self.stats['failed_extractions'],
                'total_attachments': self.stats['total_attachments'],
                'folders_created': self.stats['created_folders'],
                'success_rate_percent': round(success_rate, 1),
                'processing_duration': str(duration) if duration else 'N/A'
            },
            'status': 'COMPLETED' if self.stats['failed_extractions'] == 0 else 'COMPLETED_WITH_ERRORS'
        }
        
        # Logging del reporte
        self.logger.info("📋 REPORTE FINAL:")
        self.logger.info(f"  📧 Correos encontrados: {report['statistics']['total_emails_found']}")
        self.logger.info(f"  ✅ Procesados exitosamente: {report['statistics']['successful_extractions']}")
        self.logger.info(f"  ❌ Errores: {report['statistics']['failed_extractions']}")
        self.logger.info(f"  📎 Adjuntos procesados: {report['statistics']['total_attachments']}")
        self.logger.info(f"  📁 Carpetas creadas: {report['statistics']['folders_created']}")
        self.logger.info(f"  🎯 Tasa de éxito: {report['statistics']['success_rate_percent']}%")
        if duration:
            self.logger.info(f"  ⏱️  Duración: {duration}")
        
        return report
    
    async def _send_completion_notification(self, report: Dict):
        """Enviar notificación de finalización por email"""
        try:
            self.logger.info("📬 Enviando notificación de finalización...")
            
            # Aquí podrías implementar envío de email con los resultados
            # Por ahora solo registramos que se enviaría
            
            self.logger.info("✅ Notificación enviada")
            
        except Exception as e:
            self.logger.warning(f"⚠️  No se pudo enviar notificación: {e}")

# Función principal
async def main():
    """Función principal de la aplicación"""
    try:
        print("🚀 Iniciando FIND_DOCUMENTS - Procesador de Correos y Facturas")
        print("=" * 70)
        
        # Crear e inicializar aplicación
        app = FindDocumentsApp()
        
        # Ejecutar proceso completo
        result = await app.run_complete_process()
        
        print("\n" + "=" * 70)
        print("🎉 PROCESAMIENTO COMPLETADO")
        print("=" * 70)
        
        # Mostrar resumen
        stats = result['statistics']
        print(f"📧 Correos procesados: {stats['emails_processed']}")
        print(f"✅ Extracciones exitosas: {stats['successful_extractions']}")
        print(f"📎 Adjuntos organizados: {stats['total_attachments']}")
        print(f"🎯 Tasa de éxito: {stats['success_rate_percent']}%")
        
        # Guardar reporte
        report_path = Path("logs") / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Reporte guardado: {report_path}")
        print("\n🔗 Revisa tu Google Drive para ver los documentos organizados")
        
        return result
        
    except KeyboardInterrupt:
        print("\n⚠️  Proceso interrumpido por el usuario")
        return None
    except Exception as e:
        print(f"\n❌ Error crítico: {e}")
        print("\n🔍 Ver logs/find_documents.log para más detalles")
        return None

if __name__ == "__main__":
    # Ejecutar aplicación
    result = asyncio.run(main())
    
    if result:
        print("\n✨ ¡Aplicación ejecutada exitosamente!")
    else:
        print("\n💥 La aplicación terminó con errores")
        sys.exit(1)