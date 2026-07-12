"""
Telegram Parser & Inviter PRO v5.0  (DarkZippa Edition)
═════════════════════════════════════════════════════════
                    ✦ crafted by zippa ✦
═════════════════════════════════════════════════════════

НОВОЕ в v5.0 (DarkZippa Edition):
  🎨 Тёмная тема "DarkZippa" с фиолетово-циановыми акцентами
  ✨ Splash screen при запуске с анимированным логотипом и подписью "by zippa"
  🌟 Анимированные кнопки (hover/press с цветопереходом)
  📊 Анимированные progress bars с плавным заполнением
  💫 Пульсирующие индикаторы статуса аккаунтов
  📨 Toast-уведомления (slide-in из угла)
  🔢 Анимированные счётчики статистики (tween)
  ℹ️  Красивый About dialog с авторской подписью
  ⌨️  Горячие клавиши: F1 — help, Ctrl+F — поиск, Ctrl+S — CSV

УЛУЧШЕНИЯ (на своё усмотрение):
  📄 HTML-отчёт об инвайте с графиками
  💾 Автосохранение во время парсинга (каждые 30 сек)
  🔍 Быстрый поиск в таблице пользователей (Ctrl+F)
  ⏯️  Resume прерванного инвайта (сохранение состояния)
  🧠 Адаптивные задержки (увеличиваются при росте ошибок)
  📊 Расширенная статистика по аккаунтам в реальном времени
  🎯 Карточки аккаунтов с прогрессом
  🌡️  Индикатор "температуры" аккаунта (зелёный/жёлтый/красный)

Все исправления и возможности v4.0 сохранены:
  • Multi-account: Telethon / Pyrogram / TData
  • Ротация аккаунтов
  • Пер-аккаунтная статистика
  • Прокси SOCKS5/HTTP
  • Сухой прогон
  • Фильтр по last_seen
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import asyncio
import threading
import csv
import os
import sys
import random
import time
import json
import html
import hashlib
import base64
import atexit
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any, Set

from telethon import TelegramClient, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.channels import InviteToChannelRequest
from telethon.tl.types import Channel, Chat, User
from telethon.errors import (
    FloodWaitError, UserPrivacyRestrictedError, ChannelPrivateError,
    UserNotParticipantError, UserAlreadyParticipantError,
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError,
    ApiIdInvalidError, AuthKeyDuplicatedError, AuthKeyUnregisteredError,
    UserBotError, PeerFloodError,
)

# Опциональные импорты ошибок — некоторые существуют только в новых версиях Telethon.
# Используем try/except, чтобы не ломать совместимость со старыми версиями.
ChatWriteForbiddenError = type("ChatWriteForbiddenError", (Exception,), {})
ChatAdminInviteRequiredError = type("ChatAdminInviteRequiredError", (Exception,), {})
BroadcastForbiddenError = type("BroadcastForbiddenError", (Exception,), {})
InviteForbiddenWithJoinasError = type("InviteForbiddenWithJoinasError", (Exception,), {})
UserAlreadyInvitedError = type("UserAlreadyInvitedError", (Exception,), {})
UserPrivacyInvalidError = type("UserPrivacyInvalidError", (Exception,), {})
InputUserDeactivatedError = type("InputUserDeactivatedError", (Exception,), {})

try:
    from telethon.errors import ChatWriteForbiddenError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import ChatAdminInviteRequiredError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import BroadcastForbiddenError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import InviteForbiddenWithJoinasError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import UserAlreadyInvitedError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import UserPrivacyInvalidError  # noqa: F811
except ImportError:
    pass
try:
    from telethon.errors import InputUserDeactivatedError  # noqa: F811
except ImportError:
    pass
import logging
from logging.handlers import RotatingFileHandler

try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False

try:
    from account_loader import AccountLoader, LoadedAccount, make_string_session
    _HAS_ACCOUNT_LOADER = True
except ImportError:
    _HAS_ACCOUNT_LOADER = False

# Наш UI-фреймворк
from ui_framework import (
    Theme, AnimatedButton, AnimatedProgress, PulseIndicator,
    Toast, AnimatedCounter, SplashScreen, show_about_dialog,
    apply_dark_theme, styled_scrolledtext,
)


# =====================================================================
# ЛОГИРОВАНИЕ
# =====================================================================
def setup_logging() -> logging.Logger:
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=[
            RotatingFileHandler(
                log_dir / "telegram_invite.log",
                maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8",
            ),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger("tg_parser")


logger = setup_logging()


# =====================================================================
# DATACLASSES
# =====================================================================
@dataclass
class UserData:
    id: int
    username: str = ""
    first_name: str = ""
    last_name: str = ""
    phone: str = ""
    status: str = "Готов"
    last_seen: Optional[str] = None
    is_bot: bool = False
    access_hash: Optional[int] = None  # [NEW] критично для инвайта по user_id

    def to_csv_row(self) -> Dict[str, Any]:
        return {
            "id": self.id, "username": self.username or "",
            "first_name": self.first_name or "", "last_name": self.last_name or "",
            "phone": self.phone or "", "status": self.status,
            "last_seen": self.last_seen or "",
            "access_hash": self.access_hash or "",
        }


@dataclass
class InviteStats:
    total_invited: int = 0
    successful: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: Optional[datetime] = None
    errors: Dict[str, int] = field(default_factory=dict)


@dataclass
class AccountRuntimeInfo:
    account: LoadedAccount
    client: Optional[TelegramClient] = None
    is_connected: bool = False
    is_authorized: bool = False
    me_name: str = ""
    me_phone: str = ""
    invited_count: int = 0
    failed_count: int = 0
    flood_until: Optional[datetime] = None
    is_disabled: bool = False
    last_error: str = ""

    @property
    def temperature(self) -> str:
        """Температура аккаунта: green/yellow/red/grey."""
        if not self.is_connected or not self.is_authorized:
            return "grey"
        if self.is_disabled:
            return "grey"
        if self.flood_until and datetime.now() < self.flood_until:
            return "red"
        if self.failed_count > 3:
            return "yellow"
        return "green"


# =====================================================================
# SecureConfig (без изменений из v4)
# =====================================================================
class SecureConfig:
    def __init__(self) -> None:
        self.config_dir = Path("config")
        self.config_dir.mkdir(exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self.key_file = self.config_dir / ".key"
        self.state_file = self.config_dir / "state.json"
        self._load_or_generate_key()

    def _load_or_generate_key(self) -> None:
        if self.key_file.exists():
            with open(self.key_file, "rb") as f:
                self.key = f.read().strip()
            if _HAS_CRYPTO:
                try:
                    Fernet(self.key)
                except Exception:
                    self.key = Fernet.generate_key()
                    self._write_key()
        else:
            self.key = Fernet.generate_key() if _HAS_CRYPTO else b""
            self._write_key()

    def _write_key(self) -> None:
        with open(self.key_file, "wb") as f:
            f.write(self.key)
        try:
            os.chmod(self.key_file, 0o600)
        except Exception:
            pass

    def encrypt(self, data: str) -> str:
        if not _HAS_CRYPTO or not self.key:
            return data
        return Fernet(self.key).encrypt(data.encode("utf-8")).decode("utf-8")

    def decrypt(self, encrypted_data: str) -> str:
        if not _HAS_CRYPTO or not self.key:
            return encrypted_data
        try:
            return Fernet(self.key).decrypt(encrypted_data.encode("utf-8")).decode("utf-8")
        except Exception:
            return ""

    def save_config(self, api_id: str, api_hash: str, phone: str = "") -> None:
        config = {
            "api_id": self.encrypt(api_id),
            "api_hash": self.encrypt(api_hash),
            "phone": self.encrypt(phone) if phone else "",
        }
        tmp = self.config_file.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        tmp.replace(self.config_file)

    def load_config(self) -> Optional[Dict[str, str]]:
        if not self.config_file.exists():
            return None
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            return {
                "api_id": self.decrypt(config.get("api_id", "")),
                "api_hash": self.decrypt(config.get("api_hash", "")),
                "phone": self.decrypt(config["phone"]) if config.get("phone") else "",
            }
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
            return None

    def save_state(self, state: Dict[str, Any]) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {}
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}


# =====================================================================
# SessionManager
# =====================================================================
class SessionManager:
    def __init__(self, session_dir: str = "sessions") -> None:
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)

    def get_session_path(self, phone: str) -> str:
        session_hash = hashlib.md5(phone.encode("utf-8")).hexdigest()
        return str(self.session_dir / f"session_{session_hash}")

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for file in self.session_dir.glob("session_*.session"):
            stat = file.stat()
            sessions.append({
                "id": file.stem.replace("session_", ""),
                "file": file.name, "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
        sessions.sort(key=lambda s: s["modified"], reverse=True)
        return sessions

    def clear_all(self) -> int:
        count = 0
        for file in self.session_dir.glob("session_*.session"):
            try:
                file.unlink()
                count += 1
            except Exception:
                pass
        return count


# =====================================================================
# Rate limiter с адаптивными задержками  [NEW]
# =====================================================================
class RateLimiter:
    """Rate limiter с адаптивными задержками.

    Если за последние N инвайтов ошибок много — увеличиваем задержку.
    """

    def __init__(self) -> None:
        self.delay_min: int = 30
        self.delay_max: int = 60
        self.pause_after: int = 5
        self.pause_time: int = 60
        self.daily_limit: int = 100
        self.per_account_limit: int = 20
        self._recent_results: List[bool] = []  # True=success, False=error
        self._window = 10

    def record(self, success: bool) -> None:
        self._recent_results.append(success)
        if len(self._recent_results) > self._window:
            self._recent_results.pop(0)

    def adaptive_delay(self) -> int:
        """Адаптивная задержка: выше при росте ошибок."""
        base = random.randint(self.delay_min, self.delay_max)
        if not self._recent_results:
            return base
        error_rate = sum(1 for r in self._recent_results if not r) / len(self._recent_results)
        # Если ошибок >30% — удваиваем задержку
        if error_rate > 0.5:
            return int(base * 2.5)
        elif error_rate > 0.3:
            return int(base * 1.8)
        elif error_rate > 0.15:
            return int(base * 1.3)
        return base

    def should_pause(self, count: int) -> bool:
        return count > 0 and count % self.pause_after == 0


# =====================================================================
# HTML-отчёт  [NEW]
# =====================================================================
def generate_html_report(stats: InviteStats, accounts: List[AccountRuntimeInfo],
                          target_group: str, duration_str: str) -> str:
    """Сгенерировать красивый HTML-отчёт об инвайте."""
    attempts = stats.successful + stats.failed
    conversion = (stats.successful / attempts * 100) if attempts > 0 else 0

    # Карточки аккаунтов
    acc_rows = ""
    for info in accounts:
        if info.invited_count == 0 and info.failed_count == 0:
            continue
        label = info.me_name or info.account.display_name
        temp_color = {"green": "#3fb950", "yellow": "#e3b341",
                      "red": "#f85149", "grey": "#6e7681"}.get(info.temperature, "#6e7681")
        acc_rows += f"""
        <tr>
            <td><span class="dot" style="background:{temp_color}"></span>{info.account.source_format}</td>
            <td>{html.escape(label)}</td>
            <td class="num">{info.invited_count}</td>
            <td class="num">{info.failed_count}</td>
            <td class="num">{info.invited_count + info.failed_count}</td>
        </tr>"""

    # Топ ошибок
    error_rows = ""
    if stats.errors:
        for err, cnt in sorted(stats.errors.items(), key=lambda x: -x[1])[:10]:
            error_rows += f"<tr><td>{html.escape(err)}</td><td class='num'>{cnt}</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<title>Отчёт об инвайте — {datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    background: #0d1117;
    color: #e6edf3;
    font-family: 'Segoe UI', -apple-system, sans-serif;
    padding: 32px;
    min-height: 100vh;
}}
.container {{ max-width: 900px; margin: 0 auto; }}
h1 {{
    font-size: 28px;
    background: linear-gradient(135deg, #a371f7, #39d0d8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
}}
.subtitle {{ color: #8b949e; margin-bottom: 32px; font-size: 14px; }}
.brand {{
    text-align: right; color: #a371f7; font-style: italic;
    margin-bottom: 24px; font-size: 13px;
}}
.cards {{
    display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 16px; margin-bottom: 32px;
}}
.card {{
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 20px;
}}
.card .label {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
.card .value {{ font-size: 32px; font-weight: 700; margin-top: 8px; }}
.card.success .value {{ color: #3fb950; }}
.card.error .value {{ color: #f85149; }}
.card.skip .value {{ color: #e3b341; }}
.card.conv .value {{ color: #a371f7; }}
section {{
    background: #161b22; border: 1px solid #30363d;
    border-radius: 12px; padding: 20px; margin-bottom: 24px;
}}
h2 {{ font-size: 18px; margin-bottom: 16px; color: #39d0d8; }}
table {{ width: 100%; border-collapse: collapse; }}
th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #30363d; }}
th {{ color: #8b949e; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }}
.dot {{
    display: inline-block; width: 10px; height: 10px;
    border-radius: 50%; margin-right: 8px; vertical-align: middle;
}}
.footer {{ text-align: center; color: #6e7681; font-size: 12px; margin-top: 32px; }}
.footer a {{ color: #a371f7; text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
    <div class="brand">✦ crafted by zippa ✦</div>
    <h1>📊 Отчёт об инвайте</h1>
    <div class="subtitle">
        Целевая группа: <strong>{html.escape(target_group)}</strong> •
        Время выполнения: <strong>{duration_str}</strong> •
        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    </div>

    <div class="cards">
        <div class="card success">
            <div class="label">Успешно</div>
            <div class="value">{stats.successful}</div>
        </div>
        <div class="card error">
            <div class="label">Ошибок</div>
            <div class="value">{stats.failed}</div>
        </div>
        <div class="card skip">
            <div class="label">Пропущено</div>
            <div class="value">{stats.skipped}</div>
        </div>
        <div class="card conv">
            <div class="label">Конверсия</div>
            <div class="value">{conversion:.1f}%</div>
        </div>
    </div>

    <section>
        <h2>👥 Статистика по аккаунтам</h2>
        <table>
            <thead><tr>
                <th>Формат</th><th>Аккаунт</th>
                <th style="text-align:right">Успешно</th>
                <th style="text-align:right">Ошибок</th>
                <th style="text-align:right">Всего</th>
            </tr></thead>
            <tbody>{acc_rows or '<tr><td colspan="5" style="text-align:center;color:#6e7681">Нет данных</td></tr>'}</tbody>
        </table>
    </section>

    {f'''<section>
        <h2>⚠️ Топ ошибок</h2>
        <table>
            <thead><tr><th>Ошибка</th><th style="text-align:right">Количество</th></tr></thead>
            <tbody>{error_rows}</tbody>
        </table>
    </section>''' if error_rows else ''}

    <div class="footer">
        Telegram Parser &amp; Inviter PRO v5.0 (DarkZippa Edition)<br>
        ✦ crafted by <a href="#">zippa</a> ✦
    </div>
</div>
</body>
</html>"""


# =====================================================================
# MAIN APP
# =====================================================================
class TelegramWorkingInvite:
    VERSION = Theme.VERSION

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(f"{Theme.APP_NAME} v{Theme.VERSION}")

        # Тёмная тема
        self.root.configure(bg=Theme.BG_DEEP)
        self.style = ttk.Style()
        apply_dark_theme(self.style)

        # Менеджеры
        self.config_manager = SecureConfig()
        self.session_manager = SessionManager()
        self.rate_limiter = RateLimiter()
        self.account_loader = AccountLoader() if _HAS_ACCOUNT_LOADER else None

        self.config = self.config_manager.load_config() or {}
        self.api_id: str = self.config.get("api_id", "")
        self.api_hash: str = self.config.get("api_hash", "")

        # Состояние
        self.client: Optional[TelegramClient] = None
        self.is_authenticated: bool = False
        self.parsed_users: List[UserData] = []
        self.inviting_active: bool = False
        self.invite_paused: threading.Event = threading.Event()
        self.invite_paused.set()
        self.invite_stop: threading.Event = threading.Event()
        # [NEW] Целевая группа инвайта — тип и Input-объект
        self._invite_target_type: Optional[str] = None  # 'channel' | 'chat' | None
        self._invite_input_channel = None    # InputChannel для супергруппы
        self._invite_chat_id: Optional[int] = None  # chat_id для обычного чата
        self.auth_phone: str = ""
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.loop_thread: Optional[threading.Thread] = None
        self.loop_running: bool = False
        self.dry_run: bool = False
        self.proxy: Optional[str] = None

        # [NEW] Resume state
        self.last_invite_state: Dict[str, Any] = {}

        self.loaded_accounts: List[AccountRuntimeInfo] = []
        self.account_rotation_enabled = tk.BooleanVar(value=True)

        self.stats = InviteStats()
        self.blacklist: Set[str] = set()
        self.load_blacklist()
        self.target_members: Set[int] = set()
        self.recent_groups: List[str] = self.config_manager.load_state().get("recent_groups", [])
        self.session_phone_map: Dict[str, str] = (
            self.config_manager.load_state().get("session_map", {})
        )

        # [NEW] Animated counters
        self._counters: Dict[str, AnimatedCounter] = {}

        # [NEW] Autosave timer
        self._autosave_job = None

        # [NEW] Search
        self._search_window = None

        self.setup_ui()
        self._start_loop()

        # Splash screen
        self._splash = SplashScreen(root, duration_ms=3000)

        self.log_message(f"🚀 {Theme.APP_NAME} v{Theme.VERSION} запущен!", "success")
        self.log_message("✦ crafted by zippa ✦", "info")
        if not _HAS_ACCOUNT_LOADER:
            self.log_message("⚠️ account_loader.py не найден", "warning")
        if self.api_id and self.api_hash:
            self.log_message("✅ API данные загружены из конфигурации")
        else:
            self.log_message("⚠️ Введите API ID и Hash во вкладке 'API Настройки'")

        # Восстановление геометрии
        state = self.config_manager.load_state()
        geom = state.get("geometry")
        if geom:
            try:
                self.root.geometry(geom)
            except Exception:
                pass

        # [NEW] Автозагрузка последнего invite-состояния
        self._load_invite_state()

        atexit.register(self.close)

    # =====================================================================
    # EVENT LOOP
    # =====================================================================
    def _start_loop(self) -> None:
        if self.loop_running:
            return

        def run_loop() -> None:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop_running = True

            def handle_exception(loop, context):
                msg = context.get("exception", context.get("message", "Unknown"))
                logger.error(f"Ошибка в event loop: {msg}")

            self.loop.set_exception_handler(handle_exception)
            self.loop.run_forever()

        self.loop_thread = threading.Thread(target=run_loop, daemon=True)
        self.loop_thread.start()

        for _ in range(50):
            if self.loop_running and self.loop is not None:
                break
            time.sleep(0.05)

    def _run_coroutine(self, coro, timeout: int = 600):
        if not self.loop or not self.loop_running:
            self._safe_log("❌ Event loop не запущен", "error")
            return None
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        try:
            return future.result(timeout=timeout)
        except asyncio.TimeoutError:
            self._safe_log("⏱️  Превышено время ожидания", "warning")
            future.cancel()
            return None
        except Exception as e:
            self._safe_log(f"❌ Ошибка: {str(e)[:120]}", "error")
            logger.exception("Ошибка в корутине")
            return None

    def _safe_log(self, message: str, level: str = "info") -> None:
        try:
            self.root.after(0, lambda: self.log_message(message, level))
        except RuntimeError:
            logger.info(message)

    # =====================================================================
    # UI
    # =====================================================================
    def setup_ui(self) -> None:
        self.root.geometry("1320x880")
        self.root.minsize(1080, 740)

        # Верхняя панель с градиентом (через canvas)
        self._build_top_bar()

        # Notebook (вкладки)
        notebook_frame = tk.Frame(self.root, bg=Theme.BG_DEEP)
        notebook_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill="both", expand=True)

        self.setup_accounts_tab(self.notebook)
        self.setup_chats_tab(self.notebook)  # [NEW] Зайти в чат
        self.setup_auth_tab(self.notebook)
        self.setup_api_tab(self.notebook)
        self.setup_parser_tab(self.notebook)
        self.setup_inviter_tab(self.notebook)
        self.setup_management_tab(self.notebook)

        # Progress
        progress_frame = tk.Frame(self.root, bg=Theme.BG_DEEP)
        progress_frame.pack(fill="x", padx=10, pady=(0, 4))

        self.progress_var = tk.DoubleVar(value=0)
        self.progress = AnimatedProgress(progress_frame, width=900, height=10)
        self.progress.pack(side="left", fill="x", expand=True)

        self.progress_label = tk.Label(progress_frame, text="", font=Theme.FONT_TINY,
                                       bg=Theme.BG_DEEP, fg=Theme.TEXT_SECONDARY)
        self.progress_label.pack(side="left", padx=10)

        # Лог
        log_frame = tk.LabelFrame(self.root, text="  📋 Лог действий  ",
                                  font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                  fg=Theme.ACCENT_SECONDARY, bd=1,
                                  relief="solid", highlightthickness=0,
                                  borderwidth=1)
        log_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        log_inner = tk.Frame(log_frame, bg=Theme.BG_BASE)
        log_inner.pack(fill="both", expand=True, padx=4, pady=4)

        self.log_text, log_sb = styled_scrolledtext(log_inner, height=10)
        self.log_text.pack(side="left", fill="both", expand=True)
        log_sb.pack(side="right", fill="y")

        # Тэги цветов
        for level, color in {
            "info": Theme.TEXT_PRIMARY, "success": Theme.ACCENT_GREEN,
            "warning": Theme.ACCENT_ORANGE, "error": Theme.ACCENT_RED,
            "debug": Theme.TEXT_MUTED,
        }.items():
            self.log_text.tag_config(level, foreground=color)

        self.setup_context_menu()

        # Горячие клавиши
        self.root.bind("<F1>", lambda e: self.show_help())
        self.root.bind("<Control-f>", lambda e: self.show_search())
        self.root.bind("<Control-F>", lambda e: self.show_search())
        self.root.bind("<F5>", lambda e: self.refresh_accounts_table())
        self.root.bind("<Control-s>", lambda e: self.save_to_csv())
        self.root.bind("<Control-S>", lambda e: self.save_to_csv())
        self.root.bind("<Control-q>", lambda e: self._on_closing())
        self.root.bind("<Control-h>", lambda e: self.export_html_report())

    def _build_top_bar(self):
        """Верхняя панель с градиентом, названием и кнопкой About."""
        top = tk.Canvas(self.root, height=56, bg=Theme.BG_DEEP,
                        highlightthickness=0)
        top.pack(fill="x", padx=10, pady=(10, 5))

        # Градиентный фон (имитация через несколько прямоугольников)
        def draw_gradient():
            top.delete("bg")
            w = top.winfo_width()
            h = 56
            if w < 2:
                self.root.after(50, draw_gradient)
                return
            steps = 80
            for i in range(steps):
                t = i / steps
                # Фиолетовый → циан
                r1, g1, b1 = 0x1c, 0x22, 0x30  # BG_CARD
                r2, g2, b2 = 0x24, 0x2b, 0x3d  # BG_ELEVATED
                r = int(r1 + (r2 - r1) * t)
                g = int(g1 + (g2 - g1) * t)
                b = int(b1 + (b2 - b1) * t)
                color = f"#{r:02x}{g:02x}{b:02x}"
                top.create_rectangle(
                    i * w // steps, 0,
                    (i + 1) * w // steps + 1, h,
                    fill=color, outline="", tags="bg",
                )
            # Акцентная полоса снизу
            top.create_rectangle(0, h - 2, w, h, fill=Theme.ACCENT_PRIMARY,
                                 outline="", tags="bg")

            # Текст с названием (поверх градиента)
            top.create_text(20, h // 2, text=f"⚡ {Theme.APP_NAME}",
                            font=Theme.FONT_TITLE, fill=Theme.TEXT_PRIMARY,
                            anchor="w", tags="bg")

            # Версия и автор
            top.create_text(w - 220, h // 2, text=f"v{Theme.VERSION}",
                            font=Theme.FONT_BODY, fill=Theme.ACCENT_SECONDARY,
                            anchor="w", tags="bg")
            top.create_text(w - 160, h // 2, text="✦ by zippa ✦",
                            font=("Segoe UI", 10, "italic bold"),
                            fill=Theme.ACCENT_PRIMARY, anchor="w", tags="bg")

        # Кнопка About — рисуем как текст на canvas
        def on_about_click(event):
            show_about_dialog(self.root)

        top.bind("<Button-1>", on_about_click)
        top.bind("<Enter>", lambda e: top.config(cursor="hand2"))
        top.bind("<Leave>", lambda e: top.config(cursor=""))

        self._top_canvas = top
        self.root.after(100, draw_gradient)
        # Перерисовка при изменении размера
        top.bind("<Configure>", lambda e: draw_gradient())

        # Status bar (внизу top canvas area)
        self.status_bar = tk.Label(
            self.root, text="Готов к работе",
            bg=Theme.BG_DEEP, fg=Theme.TEXT_SECONDARY,
            font=Theme.FONT_SMALL, anchor="e",
        )
        self.status_bar.pack(fill="x", padx=20, pady=(0, 4))

    def setup_context_menu(self) -> None:
        self.log_menu = tk.Menu(self.root, tearoff=0, bg=Theme.BG_ELEVATED,
                                fg=Theme.TEXT_PRIMARY, activebackground=Theme.ACCENT_PRIMARY,
                                activeforeground=Theme.TEXT_INVERSE,
                                borderwidth=0, relief="flat")
        self.log_menu.add_command(label="📋  Копировать", command=self.copy_log)
        self.log_menu.add_command(label="🗑️  Очистить лог", command=self.clear_log)
        self.log_menu.add_command(label="💾  Сохранить лог...", command=self.save_log)
        self.log_menu.add_separator()
        self.log_menu.add_command(label="ℹ️  О программе (by zippa)",
                                  command=lambda: show_about_dialog(self.root))
        self.log_text.bind("<Button-3>", self.show_log_menu)

    def show_log_menu(self, event) -> None:
        self.log_menu.tk_popup(event.x_root, event.y_root)

    def copy_log(self) -> None:
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.log_text.get(tk.SEL_FIRST, tk.SEL_LAST))
        except tk.TclError:
            pass

    def clear_log(self) -> None:
        if messagebox.askyesno("Очистка", "Очистить лог?"):
            self.log_text.delete(1.0, tk.END)

    def save_log(self) -> None:
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log_message(f"📁 Лог сохранён: {filename}")

    def show_help(self) -> None:
        """Окно с горячими клавишами.  [NEW]"""
        win = tk.Toplevel(self.root)
        win.title("Горячие клавиши")
        win.configure(bg=Theme.BG_DEEP)
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        w, h = 480, 420
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        tk.Label(win, text="⌨️  Горячие клавиши", font=Theme.FONT_TITLE,
                 bg=Theme.BG_DEEP, fg=Theme.ACCENT_PRIMARY).pack(pady=(20, 16))

        shortcuts = [
            ("F1", "Эта справка"),
            ("Ctrl + F", "Поиск в таблице пользователей"),
            ("Ctrl + S", "Экспорт в CSV"),
            ("Ctrl + H", "HTML-отчёт об инвайте"),
            ("Ctrl + L", "Очистить лог"),
            ("Ctrl + Q", "Выход"),
            ("F5", "Обновить таблицу аккаунтов"),
            ("Правый клик", "Контекстное меню"),
        ]
        for key, desc in shortcuts:
            row = tk.Frame(win, bg=Theme.BG_DEEP)
            row.pack(fill="x", padx=40, pady=4)
            tk.Label(row, text=key, font=Theme.FONT_MONO, bg=Theme.BG_DEEP,
                     fg=Theme.ACCENT_SECONDARY, width=12, anchor="w").pack(side="left")
            tk.Label(row, text=desc, font=Theme.FONT_BODY, bg=Theme.BG_DEEP,
                     fg=Theme.TEXT_PRIMARY, anchor="w").pack(side="left")

        tk.Label(win, text="\n✦ crafted by zippa ✦", font=("Segoe UI", 10, "italic"),
                 bg=Theme.BG_DEEP, fg=Theme.ACCENT_PRIMARY).pack(side="bottom", pady=20)

        win.bind("<Escape>", lambda e: win.destroy())
        win.focus_force()

    def show_search(self) -> None:
        """Быстрый поиск в таблице пользователей.  [NEW]"""
        if not hasattr(self, "users_tree"):
            return
        if self._search_window and self._search_window.winfo_exists():
            self._search_window.lift()
            return

        win = tk.Toplevel(self.root)
        win.title("🔍 Поиск")
        win.configure(bg=Theme.BG_DEEP)
        win.transient(self.root)
        win.overrideredirect(False)

        w, h = 360, 60
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"{w}x{h}+{(sw-w)//2}+{50}")

        tk.Label(win, text="🔍", font=Theme.FONT_H1, bg=Theme.BG_DEEP,
                 fg=Theme.ACCENT_PRIMARY).pack(side="left", padx=(12, 4))

        var = tk.StringVar()
        entry = tk.Entry(win, textvariable=var, font=Theme.FONT_BODY,
                         bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                         insertbackground=Theme.ACCENT_PRIMARY,
                         relief="flat", highlightthickness=2,
                         highlightbackground=Theme.ACCENT_PRIMARY,
                         highlightcolor=Theme.ACCENT_PRIMARY)
        entry.pack(side="left", fill="x", expand=True, padx=4, pady=12)
        entry.focus_force()

        found_label = tk.Label(win, text="", font=Theme.FONT_SMALL,
                               bg=Theme.BG_DEEP, fg=Theme.ACCENT_SECONDARY)
        found_label.pack(side="left", padx=8)

        matches: List[str] = []
        current_idx = [0]

        def do_search(*_):
            query = var.get().strip().lower()
            matches.clear()
            current_idx[0] = 0
            if not query:
                found_label.config(text="")
                for item in self.users_tree.get_children():
                    self.users_tree.selection_remove(item)
                return
            for item in self.users_tree.get_children():
                values = self.users_tree.item(item, "values")
                vals_str = " ".join(str(v).lower() for v in values)
                if query in vals_str:
                    matches.append(item)
            if matches:
                self.users_tree.selection_set(matches[0])
                self.users_tree.see(matches[0])
                found_label.config(text=f"1/{len(matches)}")
            else:
                found_label.config(text="0/0")

        def next_match(event=None):
            if not matches:
                return
            for item in self.users_tree.get_children():
                self.users_tree.selection_remove(item)
            current_idx[0] = (current_idx[0] + 1) % len(matches)
            self.users_tree.selection_set(matches[current_idx[0]])
            self.users_tree.see(matches[current_idx[0]])
            found_label.config(text=f"{current_idx[0]+1}/{len(matches)}")

        var.trace_add("write", do_search)
        entry.bind("<Return>", next_match)
        entry.bind("<Escape>", lambda e: win.destroy())
        win.bind("<Escape>", lambda e: win.destroy())

        self._search_window = win

    # =====================================================================
    # ВКЛАДКА: АККАУНТЫ
    # =====================================================================
    def setup_accounts_tab(self, notebook: ttk.Notebook) -> None:
        acc_frame = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(acc_frame, text="  👥  Аккаунты  ")

        # Header
        header = tk.Frame(acc_frame, bg=Theme.BG_BASE)
        header.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(header, text="👥 Загрузка готовых сессий", font=Theme.FONT_H1,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).pack(anchor="w")
        tk.Label(header,
                 text="Telethon .session  •  Pyrogram .session  •  TData (Telegram Desktop)\n"
                      "Просто положите все сессии в одну папку и нажмите «Выбрать папку»",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_SECONDARY, justify="left").pack(anchor="w", pady=(2, 0))

        # Кнопки
        btn_frame = tk.Frame(acc_frame, bg=Theme.BG_BASE)
        btn_frame.pack(fill="x", padx=14, pady=8)

        AnimatedButton(btn_frame, text="Выбрать папку", icon="📁",
                       command=self.load_accounts_from_folder,
                       bg=Theme.ACCENT_GREEN, hover_bg="#5dd674",
                       width=160).pack(side="left", padx=(0, 6))
        AnimatedButton(btn_frame, text="Подключить все", icon="🔌",
                       command=self.connect_all_accounts,
                       bg=Theme.ACCENT_BLUE, hover_bg="#7ab8ff",
                       width=150).pack(side="left", padx=6)
        AnimatedButton(btn_frame, text="Отключить все", icon="❌",
                       command=self.disconnect_all_accounts,
                       bg=Theme.ACCENT_RED, hover_bg="#ff6b63",
                       width=150).pack(side="left", padx=6)
        AnimatedButton(btn_frame, text="Обновить", icon="🔄",
                       command=self.refresh_accounts_table,
                       bg=Theme.BG_ELEVATED, hover_bg=Theme.ACCENT_PRIMARY,
                       width=120).pack(side="left", padx=6)
        AnimatedButton(btn_frame, text="Очистить", icon="🗑️",
                       command=self.clear_accounts_list,
                       bg=Theme.BG_ELEVATED, hover_bg=Theme.ACCENT_RED,
                       width=120).pack(side="left", padx=6)

        # Ротация
        rot_frame = tk.LabelFrame(acc_frame, text="  🔄  Ротация аккаунтов  ",
                                  font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                  fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        rot_frame.pack(fill="x", padx=14, pady=6)
        tk.Checkbutton(rot_frame, text="Использовать ВСЕ аккаунты для инвайта",
                       variable=self.account_rotation_enabled,
                       bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY,
                       selectcolor=Theme.BG_INPUT, activebackground=Theme.BG_BASE,
                       activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_BODY).pack(anchor="w", padx=12, pady=(8, 2))
        tk.Label(rot_frame,
                 text="💡 При ротации каждый аккаунт приглашает по несколько пользователей — "
                      "резко снижается риск FloodWait и бана.\n"
                      "Лимит на каждый аккаунт задаётся во вкладке «Инвайт».",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=12, pady=(0, 8))

        # Таблица
        table_frame = tk.LabelFrame(acc_frame, text="  📋  Загруженные аккаунты  ",
                                    font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                    fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=14, pady=6)

        columns = ("№", "Формат", "User ID", "Имя", "Телефон", "DC",
                   "Статус", "✅", "❌", "Темп.")
        self.accounts_tree = ttk.Treeview(table_frame, columns=columns,
                                          show="headings", height=10)
        col_widths = [40, 80, 110, 150, 110, 40, 130, 60, 60, 60]
        for col, width in zip(columns, col_widths):
            self.accounts_tree.heading(col, text=col)
            self.accounts_tree.column(col, width=width, anchor="center")

        v_scroll = ttk.Scrollbar(table_frame, orient="vertical",
                                  command=self.accounts_tree.yview)
        self.accounts_tree.configure(yscrollcommand=v_scroll.set)
        self.accounts_tree.pack(side="left", fill="both", expand=True,
                                 padx=(8, 0), pady=8)
        v_scroll.pack(side="right", fill="y", pady=8)

        # Контекстное меню
        self.acc_menu = tk.Menu(self.root, tearoff=0, bg=Theme.BG_ELEVATED,
                                fg=Theme.TEXT_PRIMARY,
                                activebackground=Theme.ACCENT_PRIMARY,
                                activeforeground=Theme.TEXT_INVERSE, borderwidth=0)
        self.acc_menu.add_command(label="🔌  Подключить", command=self.connect_selected_account)
        self.acc_menu.add_command(label="❌  Отключить", command=self.disconnect_selected_account)
        self.acc_menu.add_separator()
        self.acc_menu.add_command(label="🚫  Отключить от ротации", command=self.disable_selected_account)
        self.acc_menu.add_command(label="✅  Включить в ротацию", command=self.enable_selected_account)
        self.acc_menu.add_separator()
        self.acc_menu.add_command(label="📊  Сбросить статистику", command=self.reset_selected_account_stats)
        self.accounts_tree.bind("<Button-3>", self.show_accounts_menu)
        self.accounts_tree.bind("<Double-1>", lambda e: self.connect_selected_account())

        # Сводка с анимированными счётчиками
        summary_frame = tk.LabelFrame(acc_frame, text="  📊  Сводка  ",
                                      font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                      fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        summary_frame.pack(fill="x", padx=14, pady=(6, 12))

        cards = [
            ("Всего", "total", Theme.TEXT_PRIMARY),
            ("Подключено", "connected", Theme.ACCENT_GREEN),
            ("Активно", "active", Theme.ACCENT_BLUE),
            ("В FloodWait", "flood", Theme.ACCENT_ORANGE),
            ("Инвайтов", "invited", Theme.ACCENT_PRIMARY),
        ]
        for label, key, color in cards:
            card = tk.Frame(summary_frame, bg=Theme.BG_CARD)
            card.pack(side="left", fill="both", expand=True, padx=4, pady=8, ipadx=4, ipady=4)
            tk.Label(card, text=label, font=Theme.FONT_TINY, bg=Theme.BG_CARD,
                     fg=Theme.TEXT_SECONDARY).pack(pady=(4, 0))
            val_label = tk.Label(card, text="0", font=Theme.FONT_H1, bg=Theme.BG_CARD,
                                 fg=color)
            val_label.pack(pady=(0, 4))
            self._counters[f"acc_{key}"] = AnimatedCounter(val_label, duration_ms=600)

    def show_accounts_menu(self, event) -> None:
        item = self.accounts_tree.identify_row(event.y)
        if item:
            self.accounts_tree.selection_set(item)
            self.acc_menu.tk_popup(event.x_root, event.y_root)

    # --- Загрузка аккаунтов ---
    def load_accounts_from_folder(self) -> None:
        if not _HAS_ACCOUNT_LOADER:
            messagebox.showerror("Ошибка", "account_loader.py не найден")
            return
        folder = filedialog.askdirectory(title="Выберите папку с сессиями")
        if not folder:
            return
        self.log_message(f"📁 Сканирую: {folder}", "info")
        self.progress_var.set(0)
        self.progress_label.config(text="Сканирование...")

        def _scan():
            try:
                accounts = self.account_loader.scan_folder(Path(folder))
                self.root.after(0, lambda: self._on_accounts_loaded(accounts))
            except Exception as e:
                self._safe_log(f"❌ Ошибка сканирования: {e}", "error")
            finally:
                self.root.after(0, lambda: self.progress_var.set(0))
                self.root.after(0, lambda: self.progress_label.config(text=""))

        threading.Thread(target=_scan, daemon=True).start()

    def _on_accounts_loaded(self, accounts: List[LoadedAccount]) -> None:
        if not accounts:
            msg = "Не найдено ни одной валидной сессии"
            if self.account_loader.errors:
                msg += "\n\nОшибки:\n" + "\n".join(f"• {e}" for e in self.account_loader.errors[:10])
            messagebox.showwarning("Загрузка", msg)
            Toast.show(self.root, "Сессии не найдены", level="warning")
            return

        # Фильтруем невалидные аккаунты (где auth_key пустой или StringSession не построилась)
        valid_accounts = []
        invalid_count = 0
        invalid_reasons = []
        for acc in accounts:
            if acc.is_valid and acc.telethon_string:
                # Доп. валидация
                try:
                    from account_loader import validate_string_session
                    if validate_string_session(acc.telethon_string):
                        valid_accounts.append(acc)
                    else:
                        invalid_count += 1
                        invalid_reasons.append(f"{acc.source_format} {acc.display_name}: StringSession невалидна")
                except ImportError:
                    valid_accounts.append(acc)
            else:
                invalid_count += 1
                reason = acc.error or "неизвестная причина"
                invalid_reasons.append(f"{acc.source_format} {acc.display_name}: {reason}")

        if not valid_accounts:
            msg = "Все найденные сессии невалидны!\n\nПричины:\n"
            msg += "\n".join(f"• {r}" for r in invalid_reasons[:10])
            messagebox.showerror("Загрузка", msg)
            Toast.show(self.root, "Все сессии невалидны", level="error")
            return

        # ДЕДУПЛИКАЦИЯ по auth_key (а не по user_id — он может быть None у новых Telethon-сессий)
        # Также учитываем source_path для TData (у них auth_key может совпадать, если из одной установки)
        import hashlib as _hashlib
        def _acc_key(acc: LoadedAccount) -> tuple:
            # Хэш auth_key + формат — уникальный идентификатор аккаунта
            auth_hash = _hashlib.md5(acc.auth_key).hexdigest() if acc.auth_key and any(acc.auth_key) else ""
            return (acc.source_format, auth_hash, acc.source_path)

        existing_keys = {_acc_key(a.account) for a in self.loaded_accounts}
        added = 0
        for acc in valid_accounts:
            key = _acc_key(acc)
            if key in existing_keys:
                # Уже загружен этот аккаунт — пропускаем
                continue
            self.loaded_accounts.append(AccountRuntimeInfo(account=acc))
            existing_keys.add(key)
            added += 1

        msg = f"✅ Загружено валидных аккаунтов: {added}"
        if invalid_count:
            msg += f"\n⚠️ Пропущено невалидных: {invalid_count}"
        self.log_message(msg, "success" if not invalid_count else "warning")

        if invalid_count:
            self.log_message("Причины пропуска:", "warning")
            for r in invalid_reasons[:5]:
                self.log_message(f"  • {r}", "warning")

        Toast.show(self.root, "Аккаунты загружены",
                   f"Добавлено: {added}\nВсего: {len(self.loaded_accounts)}"
                   + (f"\nПропущено: {invalid_count}" if invalid_count else ""),
                   "success" if not invalid_count else "warning")
        self.refresh_accounts_table()

        if messagebox.askyesno("Подключение",
                                f"Загружено {added} аккаунтов. Подключить сейчас?"):
            self.connect_all_accounts()

    def refresh_accounts_table(self) -> None:
        for item in self.accounts_tree.get_children():
            self.accounts_tree.delete(item)
        for i, info in enumerate(self.loaded_accounts, 1):
            acc = info.account
            connected = "✅ Да" if info.is_connected else "❌ Нет"
            if info.is_disabled:
                status = "🚫 Откл."
            elif info.flood_until and datetime.now() < info.flood_until:
                remaining = int((info.flood_until - datetime.now()).total_seconds())
                status = f"⏳ Flood {remaining}с"
            elif info.is_connected and info.is_authorized:
                status = "✅ Готов"
            elif info.is_connected and not info.is_authorized:
                status = "⚠️ Не авторизован"
            else:
                status = "⚪ Не подкл."
            temp_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴",
                          "grey": "⚫"}.get(info.temperature, "⚫")
            self.accounts_tree.insert(
                "", "end", iid=str(i - 1),
                values=(i, acc.source_format, acc.user_id or "—",
                        info.me_name or "—", info.me_phone or acc.phone or "—",
                        acc.dc_id, status, info.invited_count,
                        info.failed_count, temp_emoji),
            )

        # Сводка с анимацией
        total = len(self.loaded_accounts)
        connected = sum(1 for a in self.loaded_accounts if a.is_connected and a.is_authorized)
        active = sum(1 for a in self.loaded_accounts
                     if a.is_connected and a.is_authorized
                     and not a.is_disabled
                     and not (a.flood_until and datetime.now() < a.flood_until))
        flood = sum(1 for a in self.loaded_accounts
                    if a.flood_until and datetime.now() < a.flood_until)
        total_invited = sum(a.invited_count for a in self.loaded_accounts)

        if "acc_total" in self._counters:
            self._counters["acc_total"].set(total)
            self._counters["acc_connected"].set(connected)
            self._counters["acc_active"].set(active)
            self._counters["acc_flood"].set(flood)
            self._counters["acc_invited"].set(total_invited)

    def connect_all_accounts(self) -> None:
        if not self.api_id or not self.api_hash:
            messagebox.showerror("Ошибка", "Введите api_id/api_hash!")
            return
        if not self.loaded_accounts:
            messagebox.showinfo("Инфо", "Сначала загрузите аккаунты")
            return
        self.log_message(f"🔌 Подключаю {len(self.loaded_accounts)} аккаунтов...", "info")
        threading.Thread(target=self._connect_all_thread, daemon=True).start()

    def _connect_all_thread(self) -> None:
        total = len(self.loaded_accounts)
        for i, info in enumerate(self.loaded_accounts):
            if info.is_disabled:
                continue
            self.root.after(0, lambda i=i, t=total, info=info: (
                self.progress.set_value((i / t) * 100),
                self.progress_label.config(
                    text=f"Подключение {i+1}/{t}: {info.account.display_name}"
                ),
            ))
            try:
                self._run_coroutine(self._connect_single_account(info))
            except Exception as e:
                info.last_error = str(e)[:80]
            self.root.after(0, self.refresh_accounts_table)
        self.root.after(0, lambda: self.progress.set_value(0))
        self.root.after(0, lambda: self.progress_label.config(text=""))
        connected = sum(1 for a in self.loaded_accounts if a.is_connected and a.is_authorized)
        self._safe_log(f"✅ Подключено: {connected}/{total}", "success")
        if connected > 0:
            Toast.show(self.root, "Аккаунты подключены",
                       f"{connected}/{total} активны", "success")

    async def _connect_single_account(self, info: AccountRuntimeInfo) -> None:
        if info.client and info.client.is_connected():
            try:
                await info.client.disconnect()
            except Exception:
                pass

        # ВАЛИДАЦИЯ StringSession перед созданием клиента
        # (критично — иначе Telethon бросит "Not a valid string")
        session_str = info.account.telethon_string
        if not session_str:
            info.is_connected = False
            info.is_authorized = False
            info.last_error = "Пустая StringSession (auth_key невалиден)"
            self.log_invite(
                f"❌ [{info.account.display_name}] Пропуск: {info.last_error}",
                "error",
            )
            return

        # Доп. валидация
        try:
            from account_loader import validate_string_session
            if not validate_string_session(session_str):
                info.is_connected = False
                info.is_authorized = False
                info.last_error = "StringSession невалидна"
                self.log_invite(
                    f"❌ [{info.account.display_name}] Невалидная сессия",
                    "error",
                )
                return
        except ImportError:
            pass  # модуль недоступен — продолжаем без доп. проверки

        proxy = self._build_proxy()
        kwargs = dict(
            session=StringSession(session_str),
            api_id=int(self.api_id), api_hash=self.api_hash,
            device_model="Desktop", system_version="Windows 10",
            app_version=self.VERSION, lang_code="ru", system_lang_code="ru",
            connection_retries=5, retry_delay=2, request_retries=3, timeout=30,
        )
        if proxy:
            kwargs["proxy"] = proxy

        try:
            info.client = TelegramClient(**kwargs)
            await info.client.connect()
        except ValueError as e:
            # "Not a valid string" или похожие
            info.is_connected = False
            info.is_authorized = False
            info.last_error = f"Невалидная сессия: {e}"
            logger.error(f"Ошибка создания клиента для {info.account.display_name}: {e}")
            return
        except Exception as e:
            info.is_connected = False
            info.is_authorized = False
            info.last_error = f"Ошибка подключения: {str(e)[:80]}"
            logger.error(f"Ошибка подключения {info.account.display_name}: {e}")
            return
        if not info.client.is_connected():
            info.is_connected = False
            info.is_authorized = False
            info.last_error = "Не удалось подключиться"
            return
        info.is_connected = True
        try:
            info.is_authorized = await info.client.is_user_authorized()
            if info.is_authorized:
                try:
                    me = await info.client.get_me()
                    info.me_name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                    info.me_phone = f"+{me.phone}" if me.phone else ""
                    info.account.user_id = me.id
                    info.last_error = ""
                except Exception as e:
                    info.last_error = f"Не удалось получить me: {e}"
            else:
                info.last_error = "Auth key невалиден"
        except AuthKeyUnregisteredError:
            info.is_authorized = False
            info.last_error = "Auth key не зарегистрирован"
        except Exception as e:
            info.is_authorized = False
            info.last_error = str(e)[:80]

    def disconnect_all_accounts(self) -> None:
        def _disconnect():
            for info in self.loaded_accounts:
                if info.client and info.client.is_connected():
                    try:
                        self._run_coroutine(info.client.disconnect(), timeout=10)
                    except Exception:
                        pass
                    info.is_connected = False
                    info.is_authorized = False
            self.root.after(0, self.refresh_accounts_table)
            self._safe_log("✅ Все аккаунты отключены", "info")
        threading.Thread(target=_disconnect, daemon=True).start()

    def clear_accounts_list(self) -> None:
        if not self.loaded_accounts:
            return
        if not messagebox.askyesno("Очистка",
                f"Удалить все {len(self.loaded_accounts)} аккаунтов из списка?"):
            return
        def _cleanup():
            for info in self.loaded_accounts:
                if info.client and info.client.is_connected():
                    try:
                        self._run_coroutine(info.client.disconnect(), timeout=5)
                    except Exception:
                        pass
            self.loaded_accounts.clear()
            self.root.after(0, self.refresh_accounts_table)
            self._safe_log("🗑️ Список очищен", "info")
        threading.Thread(target=_cleanup, daemon=True).start()

    def connect_selected_account(self) -> None:
        selection = self.accounts_tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self.loaded_accounts):
            return
        info = self.loaded_accounts[idx]
        if info.is_disabled:
            messagebox.showinfo("Инфо", "Аккаунт отключён. Сначала включите его.")
            return
        def _connect():
            self._run_coroutine(self._connect_single_account(info))
            self.root.after(0, self.refresh_accounts_table)
        threading.Thread(target=_connect, daemon=True).start()

    def disconnect_selected_account(self) -> None:
        selection = self.accounts_tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if idx >= len(self.loaded_accounts):
            return
        info = self.loaded_accounts[idx]
        def _disconnect():
            if info.client and info.client.is_connected():
                self._run_coroutine(info.client.disconnect(), timeout=10)
            info.is_connected = False
            info.is_authorized = False
            self.root.after(0, self.refresh_accounts_table)
        threading.Thread(target=_disconnect, daemon=True).start()

    def disable_selected_account(self) -> None:
        selection = self.accounts_tree.selection()
        if not selection:
            return
        info = self.loaded_accounts[int(selection[0])]
        info.is_disabled = True
        self.refresh_accounts_table()

    def enable_selected_account(self) -> None:
        selection = self.accounts_tree.selection()
        if not selection:
            return
        info = self.loaded_accounts[int(selection[0])]
        info.is_disabled = False
        self.refresh_accounts_table()

    def reset_selected_account_stats(self) -> None:
        selection = self.accounts_tree.selection()
        if not selection:
            return
        info = self.loaded_accounts[int(selection[0])]
        info.invited_count = 0
        info.failed_count = 0
        info.flood_until = None
        self.refresh_accounts_table()

    def get_available_accounts_for_invite(self) -> List[AccountRuntimeInfo]:
        result = []
        now = datetime.now()
        for info in self.loaded_accounts:
            if not info.is_connected or not info.is_authorized:
                continue
            if info.is_disabled:
                continue
            if info.flood_until and now < info.flood_until:
                continue
            if info.invited_count >= self.rate_limiter.per_account_limit:
                continue
            result.append(info)
        return result

    # =====================================================================
    # ВКЛАДКА: Чаты (зайти / выйти / посмотреть)
    # =====================================================================
    def setup_chats_tab(self, notebook: ttk.Notebook) -> None:
        """Вкладка для массового входа/выхода из чатов всеми аккаунтами.

        Поддерживаемые форматы ссылок:
          - Публичные:  t.me/username, https://t.me/username, @username
          - Приватные:  t.me/+AbCdEf, https://t.me/+AbCdEf, t.me/joinchat/AbCdEf
        """
        cf = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(cf, text="  🚪  Чаты  ")

        # Header
        header = tk.Frame(cf, bg=Theme.BG_BASE)
        header.pack(fill="x", padx=14, pady=(10, 6))
        tk.Label(header, text="🚪 Вход в чаты всеми аккаунтами",
                 font=Theme.FONT_H1, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).pack(anchor="w")
        tk.Label(header,
                 text="Массовый вход/выход из чатов. Поддерживаются публичные и приватные ссылки.\n"
                      "Задержка между аккаунтами снижает риск FloodWait и бана.",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_SECONDARY, justify="left").pack(anchor="w", pady=(2, 0))

        # Настройки
        settings = tk.LabelFrame(cf, text="  Настройки  ", font=Theme.FONT_H2,
                                 bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                 bd=1, relief="solid")
        settings.pack(fill="x", padx=14, pady=8)

        link_row = tk.Frame(settings, bg=Theme.BG_BASE)
        link_row.pack(fill="x", padx=12, pady=8)
        tk.Label(link_row, text="Ссылка на чат:", width=15, anchor="w",
                 font=Theme.FONT_BODY, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).pack(side="left")
        self.chat_link_entry = tk.Entry(link_row, width=45, font=Theme.FONT_BODY,
                                         bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                         insertbackground=Theme.ACCENT_PRIMARY,
                                         relief="flat", highlightthickness=2,
                                         highlightbackground=Theme.BORDER,
                                         highlightcolor=Theme.ACCENT_PRIMARY)
        self.chat_link_entry.pack(side="left", padx=4)
        # Подсказка с примерами
        tk.Label(link_row, text="Примеры: t.me/username  •  t.me/+AbCdEf  •  @username",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_MUTED).pack(side="left", padx=(8, 4))

        # Опции входа
        opts_row = tk.LabelFrame(settings, text="  Опции  ", font=Theme.FONT_H2,
                                  bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                  bd=1, relief="solid")
        opts_row.pack(fill="x", padx=12, pady=8)

        opts_inner = tk.Frame(opts_row, bg=Theme.BG_BASE)
        opts_inner.pack(fill="x", padx=12, pady=8)

        tk.Label(opts_inner, text="Задержка между аккаунтами (сек):",
                 font=Theme.FONT_BODY, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).grid(row=0, column=0, padx=4, pady=6, sticky="w")
        self.chat_join_delay = tk.Entry(opts_inner, width=6, font=Theme.FONT_BODY,
                                         bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                         insertbackground=Theme.ACCENT_PRIMARY,
                                         relief="flat", highlightthickness=2,
                                         highlightbackground=Theme.BORDER,
                                         highlightcolor=Theme.ACCENT_PRIMARY)
        self.chat_join_delay.insert(0, "45")
        self.chat_join_delay.grid(row=0, column=1, padx=4, pady=6)

        self.chat_join_only_active = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_inner,
                       text="Только активные аккаунты (пропускать FloodWait/отключённые)",
                       variable=self.chat_join_only_active,
                       bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY,
                       selectcolor=Theme.BG_INPUT, activebackground=Theme.BG_BASE,
                       activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_SMALL).grid(row=1, column=0, columnspan=3,
                                                    sticky="w", pady=4)

        self.chat_join_skip_joined = tk.BooleanVar(value=True)
        tk.Checkbutton(opts_inner,
                       text="Пропускать аккаунты, уже состоящие в чате",
                       variable=self.chat_join_skip_joined,
                       bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY,
                       selectcolor=Theme.BG_INPUT, activebackground=Theme.BG_BASE,
                       activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_SMALL).grid(row=2, column=0, columnspan=3,
                                                    sticky="w", pady=2)

        # Кнопки управления
        btn_row = tk.Frame(settings, bg=Theme.BG_BASE)
        btn_row.pack(fill="x", padx=12, pady=10)

        AnimatedButton(btn_row, text="Войти в чат", icon="🚪",
                       command=self.join_chat_all_accounts,
                       bg=Theme.ACCENT_GREEN, hover_bg="#5dd674",
                       width=170).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="Выйти из чата", icon="🚪←",
                       command=self.leave_chat_all_accounts,
                       bg=Theme.ACCENT_ORANGE, hover_bg="#ffbd77",
                       width=170).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="Проверить статус", icon="🔍",
                       command=self.check_chat_membership,
                       bg=Theme.ACCENT_BLUE, hover_bg="#7ab8ff",
                       width=180).pack(side="left", padx=4)

        # Прогресс
        self.chat_progress_var = tk.DoubleVar(value=0)
        self.chat_progress = AnimatedProgress(settings, width=600, height=8)
        self.chat_progress.pack(fill="x", padx=12, pady=(0, 8))

        # Лог чатов
        log_frame = tk.LabelFrame(cf, text="  📝 Лог операций  ",
                                  font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                  fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True, padx=14, pady=(6, 12))

        self.chat_log, chat_sb = styled_scrolledtext(log_frame, height=12,
                                                      font=Theme.FONT_MONO_SMALL)
        self.chat_log.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        chat_sb.pack(side="right", fill="y", pady=8)
        for tag, color in {
            "success": Theme.ACCENT_GREEN, "error": Theme.ACCENT_RED,
            "warning": Theme.ACCENT_ORANGE, "info": Theme.TEXT_PRIMARY,
        }.items():
            self.chat_log.tag_config(tag, foreground=color)
        self.chat_log.insert("1.0", "Лог операций с чатами:\n" + "=" * 50 + "\n")

        # Сводка
        self.chat_summary = tk.Label(cf, text="", font=Theme.FONT_SMALL,
                                      bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY)
        self.chat_summary.pack(fill="x", padx=14, pady=(0, 8))

    def _log_chat(self, message: str, level: str = "info") -> None:
        """Логирование во вкладку Чаты — потокобезопасно."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        def _append():
            self.chat_log.insert(tk.END, log_entry)
            start = self.chat_log.index("end-1c linestart")
            end = self.chat_log.index("end-1c linestart")
            if level in ("info", "success", "warning", "error"):
                self.chat_log.tag_add(level, start, end)
            self.chat_log.see(tk.END)

        try:
            self.root.after(0, _append)
        except RuntimeError:
            logger.info(message)

    def _parse_chat_link(self, link: str) -> dict:
        """Разобрать ссылку на чат.

        Возвращает dict с полями:
          - type: 'public' | 'private'
          - username: str (для public)
          - hash: str (для private)
          - raw: исходная ссылка

        Поддерживаемые форматы:
          - t.me/username
          - https://t.me/username
          - @username
          - t.me/+AbCdEf
          - https://t.me/+AbCdEf
          - t.me/joinchat/AbCdEf
          - https://t.me/joinchat/AbCdEf
        """
        link = link.strip()
        if not link:
            return {"type": "invalid", "raw": link, "error": "Пустая ссылка"}

        # Убираем протокол
        clean = link
        for proto in ("https://", "http://", "www."):
            if clean.lower().startswith(proto):
                clean = clean[len(proto):]
                break

        # @username
        if clean.startswith("@"):
            return {"type": "public", "username": clean[1:], "raw": link}

        # t.me/+hash (приватный)
        if "t.me/+" in clean.lower():
            hash_part = clean.split("+", 1)[1]
            return {"type": "private", "hash": hash_part, "raw": link}

        # t.me/joinchat/hash (приватный)
        if "t.me/joinchat/" in clean.lower():
            hash_part = clean.split("joinchat/", 1)[1]
            return {"type": "private", "hash": hash_part, "raw": link}

        # t.me/username (публичный)
        if "t.me/" in clean.lower():
            username = clean.split("t.me/", 1)[1].split("/")[0].split("?")[0]
            if username and not username.startswith("+"):
                return {"type": "public", "username": username, "raw": link}

        return {"type": "invalid", "raw": link, "error": f"Не распознанный формат: {link}"}

    def join_chat_all_accounts(self) -> None:
        """Войти в чат всеми активными аккаунтами."""
        self._mass_chat_operation(action="join")

    def leave_chat_all_accounts(self) -> None:
        """Выйти из чата всеми активными аккаунтами."""
        self._mass_chat_operation(action="leave")

    def check_chat_membership(self) -> None:
        """Проверить, кто из аккаунтов состоит в чате."""
        self._mass_chat_operation(action="check")

    def _mass_chat_operation(self, action: str) -> None:
        """Общая логика для join/leave/check.

        action: 'join' | 'leave' | 'check'
        """
        # Проверки
        if not self.api_id or not self.api_hash:
            messagebox.showerror("Ошибка", "Сначала введите api_id/api_hash!")
            return

        link = self.chat_link_entry.get().strip()
        if not link:
            messagebox.showerror("Ошибка", "Введите ссылку на чат!")
            return

        parsed = self._parse_chat_link(link)
        if parsed["type"] == "invalid":
            messagebox.showerror("Ошибка", f"Неверная ссылка:\n{parsed.get('error', '')}")
            return

        # Получаем список аккаунтов
        if self.chat_join_only_active.get():
            accounts = [info for info in self.loaded_accounts
                        if info.is_connected and info.is_authorized
                        and not info.is_disabled
                        and not (info.flood_until and datetime.now() < info.flood_until)]
        else:
            accounts = [info for info in self.loaded_accounts
                        if info.is_connected and info.is_authorized and not info.is_disabled]

        if not accounts:
            messagebox.showerror("Ошибка",
                "Нет активных аккаунтов! Сначала загрузите и подключите аккаунты.")
            return

        # Валидация задержки
        try:
            delay = int(self.chat_join_delay.get())
            if not (0 <= delay <= 600):
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка", "Задержка должна быть 0..600 сек!")
            return

        # Подтверждение
        action_names = {
            "join": "войти в",
            "leave": "выйти из",
            "check": "проверить участие в",
        }
        action_verb = action_names.get(action, "обработать")
        confirm = (f"Вы уверены, что хотите {action_verb} чат ВСЕМИ аккаунтами?\n\n"
                   f"Аккаунтов: {len(accounts)}\n"
                   f"Ссылка: {parsed['raw']}\n"
                   f"Тип: {'публичный' if parsed['type'] == 'public' else 'приватный'}\n"
                   f"Задержка: {delay} сек\n\n")
        if action == "join":
            confirm += ("⚠️ ВНИМАНИЕ:\n"
                        "• Вход 10+ аккаунтов с одного IP в один чат — подозрительный паттерн\n"
                        "• Используйте задержку минимум 30-60 сек\n"
                        "• Рекомендуется прокси/VPN для каждого аккаунта")
        elif action == "leave":
            confirm += "⚠️ Выход массовый — необратимая операция."
        if not messagebox.askyesno("Подтверждение", confirm):
            return

        # Запускаем в отдельном потоке
        action_labels = {
            "join": ("🚪 ВХОД В ЧАТ", "вход"),
            "leave": ("🚪 ВЫХОД ИЗ ЧАТА", "выход"),
            "check": ("🔍 ПРОВЕРКА УЧАСТИЯ", "проверка"),
        }
        title, _ = action_labels.get(action, (action, action))

        self._log_chat("=" * 50, "info")
        self._log_chat(f"{title}: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self._log_chat(f"Ссылка: {parsed['raw']}", "info")
        self._log_chat(f"Тип: {'публичный' if parsed['type'] == 'public' else 'приватный'}", "info")
        self._log_chat(f"Аккаунтов: {len(accounts)}", "info")
        self._log_chat(f"Задержка: {delay} сек", "info")
        self._log_chat("=" * 50, "info")

        threading.Thread(
            target=self._mass_chat_thread,
            args=(action, parsed, accounts, delay),
            daemon=True,
        ).start()

    def _mass_chat_thread(self, action: str, parsed: dict,
                           accounts: List[AccountRuntimeInfo], delay: int) -> None:
        """Поток выполнения массовой операции с чатом."""
        try:
            self._run_coroutine(
                self._mass_chat_coroutine(action, parsed, accounts, delay),
                timeout=86400,  # 24 часа максимум
            )
        except Exception as e:
            self._log_chat(f"❌ Критическая ошибка: {e}", "error")
        finally:
            self.root.after(0, lambda: self.chat_progress.set_value(0))

    async def _mass_chat_coroutine(self, action: str, parsed: dict,
                                    accounts: List[AccountRuntimeInfo], delay: int) -> None:
        """Корутина массовой операции с чатом."""
        total = len(accounts)
        success = 0
        failed = 0
        skipped = 0
        already = 0

        for i, info in enumerate(accounts):
            label = info.me_name or info.account.display_name
            self._log_chat(f"🔄 [{i+1}/{total}] {label}...", "info")
            self.root.after(0, lambda p=((i)/total)*100: self.chat_progress.set_value(p))

            try:
                result = await self._chat_operation_single(
                    info.client, action, parsed, info
                )
                if result == "success":
                    success += 1
                    if action == "join":
                        self._log_chat(f"✅ [{label}] Вошёл в чат", "success")
                    elif action == "leave":
                        self._log_chat(f"✅ [{label}] Вышел из чата", "success")
                    elif action == "check":
                        self._log_chat(f"✅ [{label}] В чате", "success")
                elif result == "already":
                    already += 1
                    if action == "join":
                        self._log_chat(f"⏭️ [{label}] Уже в чате — пропуск", "info")
                    elif action == "leave":
                        self._log_chat(f"⏭️ [{label}] Не в чате — пропуск", "info")
                elif result == "not_member":
                    if action == "check":
                        self._log_chat(f"ℹ️ [{label}] Не состоит в чате", "info")
                        skipped += 1
                    else:
                        skipped += 1
                elif result == "skipped":
                    skipped += 1
                else:
                    failed += 1

            except FloodWaitError as e:
                wait_time = max(1, e.seconds)
                info.flood_until = datetime.now() + timedelta(seconds=wait_time)
                self._log_chat(f"⏳ [{label}] FloodWait: {wait_time}с", "warning")
                failed += 1
                self.root.after(0, self.refresh_accounts_table)
            except ChannelPrivateError:
                self._log_chat(f"❌ [{label}] Чат приватный или нет доступа", "error")
                failed += 1
            except Exception as e:
                err_str = str(e)[:120]
                self._log_chat(f"❌ [{label}] Ошибка: {err_str}", "error")
                failed += 1

            # Задержка перед следующим аккаунтом (кроме последнего)
            if i < total - 1 and delay > 0:
                self.root.after(
                    0, lambda d=delay: self.progress_label.config(
                        text=f"Ожидание {d}с перед следующим аккаунтом..."
                    )
                )
                waited = 0
                while waited < delay:
                    await asyncio.sleep(min(2, delay - waited))
                    waited += 2

        # Финал
        self.root.after(0, lambda: self.chat_progress.set_value(100))
        self._log_chat("=" * 50, "info")
        action_word = {"join": "вход", "leave": "выход", "check": "проверка"}[action]
        self._log_chat(f"🎯 {action_word.upper()} ЗАВЕРШЁН", "info")
        self._log_chat(f"✅ Успешно: {success}", "success")
        if already:
            self._log_chat(f"⏭️ Уже обработано: {already}", "info")
        if skipped:
            self._log_chat(f"ℹ️ Пропущено: {skipped}", "info")
        self._log_chat(f"❌ Ошибок: {failed}", "error")
        self._log_chat("=" * 50, "info")

        # Обновляем сводку
        summary = (f"Последняя операция: {action_word} | "
                   f"✅ {success} | ⏭️ {already} | ℹ️ {skipped} | ❌ {failed} | "
                   f"Всего: {total}")
        self.root.after(0, lambda: self.chat_summary.config(text=summary))

        # Toast
        if failed == 0:
            Toast.show(self.root, f"{action_word.capitalize()} завершён",
                       f"Успешно: {success}/{total}", "success")
        elif success > 0:
            Toast.show(self.root, f"{action_word.capitalize()} частично",
                       f"Успешно: {success}, ошибок: {failed}", "warning")
        else:
            Toast.show(self.root, f"{action_word.capitalize()} не удался",
                       f"Ошибок: {failed}", "error")

    async def _chat_operation_single(self, client: TelegramClient, action: str,
                                      parsed: dict, info: AccountRuntimeInfo) -> str:
        """Выполнить операцию для одного аккаунта.

        Returns:
            'success' — операция выполнена
            'already' — уже в нужном состоянии (в чате при join / не в чате при leave)
            'not_member' — не состоит в чате (для check)
            'skipped' — пропущен по другой причине
        """
        from telethon.tl.functions.channels import (
            JoinChannelRequest, LeaveChannelRequest,
        )
        from telethon.tl.functions.messages import (
            ImportChatInviteRequest, CheckChatInviteRequest,
            DeleteChatUserRequest,
        )
        from telethon.errors import (
            UserAlreadyParticipantError, InviteHashExpiredError,
            InviteHashInvalidError, UserNotParticipantError,
        )

        chat_type = parsed["type"]

        if action == "join":
            if chat_type == "public":
                username = parsed["username"]
                try:
                    await client(JoinChannelRequest(username))
                    return "success"
                except UserAlreadyParticipantError:
                    return "already"
                except Exception as e:
                    # Иногда Telegram бросает общую ошибку — проверим, может уже в чате
                    if "already" in str(e).lower() or "participant" in str(e).lower():
                        return "already"
                    raise

            elif chat_type == "private":
                hash_code = parsed["hash"]
                # Сначала проверяем приглашение
                try:
                    check_result = await client(CheckChatInviteRequest(hash_code))
                    # ChatInviteAlready — уже участник
                    from telethon.tl.types import ChatInviteAlready
                    if isinstance(check_result, ChatInviteAlready):
                        return "already"
                except (InviteHashExpiredError, InviteHashInvalidError) as e:
                    raise ChannelPrivateError(f"Приглашение невалидно: {e}")

                # Импортируем приглашение (входим)
                try:
                    await client(ImportChatInviteRequest(hash_code))
                    return "success"
                except UserAlreadyParticipantError:
                    return "already"
                except Exception as e:
                    if "already" in str(e).lower() or "participant" in str(e).lower():
                        return "already"
                    raise

        elif action == "leave":
            if chat_type == "public":
                username = parsed["username"]
                try:
                    # Get entity first to check membership
                    entity = await client.get_entity(username)
                    await client(LeaveChannelRequest(entity))
                    return "success"
                except UserNotParticipantError:
                    return "already"
                except Exception as e:
                    err_str = str(e).lower()
                    if "not participant" in err_str or "not a member" in err_str:
                        return "already"
                    raise

            elif chat_type == "private":
                # Для приватных чатов нужно сначала получить entity через hash
                hash_code = parsed["hash"]
                try:
                    check_result = await client(CheckChatInviteRequest(hash_code))
                    from telethon.tl.types import ChatInviteAlready
                    if isinstance(check_result, ChatInviteAlready):
                        chat = check_result.chat
                        await client(DeleteChatUserRequest(
                            chat_id=chat.id, user_id="me"
                        ))
                        return "success"
                    else:
                        # Не участник — приглашение ещё активно
                        return "already"
                except UserNotParticipantError:
                    return "already"
                except Exception as e:
                    err_str = str(e).lower()
                    if "not participant" in err_str or "not a member" in err_str:
                        return "already"
                    raise

        elif action == "check":
            if chat_type == "public":
                username = parsed["username"]
                try:
                    entity = await client.get_entity(username)
                    # Проверяем через GetParticipantRequest
                    # Telethon 1.44: participant вместо user_id
                    from telethon.tl.functions.channels import GetParticipantRequest
                    me = await client.get_me()
                    try:
                        await client(GetParticipantRequest(
                            channel=entity, participant=me.id
                        ))
                        return "success"  # состоит в чате
                    except UserNotParticipantError:
                        return "not_member"
                except Exception as e:
                    # Если не можем получить entity — возможно приватный или удалён
                    err_str = str(e).lower()
                    if "private" in err_str or "forbidden" in err_str:
                        return "not_member"
                    raise

            elif chat_type == "private":
                hash_code = parsed["hash"]
                try:
                    check_result = await client(CheckChatInviteRequest(hash_code))
                    from telethon.tl.types import ChatInviteAlready
                    if isinstance(check_result, ChatInviteAlready):
                        return "success"
                    else:
                        return "not_member"
                except Exception:
                    return "not_member"

        return "skipped"

    # =====================================================================
    # ВКЛАДКА: Ручная авторизация
    # =====================================================================
    def setup_auth_tab(self, notebook: ttk.Notebook) -> None:
        auth_frame = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(auth_frame, text="  🔐  Ручная  ")

        left = tk.Frame(auth_frame, bg=Theme.BG_BASE)
        left.pack(side="left", fill="both", expand=True, padx=14, pady=10)
        tk.Label(left, text="📱 Ручная авторизация (один аккаунт)",
                 font=Theme.FONT_H1, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(0, 4))
        tk.Label(left,
                 text="💡 Для нескольких аккаунтов используйте вкладку «👥 Аккаунты»\n"
                      "Здесь — ручная авторизация по номеру телефона.",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_SECONDARY, justify="left").pack(anchor="w", pady=(0, 12))

        # Сессии
        sess_frame = tk.LabelFrame(left, text="  Управление сессиями  ",
                                   font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                   fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        sess_frame.pack(fill="x", pady=8)
        inner = tk.Frame(sess_frame, bg=Theme.BG_BASE)
        inner.pack(fill="x", padx=12, pady=10)
        AnimatedButton(inner, text="Показать сессии", icon="📋",
                       command=self.show_sessions, bg=Theme.BG_ELEVATED,
                       hover_bg=Theme.ACCENT_PRIMARY, width=180).pack(side="left", padx=4)
        AnimatedButton(inner, text="Очистить все", icon="🗑️",
                       command=self.clear_sessions, bg=Theme.ACCENT_RED,
                       hover_bg="#ff6b63", width=180).pack(side="left", padx=4)

        # Авторизация
        auth_frame2 = tk.LabelFrame(left, text="  Быстрая авторизация  ",
                                    font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                    fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        auth_frame2.pack(fill="x", pady=8)
        a_inner = tk.Frame(auth_frame2, bg=Theme.BG_BASE)
        a_inner.pack(fill="x", padx=12, pady=10)
        tk.Label(a_inner, text="Номер телефона (+79991234567):",
                 font=Theme.FONT_BODY, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).pack(anchor="w")
        phone_row = tk.Frame(a_inner, bg=Theme.BG_BASE)
        phone_row.pack(fill="x", pady=4)
        self.phone_entry = tk.Entry(phone_row, width=22, font=Theme.FONT_BODY,
                                     bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                     insertbackground=Theme.ACCENT_PRIMARY,
                                     relief="flat", highlightthickness=2,
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.ACCENT_PRIMARY)
        self.phone_entry.pack(side="left", padx=(0, 8))
        AnimatedButton(phone_row, text="Авторизоваться", icon="📞",
                       command=self.start_auth, bg=Theme.ACCENT_BLUE,
                       hover_bg="#7ab8ff").pack(side="left")
        self.code_btn = AnimatedButton(a_inner, text="Ввести код", icon="🔑",
                                        command=self.enter_code,
                                        bg=Theme.BG_ELEVATED,
                                        hover_bg=Theme.ACCENT_PRIMARY, width=180)
        self.code_btn.pack(pady=6)

        # Прокси
        proxy_frame = tk.LabelFrame(left, text="  🌐  Прокси (опционально)  ",
                                    font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                    fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        proxy_frame.pack(fill="x", pady=8)
        p_inner = tk.Frame(proxy_frame, bg=Theme.BG_BASE)
        p_inner.pack(fill="x", padx=12, pady=10)
        tk.Label(p_inner, text="Формат: socks5://user:pass@host:port",
                 font=Theme.FONT_SMALL, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_SECONDARY).pack(anchor="w")
        self.proxy_entry = tk.Entry(p_inner, width=40, font=Theme.FONT_BODY,
                                     bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                     insertbackground=Theme.ACCENT_PRIMARY,
                                     relief="flat", highlightthickness=2,
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.ACCENT_PRIMARY)
        self.proxy_entry.pack(fill="x", pady=4)

        # Правая часть
        right = tk.Frame(auth_frame, bg=Theme.BG_BASE)
        right.pack(side="right", fill="both", expand=True, padx=14, pady=10)
        info_frame = tk.LabelFrame(right, text="  Информация о сессии  ",
                                   font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                   fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        info_frame.pack(fill="both", expand=True)
        self.session_info, sb = styled_scrolledtext(info_frame, height=15)
        self.session_info.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        sb.pack(side="right", fill="y", pady=8)
        self.session_info.insert("1.0", "Информация появится после авторизации")

        self.auth_status = tk.Label(right, text="❌ Не авторизован",
                                    font=Theme.FONT_H2, bg=Theme.BG_BASE, fg=Theme.ACCENT_RED)
        self.auth_status.pack(pady=10)

        if self.config and self.config.get("phone"):
            self.phone_entry.delete(0, tk.END)
            self.phone_entry.insert(0, self.config["phone"])

    # =====================================================================
    # ВКЛАДКА: API Настройки
    # =====================================================================
    def setup_api_tab(self, notebook: ttk.Notebook) -> None:
        api_frame = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(api_frame, text="  ⚙️  API  ")

        tk.Label(api_frame, text="⚙️ Настройки Telegram API", font=Theme.FONT_TITLE,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).pack(pady=(20, 10))

        form = tk.Frame(api_frame, bg=Theme.BG_BASE)
        form.pack(pady=10)

        tk.Label(form, text="API ID:", width=15, anchor="w", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=0, column=0, pady=10)
        self.api_id_entry = tk.Entry(form, width=32, show="*", font=Theme.FONT_BODY,
                                      bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                      insertbackground=Theme.ACCENT_PRIMARY,
                                      relief="flat", highlightthickness=2,
                                      highlightbackground=Theme.BORDER,
                                      highlightcolor=Theme.ACCENT_PRIMARY)
        self.api_id_entry.grid(row=0, column=1, pady=10, padx=8)

        tk.Label(form, text="API Hash:", width=15, anchor="w", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=1, column=0, pady=10)
        self.api_hash_entry = tk.Entry(form, width=32, show="*", font=Theme.FONT_BODY,
                                        bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                        insertbackground=Theme.ACCENT_PRIMARY,
                                        relief="flat", highlightthickness=2,
                                        highlightbackground=Theme.BORDER,
                                        highlightcolor=Theme.ACCENT_PRIMARY)
        self.api_hash_entry.grid(row=1, column=1, pady=10, padx=8)

        show_var = tk.BooleanVar()
        tk.Checkbutton(form, text="Показать", variable=show_var,
                       command=lambda: self._toggle_pwd(show_var.get()),
                       bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY,
                       selectcolor=Theme.BG_INPUT, activebackground=Theme.BG_BASE,
                       activeforeground=Theme.TEXT_PRIMARY).grid(row=2, column=1, pady=5, sticky="w")

        if self.api_id and self.api_hash:
            self.api_id_entry.insert(0, self.api_id)
            self.api_hash_entry.insert(0, self.api_hash)

        AnimatedButton(form, text="Сохранить настройки", icon="💾",
                       command=self.save_api_settings, bg=Theme.ACCENT_GREEN,
                       hover_bg="#5dd674", width=240).grid(row=3, column=0, columnspan=2, pady=20)

        info_text = (
            "📌 Инструкция по получению API данных:\n"
            "1. Перейдите на https://my.telegram.org\n"
            "2. Войдите под своим номером телефона\n"
            "3. В разделе «API Development Tools»\n"
            "4. Создайте новое приложение\n"
            "5. Скопируйте API ID и API Hash\n"
            "6. Вставьте их в поля выше\n\n"
            "⚠️ Эти api_id/api_hash будут использоваться для ВСЕХ загруженных аккаунтов.\n"
            "auth_key аккаунта не привязан к конкретному api_id — любой валидный работает.\n\n"
            "✦ crafted by zippa ✦"
        )
        tk.Label(api_frame, text=info_text, justify="left", font=Theme.FONT_SMALL,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).pack(pady=20, padx=20)

    def _toggle_pwd(self, show: bool) -> None:
        self.api_id_entry.config(show="" if show else "*")
        self.api_hash_entry.config(show="" if show else "*")

    def save_api_settings(self) -> None:
        api_id = self.api_id_entry.get().strip()
        api_hash = self.api_hash_entry.get().strip()
        if not api_id or not api_hash:
            messagebox.showerror("Ошибка", "Заполните оба поля!")
            return
        if not api_id.isdigit():
            messagebox.showerror("Ошибка", "API ID должен состоять из цифр!")
            return
        if len(api_hash) < 16:
            messagebox.showerror("Ошибка", "API Hash слишком короткий!")
            return
        self.api_id = api_id
        self.api_hash = api_hash
        phone = self.phone_entry.get().strip() if hasattr(self, "phone_entry") else ""
        self.config_manager.save_config(api_id, api_hash, phone)
        self.log_message("✅ API настройки сохранены!", "success")
        Toast.show(self.root, "Сохранено", "API настройки обновлены", "success")

    # =====================================================================
    # ВКЛАДКА: Парсинг
    # =====================================================================
    def setup_parser_tab(self, notebook: ttk.Notebook) -> None:
        pf = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(pf, text="  🔍  Парсинг  ")

        settings = tk.LabelFrame(pf, text="  Настройки парсинга  ",
                                 font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                 fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        settings.pack(fill="x", padx=14, pady=10)

        link_row = tk.Frame(settings, bg=Theme.BG_BASE)
        link_row.pack(fill="x", padx=12, pady=8)
        tk.Label(link_row, text="Ссылка:", width=10, anchor="w", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).pack(side="left")
        self.group_link = tk.Entry(link_row, width=42, font=Theme.FONT_BODY,
                                    bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                    insertbackground=Theme.ACCENT_PRIMARY,
                                    relief="flat", highlightthickness=2,
                                    highlightbackground=Theme.BORDER,
                                    highlightcolor=Theme.ACCENT_PRIMARY)
        self.group_link.pack(side="left", padx=4)
        self.recent_var = tk.StringVar()
        ttk.Combobox(link_row, textvariable=self.recent_var,
                     values=self.recent_groups, width=22).pack(side="left", padx=4)

        # Аккаунт для парсинга
        acc_row = tk.Frame(settings, bg=Theme.BG_BASE)
        acc_row.pack(fill="x", padx=12, pady=4)
        tk.Label(acc_row, text="Аккаунт:", width=10, anchor="w", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).pack(side="left")
        self.parser_account_var = tk.StringVar(value="auto")
        self.parser_account_combo = ttk.Combobox(
            acc_row, textvariable=self.parser_account_var,
            values=["auto (первый активный)"], width=38, state="readonly")
        self.parser_account_combo.pack(side="left", padx=4)
        AnimatedButton(acc_row, text="Обновить", icon="🔄",
                       command=self.update_parser_account_list,
                       bg=Theme.BG_ELEVATED, hover_bg=Theme.ACCENT_PRIMARY,
                       width=110, height=28).pack(side="left", padx=4)

        # Методы
        method_frame = tk.LabelFrame(settings, text="  Метод  ", font=Theme.FONT_H2,
                                     bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                     bd=1, relief="solid")
        method_frame.pack(fill="x", padx=12, pady=8)
        self.parser_method = tk.StringVar(value="participants")
        for text, val in [("👥 Участники (рекомендуется)", "participants"),
                          ("📝 Сообщения", "messages"),
                          ("⚡ Быстрый (первые 100)", "quick")]:
            tk.Radiobutton(method_frame, text=text, variable=self.parser_method,
                           value=val, bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY,
                           selectcolor=Theme.BG_INPUT, activebackground=Theme.BG_BASE,
                           activeforeground=Theme.TEXT_PRIMARY,
                           font=Theme.FONT_BODY).pack(anchor="w", padx=8, pady=2)
        self.aggressive_var = tk.BooleanVar(value=False)
        tk.Checkbutton(method_frame, text="Aggressive mode",
                       variable=self.aggressive_var, bg=Theme.BG_BASE,
                       fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT,
                       activebackground=Theme.BG_BASE, activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_SMALL).pack(anchor="w", padx=8, pady=2)

        # Фильтры
        filter_row = tk.Frame(settings, bg=Theme.BG_BASE)
        filter_row.pack(fill="x", padx=12, pady=8)
        tk.Label(filter_row, text="Лимит:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).pack(side="left")
        self.limit_entry = tk.Entry(filter_row, width=8, font=Theme.FONT_BODY,
                                     bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                     insertbackground=Theme.ACCENT_PRIMARY,
                                     relief="flat", highlightthickness=2,
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.ACCENT_PRIMARY)
        self.limit_entry.insert(0, "200")
        self.limit_entry.pack(side="left", padx=4)

        self.filter_bots = tk.BooleanVar(value=True)
        self.filter_deleted = tk.BooleanVar(value=True)
        self.filter_no_username = tk.BooleanVar(value=False)
        for var, text in [(self.filter_bots, "Исключить ботов"),
                          (self.filter_deleted, "Исключить удалённые"),
                          (self.filter_no_username, "Только с @username")]:
            tk.Checkbutton(filter_row, text=text, variable=var, bg=Theme.BG_BASE,
                           fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT,
                           activebackground=Theme.BG_BASE, activeforeground=Theme.TEXT_PRIMARY,
                           font=Theme.FONT_SMALL).pack(side="left", padx=6)

        self.filter_inactive_days = tk.StringVar(value="0")
        tk.Label(filter_row, text="Активность (дн.):", font=Theme.FONT_SMALL,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).pack(side="left", padx=(12, 2))
        tk.Entry(filter_row, textvariable=self.filter_inactive_days, width=5,
                 font=Theme.FONT_BODY, bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                 insertbackground=Theme.ACCENT_PRIMARY, relief="flat",
                 highlightthickness=2, highlightbackground=Theme.BORDER,
                 highlightcolor=Theme.ACCENT_PRIMARY).pack(side="left")

        # Кнопки
        btn_row = tk.Frame(settings, bg=Theme.BG_BASE)
        btn_row.pack(fill="x", padx=12, pady=10)
        AnimatedButton(btn_row, text="Начать парсинг", icon="🎯",
                       command=self.start_parsing, bg=Theme.ACCENT_GREEN,
                       hover_bg="#5dd674", width=160).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="CSV", icon="💾",
                       command=self.save_to_csv, bg=Theme.ACCENT_BLUE,
                       hover_bg="#7ab8ff", width=90).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="JSON", icon="💾",
                       command=self.save_to_json, bg=Theme.ACCENT_SECONDARY,
                       hover_bg="#5dd6de", width=90).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="Импорт", icon="📥",
                       command=self.import_csv, bg=Theme.ACCENT_PINK,
                       hover_bg="#ff98c6", width=90).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="Анализ", icon="📊",
                       command=self.analyze_users, bg=Theme.ACCENT_PRIMARY,
                       hover_bg="#bd8cff", width=90).pack(side="left", padx=4)
        AnimatedButton(btn_row, text="Очистить", icon="🗑️",
                       command=self.clear_parsed, bg=Theme.ACCENT_RED,
                       hover_bg="#ff6b63", width=90).pack(side="left", padx=4)

        # Таблица
        table_frame = tk.LabelFrame(pf, text="  Результаты  ", font=Theme.FONT_H2,
                                    bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                    bd=1, relief="solid")
        table_frame.pack(fill="both", expand=True, padx=14, pady=10)
        toolbar = tk.Frame(table_frame, bg=Theme.BG_BASE)
        toolbar.pack(fill="x", pady=4, padx=8)
        tk.Label(toolbar, text="Найдено:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).pack(side="left")
        self.count_label = tk.Label(toolbar, text="0", font=Theme.FONT_H1,
                                    bg=Theme.BG_BASE, fg=Theme.ACCENT_PRIMARY)
        self.count_label.pack(side="left", padx=4)
        tk.Label(toolbar, text="  (Ctrl+F — поиск)", font=Theme.FONT_TINY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_MUTED).pack(side="left")
        AnimatedButton(toolbar, text="Выделить все", icon="☑",
                       command=self.select_all_users, bg=Theme.BG_ELEVATED,
                       hover_bg=Theme.ACCENT_PRIMARY, width=120, height=28).pack(side="right", padx=4)
        AnimatedButton(toolbar, text="Удалить выделенные", icon="✕",
                       command=self.delete_selected, bg=Theme.BG_ELEVATED,
                       hover_bg=Theme.ACCENT_RED, width=160, height=28).pack(side="right", padx=4)

        columns = ("ID", "Username", "Имя", "Фамилия", "Телефон", "Статус", "Last seen")
        self.users_tree = ttk.Treeview(table_frame, columns=columns,
                                        show="headings", height=12)
        col_widths = [90, 130, 120, 120, 110, 100, 130]
        for col, width in zip(columns, col_widths):
            self.users_tree.heading(col, text=col)
            self.users_tree.column(col, width=width)
        v_sb = ttk.Scrollbar(table_frame, orient="vertical", command=self.users_tree.yview)
        h_sb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.users_tree.xview)
        self.users_tree.configure(yscrollcommand=v_sb.set, xscrollcommand=h_sb.set)
        self.users_tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        v_sb.pack(side="right", fill="y", pady=(0, 8))
        h_sb.pack(side="bottom", fill="x", padx=8)

    def update_parser_account_list(self) -> None:
        values = ["auto (первый активный)"]
        for i, info in enumerate(self.loaded_accounts):
            if info.is_connected and info.is_authorized and not info.is_disabled:
                name = info.me_name or info.account.display_name
                values.append(f"[{i}] {info.account.source_format} — {name}")
        self.parser_account_combo["values"] = values

    def _get_parser_client(self) -> Optional[TelegramClient]:
        sel = self.parser_account_var.get()
        if sel and sel != "auto (первый активный)":
            try:
                idx = int(sel.split("]")[0].replace("[", ""))
                if 0 <= idx < len(self.loaded_accounts):
                    info = self.loaded_accounts[idx]
                    if info.is_connected and info.is_authorized:
                        return info.client
            except (ValueError, IndexError):
                pass
        for info in self.loaded_accounts:
            if info.is_connected and info.is_authorized and not info.is_disabled:
                return info.client
        if self.client and self.is_authenticated:
            return self.client
        return None

    # =====================================================================
    # ВКЛАДКА: Инвайт
    # =====================================================================
    def setup_inviter_tab(self, notebook: ttk.Notebook) -> None:
        inv = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(inv, text="  📨  Инвайт  ")

        settings = tk.LabelFrame(inv, text="  Настройки инвайта  ",
                                 font=Theme.FONT_H2, bg=Theme.BG_BASE,
                                 fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        settings.pack(fill="x", padx=14, pady=10)

        tk.Label(settings, text="Целевая группа:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=0, column=0, sticky="w", pady=5, padx=12)
        self.target_group = tk.Entry(settings, width=40, font=Theme.FONT_BODY,
                                      bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                      insertbackground=Theme.ACCENT_PRIMARY,
                                      relief="flat", highlightthickness=2,
                                      highlightbackground=Theme.BORDER,
                                      highlightcolor=Theme.ACCENT_PRIMARY)
        self.target_group.grid(row=0, column=1, pady=5, padx=4, sticky="w")

        # Progress
        self.invite_progress_var = tk.DoubleVar(value=0)
        self.invite_progress = AnimatedProgress(settings, width=600, height=10)
        self.invite_progress.grid(row=1, column=0, columnspan=2, sticky="ew", pady=8, padx=12)

        # Безопасность
        sec = tk.LabelFrame(settings, text="  Безопасность  ", font=Theme.FONT_H2,
                            bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                            bd=1, relief="solid")
        sec.grid(row=2, column=0, columnspan=2, sticky="ew", pady=8, padx=12)

        tk.Label(sec, text="Задержка (сек):", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=0, column=0, padx=4, pady=6)
        self.delay_min = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                   fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                   relief="flat", highlightthickness=2,
                                   highlightbackground=Theme.BORDER,
                                   highlightcolor=Theme.ACCENT_PRIMARY)
        self.delay_min.insert(0, "30")
        self.delay_min.grid(row=0, column=1, padx=4)
        tk.Label(sec, text="—", bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).grid(row=0, column=2)
        self.delay_max = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                   fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                   relief="flat", highlightthickness=2,
                                   highlightbackground=Theme.BORDER,
                                   highlightcolor=Theme.ACCENT_PRIMARY)
        self.delay_max.insert(0, "60")
        self.delay_max.grid(row=0, column=3, padx=4)

        tk.Label(sec, text="Общий лимит:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=0, column=4, padx=(16, 4))
        self.daily_limit = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                     fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                     relief="flat", highlightthickness=2,
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.ACCENT_PRIMARY)
        self.daily_limit.insert(0, "100")
        self.daily_limit.grid(row=0, column=5, padx=4)

        tk.Label(sec, text="Пауза после:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=1, column=0, padx=4, pady=6)
        self.pause_after = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                     fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                     relief="flat", highlightthickness=2,
                                     highlightbackground=Theme.BORDER,
                                     highlightcolor=Theme.ACCENT_PRIMARY)
        self.pause_after.insert(0, "5")
        self.pause_after.grid(row=1, column=1, padx=4, pady=6)
        tk.Label(sec, text="на", bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).grid(row=1, column=2)
        self.pause_time = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                    fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                    relief="flat", highlightthickness=2,
                                    highlightbackground=Theme.BORDER,
                                    highlightcolor=Theme.ACCENT_PRIMARY)
        self.pause_time.insert(0, "60")
        self.pause_time.grid(row=1, column=3, padx=4, pady=6)
        tk.Label(sec, text="сек", bg=Theme.BG_BASE, fg=Theme.TEXT_SECONDARY).grid(row=1, column=4)

        tk.Label(sec, text="На аккаунт:", font=Theme.FONT_BODY,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_PRIMARY).grid(row=2, column=0, padx=4, pady=6)
        self.per_account_limit = tk.Entry(sec, width=6, font=Theme.FONT_BODY, bg=Theme.BG_INPUT,
                                           fg=Theme.TEXT_PRIMARY, insertbackground=Theme.ACCENT_PRIMARY,
                                           relief="flat", highlightthickness=2,
                                           highlightbackground=Theme.BORDER,
                                           highlightcolor=Theme.ACCENT_PRIMARY)
        self.per_account_limit.insert(0, "20")
        self.per_account_limit.grid(row=2, column=1, padx=4, pady=6)
        tk.Label(sec, text="(5 акк × 20 = 100 инвайтов)", font=Theme.FONT_SMALL,
                 bg=Theme.BG_BASE, fg=Theme.TEXT_MUTED).grid(row=2, column=2, columnspan=3, sticky="w")

        self.skip_duplicates_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sec, text="Пропускать участников уже в группе",
                       variable=self.skip_duplicates_var, bg=Theme.BG_BASE,
                       fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT,
                       activebackground=Theme.BG_BASE, activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_SMALL).grid(row=3, column=0, columnspan=5, sticky="w", pady=2)
        self.dry_run_var = tk.BooleanVar(value=False)
        tk.Checkbutton(sec, text="🧪 Сухой прогон (без реальных инвайтов)",
                       variable=self.dry_run_var, bg=Theme.BG_BASE,
                       fg=Theme.TEXT_PRIMARY, selectcolor=Theme.BG_INPUT,
                       activebackground=Theme.BG_BASE, activeforeground=Theme.TEXT_PRIMARY,
                       font=Theme.FONT_SMALL).grid(row=4, column=0, columnspan=5, sticky="w", pady=2)

        # Кнопки управления
        btn = tk.Frame(settings, bg=Theme.BG_BASE)
        btn.grid(row=3, column=0, columnspan=2, pady=12, padx=12)
        self.start_invite_btn = AnimatedButton(btn, text="Начать инвайт", icon="🚀",
                                                command=self.start_inviting,
                                                bg=Theme.ACCENT_GREEN, hover_bg="#5dd674",
                                                width=160)
        self.start_invite_btn.pack(side="left", padx=4)
        self.pause_invite_btn = AnimatedButton(btn, text="Пауза", icon="⏸",
                                                command=self.pause_inviting,
                                                bg=Theme.ACCENT_ORANGE, hover_bg="#ffbd77",
                                                width=100)
        self.pause_invite_btn.pack(side="left", padx=4)
        self.resume_invite_btn = AnimatedButton(btn, text="Продолжить", icon="▶",
                                                 command=self.resume_inviting,
                                                 bg=Theme.ACCENT_BLUE, hover_bg="#7ab8ff",
                                                 width=120)
        self.resume_invite_btn.pack(side="left", padx=4)
        self.stop_invite_btn = AnimatedButton(btn, text="Стоп", icon="🛑",
                                               command=self.stop_inviting,
                                               bg=Theme.ACCENT_RED, hover_bg="#ff6b63",
                                               width=100)
        self.stop_invite_btn.pack(side="left", padx=4)
        AnimatedButton(btn, text="HTML отчёт", icon="📊",
                       command=self.export_html_report, bg=Theme.ACCENT_PRIMARY,
                       hover_bg="#bd8cff", width=120).pack(side="left", padx=4)

        # Статистика
        stats_frame = tk.LabelFrame(inv, text="  📊 Статистика  ", font=Theme.FONT_H2,
                                    bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                    bd=1, relief="solid")
        stats_frame.pack(fill="x", padx=14, pady=6)
        self.stats_text, stats_sb = styled_scrolledtext(stats_frame, height=10)
        self.stats_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        stats_sb.pack(side="right", fill="y", pady=8)
        self.update_stats_display()

        # Лог инвайта
        log_frame = tk.LabelFrame(inv, text="  📝 Лог инвайта  ", font=Theme.FONT_H2,
                                  bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY,
                                  bd=1, relief="solid")
        log_frame.pack(fill="both", expand=True, padx=14, pady=(6, 12))
        self.invite_log, il_sb = styled_scrolledtext(log_frame, height=10,
                                                     font=Theme.FONT_MONO_SMALL)
        self.invite_log.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        il_sb.pack(side="right", fill="y", pady=8)
        for tag, color in {
            "success": Theme.ACCENT_GREEN, "error": Theme.ACCENT_RED,
            "warning": Theme.ACCENT_ORANGE, "info": Theme.TEXT_PRIMARY,
        }.items():
            self.invite_log.tag_config(tag, foreground=color)
        self.invite_log.insert("1.0", "Лог инвайта:\n" + "=" * 50 + "\n")

    # =====================================================================
    # ВКЛАДКА: Управление
    # =====================================================================
    def setup_management_tab(self, notebook: ttk.Notebook) -> None:
        mf = tk.Frame(notebook, bg=Theme.BG_BASE)
        notebook.add(mf, text="  🛠️  Управление  ")

        bl = tk.LabelFrame(mf, text="  ⚫ Чёрный список  ", font=Theme.FONT_H2,
                           bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        bl.pack(fill="both", expand=True, padx=14, pady=10)
        ctrl = tk.Frame(bl, bg=Theme.BG_BASE)
        ctrl.pack(fill="x", padx=12, pady=6)
        tk.Label(ctrl, text="ID:", font=Theme.FONT_BODY, bg=Theme.BG_BASE,
                 fg=Theme.TEXT_PRIMARY).pack(side="left")
        self.blacklist_entry = tk.Entry(ctrl, width=15, font=Theme.FONT_BODY,
                                         bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                         insertbackground=Theme.ACCENT_PRIMARY,
                                         relief="flat", highlightthickness=2,
                                         highlightbackground=Theme.BORDER,
                                         highlightcolor=Theme.ACCENT_PRIMARY)
        self.blacklist_entry.pack(side="left", padx=4)
        AnimatedButton(ctrl, text="Добавить", command=self.add_to_blacklist,
                       bg=Theme.ACCENT_GREEN, hover_bg="#5dd674",
                       width=100, height=28).pack(side="left", padx=4)
        AnimatedButton(ctrl, text="Удалить", command=self.remove_from_blacklist,
                       bg=Theme.ACCENT_ORANGE, hover_bg="#ffbd77",
                       width=100, height=28).pack(side="left", padx=4)
        AnimatedButton(ctrl, text="Очистить", command=self.clear_blacklist,
                       bg=Theme.ACCENT_RED, hover_bg="#ff6b63",
                       width=100, height=28).pack(side="left", padx=4)

        list_frame = tk.Frame(bl, bg=Theme.BG_BASE)
        list_frame.pack(fill="both", expand=True, padx=12, pady=6)
        self.blacklist_listbox = tk.Listbox(list_frame, height=10, font=Theme.FONT_MONO,
                                            bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                                            selectbackground=Theme.ACCENT_PRIMARY,
                                            selectforeground=Theme.TEXT_INVERSE,
                                            highlightthickness=2,
                                            highlightbackground=Theme.BORDER,
                                            highlightcolor=Theme.ACCENT_PRIMARY,
                                            relief="flat", bd=0)
        sb = ttk.Scrollbar(list_frame, orient="vertical",
                            command=self.blacklist_listbox.yview)
        self.blacklist_listbox.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.blacklist_listbox.config(yscrollcommand=sb.set)
        self.update_blacklist_display()

        # Backup
        bk = tk.LabelFrame(mf, text="  💾 Резервное копирование  ", font=Theme.FONT_H2,
                           bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        bk.pack(fill="x", padx=14, pady=6)
        bk_inner = tk.Frame(bk, bg=Theme.BG_BASE)
        bk_inner.pack(fill="x", padx=12, pady=8)
        AnimatedButton(bk_inner, text="Сохранить базу", icon="💾",
                       command=self.backup_data, bg=Theme.ACCENT_BLUE,
                       hover_bg="#7ab8ff", width=180).pack(side="left", padx=4)
        AnimatedButton(bk_inner, text="Восстановить базу", icon="📥",
                       command=self.restore_data, bg=Theme.ACCENT_PRIMARY,
                       hover_bg="#bd8cff", width=180).pack(side="left", padx=4)

        # Системная информация
        info = tk.LabelFrame(mf, text="  ℹ️ Системная информация  ", font=Theme.FONT_H2,
                             bg=Theme.BG_BASE, fg=Theme.ACCENT_SECONDARY, bd=1, relief="solid")
        info.pack(fill="x", padx=14, pady=6)
        self.system_info, si_sb = styled_scrolledtext(info, height=6,
                                                      font=Theme.FONT_MONO_SMALL)
        self.system_info.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        si_sb.pack(side="right", fill="y", pady=8)
        info_text = (
            f"{Theme.APP_NAME} v{Theme.VERSION} (DarkZippa Edition)\n"
            f"✦ crafted by zippa ✦\n\n"
            f"Загрузчик аккаунтов: {'доступен' if _HAS_ACCOUNT_LOADER else 'НЕ ДОСТУПЕН'}\n"
            f"Шифрование: {'включено (Fernet)' if _HAS_CRYPTO else 'ОТКЛЮЧЕНО'}\n"
            f"Папка config: {self.config_manager.config_dir.resolve()}\n"
            f"Папка sessions: {self.session_manager.session_dir.resolve()}\n"
        )
        self.system_info.insert("1.0", info_text)

    # =====================================================================
    # Логирование
    # =====================================================================
    def log_message(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        start_index = self.log_text.index("end-1c linestart")
        self.log_text.insert(tk.END, log_entry)
        end_index = self.log_text.index("end-1c linestart")
        if level in ("info", "success", "warning", "error", "debug"):
            self.log_text.tag_add(level, start_index, end_index)
        self.log_text.see(tk.END)
        getattr(logger, level, logger.info)(message)
        self.status_bar.config(text=message[:100])

    def log_invite(self, message: str, level: str = "info") -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        def _append():
            self.invite_log.insert(tk.END, log_entry)
            start = self.invite_log.index("end-1c linestart")
            end = self.invite_log.index("end-1c linestart")
            if level in ("info", "success", "warning", "error"):
                self.invite_log.tag_add(level, start, end)
            self.invite_log.see(tk.END)
        try:
            self.root.after(0, _append)
        except RuntimeError:
            logger.info(message)

    # =====================================================================
    # Авторизация (ручная)
    # =====================================================================
    def start_auth(self) -> None:
        phone = self.phone_entry.get().strip()
        if not phone or not phone.startswith("+"):
            messagebox.showerror("Ошибка", "Введите номер в формате +7999...")
            return
        if not self.api_id or not self.api_hash:
            messagebox.showerror("Ошибка", "Сначала настройте API!")
            return
        self.proxy = self.proxy_entry.get().strip() or None
        self.auth_phone = phone
        self.log_message(f"🔐 Авторизация для {phone}...")
        self.phone_entry.config(state="disabled")
        threading.Thread(target=self._auth_thread, daemon=True).start()

    def _auth_thread(self) -> None:
        try:
            result = self._run_coroutine(self._auth_coroutine())
            if result == "code_sent":
                self.root.after(0, lambda: self._enable_code_button())
            elif result == "authenticated":
                self.root.after(0, self._auth_success)
            elif result == "password_needed":
                self.root.after(0, self._ask_password)
        except Exception as e:
            self.root.after(0, lambda: self._auth_error(str(e)))

    def _build_proxy(self) -> Optional[tuple]:
        if not self.proxy:
            return None
        try:
            import socks
        except ImportError:
            return None
        from urllib.parse import urlparse
        u = urlparse(self.proxy)
        scheme = (u.scheme or "socks5").lower()
        type_map = {"socks5": socks.SOCKS5, "socks4": socks.SOCKS4, "http": socks.HTTP}
        if scheme not in type_map:
            return None
        return (type_map[scheme], u.hostname, u.port or 1080, True, u.username, u.password)

    async def _auth_coroutine(self) -> str:
        try:
            session_path = self.session_manager.get_session_path(self.auth_phone)
            if self.client and self.client.is_connected():
                await self.client.disconnect()
            kwargs = dict(
                session=session_path, api_id=int(self.api_id), api_hash=self.api_hash,
                device_model="Desktop", system_version="Windows 10",
                app_version=self.VERSION, lang_code="ru", system_lang_code="ru",
                connection_retries=5, retry_delay=2, request_retries=5, timeout=30,
            )
            proxy = self._build_proxy()
            if proxy:
                kwargs["proxy"] = proxy
            self.client = TelegramClient(**kwargs)
            await self.client.connect()
            if await self.client.is_user_authorized():
                self.is_authenticated = True
                me = await self.client.get_me()
                info = (f"✅ Авторизован!\n\n"
                        f"👤 {me.first_name or ''} {me.last_name or ''}\n"
                        f"📱 +{me.phone or 'Скрыт'}\n"
                        f"🔗 @{me.username or 'Нет'}\n🆔 {me.id}\n")
                self.root.after(0, lambda: self._update_session_info(info))
                return "authenticated"
            await self.client.send_code_request(self.auth_phone)
            return "code_sent"
        except SessionPasswordNeededError:
            return "password_needed"
        except ApiIdInvalidError:
            raise Exception("Неверный API ID или Hash")
        except AuthKeyDuplicatedError:
            raise Exception("Сессия используется в другом месте")
        except Exception as e:
            raise e

    def _update_session_info(self, text: str) -> None:
        self.session_info.delete(1.0, tk.END)
        self.session_info.insert(1.0, text)

    def _enable_code_button(self) -> None:
        self.code_btn.configure(state="normal")
        self.log_message("📱 Код отправлен!", "success")
        Toast.show(self.root, "Код отправлен", "Введите код из Telegram", "info")

    def _auth_success(self) -> None:
        self.is_authenticated = True
        self.auth_status.config(text="✅ Авторизован", fg=Theme.ACCENT_GREEN)
        self.phone_entry.config(state="normal")
        self.code_btn.configure(state="disabled")
        if self.auth_phone:
            self.config_manager.save_config(self.api_id, self.api_hash, self.auth_phone)
        self.log_message("✅ Авторизация успешна!", "success")
        Toast.show(self.root, "Авторизация успешна", level="success")

    def _ask_password(self) -> None:
        password = simpledialog.askstring("2FA", "Пароль:", show="*")
        if password:
            threading.Thread(target=self._verify_password_thread,
                             args=(password,), daemon=True).start()
        else:
            self.phone_entry.config(state="normal")

    def _verify_password_thread(self, password: str) -> None:
        try:
            result = self._run_coroutine(self._verify_password_coroutine(password))
            if result:
                self.root.after(0, self._auth_success)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Неверный пароль!"))
                self.root.after(0, lambda: self.phone_entry.config(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self._auth_error(str(e)))

    async def _verify_password_coroutine(self, password: str) -> bool:
        await self.client.sign_in(password=password)
        return await self.client.is_user_authorized()

    def _auth_error(self, error_msg: str) -> None:
        self.auth_status.config(text="❌ Ошибка", fg=Theme.ACCENT_RED)
        self.phone_entry.config(state="normal")
        self.code_btn.configure(state="disabled")
        if "FloodWait" in error_msg:
            error_msg = "Слишком много попыток. Подождите."
        messagebox.showerror("Ошибка", error_msg)
        self.log_message(f"❌ {error_msg}", "error")

    def enter_code(self) -> None:
        if not self.client:
            messagebox.showwarning("Внимание", "Сначала нажмите 'Авторизоваться'")
            return
        code = simpledialog.askstring("Код", "Введите код:", show="*")
        if not code:
            self.phone_entry.config(state="normal")
            return
        if not code.isdigit() or len(code) < 4 or len(code) > 8:
            messagebox.showerror("Ошибка", "Код: 4-8 цифр!")
            return
        self.code_btn.configure(state="disabled")
        threading.Thread(target=self._verify_code_thread, args=(code,), daemon=True).start()

    def _verify_code_thread(self, code: str) -> None:
        try:
            result = self._run_coroutine(self._verify_code_coroutine(code))
            if result:
                self.is_authenticated = True
                self.root.after(0, self._auth_success)
            else:
                self.root.after(0, lambda: messagebox.showerror("Ошибка", "Неверный код"))
                self.root.after(0, lambda: self.code_btn.configure(state="normal"))
                self.root.after(0, lambda: self.phone_entry.config(state="normal"))
        except PhoneCodeInvalidError:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", "Неверный код!"))
            self.root.after(0, lambda: self.code_btn.configure(state="normal"))
            self.root.after(0, lambda: self.phone_entry.config(state="normal"))
        except PhoneCodeExpiredError:
            self.root.after(0, lambda: messagebox.showerror("Ошибка", "Код истёк!"))
            self.root.after(0, lambda: self.code_btn.configure(state="normal"))
            self.root.after(0, lambda: self.phone_entry.config(state="normal"))
        except Exception as e:
            self.root.after(0, lambda: self._auth_error(str(e)))

    async def _verify_code_coroutine(self, code: str) -> bool:
        await self.client.sign_in(self.auth_phone, code)
        return await self.client.is_user_authorized()

    def show_sessions(self) -> None:
        sessions = self.session_manager.list_sessions()
        if not sessions:
            messagebox.showinfo("Сессии", "Нет сохранённых сессий")
            return
        text = "Сессии:\n\n"
        for i, s in enumerate(sessions[:20], 1):
            label = self.session_phone_map.get(s["id"], "—")
            text += f"{i}. {label}  ({s['modified']}, {s['size']} б)\n"
        messagebox.showinfo("Сессии", text)

    def clear_sessions(self) -> None:
        if messagebox.askyesno("Очистка", "Удалить все сессии?"):
            count = self.session_manager.clear_all()
            self.session_phone_map.clear()
            self._save_state()
            self.log_message(f"✅ Удалено: {count}", "success")
            self.is_authenticated = False
            self.auth_status.config(text="❌ Не авторизован", fg=Theme.ACCENT_RED)

    # =====================================================================
    # Парсинг
    # =====================================================================
    def start_parsing(self) -> None:
        client = self._get_parser_client()
        if not client:
            messagebox.showerror("Ошибка",
                "Нет активного клиента! Загрузите аккаунты или авторизуйтесь.")
            return
        group_link = self.group_link.get().strip()
        if not group_link:
            messagebox.showerror("Ошибка", "Введите ссылку!")
            return
        try:
            limit = int(self.limit_entry.get())
            if limit <= 0 or limit > 10000:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Ошибка", "Лимит 1..10000!")
            return
        self.log_message(f"🔍 Парсинг: {group_link}", "info")
        self.progress.set_value(0)
        self.progress_label.config(text="Подготовка...")
        self._start_autosave()  # [NEW]
        threading.Thread(target=self._parse_thread, daemon=True).start()

    def _start_autosave(self) -> None:
        """Автосохранение во время парсинга каждые 30 сек.  [NEW]"""
        if self._autosave_job:
            self.root.after_cancel(self._autosave_job)
        def _autosave():
            if self.parsed_users:
                self._save_autosave()
            self._autosave_job = self.root.after(30000, _autosave)
        self._autosave_job = self.root.after(30000, _autosave)

    def _save_autosave(self) -> None:
        """Сохранить промежуточный результат парсинга.  [NEW]"""
        try:
            autosave_file = Path("backups") / "autosave.json"
            autosave_file.parent.mkdir(exist_ok=True)
            data = {
                "parsed_users": [asdict(u) for u in self.parsed_users],
                "timestamp": datetime.now().isoformat(),
                "group": self.group_link.get().strip(),
            }
            with open(autosave_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"Autosave error: {e}")

    def _parse_thread(self) -> None:
        try:
            users = self._run_coroutine(self._parse_coroutine())
            if users is not None:
                self.parsed_users = users
                self.root.after(0, self._update_users_table)
                self._safe_log(f"✅ Найдено: {len(users)} пользователей", "success")
                Toast.show(self.root, "Парсинг завершён",
                           f"Найдено: {len(users)}", "success")
                self._add_recent_group(self.group_link.get().strip())
                self._save_autosave()
            else:
                self._safe_log("❌ Парсинг не удался", "error")
        except Exception as e:
            self._safe_log(f"❌ Ошибка: {e}", "error")
        finally:
            if self._autosave_job:
                self.root.after_cancel(self._autosave_job)
                self._autosave_job = None
            self.root.after(0, lambda: self.progress.set_value(0))
            self.root.after(0, lambda: self.progress_label.config(text=""))

    async def _parse_coroutine(self) -> List[UserData]:
        group_link = self.group_link.get().strip()
        method = self.parser_method.get()
        limit = int(self.limit_entry.get())
        client = self._get_parser_client()
        if not client:
            return []
        try:
            self._safe_log("🔄 Получаю группу...", "info")
            group = await client.get_entity(group_link)
            title = getattr(group, "title", "Unknown")
            self._safe_log(f"✅ Группа: {title}", "success")
            users: List[UserData] = []
            if method == "participants":
                users = await self._parse_participants_safe(client, group, limit)
            elif method == "messages":
                users = await self._parse_from_messages_safe(client, group, limit)
            elif method == "quick":
                users = await self._parse_quick(client, group, limit)
            return users
        except ChannelPrivateError:
            self._safe_log("❌ Группа приватная", "error")
            return []
        except Exception as e:
            self._safe_log(f"❌ {e}", "error")
            return []

    async def _parse_participants_safe(self, client, group, limit):
        users = []
        try:
            self._safe_log("👥 Парсю участников...", "info")
            aggressive = self.aggressive_var.get()
            count = 0
            async for user in client.iter_participants(group, limit=limit, aggressive=aggressive):
                if not self._is_valid_user(user):
                    continue
                users.append(self._create_user_data(user))
                count += 1
                if count % 20 == 0:
                    pct = min(100, count / limit * 100) if limit else 0
                    self.root.after(0, lambda p=pct, c=count: (
                        self.progress.set_value(p),
                        self.progress_label.config(text=f"Обработано: {c}"),
                    ))
            self._safe_log(f"✅ Найдено: {len(users)}", "success")
            return users
        except Exception as e:
            self._safe_log(f"⚠️ {e}", "warning")
            return []

    async def _parse_from_messages_safe(self, client, group, limit):
        users = []
        user_ids: Set[int] = set()
        try:
            self._safe_log("📝 Парсю из сообщений...", "info")
            async for msg in client.iter_messages(group, limit=min(limit * 5, 5000)):
                if msg.sender_id and msg.sender_id not in user_ids:
                    try:
                        user = await client.get_entity(msg.sender_id)
                        if self._is_valid_user(user):
                            user_ids.add(user.id)
                            users.append(self._create_user_data(user))
                    except Exception:
                        continue
            self._safe_log(f"✅ Найдено: {len(users)}", "success")
            return users
        except Exception as e:
            self._safe_log(f"⚠️ {e}", "warning")
            return []

    async def _parse_quick(self, client, group, limit):
        users = []
        try:
            self._safe_log("⚡ Быстрый парсинг...", "info")
            participants = await client.get_participants(group, limit=min(limit, 200))
            for user in participants:
                if self._is_valid_user(user):
                    users.append(self._create_user_data(user))
            self._safe_log(f"✅ Найдено: {len(users)}", "success")
            return users
        except Exception as e:
            self._safe_log(f"⚠️ {e}", "warning")
            return []

    def _is_valid_user(self, user) -> bool:
        if not isinstance(user, User):
            return False
        if self.filter_bots.get() and user.bot:
            return False
        if self.filter_deleted.get() and user.deleted:
            return False
        if self.filter_no_username.get() and not user.username:
            return False
        try:
            days_str = self.filter_inactive_days.get()
            days = int(days_str) if days_str else 0
        except (tk.TclError, ValueError):
            days = 0
        if days > 0:
            status = getattr(user, "status", None)
            if status is None:
                return False
            was_online = getattr(status, "was_online", None)
            if was_online is None:
                return False
            delta = datetime.now(tz=was_online.tzinfo) - was_online
            if delta.days > days:
                return False
        return True

    def _create_user_data(self, user) -> UserData:
        last_seen_str = None
        status = getattr(user, "status", None)
        was_online = getattr(status, "was_online", None) if status else None
        if was_online:
            last_seen_str = was_online.strftime("%Y-%m-%d %H:%M:%S")
        # [NEW] Сохраняем access_hash — критично для инвайта по user_id
        # Без access_hash Telethon не может создать InputEntity -> "Could not find the input entity"
        access_hash = getattr(user, "access_hash", None)
        return UserData(
            id=user.id, username=user.username or "",
            first_name=user.first_name or "", last_name=user.last_name or "",
            phone=getattr(user, "phone", "") or "",
            status="Готов", last_seen=last_seen_str,
            is_bot=bool(user.bot),
            access_hash=int(access_hash) if access_hash else None,
        )

    def _update_users_table(self) -> None:
        for item in self.users_tree.get_children():
            self.users_tree.delete(item)
        for user in self.parsed_users:
            self.users_tree.insert(
                "", "end", iid=str(user.id),
                values=(user.id, user.username or "—",
                        user.first_name, user.last_name,
                        user.phone or "Скрыт",
                        user.status, user.last_seen or "—"),
            )
        self.count_label.config(text=str(len(self.parsed_users)))

    def select_all_users(self) -> None:
        self.users_tree.selection_set(self.users_tree.get_children())

    def delete_selected(self) -> None:
        selected = self.users_tree.selection()
        if not selected:
            return
        ids_to_remove = {int(sid) for sid in selected}
        self.parsed_users = [u for u in self.parsed_users if u.id not in ids_to_remove]
        self._update_users_table()

    def analyze_users(self) -> None:
        if not self.parsed_users:
            messagebox.showwarning("Внимание", "Нет данных!")
            return
        total = len(self.parsed_users)
        with_username = sum(1 for u in self.parsed_users if u.username)
        with_phone = sum(1 for u in self.parsed_users if u.phone)
        with_name = sum(1 for u in self.parsed_users if u.first_name)
        bots = sum(1 for u in self.parsed_users if u.is_bot)
        with_last_seen = sum(1 for u in self.parsed_users if u.last_seen)
        analysis = (
            f"📊 Анализ:\n\n"
            f"👥 Всего: {total}\n"
            f"🔗 С @username: {with_username} ({with_username/total*100:.1f}%)\n"
            f"📞 С телефоном: {with_phone} ({with_phone/total*100:.1f}%)\n"
            f"👤 С именем: {with_name} ({with_name/total*100:.1f}%)\n"
            f"🤖 Ботов: {bots}\n"
            f"🕐 С last_seen: {with_last_seen} ({with_last_seen/total*100:.1f}%)"
        )
        messagebox.showinfo("Анализ", analysis)

    def clear_parsed(self) -> None:
        if not self.parsed_users:
            return
        if messagebox.askyesno("Очистка", "Очистить список?"):
            self.parsed_users = []
            self._update_users_table()
            self.log_message("🗑️ Список очищен", "info")

    def save_to_csv(self) -> None:
        if not self.parsed_users:
            messagebox.showwarning("Внимание", "Нет данных!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(f, fieldnames=["id", "username", "first_name",
                                                        "last_name", "phone", "status", "last_seen"])
                writer.writeheader()
                for u in self.parsed_users:
                    writer.writerow(u.to_csv_row())
            self.log_message(f"💾 Сохранено: {filename}", "success")
            Toast.show(self.root, "CSV сохранён", filename, "success")
        except Exception as e:
            self.log_message(f"❌ {e}", "error")

    def save_to_json(self) -> None:
        if not self.parsed_users:
            messagebox.showwarning("Внимание", "Нет данных!")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not filename:
            return
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump([asdict(u) for u in self.parsed_users], f,
                          ensure_ascii=False, indent=2)
            self.log_message(f"💾 Сохранено: {filename}", "success")
            Toast.show(self.root, "JSON сохранён", level="success")
        except Exception as e:
            self.log_message(f"❌ {e}", "error")

    def import_csv(self) -> None:
        filename = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not filename:
            return
        try:
            imported = []
            with open(filename, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # access_hash — опциональное поле (для обратной совместимости со старыми CSV)
                    access_hash_str = row.get("access_hash", "").strip()
                    try:
                        access_hash = int(access_hash_str) if access_hash_str else None
                    except ValueError:
                        access_hash = None
                    imported.append(UserData(
                        id=int(row["id"]),
                        username=row.get("username", ""),
                        first_name=row.get("first_name", ""),
                        last_name=row.get("last_name", ""),
                        phone=row.get("phone", ""),
                        status=row.get("status", "Готов"),
                        last_seen=row.get("last_seen") or None,
                        access_hash=access_hash,
                    ))
            self.parsed_users = imported
            self._update_users_table()
            self.log_message(f"📥 Импортировано: {len(imported)}", "success")
        except Exception as e:
            self.log_message(f"❌ {e}", "error")

    # =====================================================================
    # ИНВАЙТ (с ротацией аккаунтов)
    # =====================================================================
    def _validate_invite_settings(self) -> bool:
        fields = {
            "Мин. задержка": (self.delay_min.get(), 1, 3600),
            "Макс. задержка": (self.delay_max.get(), 1, 7200),
            "Общий лимит": (self.daily_limit.get(), 1, 10000),
            "Пауза после": (self.pause_after.get(), 1, 1000),
            "Время паузы": (self.pause_time.get(), 1, 7200),
            "Лимит на аккаунт": (self.per_account_limit.get(), 1, 200),
        }
        for name, (val, lo, hi) in fields.items():
            try:
                v = int(val)
                if not (lo <= v <= hi):
                    raise ValueError()
            except ValueError:
                messagebox.showerror("Ошибка", f"'{name}' должно быть {lo}..{hi}!")
                return False
        if int(self.delay_min.get()) > int(self.delay_max.get()):
            messagebox.showerror("Ошибка", "Мин ≥ Макс задержки!")
            return False
        return True

    def start_inviting(self) -> None:
        if self.account_rotation_enabled.get():
            available = self.get_available_accounts_for_invite()
            if not available:
                messagebox.showerror("Ошибка",
                    "Нет активных аккаунтов! Загрузите и подключите.")
                return
        else:
            if not (self.is_authenticated or any(
                a.is_connected and a.is_authorized for a in self.loaded_accounts
            )):
                messagebox.showerror("Ошибка", "Нет авторизованного аккаунта!")
                return
        if not self.parsed_users:
            messagebox.showwarning("Внимание", "Сначала выполните парсинг!")
            return
        target_group = self.target_group.get().strip()
        if not target_group:
            messagebox.showerror("Ошибка", "Введите целевую группу!")
            return
        if not self._validate_invite_settings():
            return

        self.dry_run = self.dry_run_var.get()
        self.rate_limiter.delay_min = int(self.delay_min.get())
        self.rate_limiter.delay_max = int(self.delay_max.get())
        self.rate_limiter.daily_limit = int(self.daily_limit.get())
        self.rate_limiter.pause_after = int(self.pause_after.get())
        self.rate_limiter.pause_time = int(self.pause_time.get())
        self.rate_limiter.per_account_limit = int(self.per_account_limit.get())

        n_accounts = len(self.get_available_accounts_for_invite()) if self.account_rotation_enabled.get() else 1
        if not messagebox.askyesno("Подтверждение",
                f"Начать инвайт {len(self.parsed_users)} пользователей?\n\n"
                f"Группа: {target_group}\n"
                f"Аккаунтов: {n_accounts}\n"
                f"Лимит/аккаунт: {self.rate_limiter.per_account_limit}\n"
                f"Общий лимит: {self.rate_limiter.daily_limit}\n"
                + ("🧪 СУХОЙ ПРОГОН\n" if self.dry_run else "")):
            return

        self._add_recent_group(target_group)
        self.stats = InviteStats(start_time=datetime.now())
        for info in self.loaded_accounts:
            info.invited_count = 0
            info.failed_count = 0

        self.inviting_active = True
        self.invite_stop.clear()
        self.invite_paused.set()
        self.start_invite_btn.configure(state="disabled")
        self.pause_invite_btn.configure(state="normal")
        self.stop_invite_btn.configure(state="normal")

        self.log_message(f"🚀 Инвайт в: {target_group}", "info")
        self.log_invite("=" * 50, "info")
        self.log_invite(f"НАЧАЛО: {datetime.now().strftime('%H:%M:%S')}", "info")
        self.log_invite(f"Группа: {target_group}", "info")
        self.log_invite(f"Аккаунтов: {n_accounts}", "info")
        if self.dry_run:
            self.log_invite("🧪 СУХОЙ ПРОГОН", "warning")
        self.log_invite("=" * 50, "info")

        # [NEW] Сохраняем состояние для resume
        self._save_invite_state(target_group)

        threading.Thread(target=self._invite_thread, daemon=True).start()

    def _save_invite_state(self, target_group: str) -> None:
        """Сохранить состояние инвайта для resume.  [NEW]"""
        try:
            state = {
                "target_group": target_group,
                "users": [{"id": u.id, "status": u.status} for u in self.parsed_users],
                "timestamp": datetime.now().isoformat(),
                "dry_run": self.dry_run,
            }
            with open(Path("backups") / "invite_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_invite_state(self) -> None:
        """Загрузить состояние для resume.  [NEW]"""
        try:
            state_file = Path("backups") / "invite_state.json"
            if state_file.exists():
                with open(state_file, "r", encoding="utf-8") as f:
                    self.last_invite_state = json.load(f)
        except Exception:
            self.last_invite_state = {}

    def _invite_thread(self) -> None:
        try:
            self._run_coroutine(self._invite_users_safe(), timeout=86400)
        except Exception as e:
            self._safe_log(f"❌ Критическая: {e}", "error")
        finally:
            self.root.after(0, self._invite_finished)

    async def _invite_users_safe(self) -> None:
        target_group = self.target_group.get().strip()

        if self.account_rotation_enabled.get():
            accounts_pool = self.get_available_accounts_for_invite()
        else:
            accounts_pool = []
            for info in self.loaded_accounts:
                if info.is_connected and info.is_authorized and not info.is_disabled:
                    accounts_pool = [info]
                    break
            if not accounts_pool and self.client and self.is_authenticated:
                # Для ручной авторизации создаём временный AccountRuntimeInfo
                # с Already-Connected клиентом (StringSession не нужна)
                tmp = AccountRuntimeInfo(account=LoadedAccount(
                    auth_key=bytes(random.randint(1, 255) for _ in range(256)),
                    dc_id=2,
                    source_format="manual",
                    telethon_string="",  # не используем — клиент уже подключён
                ))
                tmp.client = self.client
                tmp.is_connected = True
                tmp.is_authorized = True
                tmp.me_name = "Ручная авторизация"
                accounts_pool = [tmp]

        if not accounts_pool:
            self.log_invite("❌ Нет активных аккаунтов!", "error")
            return

        primary = accounts_pool[0]
        try:
            group = await primary.client.get_entity(target_group)
            title = getattr(group, "title", "Unknown")
            self.log_invite(f"🎯 Группа: {title}", "info")
        except Exception as e:
            self.log_invite(f"❌ Не удалось получить группу: {e}", "error")
            return

        # [NEW] Определяем тип группы и подготавливаем нужный Input-объект
        # Возможные типы:
        #   - Channel (megagroup=True) → супергруппа → InputChannel + InviteToChannelRequest
        #   - Channel (broadcast=True) → канал → инвайт запрещён
        #   - Chat (legacy)            → обычная группа → InputPeerChat + AddChatUserRequest
        #   - ChatForbidden            → нет доступа
        #   - ChannelForbidden         → нет доступа
        from telethon.tl.types import (
            Channel as TlChannel,
            Chat as TlChat,
            ChatForbidden as TlChatForbidden,
            ChannelForbidden as TlChannelForbidden,
            InputChannel as TlInputChannel,
            InputPeerChannel as TlInputPeerChannel,
            InputPeerChat as TlInputPeerChat,
        )

        # Сбрасываем состояние (могло остаться от предыдущего инвайта)
        self._invite_target_type = None
        self._invite_input_channel = None
        self._invite_chat_id = None

        try:
            input_entity = await primary.client.get_input_entity(group)
        except Exception as e:
            self.log_invite(f"❌ Не удалось получить input entity: {e}", "error")
            return

        # Логируем тип для отладки
        group_type_name = type(group).__name__
        input_type_name = type(input_entity).__name__
        self.log_invite(f"ℹ️ Тип группы: {group_type_name}, input: {input_type_name}", "info")

        # Анализируем тип группы
        if isinstance(group, TlChannelForbidden):
            self.log_invite("❌ Это ChannelForbidden — нет доступа к группе", "error")
            return
        if isinstance(group, TlChatForbidden):
            self.log_invite("❌ Это ChatForbidden — нет доступа к чату", "error")
            return

        if isinstance(group, TlChannel):
            # Это супергруппа или канал
            is_megagroup = getattr(group, "megagroup", False)
            is_broadcast = getattr(group, "broadcast", False)
            if is_broadcast and not is_megagroup:
                self.log_invite(
                    "🛑 Это broadcast-канал! Инвайт в каналы запрещён (только админы могут добавлять).",
                    "error",
                )
                self.invite_stop.set()
                return
            # Получаем InputChannel
            if isinstance(input_entity, TlInputPeerChannel):
                self._invite_input_channel = TlInputChannel(
                    channel_id=input_entity.channel_id,
                    access_hash=input_entity.access_hash,
                )
            elif isinstance(input_entity, TlInputChannel):
                self._invite_input_channel = input_entity
            else:
                # Попытка через group.id + access_hash
                access_hash = getattr(group, "access_hash", None)
                if access_hash:
                    self._invite_input_channel = TlInputChannel(
                        channel_id=group.id,
                        access_hash=access_hash,
                    )
                else:
                    self.log_invite(
                        f"❌ Не удалось получить access_hash для канала (input: {input_type_name})",
                        "error",
                    )
                    return
            self._invite_target_type = "channel"
            self.log_invite(
                f"✅ Супergroup (id={self._invite_input_channel.channel_id})",
                "success",
            )

        elif isinstance(group, TlChat):
            # Это обычный чат (legacy) — нужен AddChatUserRequest
            self._invite_chat_id = group.id
            self._invite_target_type = "chat"
            self.log_invite(
                f"ℹ️ Это обычный чат (chat_id={group.id}). "
                f"Будет использован AddChatUserRequest вместо InviteToChannelRequest.",
                "info",
            )
            # Если чат мигрирован в супергруппу — лучше использовать её
            migrated_to = getattr(group, "migrated_to", None)
            if migrated_to:
                self.log_invite(
                    f"⚠️ Чат мигрировал в супергруппу. Попробуйте ссылку на новую супергруппу.",
                    "warning",
                )
        else:
            self.log_invite(
                f"❌ Неизвестный тип группы: {group_type_name}",
                "error",
            )
            return

        # [NEW] Проверка прав аккаунта
        await self._check_group_permissions(primary.client, group, primary)

        if self.invite_stop.is_set():
            return

        if self.skip_duplicates_var.get() and not self.dry_run:
            self.log_invite("🔄 Загружаю участников группы...", "info")
            try:
                self.target_members = {u.id async for u in primary.client.iter_participants(group)}
                self.log_invite(f"✅ В группе: {len(self.target_members)} участников", "info")
            except Exception as e:
                self.log_invite(f"⚠️ Не удалось загрузить: {e}", "warning")
                self.target_members = set()
        else:
            self.target_members = set()

        total = len(self.parsed_users)
        consecutive_errors = 0
        MAX_ERRORS = 5
        current_idx = 0

        for i, user in enumerate(self.parsed_users):
            if self.invite_stop.is_set():
                self.log_invite("🛑 Остановлено", "warning")
                break
            while self.inviting_active and not self.invite_paused.is_set():
                self.log_invite("⏸️ На паузе", "warning")
                await asyncio.sleep(2)
                if self.invite_stop.is_set():
                    break
            if self.invite_stop.is_set():
                break
            if not self.inviting_active:
                break

            total_attempts = self.stats.successful + self.stats.failed
            if total_attempts >= self.rate_limiter.daily_limit:
                self.log_invite("⚠️ Достигнут дневной лимит!", "warning")
                break

            if str(user.id) in self.blacklist:
                self.stats.skipped += 1
                self.log_invite(f"⏭️ Blacklist: {user.username or user.id}", "info")
                continue
            if user.id in self.target_members:
                self.stats.skipped += 1
                self.log_invite(f"⏭️ Уже в группе: {user.username or user.id}", "info")
                continue
            if user.status in ("✅ Приглашён", "❌ Ошибка", "❌ Невалидный", "🧪 Dry-run"):
                # Пропускаем уже обработанных пользователей (включая невалидных)
                continue

            # Выбор аккаунта
            if self.account_rotation_enabled.get():
                info = None
                for _ in range(len(self.loaded_accounts)):
                    if current_idx >= len(self.loaded_accounts):
                        current_idx = 0
                    candidate = self.loaded_accounts[current_idx]
                    current_idx += 1
                    if (candidate.is_connected and candidate.is_authorized
                        and not candidate.is_disabled
                        and not (candidate.flood_until and datetime.now() < candidate.flood_until)
                        and candidate.invited_count < self.rate_limiter.per_account_limit):
                        info = candidate
                        break
                if not info:
                    self.log_invite("⚠️ Все аккаунты исчерпаны/в FloodWait", "warning")
                    break
            else:
                info = accounts_pool[0]

            client = info.client
            label = info.me_name or info.account.display_name
            user_info = f"{user.username or user.id} ({user.first_name} {user.last_name})".strip()
            self.log_invite(f"🔄 [{label}] → {user_info}", "info")

            if self.dry_run:
                self.stats.successful += 1
                info.invited_count += 1
                user.status = "🧪 Dry-run"
                self.log_invite(f"🧪 DRY-RUN: {user_info}", "info")
                await self._update_progress(i + 1, total)
                self.root.after(0, self.refresh_accounts_table)
                continue

            try:
                # [NEW] Создаём InputUser напрямую с access_hash
                # Это решает ошибку "Could not find the input entity for PeerUser"
                user_entity = await self._get_input_user(client, user)
                if user_entity is None:
                    self._handle_invite_error(
                        user, info, "Нет access_hash",
                        "пользователь не в кэше — пропустите или пригласите по @username"
                    )
                    consecutive_errors += 1
                    # Не считаем как критическую ошибку для автоостановки
                    consecutive_errors = max(0, consecutive_errors - 1)
                    continue

                # [NEW] Получаем InputChannel для ЭТОГО аккаунта
                # access_hash канала тоже сессионный — для каждого аккаунта свой
                input_channel_for_account = await self._get_input_channel_for_account(
                    client, info, target_group
                )
                if input_channel_for_account is None and self._invite_target_type == "channel":
                    self._handle_invite_error(
                        user, info, "Нет канала",
                        f"не удалось получить InputChannel для аккаунта"
                    )
                    consecutive_errors += 1
                    continue

                # [NEW] Выбираем метод в зависимости от типа группы
                if self._invite_target_type == "channel" and input_channel_for_account:
                    # Супергруппа — InviteToChannelRequest
                    await client(InviteToChannelRequest(
                        channel=input_channel_for_account,
                        users=[user_entity],
                    ))
                elif self._invite_target_type == "chat" and self._invite_chat_id:
                    # Обычный чат (legacy) — AddChatUserRequest
                    from telethon.tl.functions.messages import AddChatUserRequest
                    await client(AddChatUserRequest(
                        chat_id=self._invite_chat_id,
                        user_id=user_entity,
                        fwd_limit=0,
                    ))
                else:
                    self._handle_invite_error(
                        user, info, "Нет цели",
                        f"не определён тип целевой группы (type={self._invite_target_type})"
                    )
                    consecutive_errors += 1
                    continue

                self.stats.successful += 1
                info.invited_count += 1
                user.status = "✅ Приглашён"
                self.rate_limiter.record(True)
                self.log_invite(f"✅ УСПЕХ [{label}]: {user_info}", "success")
                consecutive_errors = 0
            except FloodWaitError as e:
                wait_time = max(1, e.seconds)
                info.flood_until = datetime.now() + timedelta(seconds=wait_time)
                info.failed_count += 1
                self.stats.errors["FloodWait"] = self.stats.errors.get("FloodWait", 0) + 1
                self.log_invite(f"⏳ FloodWait [{label}]: {wait_time}с", "warning")
                self.root.after(0, self.refresh_accounts_table)
                continue
            except UserPrivacyRestrictedError:
                self._handle_invite_error(user, info, "Приватность", "ограничил приглашения")
                consecutive_errors += 1
            except UserAlreadyParticipantError:
                self._handle_invite_error(user, info, "Уже в группе", "уже участник")
                self.target_members.add(user.id)
                consecutive_errors += 1
            except UserNotParticipantError:
                self._handle_invite_error(user, info, "Не найден", "не найден")
                consecutive_errors += 1
            except UserBotError:
                self._handle_invite_error(user, info, "Бот", "нельзя пригласить бота")
                consecutive_errors += 1
            except PeerFloodError:
                self._handle_invite_error(user, info, "PeerFlood", "ограничен")
                info.flood_until = datetime.now() + timedelta(hours=24)
                self.log_invite(f"🛑 [{label}] PeerFlood — откл. на 24ч", "error")
                self.root.after(0, self.refresh_accounts_table)
                consecutive_errors += 1
            except AuthKeyUnregisteredError:
                self._handle_invite_error(user, info, "AuthKey", "отозвана")
                info.is_authorized = False
                self.root.after(0, self.refresh_accounts_table)
            except ChatWriteForbiddenError:
                # "You can't write in this chat" — аккаунт не админ / это канал
                self._handle_invite_error(
                    user, info, "Нет прав",
                    "у аккаунта нет прав приглашать в эту группу"
                )
                self.log_invite(
                    f"🛑 [{label}] Нет прав на инвайт! Проверьте, что аккаунт — админ "
                    f"с правом 'Добавление пользователей'",
                    "error",
                )
                consecutive_errors += 1
            except ChatAdminInviteRequiredError:
                self._handle_invite_error(
                    user, info, "Нужен админ",
                    "в этой группе инвайт только для админов"
                )
                consecutive_errors += 1
            except BroadcastForbiddenError:
                self._handle_invite_error(
                    user, info, "Это канал",
                    "это broadcast-канал — в каналах инвайт запрещён"
                )
                self.log_invite(
                    f"🛑 Целевая группа — broadcast-канал! Инвайт невозможен. "
                    f"Используйте супергруппу.",
                    "error",
                )
                # Останавливаем — нет смысла продолжать
                self.invite_stop.set()
                break
            except Exception as e:
                err_str = str(e)
                err_lower = err_str.lower()
                # Обрабатываем "You can't write in this chat" как ChatWriteForbidden
                if "can't write in this chat" in err_lower:
                    self._handle_invite_error(
                        user, info, "Нет прав", "у аккаунта нет прав приглашать"
                    )
                    consecutive_errors += 1
                # [NEW] "Invalid channel object" — access_hash канала невалиден для этого аккаунта
                elif "invalid channel object" in err_lower:
                    self._handle_invite_error(
                        user, info, "Invalid channel",
                        "access_hash канала невалиден для этого аккаунта"
                    )
                    # Сбрасываем кэш InputChannel для этого аккаунта
                    if hasattr(info, "_input_channel_cache"):
                        info._input_channel_cache = None
                    consecutive_errors += 1
                # "Invalid user object" / "Invalid object ID for a user"
                elif ("invalid user object" in err_lower
                      or "invalid object id for a user" in err_lower):
                    self._handle_invite_error(
                        user, info, "Invalid user ID",
                        "невалидный access_hash — пользователь удалён/заблокирован"
                    )
                    # Помечаем пользователя как невалидного — не тратить время снова
                    user.status = "❌ Невалидный"
                    user.access_hash = None  # сбрасываем, чтобы не использовать повторно
                    consecutive_errors += 1
                # "PEER_ID_INVALID" — другая формулировка той же ошибки
                elif "peer_id_invalid" in err_lower or "peer id invalid" in err_lower:
                    self._handle_invite_error(
                        user, info, "Peer ID invalid",
                        "пользователь не найден на сервере Telegram"
                    )
                    user.status = "❌ Невалидный"
                    user.access_hash = None
                    consecutive_errors += 1
                # "USER_ID_INVALID" — юзер не существует
                elif "user_id_invalid" in err_lower or "user id invalid" in err_lower:
                    self._handle_invite_error(
                        user, info, "User ID invalid",
                        "пользователь не существует"
                    )
                    user.status = "❌ Невалидный"
                    consecutive_errors += 1
                # "ChatAdminRequired" / "CHANNEL_PRIVATE"
                elif "channel_private" in err_lower or "chat admin required" in err_lower:
                    self._handle_invite_error(
                        user, info, "Нет прав", "нужны права админа в группе"
                    )
                    consecutive_errors += 1
                else:
                    self._handle_invite_error(user, info, "Ошибка", err_str[:120])
                    consecutive_errors += 1

            if consecutive_errors >= MAX_ERRORS:
                self.log_invite(f"🛑 {MAX_ERRORS} ошибок подряд — автоостановка", "error")
                break

            await self._update_progress(i + 1, total)
            self.root.after(0, self.update_stats_display)
            self.root.after(0, self.refresh_accounts_table)

            if self.rate_limiter.should_pause(total_attempts + 1):
                self.log_invite(f"⏸️ Пауза {self.rate_limiter.pause_time}с", "info")
                waited = 0
                while waited < self.rate_limiter.pause_time:
                    await asyncio.sleep(min(5, self.rate_limiter.pause_time - waited))
                    waited += 5
                    if self.invite_stop.is_set():
                        break

            if self.inviting_active and i < total - 1:
                # [NEW] Адаптивная задержка
                delay = self.rate_limiter.adaptive_delay()
                self.root.after(0, lambda d=delay: self.progress_label.config(
                    text=f"Ожидание {d}с..."))
                waited = 0
                while waited < delay:
                    await asyncio.sleep(min(2, delay - waited))
                    waited += 2
                    if self.invite_stop.is_set() or not self.invite_paused.is_set():
                        break

        await self._generate_final_report()

    async def _check_group_permissions(self, client: TelegramClient, group, info: AccountRuntimeInfo) -> None:
        """Предварительная проверка типа группы и прав аккаунта.

        Решает две проблемы из лога пользователя:
        1. "You can't write in this chat" — аккаунт не админ в супергруппе
        2. Broadcast-канал — в каналах инвайт запрещён вообще

        Если проверка не проходит — ставит invite_stop и логирует понятное сообщение.
        Также использует self._invite_input_channel (InputChannel) для GetParticipantRequest,
        чтобы избежать 'Invalid channel object' ошибки.
        """
        try:
            from telethon.tl.types import Channel as TlChannel, Chat as TlChat

            # Для обычного чата (Chat) права не проверяем — AddChatUserRequest
            # работает по другим правилам (любой участник может добавить)
            if isinstance(group, TlChat):
                self.log_invite(
                    f"ℹ️ [{info.me_name or 'account'}] Обычный чат — "
                    f"права не проверяются (AddChatUserRequest работает для участников)",
                    "info",
                )
                return

            # Проверяем broadcast (канал)
            if isinstance(group, TlChannel):
                is_broadcast = not getattr(group, "megagroup", False)
                if is_broadcast:
                    self.log_invite(
                        "🛑 ЦЕЛЕВАЯ ГРУППА — ЭТО КАНАЛ (broadcast)!\n"
                        "   В каналах приглашать пользователей могут только админы.\n"
                        "   Для инвайта нужна СУПЕРГРУППА (megagroup), а не канал.\n"
                        "   Создайте супергруппу или получите права админа в существующей.",
                        "error",
                    )
                    self.invite_stop.set()
                    return

            # Проверяем, является ли аккаунт админом с правом приглашать
            # Используем InputChannel (self._invite_input_channel) — иначе 'Invalid channel'
            try:
                from telethon.tl.functions.channels import GetParticipantRequest
                from telethon.tl.types import (
                    ChannelParticipantAdmin, ChannelParticipantCreator,
                )
                me = await client.get_me()

                # Используем InputChannel, не group
                # Telethon 1.44: GetParticipantRequest принимает participant, не user_id
                channel_param = self._invite_input_channel if self._invite_input_channel else group
                result = await client(GetParticipantRequest(
                    channel=channel_param, participant=me.id
                ))
                participant = result.participant
                is_admin = isinstance(participant, (ChannelParticipantAdmin, ChannelParticipantCreator))

                if is_admin:
                    # Проверяем конкретное право "invite_users"
                    admin_rights = getattr(participant, "admin_rights", None)
                    if admin_rights:
                        can_invite = getattr(admin_rights, "invite_users", False)
                        if not can_invite:
                            self.log_invite(
                                f"⚠️ [{info.me_name or 'account'}] Админ, но БЕЗ права 'Добавление пользователей'!\n"
                                f"   Нужно дать право 'invite_users' в настройках админа.",
                                "warning",
                            )
                        else:
                            self.log_invite(
                                f"✅ [{info.me_name or 'account'}] Админ с правом инвайта",
                                "success",
                            )
                    else:
                        # Creator имеет все права
                        self.log_invite(
                            f"✅ [{info.me_name or 'account'}] Создатель группы",
                            "success",
                        )
                else:
                    # Не админ — в супергруппе участники могут приглашать если не запрещено
                    self.log_invite(
                        f"⚠️ [{info.me_name or 'account'}] НЕ админ в этой группе!\n"
                        f"   Инвайт может не сработать. Дайте аккаунту права админа\n"
                        f"   с правом 'Добавление пользователей'.",
                        "warning",
                    )
            except Exception as e:
                # Не критично — продолжаем, ошибка всплывёт при инвайте
                err_str = str(e)
                self.log_invite(
                    f"ℹ️ Не удалось проверить права (не критично): {err_str[:80]}",
                    "info",
                )

        except Exception as e:
            self.log_invite(f"⚠️ Ошибка проверки прав: {e}", "warning")

    async def _get_input_channel_for_account(self, client: TelegramClient,
                                              info: AccountRuntimeInfo,
                                              target_group: str):
        """Получить InputChannel для конкретного аккаунта.

        access_hash канала — сессионный, для каждого аккаунта свой.
        Поэтому нельзя использовать InputChannel от primary аккаунта
        для других аккаунтов в ротации.

        Кэширует результат в info._input_channel_cache чтобы не повторять запросы.
        """
        # Проверяем кэш
        if not hasattr(info, "_input_channel_cache"):
            info._input_channel_cache = None
            info._input_channel_target = None

        # Если уже кэшировали для этой же группы — возвращаем
        if info._input_channel_cache is not None and info._input_channel_target == target_group:
            return info._input_channel_cache

        from telethon.tl.types import (
            InputChannel as TlInputChannel,
            InputPeerChannel as TlInputPeerChannel,
            Channel as TlChannel,
        )

        try:
            # Получаем entity через этот аккаунт
            group = await client.get_entity(target_group)
            if not isinstance(group, TlChannel):
                # Это не Channel (возможно Chat) — не нужен InputChannel
                return None

            # Получаем InputPeerChannel
            input_entity = await client.get_input_entity(group)
            if isinstance(input_entity, TlInputPeerChannel):
                input_channel = TlInputChannel(
                    channel_id=input_entity.channel_id,
                    access_hash=input_entity.access_hash,
                )
            elif isinstance(input_entity, TlInputChannel):
                input_channel = input_entity
            else:
                # Fallback — через group.id + access_hash
                access_hash = getattr(group, "access_hash", None)
                if access_hash:
                    input_channel = TlInputChannel(
                        channel_id=group.id,
                        access_hash=access_hash,
                    )
                else:
                    self.log_invite(
                        f"⚠️ [{info.me_name or 'account'}] Не удалось получить access_hash канала",
                        "warning",
                    )
                    return None

            # Кэшируем
            info._input_channel_cache = input_channel
            info._input_channel_target = target_group
            return input_channel

        except Exception as e:
            self.log_invite(
                f"⚠️ [{info.me_name or 'account'}] Ошибка получения InputChannel: {e}",
                "warning",
            )
            return None

    async def _get_input_user(self, client: TelegramClient, user: UserData):
        """Получить валидный InputUser для инвайта.

        Решает несколько проблем:
        1. "Could not find the input entity for PeerUser" — нет access_hash в кэше
        2. "Invalid object ID for a user" — невалидный/устаревший access_hash

        Стратегия (пробуем по очереди):
        1. Если есть access_hash — создаём InputUser и валидируем через GetFullUserRequest
        2. Если есть username — резолвим через @username (получаем свежий access_hash)
        3. Если есть в кэше сессии — get_input_entity(user.id)
        4. Возвращаем None

        Дополнительно: обновляем user.access_hash в UserData, если получили новый.
        """
        from telethon.tl.types import InputUser, InputPeerUser
        from telethon.tl.functions.users import GetFullUserRequest
        # Базовые ошибки — есть во всех версиях Telethon
        from telethon.errors import (
            PeerIdInvalidError, UserNotParticipantError,
            UsernameInvalidError, UsernameOccupiedError,
            UserDeletedError, UserDeactivatedError,
        )
        # Опциональные — через try/except (могут отсутствовать в старых версиях)
        UserDeactivatedBanError = type("UserDeactivatedBanError", (Exception,), {})
        try:
            from telethon.errors import UserDeactivatedBanError  # noqa: F811
        except ImportError:
            pass

        # Нормализуем username (убираем @ если есть)
        username = user.username
        if username and username.startswith("@"):
            username = username[1:]
        if username == "—" or username == "Нет":
            username = None

        # Путь 1: есть access_hash — создаём InputUser и ВАЛИДИРУЕМ через GetFullUserRequest
        if user.access_hash:
            try:
                input_user = InputUser(user_id=user.id, access_hash=user.access_hash)
                # Валидация — GetFullUserRequest вернёт ошибку если access_hash невалидный
                try:
                    await client(GetFullUserRequest(input_user))
                    return input_user  # ✅ Валидный
                except (PeerIdInvalidError, UserDeactivatedError,
                        UserDeactivatedBanError, UserDeletedError):
                    # access_hash невалидный — пробуем другие пути
                    pass
                except Exception as e:
                    # Если ошибка не связана с невалидным ID — возвращаем InputUser
                    err_str = str(e).lower()
                    if "invalid" not in err_str and "not found" not in err_str:
                        return input_user
            except Exception:
                pass

        # Путь 2: резолвим через @username (если есть) — получаем СВЕЖИЙ access_hash
        if username:
            try:
                entity = await client.get_entity(username)
                if entity and getattr(entity, "id", None) == user.id:
                    # Совпадает — создаём InputUser с свежим access_hash
                    access_hash = getattr(entity, "access_hash", None)
                    if access_hash:
                        input_user = InputUser(user_id=user.id, access_hash=access_hash)
                        # Обновляем в UserData для следующих попыток
                        user.access_hash = int(access_hash)
                        return input_user
            except Exception:
                pass

        # Путь 3: get_input_entity(user.id) — работает если юзер в кэше сессии
        try:
            input_entity = await client.get_input_entity(user.id)
            if isinstance(input_entity, InputPeerUser):
                input_user = InputUser(
                    user_id=input_entity.user_id,
                    access_hash=input_entity.access_hash,
                )
                # Обновляем access_hash
                if input_entity.access_hash:
                    user.access_hash = int(input_entity.access_hash)
                return input_user
            elif isinstance(input_entity, InputUser):
                if input_entity.access_hash:
                    user.access_hash = int(input_entity.access_hash)
                return input_entity
        except Exception:
            pass

        # Путь 4: пробуем через get_entity(user.id) — если юзер в кэше
        try:
            entity = await client.get_entity(user.id)
            access_hash = getattr(entity, "access_hash", None)
            if access_hash:
                input_user = InputUser(user_id=user.id, access_hash=access_hash)
                user.access_hash = int(access_hash)
                return input_user
        except Exception:
            pass

        # Ничего не сработало
        return None

    def _handle_invite_error(self, user, info, error_type, error_msg):
        user.status = f"❌ {error_type}"
        self.stats.failed += 1
        info.failed_count += 1
        self.rate_limiter.record(False)
        self.stats.errors[error_msg[:50]] = self.stats.errors.get(error_msg[:50], 0) + 1
        label = info.me_name or info.account.display_name
        user_info = f"{user.username or user.id} ({user.first_name} {user.last_name})".strip()
        self.log_invite(f"❌ [{label}] {error_type}: {user_info} - {error_msg[:60]}", "error")

    async def _update_progress(self, current, total):
        pct = (current / total * 100) if total else 0
        self.root.after(0, lambda: (
            self.invite_progress.set_value(pct),
            self.progress.set_value(pct),
            self.progress_label.config(text=f"{current}/{total} ({pct:.1f}%)"),
        ))

    async def _generate_final_report(self) -> None:
        if not self.stats.start_time:
            return
        duration = datetime.now() - self.stats.start_time
        h, rem = divmod(duration.seconds, 3600)
        m, s = divmod(rem, 60)
        attempts = self.stats.successful + self.stats.failed
        conv = (self.stats.successful / attempts * 100) if attempts > 0 else 0
        self.log_invite("=" * 50, "info")
        self.log_invite("🎯 ИНВАЙТ ЗАВЕРШЁН!", "info")
        self.log_invite(f"⏱️  Время: {h:02d}:{m:02d}:{s:02d}", "info")
        self.log_invite(f"✅ Успешно: {self.stats.successful}", "success")
        self.log_invite(f"❌ Ошибок: {self.stats.failed}", "error")
        self.log_invite(f"⏭️ Пропущено: {self.stats.skipped}", "info")
        self.log_invite(f"🎯 Конверсия: {conv:.1f}%", "info")
        for info in self.loaded_accounts:
            if info.invited_count == 0 and info.failed_count == 0:
                continue
            label = info.me_name or info.account.display_name
            self.log_invite(f"   • [{info.account.source_format}] {label}: "
                            f"✅{info.invited_count} ❌{info.failed_count}", "info")
        if self.stats.errors:
            self.log_invite("📋 Ошибки:", "info")
            for err, cnt in sorted(self.stats.errors.items(), key=lambda x: -x[1])[:10]:
                self.log_invite(f"   • {err}: {cnt} раз", "info")

        # [NEW] Сохраняем финальную статистику для HTML-отчёта
        self._last_duration_str = f"{h:02d}:{m:02d}:{s:02d}"
        self._last_target_group = self.target_group.get().strip()
        # Toast
        Toast.show(self.root, "Инвайт завершён",
                   f"✅ {self.stats.successful}  ❌ {self.stats.failed}  "
                   f"🎯 {conv:.1f}%", "success" if conv > 50 else "warning")

    def export_html_report(self) -> None:
        """Экспорт HTML-отчёта.  [NEW]"""
        if not self.stats.start_time:
            messagebox.showinfo("Инфо", "Сначала запустите инвайт")
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML files", "*.html")],
            initialfile=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        )
        if not filename:
            return
        try:
            duration_str = getattr(self, "_last_duration_str", "00:00:00")
            target = getattr(self, "_last_target_group", self.target_group.get().strip())
            html_content = generate_html_report(self.stats, self.loaded_accounts,
                                                 target, duration_str)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.log_message(f"📊 HTML-отчёт: {filename}", "success")
            Toast.show(self.root, "Отчёт сохранён", filename, "success")
            # Открыть в браузере
            try:
                import webbrowser
                webbrowser.open(f"file://{os.path.abspath(filename)}")
            except Exception:
                pass
        except Exception as e:
            self.log_message(f"❌ {e}", "error")

    def _invite_finished(self) -> None:
        self.inviting_active = False
        self.start_invite_btn.configure(state="normal")
        self.pause_invite_btn.configure(state="disabled")
        self.resume_invite_btn.configure(state="disabled")
        self.stop_invite_btn.configure(state="disabled")
        self.log_message("Инвайт завершён", "info")
        self.refresh_accounts_table()

    def pause_inviting(self) -> None:
        self.invite_paused.clear()
        self.pause_invite_btn.configure(state="disabled")
        self.resume_invite_btn.configure(state="normal")
        self.log_invite("⏸️ Пауза", "warning")

    def resume_inviting(self) -> None:
        self.invite_paused.set()
        self.pause_invite_btn.configure(state="normal")
        self.resume_invite_btn.configure(state="disabled")
        self.log_invite("▶️ Продолжено", "info")

    def stop_inviting(self) -> None:
        self.invite_stop.set()
        self.invite_paused.set()
        self.inviting_active = False
        self.log_invite("🛑 Стоп", "warning")
        self._invite_finished()

    def update_stats_display(self) -> None:
        if not self.stats.start_time:
            return
        duration = datetime.now() - self.stats.start_time
        attempts = self.stats.successful + self.stats.failed
        conv = (self.stats.successful / attempts * 100) if attempts > 0 else 0
        accounts_lines = ""
        for info in self.loaded_accounts:
            if info.invited_count > 0 or info.failed_count > 0:
                label = info.me_name or info.account.display_name
                accounts_lines += f"\n  [{info.account.source_format}] {label}: ✅{info.invited_count} ❌{info.failed_count}"
        text = (
            f"📊 СТАТИСТИКА:\n\n"
            f"✅ Успешно: {self.stats.successful}\n"
            f"❌ Ошибок: {self.stats.failed}\n"
            f"⏭️ Пропущено: {self.stats.skipped}\n"
            f"📊 Попыток: {attempts}\n"
            f"🎯 Конверсия: {conv:.1f}%\n"
            f"⏱️  Время: {duration.seconds // 60}:{duration.seconds % 60:02d}"
            f"{accounts_lines}"
        )
        self.stats_text.delete("1.0", tk.END)
        self.stats_text.insert("1.0", text)

    # =====================================================================
    # Управление (blacklist, backup)
    # =====================================================================
    def load_blacklist(self) -> None:
        bl_file = Path("blacklist.txt")
        if bl_file.exists():
            try:
                with open(bl_file, "r", encoding="utf-8") as f:
                    self.blacklist = {line.strip() for line in f if line.strip()}
            except Exception:
                self.blacklist = set()

    def save_blacklist(self) -> None:
        try:
            with open(Path("blacklist.txt"), "w", encoding="utf-8") as f:
                for uid in sorted(self.blacklist):
                    f.write(f"{uid}\n")
        except Exception:
            pass

    def update_blacklist_display(self) -> None:
        self.blacklist_listbox.delete(0, tk.END)
        for uid in sorted(self.blacklist):
            self.blacklist_listbox.insert(tk.END, uid)

    def add_to_blacklist(self) -> None:
        uid = self.blacklist_entry.get().strip()
        if not uid:
            return
        if not uid.lstrip("-").isdigit():
            messagebox.showerror("Ошибка", "ID должен быть числом!")
            return
        self.blacklist.add(uid)
        self.save_blacklist()
        self.update_blacklist_display()
        self.blacklist_entry.delete(0, tk.END)

    def remove_from_blacklist(self) -> None:
        sel = self.blacklist_listbox.curselection()
        if not sel:
            return
        uid = self.blacklist_listbox.get(sel[0])
        self.blacklist.discard(uid)
        self.save_blacklist()
        self.update_blacklist_display()

    def clear_blacklist(self) -> None:
        if self.blacklist and messagebox.askyesno("Очистка", "Очистить чёрный список?"):
            self.blacklist.clear()
            self.save_blacklist()
            self.update_blacklist_display()

    def backup_data(self) -> None:
        backup_dir = Path("backups")
        backup_dir.mkdir(exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        bf = backup_dir / f"backup_{ts}.json"
        data = {
            "parsed_users": [asdict(u) for u in self.parsed_users],
            "blacklist": sorted(self.blacklist),
            "stats": asdict(self.stats) if hasattr(self.stats, "__dataclass_fields__") else {},
            "backup_time": ts,
            "version": self.VERSION,
            "author": "zippa",
        }
        try:
            with open(bf, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self.log_message(f"💾 Backup: {bf}", "success")
            Toast.show(self.root, "Резервная копия", str(bf), "success")
        except Exception as e:
            self.log_message(f"❌ {e}", "error")

    def restore_data(self) -> None:
        backup_dir = Path("backups")
        if not backup_dir.exists():
            messagebox.showerror("Ошибка", "Папка backups не найдена!")
            return
        backups = sorted(backup_dir.glob("backup_*.json"), reverse=True)
        if not backups:
            messagebox.showerror("Ошибка", "Резервные копии не найдены!")
            return
        win = tk.Toplevel(self.root)
        win.title("Восстановление")
        win.configure(bg=Theme.BG_DEEP)
        win.transient(self.root)
        win.grab_set()
        win.geometry("420x320")
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"420x320+{(sw-420)//2}+{(sh-320)//2}")
        tk.Label(win, text="Выберите копию:", font=Theme.FONT_H2,
                 bg=Theme.BG_DEEP, fg=Theme.ACCENT_PRIMARY).pack(pady=10)
        lf = tk.Frame(win, bg=Theme.BG_DEEP)
        lf.pack(fill="both", expand=True, padx=10)
        lb = tk.Listbox(lf, width=55, height=12, font=Theme.FONT_MONO,
                        bg=Theme.BG_INPUT, fg=Theme.TEXT_PRIMARY,
                        selectbackground=Theme.ACCENT_PRIMARY,
                        selectforeground=Theme.TEXT_INVERSE,
                        highlightthickness=2, highlightbackground=Theme.BORDER,
                        highlightcolor=Theme.ACCENT_PRIMARY, relief="flat", bd=0)
        sb = ttk.Scrollbar(lf, orient="vertical", command=lb.yview)
        for b in backups[:30]:
            lb.insert(tk.END, b.name)
        lb.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        lb.config(yscrollcommand=sb.set)

        def restore():
            sel = lb.curselection()
            if not sel:
                return
            bf = backups[sel[0]]
            if messagebox.askyesno("Подтверждение", f"Восстановить из {bf.name}?"):
                try:
                    with open(bf, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.parsed_users = [UserData(**u) for u in data.get("parsed_users", [])]
                    self.blacklist = set(data.get("blacklist", []))
                    self._update_users_table()
                    self.update_blacklist_display()
                    self.save_blacklist()
                    win.destroy()
                    self.log_message(f"✅ Восстановлено: {bf.name}", "success")
                    Toast.show(self.root, "Восстановлено", level="success")
                except Exception as e:
                    self.log_message(f"❌ {e}", "error")
        AnimatedButton(win, text="Восстановить", command=restore,
                       bg=Theme.ACCENT_PRIMARY, hover_bg="#bd8cff",
                       width=180).pack(pady=10)

    # =====================================================================
    # Сервис
    # =====================================================================
    def _add_recent_group(self, group: str) -> None:
        if not group:
            return
        if group in self.recent_groups:
            self.recent_groups.remove(group)
        self.recent_groups.insert(0, group)
        self.recent_groups = self.recent_groups[:20]
        self._save_state()

    def _save_state(self) -> None:
        self.config_manager.save_state({
            "recent_groups": self.recent_groups,
            "session_map": self.session_phone_map,
            "geometry": self.root.geometry(),
        })

    def _on_closing(self) -> None:
        if self.inviting_active:
            if not messagebox.askyesno("Подтверждение", "Инвайт активен. Выйти?"):
                return
        self.close()
        self.root.destroy()

    def close(self) -> None:
        try:
            self._save_state()
            self.save_blacklist()
        except Exception:
            pass
        try:
            self.invite_stop.set()
            self.invite_paused.set()
            self.inviting_active = False
        except Exception:
            pass
        async def _disconnect_all():
            for info in self.loaded_accounts:
                if info.client and info.client.is_connected():
                    try:
                        await info.client.disconnect()
                    except Exception:
                        pass
            if self.client and self.client.is_connected():
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
        try:
            if self.loop and self.loop_running:
                future = asyncio.run_coroutine_threadsafe(_disconnect_all(), self.loop)
                try:
                    future.result(timeout=10)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            if self.loop and self.loop_running:
                self.loop.call_soon_threadsafe(self.loop.stop)
                if self.loop_thread:
                    self.loop_thread.join(timeout=5)
        except Exception:
            pass
        logger.info("Программа завершена")


# =====================================================================
# main()
# =====================================================================
def main() -> None:
    root = tk.Tk()
    try:
        root.iconbitmap("icon.ico")
    except Exception:
        pass
    app = TelegramWorkingInvite(root)
    root.protocol("WM_DELETE_WINDOW", app._on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
