#!/bin/bash
# Retira (o restaura) el R y el JAGS instalados en el equipo de compilación, para comprobar que
# EasySEM funciona solo con su R y su JAGS portables.
# Uso:  bash linux/retirar_R_JAGS_sistema.sh retirar|restaurar
set -euo pipefail
OFF=/tmp/easysem_sistema_off
case "$1" in
  retirar)
    sudo mkdir -p "$OFF/jags"
    sudo mv /opt/R "$OFF/R"
    sudo mv /usr/local/lib/libjags* /usr/local/lib/libjrmath* /usr/local/lib/JAGS \
            /usr/local/libexec/jags-terminal /usr/local/bin/jags "$OFF/jags/"
    ;;
  restaurar)
    sudo mv "$OFF/R" /opt/R
    sudo mv "$OFF"/jags/libjags* "$OFF"/jags/libjrmath* "$OFF/jags/JAGS" /usr/local/lib/
    sudo mv "$OFF/jags/jags-terminal" /usr/local/libexec/
    sudo mv "$OFF/jags/jags" /usr/local/bin/
    ;;
  *) echo "Uso: $0 retirar|restaurar"; exit 2 ;;
esac
sudo ldconfig
echo "R y JAGS del sistema: $1 (hecho)"
