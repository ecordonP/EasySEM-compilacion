#!/bin/bash
# Crea el R y el JAGS portables de EasySEM para macOS (Apple Silicon) a partir de los instalados
# en el Mac de compilación (GitHub Actions): R en /Library/Frameworks/R.framework (con los paquetes
# ya instalados por preparar_R_portable.R) y JAGS en /usr/local.
#
# Uso:  bash mac/preparar_R_portable_mac.sh <carpeta_salida>
# Resultado: <carpeta_salida>/R (R_HOME portable) y <carpeta_salida>/JAGS
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd -P)"
mkdir -p "$1"
OUT="$(cd "$1" && pwd -P)"

# --- R -------------------------------------------------------------------------------------
RSRC="$(cd /Library/Frameworks/R.framework/Versions/Current/Resources && pwd -P)"
echo "R del sistema: $RSRC"
rm -rf "$OUT/R" "$OUT/JAGS"
ditto "$RSRC" "$OUT/R"

# Enlaces simbólicos absolutos hacia el framework: sustituirlos por el contenido real
find "$OUT/R" -type l | while read -r link; do
  target="$(readlink "$link")"
  case "$target" in
    /Library/Frameworks/R.framework/*)
      rm "$link"
      if [ -d "$target" ]; then ditto "$target" "$link"; else cp -p "$target" "$link"; fi
      ;;
  esac
done

# Perfil y entorno propios (vacíos): EasySEM no lee los del usuario
: > "$OUT/R/etc/Renviron.easysem"
: > "$OUT/R/etc/Rprofile.easysem"

# --- JAGS ----------------------------------------------------------------------------------
LIBJAGS="$(find /usr/local /opt -name 'libjags.4.dylib' -not -path '*/R.framework/*' 2>/dev/null | head -1 || true)"
if [ -z "$LIBJAGS" ]; then
  echo "[ERROR] No se encuentra libjags.4.dylib: ¿se ha instalado JAGS?"
  exit 1
fi
JAGS_LIB="$(cd "$(dirname "$LIBJAGS")" && pwd -P)"
JAGS_PREFIX="$(dirname "$JAGS_LIB")"
echo "JAGS del sistema: $JAGS_PREFIX ($(lipo -archs "$LIBJAGS"))"
mkdir -p "$OUT/JAGS/lib" "$OUT/JAGS/libexec" "$OUT/JAGS/bin"
cp -a "$JAGS_LIB"/libjags*.dylib "$JAGS_LIB"/libjrmath*.dylib "$OUT/JAGS/lib/"
ditto "$JAGS_LIB/JAGS" "$OUT/JAGS/lib/JAGS"
cp -p "$JAGS_PREFIX/libexec/jags-terminal" "$OUT/JAGS/libexec/"
cat > "$OUT/JAGS/bin/jags" <<'EOF'
#!/bin/sh
# Lanzador de JAGS portable (EasySEM): misma función que /usr/local/bin/jags
JAGS_HOME="$(cd "$(dirname "$0")/.." && pwd -P)"
# Como el lanzador original: jags-terminal carga los módulos (basemod, bugs...) desde LTDL_LIBRARY_PATH
LTDL_LIBRARY_PATH="$JAGS_HOME/lib/JAGS/modules-4${LTDL_LIBRARY_PATH:+:$LTDL_LIBRARY_PATH}"
export LTDL_LIBRARY_PATH
exec "$JAGS_HOME/libexec/jags-terminal" "$@"
EOF
chmod +x "$OUT/JAGS/bin/jags"

# --- Reubicar binarios Mach-O y scripts de texto -----------------------------------------------
python3 "$HERE/ajustar_scripts_R.py" "$OUT/R" \
  "$RSRC" \
  "/Library/Frameworks/R.framework/Versions/Current/Resources" \
  "/Library/Frameworks/R.framework/Resources"

python3 "$HERE/reubicar_macho.py" "$OUT" \
  "$RSRC=$OUT/R" \
  "/Library/Frameworks/R.framework/Versions/Current/Resources=$OUT/R" \
  "/Library/Frameworks/R.framework/Resources=$OUT/R" \
  "$JAGS_LIB=$OUT/JAGS/lib" \
  "$JAGS_PREFIX/libexec=$OUT/JAGS/libexec"

du -sh "$OUT/R" "$OUT/JAGS"
echo "EASYSEM_OK"
