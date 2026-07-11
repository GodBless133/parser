#!/usr/bin/env bash
# Build script for Linux/macOS
# Telegram Parser & Inviter PRO v5.0 — DarkZippa Edition
# ✦ crafted by zippa ✦

set -e

echo ""
echo "  ╔═══════════════════════════════════════════════════════╗"
echo "  ║   Telegram Parser & Inviter PRO v5.0                  ║"
echo "  ║   DarkZippa Edition                                   ║"
echo "  ║                                                       ║"
echo "  ║   ✦ crafted by zippa ✦                                ║"
echo "  ╚═══════════════════════════════════════════════════════╝"
echo ""

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден! Установите Python 3.9+"
    exit 1
fi

PYTHON=python3
echo "📦 Python: $($PYTHON --version)"

# Проверка зависимостей
echo "📦 Проверка зависимостей..."
if ! $PYTHON -c "import telethon, cryptography" 2>/dev/null; then
    echo "   Устанавливаю зависимости..."
    $PYTHON -m pip install telethon cryptography pysocks pyinstaller
else
    echo "   ✅ Зависимости установлены"
fi

# Проверка Tkinter (часто отдельный пакет в Linux)
if ! $PYTHON -c "import tkinter" 2>/dev/null; then
    echo "⚠️  Tkinter не найден!"
    echo "   Установите пакет tcl/tk для вашей системы:"
    echo "   Ubuntu/Debian: sudo apt install python3-tk"
    echo "   Fedora:        sudo dnf install python3-tkinter"
    echo "   Arch:          sudo pacman -S tk"
    exit 1
fi

# Создание структуры папок
echo ""
echo "🔧 Создание структуры папок..."
mkdir -p logs config sessions backups accounts

# Сборка
echo ""
echo "🏗️  Сборка через PyInstaller..."
echo "   Используется spec-файл: TelegramInviterPro.spec"
echo ""

$PYTHON -m PyInstaller TelegramInviterPro.spec --noconfirm --clean

# Результат
echo ""
if [ -f "dist/TelegramInviterPro" ]; then
    echo "  ╔═══════════════════════════════════════════════════════╗"
    echo "  ║   ✅ СБОРКА УСПЕШНА!                                  ║"
    echo "  ╠═══════════════════════════════════════════════════════╣"
    echo "  ║                                                       ║"
    echo "  ║   📁 Бинарь: dist/TelegramInviterPro                  ║"
    echo "  ║                                                       ║"
    echo "  ║   📋 Особенности v5.0 DarkZippa:                      ║"
    echo "  ║   • 🎨 Тёмная тема DarkZippa с анимациями             ║"
    echo "  ║   • ✨ Splash screen с подписью by zippa              ║"
    echo "  ║   • 🌟 Анимированные кнопки и прогресс-бары           ║"
    echo "  ║   • 💫 Пульсирующие индикаторы статуса                ║"
    echo "  ║   • 📨 Toast-уведомления                              ║"
    echo "  ║   • 🎯 Multi-account: Telethon/Pyrogram/TData         ║"
    echo "  ║   • 🔄 Ротация аккаунтов с пер-аккаунтной статой      ║"
    echo "  ║   • 📊 HTML-отчёты с графиками                        ║"
    echo "  ║   • 🔍 Быстрый поиск в таблице                        ║"
    echo "  ║   • 💾 Автосохранение при парсинге                    ║"
    echo "  ║   • 🧠 Адаптивные задержки                            ║"
    echo "  ║                                                       ║"
    echo "  ║   ✦ crafted by zippa ✦                                ║"
    echo "  ╚═══════════════════════════════════════════════════════╝"
    echo ""
    echo "🚀 Запуск: ./dist/TelegramInviterPro"
    echo ""

    # Делаем исполняемым
    chmod +x dist/TelegramInviterPro

    read -p "Запустить сейчас? (y/n): " run_now
    if [ "$run_now" = "y" ] || [ "$run_now" = "Y" ]; then
        ./dist/TelegramInviterPro &
    fi
else
    echo "❌ Ошибка сборки"
    echo ""
    echo "🔧 Устранение неполадок:"
    echo "   1. Проверьте Python 3.9+: python3 --version"
    echo "   2. Обновите pip: python3 -m pip install --upgrade pip"
    echo "   3. Обновите pyinstaller: pip install --upgrade pyinstaller"
    echo "   4. Удалите build/ и dist/ и попробуйте снова"
    echo "   5. Убедитесь, что tkinter установлен"
fi

echo ""
