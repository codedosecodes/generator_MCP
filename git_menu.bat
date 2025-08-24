@echo off
:: git_menu.bat - Menu interactivo para FIND_DOCUMENTS (codificacion ANSI)
title Git Menu - FIND_DOCUMENTS
color 0B
chcp 65001 >nul
setlocal enabledelayedexpansion

:MAIN_MENU
cls
echo.
echo ========================================================
echo                Git Menu - FIND_DOCUMENTS              
echo ========================================================
echo   Ubicacion: %CD%
echo   Fecha: %date% - Hora: %time%                           
echo   Repo: https://github.com/codedosecodes/generator_MCP    
echo ========================================================
echo.

:: Verificar si estamos en un repositorio Git
if exist ".git" (
    echo [OK] Repositorio Git detectado
    
    :: Mostrar estado rapido
    git status --porcelain > temp_status.txt 2>nul
    set /p QUICK_STATUS=<temp_status.txt
    del temp_status.txt 2>nul
    
    if not "!QUICK_STATUS!"=="" (
        echo [!] Hay cambios locales pendientes
    ) else (
        echo [OK] Repositorio limpio
    )
    
    :: Verificar cambios remotos
    git fetch origin 2>nul
    for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
    for /f %%i in ('git rev-list origin/main..HEAD --count 2^>nul') do set AHEAD=%%i
    
    if "!BEHIND!"=="" set BEHIND=0
    if "!AHEAD!"=="" set AHEAD=0
    
    if !BEHIND! GTR 0 echo [^>] !BEHIND! commits para descargar
    if !AHEAD! GTR 0 echo [^<] !AHEAD! commits para subir
    if !BEHIND! EQU 0 if !AHEAD! EQU 0 echo [OK] Sincronizado con GitHub
) else (
    echo [!] No hay repositorio Git inicializado
)

echo.
echo ========================================================
echo                     MENU PRINCIPAL                   
echo ========================================================
echo.
echo   CONFIGURACION INICIAL:                                 
echo   [1] Configurar Git por primera vez                       
echo   [2] Inicializar repositorio y conectar con GitHub        
echo.                                                           
echo   SUBIR CAMBIOS:                                         
echo   [3] Push automatico (mensaje automatico)                 
echo   [4] Push con mensaje personalizado                       
echo   [5] Commit rapido interactivo                            
echo.                                                            
echo   DESCARGAR CAMBIOS:                                     
echo   [6] Pull automatico (traer cambios del servidor)         
echo.                                                            
echo   SINCRONIZACION:                                        
echo   [7] Sincronizacion completa (Pull + Push)                
echo.                                                            
echo   INFORMACION:                                           
echo   [8] Ver estado detallado del repositorio                 
echo   [9] Ver historial de commits                             
echo   [10] Ver diferencias (cambios sin commitear)             
echo.                                                            
echo   UTILIDADES:                                           
echo   [11] Limpiar archivos temporales                         
echo   [12] Crear/Actualizar .gitignore                         
echo   [13] Configurar credenciales de Git                      
echo.                                                            
echo   ACCIONES RAPIDAS:                                      
echo   [14] Workflow completo (Pull - Trabajo - Push)           
echo   [15] Backup rapido (commit + push de emergencia)         
echo.                                                            
echo   [0] Salir                                              
echo.                                                            
echo ========================================================
echo.

set /p CHOICE="Selecciona una opcion (0-15): "

if "%CHOICE%"=="1" goto CONFIG_GIT
if "%CHOICE%"=="2" goto INIT_REPO
if "%CHOICE%"=="3" goto AUTO_PUSH
if "%CHOICE%"=="4" goto PUSH_CUSTOM
if "%CHOICE%"=="5" goto QUICK_COMMIT
if "%CHOICE%"=="6" goto AUTO_PULL
if "%CHOICE%"=="7" goto FULL_SYNC
if "%CHOICE%"=="8" goto STATUS_DETAIL
if "%CHOICE%"=="9" goto SHOW_LOG
if "%CHOICE%"=="10" goto SHOW_DIFF
if "%CHOICE%"=="11" goto CLEANUP
if "%CHOICE%"=="12" goto CREATE_GITIGNORE
if "%CHOICE%"=="13" goto CONFIG_CREDENTIALS
if "%CHOICE%"=="14" goto WORKFLOW_COMPLETE
if "%CHOICE%"=="15" goto EMERGENCY_BACKUP
if "%CHOICE%"=="0" goto EXIT

echo [X] Opcion invalida. Presiona cualquier tecla para continuar...
pause >nul
goto MAIN_MENU

::===============================================================================
:: FUNCIONES DEL MENU
::===============================================================================

:CONFIG_GIT
cls
echo ===============================================================
echo                    CONFIGURAR GIT
echo ===============================================================
echo.

echo Configuracion actual:
git config user.name 2>nul || echo   Nombre: (no configurado)
git config user.email 2>nul || echo   Email: (no configurado)
echo.

set /p CONFIG_NAME="Ingresa tu nombre completo: "
set /p CONFIG_EMAIL="Ingresa tu email: "

if not "%CONFIG_NAME%"=="" (
    git config --global user.name "%CONFIG_NAME%"
    echo [OK] Nombre configurado: %CONFIG_NAME%
)

if not "%CONFIG_EMAIL%"=="" (
    git config --global user.email "%CONFIG_EMAIL%"
    echo [OK] Email configurado: %CONFIG_EMAIL%
)

echo.
echo [OK] Configuracion de Git completada
goto PAUSE_RETURN

:INIT_REPO
cls
echo ===============================================================
echo              INICIALIZAR REPOSITORIO
echo ===============================================================
echo.

if exist ".git" (
    echo [OK] Ya hay un repositorio Git inicializado
) else (
    echo Inicializando repositorio Git...
    git init
    echo [OK] Repositorio inicializado
)

echo.
echo Configurando repositorio remoto...
set REPO_URL=https://github.com/codedosecodes/generator_MCP.git

git remote get-url origin >nul 2>&1
if errorlevel 1 (
    git remote add origin %REPO_URL%
    echo [OK] Repositorio remoto agregado: %REPO_URL%
) else (
    echo [OK] Repositorio remoto ya configurado
)

echo.
echo Verificando .gitignore...
if not exist ".gitignore" (
    echo Creando .gitignore basico...
    (
        echo # Entorno virtual
        echo venv_find_docs/
        echo env/
        echo ENV/
        echo.
        echo # Archivos sensibles
        echo .env
        echo config/credentials.json
        echo config/token.json
        echo config/config.json
        echo.
        echo # Logs y temporales
        echo logs/*.log
        echo *.log
        echo temp/*
        echo !temp/.gitkeep
        echo __pycache__/
        echo *.pyc
        echo.
        echo # Sistema
        echo .DS_Store
        echo Thumbs.db
        echo desktop.ini
    ) > .gitignore
    echo [OK] .gitignore creado
)

echo.
echo Quieres hacer el primer commit ahora?
set /p FIRST_COMMIT="(y/n): "
if /i "%FIRST_COMMIT%"=="y" (
    git add .
    git commit -m "Initial commit: FIND_DOCUMENTS project setup"
    git push -u origin main
    echo [OK] Primer commit realizado y subido a GitHub
)

goto PAUSE_RETURN

:AUTO_PUSH
cls
echo ===============================================================
echo                 PUSH AUTOMATICO
echo ===============================================================
echo.

echo Archivos modificados:
git status --short

git diff --cached --exit-code >nul 2>&1
if not errorlevel 1 (
    echo Agregando archivos...
    git add .
)

git diff --cached --exit-code >nul 2>&1
if errorlevel 1 (
    set "AUTO_MSG=Auto-update: Files modified - %date% %time%"
    echo Mensaje automatico: !AUTO_MSG!
    git commit -m "!AUTO_MSG!"
    
    echo Subiendo a GitHub...
    git push origin main
    
    if errorlevel 1 (
        echo [X] Error subiendo cambios
    ) else (
        echo [OK] Cambios subidos exitosamente!
    )
) else (
    echo [i] No hay cambios para commitear
)

goto PAUSE_RETURN

:PUSH_CUSTOM
cls
echo ===============================================================
echo              PUSH CON MENSAJE PERSONALIZADO
echo ===============================================================
echo.

echo Archivos modificados:
git status --short
echo.

git diff --cached --exit-code >nul 2>&1
if not errorlevel 1 (
    echo Agregando archivos...
    git add .
)

git diff --cached --exit-code >nul 2>&1
if errorlevel 1 (
    echo Archivos preparados para commit:
    git diff --cached --name-only
    echo.
    
    set /p CUSTOM_MSG="Ingresa tu mensaje de commit: "
    
    if "!CUSTOM_MSG!"=="" (
        echo [X] Mensaje requerido
        goto PAUSE_RETURN
    )
    
    git commit -m "!CUSTOM_MSG!"
    echo Subiendo a GitHub...
    git push origin main
    
    if errorlevel 1 (
        echo [X] Error subiendo cambios
    ) else (
        echo [OK] Cambios subidos exitosamente!
        echo Ver en: https://github.com/codedosecodes/generator_MCP
    )
) else (
    echo [i] No hay cambios para commitear
)

goto PAUSE_RETURN

:QUICK_COMMIT
cls
echo ===============================================================
echo                  COMMIT RAPIDO
echo ===============================================================
echo.

echo Estado actual:
git status --short
echo.

echo Agregando todos los archivos...
git add .

echo Ingresa el tipo de cambio:
echo [1] feat: Nueva funcionalidad
echo [2] fix: Correccion de bug
echo [3] docs: Documentacion
echo [4] style: Formato/estilo
echo [5] refactor: Refactorizacion
echo [6] test: Tests
echo [7] Mensaje personalizado
echo.

set /p COMMIT_TYPE="Selecciona (1-7): "

if "%COMMIT_TYPE%"=="1" set COMMIT_PREFIX=feat: 
if "%COMMIT_TYPE%"=="2" set COMMIT_PREFIX=fix: 
if "%COMMIT_TYPE%"=="3" set COMMIT_PREFIX=docs: 
if "%COMMIT_TYPE%"=="4" set COMMIT_PREFIX=style: 
if "%COMMIT_TYPE%"=="5" set COMMIT_PREFIX=refactor: 
if "%COMMIT_TYPE%"=="6" set COMMIT_PREFIX=test: 
if "%COMMIT_TYPE%"=="7" set COMMIT_PREFIX=

set /p COMMIT_DESC="Describe el cambio: "
set "FULL_MSG=%COMMIT_PREFIX%%COMMIT_DESC%"

git commit -m "%FULL_MSG%"

echo.
set /p DO_PUSH="Hacer push ahora? (y/n): "
if /i "%DO_PUSH%"=="y" (
    git push origin main
    echo [OK] Cambios subidos a GitHub!
)

goto PAUSE_RETURN

:AUTO_PULL
cls
echo ===============================================================
echo                   PULL AUTOMATICO
echo ===============================================================
echo.

echo Verificando cambios remotos...
git fetch origin

for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
if "%BEHIND%"=="" set BEHIND=0

if %BEHIND% GTR 0 (
    echo Hay %BEHIND% commits nuevos para descargar
    echo.
    echo Cambios disponibles:
    git log --oneline HEAD..origin/main
    echo.
    
    git status --porcelain > temp_status.txt
    set /p LOCAL_CHANGES=<temp_status.txt
    del temp_status.txt
    
    if not "%LOCAL_CHANGES%"=="" (
        echo [!] Tienes cambios locales. Se hara stash automaticamente.
        git stash push -m "Auto-stash before pull - %date% %time%"
    )
    
    echo Descargando cambios...
    git pull origin main
    
    if not "%LOCAL_CHANGES%"=="" (
        echo Restaurando cambios locales...
        git stash pop
    )
    
    echo [OK] Actualizacion completada
) else (
    echo [OK] Tu repositorio esta actualizado
)

goto PAUSE_RETURN

:FULL_SYNC
cls
echo ===============================================================
echo               SINCRONIZACION COMPLETA
echo ===============================================================
echo.

echo 1. Descargando cambios del servidor...
echo ----------------------------------------
git fetch origin

for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
if "%BEHIND%"=="" set BEHIND=0

if %BEHIND% GTR 0 (
    echo Descargando %BEHIND% commits...
    git pull origin main
) else (
    echo [OK] Ya esta actualizado
)

echo.
echo 2. Subiendo cambios locales...
echo ------------------------------
git status --porcelain > temp_status.txt
set /p LOCAL_CHANGES=<temp_status.txt
del temp_status.txt

if not "%LOCAL_CHANGES%"=="" (
    git add .
    
    set /p SYNC_MSG="Mensaje para el commit (Enter = automatico): "
    if "!SYNC_MSG!"=="" (
        set "SYNC_MSG=Sync: Changes from %date% %time%"
    )
    
    git commit -m "!SYNC_MSG!"
    git push origin main
    echo [OK] Cambios subidos
) else (
    echo [OK] No hay cambios locales para subir
)

echo.
echo [OK] Sincronizacion completa!
goto PAUSE_RETURN

:STATUS_DETAIL
cls
echo ===============================================================
echo               ESTADO DETALLADO DEL REPOSITORIO
echo ===============================================================
echo.

echo Ubicacion: %CD%
echo Fecha/Hora: %date% %time%
echo.

if not exist ".git" (
    echo [X] No hay repositorio Git inicializado
    goto PAUSE_RETURN
)

echo ESTADO GENERAL:
echo ----------------
git status

echo.
echo ARCHIVOS MODIFICADOS:
echo ---------------------
git status --short

echo.
echo REPOSITORIO REMOTO:
echo -------------------
git remote -v

echo.
echo ULTIMOS 10 COMMITS:
echo -------------------
git log --oneline -10

echo.
echo RAMA ACTUAL:
echo ------------
git branch --show-current

echo.
echo ESTADO DE SINCRONIZACION:
echo -------------------------
git fetch origin 2>nul
for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
for /f %%i in ('git rev-list origin/main..HEAD --count 2^>nul') do set AHEAD=%%i

if "%BEHIND%"=="" set BEHIND=0
if "%AHEAD%"=="" set AHEAD=0

echo Commits para descargar: %BEHIND%
echo Commits para subir: %AHEAD%

goto PAUSE_RETURN

:SHOW_LOG
cls
echo ===============================================================
echo                HISTORIAL DE COMMITS
echo ===============================================================
echo.

echo Selecciona el formato del historial:
echo [1] Simple (una linea por commit)
echo [2] Detallado (con archivos modificados)
echo [3] Grafico (con ramas visuales)
echo [4] Por autor
echo [5] Por fecha (ultimos 30 dias)
echo.

set /p LOG_TYPE="Selecciona (1-5): "

if "%LOG_TYPE%"=="1" (
    echo Historial simple (ultimos 20 commits):
    git log --oneline -20
)
if "%LOG_TYPE%"=="2" (
    echo Historial detallado (ultimos 10 commits):
    git log --stat -10
)
if "%LOG_TYPE%"=="3" (
    echo Historial grafico:
    git log --graph --oneline --all -15
)
if "%LOG_TYPE%"=="4" (
    echo Commits por autor:
    git shortlog -sn --all
)
if "%LOG_TYPE%"=="5" (
    echo Commits de los ultimos 30 dias:
    git log --since="30 days ago" --oneline
)

goto PAUSE_RETURN

:SHOW_DIFF
cls
echo ===============================================================
echo              DIFERENCIAS (CAMBIOS PENDIENTES)
echo ===============================================================
echo.

echo Selecciona que diferencias ver:
echo [1] Cambios sin agregar (working directory)
echo [2] Cambios agregados (staging area)
echo [3] Todos los cambios locales
echo [4] Diferencias con el servidor
echo [5] Solo nombres de archivos modificados
echo.

set /p DIFF_TYPE="Selecciona (1-5): "

if "%DIFF_TYPE%"=="1" (
    echo Cambios sin agregar:
    git diff
)
if "%DIFF_TYPE%"=="2" (
    echo Cambios en staging:
    git diff --cached
)
if "%DIFF_TYPE%"=="3" (
    echo Todos los cambios locales:
    git diff HEAD
)
if "%DIFF_TYPE%"=="4" (
    echo Diferencias con el servidor:
    git fetch origin 2>nul
    git diff origin/main
)
if "%DIFF_TYPE%"=="5" (
    echo Archivos modificados:
    git diff --name-only
    echo.
    echo Archivos en staging:
    git diff --cached --name-only
)

goto PAUSE_RETURN

:CLEANUP
cls
echo ===============================================================
echo                LIMPIAR REPOSITORIO
echo ===============================================================
echo.

echo Archivos que se limpiarian:
git clean -n

echo.
echo [!] Esta accion eliminara archivos no trackeados
set /p CONFIRM_CLEAN="Continuar con la limpieza? (y/n): "

if /i "%CONFIRM_CLEAN%"=="y" (
    echo Limpiando archivos...
    git clean -f
    
    echo Limpiando directorios vacios...
    git clean -fd
    
    echo Optimizando repositorio...
    git gc
    
    echo [OK] Limpieza completada
) else (
    echo [X] Limpieza cancelada
)

goto PAUSE_RETURN

:CREATE_GITIGNORE
cls
echo ===============================================================
echo              CREAR/ACTUALIZAR .GITIGNORE
echo ===============================================================
echo.

if exist ".gitignore" (
    echo [OK] .gitignore existente encontrado
    echo.
    echo Contenido actual:
    type .gitignore
    echo.
    set /p UPDATE_IGNORE="Actualizar .gitignore? (y/n): "
) else (
    echo [!] .gitignore no existe
    set UPDATE_IGNORE=y
)

if /i "%UPDATE_IGNORE%"=="y" (
    echo Creando .gitignore completo...
    (
        echo # === FIND_DOCUMENTS .gitignore ===
        echo.
        echo # Entornos virtuales de Python
        echo venv_find_docs/
        echo env/
        echo ENV/
        echo venv/
        echo .venv/
        echo.
        echo # Archivos de configuracion sensibles
        echo .env
        echo config/credentials.json
        echo config/token.json
        echo config/config.json
        echo *.key
        echo *.pem
        echo.
        echo # Logs
        echo logs/
        echo *.log
        echo npm-debug.log*
        echo.
        echo # Archivos temporales
        echo temp/
        echo tmp/
        echo *.tmp
        echo *.temp
        echo.
        echo # Python
        echo __pycache__/
        echo *.pyc
        echo *.pyo
        echo *.pyd
        echo .Python
        echo build/
        echo develop-eggs/
        echo dist/
        echo downloads/
        echo eggs/
        echo .eggs/
        echo lib/
        echo lib64/
        echo parts/
        echo sdist/
        echo var/
        echo wheels/
        echo *.egg-info/
        echo .installed.cfg
        echo *.egg
        echo.
        echo # Archivos del sistema
        echo .DS_Store
        echo .DS_Store?
        echo ._*
        echo .Spotlight-V100
        echo .Trashes
        echo ehthumbs.db
        echo Thumbs.db
        echo desktop.ini
        echo.
        echo # IDEs y editores
        echo .vscode/
        echo .idea/
        echo *.swp
        echo *.swo
        echo *~
        echo.
        echo # Mantener carpetas vacias importantes
        echo !temp/.gitkeep
        echo !logs/.gitkeep
    ) > .gitignore
    
    echo [OK] .gitignore actualizado exitosamente
) else (
    echo [X] Actualizacion de .gitignore cancelada
)

goto PAUSE_RETURN

:CONFIG_CREDENTIALS
cls
echo ===============================================================
echo             CONFIGURAR CREDENCIALES DE GIT
echo ===============================================================
echo.

echo Configuracion actual:
echo Nombre: 
git config user.name 2>nul || echo   (no configurado)
echo Email:  
git config user.email 2>nul || echo   (no configurado)
echo.

echo Selecciona que configurar:
echo [1] Solo nombre
echo [2] Solo email  
echo [3] Nombre y email
echo [4] Ver configuracion completa
echo.

set /p CRED_OPTION="Selecciona (1-4): "

if "%CRED_OPTION%"=="1" (
    set /p NEW_NAME="Nuevo nombre: "
    if not "!NEW_NAME!"=="" (
        git config --global user.name "!NEW_NAME!"
        echo [OK] Nombre actualizado: !NEW_NAME!
    )
)
if "%CRED_OPTION%"=="2" (
    set /p NEW_EMAIL="Nuevo email: "
    if not "!NEW_EMAIL!"=="" (
        git config --global user.email "!NEW_EMAIL!"
        echo [OK] Email actualizado: !NEW_EMAIL!
    )
)
if "%CRED_OPTION%"=="3" (
    set /p NEW_NAME="Nombre completo: "
    set /p NEW_EMAIL="Email: "
    if not "!NEW_NAME!"=="" (
        git config --global user.name "!NEW_NAME!"
        echo [OK] Nombre configurado: !NEW_NAME!
    )
    if not "!NEW_EMAIL!"=="" (
        git config --global user.email "!NEW_EMAIL!"
        echo [OK] Email configurado: !NEW_EMAIL!
    )
)
if "%CRED_OPTION%"=="4" (
    echo Configuracion completa de Git:
    git config --list
)

goto PAUSE_RETURN

:WORKFLOW_COMPLETE
cls
echo ===============================================================
echo              WORKFLOW COMPLETO DE DESARROLLO
echo ===============================================================
echo.

echo Este workflow simula un dia completo de desarrollo:
echo.
echo 1. Pull (sincronizar con servidor)
echo 2. Mostrar estado actual
echo 3. Simular trabajo (pausa para que hagas cambios)
echo 4. Add + Commit + Push automatico
echo.

set /p START_WORKFLOW="Iniciar workflow completo? (y/n): "
if /i not "%START_WORKFLOW%"=="y" goto MAIN_MENU

echo.
echo PASO 1: Sincronizando con servidor...
echo ======================================
git fetch origin
git pull origin main
echo [OK] Sincronizacion completada

echo.
echo PASO 2: Estado actual del proyecto...
echo =====================================
git status --short

echo.
echo PASO 3: TIEMPO DE DESARROLLO
echo =============================
echo Ahora puedes trabajar en tu codigo...
echo Edita archivos, agrega funcionalidades, etc.
echo.
echo Presiona cualquier tecla cuando termines de trabajar...
pause >nul

echo.
echo PASO 4: Guardando y subiendo cambios...
echo =======================================

git status --porcelain > temp_status.txt
set /p WORK_CHANGES=<temp_status.txt
del temp_status.txt

if not "%WORK_CHANGES%"=="" (
    echo Cambios detectados:
    git status --short
    echo.
    
    set /p WORK_MSG="Describe lo que hiciste: "
    if "!WORK_MSG!"=="" set "WORK_MSG=Development session - %date% %time%"
    
    git add .
    git commit -m "!WORK_MSG!"
    git push origin main
    
    echo.
    echo [OK] Workflow completado exitosamente!
    echo Ver cambios en: https://github.com/codedosecodes/generator_MCP
) else (
    echo [i] No se detectaron cambios en el codigo
    echo El workflow se completo sin modificaciones
)

goto PAUSE_RETURN

:EMERGENCY_BACKUP
cls
echo ===============================================================
echo                BACKUP DE EMERGENCIA
echo ===============================================================
echo.

echo [!] Este es un backup rapido para situaciones de emergencia
echo Guardara TODOS los cambios actuales con timestamp
echo.

echo Estado actual:
git status --short
echo.

set /p EMERGENCY_CONFIRM="Continuar con backup de emergencia? (y/n): "
if /i not "%EMERGENCY_CONFIRM%"=="y" goto MAIN_MENU

echo.
echo Ejecutando backup de emergencia...

:: Crear mensaje con timestamp detallado
for /f "tokens=1-4 delims=/ " %%i in ("%date%") do (
    set DATE_CLEAN=%%k-%%j-%%i
)
for /f "tokens=1-3 delims=:." %%i in ("%time%") do (
    set TIME_CLEAN=%%i-%%j-%%k
)

set "EMERGENCY_MSG=EMERGENCY BACKUP - %DATE_CLEAN% %TIME_CLEAN% - Auto-saved all current work"

:: Backup completo
git add .
git add -A
git commit -m "%EMERGENCY_MSG%"

if errorlevel 1 (
    echo [X] Error en commit de emergencia
    goto PAUSE_RETURN
)

echo Subiendo backup a GitHub...
git push origin main

if errorlevel 1 (
    echo [X] Error subiendo backup
    echo Intentando forzar push...
    git push origin main --force-with-lease
)

echo.
echo [OK] BACKUP DE EMERGENCIA COMPLETADO!
echo Timestamp: %DATE_CLEAN% %TIME_CLEAN%
echo Disponible en: https://github.com/codedosecodes/generator_MCP
echo.
echo Resumen del backup:
git log --oneline -1

goto PAUSE_RETURN

::===============================================================================
:: FUNCIONES AUXILIARES
::===============================================================================

:PAUSE_RETURN
echo.
echo ===============================================================
set /p RETURN_CHOICE="[M]enu principal | [S]alir | [R]epetir accion: "

if /i "%RETURN_CHOICE%"=="M" goto MAIN_MENU
if /i "%RETURN_CHOICE%"=="S" goto EXIT
if /i "%RETURN_CHOICE%"=="R" (
    echo Repitiendo ultima accion...
    timeout /t 2 >nul
    goto %LAST_ACTION%
)
goto MAIN_MENU

:EXIT
cls
echo.
echo ========================================================
echo                     HASTA LUEGO!                      
echo ========================================================
echo                                                            
echo   Gracias por usar Git Menu - FIND_DOCUMENTS            
echo                                                            
echo   Resumen de tu sesion:                                  
echo   Ubicacion: %CD%
echo   Finalizado: %date% %time%                             
echo   Repositorio: https://github.com/codedosecodes/         
echo       generator_MCP.git                                     
echo                                                            
echo   COMANDOS RAPIDOS PARA RECORDAR:                       
echo   - .\git_menu.bat           - Abrir este menu               
echo   - git status               - Ver estado                    
echo   - git add . & git commit -m "msg" & git push origin main
echo                                                            
echo   Feliz desarrollo!                                     
echo                                                            
echo ========================================================
echo.

:: Mostrar estado final si estamos en un repo
if exist ".git" (
    echo Estado final del repositorio:
    git status --short
    
    echo.
    echo Ultimo commit:
    git log --oneline -1
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul
exit /b 0