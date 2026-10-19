#!/bin/bash
# Prueba EasySEM (tar.gz y AppImage) en contenedores de varias distribuciones limpias: sin R, JAGS,
# Python ni Graphviz, solo con las bibliotecas gráficas básicas de cualquier escritorio Linux.
# Uso:  bash linux/probar_distribuciones.sh <carpeta_con_los_paquetes>
set -uo pipefail
PKG="$(cd "$1" && pwd -P)"
DEB_LIBS="libgl1 libegl1 libfontconfig1 libxkbcommon0 libdbus-1-3 libx11-xcb1 libxrender1 libxext6"
RPM_LIBS="mesa-libGL mesa-libEGL fontconfig libxkbcommon glib2 dbus-libs libX11-xcb libXrender libXext which"
SELFTEST='echo 0123456789abcdef0123456789abcdef > /etc/machine-id
cd /tmp && tar xzf /paquetes/EasySEM-linux-x86_64.tar.gz
QT_QPA_PLATFORM=offscreen ./EasySEM/sem --easysem-selftest > /tmp/selftest.txt 2>&1
rc=$?; grep -E "\"ok\"|detalle" /tmp/selftest.txt | head -60
if [ $rc -ne 0 ]; then tail -n 60 /root/.local/share/EasySEM/easysem_errores.log 2>/dev/null
  echo "---- R portable (Rscript) ----"
  env RHOME=/tmp/EasySEM/R R_HOME=/tmp/EasySEM/R /tmp/EasySEM/R/bin/Rscript -e "print(.libPaths()); print(R.home()); library(utils); library(stats); cat(\"R OK\n\")" 2>&1 | tail -n 25
  echo "---- Bibliotecas no encontradas ----"
  find /tmp/EasySEM/R /tmp/EasySEM/JAGS -name "*.so*" -type f | while read -r f; do
    ldd "$f" 2>/dev/null | grep "not found" | sed "s|^|$f: |"; done | sort -u | head -40; fi
exit $rc'
APPIMAGE_TEST='echo 0123456789abcdef0123456789abcdef > /etc/machine-id
cp /paquetes/EasySEM-linux-x86_64.AppImage /tmp/ && cd /tmp
QT_QPA_PLATFORM=offscreen ./EasySEM-linux-x86_64.AppImage --appimage-extract-and-run --easysem-selftest > /tmp/selftest.txt 2>&1
rc=$?; grep -E "^  \"ok\"" /tmp/selftest.txt; [ $rc -ne 0 ] && tail -n 60 /tmp/selftest.txt
exit $rc'

failed=()
run() {   # nombre imagen instalación prueba
  echo "::group::$1 ($2)"
  if docker run --rm -v "$PKG:/paquetes:ro" "$2" bash -c "$3 >/dev/null 2>&1 || { echo 'Fallo al instalar las bibliotecas básicas'; exit 1; }
$4"; then
    echo "$1: OK"
  else
    failed+=("$1")
    echo "$1: FALLO"
  fi
  echo "::endgroup::"
}

APT="apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends"
run "Ubuntu 22.04" ubuntu:22.04 "$APT $DEB_LIBS libglib2.0-0" "$SELFTEST"
run "Ubuntu 24.04" ubuntu:24.04 "$APT $DEB_LIBS libglib2.0-0t64" "$SELFTEST"
run "Debian 12" debian:12 "$APT $DEB_LIBS libglib2.0-0" "$SELFTEST"
run "Fedora 41" fedora:41 "dnf install -y -q $RPM_LIBS tar gzip" "$SELFTEST"
run "AppImage en Ubuntu 24.04" ubuntu:24.04 "$APT $DEB_LIBS libglib2.0-0t64" "$APPIMAGE_TEST"

if [ ${#failed[@]} -gt 0 ]; then
  echo "Fallan: ${failed[*]}"
  exit 1
fi
echo "Todas las distribuciones: OK"
