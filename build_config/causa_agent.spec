# -*- mode: python ; coding: utf-8 -*-

import sys
from pathlib import Path

# Get the source directory
src_path = Path(__file__).parent.parent / 'src'

a = Analysis(
    [str(src_path / 'launcher.py')],  # Main launcher script
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Include all source files
        (str(src_path / '*.py'), '.'),
        # Include requirements for reference
        (str(src_path / 'requirements.txt'), '.'),
        # Include example environment file
        (str(src_path / '.env.example'), '.'),
        # Include static assets if any exist
        (str(src_path / 'static'), 'static') if (src_path / 'static').exists() else None,
    ],
    # Remove None entries
    datas=[item for item in datas if item is not None],
    hiddenimports=[
        'streamlit',
        'streamlit.web.cli',
        'streamlit.runtime.scriptrunner.script_runner',
        'pandas',
        'openai',
        'langchain',
        'langgraph',
        'PIL',
        'cryptography',
        'requests',
        'python_dotenv',
        'sentence_transformers',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy.random._examples',
    ],
    noarchive=False,
)

# Filter out system libraries that might cause issues
a.binaries = [x for x in a.binaries if not x[0].startswith('libSystem')]

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CAUSA-Agent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(src_path / 'assets' / 'icon.ico') if (src_path / 'assets' / 'icon.ico').exists() else None,
)

# macOS App Bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='CAUSA-Agent.app',
        icon=str(src_path / 'assets' / 'icon.icns') if (src_path / 'assets' / 'icon.icns').exists() else None,
        bundle_identifier='com.causa.agent',
        info_plist={
            'CFBundleDisplayName': 'CAUSA Social Media Agent',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': 'True',
            'LSUIElement': '1',  # Hide from dock initially
        }
    )