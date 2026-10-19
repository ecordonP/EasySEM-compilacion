# EasySEM para Mac con procesador Intel

Compilación de EasySEM para los Mac anteriores al chip de Apple (procesador Intel, x86_64).
Produce `EasySEM-macOS-intel.dmg`, con R y JAGS portables, igual que la versión para Apple Silicon.

## Qué hay aquí y qué se comparte

| Archivo | Uso |
|---|---|
| `mac_intel/semQt_mac_intel.spec` | Spec de PyInstaller para x86_64. Es igual que `mac/semQt_mac.spec`, salvo la arquitectura. |
| `.github/workflows/compilar_mac_intel.yml` | Flujo de GitHub Actions. Los flujos tienen que estar en `.github/workflows`. |
| `semQt_mac.py` | **Compartido** con Apple Silicon: el código Python no depende de la arquitectura. |
| `mac/*.sh`, `mac/*.py` | **Compartidos**: los scripts del R portable detectan la arquitectura del Mac de compilación. |
| `mac_intel/requirements_mac_intel.txt` | Paquetes de Python: los mismos que en Apple Silicon, salvo `cryptography`. Se usa la última versión con paquete precompilado para Intel, porque la 50.0.2 compilada en el Mac de GitHub choca con el `libssl` que incluye PyInstaller. |

## Compilar

En GitHub (`ecordonP/EasySEM`): Actions → «Compilar EasySEM para macOS Intel» → Run workflow.
Al subir una etiqueta `v*`, se compilan las dos versiones de Mac y ambos `.dmg` se publican en la
misma Release.

Mac de compilación: `macos-15-intel`, el último Mac Intel que ofrece GitHub. GitHub ha anunciado
que lo retirará (previsto para 2027). A partir de entonces solo podría compilarse en un Mac Intel
propio, como runner autoalojado.

## Mac compatibles

- Sistema mínimo: **macOS 13 (Ventura)**. Lo exigen PySide6 6.11 y los binarios de R 4.6.
- Mac Intel que pueden instalar macOS 13: MacBook Pro 2017 o posterior, MacBook Air 2018 o posterior,
  iMac 2017 o posterior, iMac Pro, Mac mini 2018 o posterior y Mac Pro 2019.
- Los Mac Intel más antiguos (2012–2016) se quedan en macOS 11 o 12. Para ellos habría que compilar con una
  versión anterior de PySide6 (Qt 6.5, compatible con macOS 11) y probar de nuevo toda la
  interfaz. No está preparado.

Los Mac con chip de Apple deben usar `EasySEM-macOS-arm64.dmg`. La versión Intel también
funcionaría en ellos con Rosetta 2, pero más lenta.

## Coste

Igual que en Apple Silicon, los minutos de macOS cuentan ×10. Los Mac Intel de GitHub son más lentos,
así que cada compilación tarda unos 15–25 minutos, es decir, 150–250 de los 3.000 minutos mensuales.
