# -*- coding: utf-8 -*-
"""
Ayuda para los specs de macOS y Linux: sustituye en el Analysis de PyInstaller el
programa por su versión ofuscada con PyArmor (generada en Windows con
ofuscar_mac_linux.py) y añade el runtime de PyArmor. Equivale al parche que hace
`pyarmor gen --pack` en Windows, que no se puede usar en GitHub Actions.

EASYSEM_SIN_OFUSCAR=1 compila sin ofuscar (solo para depurar).
"""
import os

RUNTIME_PKG = "pyarmor_runtime_011681"


def apply_obfuscated(a, obf_dir, script):
    if os.environ.get("EASYSEM_SIN_OFUSCAR") == "1":
        print("AVISO: EASYSEM_SIN_OFUSCAR=1, se compila el programa SIN ofuscar")
        return
    obf_script = os.path.join(obf_dir, script)
    runtime_init = os.path.join(obf_dir, RUNTIME_PKG, "__init__.py")
    runtime_so = os.path.join(obf_dir, RUNTIME_PKG, "pyarmor_runtime.so")
    for path in (obf_script, runtime_init, runtime_so):
        if not os.path.isfile(path):
            raise SystemExit(f"No se encuentra {path}: ejecute 'python ofuscar_mac_linux.py' en Windows.")
    found = False
    for i, (name, path, typecode) in enumerate(a.scripts):
        if os.path.basename(path) == script:
            a.scripts[i] = (name, obf_script, typecode)
            found = True
    if not found:
        raise SystemExit(f"El Analysis no contiene {script}")
    a.pure.append((RUNTIME_PKG, runtime_init, "PYMODULE"))
    a.binaries.append((os.path.join(RUNTIME_PKG, "pyarmor_runtime.so"), runtime_so, "EXTENSION"))
    print(f"Programa ofuscado: {obf_script}")
