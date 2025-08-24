@echo off
:: validate_setup.bat - Validador de configuración para Windows
title Validador FIND_DOCUMENTS
color 0B
chcp 65001 >nul
setlocal enabledelayedexpansion

echo.
echo ========================================================
echo             VALIDADOR FIND_DOCUMENTS
echo ========================================================
echo   Verificacion de configuracion Google APIs y Email
echo ========================================================
echo.

:: Verificar que estamos en la carpeta correcta
if not exist "src\" (
    echo [X] Error: No se encuentra la carpeta src/
    echo [!] Ejecutar desde la carpeta raiz del proyecto FIND_DOCUMENTS
    echo.
    pause
    exit /b 1
)

:: Verificar que Python esta disponible
python --version >nul 2>&1
if errorlevel 1 (
    echo [X] Error: Python no esta instalado o no esta en PATH
    echo [!] Instalar Python desde: https://python.org/downloads
    echo.
    pause
    exit /b 1
)

:: Activar entorno virtual si existe
if exist "venv_find_docs\Scripts\activate.bat" (
    echo [i] Activando entorno virtual...
    call venv_find_docs\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [!] Entorno virtual no encontrado, usando Python del sistema
)

echo.
echo Selecciona el tipo de validacion:
echo.
echo [1] Verificacion rapida (sin conexiones externas)
echo [2] Validacion completa (incluye conexiones a Google y Email)
echo [3] Solo mostrar guia de configuracion
echo [4] Crear archivos de configuracion de ejemplo
echo [0] Salir
echo.

set /p choice="Selecciona opcion (0-4): "

if "%choice%"=="1" goto QUICK_CHECK
if "%choice%"=="2" goto FULL_VALIDATION
if "%choice%"=="3" goto SHOW_HELP
if "%choice%"=="4" goto CREATE_EXAMPLES
if "%choice%"=="0" goto EXIT

echo [X] Opcion invalida
pause
goto :eof

:QUICK_CHECK
echo.
echo ===============================================
echo         VERIFICACION RAPIDA
echo ===============================================
echo.

python scripts\quick_check.py
set exit_code=%ERRORLEVEL%

echo.
if %exit_code%==0 (
    echo [OK] Verificacion rapida exitosa
    echo [!] Ejecutar validacion completa: validate_setup.bat y seleccionar opcion 2
) else if %exit_code%==1 (
    echo [!] Verificacion con advertencias
) else (
    echo [X] Verificacion fallida
)

goto PAUSE_EXIT

:FULL_VALIDATION
echo.
echo ===============================================
echo         VALIDACION COMPLETA
echo ===============================================
echo [!] Esta validacion probara conexiones reales
echo [!] Puede abrir navegador para autorizacion Google
echo.

set /p confirm="Continuar con validacion completa? (y/n): "
if /i not "%confirm%"=="y" goto :eof

echo.
echo Ejecutando validacion completa...
python scripts\validate_setup.py
set exit_code=%ERRORLEVEL%

echo.
if %exit_code%==0 (
    echo [OK] VALIDACION COMPLETA EXITOSA!
    echo [OK] Tu configuracion esta lista para usar
    echo.
    echo Comandos disponibles:
    echo   python src\find_documents_main.py    # Ejecutar aplicacion
    echo   .\git_menu.bat                       # Menu Git
) else if %exit_code%==1 (
    echo [!] VALIDACION PARCIAL
    echo [!] Configuracion basica OK, pero hay advertencias
) else (
    echo [X] VALIDACION FALLIDA
    echo [X] Revisar errores y completar configuracion
)

goto PAUSE_EXIT

:SHOW_HELP
echo.
echo ===============================================
echo         GUIA DE CONFIGURACION
echo ===============================================
echo.

python scripts\validate_setup.py --help-setup

goto PAUSE_EXIT

:CREATE_EXAMPLES
echo.
echo ===============================================
echo      CREAR ARCHIVOS DE EJEMPLO
echo ===============================================
echo.

:: Crear config.json desde template si no existe
if not exist "config\config.json" (
    if exist "config.json.template" (
        copy config.json.template config\config.json >nul
        echo [OK] config\config.json creado desde template
    ) else (
        echo [!] Template no encontrado, creando configuracion basica...
        
        if not exist "config\" mkdir config
        
        (
            echo {
            echo   "email_credentials": {
            echo     "server": "imap.gmail.com",
            echo     "port": 993,
            echo     "username": "tu-email@gmail.com",
            echo     "password": "tu-app-password"
            echo   },
            echo   "search_parameters": {
            echo     "start_date": "2024-01-01",
            echo     "end_date": "2024-12-31",
            echo     "keywords": ["factura", "invoice", "bill"],
            echo     "folder_name": "Documentos_2024"
            echo   },
            echo   "google_services": {
            echo     "credentials_path": "./config/credentials.json",
            echo     "token_path": "./config/token.json",
            echo     "drive_folder_root": "FIND_DOCUMENTS"
            echo   }
            echo }
        ) > config\config.json
        
        echo [OK] config\config.json creado con valores por defecto
    )
) else (
    echo [i] config\config.json ya existe
)

:: Crear .env desde template si no existe
if not exist ".env" (
    if exist ".env.template" (
        copy .env.template .env >nul
        echo [OK] .env creado desde template
    ) else (
        echo [!] Creando .env basico...
        (
            echo # FIND_DOCUMENTS - Variables de Entorno
            echo EMAIL_USERNAME=tu-email@gmail.com
            echo EMAIL_PASSWORD=tu-app-password
            echo GOOGLE_CREDENTIALS_PATH=./config/credentials.json
            echo DEFAULT_FOLDER_NAME=Documentos_Procesados
        ) > .env
        echo [OK] .env creado con valores por defecto
    )
) else (
    echo [i] .env ya existe
)

echo.
echo [OK] Archivos de configuracion preparados
echo.
echo PROXIMOS PASOS:
echo 1. Editar config\config.json con tus datos reales
echo 2. Configurar Google APIs y descargar credentials.json
echo 3. Ejecutar validacion: validate_setup.bat (opcion 1 o 2)
echo.
echo IMPORTANTE:
echo - Para Gmail: usar App Password, no contraseña normal
echo - Google APIs: descargar credentials.json a carpeta config\

goto PAUSE_EXIT

:PAUSE_EXIT
echo.
echo ===============================================
set /p return_choice="[Enter] Continuar | [M]enu principal | [S]alir: "

if /i "%return_choice%"=="M" (
    cls
    goto :eof
)
if /i "%return_choice%"=="S" goto EXIT

goto EXIT

:EXIT
echo.
echo ===============================================
echo              HASTA LUEGO!
echo ===============================================
echo.
echo Gracias por usar el validador FIND_DOCUMENTS
echo.
echo COMANDOS UTILES:
echo   validate_setup.bat       # Este validador
echo   .\git_menu.bat           # Menu Git
echo   python src\find_documents_main.py  # Ejecutar aplicacion
echo.
pause
exit /b 0