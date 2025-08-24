"""
Config Manager - FIND_DOCUMENTS
Maneja la configuración de la aplicación desde archivos JSON y variables de entorno
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
from dataclasses import dataclass

# Importar para variables de entorno
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    logging.warning("⚠️  python-dotenv no disponible, usando solo variables de entorno del sistema")

logger = logging.getLogger(__name__)

@dataclass
class EmailConfig:
    """Configuración de email"""
    server: str
    port: int
    username: str
    password: str
    
    def validate(self) -> List[str]:
        """Valida la configuración de email"""
        errors = []
        if not self.server:
            errors.append("Servidor de email requerido")
        if not self.username:
            errors.append("Usuario de email requerido")
        if not self.password:
            errors.append("Contraseña de email requerida")
        if self.port not in [143, 993, 587, 25, 465]:
            errors.append("Puerto de email debe ser uno de: 143, 993, 587, 25, 465")
        return errors

@dataclass
class SearchParams:
    """Parámetros de búsqueda"""
    start_date: str
    end_date: str
    keywords: List[str]
    folder_name: str
    
    def validate(self) -> List[str]:
        """Valida los parámetros de búsqueda"""
        errors = []
        
        # Validar fechas
        try:
            start = datetime.strptime(self.start_date, "%Y-%m-%d")
            end = datetime.strptime(self.end_date, "%Y-%m-%d")
            
            if start >= end:
                errors.append("Fecha de inicio debe ser anterior a fecha final")
            
            if (end - start).days > 365:
                errors.append("Rango de fechas no debe exceder 365 días")
                
        except ValueError:
            errors.append("Fechas deben estar en formato YYYY-MM-DD")
        
        # Validar palabras clave
        if not self.keywords or not any(self.keywords):
            errors.append("Al menos una palabra clave es requerida")
        
        # Validar nombre de carpeta
        if not self.folder_name or len(self.folder_name.strip()) == 0:
            errors.append("Nombre de carpeta es requerido")
        
        return errors

@dataclass
class GoogleServicesConfig:
    """Configuración de servicios Google"""
    credentials_path: str
    token_path: str
    drive_folder_root: str = "FIND_DOCUMENTS"
    
    def validate(self) -> List[str]:
        """Valida la configuración de Google"""
        errors = []
        
        if not os.path.exists(self.credentials_path):
            errors.append(f"Archivo de credenciales no existe: {self.credentials_path}")
        
        # Validar que el directorio del token sea escribible
        token_dir = os.path.dirname(self.token_path)
        if not os.path.exists(token_dir):
            try:
                os.makedirs(token_dir, exist_ok=True)
            except Exception as e:
                errors.append(f"No se puede crear directorio para token: {e}")
        
        return errors

@dataclass
class ProcessingOptions:
    """Opciones de procesamiento"""
    max_emails: int = 1000
    enable_ai_extraction: bool = True
    create_backup: bool = True
    send_completion_report: bool = True
    timeout_seconds: int = 300
    
    def validate(self) -> List[str]:
        """Valida las opciones de procesamiento"""
        errors = []
        
        if self.max_emails <= 0:
            errors.append("max_emails debe ser mayor a 0")
        elif self.max_emails > 10000:
            errors.append("max_emails no debe exceder 10,000")
            
        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds debe ser mayor a 0")
            
        return errors

@dataclass
class NotificationSettings:
    """Configuración de notificaciones"""
    email_reports: bool = False
    progress_updates: bool = True
    error_notifications: bool = True
    webhook_url: Optional[str] = None
    
    def validate(self) -> List[str]:
        """Valida las configuraciones de notificación"""
        errors = []
        
        if self.webhook_url and not self.webhook_url.startswith(('http://', 'https://')):
            errors.append("webhook_url debe ser una URL válida")
            
        return errors

class ConfigManager:
    """Gestor principal de configuración"""
    
    def __init__(self, config_path: str = "config/config.json"):
        self.config_path = config_path
        self.config_data = {}
        
        # Cargar variables de entorno
        if DOTENV_AVAILABLE:
            # Buscar archivo .env en varios lugares
            env_files = ['.env', '../.env', '../../.env']
            for env_file in env_files:
                if os.path.exists(env_file):
                    load_dotenv(env_file)
                    logger.info(f"🔧 Variables de entorno cargadas desde {env_file}")
                    break
        
        logger.info("🔧 ConfigManager inicializado")
    
    def load_config(self) -> Dict[str, Any]:
        """Carga la configuración completa"""
        try:
            # Cargar desde archivo JSON
            base_config = self._load_from_file()
            
            # Sobrescribir con variables de entorno
            merged_config = self._merge_with_env_vars(base_config)
            
            # Validar configuración
            self._validate_config(merged_config)
            
            # Aplicar configuraciones por defecto
            final_config = self._apply_defaults(merged_config)
            
            self.config_data = final_config
            logger.info("✅ Configuración cargada exitosamente")
            
            return final_config
            
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            raise
    
    def _load_from_file(self) -> Dict[str, Any]:
        """Carga configuración desde archivo JSON"""
        if not os.path.exists(self.config_path):
            logger.warning(f"⚠️  Archivo de configuración no existe: {self.config_path}")
            return self._get_default_config()
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            logger.info(f"📁 Configuración cargada desde {self.config_path}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error leyendo archivo de configuración: {e}")
            raise
    
    def _merge_with_env_vars(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Mezcla configuración con variables de entorno"""
        merged = config.copy()
        
        # Mapeo de variables de entorno a configuración
        env_mappings = {
            # Email credentials
            'EMAIL_USERNAME': ['email_credentials', 'username'],
            'EMAIL_PASSWORD': ['email_credentials', 'password'],
            'EMAIL_SERVER': ['email_credentials', 'server'],
            'EMAIL_PORT': ['email_credentials', 'port'],
            
            # Google services
            'GOOGLE_CREDENTIALS_PATH': ['google_services', 'credentials_path'],
            'GOOGLE_TOKEN_PATH': ['google_services', 'token_path'],
            'DRIVE_FOLDER_ROOT': ['google_services', 'drive_folder_root'],
            
            # Search parameters
            'DEFAULT_START_DATE': ['search_parameters', 'start_date'],
            'DEFAULT_END_DATE': ['search_parameters', 'end_date'],
            'DEFAULT_FOLDER_NAME': ['search_parameters', 'folder_name'],
            'DEFAULT_KEYWORDS': ['search_parameters', 'keywords'],
            
            # Processing options
            'MAX_EMAILS_PER_BATCH': ['processing_options', 'max_emails'],
            'ENABLE_AI_EXTRACTION': ['processing_options', 'enable_ai_extraction'],
            'AUTO_SEND_REPORT': ['processing_options', 'send_completion_report'],
            
            # Notification settings
            'EMAIL_REPORTS': ['notification_settings', 'email_reports'],
            'WEBHOOK_URL': ['notification_settings', 'webhook_url']
        }
        
        for env_var, config_path in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value:
                # Navegar y actualizar configuración anidada
                current = merged
                for key in config_path[:-1]:
                    if key not in current:
                        current[key] = {}
                    current = current[key]
                
                # Convertir tipos apropiados
                final_key = config_path[-1]
                current[final_key] = self._convert_env_value(env_value, final_key)
                
                logger.debug(f"🔧 Variable de entorno aplicada: {env_var} -> {'.'.join(config_path)}")
        
        return merged
    
    def _convert_env_value(self, value: str, key: str) -> Any:
        """Convierte valores de variables de entorno a tipos apropiados"""
        # Convertir booleanos
        if key in ['enable_ai_extraction', 'create_backup', 'send_completion_report', 
                   'email_reports', 'progress_updates', 'error_notifications']:
            return value.lower() in ('true', '1', 'yes', 'on')
        
        # Convertir enteros
        if key in ['port', 'max_emails', 'timeout_seconds']:
            try:
                return int(value)
            except ValueError:
                logger.warning(f"⚠️  No se pudo convertir {key}='{value}' a entero")
                return value
        
        # Convertir listas (keywords)
        if key == 'keywords':
            return [kw.strip() for kw in value.split(',') if kw.strip()]
        
        # Por defecto, devolver string
        return value
    
    def _validate_config(self, config: Dict[str, Any]):
        """Valida la configuración completa"""
        all_errors = []
        
        # Validar email credentials
        if 'email_credentials' in config:
            email_config = EmailConfig(**config['email_credentials'])
            all_errors.extend(email_config.validate())
        else:
            all_errors.append("Configuración de email requerida")
        
        # Validar search parameters
        if 'search_parameters' in config:
            search_config = SearchParams(**config['search_parameters'])
            all_errors.extend(search_config.validate())
        else:
            all_errors.append("Parámetros de búsqueda requeridos")
        
        # Validar Google services
        if 'google_services' in config:
            google_config = GoogleServicesConfig(**config['google_services'])
            all_errors.extend(google_config.validate())
        else:
            all_errors.append("Configuración de Google Services requerida")
        
        # Validar processing options
        if 'processing_options' in config:
            processing_config = ProcessingOptions(**config['processing_options'])
            all_errors.extend(processing_config.validate())
        
        # Validar notification settings
        if 'notification_settings' in config:
            notification_config = NotificationSettings(**config['notification_settings'])
            all_errors.extend(notification_config.validate())
        
        if all_errors:
            error_msg = "Errores de configuración:\n" + "\n".join(f"  - {error}" for error in all_errors)
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _apply_defaults(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Aplica valores por defecto donde sea necesario"""
        defaults = self._get_default_config()
        
        def merge_defaults(base: Dict, defaults: Dict) -> Dict:
            """Función recursiva para mezclar defaults"""
            result = base.copy()
            
            for key, value in defaults.items():
                if key not in result:
                    result[key] = value
                elif isinstance(value, dict) and isinstance(result[key], dict):
                    result[key] = merge_defaults(result[key], value)
            
            return result
        
        return merge_defaults(config, defaults)
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Obtiene configuración por defecto"""
        today = datetime.now()
        year_ago = today - timedelta(days=365)
        
        return {
            "email_credentials": {
                "server": "imap.gmail.com",
                "port": 993,
                "username": "",
                "password": ""
            },
            "search_parameters": {
                "start_date": year_ago.strftime("%Y-%m-%d"),
                "end_date": today.strftime("%Y-%m-%d"),
                "keywords": ["factura", "invoice", "bill", "receipt"],
                "folder_name": f"Documentos_{today.strftime('%Y_%m')}"
            },
            "processing_options": {
                "max_emails": 1000,
                "enable_ai_extraction": True,
                "create_backup": True,
                "send_completion_report": True,
                "timeout_seconds": 300
            },
            "google_services": {
                "credentials_path": "./config/credentials.json",
                "token_path": "./config/token.json",
                "drive_folder_root": "FIND_DOCUMENTS"
            },
            "notification_settings": {
                "email_reports": False,
                "progress_updates": True,
                "error_notifications": True,
                "webhook_url": None
            }
        }
    
    def save_config(self, config: Dict[str, Any] = None):
        """Guarda la configuración actual al archivo"""
        try:
            config_to_save = config or self.config_data
            
            # Crear directorio si no existe
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Guardar configuración
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"💾 Configuración guardada en {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
            raise
    
    def get_email_config(self) -> EmailConfig:
        """Obtiene configuración de email como dataclass"""
        return EmailConfig(**self.config_data['email_credentials'])
    
    def get_search_params(self) -> SearchParams:
        """Obtiene parámetros de búsqueda como dataclass"""
        return SearchParams(**self.config_data['search_parameters'])
    
    def get_google_config(self) -> GoogleServicesConfig:
        """Obtiene configuración de Google como dataclass"""
        return GoogleServicesConfig(**self.config_data['google_services'])
    
    def get_processing_options(self) -> ProcessingOptions:
        """Obtiene opciones de procesamiento como dataclass"""
        return ProcessingOptions(**self.config_data.get('processing_options', {}))
    
    def get_notification_settings(self) -> NotificationSettings:
        """Obtiene configuración de notificaciones como dataclass"""
        return NotificationSettings(**self.config_data.get('notification_settings', {}))
    
    def validate_current_config(self) -> Dict[str, Any]:
        """Valida la configuración actual y devuelve reporte"""
        try:
            self._validate_config(self.config_data)
            
            return {
                'valid': True,
                'errors': [],
                'warnings': [],
                'summary': {
                    'email_configured': bool(self.config_data.get('email_credentials', {}).get('username')),
                    'google_configured': bool(self.config_data.get('google_services', {}).get('credentials_path')),
                    'search_params_set': bool(self.config_data.get('search_parameters', {}).get('keywords')),
                    'config_file': self.config_path
                }
            }
            
        except ValueError as e:
            return {
                'valid': False,
                'errors': str(e).split('\n')[1:],  # Remover primera línea del mensaje
                'warnings': [],
                'summary': {
                    'email_configured': False,
                    'google_configured': False,
                    'search_params_set': False,
                    'config_file': self.config_path
                }
            }
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen de la configuración actual"""
        if not self.config_data:
            return {'error': 'Configuración no cargada'}
        
        email_cfg = self.config_data.get('email_credentials', {})
        search_cfg = self.config_data.get('search_parameters', {})
        google_cfg = self.config_data.get('google_services', {})
        
        return {
            'config_file': self.config_path,
            'email': {
                'server': email_cfg.get('server', 'No configurado'),
                'username': email_cfg.get('username', 'No configurado'),
                'password_set': bool(email_cfg.get('password'))
            },
            'search': {
                'date_range': f"{search_cfg.get('start_date', 'N/A')} - {search_cfg.get('end_date', 'N/A')}",
                'keywords': search_cfg.get('keywords', []),
                'folder_name': search_cfg.get('folder_name', 'No configurado')
            },
            'google': {
                'credentials_exist': os.path.exists(google_cfg.get('credentials_path', '')),
                'token_exists': os.path.exists(google_cfg.get('token_path', '')),
                'drive_root': google_cfg.get('drive_folder_root', 'FIND_DOCUMENTS')
            },
            'processing': {
                'max_emails': self.config_data.get('processing_options', {}).get('max_emails', 1000),
                'ai_extraction': self.config_data.get('processing_options', {}).get('enable_ai_extraction', True)
            }
        }

# Funciones de utilidad
def create_sample_config_file(output_path: str = "config_sample.json"):
    """Crea un archivo de configuración de muestra"""
    manager = ConfigManager()
    sample_config = manager._get_default_config()
    
    # Agregar comentarios como valores de ejemplo
    sample_config['_comments'] = {
        "email_credentials": "Configura tus credenciales de email. Para Gmail usa App Password.",
        "search_parameters": "Define el rango de fechas y palabras clave para buscar",
        "keywords": "Lista de palabras que deben aparecer en el email o asunto",
        "folder_name": "Nombre de la carpeta que se creará en Google Drive",
        "google_services": "Rutas a archivos de credenciales de Google APIs",
        "processing_options": "Opciones para controlar el comportamiento del procesamiento"
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sample_config, f, indent=2, ensure_ascii=False)
        
        print(f"📄 Archivo de configuración de muestra creado: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Error creando archivo de muestra: {e}")
        raise

def validate_email_credentials(server: str, port: int, username: str, password: str) -> Dict[str, Any]:
    """Valida credenciales de email básicamente"""
    errors = []
    warnings = []
    
    # Validaciones básicas
    if not server:
        errors.append("Servidor requerido")
    elif not server.replace('.', '').replace('-', '').replace('_', '').replace('0', '').replace('1', '').replace('2', '').replace('3', '').replace('4', '').replace('5', '').replace('6', '').replace('7', '').replace('8', '').replace('9', '').isalpha():
        warnings.append("Formato de servidor puede ser inválido")
    
    if port not in [143, 993, 587, 25, 465]:
        warnings.append(f"Puerto {port} no es estándar para email")
    
    if not username:
        errors.append("Nombre de usuario requerido")
    elif '@' not in username:
        warnings.append("Nombre de usuario no parece ser un email válido")
    
    if not password:
        errors.append("Contraseña requerida")
    elif len(password) < 8:
        warnings.append("Contraseña parece muy corta")
    
    # Detectar configuraciones específicas
    suggestions = []
    if 'gmail.com' in username.lower():
        suggestions.append("Para Gmail, usa App Password en lugar de contraseña normal")
        if port != 993:
            warnings.append("Gmail IMAP generalmente usa puerto 993")
    
    return {
        'valid': len(errors) == 0,
        'errors': errors,
        'warnings': warnings,
        'suggestions': suggestions
    }