# test_installation.py - Verificar instalación
import sys
import importlib
import os
from pathlib import Path

def check_python_version():
    version = sys.version_info
    if version.major >= 3 and version.minor >= 9:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - OK")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Necesitas Python 3.9+")
        return False

def check_packages():
    required_packages = [
        'google.auth',
        'google.oauth2',
        'googleapiclient',
        'pandas',
        'openpyxl',
        'dotenv'
    ]
    
    all_installed = True
    print("\n📦 Verificando paquetes:")
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - FALTANTE")
            all_installed = False
    
    return all_installed

def check_structure():
    required_folders = [
        'src', 'tests', 'scripts', 'config', 
        'logs', 'temp', 'docs', 'examples'
    ]
    
    all_exist = True
    print("\n📁 Verificando estructura:")
    for folder in required_folders:
        if Path(folder).exists():
            print(f"   ✅ {folder}/")
        else:
            print(f"   ❌ {folder}/ - FALTANTE")
            all_exist = False
    
    return all_exist

def check_config_files():
    config_files = [
        'requirements.txt',
        '.env.template', 
        'config.json.template',
        '.gitignore',
        'README.md'
    ]
    
    all_exist = True
    print("\n📄 Verificando archivos de configuración:")
    for file in config_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - FALTANTE")
            all_exist = False
    
    return all_exist

def main():
    print("🔍 FIND_DOCUMENTS - Verificación de Instalación")
    print("=" * 60)
    
    python_ok = check_python_version()
    packages_ok = check_packages()
    structure_ok = check_structure()
    config_ok = check_config_files()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN:")
    
    if python_ok and packages_ok and structure_ok and config_ok:
        print("🎉 ¡TODO PERFECTO! Instalación completada exitosamente")
        print("\n🚀 Próximos pasos:")
        print("1. Configurar Google APIs (credentials.json)")
        print("2. Copiar .env.template a .env y configurar")
        print("3. Copiar config.json.template a config/config.json")
        print("4. Ejecutar el programa principal")
    else:
        print("❌ Instalación incompleta. Revisar errores arriba.")
        
        if not packages_ok:
            print("\n💡 Para instalar paquetes faltantes:")
            print("   pip install -r requirements.txt")
        
        if not structure_ok:
            print("\n💡 Para crear carpetas faltantes, ejecutar:")
            print("   mkdir carpeta_faltante")

if __name__ == "__main__":
    main()
