#!/usr/bin/env python3
# 
# ===========================================================
# validation_setup.py
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
Script de Validación para DOCUFIND
Verifica que todo esté correctamente configurado
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime

# Agregar el directorio src al path
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

print("=" * 60)
print("🧪 VALIDACIÓN DEL SISTEMA DOCUFIND")
print("=" * 60)

# Variables globales para el estado
validation_passed = True
errors = []
warnings = []

def check_directory_structure():
    """Verifica la estructura de directorios"""
    print("\n1️⃣ VERIFICANDO ESTRUCTURA DE DIRECTORIOS")
    print("-" * 40)
    
    required_dirs = {
        'config': 'Archivos de configuración',
        'src': 'Código fuente',
        'logs': 'Archivos de log',
        'scripts': 'Scripts de utilidad',
        'temp': 'Archivos temporales'
    }
    
    for dir_name, description in required_dirs.items():
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"   ✅ {dir_name}/ - {description}")
        else:
            print(f"   ⚠️ {dir_name}/ no existe - Creando...")
            dir_path.mkdir(exist_ok=True, parents=True)
            print(f"   ✅ {dir_name}/ creado")

def check_config_files():
    """Verifica los archivos de configuración"""
    global validation_passed
    
    print("\n2️⃣ VERIFICANDO ARCHIVOS DE CONFIGURACIÓN")
    print("-" * 40)
    
    config_file = project_root / 'config' / 'config.json'
    
    if not config_file.exists():
        print(f"   ❌ config.json no encontrado")
        print(f"   📝 Necesitas crear: {config_file}")
        errors.append("Falta config.json")
        validation_passed = False
        return None
    
    print(f"   ✅ config.json encontrado")
    
    # Leer y validar contenido
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"   ✅ config.json válido (JSON correcto)")
        
        # Verificar campos principales
        required_sections = {
            'email_credentials': ['server', 'port', 'username', 'password'],
            'google_services': ['credentials_path', 'token_path', 'drive_folder_root'],
            'search_parameters': ['keywords']
        }
        
        for section, fields in required_sections.items():
            if section in config:
                print(f"   ✅ Sección '{section}' encontrada")
                
                # Verificar campos dentro de la sección
                missing_fields = []
                for field in fields:
                    if field not in config[section]:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"      ⚠️ Campos faltantes: {', '.join(missing_fields)}")
                    warnings.append(f"Campos faltantes en {section}: {missing_fields}")
                else:
                    print(f"      ✅ Todos los campos requeridos presentes")
                    
                # Mostrar valores (ocultando contraseña)
                if section == 'email_credentials':
                    username = config[section].get('username', 'No configurado')
                    server = config[section].get('server', 'No configurado')
                    print(f"      📧 Email: {username}")
                    print(f"      📬 Servidor: {server}")
                elif section == 'google_services':
                    drive_root = config[section].get('drive_folder_root', 'No configurado')
                    print(f"      📁 Carpeta Drive: {drive_root}")
                    
            else:
                print(f"   ❌ Sección '{section}' no encontrada")
                errors.append(f"Falta sección {section}")
                validation_passed = False
        
        return config
        
    except json.JSONDecodeError as e:
        print(f"   ❌ Error en config.json: {e}")
        errors.append("config.json tiene formato JSON inválido")
        validation_passed = False
        return None
    except Exception as e:
        print(f"   ❌ Error leyendo config.json: {e}")
        errors.append(f"Error leyendo config.json: {e}")
        validation_passed = False
        return None

def check_google_credentials(config):
    """Verifica las credenciales de Google"""
    global validation_passed
    
    print("\n3️⃣ VERIFICANDO CREDENCIALES DE GOOGLE")
    print("-" * 40)
    
    if not config:
        print("   ⚠️ No se puede verificar sin configuración")
        return
    
    google_config = config.get('google_services', {})
    
    # Verificar credentials.json
    creds_path = google_config.get('credentials_path', './config/credentials.json')
    # Convertir a path absoluto si es relativo
    if creds_path.startswith('./'):
        creds_path = project_root / creds_path[2:]
    else:
        creds_path = Path(creds_path)
    
    if not creds_path.exists():
        print(f"   ❌ credentials.json no encontrado en: {creds_path}")
        print(f"\n   📝 Instrucciones para obtener credentials.json:")
        print("   1. Ve a https://console.cloud.google.com/")
        print("   2. Crea o selecciona un proyecto")
        print("   3. Ve a 'APIs y servicios' > 'Credenciales'")
        print("   4. Crea credenciales OAuth 2.0 (Aplicación de escritorio)")
        print("   5. Descarga y guarda en:", creds_path)
        errors.append("Falta credentials.json")
        validation_passed = False
    else:
        print(f"   ✅ credentials.json encontrado")
        
        # Verificar formato
        try:
            with open(creds_path, 'r') as f:
                creds = json.load(f)
            
            if 'installed' in creds or 'web' in creds:
                print(f"   ✅ Formato de credenciales válido")
                
                # Mostrar info del proyecto
                if 'installed' in creds:
                    project_id = creds['installed'].get('project_id', 'No especificado')
                    print(f"   📋 Proyecto: {project_id}")
                    print(f"   📋 Tipo: Aplicación de escritorio")
            else:
                print(f"   ⚠️ Formato de credenciales no reconocido")
                warnings.append("Formato de credentials.json no estándar")
                
        except json.JSONDecodeError:
            print(f"   ❌ credentials.json no es JSON válido")
            errors.append("credentials.json corrupto")
            validation_passed = False
        except Exception as e:
            print(f"   ⚠️ Error leyendo credentials.json: {e}")
            warnings.append(f"Error leyendo credentials.json: {e}")
    
    # Verificar token.json
    token_path = google_config.get('token_path', './config/token.json')
    if token_path.startswith('./'):
        token_path = project_root / token_path[2:]
    else:
        token_path = Path(token_path)
    
    if token_path.exists():
        print(f"   ✅ token.json encontrado (autenticación previa)")
    else:
        print(f"   ℹ️ token.json no existe (se creará en primera autenticación)")

def check_python_modules():
    """Verifica los módulos de Python"""
    global validation_passed
    
    print("\n4️⃣ VERIFICANDO MÓDULOS DE PYTHON")
    print("-" * 40)
    
    modules_to_check = [
        ('config_manager', 'ConfigManager', 'Gestor de configuración'),
        ('email_processor', 'EmailProcessor', 'Procesador de emails'),
        ('google_drive_client', 'GoogleDriveClient', 'Cliente de Google Drive'),
        ('invoice_extractor', 'InvoiceExtractor', 'Extractor de facturas'),
    ]
    
    all_modules_ok = True
    
    for module_name, class_name, description in modules_to_check:
        try:
            module = __import__(module_name)
            if hasattr(module, class_name):
                print(f"   ✅ {module_name}.py - {description}")
            else:
                print(f"   ⚠️ {module_name}.py encontrado pero falta clase {class_name}")
                warnings.append(f"Clase {class_name} no encontrada en {module_name}")
                all_modules_ok = False
        except ImportError as e:
            error_msg = str(e)
            if 'No module named' in error_msg:
                print(f"   ❌ {module_name}.py - No encontrado")
                errors.append(f"Módulo {module_name} no encontrado")
            else:
                print(f"   ❌ {module_name}.py - Error al importar: {error_msg[:50]}")
                errors.append(f"Error importando {module_name}: {error_msg}")
            all_modules_ok = False
            validation_passed = False
        except Exception as e:
            print(f"   ❌ {module_name}.py - Error inesperado: {str(e)[:50]}")
            errors.append(f"Error en {module_name}: {e}")
            all_modules_ok = False
            validation_passed = False
    
    return all_modules_ok

def check_dependencies():
    """Verifica las dependencias externas"""
    global validation_passed
    
    print("\n5️⃣ VERIFICANDO DEPENDENCIAS EXTERNAS")
    print("-" * 40)
    
    dependencies = {
        'google.auth': 'Google Auth',
        'google_auth_oauthlib': 'Google OAuth',
        'googleapiclient': 'Google API Client',
    }
    
    missing_deps = []
    
    for import_name, display_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"   ✅ {display_name}")
        except ImportError:
            print(f"   ❌ {display_name} no instalado")
            missing_deps.append(import_name)
            validation_passed = False
    
    if missing_deps:
        print("\n   📦 Instala las dependencias faltantes con:")
        print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        errors.append(f"Dependencias faltantes: {', '.join(missing_deps)}")

def integration_test(config):
    """Prueba de integración básica"""
    print("\n6️⃣ PRUEBA DE INTEGRACIÓN")
    print("-" * 40)
    
    if not config:
        print("   ⚠️ No se puede hacer prueba de integración sin configuración")
        return
    
    if errors:
        print("   ⚠️ Saltando prueba de integración debido a errores previos")
        return
    
    try:
        from config_manager import ConfigManager
        from email_processor import EmailProcessor
        from google_drive_client import GoogleDriveClient
        from invoice_extractor import InvoiceExtractor
        
        print("   ✅ Todos los imports exitosos")
        
        # Intentar crear instancias
        try:
            # ConfigManager
            cm = ConfigManager()
            loaded_config = cm.load_config()
            print(f"   ✅ ConfigManager inicializado")
            
            # EmailProcessor
            email_config = loaded_config.get('email', {})
            email_proc = EmailProcessor(email_config)
            print(f"   ✅ EmailProcessor inicializado")
            
            # GoogleDriveClient
            drive_config = loaded_config.get('google_drive', {})
            drive_client = GoogleDriveClient(config=drive_config)
            print(f"   ✅ GoogleDriveClient inicializado")
            
            # InvoiceExtractor
            extraction_config = loaded_config.get('extraction', {})
            invoice_ext = InvoiceExtractor(extraction_config)
            print(f"   ✅ InvoiceExtractor inicializado")
            
            print("\n   ✅ Prueba de integración exitosa")
            
        except Exception as e:
            print(f"   ❌ Error en integración: {e}")
            warnings.append(f"Error de integración: {e}")
            
    except ImportError as e:
        print(f"   ❌ Error importando módulos: {e}")
        errors.append(f"Error de import en integración: {e}")
    except Exception as e:
        print(f"   ❌ Error inesperado: {e}")
        errors.append(f"Error en integración: {e}")

def print_summary():
    """Imprime el resumen de la validación"""
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE VALIDACIÓN")
    print("=" * 60)
    
    if not errors and not warnings:
        print("\n✅ ¡SISTEMA COMPLETAMENTE VALIDADO!")
        print("\n🎉 DOCUFIND está listo para usar")
        print("\nEjecuta:")
        print(f"   cd {project_root}")
        print("   python src/find_documents_main.py --help")
        
    else:
        if errors:
            print(f"\n❌ ERRORES ENCONTRADOS ({len(errors)}):")
            for error in errors:
                print(f"   • {error}")
        
        if warnings:
            print(f"\n⚠️ ADVERTENCIAS ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        
        print("\n📝 ACCIONES REQUERIDAS:")
        
        if 'Falta config.json' in str(errors):
            print("\n1. Crea el archivo config/config.json")
            print("   Usa la plantilla proporcionada")
            
        if 'credentials.json' in str(errors):
            print("\n2. Descarga credentials.json desde Google Cloud Console")
            print("   Guárdalo en config/credentials.json")
            
        if 'Dependencias faltantes' in str(errors):
            print("\n3. Instala las dependencias de Google:")
            print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            
        if any('Módulo' in e for e in errors):
            print("\n4. Verifica que todos los archivos .py estén en src/")
            print("   - config_manager.py")
            print("   - email_processor.py")
            print("   - google_drive_client.py")
            print("   - invoice_extractor.py")
    
    print("\n" + "=" * 60)
    print("📚 INFORMACIÓN DEL SISTEMA")
    print("=" * 60)
    print(f"   Python: {sys.version.split()[0]}")
    print(f"   Directorio: {project_root}")
    print(f"   Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if validation_passed:
        print(f"   Estado: ✅ Listo")
    else:
        print(f"   Estado: ⚠️ Requiere configuración")

def main():
    """Función principal"""
    print(f"\n📁 Directorio del proyecto: {project_root}")
    print(f"📁 Directorio de scripts: {script_dir}")
    print(f"📁 Directorio src: {src_dir}")
    
    # Ejecutar verificaciones
    check_directory_structure()
    config = check_config_files()
    check_google_credentials(config)
    modules_ok = check_python_modules()
    check_dependencies()
    
    # Solo hacer prueba de integración si los módulos están OK
    if modules_ok and config:
        integration_test(config)
    
    # Mostrar resumen
    print_summary()
    
    # Código de salida
    if validation_passed and not errors:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Validación interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)