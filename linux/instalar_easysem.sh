#!/bin/bash
# Añade EasySEM al menú de aplicaciones del usuario (no necesita permisos de administrador).
# Uso: descomprima EasySEM-linux-x86_64.tar.gz donde quiera conservarlo y ejecute
#      ./instalar_easysem.sh   desde la carpeta EasySEM.
# Para quitarlo del menú:  ./instalar_easysem.sh --desinstalar
set -e
DIR="$(cd "$(dirname "$0")" && pwd -P)"
APPS="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
DESKTOP="$APPS/easysem.desktop"
if [ "${1:-}" = "--desinstalar" ]; then
  rm -f "$DESKTOP"
  echo "EasySEM se ha quitado del menú (la carpeta $DIR no se ha borrado)."
  exit 0
fi
mkdir -p "$APPS"
cat > "$DESKTOP" <<DESKTOP_ENTRY
[Desktop Entry]
Type=Application
Name=EasySEM
Comment=Análisis factorial confirmatorio y modelos de ecuaciones estructurales
Exec="$DIR/sem"
Path=$DIR
Icon=$DIR/easysem.png
Categories=Science;Education;Math;
Terminal=false
DESKTOP_ENTRY
chmod +x "$DESKTOP" "$DIR/sem"
command -v update-desktop-database >/dev/null && update-desktop-database "$APPS" 2>/dev/null || true
echo "EasySEM añadido al menú de aplicaciones. También puede abrirlo con: $DIR/sem"
