"""Hace portables el R y el JAGS copiados en <carpeta> (Linux).

Uso:  python3 reubicar_elf.py <carpeta>        (contiene R/ y JAGS/)

1. Busca las bibliotecas del sistema que necesitan los binarios ELF de R y JAGS (dependencias
   directas e indirectas, según «readelf -d» y la resolución de «ldd») y las copia en R/lib/ext,
   salvo las que forman parte de cualquier Linux de escritorio (glibc, libstdc++, X11, OpenGL,
   fontconfig, glib...), que se toman del equipo del usuario.
2. Cambia la ruta de búsqueda (RUNPATH) de cada binario por rutas relativas ($ORIGIN) a
   R/lib, R/lib/ext y JAGS/lib, de modo que funcionen en cualquier carpeta sin LD_LIBRARY_PATH.
3. Comprueba que ninguna dependencia queda sin resolver ni apunta al R o JAGS del sistema.
Necesita patchelf.
"""
import os
import re
import shutil
import subprocess
import sys

# Bibliotecas que NO se incluyen: base de cualquier Linux de escritorio. Incluirlas (sobre todo
# glibc, libstdc++ y los controladores gráficos) causa fallos en distribuciones más nuevas.
EXCLUDE_PREFIXES = (
    "linux-vdso", "linux-gate", "ld-linux", "libc.so", "libm.so", "libmvec.so", "libdl.so",
    "libpthread.so", "librt.so", "libresolv.so", "libutil.so", "libanl.so", "libnsl.so",
    "libcrypt.so", "libBrokenLocale", "libnss_", "libthread_db", "libstdc++.so", "libgcc_s.so",
    "libGL.so", "libGLX", "libGLdispatch", "libEGL", "libOpenGL", "libGLES", "libdrm", "libgbm",
    "libX11.so", "libX11-xcb", "libxcb", "libXau", "libXdmcp", "libXext", "libXrender",
    "libfontconfig", "libfreetype", "libharfbuzz.so", "libexpat", "libz.so",
    "libglib-2.0", "libgobject-2.0", "libgio-2.0", "libgmodule-2.0", "libgthread-2.0",
    "libdbus-1", "libsystemd", "libudev", "libuuid", "libselinux", "libmount", "libblkid",
    "libasound", "libpulse", "libwayland",
)


def excluded(soname):
    return soname.startswith(EXCLUDE_PREFIXES)


def is_elf(path):
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"\x7fELF"
    except OSError:
        return False


def needed(path):
    out = subprocess.run(["readelf", "-d", path], capture_output=True, text=True).stdout
    return re.findall(r"\(NEEDED\)\s+Shared library: \[([^\]]+)\]", out)


def ldd_map(path, env):
    """soname -> ruta resuelta (None si «not found»)."""
    out = subprocess.run(["ldd", path], capture_output=True, text=True, env=env).stdout
    result = {}
    for line in out.splitlines():
        line = line.strip()
        m = re.match(r"(\S+) => (not found|(\S+) \(0x[0-9a-f]+\))", line)
        if m:
            result[m.group(1)] = None if m.group(2) == "not found" else m.group(3)
    return result


def main():
    root = os.path.realpath(sys.argv[1])
    r_lib = os.path.join(root, "R", "lib")
    jags_lib = os.path.join(root, "JAGS", "lib")
    ext = os.path.join(r_lib, "ext")
    os.makedirs(ext, exist_ok=True)
    own_dirs = [r_lib, ext, jags_lib]
    env = dict(os.environ, LD_LIBRARY_PATH=":".join(own_dirs))

    def scan():
        elfs = []
        for sub in ("R", "JAGS"):
            for dirpath, _dirs, files in os.walk(os.path.join(root, sub)):
                for name in files:
                    p = os.path.join(dirpath, name)
                    if not os.path.islink(p) and is_elf(p):
                        elfs.append(p)
        return elfs

    def inside(path):
        return os.path.realpath(path).startswith(root + os.sep)

    # 1. Copiar dependencias externas (cierre transitivo sin entrar en las excluidas)
    resolved = {}
    copied = []
    pending = scan()
    seen = set()
    while pending:
        path = pending.pop()
        if path in seen:
            continue
        seen.add(path)
        resolved.update({k: v for k, v in ldd_map(path, env).items() if v})
        for soname in needed(path):
            if excluded(soname):
                continue
            target = resolved.get(soname)
            if not target:
                target = ldd_map(path, env).get(soname)
            if not target or inside(target):
                continue
            dst = os.path.join(ext, soname)
            if not os.path.exists(dst):
                shutil.copy2(os.path.realpath(target), dst)
                os.chmod(dst, 0o755)
                copied.append(soname)
                pending.append(dst)
    print(f"Bibliotecas del sistema incluidas en R/lib/ext: {len(copied)}")
    print("  " + " ".join(sorted(copied)))

    # 2. RUNPATH relativo en todos los binarios
    #    Además de R/lib, R/lib/ext y JAGS/lib: las rutas $ORIGIN que ya tuviera el binario y la
    #    carpeta de cualquier dependencia incluida en un paquete de R (p. ej. libtbb.so de
    #    RcppParallel, que también usa blavaan)
    elfs = scan()
    in_tree = {}     # nombre de archivo (también enlaces simbólicos como libtbb.so) -> carpeta
    for sub in ("R", "JAGS"):
        for dirpath, _dirs, files in os.walk(os.path.join(root, sub)):
            for name in files:
                if ".so" in name:
                    in_tree.setdefault(name, dirpath)
    patched, failed = 0, []
    for path in elfs:
        folder = os.path.dirname(path)
        dirs = list(own_dirs)
        old = subprocess.run(["patchelf", "--print-rpath", path], capture_output=True, text=True).stdout.strip()
        for entry in filter(None, old.split(":")):
            if entry.startswith("$ORIGIN"):
                d = os.path.normpath(os.path.join(folder, entry[len("$ORIGIN"):].lstrip("/")))
                if d not in dirs:
                    dirs.append(d)
        for soname in needed(path):
            d = in_tree.get(soname)
            if d and d not in dirs:
                dirs.append(d)
        rpath = ":".join("$ORIGIN" + ("" if os.path.relpath(d, folder) == "." else "/" + os.path.relpath(d, folder))
                         for d in dirs)
        os.chmod(path, os.stat(path).st_mode | 0o200)
        run = subprocess.run(["patchelf", "--set-rpath", rpath, path], capture_output=True, text=True)
        if run.returncode == 0:
            patched += 1
        elif needed(path):
            failed.append(f"{os.path.relpath(path, root)}: {run.stderr.strip()}")
    print(f"Binarios ELF: {len(elfs)}; RUNPATH relativo en {patched}")
    if failed:
        print("No se ha podido cambiar el RUNPATH de:\n  " + "\n  ".join(failed))
        sys.exit(1)

    # 3. Verificación sin LD_LIBRARY_PATH: todo se resuelve dentro de la carpeta o en el sistema base
    clean_env = {k: v for k, v in os.environ.items() if k != "LD_LIBRARY_PATH"}
    problems = []
    forbidden = tuple(p for p in sys.argv[2:])   # p. ej. /opt/R /usr/local/lib
    for path in elfs:          # incluye R/lib/ext
        # Dependencias directas: las indirectas son directas de otro binario que también se revisa
        # (las de las bibliotecas del sistema base, como glib, las resuelve el propio sistema)
        resolved_here = ldd_map(path, clean_env)
        for soname in needed(path):
            target = resolved_here.get(soname)
            if excluded(soname):          # del sistema base (ld-linux aparece sin «=>» en ldd)
                continue
            if target is None:
                problems.append(f"{os.path.relpath(path, root)} -> {soname} (no encontrada)")
            elif forbidden and os.path.realpath(target).startswith(forbidden):
                problems.append(f"{os.path.relpath(path, root)} -> {target}")
            elif not inside(target) and not excluded(soname):
                problems.append(f"{os.path.relpath(path, root)} -> {target} (fuera de la carpeta)")
    if problems:
        print("\nDEPENDENCIAS SIN REUBICAR:")
        print("\n".join(sorted(set(problems))[:200]))
        sys.exit(1)
    print("Sin dependencias fuera de la carpeta (salvo las del sistema base).")


if __name__ == "__main__":
    main()
