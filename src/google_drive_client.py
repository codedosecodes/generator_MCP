"""
Google Drive Client - FIND_DOCUMENTS
Maneja la organización automática de documentos en Google Drive y Google Sheets
"""

import os
import json
import base64
import io
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleDriveClient:
    """Cliente para manejar Google Drive y Google Sheets"""
    
    # Scopes necesarios
    SCOPES = [
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.drive_service = None
        self.sheets_service = None
        self.credentials = None
        
        logger.info("🔗 GoogleDriveClient inicializado")
    
    async def initialize(self):
        """Inicializa los servicios de Google Drive y Sheets"""
        try:
            logger.info("🔐 Inicializando servicios de Google...")
            
            # Cargar o crear credenciales
            self.credentials = self._load_or_create_credentials()
            
            # Crear servicios
            self.drive_service = build('drive', 'v3', credentials=self.credentials)
            self.sheets_service = build('sheets', 'v4', credentials=self.credentials)
            
            # Probar conexión
            await self._test_connection()
            
            logger.info("✅ Servicios de Google inicializados correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando servicios Google: {e}")
            raise
    
    def _load_or_create_credentials(self) -> Credentials:
        """Carga credenciales existentes o crea nuevas"""
        creds = None
        
        # Cargar token existente
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)
                logger.info("🔑 Token existente cargado")
            except Exception as e:
                logger.warning(f"⚠️  Token existente inválido: {e}")
        
        # Si no hay credenciales válidas, obtenerlas
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("🔄 Renovando token expirado...")
                try:
                    creds.refresh(Request())
                    logger.info("✅ Token renovado exitosamente")
                except Exception as e:
                    logger.error(f"❌ Error renovando token: {e}")
                    creds = None
            
            if not creds:
                logger.info("🌐 Iniciando flujo de autorización OAuth...")
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(f"Archivo de credenciales no encontrado: {self.credentials_path}")
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)
                logger.info("✅ Autorización completada")
            
            # Guardar credenciales para uso futuro
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"💾 Token guardado en {self.token_path}")
        
        return creds
    
    async def _test_connection(self):
        """Prueba la conexión con los servicios"""
        try:
            # Probar Drive API
            about = self.drive_service.about().get(fields='user').execute()
            user_email = about['user']['emailAddress']
            logger.info(f"✅ Google Drive conectado como: {user_email}")
            
            # Probar Sheets API obteniendo info básica
            # No hacemos una llamada real aquí para evitar crear hojas innecesarias
            logger.info("✅ Google Sheets API disponible")
            
        except HttpError as e:
            logger.error(f"❌ Error de API de Google: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error probando conexión: {e}")
            raise
    
    async def create_or_get_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """Crea una carpeta o obtiene su ID si ya existe"""
        try:
            # Construir query de búsqueda
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            # Buscar carpeta existente
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                logger.debug(f"📁 Carpeta '{folder_name}' ya existe: {folder_id}")
                return folder_id
            
            # Crear nueva carpeta
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.drive_service.files().create(
                body=folder_metadata,
                fields='id'
            ).execute()
            
            folder_id = folder.get('id')
            logger.info(f"📁 Carpeta '{folder_name}' creada: {folder_id}")
            return folder_id
            
        except HttpError as e:
            logger.error(f"❌ Error API creando carpeta {folder_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error creando carpeta {folder_name}: {e}")
            raise
    
    async def upload_file(self, file_content: str, filename: str, parent_folder_id: str, 
                         content_type: str = 'application/octet-stream') -> str:
        """Sube un archivo a Google Drive"""
        try:
            # Decodificar contenido base64
            file_data = base64.b64decode(file_content)
            
            # Crear stream de datos
            file_stream = io.BytesIO(file_data)
            
            # Metadata del archivo
            file_metadata = {
                'name': filename,
                'parents': [parent_folder_id]
            }
            
            # Media upload
            media = MediaIoBaseUpload(
                file_stream,
                mimetype=content_type,
                resumable=True
            )
            
            # Subir archivo
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            logger.debug(f"📎 Archivo '{filename}' subido: {file_id}")
            return file_id
            
        except HttpError as e:
            logger.error(f"❌ Error API subiendo {filename}: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error subiendo {filename}: {e}")
            raise
    
    async def create_spreadsheet(self, title: str, parent_folder_id: str, 
                                headers: List[str]) -> str:
        """Crea una hoja de cálculo con headers"""
        try:
            # Crear hoja de cálculo
            spreadsheet_body = {
                'properties': {
                    'title': title
                },
                'sheets': [{
                    'properties': {
                        'title': 'Documentos Procesados'
                    }
                }]
            }
            
            spreadsheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet_body
            ).execute()
            
            spreadsheet_id = spreadsheet['spreadsheetId']
            logger.info(f"📊 Hoja de cálculo '{title}' creada: {spreadsheet_id}")
            
            # Mover a carpeta específica
            self.drive_service.files().update(
                fileId=spreadsheet_id,
                addParents=parent_folder_id,
                removeParents='root'
            ).execute()
            
            # Agregar headers
            if headers:
                await self._write_headers_to_sheet(spreadsheet_id, headers)
            
            logger.info(f"✅ Hoja de cálculo configurada con {len(headers)} columnas")
            return spreadsheet_id
            
        except HttpError as e:
            logger.error(f"❌ Error API creando hoja de cálculo: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error creando hoja de cálculo: {e}")
            raise
    
    async def _write_headers_to_sheet(self, spreadsheet_id: str, headers: List[str]):
        """Escribe headers en la primera fila de la hoja"""
        try:
            # Preparar datos
            values = [headers]
            body = {
                'values': values
            }
            
            # Escribir headers
            range_name = f'A1:{chr(65 + len(headers) - 1)}1'  # A1:K1, etc.
            
            result = self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption='USER_ENTERED',
                body=body
            ).execute()
            
            # Formatear headers (negrita)
            await self._format_header_row(spreadsheet_id, len(headers))
            
            logger.debug(f"📋 Headers escritos en rango {range_name}")
            
        except HttpError as e:
            logger.error(f"❌ Error API escribiendo headers: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error escribiendo headers: {e}")
            raise
    
    async def _format_header_row(self, spreadsheet_id: str, num_columns: int):
        """Formatea la fila de headers (negrita, color de fondo)"""
        try:
            requests = [{
                'repeatCell': {
                    'range': {
                        'sheetId': 0,
                        'startRowIndex': 0,
                        'endRowIndex': 1,
                        'startColumnIndex': 0,
                        'endColumnIndex': num_columns
                    },
                    'cell': {
                        'userEnteredFormat': {
                            'textFormat': {
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat(textFormat,backgroundColor)'
                }
            }]
            
            body = {
                'requests': requests
            }
            
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            logger.debug("✨ Formato aplicado a headers")
            
        except Exception as e:
            logger.warning(f"⚠️  Error aplicando formato a headers: {e}")
    
    async def append_to_spreadsheet(self, spreadsheet_id: str, rows_data: List[List[str]]):
        """Agrega filas de datos a la hoja de cálculo"""
        try:
            if not rows_data:
                logger.warning("⚠️  No hay datos para agregar a la hoja")
                return
            
            body = {
                'values': rows_data
            }
            
            result = self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='A:Z',  # Rango amplio para permitir muchas columnas
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            updates = result.get('updates', {})
            rows_added = updates.get('updatedRows', 0)
            
            logger.info(f"📊 {rows_added} filas agregadas a la hoja de cálculo")
            
        except HttpError as e:
            logger.error(f"❌ Error API agregando datos: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error agregando datos a hoja: {e}")
            raise
    
    async def get_folder_structure(self, root_folder_name: str = 'FIND_DOCUMENTS') -> Dict[str, Any]:
        """Obtiene la estructura de carpetas creada"""
        try:
            # Buscar carpeta raíz
            query = f"name='{root_folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.drive_service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if not folders:
                return {'error': f'Carpeta {root_folder_name} no encontrada'}
            
            root_folder = folders[0]
            structure = await self._get_folder_contents_recursive(
                root_folder['id'], 
                root_folder['name']
            )
            
            return structure
            
        except Exception as e:
            logger.error(f"❌ Error obteniendo estructura: {e}")
            return {'error': str(e)}
    
    async def _get_folder_contents_recursive(self, folder_id: str, folder_name: str) -> Dict[str, Any]:
        """Obtiene contenidos de carpeta recursivamente"""
        try:
            query = f"'{folder_id}' in parents and trashed=false"
            results = self.drive_service.files().list(
                q=query,
                fields="files(id, name, mimeType, size, modifiedTime, webViewLink)"
            ).execute()
            
            contents = {
                'name': folder_name,
                'id': folder_id,
                'type': 'folder',
                'folders': [],
                'files': [],
                'spreadsheets': []
            }
            
            for item in results.get('files', []):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Carpeta - obtener contenido recursivo
                    subfolder = await self._get_folder_contents_recursive(
                        item['id'], 
                        item['name']
                    )
                    contents['folders'].append(subfolder)
                
                elif item['mimeType'] == 'application/vnd.google-apps.spreadsheet':
                    # Hoja de cálculo
                    contents['spreadsheets'].append({
                        'name': item['name'],
                        'id': item['id'],
                        'modified': item.get('modifiedTime', ''),
                        'link': item.get('webViewLink', '')
                    })
                
                else:
                    # Archivo regular
                    contents['files'].append({
                        'name': item['name'],
                        'id': item['id'],
                        'size': item.get('size', '0'),
                        'modified': item.get('modifiedTime', ''),
                        'link': item.get('webViewLink', '')
                    })
            
            return contents
            
        except HttpError as e:
            logger.error(f"❌ Error API obteniendo contenidos de {folder_name}: {e}")
            return {
                'name': folder_name,
                'id': folder_id,
                'error': str(e)
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo contenidos de {folder_name}: {e}")
            return {
                'name': folder_name,
                'id': folder_id,
                'error': str(e)
            }
    
    async def get_spreadsheet_data(self, spreadsheet_id: str, range_name: str = 'A:Z') -> Dict[str, Any]:
        """Obtiene datos de una hoja de cálculo"""
        try:
            result = self.sheets_service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            return {
                'total_rows': len(values),
                'headers': values[0] if values else [],
                'data_rows': values[1:] if len(values) > 1 else [],
                'range': range_name
            }
            
        except HttpError as e:
            logger.error(f"❌ Error API obteniendo datos de hoja: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"❌ Error obteniendo datos de hoja: {e}")
            return {'error': str(e)}
    
    async def share_file_or_folder(self, file_id: str, email_address: str, role: str = 'reader'):
        """Comparte un archivo o carpeta con un usuario específico"""
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email_address
            }
            
            self.drive_service.permissions().create(
                fileId=file_id,
                body=permission,
                sendNotificationEmail=False
            ).execute()
            
            logger.info(f"🔗 Archivo/carpeta {file_id} compartido con {email_address} como {role}")
            
        except HttpError as e:
            logger.error(f"❌ Error API compartiendo archivo: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error compartiendo archivo: {e}")
            raise
    
    async def get_file_info(self, file_id: str) -> Dict[str, Any]:
        """Obtiene información detallada de un archivo"""
        try:
            file_info = self.drive_service.files().get(
                fileId=file_id,
                fields="id,name,mimeType,size,createdTime,modifiedTime,webViewLink,parents"
            ).execute()
            
            return file_info
            
        except HttpError as e:
            logger.error(f"❌ Error API obteniendo info de archivo: {e}")
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"❌ Error obteniendo info de archivo: {e}")
            return {'error': str(e)}
    
    async def cleanup_old_files(self, folder_id: str, days_old: int = 30):
        """Limpia archivos antiguos de una carpeta específica"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.now() - timedelta(days=days_old)
            cutoff_date_str = cutoff_date.strftime('%Y-%m-%dT%H:%M:%S')
            
            query = f"'{folder_id}' in parents and modifiedTime < '{cutoff_date_str}' and trashed=false"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            cleaned_count = 0
            
            for file in files:
                try:
                    self.drive_service.files().delete(fileId=file['id']).execute()
                    cleaned_count += 1
                    logger.info(f"🗑️  Archivo antiguo eliminado: {file['name']}")
                except Exception as e:
                    logger.warning(f"⚠️  No se pudo eliminar {file['name']}: {e}")
            
            logger.info(f"🧹 Limpieza completada: {cleaned_count} archivos eliminados")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"❌ Error en limpieza: {e}")
            return 0
    
    def get_service_status(self) -> Dict[str, Any]:
        """Obtiene estado de los servicios"""
        return {
            'drive_service_available': self.drive_service is not None,
            'sheets_service_available': self.sheets_service is not None,
            'credentials_valid': self.credentials and self.credentials.valid,
            'credentials_expired': self.credentials and self.credentials.expired,
            'token_path': self.token_path,
            'credentials_path': self.credentials_path
        }

# Funciones de utilidad
async def test_google_services(credentials_path: str, token_path: str) -> Dict[str, Any]:
    """Prueba los servicios de Google Drive y Sheets"""
    try:
        client = GoogleDriveClient(credentials_path, token_path)
        await client.initialize()
        
        # Obtener información del usuario
        about = client.drive_service.about().get(fields='user,storageQuota').execute()
        user = about.get('user', {})
        quota = about.get('storageQuota', {})
        
        return {
            'success': True,
            'user_email': user.get('emailAddress', 'Unknown'),
            'user_name': user.get('displayName', 'Unknown'),
            'storage_used': quota.get('usage', 'Unknown'),
            'storage_limit': quota.get('limit', 'Unknown'),
            'services': {
                'drive': True,
                'sheets': True
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error probando servicios Google: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def format_file_size(size_bytes: str) -> str:
    """Formatea tamaño de archivo en formato legible"""
    try:
        size = int(size_bytes)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except (ValueError, TypeError):
        return "Unknown size"

def validate_google_credentials_file(credentials_path: str) -> List[str]:
    """Valida archivo de credenciales de Google"""
    errors = []
    
    if not os.path.exists(credentials_path):
        errors.append(f"Archivo de credenciales no existe: {credentials_path}")
        return errors
    
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        # Validar estructura
        if 'installed' not in creds_data and 'web' not in creds_data:
            errors.append("Formato de credenciales inválido: debe tener 'installed' or 'web'")
        
        # Validar campos requeridos
        creds = creds_data.get('installed', creds_data.get('web', {}))
        required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
        
        for field in required_fields:
            if field not in creds:
                errors.append(f"Campo requerido faltante: {field}")
        
    except json.JSONDecodeError:
        errors.append("Archivo de credenciales no es un JSON válido")
    except Exception as e:
        errors.append(f"Error leyendo credenciales: {str(e)}")
    
    return errors