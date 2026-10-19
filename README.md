# EasySEM: compilación para macOS y Linux

Este repositorio **no contiene el código fuente** de EasySEM. Solo contiene lo necesario para
compilar las versiones portables (con R y JAGS incluidos) de macOS y Linux en GitHub Actions:

- `obf_mac/`, `obf_mac_intel/`, `obf_linux/`: el programa **ofuscado con PyArmor** para macOS
  Apple Silicon, macOS Intel y Linux x86_64.
- `semQt_mac.py` y `semQt_linux.py`: **solo las líneas `import`** del programa, que PyInstaller
  necesita para saber qué librerías incluir. No contienen el programa.
- Specs de PyInstaller, scripts para preparar R y JAGS portables y flujos de Actions.

El código fuente está en un repositorio privado; este se actualiza desde allí con
`publicar_compilacion.py`. **No edite este repositorio a mano.**

| Flujo | Máquina | Resultado |
|---|---|---|
| Compilar EasySEM para macOS | `macos-15` (M1-M5) | `EasySEM-macOS-arm64.dmg` |
| Compilar EasySEM para macOS Intel | `macos-15-intel` | `EasySEM-macOS-intel.dmg` |
| Compilar EasySEM para Linux | `ubuntu-22.04` | `EasySEM-linux-x86_64.AppImage` y `.tar.gz` |

EasySEM es software con licencia de uso (ver `licencia.md`). Las licencias van firmadas
digitalmente: el programa solo contiene la clave pública, que permite comprobarlas pero no
crearlas. © 2026 Eulogio Cordón Pozo, Universidad de Granada.
