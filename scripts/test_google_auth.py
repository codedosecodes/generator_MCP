# 
# ===========================================================
# test_google_auth.py
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

# test_google_auth.py - Probar autenticación con Google
import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Scopes necesarios
SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets'
]

def test_credentials():
    print("🔐 Probando credenciales de Google...")
    print("=" * 50)
    
    # Verificar que existe credentials.json
    credentials_path = Path('config/credentials.json')
    if not credentials_path.exists():
        print("❌ Error: config/credentials.json no encontrado")
        print("💡 Asegúrate de haber descargado el archivo desde Google Cloud Console")
        return False
    
    print("✅ Archivo credentials.json encontrado")
    
    # Verificar estructura del archivo
    try:
        with open(credentials_path, 'r') as f:
            creds_data = json.load(f)
        
        if 'installed' not in creds_data:
            print("❌ Error: Formato de credentials.json incorrecto")
            print("💡 Asegúrate de descargar credenciales para 'Aplicación de escritorio'")
            return False
        
        print("✅ Estructura de credenciales válida")
        
    except json.JSONDecodeError:
        print("❌ Error: credentials.json no es un JSON válido")
        return False
    
    # Intentar autenticación
    print("\n🔑 Iniciando proceso de autenticación...")
    
    creds = None
    token_path = Path('config/token.json')
    
    # Cargar token existente si existe
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
            print("✅ Token existente encontrado")
        except:
            print("⚠️  Token existente inválido, regenerando...")
    
    # Si no hay credenciales válidas, obtenerlas
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Renovando token expirado...")
            creds.refresh(Request())
        else:
            print("🌐 Abriendo navegador para autorización...")
            print("👆 Autoriza la aplicación en el navegador que se abrirá")
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Guardar token para próximas ejecuciones
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print("✅ Token guardado para futuras ejecuciones")
    
    # Probar APIs
    print("\n🧪 Probando APIs...")
    
    try:
        # Probar Google Drive API
        drive_service = build('drive', 'v3', credentials=creds)
        drive_info = drive_service.about().get(fields='user').execute()
        user_email = drive_info['user']['emailAddress']
        print(f"✅ Google Drive API - Conectado como: {user_email}")
        
        # Probar Google Sheets API
        sheets_service = build('sheets', 'v4', credentials=creds)
        print("✅ Google Sheets API - Conexión exitosa")
        
        print(f"\n🎉 ¡Autenticación completada exitosamente!")
        print(f"📧 Cuenta autorizada: {user_email}")
        print(f"🔑 Token guardado en: {token_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error probando APIs: {e}")
        return False

if __name__ == "__main__":
    success = test_credentials()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ CONFIGURACIÓN DE CREDENCIALES COMPLETA")
        print("🚀 Ya puedes usar Google Drive y Sheets APIs")
        print("💡 El token se reutilizará automáticamente en próximas ejecuciones")
    else:
        print("\n" + "=" * 50)
        print("❌ CONFIGURACIÓN FALLIDA")
        print("📖 Revisa los pasos anteriores y vuelve a intentar")
