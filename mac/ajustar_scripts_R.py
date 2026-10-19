"""Quita las rutas fijas del framework de R en los scripts de texto del R portable (macOS).

Uso:  python3 ajustar_scripts_R.py <R_HOME_portable> <ruta_antigua> [<ruta_antigua> ...]

- bin/R: R_HOME_DIR deja de ser una ruta fija y se calcula a partir de la ubicación del script.
- bin/* (scripts) y etc/* (Renviron, ldpaths, Makeconf...): cada ruta antigua pasa a ${R_HOME}.
  En Renviron, un valor entre comillas simples no expande variables: '...' se cambia por "...".
"""
import os
import re
import sys

r_home = sys.argv[1]
old_paths = sorted({p.rstrip("/") for p in sys.argv[2:]}, key=len, reverse=True)


def is_text(path):
    try:
        with open(path, "rb") as f:
            chunk = f.read(4096)
    except OSError:
        return False
    return b"\0" not in chunk


changed = []
for sub in ("bin", "etc"):
    folder = os.path.join(r_home, sub)
    for name in sorted(os.listdir(folder)):
        path = os.path.join(folder, name)
        if os.path.islink(path) or not os.path.isfile(path) or not is_text(path):
            continue
        text = open(path, encoding="utf-8", errors="surrogateescape").read()
        new = text
        if sub == "bin" and name == "R":
            new = re.sub(r"^R_HOME_DIR=.*$",
                         lambda m: 'R_HOME_DIR="$(cd "$(dirname "$0")/.." && pwd -P)"',
                         new, count=1, flags=re.M)
        lines = new.split("\n")
        for k, line in enumerate(lines):
            # Las comparaciones con la ruta original («if test ... = /Library/...») se dejan:
            # con ${R_HOME} serían siempre ciertas y activarían ramas pensadas para esa ruta
            if line.lstrip().startswith("if test"):
                continue
            for old in old_paths:
                line = re.sub("'" + re.escape(old) + r"([^']*)'", lambda m: '"${R_HOME}' + m.group(1) + '"', line)
                line = line.replace(old, "${R_HOME}")
            lines[k] = line
        new = "\n".join(lines)
        if new != text:
            with open(path, "w", encoding="utf-8", errors="surrogateescape") as f:
                f.write(new)
            changed.append(f"{sub}/{name}")

print("Scripts ajustados:", ", ".join(changed) or "ninguno")
if "bin/R" not in changed:
    sys.exit("[ERROR] No se ha podido ajustar R_HOME_DIR en bin/R")
