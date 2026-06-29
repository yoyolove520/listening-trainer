# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for ListeningTrainer — Apple Design Edition.
One-folder distributable for fast startup.
"""
import os
import sys
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
app_dir = os.getcwd()

a = Analysis(
    ['main.py'],
    pathex=[app_dir],
    binaries=[],
    datas=[
        ('listening_app.db', '.'),
        ('app_icon.ico', '.'),
    ] + collect_data_files('certifi') + collect_data_files('ssl'),
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
        # SSL cert bundle (required on Mac/Linux)
        'certifi',
        'certifi.core',
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
    [],
    exclude_binaries=True,
    name='ListeningTrainer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='app_icon.ico',
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ListeningTrainer',
)
