#!/bin/bash
# Empaqueta la carpeta compilada de EasySEM para Linux en:
#   - EasySEM-linux-x86_64.AppImage  (un solo archivo ejecutable; no necesita instalación)
#   - EasySEM-linux-x86_64.tar.gz    (carpeta EasySEM + instalar_easysem.sh, sin FUSE)
#
# Uso:  bash linux/crear_paquetes_linux.sh <carpeta_EasySEM> <carpeta_salida>
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd -P)"
APP="$(cd "$1" && pwd -P)"
mkdir -p "$2"
OUT="$(cd "$2" && pwd -P)"
WORK="$(mktemp -d)"

# Icono PNG (256 px) a partir de iconEasySEM.ico
python3 - "$APP/iconEasySEM.ico" "$APP/easysem.png" <<'PY'
import sys
from PIL import Image
im = Image.open(sys.argv[1])
sizes = sorted(im.info.get("sizes", [im.size]))
im.size = sizes[-1]
im.convert("RGBA").resize((256, 256), Image.LANCZOS).save(sys.argv[2])
PY

# --- tar.gz con instalador para el menú de aplicaciones --------------------------------------
cp "$HERE/instalar_easysem.sh" "$APP/instalar_easysem.sh"
chmod +x "$APP/instalar_easysem.sh" "$APP/sem"
tar -C "$(dirname "$APP")" -czf "$OUT/EasySEM-linux-x86_64.tar.gz" "$(basename "$APP")"

# --- AppImage ------------------------------------------------------------------------------
APPDIR="$WORK/EasySEM.AppDir"
cp -a "$APP" "$APPDIR"
rm -f "$APPDIR/instalar_easysem.sh"
cat > "$APPDIR/AppRun" <<'APPRUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/sem" "$@"
APPRUN
chmod +x "$APPDIR/AppRun"
cp "$APP/easysem.png" "$APPDIR/easysem.png"
cat > "$APPDIR/easysem.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=EasySEM
Comment=Análisis factorial confirmatorio y modelos de ecuaciones estructurales
Exec=sem
Icon=easysem
Categories=Science;Education;Math;
Terminal=false
DESKTOP
TOOL="$WORK/appimagetool"
curl -fsSL -o "$TOOL" "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage"
chmod +x "$TOOL"
# Sin FUSE en el equipo de compilación: la herramienta se descomprime y se ejecuta
APPIMAGE_EXTRACT_AND_RUN=1 ARCH=x86_64 "$TOOL" --no-appstream "$APPDIR" "$OUT/EasySEM-linux-x86_64.AppImage"
rm -rf "$WORK"
ls -lh "$OUT"
