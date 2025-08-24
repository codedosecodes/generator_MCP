# 🚀 FIND_DOCUMENTS - Sistema MCP de Procesamiento de Correos y Facturas

## 📋 Descripción del Sistema

## 📋 Descripción del Sistema

Esta aplicación utiliza el **Model Context Protocol (MCP)** para automatizar completamente el proceso de:

1. **Búsqueda inteligente de correos** con filtros específicos
2. **Extracción automática de datos de facturas** usando IA
3. **Organización automática en Google Drive** con estructura jerárquica
4. **Creación de hojas de cálculo** con datos procesados
5. **Reportes automáticos** vía email

## 🛠️ Herramientas y Prerequisitos para Windows

### 📋 Lista Completa de Herramientas Requeridas

#### 1. **Python 3.9+ (OBLIGATORIO)**
- **Propósito**: Lenguaje base de la aplicación
- **Versión mínima**: Python 3.9
- **Versión recomendada**: Python 3.11
- **Descarga**: [python.org](https://www.python.org/downloads/windows/)

#### 2. **Git para Windows (RECOMENDADO)**
- **Propósito**: Control de versiones y clonado de repositorios
- **Descarga**: [git-scm.com](https://git-scm.com/download/win)
- **Incluye**: Git Bash, Git GUI, integración con Windows

#### 3. **Visual Studio Code (RECOMENDADO)**
- **Propósito**: Editor de código principal
- **Descarga**: [code.visualstudio.com](https://code.visualstudio.com/download)
- **Extensiones necesarias**:
  - Python
  - Python Debugger
  - Pylance
  - Python Docstring Generator

#### 4. **Windows Terminal (OPCIONAL pero RECOMENDADO)**
- **Propósito**: Terminal moderna para Windows
- **Instalación**: Microsoft Store → "Windows Terminal"
- **Alternativa**: Command Prompt o PowerShell nativo

#### 5. **Google Chrome/Edge (PARA OAUTH2)**
- **Propósito**: Autenticación con Google APIs
- **Requerido para**: Proceso de autorización OAuth2

### 🔧 Software Adicional (Opcional)

#### **Para Desarrollo Avanzado:**
- **PyCharm Community**: IDE Python completo
- **Postman**: Testing de APIs
- **DB Browser for SQLite**: Ver datos locales
- **FileZilla**: Transferencia de archivos (si necesitas)

#### **Para Debugging:**
- **Process Monitor**: Monitorear archivos y procesos
- **Wireshark**: Análisis de red (avanzado)

### 💻 Instalación Paso a Paso en Windows

#### **PASO 1: Instalación de Python**

```powershell
# Opción 1: Descarga manual desde python.org
# 1. Ir a https://www.python.org/downloads/windows/
# 2. Descargar Python 3.11.x (Windows installer 64-bit)
# 3. IMPORTANTE: Marcar "Add Python to PATH"
# 4. Ejecutar instalador como administrador

# Opción 2: Usando winget (Windows 10/11)
winget install Python.Python.3.11

# Opción 3: Usando Chocolatey
choco install python3

# Verificar instalación
python --version
pip --version
```

#### **PASO 2: Configuración del Entorno Virtual**

```powershell
# Abrir PowerShell como Administrador

# Navegar a tu directorio de proyectos
cd C:\Users\%USERNAME%\Documents\
mkdir PythonProjects
cd PythonProjects

# Crear carpeta del proyecto
mkdir FIND_DOCUMENTS
cd FIND_DOCUMENTS

# Crear entorno virtual
python -m venv venv_find_docs

# Activar entorno virtual
venv_find_docs\Scripts\activate

# Verificar activación (debería mostrar (venv_find_docs))
```

#### **PASO 3: Instalación de Dependencias**

```powershell
# Con el entorno virtual activado

# Actualizar pip
python -m pip install --upgrade pip

# Crear archivo requirements.txt
echo mcp>=0.4.0 > requirements.txt
echo google-auth>=2.15.0 >> requirements.txt
echo google-auth-oauthlib>=0.8.0 >> requirements.txt
echo google-auth-httplib2>=0.1.1 >> requirements.txt
echo google-api-python-client>=2.100.0 >> requirements.txt
echo gspread>=5.11.0 >> requirements.txt
echo oauth2client>=4.1.3 >> requirements.txt
echo pandas>=1.5.0 >> requirements.txt
echo openpyxl>=3.1.0 >> requirements.txt
echo python-dateutil>=2.8.2 >> requirements.txt

# Instalar todas las dependencias
pip install -r requirements.txt

# Verificar instalación
pip list
```

#### **PASO 4: Configuración de Visual Studio Code**

```powershell
# Instalar VS Code si no lo tienes
winget install Microsoft.VisualStudioCode

# Abrir el proyecto en VS Code
code .

# En VS Code, instalar extensiones:
# 1. Ctrl+Shift+X para abrir extensiones
# 2. Buscar e instalar:
#    - Python (Microsoft)
#    - Python Debugger
#    - Pylance
#    - Python Docstring Generator
```

**Configuración de VS Code (settings.json)**:
```json
{
    "python.interpreter.path": ".\\venv_find_docs\\Scripts\\python.exe",
    "python.terminal.activateEnvironment": true,
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black"
}
```

#### **PASO 5: Configuración de Git (si es necesario)**

```powershell
# Instalar Git
winget install Git.Git

# Configuración inicial
git config --global user.name "Tu Nombre"
git config --global user.email "tu-email@ejemplo.com"

# Verificar configuración
git config --list
```

### 🔐 Configuración de Credenciales Windows

#### **Variables de Entorno (Método Seguro)**

```powershell
# Opción 1: Usando PowerShell (temporal)
$env:EMAIL_PASSWORD="tu-password-de-app"
$env:EMAIL_USERNAME="tu-email@gmail.com"

# Opción 2: Variables de sistema permanentes
# 1. Win + R → sysdm.cpl
# 2. Pestaña "Opciones Avanzadas"
# 3. "Variables de entorno"
# 4. Agregar nuevas variables:
#    - EMAIL_USERNAME
#    - EMAIL_PASSWORD
#    - GOOGLE_CREDENTIALS_PATH
```

#### **Archivo .env (Método Alternativo)**

```powershell
# Instalar python-dotenv
pip install python-dotenv

# Crear archivo .env en la raíz del proyecto
echo EMAIL_USERNAME=tu-email@gmail.com > .env
echo EMAIL_PASSWORD=tu-app-password >> .env
echo GOOGLE_CREDENTIALS_PATH=./credentials.json >> .env
echo FOLDER_NAME=Documentos_Procesados >> .env

# IMPORTANTE: Agregar .env al .gitignore
echo .env >> .gitignore
```

### 🚀 Métodos de Instalación

#### **Método 1: Instalación Completa Automatizada**

```powershell
# Script de instalación automática (run_setup.ps1)
# Guardar como setup_find_documents.ps1

# Verificar si Python está instalado
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "✅ Python encontrado" -ForegroundColor Green
    python --version
} else {
    Write-Host "❌ Python no encontrado. Instalando..." -ForegroundColor Red
    winget install Python.Python.3.11
}

# Crear directorio del proyecto
$projectPath = "$env:USERPROFILE\Documents\FIND_DOCUMENTS"
if (!(Test-Path $projectPath)) {
    New-Item -ItemType Directory -Path $projectPath
    Write-Host "✅ Directorio creado: $projectPath" -ForegroundColor Green
}

Set-Location $projectPath

# Crear entorno virtual
python -m venv venv_find_docs
Write-Host "✅ Entorno virtual creado" -ForegroundColor Green

# Activar entorno virtual
& "venv_find_docs\Scripts\Activate.ps1"

# Instalar dependencias
pip install --upgrade pip
pip install mcp google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client gspread oauth2client pandas openpyxl python-dateutil python-dotenv

Write-Host "✅ Instalación completada!" -ForegroundColor Green
Write-Host "📁 Proyecto ubicado en: $projectPath" -ForegroundColor Yellow
Write-Host "🐍 Para activar el entorno: venv_find_docs\Scripts\activate" -ForegroundColor Yellow
```

**Ejecutar el script:**
```powershell
# Cambiar política de ejecución (una sola vez)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Ejecutar script de instalación
.\setup_find_documents.ps1
```

#### **Método 2: Usando Conda/Miniconda**

```powershell
# Instalar Miniconda
winget install Anaconda.Miniconda3

# Reiniciar PowerShell o abrir Anaconda Prompt

# Crear entorno conda
conda create -n find_docs python=3.11
conda activate find_docs

# Instalar dependencias básicas con conda
conda install pandas openpyxl requests

# Instalar dependencias específicas con pip
pip install mcp google-auth google-auth-oauthlib google-api-python-client gspread oauth2client
```

#### **Método 3: Docker en Windows (Avanzado)**

```powershell
# Instalar Docker Desktop
winget install Docker.DockerDesktop

# Crear Dockerfile
@'
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "find_documents_mcp.py"]
'@ | Out-File -FilePath Dockerfile -Encoding UTF8

# Crear docker-compose.yml
@'
version: '3.8'
services:
  find-documents:
    build: .
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - EMAIL_USERNAME=${EMAIL_USERNAME}
      - EMAIL_PASSWORD=${EMAIL_PASSWORD}
'@ | Out-File -FilePath docker-compose.yml -Encoding UTF8

# Construir y ejecutar
docker-compose up --build
```

### 🔍 Verificación de Instalación

#### **Script de Verificación Completa**

```powershell
# Crear test_installation.py
@'
import sys
import subprocess
import importlib

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
        'mcp'
    ]
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - Instalado")
        except ImportError:
            print(f"❌ {package} - Faltante")
            return False
    
    return True

def check_environment():
    import os
    
    # Verificar variables de entorno
    env_vars = ['EMAIL_USERNAME', 'EMAIL_PASSWORD']
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ Variable {var} - Configurada")
        else:
            print(f"⚠️  Variable {var} - No configurada")

def main():
    print("🔍 Verificando instalación de FIND_DOCUMENTS")
    print("=" * 50)
    
    python_ok = check_python_version()
    packages_ok = check_packages()
    
    print("\n🌍 Variables de entorno:")
    check_environment()
    
    print("\n" + "=" * 50)
    if python_ok and packages_ok:
        print("✅ ¡Instalación completada exitosamente!")
        print("🚀 Listo para ejecutar FIND_DOCUMENTS")
    else:
        print("❌ Instalación incompleta. Revisar errores arriba.")

if __name__ == "__main__":
    main()
'@ | Out-File -FilePath test_installation.py -Encoding UTF8

# Ejecutar verificación
python test_installation.py
```

### 🚨 Solución de Problemas Comunes en Windows

#### **Error: 'python' no se reconoce como comando**
```powershell
# Solución 1: Reinstalar Python marcando "Add to PATH"
# Solución 2: Agregar manualmente al PATH
$env:PATH += ";C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311;C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python311\Scripts"
```

#### **Error: Scripts deshabilitados en PowerShell**
```powershell
# Cambiar política de ejecución
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### **Error: Acceso denegado al instalar paquetes**
```powershell
# Usar --user flag
pip install --user package_name

# O ejecutar PowerShell como administrador
```

#### **Error: SSL Certificate verification failed**
```powershell
# Actualizar certificados
pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org --upgrade pip

# O usar certificados corporativos
pip install --cert path\to\certificate.pem package_name
```

#### **Error: Long path names en Windows**
```powershell
# Habilitar long paths en Windows (como administrador)
# En el registro: HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\FileSystem
# Crear DWORD: LongPathsEnabled = 1

# O usar subst para paths cortos
subst P: C:\Users\%USERNAME%\Documents\PythonProjects\FIND_DOCUMENTS
cd P:\
```

### 📁 Estructura Final del Proyecto

```
C:\Users\[TuUsuario]\Documents\FIND_DOCUMENTS\
├── venv_find_docs\                    # Entorno virtual
├── find_documents_mcp.py             # Aplicación principal
├── requirements.txt                   # Dependencias
├── config.json                       # Configuración
├── credentials.json                   # Credenciales Google (a crear)
├── token.json                        # Token OAuth (se genera automático)
├── .env                              # Variables de entorno (opcional)
├── test_installation.py              # Script de verificación
├── setup_find_documents.ps1          # Script de instalación
├── logs\                             # Carpeta de logs
├── temp\                             # Archivos temporales
└── docs\                             # Documentación
```

### 🎯 Comandos Útiles Post-Instalación

```powershell
# Activar entorno virtual
venv_find_docs\Scripts\activate

# Verificar instalación
python test_installation.py

# Ejecutar aplicación
python find_documents_mcp.py

# Ver logs en tiempo real
Get-Content .\logs\find_documents.log -Wait

# Desactivar entorno virtual
deactivate

# Actualizar dependencias
pip list --outdated
pip install --upgrade package_name
```

¡Con esta guía completa ya puedes instalar y configurar todo en tu ambiente Windows! 💪

## 🛠️ Instalación y Configuración

### Dependencias Requeridas

```bash
# Instalar dependencias Python
pip install -r requirements.txt
```

**requirements.txt:**
```
mcp>=0.4.0
google-auth>=2.15.0
google-auth-oauthlib>=0.8.0
google-auth-httplib2>=0.1.1
google-api-python-client>=2.100.0
gspread>=5.11.0
oauth2client>=4.1.3
pandas>=1.5.0
openpyxl>=3.1.0
python-dateutil>=2.8.2
```

### 1. Configuración de Google APIs

#### Paso 1: Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita las siguientes APIs:
   - Google Drive API
   - Google Sheets API
   - Gmail API (opcional, para envío de reportes)

#### Paso 2: Crear Credenciales OAuth2

1. Ve a "Credenciales" en la consola
2. Crear credenciales → ID de cliente OAuth 2.0
3. Tipo de aplicación: Aplicación de escritorio
4. Descargar el archivo JSON como `credentials.json`

**Estructura de credentials.json:**
```json
{
  "installed": {
    "client_id": "tu-client-id.googleusercontent.com",
    "project_id": "tu-proyecto",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "client_secret": "tu-client-secret",
    "redirect_uris": ["http://localhost"]
  }
}
```

### 2. Configuración de Email

#### Para Gmail:
1. Habilitar autenticación de 2 factores
2. Generar "Contraseña de aplicación" específica
3. Usar esta contraseña en lugar de la contraseña principal

#### Para otros proveedores:
- **Outlook/Hotmail**: `outlook.office365.com:993`
- **Yahoo**: `imap.mail.yahoo.com:993`
- **Corporativo**: Consultar con administrador IT

### 3. Configuración de Parámetros

**Crear archivo config.json:**
```json
{
  "email_credentials": {
    "server": "imap.gmail.com",
    "port": 993,
    "username": "tu-email@gmail.com",
    "password": "tu-app-password-de-16-caracteres"
  },
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "keywords": [
    "factura",
    "invoice", 
    "bill",
    "receipt",
    "payment",
    "cobro"
  ],
  "folder_name": "Facturas_2024_Procesadas"
}
```

## 🚀 Uso del Sistema

### Ejecución Básica

```python
import asyncio
from find_documents_mcp import FindDocumentsApp
import json

async def run_processing():
    # Cargar configuración
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Crear aplicación
    app = FindDocumentsApp()
    
    # Ejecutar procesamiento completo
    result = await app.run_complete_process(config)
    
    print("Resultado:", json.dumps(result, indent=2))

# Ejecutar
asyncio.run(run_processing())
```

### Ejecución por Línea de Comandos

```bash
# Configuración inicial
python find_documents_mcp.py setup

# Procesamiento completo
python find_documents_mcp.py

# Con archivo de configuración específico
python find_documents_mcp.py --config mi_config.json
```

## 📊 Estructura de Salida

### Google Drive
```
FIND_DOCUMENTS/
└── [folder_name]/
    ├── [folder_name]_Documentos_Procesados.xlsx
    ├── 2024/
    │   ├── 01/
    │   │   ├── Email_12345/
    │   │   │   ├── factura.pdf
    │   │   │   └── anexo.xlsx
    │   │   └── Email_12346/
    │   └── 02/
    └── 2023/
```

### Hoja de Cálculo
| Fecha Correo | From | To | Subject | Tiene Adjuntos | Ruta Adjuntos | Valor Factura | Concepto | Quien Facturo | ID Correo | Fecha Procesamiento |
|--------------|------|----|---------|--------------|--------------|--------------|---------|--------------|-----------|--------------------|

## 🔍 Funcionalidades MCP

### Resources Disponibles
- `mcp://email/search/filtered` - Búsqueda filtrada de emails
- `mcp://drive/folder/structure` - Estructura de carpetas actual
- `mcp://spreadsheet/data/current` - Datos de la hoja de cálculo
- `mcp://stats/processing/current` - Estadísticas de procesamiento

### Tools Disponibles
- `process_email_search` - Procesamiento completo
- `create_drive_structure` - Creación de estructura de carpetas
- `extract_invoice_data` - Extracción de datos con IA
- `send_completion_report` - Envío de reporte final

### Prompts Inteligentes
- Análisis de contenido de emails para identificar facturas
- Extracción automática de montos, conceptos y proveedores
- Categorización inteligente de documentos

## 📈 Monitoreo y Estadísticas

### Durante el Procesamiento
```
🚀 Iniciando procesamiento de correos...
📧 Encontrados 45 correos
📊 Procesando 12/45 (26.7%)
✅ Estructura de carpetas creada: FIND_DOCUMENTS/Facturas_2024
📊 Hoja de cálculo creada: 1a2b3c4d5e6f...
```

### Estadísticas Finales
```json
{
  "total_emails": 45,
  "processed_emails": 45,
  "successful_extractions": 42,
  "failed_extractions": 3,
  "success_rate": 93.3,
  "total_attachments": 67
}
```

### Reporte por Email
Al finalizar, se envía un reporte HTML con:
- Tabla de estadísticas completa
- Enlaces a carpetas de Google Drive
- Resumen de documentos procesados
- Timestamp de finalización

## ⚙️ Configuraciones Avanzadas

### Filtros de Búsqueda Personalizados

```python
# Búsqueda por remitente específico
keywords = ["empresa-proveedora.com"]

# Búsqueda por conceptos específicos
keywords = ["hosting", "dominio", "servidor"]

# Búsqueda combinada
keywords = ["factura AND servicios", "invoice AND consulting"]
```

### Personalización de Extracción

```python
# Patrones personalizados para extraer datos
custom_patterns = {
    'tax_id': r'nit:?\s*([0-9-]+)',
    'due_date': r'vencimiento:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
    'category': r'categor[íi]a:?\s*([^\n]+)'
}
```

### Integración con Otros Sistemas

```python
# Webhook para notificaciones
webhook_config = {
    "url": "https://hooks.slack.com/services/...",
    "on_completion": True,
    "on_error": True
}

# Base de datos externa
database_config = {
    "connection_string": "postgresql://user:pass@host:port/db",
    "table_name": "processed_invoices"
}
```

## 🔧 Solución de Problemas

### Errores Comunes

#### Error de Autenticación Email
```
❌ Error: [AUTHENTICATIONFAILED] Invalid credentials
```
**Solución**: Verificar que la contraseña de aplicación esté correcta.

#### Error de Permisos Google Drive
```
❌ Error: insufficient permissions
```
**Solución**: Reautenticar y asegurar que todos los scopes están habilitados.

#### Error de Cuota de API
```
❌ Error: quota exceeded
```
**Solución**: Esperar o solicitar incremento de cuota en Google Cloud Console.

### Debugging

#### Activar Logs Detallados
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Modo de Prueba
```python
# Procesar solo 5 emails para pruebas
test_config = config.copy()
test_config["max_emails"] = 5
```

## 📚 Ejemplos de Uso Específicos

### Caso 1: Facturas de Servicios Públicos
```json
{
  "keywords": ["epm", "unes", "gas natural", "acueducto", "energia"],
  "folder_name": "Servicios_Publicos_2024",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### Caso 2: Facturas de Proveedores IT
```json
{
  "keywords": ["hosting", "dominio", "ssl", "servidor", "microsoft", "adobe"],
  "folder_name": "Servicios_IT_2024",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

### Caso 3: Recibos de Nómina
```json
{
  "keywords": ["nomina", "payroll", "salario", "liquidacion"],
  "folder_name": "Nomina_2024",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

## 🔐 Consideraciones de Seguridad

### Manejo de Credenciales
- Nunca hardcodear passwords en el código
- Usar variables de entorno para datos sensibles
- Rotar passwords regularmente

### Permisos de Google Drive
- Otorgar permisos mínimos necesarios
- Revisar aplicaciones conectadas periódicamente
- Usar cuentas de servicio para producción

### Datos Sensibles
- Los adjuntos se almacenan en Google Drive privado
- Los datos de la hoja de cálculo son privados
- Considerar cifrado adicional para datos altamente sensibles

## 🚀 Escalabilidad y Performance

### Para Grandes Volúmenes
- Implementar procesamiento en lotes
- Usar workers paralelos
- Considerar base de datos para metadata

### Optimizaciones
- Cache de resultados de extracción
- Compresión de adjuntos grandes
- Limpieza automática de archivos temporales

## 📞 Soporte

### Logs de Sistema
Todos los logs se almacenan en `find_documents.log`

### Contacto
Para soporte técnico o mejoras, crear issue en el repositorio del proyecto.

---

**¡Sistema FIND_DOCUMENTS listo para automatizar tu procesamiento de facturas y documentos!** 🎉