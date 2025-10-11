# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files

# Collect all necessary packages
datas = []
binaries = []
hiddenimports = []

# LightRAG and dependencies
packages = [
    'lightrag',
    'fastapi',
    'uvicorn',
    'pydantic',
    'pydantic_core',
    'starlette',
    'anyio',
    'sniffio',
]

for package in packages:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
    except Exception as e:
        print(f"Warning: Could not collect {package}: {e}")

# Add uvicorn workers
hiddenimports += [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
]

# Analysis
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary packages
        'pytest',
        'IPython',
        'matplotlib',
        'notebook',
        'jupyter',
        'sphinx',
        'setuptools',
        'pip',
        'wheel',
        'black',
        'pylint',
        'mypy',
        'pytest-cov',
        'coverage',
        # Exclude GUI frameworks if not used
        'tkinter',
        'tk',
        'tcl',
        'PyQt5',
        'PyQt6',
        'PySide2',
        'PySide6',
        # Exclude unused stdlib modules
        'distutils',
        'email',
        'html',
        'http.client',
        'urllib',
        'xml',
        'xmlrpc',
        'pydoc',
        'doctest',
        'argparse',
        'difflib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Single file executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,  # Strip binary (Linux/macOS)
    upx=False,   # Disable UPX (causes issues sometimes)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Platform-specific options
    icon='icon.ico' if sys.platform == 'win32' else None,
)

# For debugging: create directory build to see what's included
# coll = COLLECT(
#     exe,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     strip=False,
#     upx=False,
#     upx_exclude=[],
#     name='backend',
# )