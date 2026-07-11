@echo off
chcp 65001 >nul
title Telegram Parser & Inviter PRO v5.0 — Builder
color 0A

echo.
echo  ╔═══════════════════════════════════════════════════════╗
echo  ║   Telegram Parser ^& Inviter PRO v5.0                  ║
echo  ║   DarkZippa Edition                                   ║
echo  ║                                                       ║
echo  ║   ✦ crafted by zippa ✦                                ║
echo  ╚═══════════════════════════════════════════════════════╝
echo.

REM Проверка Python
where python >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python 3.9+ с https://python.org
    pause
    exit /b 1
)

echo 📦 Проверка зависимостей...
python -c "import telethon, cryptography, socks" 2>nul
if errorlevel 1 (
    echo    Устанавливаю зависимости...
    pip install telethon cryptography pysocks pyinstaller
    if errorlevel 1 (
        echo ❌ Ошибка установки зависимостей
        pause
        exit /b 1
    )
) else (
    echo    ✅ Зависимости установлены
)

echo.
echo 🔧 Создание структуры папок...
if not exist "logs"      mkdir logs
if not exist "config"    mkdir config
if not exist "sessions"  mkdir sessions
if not exist "backups"   mkdir backups
if not exist "accounts"  mkdir accounts

echo.
echo 🏗️  Сборка EXE через PyInstaller...
echo    Используется spec-файл: TelegramInviterPro.spec
echo.

pyinstaller TelegramInviterPro.spec --noconfirm --clean

echo.
if exist "dist\TelegramInviterPro.exe" (
    echo  ╔═══════════════════════════════════════════════════════╗
    echo  ║   ✅ СБОРКА УСПЕШНА!                                  ║
    echo  ╠═══════════════════════════════════════════════════════╣
    echo  ║                                                       ║
    echo  ║   📁 EXE файл: dist\TelegramInviterPro.exe            ║
    echo  ║                                                       ║
    echo  ║   📋 Особенности v5.0 DarkZippa:                      ║
    echo  ║   • 🎨 Тёмная тема DarkZippa с анимациями             ║
    echo  ║   • ✨ Splash screen с подписью by zippa              ║
    echo  ║   • 🌟 Анимированные кнопки и прогресс-бары           ║
    echo  ║   • 💫 Пульсирующие индикаторы статуса                ║
    echo  ║   • 📨 Toast-уведомления                              ║
    echo  ║   • 🎯 Multi-account: Telethon/Pyrogram/TData         ║
    echo  ║   • 🔄 Ротация аккаунтов с пер-аккаунтной статой      ║
    echo  ║   • 📊 HTML-отчёты с графиками                        ║
    echo  ║   • 🔍 Быстрый поиск в таблице                        ║
    echo  ║   • 💾 Автосохранение при парсинге                    ║
    echo  ║   • 🧠 Адаптивные задержки                            ║
    echo  ║                                                       ║
    echo  ║   ✦ crafted by zippa ✦                                ║
    echo  ╚═══════════════════════════════════════════════════════╝
    echo.

    REM Копируем EXE в корень для удобства
    copy "dist\TelegramInviterPro.exe" "TelegramInviterPro.exe" >nul
    echo 📋 EXE также скопирован в: TelegramInviterPro.exe
    echo.

    echo 🚀 Запуск: dist\TelegramInviterPro.exe
    echo    Или: TelegramInviterPro.exe
    echo.

    set /p run_now="Запустить сейчас? (y/n): "
    if /i "%run_now%"=="y" (
        start "" "dist\TelegramInviterPro.exe"
    )
) else (
    echo ❌ Ошибка сборки
    echo.
    echo 🔧 Устранение неполадок:
    echo    1. Проверьте Python 3.9+: python --version
    echo    2. Обновите pip: python -m pip install --upgrade pip
    echo    3. Обновите pyinstaller: pip install --upgrade pyinstaller
    echo    4. Удалите папку build и dist и попробуйте снова
    echo    5. Убедитесь, что все .py файлы рядом со spec-файлом
)

echo.
pause
