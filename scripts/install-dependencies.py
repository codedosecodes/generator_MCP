#!/usr/bin/env python3
"""
Instalador de dependencias para DOCUFIND
Instala todas las librerías necesarias
"""

import subprocess
import sys
import os

def install_package(package):
    """Instala un paquete usando pip"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=" * 60)
    print("🚀 DOCUFIND - Instalador de Dependencias")
    print("=" * 60)
    print()
    
    # Lista de dependencias requeridas
    dependencies = [
        ("google-auth", "Autenticación de Google"),
        ("google-auth-oauthlib", "OAuth para Google"),
        ("google-auth-httplib2", "HTTP para Google Auth"),
        ("google-api-python-client", "Cliente de API de Google"),
    ]
    
    # Dependencias opcionales (no críticas)
    optional_dependencies = [
        ("PyPDF2", "Procesamiento de PDFs"),
        ("python-docx", "Procesamiento de documentos Word"),
        ("openpyxl", "Procesamiento de Excel"),
        ("lxml", "Procesamiento de XML"),
    ]
    
    print("📦 Instalando dependencias requeridas...")
    print("-" * 40)
    
    failed = []
    for package, description in dependencies:
        print(f"\n📦 Instalando {package} ({description})...")
        if install_package(package):
            print(f"   ✅ {package} instalado correctamente")
        else:
            print(f"   ❌ Error instalando {package}")
            failed.append(package)
    
    print("\n📦 Instalando dependencias opcionales...")
    print("-" * 40)
    
    optional_failed = []
    for package, description in optional_dependencies:
        print(f"\n📦 Instalando {package} ({description})...")
        if install_package(package):
            print(f"   ✅ {package} instalado correctamente")
        else:
            print(f"   ⚠️  {package} no se pudo instalar (opcional)")
            optional_failed.append(package)
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE INSTALACIÓN")
    print("=" * 60)
    
    if not failed:
        print("✅ Todas las dependencias requeridas instaladas correctamente")
    else:
        print(f"❌ Dependencias requeridas que fallaron: {', '.join(failed)}")
        print("\nIntenta instalarlas manualmente:")
        for pkg in failed:
            print(f"   pip install {pkg}")
    
    if optional_failed:
        print(f"\n⚠️  Dependencias opcionales no instaladas: {', '.join(optional_failed)}")
        print("   (No son críticas para el funcionamiento básico)")
    
    # Verificar imports críticos
    print("\n🧪 Verificando imports...")
    print("-" * 40)
    
    imports_ok = True
    
    # Verificar Google APIs
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        print("✅ Google APIs importadas correctamente")
    except ImportError as e:
        print(f"❌ Error importando Google APIs: {e}")
        imports_ok = False
    
    # Verificar módulos estándar
    try:
        import imaplib
        import email
        import json
        import base64
        print("✅ Módulos estándar de Python OK")
    except ImportError as e:
        print(f"❌ Error con módulos estándar: {e}")
        imports_ok = False
    
    print("\n" + "=" * 60)
    
    if imports_ok and not failed:
        print("✅ ¡SISTEMA LISTO! Todas las dependencias están instaladas")
        print("\nAhora puedes ejecutar:")
        print("   python src/find_documents_main.py")
    else:
        print("⚠️  Hay problemas con algunas dependencias")
        print("Revisa los errores arriba y corrige antes de continuar")
        sys.exit(1)

if __name__ == "__main__":
    main()