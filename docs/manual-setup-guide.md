@echo off
:: git_menu.bat - Interactive menu for FIND_DOCUMENTS (ANSI encoding)
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
echo   Location: %CD%
echo   Date: %date% - Time: %time%                           
echo   Repo: https://github.com/codedosecodes/generator_MCP    
echo ========================================================
echo.

:: Check if we are inside a Git repository
if exist ".git" (
    echo [OK] Git repository detected
    
    :: Quick status
    git status --porcelain > temp_status.txt 2>nul
    set /p QUICK_STATUS=<temp_status.txt
    del temp_status.txt 2>nul
    
    if not "!QUICK_STATUS!"=="" (
        echo [!] Local changes pending
    ) else (
        echo [OK] Repository is clean
    )
    
    :: Check remote changes
    git fetch origin 2>nul
    for /f %%i in ('git rev-list HEAD..origin/main --count 2^>nul') do set BEHIND=%%i
    for /f %%i in ('git rev-list origin/main..HEAD --count 2^>nul') do set AHEAD=%%i
    
    if "!BEHIND!"=="" set BEHIND=0
    if "!AHEAD!"=="" set AHEAD=0
    
    if !BEHIND! GTR 0 echo [^>] !BEHIND! commits to pull
    if !AHEAD! GTR 0 echo [^<] !AHEAD! commits to push
    if !BEHIND! EQU 0 if !AHEAD! EQU 0 echo [OK] Synced with GitHub
) else (
    echo [!] No Git repository found
)

echo.
echo ========================================================
echo                   MAIN MENU                    
echo ========================================================
echo.
echo   INITIAL CONFIGURATION:                                 
echo   [1] Configure Git for the first time                       
echo   [2] Initialize repository and connect to GitHub        
echo.                                                           
echo   PUSH CHANGES:                                         
echo   [3] Automatic push (auto message)                  
echo   [4] Push with custom message                       
echo   [5] Quick interactive commit                             
echo.                                                            
echo   PULL CHANGES:                                     
echo   [6] Automatic pull (fetch from server)         
echo.                                                            
echo   SYNCHRONIZATION:                                        
echo   [7] Full sync (Pull + Push)                
echo.                                                            
echo   INFORMATION:                                           
echo   [8] View detailed repository status                  
echo   [9] View commit history                             
echo   [10] View differences (unstaged changes)             
echo.                                                            
echo   UTILITIES:                                           
echo   [11] Clean temporary files                          
echo   [12] Create/Update .gitignore                          
echo   [13] Configure Git credentials                       
echo.                                                            
echo   QUICK ACTIONS:                                       
echo   [14] Full workflow (Pull - Work - Push)           
echo   [15] Emergency backup (commit + push)         
echo.                                                            
echo   [0] Exit                                              
echo.                                                            
echo ========================================================
echo.

set /p CHOICE="Select an option (0-15): "

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

echo [X] Invalid option. Press any key to continue...
pause >nul
goto MAIN_MENU

:: ===============================================================
:: MENU FUNCTIONS
:: ===============================================================

:CONFIG_GIT
cls
echo ===============================================================
echo                    CONFIGURE GIT
echo ===============================================================
echo.

echo Current config:
git config user.name 2>nul || echo   Name: (not set)
git config user.email 2>nul || echo   Email: (not set)
echo.

set /p CONFIG_NAME="Enter your full name: "
set /p CONFIG_EMAIL="Enter your email: "

if not "%CONFIG_NAME%"=="" (
    git config --global user.name "%CONFIG_NAME%"
    echo [OK] Name set: %CONFIG_NAME%
)

if not "%CONFIG_EMAIL%"=="" (
    git config --global user.email "%CONFIG_EMAIL%"
    echo [OK] Email set: %CONFIG_EMAIL%
)

echo.
echo [OK] Git configuration complete
goto PAUSE_RETURN
