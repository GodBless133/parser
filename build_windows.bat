@echo off
REM ============================================================
REM  Telegram Parser & Inviter PRO v5.0 - Build Script
REM  DarkZippa Edition
REM  crafted by zippa
REM ============================================================

title Telegram Parser & Inviter PRO v5.0 - Builder
color 0A

echo.
echo  ============================================================
echo    Telegram Parser and Inviter PRO v5.0
echo    DarkZippa Edition
echo.
echo    crafted by zippa
echo  ============================================================
echo.

REM Check Python
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Install Python 3.9+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo [OK] Python found
python --version
echo.

REM Check dependencies
echo Checking dependencies...
python -c "import telethon, cryptography, socks" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install telethon cryptography pysocks pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies
        echo.
        pause
        exit /b 1
    )
) else (
    echo [OK] All dependencies installed
)
echo.

REM Create folder structure
echo Creating folder structure...
if not exist "logs"      mkdir logs
if not exist "config"    mkdir config
if not exist "sessions"  mkdir sessions
if not exist "backups"   mkdir backups
if not exist "accounts"  mkdir accounts
echo [OK] Folders created
echo.

REM Check required files
echo Checking required files...
set MISSING=0
if not exist "tg_pro_v5.py"              (echo [MISSING] tg_pro_v5.py              & set MISSING=1)
if not exist "ui_framework.py"           (echo [MISSING] ui_framework.py           & set MISSING=1)
if not exist "account_loader.py"         (echo [MISSING] account_loader.py         & set MISSING=1)
if not exist "TelegramInviterPro.spec"   (echo [MISSING] TelegramInviterPro.spec   & set MISSING=1)

if "%MISSING%"=="1" (
    echo.
    echo [ERROR] Some files are missing! Download all files from GitHub:
    echo         https://github.com/GodBless133/parser
    echo.
    pause
    exit /b 1
)
echo [OK] All files present
echo.

REM Build
echo ============================================================
echo  Building EXE via PyInstaller...
echo  Spec file: TelegramInviterPro.spec
echo ============================================================
echo.

pyinstaller TelegramInviterPro.spec --noconfirm --clean

echo.
echo ============================================================

if exist "dist\TelegramInviterPro.exe" (
    echo  [SUCCESS] BUILD COMPLETE!
    echo ============================================================
    echo.
    echo  EXE file: dist\TelegramInviterPro.exe
    echo.
    echo  Features v5.0 DarkZippa:
    echo    - Dark theme DarkZippa with animations
    echo    - Splash screen with "by zippa" signature
    echo    - Animated buttons and progress bars
    echo    - Pulsing status indicators
    echo    - Toast notifications
    echo    - Multi-account: Telethon / Pyrogram / TData
    echo    - Account rotation with per-account stats
    echo    - HTML reports with charts
    echo    - Quick search in table (Ctrl+F)
    echo    - Autosave during parsing
    echo    - Adaptive delays
    echo.
    echo  crafted by zippa
    echo ============================================================
    echo.

    REM Copy EXE to root for convenience
    copy "dist\TelegramInviterPro.exe" "TelegramInviterPro.exe" >nul
    echo [INFO] EXE also copied to: TelegramInviterPro.exe
    echo.

    echo Run: dist\TelegramInviterPro.exe
    echo  Or:  TelegramInviterPro.exe
    echo.

    set /p run_now="Run now? (y/n): "
    if /i "%run_now%"=="y" (
        start "" "dist\TelegramInviterPro.exe"
    )
) else (
    echo  [ERROR] BUILD FAILED
    echo ============================================================
    echo.
    echo Troubleshooting:
    echo    1. Check Python 3.9+: python --version
    echo    2. Upgrade pip: python -m pip install --upgrade pip
    echo    3. Upgrade pyinstaller: pip install --upgrade pyinstaller
    echo    4. Delete build and dist folders and try again
    echo    5. Make sure all .py files are next to .spec file
    echo    6. Read build.log in build/ folder for details
    echo.
)

echo.
pause
