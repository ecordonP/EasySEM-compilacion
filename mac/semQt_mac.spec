# -*- mode: python ; coding: utf-8 -*-
#
# Spec para EasySEM en macOS (Apple Silicon, arm64), versión con R portable (semQt_mac.py).
#
# Compilar (en un Mac o en GitHub Actions, desde la carpeta CFA):
#   pyinstaller --noconfirm mac/semQt_mac.spec
#
# Resultado: dist/EasySEM.app. El R y el JAGS portables (mac/preparar_R_portable_mac.sh) NO se
# empaquetan aquí: el flujo .github/workflows/compilar_mac.yml los copia después en
# EasySEM.app/Contents/Resources/R y JAGS y vuelve a firmar la aplicación.

import os
import subprocess

from PyInstaller.utils.hooks import (
    collect_data_files,
    collect_dynamic_libs,
    collect_submodules,
    copy_metadata,
)

ROOT = os.path.dirname(SPECPATH)          # carpeta CFA
block_cipher = None

datas = []
binaries = []
hiddenimports = []


def collect_graphviz_binaries():
    """dot de Homebrew y sus complementos, para dibujar los diagramas sin Graphviz instalado.
    PyInstaller copia también las bibliotecas de las que dependen y reescribe sus rutas."""
    try:
        prefix = subprocess.run(["brew", "--prefix", "graphviz"], capture_output=True,
                                text=True, check=True).stdout.strip()
    except Exception:
        print('AVISO: Homebrew/graphviz no disponible; los diagramas necesitarán Graphviz instalado.')
        return [], []
    dot = os.path.join(prefix, 'bin', 'dot')
    plugin_dir = os.path.join(prefix, 'lib', 'graphviz')
    bins = [(dot, 'graphviz_bin')]
    data = []
    for name in sorted(os.listdir(plugin_dir)):
        src = os.path.join(plugin_dir, name)
        if name.startswith('libgvplugin_') and name.endswith('.dylib') and not os.path.islink(src):
            bins.append((src, 'graphviz_bin/graphviz'))
        elif name.startswith('config'):
            # Registro de complementos (lo genera «dot -c»); sin él dot no reconoce ningún formato
            data.append((src, 'graphviz_bin/graphviz'))
    return bins, data


# Metadatos que algunos paquetes consultan en tiempo de ejecución.
for pkg in [
    'pandas', 'numpy', 'scipy', 'statsmodels', 'semopy', 'pingouin', 'pyreadstat',
    'reportlab', 'graphviz', 'cryptography', 'Pillow', 'python-dateutil', 'python-docx',
    'rpy2', 'anthropic', 'PySide6', 'matplotlib', 'seaborn',
]:
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

# Datos estáticos de paquetes (plantillas, fuentes, recursos internos).
for pkg in ['reportlab', 'statsmodels', 'semopy', 'graphviz', 'PIL', 'docx', 'rpy2', 'pingouin']:
    try:
        datas += collect_data_files(pkg)
    except Exception:
        pass

# Librerías dinámicas/extensiones compiladas.
for pkg in ['pyreadstat', 'numpy', 'scipy', 'pandas', 'statsmodels', 'semopy', 'cryptography', 'PIL']:
    try:
        binaries += collect_dynamic_libs(pkg)
    except Exception:
        pass

_gv_bins, _gv_data = collect_graphviz_binaries()
binaries += _gv_bins
datas += _gv_data

# Imports dinámicos que el análisis estático no detecta.
for pkg in ['pyreadstat', 'semopy', 'pingouin', 'reportlab', 'graphviz', 'PIL', 'rpy2', 'anthropic', 'docx']:
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# Recursos de la aplicación: van a EasySEM.app/Contents/Resources (_get_script_path).
# config.CFA es opcional (clave de DeepSeek del autor); no se sube a GitHub por defecto.
APP_RESOURCES = ['config.CFA', 'licencia.md', 'logoEasyCFA.png', 'logoEasySEM.png',
                 'iconEasySEM.ico', 'iconEasyCFA.ico']
for res in APP_RESOURCES:
    path = os.path.join(ROOT, res)
    if os.path.exists(path):
        datas.append((path, '.'))

_excludes = [
    # La versión Qt no usa Tkinter
    'tkinter', '_tkinter', 'tkinter.test',
    'matplotlib.backends.backend_tkagg', 'matplotlib.backends._backend_tk',
    # Otros enlaces de Qt (evitan conflictos con PySide6)
    'PyQt5', 'PyQt6', 'PySide2',
    # Módulos de Qt que la aplicación no usa
    'PySide6.QtWebEngineCore', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineQuick',
    'PySide6.Qt3DCore', 'PySide6.Qt3DRender', 'PySide6.QtQuick', 'PySide6.QtQml',
    'PySide6.QtMultimedia', 'PySide6.QtCharts', 'PySide6.QtDataVisualization',
    'PySide6.QtTest', 'PySide6.QtDesigner',
    # Entornos interactivos y frameworks de test de terceros
    'IPython', 'ipykernel', 'ipywidgets', 'jupyter', 'notebook', 'nbformat', 'nbconvert',
    'nbclient', 'tornado', 'zmq', 'pyzmq', 'pytest', '_pytest',
    'scipy._lib.tests', 'statsmodels.sandbox',
    # Solo Windows
    'winreg', '_winapi',
]

a = Analysis(
    [os.path.join(ROOT, 'semQt_mac.py')],
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=_excludes,
    noarchive=False,
    optimize=0,
    cipher=block_cipher,
)

# Programa ofuscado con PyArmor en Windows (ofuscar_mac_linux.py -> obf_mac/), como la
# compilación de Windows. EASYSEM_SIN_OFUSCAR=1 compila sin ofuscar (solo para depurar).
import sys
sys.path.insert(0, ROOT)
from pyarmor_spec import apply_obfuscated
apply_obfuscated(a, os.path.join(ROOT, 'obf_mac'), 'semQt_mac.py')

# R se distribuye como R portable dentro de la aplicación. rpy2 se usa en modo ABI (abre
# libR.dylib del portable con dlopen): no se empaqueta ninguna biblioteca del R de compilación.
a.binaries = [b for b in a.binaries
              if not os.path.basename(b[0]).startswith(('libR.', 'libRblas', 'libRlapack'))]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sem',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch='arm64',          # Apple Silicon: M1, M2, M3, M4, M5...
    codesign_identity=None,       # firma ad hoc; la definitiva la hace el flujo de GitHub
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='EasySEM',
)

app = BUNDLE(
    coll,
    name='EasySEM.app',
    icon=os.path.join(ROOT, 'iconEasySEM.ico'),   # PyInstaller lo convierte a .icns con Pillow
    bundle_identifier='es.ugr.easysem',
    version='1.2.0',
    info_plist={
        'CFBundleName': 'EasySEM',
        'CFBundleDisplayName': 'EasySEM',
        'CFBundleShortVersionString': '1.2.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '13.0',
        'LSArchitecturePriority': ['arm64'],
        # La interfaz está diseñada con colores claros: no se adapta al modo oscuro
        'NSRequiresAquaSystemAppearance': True,
        'NSHumanReadableCopyright': 'Copyright (c) 2026 Eulogio Cordón Pozo',
    },
)
