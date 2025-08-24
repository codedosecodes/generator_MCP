#!/usr/bin/env python3
"""
Quick Check - FIND_DOCUMENTS
Verificación rápida de configuración sin conexiones externas
"""

import os
import json
import sys
from pathlib import Path

def check_project_structure():
    """Verifica estructura básica del proyecto"""
    print("📁 ESTRUCTURA DEL PROYECTO")
    print("-" * 30)
    
    required_folders = ['src', 'config', 'logs', 'temp']
    required_files = [
        'src/find_documents_main.py',
        'src/email_processor.py',
        'src/google_drive_client.py',
        'src/invoice_extractor.py',
        'src/config_manager.py'
    ]
    
    all_good = True
    
    # Verificar carpetas
    for folder in required_folders:
        if os.path.exists(folder):
            print(f"✅ {folder}/")
        else:
            print(f"❌ {folder}/ - FALTANTE")
            all_good = False
    
    # Verificar archivos principales
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} - FALTANTE")
            all_good = False
    
    return all_good

def check_config_files():
    """Verifica archivos de configuración"""
    print("\n⚙️  ARCHIVOS DE CONFIGURACIÓN")
    print("-" * 30)
    
    config_status = {}
    
    # 1. config.json
    config_paths = ['config/config.json', 'config.json']
    config_file = None
    
    for path in config_paths:
        if os.path.exists(path):
            config_file = path
            break
    
    if config_file:
        print(f"✅ Configuración: {config_file}")
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Verificar secciones principales
            required_sections = [
                'email_credentials',
                'search_parameters', 
                'google_services'
            ]
            
            for section in required_sections:
                if section in config_data:
                    print(f"✅ {section}")
                else:
                    print(f"❌ {section} - FALTANTE")
                    
            config_status['config_file'] = True
            config_status['config_data'] = config_data
            
        except json.JSONDecodeError as e:
            print(f"❌ Error JSON en {config_file}: {e}")
            config_status['config_file'] = False
        except Exception as e:
            print(f"❌ Error leyendo {config_file}: {e}")
            config_status['config_file'] = False
    else:
        print("❌ config.json - NO ENCONTRADO")
        print("💡 Ubicaciones buscadas:")
        for path in config_paths:
            print(f"   - {os.path.abspath(path)}")
        config_status['config_file'] = False
    
    return config_status

def check_google_credentials(config_status):
    """Verifica credenciales de Google"""
    print("\n🔐 CREDENCIALES DE GOOGLE")
    print("-" * 30)
    
    if not config_status.get('config_file'):
        print("❌ No se puede verificar - config.json no cargado")
        return False
    
    config_data = config_status.get('config_data', {})
    google_config = config_data.get('google_services', {})
    
    # Verificar credentials.json
    creds_path = google_config.get('credentials_path', './config/credentials.json')
    
    if os.path.exists(creds_path):
        print(f"✅ credentials.json: {creds_path}")
        
        try:
            with open(creds_path, 'r') as f:
                creds_data = json.load(f)
            
            if 'installed' in creds_data or 'web' in creds_data:
                print("✅ Formato de credentials.json válido")
                
                # Mostrar info básica
                creds = creds_data.get('installed', creds_data.get('web', {}))
                if 'project_id' in creds:
                    print(f"📋 Proyecto: {creds['project_id']}")
                if 'client_id' in creds:
                    print(f"🔑 Client ID: {creds['client_id'][:20]}...")
                    
                return True
            else:
                print("❌ Formato de credentials.json inválido")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ credentials.json no es JSON válido")
            return False
        except Exception as e:
            print(f"❌ Error leyendo credentials.json: {e}")
            return False
    else:
        print(f"❌ credentials.json NO ENCONTRADO: {creds_path}")
        print("💡 Pasos para obtenerlo:")
        print("   1. Ir a: https://console.cloud.google.com/")
        print("   2. Crear/seleccionar proyecto")
        print("   3. Habilitar: Google Drive API, Google Sheets API")
        print("   4. Crear credenciales OAuth2 'Aplicación de escritorio'")
        print("   5. Descargar JSON y guardar como credentials.json")
        return False

def check_email_config(config_status):
    """Verifica configuración de email"""
    print("\n📧 CONFIGURACIÓN DE EMAIL")
    print("-" * 30)
    
    if not config_status.get('config_file'):
        print("❌ No se puede verificar - config.json no cargado")
        return False
    
    config_data = config_status.get('config_data', {})
    email_config = config_data.get('email_credentials', {})
    
    # Verificar campos requeridos
    required_fields = ['server', 'port', 'username', 'password']
    missing_fields = []
    
    for field in required_fields:
        if field not in email_config or not email_config[field]:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Campos faltantes: {', '.join(missing_fields)}")
        return False
    
    # Mostrar configuración (sin password)
    print(f"✅ Servidor: {email_config['server']}:{email_config['port']}")
    print(f"✅ Usuario: {email_config['username']}")
    print(f"✅ Password: {'*' * len(str(email_config['password']))} ({len(str(email_config['password']))} caracteres)")
    
    # Verificar valores por defecto
    default_values = [
        'tu-email@gmail.com',
        'tu-app-password',
        'tu-app-password-aqui'
    ]
    
    if email_config['username'] in default_values:
        print("⚠️  Username parece ser valor por defecto")
        return False
    
    if str(email_config['password']) in default_values:
        print("⚠️  Password parece ser valor por defecto") 
        return False
    
    # Recomendaciones por proveedor
    username = email_config['username'].lower()
    if 'gmail.com' in username:
        print("💡 Gmail detectado - usar App Password (no contraseña normal)")
    elif 'outlook.com' in username or 'hotmail.com' in username:
        print("💡 Outlook detectado - puede requerir App Password")
    
    return True

def check_search_params(config_status):
    """Verifica parámetros de búsqueda"""
    print("\n🔍 PARÁMETROS DE BÚSQUEDA")
    print("-" * 30)
    
    if not config_status.get('config_file'):
        print("❌ No se puede verificar - config.json no cargado")
        return False
    
    config_data = config_status.get('config_data', {})
    search_config = config_data.get('search_parameters', {})
    
    # Verificar campos requeridos
    required_fields = ['start_date', 'end_date', 'keywords', 'folder_name']
    missing_fields = []
    
    for field in required_fields:
        if field not in search_config or not search_config[field]:
            missing_fields.append(field)
    
    if missing_fields:
        print(f"❌ Campos faltantes: {', '.join(missing_fields)}")
        return False
    
    # Mostrar configuración
    print(f"✅ Rango de fechas: {search_config['start_date']} - {search_config['end_date']}")
    print(f"✅ Palabras clave: {', '.join(search_config['keywords'][:5])}{'...' if len(search_config['keywords']) > 5 else ''}")
    print(f"✅ Carpeta destino: {search_config['folder_name']}")
    
    # Validar fechas básicamente
    try:
        from datetime import datetime
        start = datetime.strptime(search_config['start_date'], '%Y-%m-%d')
        end = datetime.strptime(search_config['end_date'], '%Y-%m-%d')
        
        if start >= end:
            print("❌ Fecha de inicio debe ser anterior a fecha final")
            return False
        
        days_diff = (end - start).days
        if days_diff > 365:
            print(f"⚠️  Rango muy amplio: {days_diff} días (recomendado: ≤365)")
        
        print(f"📅 Período: {days_diff} días")
        
    except ValueError as e:
        print(f"❌ Error en formato de fechas: {e}")
        return False
    
    return True

def check_python_dependencies():
    """Verifica dependencias de Python"""
    print("\n🐍 DEPENDENCIAS DE PYTHON")
    print("-" * 30)
    
    required_packages = [
        ('google.auth', 'google-auth'),
        ('google.oauth2', 'google-auth-oauthlib'),
        ('googleapiclient', 'google-api-python-client'),
        ('pandas', 'pandas'),
        ('openpyxl', 'openpyxl')
    ]
    
    optional_packages = [
        ('dotenv', 'python-dotenv'),
        ('tqdm', 'tqdm'),
        ('colorama', 'colorama')
    ]
    
    missing_required = []
    missing_optional = []
    
    # Verificar paquetes requeridos
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"✅ {package_name}")
        except ImportError:
            print(f"❌ {package_name} - FALTANTE")
            missing_required.append(package_name)
    
    # Verificar paquetes opcionales
    for module_name, package_name in optional_packages:
        try:
            __import__(module_name)
            print(f"✅ {package_name} (opcional)")
        except ImportError:
            print(f"⚠️  {package_name} - OPCIONAL")
            missing_optional.append(package_name)
    
    if missing_required:
        print(f"\n💡 Instalar paquetes faltantes:")
        print(f"   pip install {' '.join(missing_required)}")
        return False
    
    return True

def show_next_steps(results):
    """Muestra próximos pasos basado en resultados"""
    print("\n🎯 PRÓXIMOS PASOS")
    print("=" * 50)
    
    if all(results.values()):
        print("🎉 ¡CONFIGURACIÓN BÁSICA COMPLETA!")
        print()
        print("✨ Tu setup parece estar listo")
        print("🚀 Comando para ejecutar validación completa:")
        print("   python scripts/validate_setup.py")
        print()
        print("🚀 Comando para ejecutar aplicación:")
        print("   python src/find_documents_main.py")
        
    else:
        print("🔧 Completar configuración pendiente:")
        print()
        
        if not results.get('structure'):
            print("1. ❌ Crear estructura del proyecto y archivos de código")
            
        if not results.get('dependencies'):
            print("2. ❌ Instalar dependencias Python:")
            print("   pip install -r requirements.txt")
            
        if not results.get('config'):
            print("3. ❌ Crear y configurar config.json:")
            print("   cp config.json.template config/config.json")
            print("   # Luego editar con tus datos")
            
        if not results.get('google'):
            print("4. ❌ Configurar Google APIs:")
            print("   - Ir a https://console.cloud.google.com/")
            print("   - Habilitar Drive API y Sheets API")
            print("   - Descargar credentials.json")
            
        if not results.get('email'):
            print("5. ❌ Configurar credenciales de email en config.json")
            print("   - Para Gmail: usar App Password")
            
        print()
        print("📖 Para ayuda detallada:")
        print("   python scripts/validate_setup.py --help-setup")

def main():
    """Función principal de verificación rápida"""
    print("🔍 FIND_DOCUMENTS - Verificación Rápida")
    print("=" * 50)
    print("⚡ Validación básica sin conexiones externas")
    print()
    
    results = {}
    
    # 1. Verificar estructura del proyecto
    results['structure'] = check_project_structure()
    
    # 2. Verificar dependencias Python
    results['dependencies'] = check_python_dependencies()
    
    # 3. Verificar archivos de configuración
    config_status = check_config_files()
    results['config'] = config_status.get('config_file', False)
    
    # 4. Verificar credenciales Google (si config existe)
    if results['config']:
        results['google'] = check_google_credentials(config_status)
        results['email'] = check_email_config(config_status)
        results['search'] = check_search_params(config_status)
    else:
        results['google'] = False
        results['email'] = False
        results['search'] = False
    
    # Mostrar resumen
    print("\n📊 RESUMEN DE VERIFICACIÓN")
    print("=" * 50)
    
    checks = [
        ("Estructura del proyecto", results['structure']),
        ("Dependencias Python", results['dependencies']),
        ("Archivo de configuración", results['config']),
        ("Credenciales Google", results['google']),
        ("Configuración email", results['email']),
        ("Parámetros búsqueda", results.get('search', False))
    ]
    
    for check_name, status in checks:
        icon = "✅" if status else "❌"
        print(f"{icon} {check_name}")
    
    # Calcular estado general
    critical_checks = [
        results['structure'],
        results['dependencies'], 
        results['config'],
        results['google'],
        results['email']
    ]
    
    if all(critical_checks):
        overall_status = "READY"
        print(f"\n🎉 ESTADO: LISTO PARA VALIDACIÓN COMPLETA")
    elif any(critical_checks):
        overall_status = "PARTIAL"
        print(f"\n⚠️  ESTADO: CONFIGURACIÓN PARCIAL")
    else:
        overall_status = "INCOMPLETE"
        print(f"\n❌ ESTADO: CONFIGURACIÓN INCOMPLETA")
    
    # Mostrar próximos pasos
    show_next_steps(results)
    
    return overall_status

if __name__ == "__main__":
    import sys
    
    try:
        status = main()
        
        if status == "READY":
            sys.exit(0)
        elif status == "PARTIAL":  
            sys.exit(1)
        else:
            sys.exit(2)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Verificación interrumpida por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error durante verificación: {e}")
        sys.exit(1)