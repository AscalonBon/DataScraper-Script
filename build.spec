# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect data files from dependencies
datas = []
datas += collect_data_files('selenium')
datas += collect_data_files('webdriver_manager')
datas += collect_data_files('bs4')

# Add assets and data directories
datas += [('assets', 'assets')]
datas += [('data', 'data')]

# Hidden imports for dynamic imports
hiddenimports = [
    'selenium',
    'selenium.webdriver',
    'selenium.webdriver.common',
    'selenium.webdriver.firefox',
    'selenium.webdriver.firefox.options',
    'selenium.webdriver.firefox.service',
    'webdriver_manager',
    'webdriver_manager.firefox',
    'beautifulsoup4',
    'bs4',
    'bs4.builder',
    'bs4.builder._htmlparser',
    'bs4.builder._lxml',
    'lxml',
    'lxml.etree',
    'lxml._elementpath',
    'PIL',
    'PIL.Image',
    'PIL.ImageTk',
    'tkinter',
    'tkinter.ttk',
]

# Analysis
a = Analysis(
    ['src/main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Create the executable
exe = EXE(
    pyd,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PetdentityScraper',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True to show console window for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

# Create a one-file bundle (optional - comment out if you want multiple files)
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     name='PetdentityScraper',
# )