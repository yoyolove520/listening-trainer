# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ListeningTrainer — macOS .app bundle.
One-folder bundle inside .app for fast startup.
"""
import os
import sys

block_cipher = None
app_dir = os.getcwd()

# ── Find icon ─────────────────────────────────────────────
icon_candidates = [
    os.path.join(app_dir, "app_icon.icns"),
    os.path.join(app_dir, "app_icon.ico"),
]
icon_path = None
for p in icon_candidates:
    if os.path.exists(p):
        icon_path = p
        break

a = Analysis(
    ['main.py'],
    pathex=[app_dir],
    binaries=[],
    datas=[
        ('listening_app.db', '.'),
    ],
    hiddenimports=[
        # PySide6
        'PySide6.QtWidgets',
        'PySide6.QtGui',
        'PySide6.QtCore',
        'PySide6.QtMultimedia',
        # TTS + async
        'edge_tts',
        'edge_tts.exceptions',
        'aiohttp',
        'aiohttp._websocket',
        'aiohttp._websocket.reader_c',
        'aiohttp._websocket.mask',
        # App modules
        'app',
        'app.theme',
        'app.main_window',
        'app.pages',
        'app.pages.generate_page',
        'app.pages.history_page',
        'app.pages.settings_page',
        'app.pages.stats_page',
        'app.widgets',
        'app.widgets.nav_sidebar',
        'app.widgets.exercise_item',
        'app.widgets.dialogs',
        'app.services',
        'app.services.models',
        'app.services.database',
        'app.services.storage',
        'app.services.ai_service',
        'app.services.tts_service',
        'app.services.generate_service',
        'app.services.archive_service',
        'app.services.student_service',
        'app.services.config_service',
        'app.services.player_service',
        'app.services.stats_service',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy', 'numpy', 'pandas',
        'cv2', 'PIL', 'notebook', 'jupyter', 'IPython',
        'setuptools', 'pip', 'unittest', 'pydoc',
        'PySide6.QtQml', 'PySide6.QtQuick',
        'PySide6.QtWebEngine', 'PySide6.QtWebEngineWidgets',
        'PySide6.QtSvg', 'PySide6.QtTest',
        'PySide6.QtBluetooth', 'PySide6.QtPositioning',
        'PySide6.QtSensors', 'PySide6.QtSerialPort', 'PySide6.QtXml',
        'PySide6.QtSql', 'PySide6.QtHelp', 'PySide6.QtPrintSupport',
        'PySide6.QtOpenGL', 'PySide6.QtOpenGLWidgets',
    ],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ListeningTrainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=icon_path,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS .app bundle
app = BUNDLE(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='ListeningTrainer.app',
    icon=icon_path,
    bundle_identifier='com.listeningtrainer.app',
    info_plist={
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': '© 2024 ListeningTrainer',
        'NSRequiresAquaSystemAppearance': False,
        'CFBundleName': '听力练习助手',
        'CFBundleDisplayName': '听力练习助手',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
    },
)
