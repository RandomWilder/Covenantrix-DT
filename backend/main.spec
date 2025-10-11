# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Covenantrix Backend
Optimized for production deployment with Electron
"""
import sys
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules

block_cipher = None

# ============================================================================
# Data Collection
# ============================================================================

datas = []
binaries = []
hiddenimports = []

print("=" * 60)
print("Building Covenantrix Backend Executable")
print("=" * 60)

# Collect FastAPI and dependencies
print("\nCollecting FastAPI ecosystem...")
for package in ['fastapi', 'pydantic', 'pydantic_core', 'pydantic_settings']:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
        print(f"  ✓ {package}")
    except Exception as e:
        print(f"  ⚠ {package}: {e}")

# Collect Uvicorn with all modules (CRITICAL for FastAPI)
print("\nCollecting Uvicorn...")
hiddenimports += [
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.http.httptools_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.protocols.websockets.websockets_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
]
print("  ✓ Uvicorn (all protocols)")

# Collect Starlette (FastAPI dependency)
print("\nCollecting Starlette...")
try:
    starlette_datas, starlette_binaries, starlette_hiddenimports = collect_all('starlette')
    datas += starlette_datas
    binaries += starlette_binaries
    hiddenimports += starlette_hiddenimports
    print("  ✓ Starlette")
except Exception as e:
    print(f"  ⚠ Starlette: {e}")

# Collect AI/ML libraries
print("\nCollecting AI/ML libraries...")
ai_packages = ['openai', 'cohere', 'langdetect']
for package in ai_packages:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
        print(f"  ✓ {package}")
    except Exception as e:
        print(f"  ⚠ {package}: {e}")

# Collect LightRAG (CRITICAL for RAG functionality)
print("\nCollecting LightRAG...")
try:
    lightrag_datas, lightrag_binaries, lightrag_hiddenimports = collect_all('lightrag')
    datas += lightrag_datas
    binaries += lightrag_binaries
    hiddenimports += lightrag_hiddenimports
    print("  ✓ LightRAG")
except Exception as e:
    print(f"  ⚠ LightRAG: {e}")

# Collect document processing libraries
print("\nCollecting document processing libraries...")
doc_packages = [
    'PyPDF2',      # PDF extraction
    'docx',        # Word documents
    'PIL',         # Image processing
    'pytesseract', # OCR
    'openpyxl',    # Excel files
    'pptx',        # PowerPoint
    'fitz'         # PyMuPDF
]
for package in doc_packages:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
        print(f"  ✓ {package}")
    except Exception as e:
        print(f"  ⚠ {package}: {e}")

# Collect HTTP/Network libraries
print("\nCollecting HTTP/Network libraries...")
network_packages = ['aiohttp', 'httpx', 'aiofiles']
for package in network_packages:
    try:
        pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hiddenimports
        print(f"  ✓ {package}")
    except Exception as e:
        print(f"  ⚠ {package}: {e}")

# Collect geocoding libraries
print("\nCollecting geocoding libraries...")
try:
    geopy_datas, geopy_binaries, geopy_hiddenimports = collect_all('geopy')
    datas += geopy_datas
    binaries += geopy_binaries
    hiddenimports += geopy_hiddenimports
    print("  ✓ geopy")
except Exception as e:
    print(f"  ⚠ geopy: {e}")

# Collect Google API libraries
print("\nCollecting Google API libraries...")
google_packages = [
    'google', 
    'google.auth', 
    'google.oauth2',
    'google_auth_oauthlib',
    'googleapiclient'
]
for package in google_packages:
    try:
        hiddenimports += collect_submodules(package)
        print(f"  ✓ {package}")
    except Exception as e:
        print(f"  ⚠ {package}: {e}")

# Additional critical hidden imports
print("\nAdding critical hidden imports...")
hiddenimports += [
    # Core dependencies
    'typing_extensions',
    'anyio',
    'sniffio',
    'h11',
    'httptools',
    'websockets',
    'click',
    'cryptography',
    'dotenv',
    'multipart',  # python-multipart
    
    # Date utilities
    'dateutil',
    'dateutil.parser',
    'dateutil.tz',
    
    # Additional starlette components
    'starlette.routing',
    'starlette.middleware',
    'starlette.middleware.cors',
    'starlette.responses',
    'starlette.requests',
    'starlette.exceptions',
]
print("  ✓ Critical hidden imports added")

# Add application modules (your backend code)
print("\nAdding application modules...")
app_modules = ['core', 'api', 'domain', 'infrastructure']
for module in app_modules:
    if os.path.exists(module):
        datas += [(module, module)]
        print(f"  ✓ {module}")
    else:
        print(f"  ⚠ {module} directory not found")

# Add .env.example if exists
if os.path.exists('.env.example'):
    datas += [('.env.example', '.')]
    print("  ✓ .env.example")
else:
    print("  ⚠ .env.example not found")

# ============================================================================
# Platform-specific configurations
# ============================================================================

print("\nConfiguring platform-specific settings...")

# Windows-specific
if sys.platform == 'win32':
    print("  Platform: Windows")
    try:
        magic_datas, magic_binaries, magic_hiddenimports = collect_all('magic')
        datas += magic_datas
        binaries += magic_binaries
        hiddenimports += magic_hiddenimports
        print("  ✓ python-magic-bin")
    except Exception as e:
        print(f"  ⚠ python-magic-bin: {e}")

# macOS-specific
elif sys.platform == 'darwin':
    print("  Platform: macOS")
    # python-magic should be installed via brew
    print("  ℹ Requires: brew install libmagic")

# Linux-specific
elif sys.platform.startswith('linux'):
    print("  Platform: Linux")
    print("  ℹ Requires: apt-get install libmagic1")

# ============================================================================
# Analysis
# ============================================================================

print("\n" + "=" * 60)
print("Running PyInstaller Analysis...")
print("=" * 60)

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
        # Exclude unnecessary packages to reduce size
        'tkinter',
        'matplotlib',
        'numpy',     # Only if not used by LightRAG
        'scipy',
        'pandas',    # Only if not used
        'notebook',
        'IPython',
        'jupyter',
        'pytest',    # Don't include tests in production
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# ============================================================================
# PYZ (Python Zip Archive)
# ============================================================================

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

# ============================================================================
# EXE (Executable)
# ============================================================================

# Determine console mode (True for debugging, False for production)
# Can be overridden via command line: pyinstaller main.spec -- --console
console_mode = False  # Set to True if backend won't start

# Safe icon handling
icon_path = None
if sys.platform == 'win32':
    if os.path.exists('icon.ico'):
        icon_path = 'icon.ico'
        print("\n✓ Using icon.ico")
    else:
        print("\n⚠ icon.ico not found, building without icon")

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    upx_exclude=[],
    runtime_tmpdir=None,
    console=console_mode,  # False = no console window (production)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,
)

print("\n" + "=" * 60)
print("Build Configuration:")
print("=" * 60)
print(f"Executable name: main{'exe' if sys.platform == 'win32' else ''}")
print(f"Console mode: {console_mode}")
print(f"UPX compression: Enabled")
print(f"Platform: {sys.platform}")
print(f"Icon: {icon_path if icon_path else 'None'}")
print("=" * 60)
print("\nBuild complete! Check dist/ directory for executable.")
print("=" * 60)

# ============================================================================
# USAGE INSTRUCTIONS
# ============================================================================

"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COVENANTRIX BACKEND BUILD INSTRUCTIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 BUILDING:
───────────

1. Install PyInstaller:
   pip install pyinstaller

2. Build the executable:
   pyinstaller main.spec

3. Test the executable:
   Windows: .\dist\main.exe
   Unix:    ./dist/main

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🐛 DEBUGGING:
───────────

If the backend doesn't start:

1. Enable console mode:
   - Edit this file: Set console_mode = True (line ~263)
   - Rebuild: pyinstaller main.spec
   - Run and check console output

2. Clean build:
   pyinstaller --clean main.spec

3. Verbose build:
   pyinstaller --log-level=DEBUG main.spec

4. Test imports manually:
   python -c "import fastapi; import uvicorn; import lightrag"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠️  COMMON ISSUES:
───────────────

ISSUE: Backend won't start (no window appears)
FIX: Set console_mode = True to see error messages

ISSUE: "Module not found" error
FIX: Add the module to hiddenimports list above

ISSUE: Large executable size (>200MB)
FIX: Add more packages to excludes list

ISSUE: Missing data files
FIX: Verify 'datas' includes all required files

ISSUE: LightRAG not working
FIX: Ensure lightrag-hku is installed: pip install lightrag-hku

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 ENVIRONMENT SETUP:
────────────────

The bundled executable will read configuration from:
1. .env file (same directory as executable)
2. System environment variables
3. Default values in core/config.py

Required environment variables:
- OPENAI_API_KEY (for AI features)
- Optional: COHERE_API_KEY, GOOGLE_API_KEY

Create .env file alongside the executable:
OPENAI_API_KEY=sk-...
SERVER_HOST=127.0.0.1
SERVER_PORT=8000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ VERIFICATION:
──────────────

After building, verify:
1. ✓ Executable exists in dist/
2. ✓ Executable runs without errors
3. ✓ Health check responds: http://127.0.0.1:8000/health
4. ✓ API documentation loads: http://127.0.0.1:8000/docs
5. ✓ File upload works
6. ✓ Chat functionality works

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 DEPLOYMENT:
─────────────

For Electron integration:
1. Build executable with this spec
2. Place in covenantrix-desktop/backend/
3. Electron's backend-manager.js will launch it automatically
4. No Python installation required on user's machine!

For standalone deployment:
1. Copy dist/main executable to target machine
2. Copy .env file with required API keys
3. Run the executable
4. Access API at http://127.0.0.1:8000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""