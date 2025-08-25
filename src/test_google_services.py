#!/usr/bin/env python3
"""
Test Google Services - DOCUFIND
Prueba completa de los servicios de Google Drive y Sheets
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime
import time

# Agregar src al path
sys.path.insert(0, 'src')

def test_google_services():
    """
    Prueba completa de los servicios de Google
    
    Returns:
        bool: True si todas las pruebas pasan
    """
    print("=" * 60)
    print("🧪 PRUEBA DE SERVICIOS DE GOOGLE")
    print("=" * 60)
    
    all_tests_passed = True
    test_results = {
        'credentials': False,
        'libraries': False,
        'authentication': False,
        'folder_creation': False,
        'file_upload': False,
        'spreadsheet': False,
        'data_append': False
    }
    
    # 1. Verificar credenciales
    print("\n1️⃣ Verificando archivos de credenciales...")
    credentials_path = Path('config/credentials.json')
    token_path = Path('config/token.json')
    
    if not credentials_path.exists():
        print(f"   ❌ No se encontró credentials.json")
        print(f"   📝 Descárgalo desde Google Cloud Console")
        print(f"   📍 Guárdalo en: {credentials_path.absolute()}")
        print("\n   Instrucciones:")
        print("   1. Ve a https://console.cloud.google.com/")
        print("   2. Crea o selecciona un proyecto")
        print("   3. Ve a 'APIs y servicios' > 'Credenciales'")
        print("   4. Crea credenciales OAuth 2.0 (Aplicación de escritorio)")
        print("   5. Descarga el JSON y guárdalo como credentials.json")
        return False
    else:
        print(f"   ✅ credentials.json encontrado")
        test_results['credentials'] = True
        
        # Verificar formato
        try:
            with open(credentials_path, 'r') as f:
                creds = json.load(f)
            
            if 'installed' in creds:
                print(f"   ✅ Credenciales tipo: Aplicación de escritorio")
                client_id = creds['installed'].get('client_id', '')
                if client_id:
                    print(f"   📋 Client ID: {client_id[:30]}...")
            elif 'web' in creds:
                print(f"   ✅ Credenciales tipo: Aplicación web")
            else:
                print(f"   ⚠️ Formato de credenciales no reconocido")
                all_tests_passed = False
        except json.JSONDecodeError:
            print(f"   ❌ Error leyendo credentials.json - formato inválido")
            all_tests_passed = False
        except Exception as e:
            print(f"   ❌ Error: {e}")
            all_tests_passed = False
    
    if token_path.exists():
        print(f"   ✅ token.json encontrado (autenticación previa)")
    else:
        print(f"   ℹ️ token.json no existe (se creará en primera autenticación)")
    
    # 2. Importar y verificar librerías
    print("\n2️⃣ Verificando librerías de Google...")
    
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        print("   ✅ Todas las librerías de Google importadas")
        test_results['libraries'] = True
    except ImportError as e:
        print(f"   ❌ Error importando librerías: {e}")
        print("\n   📦 Instala con:")
        print("   pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        return False
    
    # 3. Probar GoogleDriveClient
    print("\n3️⃣ Probando GoogleDriveClient...")
    
    try:
        from google_drive_client import GoogleDriveClient, GoogleServicesConfig
        print("   ✅ GoogleDriveClient importado")
    except ImportError as e:
        print(f"   ❌ Error importando GoogleDriveClient: {e}")
        return False
    
    # 4. Cargar configuración
    print("\n4️⃣ Cargando configuración...")
    
    try:
        from config_manager import ConfigManager
        cm = ConfigManager()
        config = cm.load_config()
        drive_config = config.get('google_drive', {})
        
        print(f"   ✅ Configuración cargada")
        print(f"   📁 Carpeta raíz: {drive_config.get('root_folder', 'DOCUFIND')}")
        
    except Exception as e:
        print(f"   ❌ Error cargando configuración: {e}")
        # Usar configuración por defecto
        drive_config = {
            'credentials_path': './config/credentials.json',
            'token_path': './config/token.json',
            'drive_folder_root': 'DOCUFIND_TEST'
        }
        print(f"   ⚠️ Usando configuración por defecto")
    
    # 5. Crear instancia y probar autenticación
    print("\n5️⃣ Probando autenticación con Google...")
    
    try:
        client = GoogleDriveClient(config=drive_config)
        
        print("\n   🔐 Iniciando autenticación...")
        print("   ℹ️ Si es la primera vez, se abrirá el navegador")
        print("   ℹ️ Autoriza el acceso a tu cuenta de Google")
        
        if client.authenticate():
            print("   ✅ Autenticación exitosa")
            test_results['authentication'] = True
            
            # 6. Pruebas de funcionalidad
            print("\n6️⃣ Ejecutando pruebas de funcionalidad...")
            print("   " + "-" * 40)
            
            # Variables para las pruebas
            test_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            test_folder_name = f"DOCUFIND_TEST_{test_timestamp}"
            folder_id = None
            file_id = None
            sheet_id = None
            
            # Prueba 1: Crear carpeta de prueba
            print("\n   📁 PRUEBA 1: Crear carpeta...")
            try:
                folder_id = client.create_folder(test_folder_name)
                
                if folder_id:
                    print(f"   ✅ Carpeta creada: {test_folder_name}")
                    print(f"   📋 ID: {folder_id}")
                    test_results['folder_creation'] = True
                else:
                    print(f"   ❌ No se pudo crear la carpeta")
                    all_tests_passed = False
            except Exception as e:
                print(f"   ❌ Error: {e}")
                all_tests_passed = False
            
            # Prueba 2: Subir archivo de prueba
            if folder_id:
                print("\n   📄 PRUEBA 2: Subir archivo...")
                try:
                    test_content = f"""DOCUFIND - Archivo de Prueba
Fecha: {datetime.now()}
Este es un archivo de prueba generado automáticamente.
Puede ser eliminado sin problemas.

Prueba de caracteres especiales: áéíóú ñ € $ @
Prueba de números: 1234567890
Prueba de símbolos: !@#$%^&*()

Sistema: DOCUFIND
Versión: 1.0
Estado: En pruebas
"""
                    
                    file_id = client.upload_file(
                        content=test_content.encode('utf-8'),
                        filename=f"test_docufind_{test_timestamp}.txt",
                        folder_id=folder_id,
                        metadata={'tipo': 'prueba', 'sistema': 'DOCUFIND'}
                    )
                    
                    if file_id:
                        print(f"   ✅ Archivo subido exitosamente")
                        print(f"   📋 ID: {file_id}")
                        test_results['file_upload'] = True
                    else:
                        print(f"   ❌ No se pudo subir el archivo")
                        all_tests_passed = False
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    all_tests_passed = False
            
            # Prueba 3: Crear hoja de cálculo
            if folder_id:
                print("\n   📊 PRUEBA 3: Crear hoja de cálculo...")
                try:
                    sheet_name = f"DOCUFIND_TEST_SHEET_{datetime.now().strftime('%Y%m%d')}"
                    sheet_id = client.get_or_create_spreadsheet(sheet_name, folder_id)
                    
                    if sheet_id:
                        print(f"   ✅ Hoja de cálculo creada/encontrada")
                        print(f"   📋 ID: {sheet_id}")
                        test_results['spreadsheet'] = True
                    else:
                        print(f"   ❌ No se pudo crear la hoja de cálculo")
                        all_tests_passed = False
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    all_tests_passed = False
            
            # Prueba 4: Agregar datos a la hoja
            if sheet_id:
                print("\n   📝 PRUEBA 4: Agregar datos...")
                try:
                    # Agregar varias filas de prueba
                    test_data = [
                        [
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '2024-01-15',
                            'Proveedor Prueba SA',
                            'INV-TEST-001',
                            '1000.00',
                            '160.00',
                            '1160.00',
                            'MXN',
                            'Transferencia',
                            'Procesado',
                            f'https://drive.google.com/file/d/{file_id}/view' if file_id else '',
                            'Prueba',
                            'Registro de prueba automático'
                        ],
                        [
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            '2024-01-16',
                            'Test Company Inc',
                            'INV-TEST-002',
                            '2500.50',
                            '400.08',
                            '2900.58',
                            'USD',
                            'Tarjeta',
                            'Pendiente',
                            '',
                            'Software',
                            'Segunda línea de prueba'
                        ]
                    ]
                    
                    success_count = 0
                    for i, row in enumerate(test_data, 1):
                        if client.append_to_spreadsheet(sheet_id, row):
                            print(f"   ✅ Fila {i} agregada")
                            success_count += 1
                            time.sleep(0.5)  # Pequeña pausa entre escrituras
                        else:
                            print(f"   ❌ Error agregando fila {i}")
                    
                    if success_count > 0:
                        print(f"   ✅ {success_count} filas agregadas exitosamente")
                        test_results['data_append'] = True
                    else:
                        print(f"   ❌ No se pudieron agregar datos")
                        all_tests_passed = False
                        
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    all_tests_passed = False
            
            # Prueba 5: Listar archivos en la carpeta
            if folder_id:
                print("\n   📋 PRUEBA 5: Listar contenido...")
                try:
                    files = client.list_files_in_folder(folder_id)
                    print(f"   ✅ {len(files)} archivos encontrados en la carpeta de prueba:")
                    for f in files:
                        print(f"      • {f.get('name')} ({f.get('mimeType', 'Unknown')})")
                except Exception as e:
                    print(f"   ⚠️ Error listando archivos: {e}")
            
            # Información de acceso
            if folder_id:
                print("\n   🌐 ACCESO A LOS ARCHIVOS DE PRUEBA:")
                print(f"   📁 Ve a tu Google Drive y busca: {test_folder_name}")
                print(f"   🔗 O visita: https://drive.google.com/drive/folders/{folder_id}")
                if sheet_id:
                    print(f"   📊 Hoja de cálculo: https://docs.google.com/spreadsheets/d/{sheet_id}")
                
        else:
            print("   ❌ Error de autenticación")
            print("\n   Posibles causas:")
            print("   • credentials.json inválido")
            print("   • No se completó la autorización en el navegador")
            print("   • Problemas de conexión a internet")
            print("   • APIs no habilitadas en Google Cloud Console")
            all_tests_passed = False
            
    except Exception as e:
        print(f"   ❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
        all_tests_passed = False
    
    # 7. Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE PRUEBAS")
    print("=" * 60)
    
    for test_name, passed in test_results.items():
        status = "✅" if passed else "❌"
        test_display = test_name.replace('_', ' ').title()
        print(f"   {status} {test_display}")
    
    print("\n" + "=" * 60)
    
    if all([v for v in test_results.values()]):
        print("✅ TODAS LAS PRUEBAS PASARON EXITOSAMENTE")
        print("\n🎉 Google Drive está correctamente configurado")
        print("   El sistema DOCUFIND está listo para usar")
        print("\n   Próximo paso:")
        print("   python src/find_documents_main.py")
    else:
        failed_tests = [k for k, v in test_results.items() if not v]
        print("⚠️ ALGUNAS PRUEBAS FALLARON")
        print(f"\n   Pruebas fallidas: {', '.join(failed_tests)}")
        print("\n   Revisa los errores arriba y:")
        print("   1. Verifica tu archivo credentials.json")
        print("   2. Asegúrate de tener conexión a internet")
        print("   3. Completa la autorización en el navegador")
        print("   4. Verifica que las APIs estén habilitadas:")
        print("      • Google Drive API")
        print("      • Google Sheets API")
    
    print("=" * 60)
    
    return all([v for v in test_results.values()])

def test_google_api_permissions():
    """Verifica los permisos de la API de Google"""
    print("\n🔍 VERIFICACIÓN DE PERMISOS DE API")
    print("=" * 60)
    
    credentials_path = Path('config/credentials.json')
    if not credentials_path.exists():
        print("   ❌ No se puede verificar sin credentials.json")
        return
    
    try:
        with open(credentials_path, 'r') as f:
            creds = json.load(f)
        
        # Obtener información del proyecto
        if 'installed' in creds:
            project_id = creds['installed'].get('project_id', 'No especificado')
            auth_uri = creds['installed'].get('auth_uri', '')
            print(f"\n   📋 Tipo de aplicación: Desktop")
            print(f"   📋 ID del proyecto: {project_id}")
        elif 'web' in creds:
            project_id = creds['web'].get('project_id', 'No especificado')
            print(f"\n   📋 Tipo de aplicación: Web")
            print(f"   📋 ID del proyecto: {project_id}")
        
        print("\n   📌 APIs Necesarias:")
        print("   • Google Drive API - Para gestión de archivos")
        print("   • Google Sheets API - Para hojas de cálculo")
        
        print("\n   🔧 Cómo habilitar las APIs:")
        print("   1. Ve a https://console.cloud.google.com/")
        print(f"   2. Selecciona el proyecto: {project_id}")
        print("   3. Ve a 'APIs y servicios' > 'Biblioteca'")
        print("   4. Busca y habilita:")
        print("      • Google Drive API")
        print("      • Google Sheets API")
        
        print("\n   🔐 Permisos (Scopes) requeridos:")
        print("   • https://www.googleapis.com/auth/drive.file")
        print("   • https://www.googleapis.com/auth/spreadsheets")
        
    except Exception as e:
        print(f"   ❌ Error leyendo credentials.json: {e}")

def quick_test():
    """Prueba rápida de conectividad"""
    print("\n⚡ PRUEBA RÁPIDA DE CONECTIVIDAD")
    print("=" * 60)
    
    try:
        # Verificar archivos
        checks = {
            'config/': Path('config').exists(),
            'config/credentials.json': Path('config/credentials.json').exists(),
            'config/config.json': Path('config/config.json').exists(),
            'src/google_drive_client.py': Path('src/google_drive_client.py').exists()
        }
        
        all_ok = True
        for item, exists in checks.items():
            status = "✅" if exists else "❌"
            print(f"   {status} {item}")
            if not exists:
                all_ok = False
        
        if all_ok:
            print("\n   ✅ Todos los archivos necesarios están presentes")
            print("   Ejecuta: python test_google_services.py")
        else:
            print("\n   ⚠️ Faltan archivos necesarios")
            
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    """Función principal"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Prueba los servicios de Google para DOCUFIND',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python test_google_services.py              # Prueba completa
  python test_google_services.py --quick      # Verificación rápida
  python test_google_services.py --perms      # Ver permisos necesarios
        """
    )
    
    parser.add_argument(
        '--quick', '-q',
        action='store_true',
        help='Verificación rápida de archivos'
    )
    
    parser.add_argument(
        '--perms', '-p',
        action='store_true',
        help='Verificar permisos de API necesarios'
    )
    
    parser.add_argument(
        '--skip-tests',
        action='store_true',
        help='Solo verificar configuración sin hacer pruebas'
    )
    
    args = parser.parse_args()
    
    if args.quick:
        quick_test()
    elif args.perms:
        test_google_api_permissions()
    elif args.skip_tests:
        print("📋 Verificación de configuración...")
        quick_test()
        test_google_api_permissions()
    else:
        # Ejecutar pruebas completas
        print("🚀 Iniciando pruebas completas de Google Services...")
        print("   Esto puede tomar unos momentos...\n")
        success = test_google_services()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()