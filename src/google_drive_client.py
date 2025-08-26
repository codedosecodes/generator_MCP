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
        Autentica con Google Drive
        
        Returns:
            True si la autenticación fue exitosa
        """
        try:
            # Token existe y es válido
            if os.path.exists(self.token_path):
                self.creds = Credentials.from_authorized_user_file(
                    self.token_path, 
                    self.config.scopes
                )
                logger.info("🔑 Token existente cargado")
            
            # Si no hay credenciales válidas
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    # Refrescar token
                    self.creds.refresh(Request())
                    logger.info("🔄 Token refrescado")
                else:
                    # Flujo de autenticación inicial
                    if not os.path.exists(self.credentials_path):
                        logger.error(f"❌ No se encontró: {self.credentials_path}")
                        logger.error("Descarga credentials.json desde Google Cloud Console")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path,
                        self.config.scopes
                    )
                    self.creds = flow.run_local_server(port=0)
                    logger.info("✅ Nueva autenticación completada")
                
                # Guardar token para próximas ejecuciones
                with open(self.token_path, 'w') as token:
                    token.write(self.creds.to_json())
                logger.info(f"💾 Token guardado en: {self.token_path}")
            
            # Construir servicios
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
            
            logger.info("✅ Servicios de Google inicializados")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error de autenticación: {e}")
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
                file_metadata['properties'] = metadata
            
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
        Obtiene o crea una hoja de cálculo
        
        Args:
            name: Nombre de la hoja
            folder_id: ID de la carpeta
            
        Returns:
            ID de la hoja de cálculo
        """
        if not self.sheets_service:
            if not self.authenticate():
                return None
        
        try:
            # Buscar si existe
            query = f"name='{name}' and mimeType='application/vnd.google-apps.spreadsheet'"
            if folder_id:
                query += f" and '{folder_id}' in parents"
            
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
            spreadsheet = {
                'properties': {
                    'title': name
                },
                'sheets': [{
                    'properties': {
                        'title': 'Datos',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 20
                        }
                    }
                }]
            }
            
            sheet = self.sheets_service.spreadsheets().create(
                body=spreadsheet
            ).execute()
            
            spreadsheet_id = sheet['spreadsheetId']
            
            # Mover a carpeta si se especificó
            if folder_id:
                self.drive_service.files().update(
                    fileId=spreadsheet_id,
                    addParents=folder_id,
                    fields='id, parents'
                ).execute()
            
            # Agregar headers
            self._add_spreadsheet_headers(spreadsheet_id)
            
            logger.info(f"✅ Hoja de cálculo creada: {name}")
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
            # Agregar fila
            body = {'values': [row_data]}
            
            self.sheets_service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range='Datos!A:Z',
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"✅ Fila agregada a hoja de cálculo")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Error agregando fila: {e}")
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
        try:
            headers = [
                'Fecha Procesamiento',
                'Fecha Factura',
                'Proveedor',
                'Número Factura',
                'Subtotal',
                'Impuestos',
                'Total',
                'Moneda',
                'Método Pago',
                'Estado',
                'Link Archivo',
                'Categoría',
                'Notas'
            ]
            
            body = {'values': [headers]}
            
            self.sheets_service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id,
                range='Datos!A1:M1',
                valueInputOption='RAW',
                body=body
            ).execute()
            
            # Formatear headers (negrita)
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
                                'bold': True
                            },
                            'backgroundColor': {
                                'red': 0.9,
                                'green': 0.9,
                                'blue': 0.9
                            }
                        }
                    },
                    'fields': 'userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColor'
                }
            }]
            
            # Ajustar ancho de columnas
            requests.append({
                'autoResizeDimensions': {
                    'dimensions': {
                        'sheetId': 0,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 13
                    }
                }
            })
            
            body = {'requests': requests}
            self.sheets_service.spreadsheets().batchUpdate(
                spreadsheetId=spreadsheet_id,
                body=body
            ).execute()
            
            logger.info("✅ Headers agregados y formateados")
            
        except Exception as e:
            logger.error(f"⚠️ Error agregando headers: {e}")
    
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

if __name__ == "__main__":
    # Prueba básica
    print("🧪 Probando GoogleDriveClient...")
    print("=" * 60)
    
    # Configuración de prueba
    test_config = {
        'credentials_path': './config/credentials.json',
        'token_path': './config/token.json',
        'drive_folder_root': 'DOCUFIND'
    }
    
    client = GoogleDriveClient(config=test_config)
    print(f"✅ GoogleDriveClient creado")
    print(f"📁 Carpeta raíz: {client.config.root_folder}")
    
    # Probar autenticación si hay credenciales
    if os.path.exists(test_config['credentials_path']):
        if client.authenticate():
            print("✅ Autenticación exitosa")
            
            # Prueba rápida
            print("\n🧪 Prueba rápida:")
            test_folder = f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            folder_id = client.create_folder(test_folder)
            
            if folder_id:
                print(f"✅ Carpeta creada: {test_folder}")
                
                # Subir archivo de prueba
                test_content = b"Este es un archivo de prueba de DOCUFIND"
                file_id = client.upload_file(
                    test_content,
                    "test.txt",
                    folder_id
                )
                
                if file_id:
                    print(f"✅ Archivo subido exitosamente")
                    print(f"\n📁 Ve tu Google Drive y busca la carpeta: {test_folder}")
        else:
            print("❌ Error de autenticación")
    else:
        print("⚠️ No se encontró credentials.json")
        print("   Descárgalo desde Google Cloud Console")