#!/usr/bin/env python3
"""
Script de Validación para DOCUFIND
Verifica que todo esté correctamente configurado
"""

import sys
import os
from pathlib import Path

# Agregar el directorio src al path
script_dir = Path(__file__).parent
project_root = script_dir.parent
src_dir = project_root / 'src'
sys.path.insert(0, str(src_dir))

print("=" * 60)
print("🧪 VALIDACIÓN DEL SISTEMA DOCUFIND")
print("=" * 60)

# 1. Verificar estructura de directorios
print("\n1️⃣ Verificando estructura de directorios...")
required_dirs = ['config', 'src', 'logs', 'scripts']
missing_dirs = []

for dir_name in required_dirs:
    dir_path = project_root / dir_name
    if dir_path.exists():
        print(f"   ✅ {dir_name}/")
    else:
        print(f"   ❌ {dir_name}/ (no encontrado)")
        missing_dirs.append(dir_name)

if missing_dirs:
    print(f"\n   ⚠️ Creando directorios faltantes...")
    for dir_name in missing_dirs:
        (project_root / dir_name).mkdir(exist_ok=True)
        print(f"   ✅ {dir_name}/ creado")

# 2. Verificar archivos de configuración
print("\n2️⃣ Verificando archivos de configuración...")
config_file = project_root / 'config' / 'config.json'

if config_file.exists():
    print(f"   ✅ config.json encontrado")
    
    # Verificar contenido básico
    try:
        import json
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Verificar campos principales
        required_fields = ['email_credentials', 'google_services', 'search_parameters']
        for field in required_fields:
            if field in config:
                print(f"   ✅ {field} configurado")
            else:
                print(f"   ⚠️ {field} no encontrado en config.json")
                
    except json.JSONDecodeError as e:
        print(f"   ❌ Error en config.json: {e}")
else:
    print(f"   ❌ config.json no encontrado")
    print(f"   📝 Crea el archivo en: {config_file}")

# 3. Verificar módulos de Python
print("\n3️⃣ Verificando módulos del sistema...")
modules_status = {}

# Módulos principales
modules_to_check = [
    ('config_manager', 'ConfigManager'),
    ('email_processor', 'EmailProcessor'),
    ('google_drive_client', 'GoogleDriveClient'),
    ('invoice_extractor', 'InvoiceExtractor'),
]

all_modules_ok = True
for module_name, class_name in modules_to_check:
    try:
        module = __import__(module_name)
        if hasattr(module, class_name):
            print(f"   ✅ {module_name}.py → {class_name}")
            modules_status[module_name] = True
        else:
            print(f"   ⚠️ {module_name}.py encontrado pero falta clase {class_name}")
            modules_status[module_name] = False
            all_modules_ok = False
    except ImportError as e:
        print(f"   ❌ {module_name}.py → Error: {str(e)[:50]}")
        modules_status[module_name] = False
        all_modules_ok = False
    except Exception as e:
        print(f"   ❌ {module_name}.py → Error inesperado: {str(e)[:50]}")
        modules_status[module_name] = False
        all_modules_ok = False

# 4. Verificar dependencias externas
print("\n4️⃣ Verificando dependencias externas...")
dependencies = {
    'Google Auth': 'google.auth',
    'Google OAuth': 'google_auth_oauthlib',
    'Google API Client': 'googleapiclient',
}

missing_deps = []
for dep_name, import_name in dependencies.items():
    try:
        __import__(import_name)
        print(f"   ✅ {dep_name}")
    except ImportError:
        print(f"   ❌ {dep_name} no instalado")
        missing_deps.append(import_name)

if missing_deps:
    print("\n   📦 Instala las dependencias faltantes con:")
    print(f"   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")

# 5. Verificar credenciales de Google
print("\n5️⃣ Verificando credenciales de Google...")
credentials_file = project_root / 'config' / 'credentials.json'

if credentials_file.exists():
    print(f"   ✅ credentials.json encontrado")
    try:
        with open(credentials_file, 'r') as f:
            creds = json.load(f)
        if 'installed' in creds or 'web' in creds:
            print(f"   ✅ Formato de credenciales válido")
        else:
            print(f"   ⚠️ Formato de credenciales no reconocido")
    except:
        print(f"   ⚠️ No se pudo leer credentials.json")
else:
    print(f"   ❌ credentials.json no encontrado")
    print(f"   📝 Descarga desde Google Cloud Console y guarda en: {credentials_file}")

# 6. Prueba de integración
if all_modules_ok and not missing_deps:
    print("\n6️⃣ Prueba de integración...")
    try:
        from config_manager import ConfigManager
        from email_processor import EmailProcessor
        from google_drive_client import GoogleDriveClient
        from invoice_extractor import InvoiceExtractor
        
        # Intentar cargar configuración
        cm = ConfigManager()
        config = cm.load_config()
        print(f"   ✅ Configuración cargada")
        
        # Intentar crear instancias
        email_proc = EmailProcessor(config['email'])
        print(f"   ✅ EmailProcessor inicializado")
        
        drive_client = GoogleDriveClient(config=config['google_drive'])
        print(f"   ✅ GoogleDriveClient inicializado")
        
        invoice_ext = InvoiceExtractor(config.get('extraction', {}))
        print(f"   ✅ InvoiceExtractor inicializado")
        
        print("\n" + "=" * 60)
        print("✅ ¡SISTEMA VALIDADO CORRECTAMENTE!")
        print("=" * 60)
        print("\n🚀 El sistema está listo para usar:")
        print(f"   cd {project_root}")
        print("   python src/find_documents_main.py --help")
        
    except Exception as e:
        print(f"\n   ❌ Error en prueba de integración: {e}")
        print("\n" + "=" * 60)
        print("⚠️ SISTEMA CON ERRORES")
        print("=" * 60)
        print("\nRevisa los errores arriba y corrige antes de continuar")
else:
    print("\n" + "=" * 60)
    print("⚠️ VALIDACIÓN INCOMPLETA")
    print("=" * 60)
    
    if not all_modules_ok:
        print("\n❌ Hay errores en los módulos de Python")
        print("   Revisa que todos los archivos .py estén en src/")
    
    if missing_deps:
        print("\n❌ Faltan dependencias externas")
        print("   Ejecuta: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    
    print("\nCorrige los problemas y ejecuta este script nuevamente")

# 7. Información adicional
print("\n📚 Información del Sistema:")
print(f"   Python: {sys.version.split()[0]}")
print(f"   Directorio: {project_root}")
print(f"   Config: {config_file}")

if config_file.exists():
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        email = config.get('email_credentials', {}).get('username', 'No configurado')
        print(f"   Email: {email}")
        drive_root = config.get('google_services', {}).get('drive_folder_root', 'No configurado')
        print(f"   Drive: {drive_root}")
    except:
        pass