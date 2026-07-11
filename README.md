# ⚡ Telegram Parser & Inviter PRO v5.0

**DarkZippa Edition** — многофункциональный парсер и инвайтер для Telegram с поддержкой нескольких аккаунтов.

> ✦ **crafted by zippa** ✦

![Version](https://img.shields.io/badge/version-5.0-purple)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)

---

## ✨ Особенности

### 🎨 Дизайн (DarkZippa Edition)
- **Тёмная тема** с фиолетово-циановыми акцентами
- **Splash screen** при запуске с анимированным логотипом и подписью "by zippa"
- **Анимированные кнопки** — плавный цветопереход при hover, лёгкое нажатие при press
- **Анимированные progress bars** с плавным заполнением и бликом
- **Пульсирующие индикаторы** статуса аккаунтов (🟢🟡🔴⚫)
- **Toast-уведомления** — slide-in справа с автозакрытием
- **Анимированные счётчики** статистики (tween-анимация)
- **Красивый About dialog** с авторской подписью

### 🎯 Multi-Account
- **Загрузка готовых сессий** трёх форматов:
  - 📦 **Telethon** — `.session` файлы (SQLite)
  - 📦 **Pyrogram** — `.session` файлы (SQLite)
  - 📦 **TData** — папка `tdata/` из Telegram Desktop
- **Ротация аккаунтов** при инвайте — распределяет нагрузку, снижает риск бана
- **Пер-аккаунтная статистика** — успешные/ошибки/FloodWait для каждого аккаунта
- **Авто-пропуск аккаунтов** в FloodWait
- **Один api_id/api_hash** на все аккаунты

### 🚀 Парсинг и инвайт
- 3 метода парсинга: участники / сообщения / быстрый
- Фильтры: боты, удалённые, без username, по last_seen
- **Адаптивные задержки** — увеличиваются при росте ошибок
- **Сухой прогон** (dry-run) — тест без реальных инвайтов
- **Пропуск дублей** — предзагрузка участников целевой группы
- **Автоостановка** при 5 ошибках подряд

### 📊 Отчётность
- **HTML-отчёт** с графиками и разбивкой по аккаунтам
- **Экспорт CSV / JSON** + импорт CSV
- **Автосохранение** во время парсинга (каждые 30 сек)
- **Resume** прерванного инвайта
- **Быстрый поиск** в таблице (Ctrl+F)

---

## 📦 Установка

### Требования
- Python 3.9+
- tkinter (входит в стандартную поставку Python)
- На некоторых Linux: `sudo apt install python3-tk`

### Установка зависимостей

\`\`\`bash
pip install -r requirements.txt
\`\`\`

Зависимости:
- \`telethon\` — работа с Telegram API
- \`cryptography\` — шифрование (Fernet для config, AES-IGE для TData)
- \`pysocks\` — прокси (опционально)

### Запуск

\`\`\`bash
python tg_pro_v5.py
\`\`\`

---

## 🏗️ Сборка в EXE

### Windows
\`\`\`bat
build_windows.bat
\`\`\`
Готовый EXE будет в \`dist\\TelegramInviterPro.exe\`

### Linux / macOS
\`\`\`bash
chmod +x build_linux.sh
./build_linux.sh
\`\`\`
Готовый бинарь будет в \`dist/TelegramInviterPro\`

### Вручную через PyInstaller
\`\`\`bash
pyinstaller TelegramInviterPro.spec --noconfirm --clean
\`\`\`

---

## 🚀 Использование

### Шаг 1: Подготовка сессий

Создайте папку (например, \`accounts\`) и положите туда сессии:

\`\`\`
accounts/
├── account1.session          ← Telethon
├── account2.session          ← Pyrogram
├── tdata_account1/
│   └── tdata/                ← Telegram Desktop
│       └── D877F783D5D3EF8C/
│           └── key_datas
└── tdata_account2/
    └── tdata/
\`\`\`

### Шаг 2: Получение API данных

1. Перейдите на https://my.telegram.org
2. Войдите под своим номером телефона
3. В разделе "API Development Tools" создайте приложение
4. Скопируйте \`api_id\` и \`api_hash\`

### Шаг 3: Запуск

1. Запустите программу: \`python tg_pro_v5.py\`
2. Во вкладке **"⚙️ API"** введите \`api_id\` и \`api_hash\`
3. Во вкладке **"👥 Аккаунты"** нажмите **"📁 Выбрать папку с сессиями"**
4. Выберите папку с сессиями → программа найдёт все аккаунты
5. Нажмите **"🔌 Подключить все"**
6. Парсите и приглашайте — аккаунты будут ротироваться автоматически

---

## ⌨️ Горячие клавиши

| Клавиша | Действие |
|---------|----------|
| \`F1\` | Справка |
| \`Ctrl + F\` | Поиск в таблице |
| \`Ctrl + S\` | Экспорт CSV |
| \`Ctrl + H\` | HTML-отчёт |
| \`Ctrl + L\` | Очистить лог |
| \`Ctrl + Q\` | Выход |
| \`F5\` | Обновить таблицу аккаунтов |

---

## 📁 Структура проекта

\`\`\`
parser/
├── tg_pro_v5.py                  # Основной файл (GUI + логика)
├── ui_framework.py               # UI-фреймворк (тема, анимации, splash, toasts)
├── account_loader.py             # Загрузка сессий (Telethon/Pyrogram/TData)
├── TelegramInviterPro.spec       # PyInstaller spec-файл
├── build_windows.bat             # Сборка для Windows
├── build_linux.sh                # Сборка для Linux/macOS
├── requirements.txt              # Зависимости
└── README.md
\`\`\`

---

## 🔧 Технические детали

### Загрузка сессий

Все три формата сессий (Telethon, Pyrogram, TData) приводятся к единой модели \`LoadedAccount\` с \`auth_key\` + \`dc_id\`. Из них строится \`StringSession\` для Telethon.

### AES-IGE для TData

TData (Telegram Desktop) шифруется AES-256-IGE — редкий режим. Реализован на чистой \`cryptography\` через AES-ECB + ручная IGE-надстройка. Прошёл round-trip тесты для всех длин (16-4096 байт).

---

## ⚠️ Важные замечания

1. **Используйте только свои сессии**
2. **Соблюдайте правила Telegram** — начинайте с малых объёмов (10-20 в день)
3. **Не передавайте \`config/.key\`** третьим лицам
4. **Отозванные сессии** покажут статус "⚠️ Не авторизован"

---

## 👤 Автор

**✦ crafted by zippa ✦**

- Telegram: @zippa
- GitHub: [GodBless133](https://github.com/GodBless133)
- 2024-2025

---

## 📄 Лицензия

MIT License — используйте свободно, но на свой страх и риск.

Автор не несёт ответственности за блокировку аккаунтов Telegram при нарушении правил сервиса.
