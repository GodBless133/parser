# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec для Telegram Parser & Inviter PRO v5.0
DarkZippa Edition — by zippa

Сборка:
    pyinstaller TelegramInviterPro.spec
"""

import sys
import os
from pathlib import Path

# Поиск Tcl/Tk библиотек (libtcl9.0.so, libtk9.0.so)
# Это критично для tkinter в собранном приложении
def find_tcl_tk_libs():
    """Найти libtcl*.so и libtk*.so в стандартных путях."""
    search_paths = [
        Path(sys.prefix) / "lib",
        Path(sys.base_prefix) / "lib",
        Path.home() / ".local/share/uv/python",
        Path("/usr/lib"),
        Path("/usr/lib/x86_64-linux-gnu"),
    ]
    libs = []
    seen = set()
    for base in search_paths:
        if not base.exists():
            continue
        for lib in list(base.glob("libtcl*.so*")) + list(base.glob("libtk*.so*")):
            if lib.name not in seen and "itcl" not in lib.name and "thread" not in lib.name:
                libs.append((str(lib), '.'))
                seen.add(lib.name)
    return libs

tcl_tk_libs = find_tcl_tk_libs()

block_cipher = None

a = Analysis(
    ['tg_pro_v5.py'],
    pathex=['.'],
    binaries=tcl_tk_libs,
    datas=[
        # account_loader.py и ui_framework.py как отдельные модули
        ('account_loader.py', '.'),
        ('ui_framework.py', '.'),
    ],
    hiddenimports=[
        'telethon',
        'telethon.network.connection',
        'telethon.sessions',
        'cryptography.fernet',
        'cryptography.hazmat.backends.openssl',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.ciphers.algorithms',
        'cryptography.hazmat.primitives.ciphers.modes',
        'socks',
        'account_loader',
        'ui_framework',
        '_tkinter',  # важно для tkinter
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter.test', 'unittest', 'test'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TelegramInviterPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # GUI приложение — консоль не нужна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',  # раскомментируйте если есть icon.ico рядом
)
