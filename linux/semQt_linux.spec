# -*- mode: python ; coding: utf-8 -*-
#
# Spec para EasySEM en Linux (x86_64), versión con R portable (semQt_linux.py).
#
# Compilar (en Linux o en GitHub Actions, desde la carpeta CFA):
#   pyinstaller --noconfirm linux/semQt_linux.spec
#
# Resultado: dist/EasySEM (ejecutable «sem» + _internal). El R y el JAGS portables
# (linux/preparar_R_portable_linux.sh) NO se empaquetan aquí: el flujo
# .github/workflows/compilar_linux.yml los copia después en dist/EasySEM/R y JAGS.

import glob
import os
import re
import shutil

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
    """dot del sistema (apt install graphviz) y sus complementos, para dibujar los diagramas sin
    Graphviz instalado. PyInstaller incluye también las bibliotecas de las que dependen."""
    dot = shutil.which('dot')
    plugin_dirs = glob.glob('/usr/lib/*-linux-gnu/graphviz') + ['/usr/lib/graphviz', '/usr/lib64/graphviz']
    plugin_dir = next((d for d in plugin_dirs if os.path.isdir(d)), None)
    if not dot or not plugin_dir:
        print('AVISO: Graphviz no disponible; los diagramas necesitarán Graphviz instalado.')
        return [], []
    # En Ubuntu, /usr/bin/dot es un enlace a un ejecutable multiuso que actúa según el nombre
    # con que se llama: se copia con el nombre «dot»
    gv_tmp = os.path.join(ROOT, 'build', 'graphviz_dot')
    os.makedirs(gv_tmp, exist_ok=True)
    shutil.copy2(os.path.realpath(dot), os.path.join(gv_tmp, 'dot'))
    bins = [(os.path.join(gv_tmp, 'dot'), 'graphviz_bin')]
    data = []
    for name in sorted(os.listdir(plugin_dir)):
        src = os.path.join(plugin_dir, name)
        if name.startswith('libgvplugin_') and re.search(r'\.so\.\d+$', name):
            # El registro (config6a) cita los complementos por su nombre corto (.so.6), que en
            # Debian/Ubuntu es un enlace al archivo real (.so.6.0.0): se copia con ese nombre
            os.makedirs(os.path.join(gv_tmp, 'graphviz'), exist_ok=True)
            plugin = os.path.join(gv_tmp, 'graphviz', name)
            shutil.copy2(os.path.realpath(src), plugin)
            bins.append((plugin, 'graphviz_bin/graphviz'))
        elif name.startswith('config'):
            # Registro de complementos (lo genera «dot -c»); sin él dot no reconoce ningún formato
            data.append((src, 'graphviz_bin/graphviz'))
    return bins, data


def collect_pdf_fonts():
    """Fuentes Liberation (licencia SIL OFL; mismas medidas que Arial y Courier New) para los PDF."""
    found = []
    for pattern in ('/usr/share/fonts/truetype/liberation/LiberationSans-*.ttf',
                    '/usr/share/fonts/truetype/liberation/LiberationMono-*.ttf'):
        found += [(path, 'fonts') for path in glob.glob(pattern)]
    lic = '/usr/share/doc/fonts-liberation/copyright'
    if os.path.exists(lic):
        found.append((lic, 'fonts'))
    if not found:
        print('AVISO: fuentes Liberation no encontradas; los PDF usarán Helvetica.')
    return found


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
datas += collect_pdf_fonts()

# Imports dinámicos que el análisis estático no detecta.
for pkg in ['pyreadstat', 'semopy', 'pingouin', 'reportlab', 'graphviz', 'PIL', 'rpy2', 'anthropic', 'docx']:
    try:
        hiddenimports += collect_submodules(pkg)
    except Exception:
        pass

# pkg_resources (arranque de PyInstaller) -> jaraco.context -> backports.tarfile
hiddenimports += ['backports', 'backports.tarfile']

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
    [os.path.join(ROOT, 'semQt_linux.py')],
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

# Programa ofuscado con PyArmor en Windows (ofuscar_mac_linux.py -> obf_linux/), como la
# compilación de Windows. EASYSEM_SIN_OFUSCAR=1 compila sin ofuscar (solo para depurar).
import sys
sys.path.insert(0, ROOT)
from pyarmor_spec import apply_obfuscated
apply_obfuscated(a, os.path.join(ROOT, 'obf_linux'), 'semQt_linux.py')

# R se distribuye como R portable junto al ejecutable. rpy2 se usa en modo ABI (abre libR.so
# del portable con dlopen): no se empaqueta ninguna biblioteca del R de compilación.
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
