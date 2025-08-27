#!/usr/bin/env python3
# 
# ===========================================================
# config_manager.py
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
Config Manager - DOCUFIND
Gestor de configuración compatible con tu estructura actual
"""

import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfigManager:
    """Gestor de configuración para DOCUFIND"""
    
    def __init__(self, config_path: str = "config/config.json"):
        """
        Inicializa el gestor de configuración
        
        Args:
            config_path: Ruta al archivo de configuración
        """
        self.config_path = Path(config_path)
        self.config = {}
        self.normalized_config = {}
        
    def load_config(self) -> Dict[str, Any]:
        """
        Carga la configuración desde el archivo JSON
        
        Returns:
            Diccionario con la configuración normalizada
        """
        try:
            if not self.config_path.exists():
                raise FileNotFoundError(f"Archivo de configuración no encontrado: {self.config_path}")
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            logger.info(f"✅ Configuración cargada desde: {self.config_path}")
            
            # Normalizar la configuración para que sea compatible con el código
            self.normalized_config = self._normalize_config(self.config)
            
            return self.normalized_config
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error parseando JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error cargando configuración: {e}")
            raise
    
    def _normalize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normaliza la configuración para hacerla compatible con el código esperado
        
        Args:
            config: Configuración original
            
        Returns:
            Configuración normalizada
        """
        # Mapear tu estructura actual a la estructura esperada por el código
        normalized = {
            # Configuración de email - mapeando desde email_credentials
            "email": {
                "provider": "gmail",
                "username": config.get("email_credentials", {}).get("username", ""),
                "password": config.get("email_credentials", {}).get("password", ""),
                "imap_server": config.get("email_credentials", {}).get("server", "imap.gmail.com"),
                "imap_port": config.get("email_credentials", {}).get("port", 993),
                "use_ssl": True,
                "folder": "INBOX",
                "mark_as_read": False,
                "download_attachments": True,
                "max_results": config.get("processing_options", {}).get("max_emails", 100),
                "senders": [],  # No está en tu config actual
                "subject_filters": config.get("search_parameters", {}).get("keywords", []),
                "has_attachments": True
            },
            
            # Configuración de Google Drive - mapeando desde google_services
            "google_drive": {
                "credentials_path": config.get("google_services", {}).get("credentials_path", "./config/credentials.json"),
                "token_path": config.get("google_services", {}).get("token_path", "./config/token.json"),
                "scopes": [
                    "https://www.googleapis.com/auth/drive",  # Cambiado de drive.file a drive
                    "https://www.googleapis.com/auth/spreadsheets"
                ],
                "root_folder": config.get("google_services", {}).get("drive_folder_root", "DOCUFIND"),
                "create_year_folders": True,
                "create_month_folders": True,
                "upload_reports": True
            },
            "spreadsheet_name": config.get("google_services", {}).get("spreadsheet_name"),
            "spreadsheet_name_pattern": config.get("google_services", {}).get("spreadsheet_name_pattern"),
            "spreadsheet_prefix": config.get("google_services", {}).get("spreadsheet_prefix", "DOCUFIND_Facturas"),
            
            # Configuración de extracción
            "extraction": {
                "extract_amounts": True,
                "extract_dates": True,
                "extract_vendors": True,
                "extract_invoice_numbers": True,
                "extract_tax_info": True,
                "confidence_threshold": 0.6,
                "supported_formats": [".pdf", ".xml", ".txt", ".html"],
                "ocr_enabled": False,
                "enable_ai": config.get("processing_options", {}).get("enable_ai_extraction", True)
            },
            
            # Configuración de procesamiento - mapeando desde processing_options
            "processing": {
                "batch_size": 10,
                "parallel_processing": False,
                "retry_failed": True,
                "max_retries": 3,
                "timeout_seconds": config.get("processing_options", {}).get("timeout_seconds", 300),
                "max_emails": config.get("processing_options", {}).get("max_emails", 1000),
                "create_backup": config.get("processing_options", {}).get("create_backup", True)
            },
            
            # Configuración de notificaciones - mapeando desde notification_settings
            "notifications": {
                "enabled": config.get("notification_settings", {}).get("email_reports", False),
                "recipients": [config.get("email_credentials", {}).get("username", "")],
                "send_on_success": config.get("processing_options", {}).get("send_completion_report", True),
                "send_on_error": config.get("notification_settings", {}).get("error_notifications", True),
                "include_summary": True,
                "progress_updates": config.get("notification_settings", {}).get("progress_updates", True)
            },
            
            # Configuración de reportes
            "reports": {
                "generate_report": True,
                "report_format": "json",
                "upload_to_drive": True,
                "include_statistics": True,
                "include_errors": True
            },
            
            # Configuración de logging
            "logging": {
                "level": "INFO",
                "file_logging": True,
                "console_logging": True,
                "log_directory": "logs",
                "max_log_size_mb": 10,
                "backup_count": 5
            },
            
            # Configuración de filtros - mapeando desde search_parameters
            "filters": {
                "date_range_days": 30,
                "start_date": config.get("search_parameters", {}).get("start_date"),
                "end_date": config.get("search_parameters", {}).get("end_date"),
                "skip_processed": True,
                "min_attachment_size_kb": 1,
                "max_attachment_size_mb": 20,
                "allowed_extensions": [
                    ".pdf", ".xml", ".xlsx", ".xls",
                    ".doc", ".docx", ".txt", ".csv"
                ],
                "folder_name": config.get("search_parameters", {}).get("folder_name", "Documentos_Procesados_2025")
            },
            
            "search_parameters": {
                "start_date": config.get("search_parameters", {}).get("start_date"),
                "end_date": config.get("search_parameters", {}).get("end_date"),
                "keywords": config.get("search_parameters", {}).get("keywords", []),
                # ... resto de search_parameters
            },
            
            # Configuración de categorías
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
        
        return normalized
    
    def save_config(self, config: Optional[Dict[str, Any]] = None):
        """
        Guarda la configuración en el archivo JSON
        
        Args:
            config: Configuración a guardar (si no se proporciona, usa la actual)
        """
        try:
            config_to_save = config or self.config
            
            # Hacer backup si existe
            if self.config_path.exists():
                backup_path = self.config_path.with_suffix('.json.backup')
                self.config_path.rename(backup_path)
                logger.info(f"📋 Backup creado: {backup_path}")
            
            # Guardar configuración
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config_to_save, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Configuración guardada en: {self.config_path}")
            
        except Exception as e:
            logger.error(f"❌ Error guardando configuración: {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de la configuración normalizada
        
        Args:
            key: Clave a buscar
            default: Valor por defecto si no existe
            
        Returns:
            Valor de la configuración o default
        """
        return self.normalized_config.get(key, default)
    
    def get_nested(self, keys: str, default: Any = None) -> Any:
        """
        Obtiene un valor anidado usando notación de punto
        
        Args:
            keys: Claves separadas por punto (ej: "email.username")
            default: Valor por defecto
            
        Returns:
            Valor encontrado o default
        """
        try:
            value = self.normalized_config
            for key in keys.split('.'):
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def update(self, key: str, value: Any):
        """
        Actualiza un valor en la configuración
        
        Args:
            key: Clave a actualizar
            value: Nuevo valor
        """
        self.normalized_config[key] = value
        # También actualizar en la config original si es posible
        if key in self.config:
            self.config[key] = value
    
    def validate_config(self) -> bool:
        """
        Valida que la configuración tenga todos los campos necesarios
        
        Returns:
            True si la configuración es válida
        """
        required_fields = [
            ('email.username', 'Email username'),
            ('email.password', 'Email password'),
            ('email.imap_server', 'IMAP server'),
            ('google_drive.credentials_path', 'Google credentials path')
        ]
        
        errors = []
        for field_path, field_name in required_fields:
            if not self.get_nested(field_path):
                errors.append(f"❌ Falta configurar: {field_name}")
        
        if errors:
            for error in errors:
                logger.error(error)
            return False
        
        logger.info("✅ Configuración validada correctamente")
        return True
    
    def get_email_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de email"""
        return self.normalized_config.get('email', {})
    
    def get_drive_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de Google Drive"""
        return self.normalized_config.get('google_drive', {})
    
    def get_extraction_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de extracción"""
        return self.normalized_config.get('extraction', {})
    
    def get_notification_config(self) -> Dict[str, Any]:
        """Obtiene la configuración de notificaciones"""
        return self.normalized_config.get('notifications', {})

# Funciones de utilidad
def create_default_config(path: str = "config/config.json"):
    """
    Crea un archivo de configuración por defecto
    
    Args:
        path: Ruta donde crear el archivo
    """
    default_config = {
        "email_credentials": {
            "server": "imap.gmail.com",
            "port": 993,
            "username": "tu_email@gmail.com",
            "password": "tu_app_password"
        },
        "search_parameters": {
            "start_date": datetime.now().strftime("%Y-%m-01"),
            "end_date": datetime.now().strftime("%Y-%m-%d"),
            "keywords": ["factura", "invoice", "bill", "receipt"],
            "folder_name": f"Documentos_Procesados_{datetime.now().year}"
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
            "drive_folder_root": "DOCUFIND"
        },
        "notification_settings": {
            "email_reports": False,
            "progress_updates": True,
            "error_notifications": True,
            "webhook_url": None
        }
    }
    
    config_path = Path(path)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(default_config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Configuración por defecto creada en: {config_path}")
    return default_config

def test_config():
    """Función de prueba para verificar la configuración"""
    print("🧪 Probando ConfigManager...")
    print("=" * 60)
    
    manager = ConfigManager()
    
    try:
        config = manager.load_config()
        print("✅ Configuración cargada exitosamente")
        
        # Mostrar algunas configuraciones
        print(f"\n📧 Email: {manager.get_nested('email.username')}")
        print(f"📁 Google Drive Root: {manager.get_nested('google_drive.root_folder')}")
        print(f"⚙️ Max Emails: {manager.get_nested('processing.max_emails')}")
        
        # Validar
        if manager.validate_config():
            print("\n✅ Configuración válida y lista para usar")
        else:
            print("\n⚠️ Configuración incompleta")
            
    except FileNotFoundError:
        print("❌ No se encontró config.json")
        print("\n¿Deseas crear una configuración por defecto? (s/n): ", end="")
        if input().lower() == 's':
            create_default_config()
            print("\n📝 Edita config/config.json con tus credenciales")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_config()