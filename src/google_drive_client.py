#!/usr/bin/env python3
"""
Google Drive Client - DOCUFIND
Cliente para interactuar con Google Drive y Sheets
"""

import os
import io
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

# Google API imports
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
except ImportError:
    print("❌ Error: Librerías de Google no instaladas")
    print("Ejecuta: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    raise

logger = logging.getLogger(__name__)

class GoogleServicesConfig:
    """Configuración para los servicios de Google"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        """
        Inicializa la configuración desde un diccionario
        
        Args:
            config_dict: Diccionario con la configuración
        """
        self.credentials_path = config_dict.get('credentials_path', './config/credentials.json')
        self.token_path = config_dict.get('token_path', './config/token.json')
        self.drive_folder_root = config_dict.get('drive_folder_root', 'DOCUFIND')
        self.root_folder = config_dict.get('root_folder', self.drive_folder_root)  # Alias
        self.scopes = config_dict.get('scopes', [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/spreadsheets'
        ])
        self.create_year_folders = config_dict.get('create_year_folders', True)
        self.create_month_folders = config_dict.get('create_month_folders', True)
        self.upload_reports = config_dict.get('upload_reports', True)

class GoogleDriveClient:
    """Cliente para interactuar con Google Drive"""
    
    # Scopes necesarios
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, 
                 credentials_path: Optional[str] = None,
                 token_path: Optional[str] = None,
                 config: Optional[Union[Dict[str, Any], GoogleServicesConfig]] = None):
        """
        Inicializa el cliente de Google Drive
        
        Args:
            credentials_path: Ruta al archivo credentials.json
            token_path: Ruta al archivo token.json
            config: Configuración completa (dict o GoogleServicesConfig)
        """
        # Si se pasa config, usarla
        if config:
            if isinstance(config, dict):
                self.config = GoogleServicesConfig(config)
            else:
                self.config = config
            self.credentials_path = self.config.credentials_path
            self.token_path = self.config.token_path
        else:
            # Usar parámetros individuales
            self.credentials_path = credentials_path or './config/credentials.json'
            self.token_path = token_path or './config/token.json'
            self.config = GoogleServicesConfig({
                'credentials_path': self.credentials_path,
                'token_path': self.token_path
            })
        
        self.creds = None
        self.drive_service = None
        self.sheets_service = None
        
        # Cache de carpetas
        self.folder_cache = {}
        
        logger.info("📁 GoogleDriveClient inicializado")
    
    def authenticate(self) -> bool:
        """
        Autentica con Google Drive con mejor manejo de errores
        
        Returns:
            True si la autenticación fue exitosa
        """
        try:
            # Token existe y es válido
            if os.path.exists(self.token_path):
                try:
                    self.creds = Credentials.from_authorized_user_file(
                        self.token_path, 
                        self.config.scopes
                    )
                    logger.info("🔑 Token existente cargado")
                except Exception as e:
                    logger.warning(f"⚠️ Error cargando token existente: {e}")
                    logger.info("🔄 Eliminando token corrupto...")
                    try:
                        os.remove(self.token_path)
                        logger.info("✅ Token eliminado, se generará uno nuevo")
                    except:
                        pass
                    self.creds = None
            
            # Si no hay credenciales válidas
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    try:
                        # Intentar refrescar token
                        self.creds.refresh(Request())
                        logger.info("🔄 Token refrescado exitosamente")
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo refrescar token: {e}")
                        
                        # Si el refresh falla, eliminar token y crear uno nuevo
                        logger.info("🔄 Generando nuevo token...")
                        try:
                            os.remove(self.token_path)
                        except:
                            pass
                        
                        # Forzar nueva autenticación
                        self.creds = None
                        
                # Si aún no hay credenciales, hacer flujo completo
                if not self.creds or not self.creds.valid:
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"❌ No se encontró: {self.credentials_path}")
                        logger.error("📋 Descarga credentials.json desde Google Cloud Console")
                        logger.error("   1. Ve a https://console.cloud.google.com/")
                        logger.error("   2. Habilita Google Drive API y Google Sheets API")
                        logger.error("   3. Crea credenciales OAuth 2.0")
                        logger.error("   4. Descarga y guarda como config/credentials.json")
                        return False
                    
                    logger.info("🌐 Iniciando flujo de autorización...")
                    logger.info("📌 Se abrirá el navegador para autorizar")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path,
                        self.config.scopes
                    )
                    
                    # Intentar con diferentes puertos si el 0 no funciona
                    try:
                        self.creds = flow.run_local_server(port=0)
                    except Exception as e:
                        logger.warning(f"⚠️ Error con puerto automático: {e}")
                        logger.info("🔄 Intentando con puerto 8080...")
                        try:
                            self.creds = flow.run_local_server(port=8080)
                        except:
                            logger.info("🔄 Intentando con puerto 8090...")
                            self.creds = flow.run_local_server(port=8090)
                    
                    logger.info("✅ Nueva autenticación completada")
                
                # Guardar token para próximas ejecuciones
                if self.creds:
                    with open(self.token_path, 'w') as token:
                        token.write(self.creds.to_json())
                    logger.info(f"💾 Token guardado en: {self.token_path}")
            
            # Construir servicios
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
            
            # Verificar que los servicios funcionan
            try:
                # Prueba simple: listar archivos (límite 1)
                self.drive_service.files().list(pageSize=1).execute()
                logger.info("✅ Conexión con Google Drive verificada")
            except Exception as e:
                logger.error(f"❌ Error verificando conexión: {e}")
                return False
            
            logger.info("✅ Servicios de Google inicializados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error de autenticación: {e}")
            
            # Si es error de grant inválido, sugerir solución
            if "invalid_grant" in str(e):
                logger.error("🔧 SOLUCIÓN:")
                logger.error("   1. Elimina el archivo: config/token.json")
                logger.error("   2. Ejecuta el programa nuevamente")
                logger.error("   3. Autoriza en el navegador cuando se abra")
            
            return False
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Crea una carpeta en Google Drive
        
        Args:
            folder_name: Nombre de la carpeta
            parent_id: ID de la carpeta padre (opcional)
            
        Returns:
            ID de la carpeta creada
        """
        if not self.drive_service:
            if not self.authenticate():
                return None
        
        try:
            # Verificar si ya existe
            existing = self._find_folder(folder_name, parent_id)
            if existing:
                logger.info(f"📁 Carpeta ya existe: {folder_name}")
                return existing
            
            # Crear metadata de la carpeta
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            # Crear carpeta
            folder = self.drive_service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"✅ Carpeta creada: {folder_name} (ID: {folder_id})")
            
            # Cachear
            self.folder_cache[folder_name] = folder_id
            
            return folder_id
            
        except HttpError as e:
            logger.error(f"❌ Error creando carpeta: {e}")
            return None
    
    def create_folder_path(self, path: str) -> Optional[str]:
        """
        Crea una ruta completa de carpetas
        
        Args:
            path: Ruta de carpetas separadas por /
            
        Returns:
            ID de la última carpeta creada
        """
        if not self.drive_service:
            if not self.authenticate():
                return None
        
        try:
            parts = path.split('/')
            parent_id = None
            
            for part in parts:
                if part:
                    parent_id = self.create_folder(part, parent_id)
                    if not parent_id:
                        return None
            
            return parent_id
            
        except Exception as e:
            logger.error(f"❌ Error creando ruta de carpetas: {e}")
            return None
    
    def upload_file(self, 
                   content: Union[bytes, str],
                   filename: str,
                   folder_id: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Sube un archivo a Google Drive
        
        Args:
            content: Contenido del archivo (bytes o path)
            filename: Nombre del archivo
            folder_id: ID de la carpeta destino
            metadata: Metadata adicional
            
        Returns:
            ID del archivo subido
        """
        if not self.drive_service:
            if not self.authenticate():
                return None
        
        try:
            # Preparar metadata
            file_metadata = {'name': filename}
            
            if folder_id:
                file_metadata['parents'] = [folder_id]
            
            
            if metadata:
                # Solo incluir propiedades cortas y esenciales
                limited_metadata = {}
                
                # Campos permitidos con valores cortos
                if 'invoice_number' in metadata:
                    # Limitar a 20 caracteres
                    inv_num = str(metadata['invoice_number'])[:20]
                    if inv_num:
                        limited_metadata['inv'] = inv_num
                
                if 'vendor' in metadata:
                    # Limitar vendor a 30 caracteres
                    vendor = str(metadata['vendor'])[:30]
                    if vendor:
                        limited_metadata['vnd'] = vendor
                
                if 'amount' in metadata:
                    # Solo el monto como string corto
                    amount = str(metadata['amount'])[:15]
                    if amount:
                        limited_metadata['amt'] = amount
                
                # Solo agregar si el total es menor a 100 bytes
                total_size = sum(len(k) + len(v) for k, v in limited_metadata.items())
                if total_size < 100:  # Dejar margen de seguridad
                    file_metadata['properties'] = limited_metadata
                else:
                    logger.debug("Metadata muy larga, omitiendo propiedades personalizadas")
            
            
            # Determinar tipo MIME
            mime_type = self._get_mime_type(filename)
            
            # Crear media upload
            if isinstance(content, bytes):
                media = MediaIoBaseUpload(
                    io.BytesIO(content),
                    mimetype=mime_type,
                    resumable=True
                )
            else:
                # Si es un path
                media = MediaFileUpload(
                    content,
                    mimetype=mime_type,
                    resumable=True
                )
            
            # Subir archivo
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.info(f"✅ Archivo subido: {filename} (ID: {file_id})")
            
            return file_id
            
        except HttpError as e:
            logger.error(f"❌ Error subiendo archivo: {e}")
            return None
    
    
    
    def get_or_create_spreadsheet(self, name: str, folder_id: Optional[str] = None) -> Optional[str]:
        """
        Obtiene o crea una hoja de cálculo dentro de la carpeta DOCUFIND
        
        Args:
            name: Nombre de la hoja
            folder_id: ID de la carpeta (si no se especifica, usa carpeta raíz DOCUFIND)
            
        Returns:
            ID de la hoja de cálculo
        """
        if not self.sheets_service:
            if not self.authenticate():
                return None
        
        try:
            # Si no se especifica folder_id, crear/obtener carpeta raíz DOCUFIND
            if not folder_id:
                # Crear carpeta DOCUFIND si no existe
                root_folder_name = self.config.root_folder or "DOCUFIND"
                folder_id = self.create_folder(root_folder_name)
                
                if not folder_id:
                    logger.error("❌ No se pudo crear carpeta raíz DOCUFIND")
                    return None
                    
                logger.info(f"📁 Usando carpeta raíz: {root_folder_name}")
            
            # Buscar si la hoja ya existe en la carpeta
            query = f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            query += " and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                spreadsheet_id = files[0]['id']
                logger.info(f"📊 Hoja existente encontrada: {name}")
                return spreadsheet_id
            
            # Crear nueva hoja
            logger.info(f"📊 Creando nueva hoja: {name}")
            
            spreadsheet = {
                'properties': {
                    'title': name
                },
                'sheets': [{
                    'properties': {
                        'title': 'Datos',
                        'gridProperties': {
                            'rowCount': 10000,  # Más filas
                            'columnCount': 30   # Más columnas para todos los campos
                        }
                    }
                }]
            }
            
            sheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = sheet['spreadsheetId']
            
            # IMPORTANTE: Mover la hoja a la carpeta DOCUFIND
            if folder_id:
                # Obtener los padres actuales
                file = self.drive_service.files().get(
                    fileId=spreadsheet_id,
                    fields='parents'
                ).execute()
                
                previous_parents = ",".join(file.get('parents', []))
                
                # Mover a la carpeta DOCUFIND
                self.drive_service.files().update(
                    fileId=spreadsheet_id,
                    addParents=folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
                
                logger.info(f"✅ Hoja movida a carpeta DOCUFIND")
            
            # Agregar headers ampliados
            self._add_spreadsheet_headers(spreadsheet_id)
            
            logger.info(f"✅ Hoja de cálculo creada: {name} (ID: {spreadsheet_id})")
            return spreadsheet_id
            
        except HttpError as e:
            logger.error(f"❌ Error con hoja de cálculo: {e}")
            return None
    
    
    
    def append_to_spreadsheet(self, spreadsheet_id: str, row_data: List[Any]) -> bool:
        """
        Agrega una fila a la hoja de cálculo
        
        Args:
            spreadsheet_id: ID de la hoja
            row_data: Datos de la fila
            
        Returns:
            True si se agregó exitosamente
        """
        if not self.sheets_service:
            if not self.authenticate():
                return False
        
        try:
            # IMPORTANTE: Limpiar datos para evitar caracteres especiales problemáticos
            cleaned_data = []
            for item in row_data:
                if item is None:
                    cleaned_data.append('')
                elif isinstance(item, str):
                    # Limpiar caracteres especiales
                    clean_item = item.encode('utf-8', 'ignore').decode('utf-8')
                    # Reemplazar saltos de línea
                    clean_item = clean_item.replace('\\n', ' ').replace('\\r', ' ')
                    # Limitar longitud
                    if len(clean_item) > 500:
                        clean_item = clean_item[:497] + '...'
                    cleaned_data.append(clean_item)
                else:
                    cleaned_data.append(str(item))
            
            # Preparar body para la API
            body = {'values': [cleaned_data]}
            
            # IMPORTANTE: Usar A:T para 20 columnas exactas
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Datos!A:T',  # Específicamente columnas A hasta T
                valueInputOption='USER_ENTERED',  # Permite formato automático
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Fila agregada en posición {result.get('updates', {}).get('updatedRange', 'desconocida')}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Error agregando fila: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado: {e}")
            return False
    
    def list_files_in_folder(self, folder_id: str, mime_type: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Lista archivos en una carpeta
        
        Args:
            folder_id: ID de la carpeta
            mime_type: Tipo MIME específico (opcional)
            
        Returns:
            Lista de archivos con su información
        """
        if not self.drive_service:
            if not self.authenticate():
                return []
        
        try:
            query = f"'{folder_id}' in parents"
            
            if mime_type:
                query += f" and mimeType='{mime_type}'"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, modifiedTime, size)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"📋 {len(files)} archivos encontrados en la carpeta")
            
            return files
            
        except HttpError as e:
            logger.error(f"❌ Error listando archivos: {e}")
            return []
    
    def download_file(self, file_id: str) -> Optional[bytes]:
        """
        Descarga un archivo de Google Drive
        
        Args:
            file_id: ID del archivo
            
        Returns:
            Contenido del archivo en bytes
        """
        if not self.drive_service:
            if not self.authenticate():
                return None
        
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            content = request.execute()
            
            logger.info(f"✅ Archivo descargado: {len(content)} bytes")
            return content
            
        except HttpError as e:
            logger.error(f"❌ Error descargando archivo: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """
        Elimina un archivo o carpeta
        
        Args:
            file_id: ID del archivo o carpeta
            
        Returns:
            True si se eliminó exitosamente
        """
        if not self.drive_service:
            if not self.authenticate():
                return False
        
        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"✅ Archivo/carpeta eliminado")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Error eliminando: {e}")
            return False
    
    def _find_folder(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Busca una carpeta por nombre"""
        try:
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            query += " and trashed=false"  # No buscar en papelera
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            
            if files:
                return files[0]['id']
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error buscando carpeta: {e}")
            return None
    
    def _get_mime_type(self, filename: str) -> str:
        """Determina el tipo MIME basado en la extensión"""
        extension = os.path.splitext(filename)[1].lower()
        
        mime_types = {
            '.pdf': 'application/pdf',
            '.txt': 'text/plain',
            '.csv': 'text/csv',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            '.xls': 'application/vnd.ms-excel',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xml': 'application/xml',
            '.json': 'application/json',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.html': 'text/html',
            '.zip': 'application/zip'
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    


    def _add_spreadsheet_headers(self, spreadsheet_id: str):
        """Agrega headers a una hoja de cálculo nueva"""
        if not self.sheets_service:
            if not self.authenticate():
                return False
        
        try:
            # Headers completos para todos los campos
            headers = [
                'Fecha Procesamiento',
                'Fecha Email',
                'Remitente',
                'Asunto',
                'Tiene Adjuntos',
                'Cantidad Adjuntos',
                'Nombres Adjuntos',
                'Fecha Factura',
                'Proveedor',
                'Número Factura',
                'Concepto',
                'Subtotal',
                'Impuestos',
                'Total',
                'Moneda',
                'Método Pago',
                'Categoría',
                'Estado',
                'Confianza',
                'Link Archivo'
            ]
            
            # Preparar datos para actualizar
            body = {'values': [headers]}
            
            # Actualizar la primera fila con headers
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Datos!A1:T1',  # 20 columnas
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Formatear la primera fila
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True,
                                'fontSize': 11
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.95
                            },
                            'horizontalAlignment': 'CENTER'
                        }
                    },
                    'fields': 'userEnteredFormat'
                }
            },
            {
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 20
                    }
                }
            },
            {
                'updateSheetProperties': {
                    'properties': {
                        'sheetId': 0,
                        'gridProperties': {
                            'frozenRowCount': 1
                        }
                    },
                    'fields': 'gridProperties.frozenRowCount'
                }
            }]
            
            body = {'requests': requests}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("✅ Headers agregados y formateados correctamente")
            return True
            
        except Exception as e:
            logger.error(f"⚠️ Error agregando headers: {e}")
            return False

    
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

    
    
    
    
    
    
    
    
    
    
    
            
    def search_files(self, query: str, max_results: int = 10) -> List[Dict[str, str]]:
        """
        Busca archivos en Google Drive
        
        Args:
            query: Query de búsqueda
            max_results: Número máximo de resultados
            
        Returns:
            Lista de archivos encontrados
        """
        if not self.drive_service:
            if not self.authenticate():
                return []
        
        try:
            results = self.drive_service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, mimeType, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            logger.info(f"🔍 {len(files)} archivos encontrados")
            
            return files
            
        except HttpError as e:
            logger.error(f"❌ Error buscando archivos: {e}")
            return []
    
    def get_file_metadata(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene metadata de un archivo
        
        Args:
            file_id: ID del archivo
            
        Returns:
            Metadata del archivo
        """
        if not self.drive_service:
            if not self.authenticate():
                return None
        
        try:
            file = self.drive_service.files().get(
                fileId=file_id,
                fields='*'
            ).execute()
            
            return file
            
        except HttpError as e:
            logger.error(f"❌ Error obteniendo metadata: {e}")
            return None

# Funciones de utilidad
def test_authentication(credentials_path: str = "./config/credentials.json") -> bool:
    """
    Prueba la autenticación con Google Drive
    
    Args:
        credentials_path: Ruta al archivo de credenciales
        
    Returns:
        True si la autenticación es exitosa
    """
    client = GoogleDriveClient(credentials_path=credentials_path)
    return client.authenticate()

def quick_upload(file_path: str, folder_name: str = "DOCUFIND") -> Optional[str]:
    """
    Sube rápidamente un archivo a Google Drive
    
    Args:
        file_path: Ruta del archivo a subir
        folder_name: Nombre de la carpeta destino
        
    Returns:
        ID del archivo subido
    """
    client = GoogleDriveClient()
    
    if not client.authenticate():
        return None
    
    # Crear carpeta si no existe
    folder_id = client.create_folder(folder_name)
    
    if not folder_id:
        return None
    
    # Subir archivo
    with open(file_path, 'rb') as f:
        content = f.read()
    
    filename = os.path.basename(file_path)
    return client.upload_file(content, filename, folder_id)


def main():
    """
    Muestra todas las correcciones necesarias
    """
    print("=" * 60)
    print("🔧 CORRECCIONES PARA MEJORAR LA HOJA DE EXCEL")
    print("=" * 60)
    
    print("\n📋 CAMBIOS NECESARIOS:")
    print("1. Actualizar headers de la hoja con campos del email")
    print("2. Crear la hoja en la carpeta raíz DOCUFIND")
    print("3. Capturar información de adjuntos")
    print("4. Actualizar el método de escritura")
    
    print("\n" + "=" * 60)
    print("📝 INSTRUCCIONES DE IMPLEMENTACIÓN:")
    print("=" * 60)
    
    print("\n1️⃣ EN google_drive_client.py:")
    print("   • Actualizar _add_spreadsheet_headers()")
    print("   • Actualizar get_or_create_spreadsheet()")
    print("   Los nuevos headers incluirán:")
    print("   - Fecha del correo")
    print("   - Remitente")
    print("   - Asunto")
    print("   - Información de adjuntos")
    
    print("\n2️⃣ EN find_documents_main.py:")
    print("   • Actualizar _update_spreadsheet()")
    print("   • Actualizar _process_single_email()")
    print("   • Pasar información del email completa")
    
    print("\n3️⃣ RESULTADO ESPERADO:")
    print("   La hoja tendrá estas columnas:")
    headers = [
        'Fecha Procesamiento', 'Fecha Email', 'Remitente', 'Asunto',
        'Tiene Adjuntos', 'Cantidad Adjuntos', 'Nombres Adjuntos',
        'Fecha Factura', 'Proveedor', 'Número Factura', 'Concepto',
        'Subtotal', 'Impuestos', 'Total', 'Moneda', 'Método Pago',
        'Categoría', 'Estado', 'Confianza Extracción', 'Link Archivo', 'Notas'
    ]
    
    for i, header in enumerate(headers, 1):
        print(f"   {i:2}. {header}")
    
    print("\n" + "=" * 60)
    print("💡 RESUMEN DE MEJORAS:")
    print("=" * 60)
    print("✅ La hoja se creará en la carpeta raíz DOCUFIND")
    print("✅ Se registrarán TODOS los emails (con y sin adjuntos)")
    print("✅ Se incluirá información completa del email")
    print("✅ Se listarán todos los nombres de adjuntos")
    print("✅ Headers con formato y colores")
    print("✅ Primera fila congelada para facilitar navegación")

if __name__ == "__main__":
    # Mostrar los códigos actualizados
    print("\n🔧 CÓDIGO ACTUALIZADO:")
    print("=" * 60)
    
    print("\n1. HEADERS ACTUALIZADOS:")
    print(update_spreadsheet_headers())
    
    print("\n2. CREAR SPREADSHEET EN CARPETA DOCUFIND:")
    print(update_get_or_create_spreadsheet())
    
    print("\n3. MÉTODO UPDATE_SPREADSHEET:")
    print(update_spreadsheet_method())
    
    print("\n4. PROCESO CON INFO DE ADJUNTOS:")
    print(update_process_single_email())
    
    main()
    
    
    