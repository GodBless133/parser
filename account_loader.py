"""
account_loader.py
=================

Универсальный загрузчик Telegram-аккаунтов из трёх форматов:

  1. Telethon   (.session SQLite — собственный формат Telethon)
  2. Pyrogram   (.session SQLite — собственный формат Pyrogram)
  3. TData      (папка tdata/ из Telegram Desktop)

Все три формата приводятся к единому объекту LoadedAccount, который
содержит auth_key + dc_id. Из них строится StringSession для Telethon,
которую можно передать в TelegramClient — никаких отдельных API-данных
на аккаунт не требуется (используется один общий api_id/api_hash).

ЗАВИСИМОСТИ:
  - cryptography (для TData — AES-IGE через ECB + ручная IGE-надстройка)

ИСПОЛЬЗОВАНИЕ:
  from account_loader import AccountLoader
  loader = AccountLoader()
  accounts = loader.scan_folder(Path("my_sessions"))
  for acc in accounts:
      print(acc.source_format, acc.user_id, acc.dc_id)

  # Подключение:
  from telethon import TelegramClient
  from telethon.sessions import StringSession
  client = TelegramClient(StringSession(acc.telethon_string), api_id, api_hash)
  await client.connect()
  if await client.is_user_authorized():
      me = await client.get_me()
"""

import base64
import hashlib
import logging
import sqlite3
import struct
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger("tg_parser.accounts")


# Карта Telegram-датацентров: dc_id -> (server, port)
DC_MAP = {
    1: ("149.154.175.50", 443),
    2: ("149.154.167.51", 443),
    3: ("149.154.175.100", 443),
    4: ("149.154.167.91", 443),
    5: ("91.108.56.130", 443),
}


# =====================================================================
# LoadedAccount — универсальная модель аккаунта
# =====================================================================
@dataclass
class LoadedAccount:
    """Универсальное представление загруженного аккаунта.

    Атрибуты:
        auth_key:    256-байтовый ключ авторизации Telegram
        dc_id:       идентификатор дата-центра (1-5)
        user_id:     Telegram user_id (если удалось извлечь)
        phone:       телефон (если есть в сессии)
        api_id:      api_id из сессии (только Telethon/Pyrogram; для TData=None)
        source_format: "telethon" | "pyrogram" | "tdata"
        source_path: путь к файлу/папке сессии
        telethon_string: готовый StringSession для Telethon
        display_name: человекочитаемое имя (телефон или ID)
        is_valid:    признак успешной загрузки
        error:       сообщение об ошибке (если is_valid=False)
    """
    auth_key: bytes
    dc_id: int
    user_id: Optional[int] = None
    phone: Optional[str] = None
    api_id: Optional[int] = None
    source_format: str = "unknown"
    source_path: str = ""
    telethon_string: str = field(default="", repr=False)
    display_name: str = ""
    is_valid: bool = True
    error: str = ""

    def __post_init__(self) -> None:
        # Не пытаемся строить StringSession, если auth_key пустой/нулевой
        # (это бывает для fallback-аккаунтов при ручной авторизации)
        if not self.telethon_string and self.auth_key and len(self.auth_key) == 256 and any(self.auth_key):
            try:
                self.telethon_string = make_string_session(self.auth_key, self.dc_id)
            except Exception as e:
                self.is_valid = False
                self.error = f"Не удалось построить StringSession: {e}"
                logger.warning(f"StringSession build failed for {self.source_path}: {e}")
        elif self.auth_key and (len(self.auth_key) != 256 or not any(self.auth_key)):
            self.is_valid = False
            self.error = (
                f"auth_key невалиден (длина={len(self.auth_key)}, "
                f"все нули={not any(self.auth_key)})"
            )
            logger.warning(f"Invalid auth_key for {self.source_path}: {self.error}")
        if not self.display_name:
            if self.phone:
                self.display_name = self.phone
            elif self.user_id:
                self.display_name = f"ID:{self.user_id}"
            else:
                self.display_name = Path(self.source_path).name


# =====================================================================
# StringSession builder  (Telethon 1.34+ format)
# =====================================================================
def make_string_session(auth_key: bytes, dc_id: int) -> str:
    """Строит Telethon StringSession из auth_key + dc_id.

    ФОРМАТ Telethon 1.34+ (актуальный для 1.44):

        Структура struct.pack('>B{}sH256s', ...):
          - B  = dc_id          (1 байт, unsigned char)
          - {}s = IP-адрес      (4 байта для IPv4 / 16 для IPv6 — packed bytes)
          - H  = port           (2 байта, unsigned short, big-endian)
          - 256s = auth_key     (256 байт)

        Полная строка: '1' + base64_urlsafe(packed)

        Telethon определяет IPv4 vs IPv6 по длине декодированных данных:
            len == 352 (после base64) → IPv4 (4 байта IP)
            иначе → IPv6 (16 байт IP)

    Старый формат (с int32 длиной адреса + utf-8 строкой) БОЛЬШЕ НЕ РАБОТАЕТ
    в Telethon 1.34+ — вызывал ошибку "Not a valid string".
    """
    import ipaddress

    # Валидация auth_key
    if not auth_key or len(auth_key) != 256:
        raise ValueError(
            f"auth_key должен быть 256 байт, получено {len(auth_key) if auth_key else 0}"
        )
    # Telethon проверяет `if any(key)` — если все нули, ключ считается невалидным
    if not any(auth_key):
        raise ValueError("auth_key состоит только из нулей — невалиден")

    if dc_id not in DC_MAP:
        logger.warning(f"Неизвестный dc_id={dc_id}, использую DC2")
        dc_id = 2
    server, port = DC_MAP[dc_id]

    # IP-адрес как packed bytes (4 байта для IPv4)
    try:
        ip_bytes = ipaddress.ip_address(server).packed
    except ValueError as e:
        raise ValueError(f"Невалидный IP-адрес {server}: {e}")

    # Pack: >B{len}sH256s
    # B = dc_id (1), {}s = ip (4 для IPv4), H = port (2), 256s = auth_key
    packed = struct.pack(
        f">B{len(ip_bytes)}sH256s",
        dc_id,
        ip_bytes,
        port,
        auth_key,
    )

    # base64 urlsafe кодировка + префикс версии
    encoded = base64.urlsafe_b64encode(packed).decode("ascii")
    return "1" + encoded


def validate_string_session(session_str: str) -> bool:
    """Проверить, что строка StringSession валидна для текущей версии Telethon.

    Используется для раннего обнаружения проблем перед созданием клиента.
    """
    if not session_str or not session_str.startswith("1"):
        return False
    try:
        import ipaddress
        # Декодируем
        raw = base64.urlsafe_b64decode(session_str[1:])
        # Длина: 1 (dc) + 4 (IPv4) или 16 (IPv6) + 2 (port) + 256 (auth_key)
        # = 263 для IPv4, 275 для IPv6
        if len(raw) not in (263, 275):
            return False
        ip_len = 4 if len(raw) == 263 else 16
        dc_id, ip, port, key = struct.unpack(f">B{ip_len}sH256s", raw)
        # Проверки
        if not (1 <= dc_id <= 5):
            return False
        ipaddress.ip_address(ip)  # бросит исключение если невалидный
        if not (1 <= port <= 65535):
            return False
        if not any(key):
            return False
        return True
    except Exception:
        return False


# =====================================================================
# Telethon session loader
# =====================================================================
def load_telethon_session(path: Path) -> Optional[LoadedAccount]:
    """Загрузка .session файла Telethon.

    Схема SQLite Telethon:
        sessions (dc_id, server_address, port, auth_key, takeout_id)
        parameters (name, value)  -- здесь хранится api_id
        entities (id, hash, name, ...)

    Возвращает None, если файл не является сессией Telethon.
    """
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}

        # Признак Telethon: есть таблица sessions И parameters (необязательно)
        if "sessions" not in tables:
            conn.close()
            return None

        # Telethon sessions: dc_id, server_address, port, auth_key, takeout_id
        try:
            cur.execute("SELECT dc_id, server_address, port, auth_key FROM sessions LIMIT 1")
        except sqlite3.OperationalError:
            conn.close()
            return None
        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        dc_id, server, port, auth_key = row
        if not auth_key or len(auth_key) != 256:
            conn.close()
            return None

        # api_id хранится в parameters
        api_id: Optional[int] = None
        if "parameters" in tables:
            try:
                cur.execute("SELECT value FROM parameters WHERE name='api_id' LIMIT 1")
                r = cur.fetchone()
                if r:
                    api_id = int(r[0])
            except Exception:
                pass

        # user_id обычно хранится в entities (как id пользователя с самым большим id)
        # или отсутствует — Telethon его явно не сохраняет в новой версии
        user_id: Optional[int] = None
        if "entities" in tables:
            try:
                # Ищем запись типа "user" — берём максимальный id
                cur.execute("SELECT MAX(id) FROM entities WHERE id > 0 LIMIT 1")
                r = cur.fetchone()
                if r and r[0]:
                    user_id = int(r[0])
            except Exception:
                pass

        conn.close()

        return LoadedAccount(
            auth_key=auth_key,
            dc_id=int(dc_id) if dc_id else 2,
            user_id=user_id,
            api_id=api_id,
            source_format="telethon",
            source_path=str(path),
        )
    except Exception as e:
        logger.debug(f"Не Telethon-сессия {path}: {e}")
        return None


# =====================================================================
# Pyrogram session loader
# =====================================================================
def load_pyrogram_session(path: Path) -> Optional[LoadedAccount]:
    """Загрузка .session файла Pyrogram.

    Схема SQLite Pyrogram:
        sessions (dc_id, api_id, test_mode, auth_key, date, user_id, is_bot)

    Файлы Pyrogram имеют ту же структуру таблицы 'sessions', но с другим
    набором колонок — по этому признаку отличаем от Telethon.
    """
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        cur = conn.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        if "sessions" not in tables:
            conn.close()
            return None

        # Pyrogram: dc_id, api_id, test_mode, auth_key, date, user_id, is_bot
        try:
            cur.execute(
                "SELECT dc_id, api_id, auth_key, user_id FROM sessions LIMIT 1"
            )
        except sqlite3.OperationalError:
            # Если колонок api_id/user_id нет — это не Pyrogram
            conn.close()
            return None

        row = cur.fetchone()
        if not row:
            conn.close()
            return None

        dc_id, api_id, auth_key, user_id = row
        if not auth_key or len(auth_key) != 256:
            conn.close()
            return None

        conn.close()

        return LoadedAccount(
            auth_key=auth_key,
            dc_id=int(dc_id) if dc_id else 2,
            user_id=int(user_id) if user_id else None,
            api_id=int(api_id) if api_id else None,
            source_format="pyrogram",
            source_path=str(path),
        )
    except Exception as e:
        logger.debug(f"Не Pyrogram-сессия {path}: {e}")
        return None


# =====================================================================
# TData loader (Telegram Desktop)
# =====================================================================
# Для AES-IGE используем cryptography (уже в зависимостях) — режим ECB +
# собственная реализация IGE на чистом Python. Это позволяет не тянуть
# pycryptodome только ради одной функции.
try:
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes  # type: ignore
    _HAS_CRYPTO_AES = True
except ImportError:
    _HAS_CRYPTO_AES = False


def _aes_ige_decrypt(data: bytes, key: bytes, iv: bytes) -> bytes:
    """AES-256-IGE дешифровка.

    IGE (Infinite Garble Extension) — режим AES, используемый в MTProto
    и Telegram Desktop для локального шифрования.

    Спецификация IGE (RFC-style):
        Encrypt:  C_j = E_k(P_j XOR C_{j-1}) XOR P_{j-1}
                  где C_0 = IV_1 = iv[:16],  P_0 = IV_2 = iv[16:32]
        Decrypt:  P_j = D_k(C_j XOR P_{j-1}) XOR C_{j-1}

    То есть для decrypt на каждом блоке:
        - XOR'им шифротекст с prev_plain (до D_k)
        - XOR'им результат D_k с prev_cipher (после D_k)
        - prev_plain = P_j, prev_cipher = C_j для следующей итерации

    Реализация на cryptography.hazmat — не требует pycryptodome.
    """
    if not _HAS_CRYPTO_AES:
        raise RuntimeError(
            "Для поддержки TData требуется библиотека cryptography: "
            "pip install cryptography"
        )
    if len(key) != 32:
        raise ValueError(f"AES key должен быть 32 байта, получено {len(key)}")
    if len(iv) < 32:
        raise ValueError(f"IV должен быть >= 32 байт, получено {len(iv)}")

    # Выравниваем данные до кратного 16
    if len(data) % 16 != 0:
        data = data[: (len(data) // 16) * 16]

    cipher = Cipher(algorithms.AES(key), modes.ECB())
    decryptor = cipher.decryptor()

    # IGE: C_0 = IV_1 (xor до E), P_0 = IV_2 (xor после E)
    prev_cipher = iv[:16]    # C_{j-1} — для XOR после D_k
    prev_plain = iv[16:32]   # P_{j-1} — для XOR до D_k
    result_blocks: List[bytes] = []

    for i in range(0, len(data), 16):
        block = data[i : i + 16]
        # XOR'им шифротекст с предыдущим открытым текстом (до D_k)
        xored_input = bytes(a ^ b for a, b in zip(block, prev_plain))
        # AES-ECB decrypt
        intermediate = decryptor.update(xored_input)
        # XOR'им результат с предыдущим шифротекстом (после D_k)
        plain = bytes(a ^ b for a, b in zip(intermediate, prev_cipher))
        result_blocks.append(plain)
        # Обновляем prev для следующей итерации
        prev_plain = plain
        prev_cipher = block

    # Завершаем
    decryptor.finalize()

    return b"".join(result_blocks)


def _create_local_key(passcode: bytes, salt: bytes) -> bytes:
    """TDesktop LocalKey derivation.

    Реализует PBKDF2-HMAC-SHA512 с 100000 итераций, как в tdesktop:
        Telegram/SourceFiles/storage/details/storage_file_utilities.cpp
        CreateLocalKey()

    Возвращает 256 байт — полный локальный ключ.
    """
    return hashlib.pbkdf2_hmac("sha512", passcode, salt, 100000, dklen=256)


def _decrypt_tdata_block(data: bytes, passcode: bytes = b"") -> Optional[bytes]:
    """Дешифровка блока данных TData.

    Структура файла key_datas:
        [salt: 32 байта]      -- соль для KDF
        [encrypted: остальное] -- AES-IGE-256 зашифрованные данные

    AES key = local_key[0:32]
    AES IV  = local_key[32:64]
    """
    if len(data) < 32 + 16:  # минимум salt + один блок
        return None
    salt = data[:32]
    encrypted = data[32:]

    local_key = _create_local_key(passcode, salt)
    aes_key = local_key[:32]
    aes_iv = local_key[32:64]

    try:
        return _aes_ige_decrypt(encrypted, aes_key, aes_iv)
    except Exception as e:
        logger.error(f"Ошибка дешифровки TData: {e}")
        return None


def _find_key_datas(tdata_dir: Path) -> Optional[Path]:
    """Найти файл key_datas в директории TData.

    Возможные пути:
        tdata/key_datas                — прямое расположение
        tdata/D877F783D5D3EF8C/key_datas — стандартный подкаталог TDesktop
        tdata/key_datas0, key_datas1, ... — версии (берём последний)
    """
    candidates: List[Path] = []

    # Прямой путь
    direct = tdata_dir / "key_datas"
    if direct.exists():
        candidates.append(direct)

    # В подкаталогах (типичное D877F783D5D3EF8C)
    try:
        for sub in tdata_dir.iterdir():
            if sub.is_dir():
                kd = sub / "key_datas"
                if kd.exists():
                    candidates.append(kd)
                # Версии
                for f in sub.glob("key_datas*"):
                    if f != kd and f.is_file():
                        candidates.append(f)
    except Exception:
        pass

    if not candidates:
        return None

    # Берём самый последний изменённый (обычно это актуальный)
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _extract_auth_from_decrypted(decrypted: bytes) -> Optional[tuple]:
    """Извлечь (dc_id, user_id, auth_key) из дешифрованного key_datas.

    Формат дешифрованных данных TDesktop (MTPauthorization):
        [mainDC: 4 байта int32 LE]      -- основной DC (1-5)
        [userId: 8 байт int64 LE]       -- ID пользователя
        [auth_key: 256 байт]            -- ключ авторизации

    В редких случаях перед mainDC могут быть дополнительные байты
    (TL constructor ID), поэтому добавляем fallback-поиск.
    """
    if len(decrypted) < 12 + 256:
        return None

    # Основная попытка: dc_id с самого начала
    for offset in (0, 4):
        if len(decrypted) < offset + 12 + 256:
            continue
        try:
            dc_id = struct.unpack("<i", decrypted[offset : offset + 4])[0]
            if 1 <= dc_id <= 5:
                user_id = struct.unpack(
                    "<q", decrypted[offset + 4 : offset + 12]
                )[0]
                auth_key = decrypted[offset + 12 : offset + 12 + 256]
                if len(auth_key) == 256:
                    return (dc_id, user_id, auth_key)
        except struct.error:
            continue

    # Fallback: ищем 256-байтный блок, который выглядит как auth_key
    # (начинается с типичных байтов). Это эвристика — менее надёжна.
    logger.warning("Стандартный парсинг TData не удался, использую эвристику")
    for i in range(0, len(decrypted) - 256 - 4, 4):
        chunk = decrypted[i : i + 4]
        try:
            dc_id = struct.unpack("<i", chunk)[0]
            if 1 <= dc_id <= 5 and i + 4 + 256 <= len(decrypted):
                auth_key = decrypted[i + 4 : i + 4 + 256]
                return (dc_id, 0, auth_key)
        except struct.error:
            continue

    return None


def load_tdata(tdata_dir: Path, passcode: str = "") -> Optional[LoadedAccount]:
    """Загрузка аккаунта из папки TData (Telegram Desktop).

    Структура:
        tdata/
        ├── D877F783D5D3EF8C/
        │   ├── map
        │   ├── key_datas        <-- нас интересует этот файл
        │   ├── key_datas0
        │   └── ...
        ├── key_datas            <-- или этот
        └── ...

    Аргументы:
        tdata_dir: путь к папке tdata (или к родительской, содержащей tdata/)
        passcode:  локальный пароль TDesktop (если установлен, обычно пустой)

    Возвращает LoadedAccount или None при ошибке.
    """
    # Принимаем как саму папку tdata, так и родительскую
    if tdata_dir.name.lower() != "tdata" and (tdata_dir / "tdata").exists():
        tdata_dir = tdata_dir / "tdata"
    if not tdata_dir.exists() or not tdata_dir.is_dir():
        return None

    if not _HAS_CRYPTO_AES:
        logger.error(
            "Для загрузки TData требуется библиотека cryptography: "
            "pip install cryptography"
        )
        return None

    key_datas = _find_key_datas(tdata_dir)
    if not key_datas:
        logger.error(f"key_datas не найден в {tdata_dir}")
        return None

    try:
        with open(key_datas, "rb") as f:
            raw = f.read()
    except Exception as e:
        logger.error(f"Не удалось прочитать {key_datas}: {e}")
        return None

    decrypted = _decrypt_tdata_block(raw, passcode.encode("utf-8"))
    if not decrypted:
        logger.error(
            f"Не удалось дешифровать {key_datas} — неверный пароль или повреждённый файл"
        )
        return None

    extracted = _extract_auth_from_decrypted(decrypted)
    if not extracted:
        logger.error(
            f"Не удалось извлечь auth_key из {key_datas} — неизвестный формат"
        )
        return None

    dc_id, user_id, auth_key = extracted

    return LoadedAccount(
        auth_key=auth_key,
        dc_id=dc_id,
        user_id=user_id if user_id > 0 else None,
        source_format="tdata",
        source_path=str(tdata_dir),
    )


# =====================================================================
# AccountLoader — сканирование папки
# =====================================================================
class AccountLoader:
    """Сканирование папки и загрузка всех найденных аккаунтов.

    Поддерживаемые структуры:
        folder/
        ├── session1.session      (Telethon или Pyrogram)
        ├── session2.session
        ├── account1/
        │   └── tdata/            (TData в подкаталоге)
        ├── account2/
        │   └── D877F783D5D3EF8C/  (TData без родительской tdata/)
        │       └── key_datas
        └── tdata/                (голая папка tdata)
    """

    def __init__(self) -> None:
        self.accounts: List[LoadedAccount] = []
        self.errors: List[str] = []

    def scan_folder(self, folder) -> List[LoadedAccount]:
        """Сканировать папку и вернуть список найденных аккаунтов."""
        folder = Path(folder)
        self.accounts = []
        self.errors = []

        if not folder.exists() or not folder.is_dir():
            self.errors.append(f"Папка не существует: {folder}")
            return []

        try:
            entries = list(folder.iterdir())
        except Exception as e:
            self.errors.append(f"Не удалось прочитать папку: {e}")
            return []

        # Рекурсивно обходим (но не глубже 2 уровней для TData)
        self._scan_dir(folder, max_depth=2)

        logger.info(
            f"Сканирование {folder}: найдено {len(self.accounts)} аккаунтов, "
            f"{len(self.errors)} ошибок"
        )
        return self.accounts

    def _scan_dir(self, folder: Path, depth: int = 0, max_depth: int = 2) -> None:
        """Рекурсивное сканирование с ограничением глубины."""
        if depth > max_depth:
            return

        try:
            entries = list(folder.iterdir())
        except Exception:
            return

        for entry in entries:
            if not entry.exists():
                continue

            try:
                if entry.is_file() and entry.suffix.lower() == ".session":
                    acc = self._try_load_session_file(entry)
                    if acc:
                        self.accounts.append(acc)
                    else:
                        self.errors.append(f"Не распознан формат: {entry}")
                elif entry.is_dir():
                    # Это TData?
                    tdata_path = self._detect_tdata(entry)
                    if tdata_path:
                        acc = load_tdata(tdata_path)
                        if acc:
                            self.accounts.append(acc)
                        else:
                            self.errors.append(
                                f"Не удалось загрузить TData: {tdata_path}"
                            )
                    elif depth < max_depth:
                        # Рекурсивно в подкаталог
                        self._scan_dir(entry, depth + 1, max_depth)
            except Exception as e:
                self.errors.append(f"Ошибка при обработке {entry}: {e}")

    def _try_load_session_file(self, path: Path) -> Optional[LoadedAccount]:
        """Попытаться загрузить .session файл (сначала Telethon, затем Pyrogram)."""
        # Telethon
        acc = load_telethon_session(path)
        if acc:
            return acc
        # Pyrogram
        acc = load_pyrogram_session(path)
        if acc:
            return acc
        return None

    def _detect_tdata(self, path: Path) -> Optional[Path]:
        """Проверить, является ли папка TData. Вернуть путь к tdata или None."""
        # Случай 1: сама папка называется tdata
        if path.name.lower() == "tdata":
            return path

        # Случай 2: внутри есть папка tdata
        if (path / "tdata").exists() and (path / "tdata").is_dir():
            return path / "tdata"

        # Случай 3: внутри есть признаки TData (key_datas, map, D877F783D5D3EF8C)
        try:
            for item in path.iterdir():
                name = item.name.lower()
                if name in ("key_datas", "map", "usertag"):
                    return path
                if name.startswith("key_datas") or name.startswith("map"):
                    return path
                # Стандартный подкаталог TDesktop
                if item.is_dir() and (item / "key_datas").exists():
                    return path
        except Exception:
            pass

        return None


# =====================================================================
# CLI для тестирования
# =====================================================================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(f"Использование: {sys.argv[0]} <папка с сессиями>")
        print()
        print("Пример структуры папки:")
        print("  my_sessions/")
        print("  ├── account1.session   (Telethon)")
        print("  ├── account2.session   (Pyrogram)")
        print("  ├── tdata_account1/")
        print("  │   └── tdata/         (Telegram Desktop)")
        print("  └── tdata/             (голая tdata)")
        sys.exit(1)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    folder = Path(sys.argv[1])
    loader = AccountLoader()
    accounts = loader.scan_folder(folder)

    print(f"\n{'='*60}")
    print(f"Найдено аккаунтов: {len(accounts)}")
    print(f"Ошибок: {len(loader.errors)}")
    print(f"{'='*60}\n")

    for i, acc in enumerate(accounts, 1):
        print(f"--- Аккаунт {i} ---")
        print(f"  Формат:     {acc.source_format}")
        print(f"  User ID:    {acc.user_id or 'неизвестно'}")
        print(f"  DC:         {acc.dc_id}")
        print(f"  API ID:     {acc.api_id or 'не указан'}")
        print(f"  Источник:   {acc.source_path}")
        print(f"  Auth key:   {acc.auth_key[:16].hex()}...")
        print(f"  Session:    {acc.telethon_string[:60]}...")
        print()

    if loader.errors:
        print("Ошибки:")
        for err in loader.errors:
            print(f"  • {err}")
