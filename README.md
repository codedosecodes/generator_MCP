# 🚀 DOCFIND - Procesador Inteligente de Correos y Facturas

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



# 📁 Estructura Completa del Proyecto DOCUFIND

## 🗂️ Árbol de Archivos del Proyecto

```
DOCUFIND/
├── 📄 README.md                          # Guía principal del proyecto
├── 📄 INSTALLATION_GUIDE.md              # Guía de instalación detallada
├── 📄 requirements.txt                   # Dependencias de Python
├── 📄 setup_find_documents.ps1           # Script de instalación Windows
├── 📄 .env.template                      # Plantilla de variables de entorno
├── 📄 .gitignore                         # Archivos a ignorar en Git
├── 📄 config.json.template               # Plantilla de configuración
├── 📄 docker-compose.yml                 # Configuración Docker (opcional)
├── 📄 Dockerfile                         # Imagen Docker (opcional)
├── 
├── 📂 src/                               # Código fuente principal
│   ├── 📄 __init__.py
│   ├── 📄 find_documents_mcp.py          # Aplicación principal MCP
│   ├── 📄 email_processor.py             # Procesador de correos
│   ├── 📄 google_drive_client.py         # Cliente Google Drive
│   ├── 📄 invoice_extractor.py           # Extractor de datos de facturas
│   └── 📄 config_manager.py              # Gestor de configuraciones
│   
├── 📂 tests/                             # Tests unitarios
│   ├── 📄 __init__.py
│   ├── 📄 test_email_processor.py
│   ├── 📄 test_google_drive.py
│   ├── 📄 test_invoice_extractor.py
│   └── 📄 test_integration.py
│   
├── 📂 scripts/                           # Scripts de utilidad
│   ├── 📄 test_installation.py           # Verificar instalación
│   ├── 📄 validate_credentials.py        # Validar credenciales
│   ├── 📄 setup_google_auth.py           # Configurar Google OAuth
│   └── 📄 cleanup_temp_files.py          # Limpiar archivos temporales
│   
├── 📂 config/                            # Configuraciones
│   ├── 📄 credentials.json               # Credenciales Google (no incluir en Git)
│   ├── 📄 token.json                     # Token OAuth (se genera automático)
│   ├── 📄 config.json                    # Configuración principal
│   └── 📄 email_providers.json           # Configuraciones de proveedores email
│   
├── 📂 logs/                              # Archivos de log
│   ├── 📄 find_documents.log
│   ├── 📄 errors.log
│   └── 📄 processing_stats.log
│   
├── 📂 temp/                              # Archivos temporales
│   └── 📄 .gitkeep
│   
├── 📂 docs/                              # Documentación adicional
│   ├── 📄 API_REFERENCE.md               # Referencia de APIs
│   ├── 📄 TROUBLESHOOTING.md             # Solución de problemas
│   ├── 📄 EXAMPLES.md                    # Ejemplos de uso
│   └── 📄 CHANGELOG.md                   # Historial de cambios
│   
├── 📂 examples/                          # Ejemplos de configuración
│   ├── 📄 basic_usage.py                 # Uso básico
│   ├── 📄 advanced_filtering.py          # Filtrado avanzado
│   ├── 📄 batch_processing.py            # Procesamiento en lotes
│   └── 📂 sample_configs/                # Configuraciones de ejemplo
│       ├── 📄 gmail_config.json
│       ├── 📄 outlook_config.json
│       └── 📄 corporate_config.json
│   
└── 📂 venv_find_docs/                    # Entorno virtual (no incluir en Git)
    └── ...
```

## 📝 Archivos Principales a Crear

### 1. **README.md** - Archivo Principal
```markdown
# 🚀 FIND_DOCUMENTS - Procesador Inteligente de Correos y Facturas

Sistema automatizado que utiliza **Model Context Protocol (MCP)** para procesar correos electrónicos, extraer facturas y organizarlas en Google Drive.

## ✨ Características Principales

- 📧 **Búsqueda inteligente** de correos con filtros avanzados
- 🤖 **Extracción automática** de datos de facturas usando IA
- 📁 **Organización automática** en Google Drive por fecha
- 📊 **Hojas de cálculo automáticas** con datos procesados
- 📈 **Reportes en tiempo real** con estadísticas de progreso
- 📬 **Notificaciones automáticas** por email al finalizar

## 🚀 Instalación Rápida

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/find-documents.git
cd find-documents

# Ejecutar instalación automática (Windows)
.\setup_find_documents.ps1

# O instalación manual
python -m venv venv_find_docs
venv_find_docs\Scripts\activate
pip install -r requirements.txt
```

## 📋 Uso Básico

```python
from src.find_documents_mcp import FindDocumentsApp

# Configuración
config = {
    "email_credentials": {
        "server": "imap.gmail.com",
        "username": "tu-email@gmail.com",
        "password": "tu-app-password"
    },
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "keywords": ["factura", "invoice"],
    "folder_name": "Facturas_2024"
}

# Ejecutar
app = FindDocumentsApp()
result = await app.run_complete_process(config)
```

## 📖 Documentación

- [📘 Guía de Instalación](INSTALLATION_GUIDE.md)
- [🔧 Solución de Problemas](docs/TROUBLESHOOTING.md)
- [📚 Ejemplos](docs/EXAMPLES.md)
- [🔗 API Reference](docs/API_REFERENCE.md)

## 🤝 Contribuir

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver [LICENSE](LICENSE) para detalles.
```

### 2. **requirements.txt**
```
# MCP y componentes principales
mcp>=0.4.0

# Google APIs
google-auth>=2.15.0
google-auth-oauthlib>=0.8.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
gspread>=5.11.0
oauth2client>=4.1.3

# Procesamiento de datos
pandas>=1.5.0
openpyxl>=3.1.0
python-dateutil>=2.8.2

# Utilidades
python-dotenv>=1.0.0
requests>=2.28.0
beautifulsoup4>=4.12.0
lxml>=4.9.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0

# Logging y monitoreo
colorama>=0.4.6
tqdm>=4.65.0

# Opcional - para formatos adicionales
PyPDF2>=3.0.0
python-docx>=0.8.11
Pillow>=9.5.0
```

### 3. **setup_find_documents.ps1**
```powershell
# Script de instalación automática para Windows
Write-Host "🚀 Configurando FIND_DOCUMENTS..." -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green

# Verificar Python
try {
    $pythonVersion = python --version
    Write-Host "✅ $pythonVersion encontrado" -ForegroundColor Green
} catch {
    Write-Host "❌ Python no encontrado. Instalando..." -ForegroundColor Red
    winget install Python.Python.3.11
    Write-Host "✅ Python instalado. Reinicia PowerShell y ejecuta el script nuevamente." -ForegroundColor Yellow
    exit
}

# Crear entorno virtual
Write-Host "📦 Creando entorno virtual..." -ForegroundColor Blue
python -m venv venv_find_docs

# Activar entorno virtual
Write-Host "🔧 Activando entorno virtual..." -ForegroundColor Blue
& "venv_find_docs\Scripts\Activate.ps1"

# Actualizar pip
Write-Host "⬆️  Actualizando pip..." -ForegroundColor Blue
python -m pip install --upgrade pip

# Instalar dependencias
Write-Host "📥 Instalando dependencias..." -ForegroundColor Blue
pip install -r requirements.txt

# Crear estructura de carpetas
Write-Host "📁 Creando estructura de carpetas..." -ForegroundColor Blue
$folders = @("config", "logs", "temp", "docs", "examples", "tests", "scripts")
foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "  ✅ Creado: $folder" -ForegroundColor Green
    }
}

# Crear archivos de configuración desde templates
Write-Host "⚙️  Creando archivos de configuración..." -ForegroundColor Blue

if (!(Test-Path "config\config.json")) {
    Copy-Item "config.json.template" "config\config.json"
    Write-Host "  ✅ config.json creado desde template" -ForegroundColor Green
}

if (!(Test-Path ".env")) {
    Copy-Item ".env.template" ".env"
    Write-Host "  ✅ .env creado desde template" -ForegroundColor Green
}

# Ejecutar test de instalación
Write-Host "🔍 Verificando instalación..." -ForegroundColor Blue
python scripts\test_installation.py

Write-Host ""
Write-Host "🎉 ¡Instalación completada!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host "📋 Próximos pasos:"
Write-Host "1. Configurar Google APIs (ver INSTALLATION_GUIDE.md)"
Write-Host "2. Editar config\config.json con tus credenciales"
Write-Host "3. Ejecutar: python src\find_documents_mcp.py"
Write-Host ""
Write-Host "💡 Para activar el entorno: venv_find_docs\Scripts\activate"
Write-Host "📖 Ver documentación completa: INSTALLATION_GUIDE.md"
```

### 4. **.env.template**
```bash
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
```

### 5. **config.json.template**
```json
{
  "email_credentials": {
    "server": "imap.gmail.com",
    "port": 993,
    "username": "${EMAIL_USERNAME}",
    "password": "${EMAIL_PASSWORD}"
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
```

### 6. **.gitignore**
```gitignore
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

# Coverage reports
htmlcov/
.coverage
.coverage.*
coverage.xml

# Pytest
.pytest_cache/

# mypy
.mypy_cache/
.dmypy.json
dmypy.json
```

### 7. **docker-compose.yml** (Opcional)
```yaml
version: '3.8'

services:
  find-documents:
    build: .
    container_name: find_documents_app
    volumes:
      - ./config:/app/config
      - ./logs:/app/logs
      - ./temp:/app/temp
      - ./data:/app/data
    environment:
      - EMAIL_USERNAME=${EMAIL_USERNAME}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
      - GOOGLE_CREDENTIALS_PATH=/app/config/credentials.json
    env_file:
      - .env
    restart: unless-stopped
    
  # Opcional: Base de datos para logs
  postgres:
    image: postgres:15-alpine
    container_name: find_docs_db
    environment:
      - POSTGRES_DB=find_documents
      - POSTGRES_USER=finduser
      - POSTGRES_PASSWORD=findpass123
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🚀 Comandos de Creación del Proyecto

### **Script PowerShell para Crear Proyecto Completo**

```powershell
# create_project.ps1
param(
    [string]$ProjectPath = "$env:USERPROFILE\Documents\FIND_DOCUMENTS"
)

Write-Host "🚀 Creando proyecto FIND_DOCUMENTS..." -ForegroundColor Green
Write-Host "📍 Ubicación: $ProjectPath" -ForegroundColor Yellow

# Crear directorio principal
if (!(Test-Path $ProjectPath)) {
    New-Item -ItemType Directory -Path $ProjectPath | Out-Null
    Write-Host "✅ Directorio principal creado" -ForegroundColor Green
}

Set-Location $ProjectPath

# Crear estructura de carpetas
$folders = @(
    "src",
    "tests", 
    "scripts",
    "config",
    "logs",
    "temp",
    "docs",
    "examples",
    "examples/sample_configs"
)

foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder | Out-Null
        Write-Host "  📁 $folder" -ForegroundColor Gray
    }
}

# Crear archivos principales
$files = @{
    "README.md" = $readme_content
    "INSTALLATION_GUIDE.md" = $installation_guide_content  
    "requirements.txt" = $requirements_content
    "setup_find_documents.ps1" = $setup_script_content
    ".env.template" = $env_template_content
    "config.json.template" = $config_template_content
    ".gitignore" = $gitignore_content
    "docker-compose.yml" = $docker_compose_content
    "temp/.gitkeep" = ""
    "logs/.gitkeep" = ""
}

foreach ($file in $files.Keys) {
    if (!(Test-Path $file)) {
        $files[$file] | Out-File -FilePath $file -Encoding UTF8
        Write-Host "  📄 $file" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "✅ Proyecto creado exitosamente!" -ForegroundColor Green
Write-Host "📋 Próximos pasos:"
Write-Host "1. cd '$ProjectPath'"
Write-Host "2. .\setup_find_documents.ps1"
Write-Host "3. Configurar credenciales en config/"
Write-Host "4. python src\find_documents_mcp.py"
```

### **Ejecutar la Creación del Proyecto:**

```powershell
# Descargar y ejecutar script de creación
Invoke-WebRequest -Uri "https://tu-repo.com/create_project.ps1" -OutFile "create_project.ps1"
.\create_project.ps1

# O crear manualmente
mkdir FIND_DOCUMENTS
cd FIND_DOCUMENTS
# ... crear archivos uno por uno usando el contenido de arriba
```

¿Te parece completa esta estructura de proyecto? ¿Quieres que genere algún archivo específico adicional o que ajuste algún aspecto?


Ver archivos en docs/ para más información.
