# 📝 Instalación Manual - FIND_DOCUMENTS

## 🗂️ Paso 1: Crear Estructura de Carpetas

```powershell
# Abrir PowerShell y navegar a tu directorio de trabajo
cd "C:\DevOps\DOTNET CLI\mcp"

# Crear carpeta principal del proyecto
mkdir FIND_DOCUMENTS
cd FIND_DOCUMENTS

# Crear estructura de carpetas
mkdir src
mkdir tests
mkdir scripts
mkdir config
mkdir logs
mkdir temp
mkdir docs
mkdir examples
mkdir "examples\sample_configs"

# Verificar estructura creada
tree /F
```

## 🐍 Paso 2: Configurar Entorno Virtual de Python

```powershell
# Verificar que Python esté instalado
python --version
# Debería mostrar algo como: Python 3.11.x

# Crear entorno virtual
python -m venv venv_find_docs

# Activar entorno virtual
venv_find_docs\Scripts\activate

# Verificar que está activado (debería mostrar (venv_find_docs) al inicio)
# Tu prompt se verá así: (venv_find_docs) PS C:\DevOps\DOTNET CLI\mcp\FIND_DOCUMENTS>
```

## 📦 Paso 3: Instalar Dependencias

### Dependencias Básicas (Obligatorias)
```powershell
# Actualizar pip
python -m pip install --upgrade pip

# Instalar dependencias core una por una
pip install google-auth
pip install google-auth-oauthlib
pip install google-api-python-client
pip install pandas
pip install openpyxl
pip install python-dotenv
```

### Dependencias Adicionales (Recomendadas)
```powershell
# Para interfaz mejorada
pip install tqdm
pip install colorama

# Para procesamiento de documentos
pip install PyPDF2
pip install python-docx
pip install Pillow
```

### Dependencias de Testing (Opcional)
```powershell
# Solo si vas a hacer desarrollo
pip install pytest
pip install pytest-asyncio
```

### Verificar Instalación
```powershell
# Probar que todo se instaló correctamente
python -c "import google.auth, pandas, openpyxl; print('✅ Dependencias básicas OK')"

# Ver lista completa de paquetes instalados
pip list
```

## 📄 Paso 4: Crear Archivos de Configuración

### 4.1 Crear requirements.txt
```powershell
# Crear archivo requirements.txt
@"
# FIND_DOCUMENTS - Dependencias Core
google-auth>=2.15.0
google-auth-oauthlib>=0.8.0
google-api-python-client>=2.100.0
gspread>=5.11.0
pandas>=1.5.0
openpyxl>=3.1.0
python-dateutil>=2.8.2
python-dotenv>=1.0.0
requests>=2.28.0
tqdm>=4.65.0
colorama>=0.4.6
PyPDF2>=3.0.0
python-docx>=0.8.11
Pillow>=9.5.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8
```

### 4.2 Crear .env.template
```powershell
@"
# Configuración de Email
EMAIL_USERNAME=tu-email@gmail.com
EMAIL_PASSWORD=tu-app-password-aqui

# Google APIs
GOOGLE_CREDENTIALS_PATH=./config/credentials.json
GOOGLE_TOKEN_PATH=./config/token.json

# Configuración del proyecto
PROJECT_NAME=FIND_DOCUMENTS
DEFAULT_FOLDER_NAME=Documentos_Procesados
LOG_LEVEL=INFO

# Configuraciones opcionales
MAX_EMAILS_PER_BATCH=100
ENABLE_DEBUG_MODE=false
AUTO_SEND_REPORT=true

# Rutas de trabajo
TEMP_DIR=./temp
LOGS_DIR=./logs
CONFIG_DIR=./config
"@ | Out-File -FilePath ".env.template" -Encoding UTF8
```

### 4.3 Crear config.json.template
```powershell
@"
{
  "email_credentials": {
    "server": "imap.gmail.com",
    "port": 993,
    "username": "tu-email@gmail.com",
    "password": "tu-app-password"
  },
  "search_parameters": {
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "keywords": [
      "factura",
      "invoice",
      "bill",
      "receipt",
      "payment"
    ],
    "folder_name": "Facturas_2024"
  },
  "processing_options": {
    "max_emails": 1000,
    "enable_ai_extraction": true,
    "create_backup": true,
    "send_completion_report": true
  },
  "google_services": {
    "credentials_path": "./config/credentials.json",
    "token_path": "./config/token.json",
    "drive_folder_root": "FIND_DOCUMENTS"
  },
  "notification_settings": {
    "email_reports": true,
    "progress_updates": true,
    "error_notifications": true
  }
}
"@ | Out-File -FilePath "config.json.template" -Encoding UTF8
```

### 4.4 Crear .gitignore
```powershell
@"
# Entorno virtual
venv_find_docs/
env/
ENV/

# Archivos de configuración sensibles
.env
config/credentials.json
config/token.json
config/config.json

# Logs
logs/*.log
*.log

# Archivos temporales
temp/*
!temp/.gitkeep
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# Archivos del sistema
.DS_Store
Thumbs.db
desktop.ini

# IDEs
.vscode/settings.json
.idea/
*.swp
*.swo

# Archivos de prueba
test_data/
sample_emails/

# Documentos procesados
processed_documents/
output/

# Respaldos
backup/
*.bak
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8
```

### 4.5 Crear README.md
```powershell
@"
# 🚀 FIND_DOCUMENTS - Procesador Inteligente de Correos y Facturas

Sistema automatizado para procesar correos electrónicos, extraer facturas y organizarlas en Google Drive.

## ✨ Características Principales

- 📧 **Búsqueda inteligente** de correos con filtros avanzados
- 🤖 **Extracción automática** de datos de facturas
- 📁 **Organización automática** en Google Drive por fecha
- 📊 **Hojas de cálculo automáticas** con datos procesados
- 📈 **Reportes en tiempo real** con estadísticas de progreso
- 📬 **Notificaciones automáticas** por email al finalizar

## 📋 Uso Básico

1. Configurar credenciales en config/config.json
2. Ejecutar: python src/find_documents_main.py
3. Revisar resultados en Google Drive

## 📖 Documentación

Ver archivos en docs/ para más información.
"@ | Out-File -FilePath "README.md" -Encoding UTF8
```

## 📄 Paso 5: Crear Archivos .gitkeep para Carpetas Vacías

```powershell
# Crear archivos .gitkeep para que Git trackee las carpetas vacías
"" | Out-File -FilePath "temp\.gitkeep" -Encoding UTF8
"" | Out-File -FilePath "logs\.gitkeep" -Encoding UTF8
```

## 🧪 Paso 6: Crear Script de Verificación

```powershell
# Crear script de verificación en scripts/test_installation.py
@"
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
"@ | Out-File -FilePath "scripts\test_installation.py" -Encoding UTF8
```

## ✅ Paso 7: Verificar Instalación Completa

```powershell
# Ejecutar script de verificación
python scripts\test_installation.py

# Debería mostrar algo como:
# 🎉 ¡TODO PERFECTO! Instalación completada exitosamente
```

## 🗂️ Paso 8: Crear Archivos de Configuración Personales

```powershell
# Copiar templates a archivos reales
Copy-Item ".env.template" ".env"
Copy-Item "config.json.template" "config\config.json"

# Editar .env con tus datos reales
notepad .env

# Editar config.json con tus credenciales
notepad config\config.json
```

## 🎯 Verificación Final

### Estructura Final Esperada:
```
FIND_DOCUMENTS/
├── venv_find_docs/          # Entorno virtual
├── src/                     # Código fuente (crear después)
├── tests/                   # Tests
├── scripts/
│   └── test_installation.py
├── config/
│   └── config.json          # Tu configuración
├── logs/
│   └── .gitkeep
├── temp/
│   └── .gitkeep
├── docs/                    # Documentación
├── examples/                # Ejemplos
├── requirements.txt
├── .env                     # Tu configuración de ambiente
├── .env.template
├── config.json.template
├── .gitignore
└── README.md
```

### Comandos de Verificación:
```powershell
# Ver estructura
tree /F

# Verificar entorno virtual activo
python -c "import sys; print('✅ Entorno virtual activo' if 'venv_find_docs' in sys.executable else '❌ Activar entorno virtual')"

# Verificar dependencias
python scripts\test_installation.py

# Ver paquetes instalados
pip list | findstr google
```

## 🚀 ¡Listo!

Tu proyecto está configurado manualmente y listo para el desarrollo. 

**¿Quieres que continuemos creando los archivos de código principal (como `src/find_documents_main.py`) o prefieres configurar primero las credenciales de Google?**