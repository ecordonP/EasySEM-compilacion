#!/bin/bash
# Crea el R y el JAGS portables de EasySEM para Linux (x86_64) a partir de los instalados en el
# equipo de compilación (GitHub Actions, Ubuntu 22.04): R de Posit en /opt/R/<versión> (con los
# paquetes ya instalados por preparar_R_portable.R) y JAGS compilado en /usr/local.
#
# Uso:  bash linux/preparar_R_portable_linux.sh <carpeta_salida>
# Resultado: <carpeta_salida>/R (R_HOME portable) y <carpeta_salida>/JAGS
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd -P)"
mkdir -p "$1"
OUT="$(cd "$1" && pwd -P)"

# --- R -------------------------------------------------------------------------------------
RSRC="$(Rscript --vanilla -e 'cat(normalizePath(R.home()))')"
echo "R del sistema: $RSRC"
rm -rf "$OUT/R" "$OUT/JAGS"
# -L: los enlaces simbólicos se sustituyen por su contenido (algunos apuntan fuera de R_HOME)
cp -rL "$RSRC" "$OUT/R"

# Perfil y entorno propios (vacíos): EasySEM no lee los del usuario
: > "$OUT/R/etc/Renviron.easysem"
: > "$OUT/R/etc/Rprofile.easysem"

# --- JAGS ----------------------------------------------------------------------------------
JAGS_PREFIX=/usr/local
if [ ! -e "$JAGS_PREFIX/lib/libjags.so.4" ]; then
  echo "[ERROR] No se encuentra $JAGS_PREFIX/lib/libjags.so.4: ¿se ha compilado JAGS?"
  exit 1
fi
echo "JAGS del sistema: $JAGS_PREFIX"
echo "---- Lanzador original de JAGS ($JAGS_PREFIX/bin/jags) ----"; cat "$JAGS_PREFIX/bin/jags"; echo "----"
mkdir -p "$OUT/JAGS/lib" "$OUT/JAGS/libexec" "$OUT/JAGS/bin"
cp -a "$JAGS_PREFIX"/lib/libjags.so* "$JAGS_PREFIX"/lib/libjrmath.so* "$OUT/JAGS/lib/"
cp -a "$JAGS_PREFIX/lib/JAGS" "$OUT/JAGS/lib/JAGS"
# Los .la contienen rutas absolutas: sin ellos, libltdl carga directamente los .so de los módulos
find "$OUT/JAGS" -name '*.la' -delete
cp -p "$JAGS_PREFIX/libexec/jags-terminal" "$OUT/JAGS/libexec/"
cat > "$OUT/JAGS/bin/jags" <<'LAUNCHER'
#!/bin/sh
# Lanzador de JAGS portable (EasySEM): misma función que /usr/local/bin/jags, con rutas relativas
JAGS_HOME="$(cd "$(dirname "$0")/.." && pwd -P)"
LTDL_LIBRARY_PATH="$JAGS_HOME/lib/JAGS/modules-4${LTDL_LIBRARY_PATH:+:$LTDL_LIBRARY_PATH}"
export LTDL_LIBRARY_PATH
exec "$JAGS_HOME/libexec/jags-terminal" "$@"
LAUNCHER
chmod +x "$OUT/JAGS/bin/jags"

# --- Rutas fijas en scripts de texto y bibliotecas ------------------------------------------
python3 "$HERE/../mac/ajustar_scripts_R.py" "$OUT/R" "$RSRC"
python3 "$HERE/reubicar_elf.py" "$OUT" "$RSRC" "$JAGS_PREFIX/lib"

du -sh "$OUT/R" "$OUT/JAGS"
echo "EASYSEM_OK"
