# 
# ===========================================================
# test_email_connection.py
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

# test_email_connection.py - Probar conexión de email
import imaplib
import ssl
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def test_email_connection():
    print("📧 Probando conexión de email...")
    print("=" * 40)
    
    # Obtener credenciales
    username = os.getenv('EMAIL_USERNAME')
    password = os.getenv('EMAIL_PASSWORD')
    
    if not username or not password:
        print("❌ Error: EMAIL_USERNAME o EMAIL_PASSWORD no configurados en .env")
        return False
    
    print(f"👤 Usuario: {username}")
    print(f"🔑 Password: {'*' * len(password)} ({len(password)} caracteres)")
    
    try:
        # Crear contexto SSL
        context = ssl.create_default_context()
        
        # Conectar con Gmail IMAP
        print("\n🔌 Conectando a Gmail IMAP...")
        mail = imaplib.IMAP4_SSL('imap.gmail.com', 993, ssl_context=context)
        
        # Autenticar
        print("🔐 Autenticando...")
        mail.login(username, password)
        
        # Seleccionar INBOX
        mail.select('INBOX')
        
        # Obtener info básica
        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()
        total_emails = len(email_ids)
        
        print(f"✅ ¡Conexión exitosa!")
        print(f"📬 Total de emails en INBOX: {total_emails}")
        
        # Cerrar conexión
        mail.logout()
        
        print(f"🎉 Credenciales de email configuradas correctamente")
        return True
        
    except imaplib.IMAP4.error as e:
        print(f"❌ Error de autenticación IMAP: {e}")
        print("💡 Verifica que EMAIL_PASSWORD sea un App Password válido")
        return False
    except ssl.SSLError as e:
        print(f"❌ Error SSL: {e}")
        return False
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return False

if __name__ == "__main__":
    success = test_email_connection()
    
    if success:
        print("\n" + "=" * 40)
        print("✅ CONFIGURACIÓN DE EMAIL COMPLETA")
    else:
        print("\n" + "=" * 40)
        print("❌ CONFIGURACIÓN DE EMAIL FALLIDA")
        print("📖 Revisa el App Password de Gmail")
