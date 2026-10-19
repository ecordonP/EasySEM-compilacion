# EasySEM para Linux (x86_64)

Versión de EasySEM para Linux con **R 4.6.1 y JAGS 4.3.2 portables**: las mismas funciones que la
versión portable de Windows. No usa ningún R, JAGS, Python ni Graphviz instalado en el equipo.

## Archivos

| Archivo | Función |
|---|---|
| `generar_semQt_linux.py` | Genera `semQt_linux.py` a partir de `semQt_portable.py` (no editar `semQt_linux.py` a mano) |
| `semQt_linux.spec` | Spec de PyInstaller (ejecutable `sem` + `_internal`, Graphviz y fuentes Liberation) |
| `requirements_linux.txt` | Paquetes de Python (mismas versiones que Windows y macOS) |
| `preparar_R_portable_linux.sh` | Copia el R y el JAGS de compilación y los hace portables |
| `reubicar_elf.py` | Incluye las bibliotecas del sistema que necesitan R y JAGS (`R/lib/ext`) y pone rutas relativas (`$ORIGIN`) |
| `retirar_R_JAGS_sistema.sh` | Retira el R y el JAGS de compilación para las pruebas |
| `probar_R_portable_linux.sh` | Prueba el R portable (lavaan, blavaan, rjags, runjags/jags-terminal) |
| `crear_paquetes_linux.sh` | Crea el AppImage y el .tar.gz |
| `instalar_easysem.sh` | Añade EasySEM al menú de aplicaciones (va dentro del .tar.gz) |
| `probar_distribuciones.sh` | Prueba los paquetes en Ubuntu 22.04/24.04, Debian 12 y Fedora 41 limpios (Docker) |

El flujo es `.github/workflows/compilar_linux.yml` (Ubuntu 22.04 de GitHub Actions). Se lanza a mano
(Actions → «Compilar EasySEM para Linux» → Run workflow) o con una etiqueta `v*`.

## Requisitos del equipo del usuario

- Linux x86_64 con glibc 2.35 o posterior: Ubuntu 22.04+, Linux Mint 21+, Debian 12+, Fedora 36+,
  openSUSE Leap 15.5+ y similares.
- Escritorio gráfico (X11 o Wayland). Las bibliotecas básicas (OpenGL, fontconfig, glib, xkbcommon)
  están en cualquier escritorio, igual que la orden `which` (R la usa al arrancar; solo falta en
  instalaciones mínimas o contenedores: `sudo dnf install which`).
- El AppImage necesita FUSE (en Ubuntu 24.04: `sudo apt install libfuse2t64`). Sin FUSE, use el
  .tar.gz o ejecute `./EasySEM-linux-x86_64.AppImage --appimage-extract-and-run`.

## Uso

- **AppImage**: `chmod +x EasySEM-linux-x86_64.AppImage` y abrirlo (doble clic o desde la terminal).
- **.tar.gz**: `tar xzf EasySEM-linux-x86_64.tar.gz`, después `EasySEM/instalar_easysem.sh` para
  añadirlo al menú, o abrir directamente `EasySEM/sem`.

La licencia (`EasySEM.lic`), `app_config.json` y el registro de errores se guardan en
`~/.local/share/EasySEM` (el AppImage es de solo lectura). El código del equipo de la licencia se
obtiene de `/etc/machine-id`.
