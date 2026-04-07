# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Big Homie
Builds standalone executable with logo and all dependencies
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('logo.png', '.'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'anthropic',
        'openai',
        'httpx',
        'pydantic',
        'pydantic_settings',
        'loguru',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'sqlalchemy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
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
    name='BigHomie',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='logo.png',  # Application icon
)

# For macOS
app = BUNDLE(
    exe,
    name='BigHomie.app',
    icon='logo.png',
    bundle_identifier='com.bighomie.agent',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleName': 'Big Homie',
        'CFBundleDisplayName': 'Big Homie',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2026 Big Homie',
    },
)
