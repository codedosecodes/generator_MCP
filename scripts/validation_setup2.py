#!/usr/bin/env python3
"""
Validate Setup - DOCUFIND
Valida que las configuraciones de Google APIs y Email estén correctas
"""

import os
import sys
import json
import asyncio
import imaplib
import ssl
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Agregar src al path para imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


try:
    from config_manager import ConfigManager
    from email_processor import EmailProcessor, EmailCredentials,EmailConfig
    from google_drive_client import GoogleDriveClient, GoogleServicesConfig
    from test_google_services import test_google_services
    

except ImportError as e:
    print(f"❌ Error importando módulos: {e}")
    print("💡 Asegúrate de ejecutar desde la carpeta raíz del proyecto")
    sys.exit(1)

class SetupValidator:
    """Validador completo de configuración"""
    
    def __init__(self):
        self.results = {
            'config_file': False,
            'google_credentials': False,
            'google_connection': False,
            'email_credentials': False,
            'email_connection': False,
            'overall_status': 'FAILED'
        }
        
        self.detailed_results = {}
        self.config_manager = None
    
    async def run_complete_validation(self):
        """Ejecuta validación completa del setup"""
        print("🔍 DOCUFIND - Validador de Configuración")
        print("=" * 60)
        print(f"📅 Ejecutado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Paso 1: Validar archivo de configuración
        await self._validate_config_file()
        
        # Paso 2: Validar credenciales de Google
        await self._validate_google_credentials()
        
        # Paso 3: Validar conexión con Google APIs
        if self.results['google_credentials']:
            await self._validate_google_connection()
        
        # Paso 4: Validar credenciales de email
        if self.results['config_file']:
            await self._validate_email_credentials()
        
        # Paso 5: Validar conexión de email
        if self.results['email_credentials']:
            await self._validate_email_connection()
        
        # Mostrar resumen final
        self._show_final_summary()
        
        # Determinar estado general
        self._calculate_overall_status()
        
        return self.results
    
    async def _validate_config_file(self):
        """Valida el archivo de configuración principal"""
        print("1️⃣  VALIDANDO ARCHIVO DE CONFIGURACIÓN")
        print("-" * 40)
        
        try:
            # Buscar archivo de configuración
            config_paths = [
                "config/config.json",
                "config.json",
                "../config/config.json"
            ]
            
            config_path = None
            for path in config_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if not config_path:
                print("❌ Archivo config.json no encontrado en:")
                for path in config_paths:
                    print(f"   - {os.path.abspath(path)}")
                print()
                print("💡 Crear archivo con: cp config.json.template config/config.json")
                return
            
            # Cargar y validar configuración
            self.config_manager = ConfigManager(config_path)
            config = self.config_manager.load_config()
            
            print(f"✅ Archivo encontrado: {os.path.abspath(config_path)}")
            
            # Validar estructura
            validation_result ='valid'
           # validation_result = self.config_manager.validate_current_config()
           # 
           # if validation_result['valid']:
           #     print("✅ Estructura de configuración válida")
           #     self.results['config_file'] = True
           #     
           #     # Mostrar resumen
           #     summary = self.config_manager.get_config_summary()
           #     print(f"📧 Email: {summary['email']['username']}")
           #     print(f"📅 Rango: {summary['search']['date_range']}")
           #     print(f"🔍 Palabras clave: {', '.join(summary['search']['keywords'][:3])}...")
           #     print(f"📁 Carpeta: {summary['search']['folder_name']}")
           #     
           # else:
           #     print("❌ Errores en configuración:")
           #     for error in validation_result['errors']:
           #         print(f"   - {error}")
                
            self.detailed_results['config'] = validation_result
            
        except Exception as e:
            print(f"❌ Error validando configuración: {e}")
            self.detailed_results['config'] = {'error': str(e)}
        
        print()
    
    async def _validate_google_credentials(self):
        """Valida las credenciales de Google"""
        print("2️⃣  VALIDANDO CREDENCIALES DE GOOGLE")
        print("-" * 40)
        
        if not self.config_manager:
            print("❌ Configuración no cargada, saltando validación Google")
            print()
            return
        
        try:
            google_config = self.config_manager.get_google_config()
            
            # Verificar archivo credentials.json
            creds_path = google_config.credentials_path
            if not os.path.exists(creds_path):
                print(f"❌ Archivo credentials.json no encontrado: {creds_path}")
                print()
                print("💡 Pasos para configurar Google APIs:")
                print("   1. Ir a: https://console.cloud.google.com/")
                print("   2. Crear proyecto o seleccionar existente")
                print("   3. Habilitar APIs: Google Drive API, Google Sheets API")
                print("   4. Crear credenciales OAuth2 para 'Aplicación de escritorio'")
                print("   5. Descargar JSON y guardarlo como credentials.json")
                print()
                return
            
            print(f"✅ Archivo credentials.json encontrado: {os.path.abspath(creds_path)}")
            
            # Validar contenido del archivo
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            if 'installed' not in creds_data and 'web' not in creds_data:
                print("❌ Formato de credentials.json inválido")
                print("💡 Debe contener sección 'installed' para aplicaciones de escritorio")
                return
            
            creds_section = creds_data.get('installed', creds_data.get('web', {}))
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            
            missing_fields = [field for field in required_fields if field not in creds_section]
            if missing_fields:
                print(f"❌ Campos faltantes en credentials.json: {', '.join(missing_fields)}")
                return
            
            print("✅ Estructura de credentials.json válida")
            print(f"🔑 Client ID: {creds_section['client_id'][:20]}...")
            print(f"🌐 Proyecto: {creds_section.get('project_id', 'N/A')}")
            
            # Verificar token existente
            token_path = google_config.token_path
            if os.path.exists(token_path):
                print(f"✅ Token OAuth2 encontrado: {os.path.abspath(token_path)}")
                
                # Verificar validez del token
                try:
                    with open(token_path, 'r') as f:
                        token_data = json.load(f)
                    
                    if 'token' in token_data and 'refresh_token' in token_data:
                        print("✅ Token contiene refresh_token (reutilizable)")
                    else:
                        print("⚠️  Token puede necesitar renovación")
                        
                except json.JSONDecodeError:
                    print("⚠️  Token corrupto, se regenerará automáticamente")
            else:
                print(f"⚠️  Token no existe aún: {os.path.abspath(token_path)}")
                print("💡 Se creará automáticamente en la primera conexión")
            
            self.results['google_credentials'] = True
            
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando credentials.json: {e}")
        except Exception as e:
            print(f"❌ Error validando credenciales Google: {e}")
        
        print()
    
    async def _validate_google_connection(self):
        """Valida la conexión con Google APIs"""
        print("3️⃣  VALIDANDO CONEXIÓN CON GOOGLE APIS")
        print("-" * 40)
        
        try:
            google_config = self.config_manager.get_google_config()
            
            print("🔌 Probando conexión con Google APIs...")
            print("   (Esto puede abrir un navegador para autorización)")
            
            # Probar servicios de Google
            test_result = await test_google_services(
                google_config.credentials_path,
                google_config.token_path
            )
            
            if test_result['success']:
                print("✅ Conexión exitosa con Google APIs")
                print(f"👤 Usuario: {test_result['user_name']} ({test_result['user_email']})")
                
                # Mostrar info de almacenamiento si está disponible
                if test_result.get('storage_used') != 'Unknown':
                    used = self._format_bytes(test_result['storage_used'])
                    limit = self._format_bytes(test_result['storage_limit'])
                    print(f"💾 Almacenamiento: {used} / {limit}")
                
                print("🔧 Servicios disponibles:")
                services = test_result.get('services', {})
                if services.get('drive'):
                    print("   ✅ Google Drive API")
                if services.get('sheets'):
                    print("   ✅ Google Sheets API")
                
                self.results['google_connection'] = True
                
            else:
                print(f"❌ Error conectando con Google APIs: {test_result['error']}")
                print()
                print("💡 Posibles soluciones:")
                print("   1. Verificar que las APIs estén habilitadas en Google Cloud Console")
                print("   2. Verificar que el archivo credentials.json sea correcto")
                print("   3. Intentar eliminar token.json para forzar re-autenticación")
            
            self.detailed_results['google_connection'] = test_result
            
        except Exception as e:
            print(f"❌ Error probando conexión Google: {e}")
            self.detailed_results['google_connection'] = {'error': str(e)}
        
        print()
    
    async def _validate_email_credentials(self):
        """Valida las credenciales de email"""
        print("4️⃣  VALIDANDO CREDENCIALES DE EMAIL")
        print("-" * 40)
        
        try:
            email_config = self.config_manager.get_email_config()
            
            print(f"📧 Servidor: {email_config.server}:{email_config.port}")
            print(f"👤 Usuario: {email_config.username}")
            print(f"🔒 Password: {'*' * len(email_config.password)} ({len(email_config.password)} caracteres)")
            
            # Validar formato básico
            validation_errors = email_config.validate()
            if validation_errors:
                print("❌ Errores en configuración de email:")
                for error in validation_errors:
                    print(f"   - {error}")
                return
            
            # Verificar que no sean valores por defecto
            if not email_config.username or email_config.username == "tu-email@gmail.com":
                print("❌ Email username no configurado o es valor por defecto")
                return
            
            if not email_config.password or email_config.password == "tu-app-password":
                print("❌ Password no configurado o es valor por defecto")
                return
            
            print("✅ Credenciales de email básicas válidas")
            
            # Mostrar recomendaciones por proveedor
            domain = email_config.username.split('@')[-1].lower()
            if domain == 'gmail.com':
                print("💡 Gmail detectado:")
                print("   - Asegúrate de usar App Password (no contraseña normal)")
                print("   - 2FA debe estar habilitado")
                print("   - Crear App Password en: https://myaccount.google.com/apppasswords")
            elif domain in ['outlook.com', 'hotmail.com']:
                print("💡 Outlook/Hotmail detectado:")
                print("   - Puede requerir App Password")
                print("   - Verificar configuración en: https://account.microsoft.com/security")
            
            self.results['email_credentials'] = True
            
        except Exception as e:
            print(f"❌ Error validando credenciales de email: {e}")
        
        print()
    
    async def _validate_email_connection(self):
        """Valida la conexión con el servidor de email"""
        print("5️⃣  VALIDANDO CONEXIÓN DE EMAIL")
        print("-" * 40)
        
        try:
            email_config = self.config_manager.get_email_config()
            
            print("🔌 Probando conexión con servidor de email...")
            
            # Crear credenciales para EmailProcessor
            email_creds = EmailCredentials(
                server=email_config.server,
                port=email_config.port,
                username=email_config.username,
                password=email_config.password
            )
            
            # Probar conexión
            email_processor = EmailProcessor(email_creds)
            test_result = await email_processor.test_connection()
            
            if test_result['success']:
                print("✅ Conexión exitosa con servidor de email")
                print(f"📬 Total emails en INBOX: {test_result['total_emails_in_inbox']:,}")
                print(f"🌐 Servidor: {test_result['server_info']}")
                
                self.results['email_connection'] = True
                
                # Test adicional: buscar algunos emails recientes
                print()
                print("🔍 Probando búsqueda básica de emails...")
                try:
                    from email_processor import EmailFilter
                    from datetime import datetime, timedelta
                    
                    # Buscar emails de los últimos 7 días
                    end_date = datetime.now()
                    start_date = end_date - timedelta(days=7)
                    
                    test_filter = EmailFilter(
                        start_date=start_date.strftime('%Y-%m-%d'),
                        end_date=end_date.strftime('%Y-%m-%d'),
                        keywords=['the', 'and', 'or']  # Palabras comunes para encontrar algo
                    )
                    
                    await email_processor.connect()
                    recent_emails = await email_processor.search_emails(test_filter)
                    await email_processor.disconnect()
                    
                    print(f"✅ Búsqueda de prueba exitosa: {len(recent_emails)} emails encontrados")
                    
                except Exception as search_error:
                    print(f"⚠️  Advertencia en búsqueda de prueba: {search_error}")
                
            else:
                print(f"❌ Error conectando con email: {test_result['error']}")
                print()
                print("💡 Posibles soluciones:")
                print("   1. Verificar credenciales de email")
                print("   2. Para Gmail: usar App Password en lugar de contraseña normal")
                print("   3. Verificar que IMAP esté habilitado en tu cuenta")
                print("   4. Revisar configuración de servidor y puerto")
                
            self.detailed_results['email_connection'] = test_result
            
        except Exception as e:
            print(f"❌ Error probando conexión de email: {e}")
            self.detailed_results['email_connection'] = {'error': str(e)}
        
        print()
    
    def _format_bytes(self, size_str: str) -> str:
        """Formatea bytes en formato legible"""
        try:
            size = int(size_str)
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} PB"
        except (ValueError, TypeError):
            return str(size_str)
    
    def _show_final_summary(self):
        """Muestra resumen final de validación"""
        print("📊 RESUMEN DE VALIDACIÓN")
        print("=" * 60)
        
        checks = [
            ("Archivo de configuración", self.results['config_file']),
            ("Credenciales de Google", self.results['google_credentials']),
            ("Conexión Google APIs", self.results['google_connection']),
            ("Credenciales de email", self.results['email_credentials']),
            ("Conexión de email", self.results['email_connection'])
        ]
        
        for check_name, status in checks:
            icon = "✅" if status else "❌"
            print(f"{icon} {check_name}")
        
        print()
    
    def _calculate_overall_status(self):
        """Calcula estado general del setup"""
        required_checks = [
            self.results['config_file'],
            self.results['google_credentials'],
            self.results['email_credentials']
        ]
        
        optional_checks = [
            self.results['google_connection'],
            self.results['email_connection']
        ]
        
        if all(required_checks) and all(optional_checks):
            self.results['overall_status'] = 'READY'
            status_msg = "🎉 ¡CONFIGURACIÓN COMPLETA!"
            color = "green"
        elif all(required_checks):
            self.results['overall_status'] = 'PARTIAL'
            status_msg = "⚠️  CONFIGURACIÓN PARCIAL"
            color = "yellow" 
        else:
            self.results['overall_status'] = 'FAILED'
            status_msg = "❌ CONFIGURACIÓN INCOMPLETA"
            color = "red"
        
        print("🎯 ESTADO FINAL")
        print("=" * 60)
        print(status_msg)
        print()
        
        if self.results['overall_status'] == 'READY':
            print("✨ Tu configuración está lista para ejecutar DOCUFIND")
            print("🚀 Comando para ejecutar:")
            print("   python src/find-documents-main.py")
            
        elif self.results['overall_status'] == 'PARTIAL':
            print("⚙️  Configuración básica lista, pero hay advertencias")
            print("💡 Puedes intentar ejecutar el programa, pero puede haber errores")
            
        else:
            print("🔧 Completa la configuración antes de ejecutar el programa")
            print()
            print("📋 PRÓXIMOS PASOS:")
            
            if not self.results['config_file']:
                print("   1. Crear y configurar config/config.json")
                
            if not self.results['google_credentials']:
                print("   2. Configurar Google APIs y descargar credentials.json")
                
            if not self.results['email_credentials']:
                print("   3. Configurar credenciales de email en config.json")
        
        print()

# Función de ayuda
def show_setup_help():
    """Muestra ayuda para configurar el sistema"""
    print("📚 GUÍA DE CONFIGURACIÓN RÁPIDA")
    print("=" * 60)
    print()
    
    print("🔧 1. CONFIGURAR GOOGLE APIS:")
    print("   • Ir a: https://console.cloud.google.com/")
    print("   • Crear proyecto nuevo")
    print("   • Habilitar: Google Drive API, Google Sheets API")
    print("   • Crear credenciales OAuth2 para 'Aplicación de escritorio'")
    print("   • Descargar JSON y guardar como config/credentials.json")
    print()
    
    print("📧 2. CONFIGURAR EMAIL:")
    print("   • Para Gmail: Habilitar 2FA y crear App Password")
    print("   • Editar config/config.json con:")
    print("     - email_credentials.username: tu-email@gmail.com")
    print("     - email_credentials.password: tu-app-password")
    print()
    
    print("📋 3. CONFIGURAR BÚSQUEDA:")
    print("   • Editar config/config.json con:")
    print("     - search_parameters.start_date: 2024-01-01")
    print("     - search_parameters.end_date: 2024-12-31")
    print("     - search_parameters.keywords: ['factura', 'invoice']")
    print("     - search_parameters.folder_name: MisCarpeta2024")
    print()

# Función principal
async def main():
    """Función principal del validador"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validar configuración de DOCUFIND')
    parser.add_argument('--help-setup', action='store_true', 
                       help='Mostrar guía de configuración')
    parser.add_argument('--save-report', action='store_true',
                       help='Guardar reporte de validación en archivo')
    
    args = parser.parse_args()
    
    if args.help_setup:
        show_setup_help()
        return
    
    # Ejecutar validación
    validator = SetupValidator()
    results = await validator.run_complete_validation()
    
    # Guardar reporte si se solicita
    if args.save_report:
        report_path = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'results': results,
            'detailed_results': validator.detailed_results
        }
        
        try:
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            print(f"📄 Reporte guardado: {report_path}")
        except Exception as e:
            print(f"⚠️  Error guardando reporte: {e}")
    
    # Código de salida basado en resultado
    if results['overall_status'] == 'READY':
        sys.exit(0)  # Éxito
    elif results['overall_status'] == 'PARTIAL':
        sys.exit(1)  # Advertencia
    else:
        sys.exit(2)  # Error

if __name__ == "__main__":
    asyncio.run(main())