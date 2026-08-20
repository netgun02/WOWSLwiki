# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['wowslnamu.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data/*.txt', 'data'),
        ('data/wowsl_terms.json', 'data'),
        ('data/consumables_parser_rules/*.json', 'data/consumables_parser_rules'),
    ],
    hiddenimports=['tkinter', '_tkinter'],
    hookspath=['pyinstaller_hooks'],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='wowslnamu-onefile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
