"""Reubica binarios Mach-O (macOS) copiados fuera de su ubicación de instalación.

Uso:  python3 reubicar_macho.py <carpeta> <prefijo_antiguo>=<carpeta_nueva> [...]

Para cada biblioteca o ejecutable Mach-O dentro de <carpeta>:
  - cada dependencia que empieza por un <prefijo_antiguo> se cambia por la ruta relativa
    @loader_path/... del archivo correspondiente en <carpeta_nueva> (si existe);
  - el identificador (install name) de cada biblioteca .dylib pasa a ser @rpath/<nombre>;
  - el archivo se vuelve a firmar ad hoc (en Apple Silicon no se ejecuta código modificado sin firma).
Al final comprueba que ninguna dependencia apunta fuera de la carpeta, salvo bibliotecas del
sistema (/usr/lib, /System). Si alguna lo hace, lo muestra y termina con código 1.
"""
import os
import platform
import subprocess
import sys

# Arquitectura que se compila: la del Mac de compilación (arm64 en Apple Silicon, x86_64 en Intel),
# o la indicada en EASYSEM_ARCH
ARCH = os.environ.get("EASYSEM_ARCH") or platform.machine()

SYSTEM_PREFIXES = ("/usr/lib/", "/System/", "@rpath/", "@loader_path/", "@executable_path/")
# Dependencias opcionales que el R oficial de macOS tampoco incluye: XQuartz (/opt/X11) para los
# módulos X11, el editor de datos y cairo, y Tcl/Tk (/opt/R/<arquitectura>/lib/libtcl*, libtk*) para
# tcltk. EasySEM no usa esos módulos; solo funcionan si el usuario instala XQuartz. Se avisan, no se paran.
OPTIONAL_PREFIXES = ("/opt/X11/", f"/opt/R/{ARCH}/lib/libtcl", f"/opt/R/{ARCH}/lib/libtk")


def is_macho(path):
    try:
        with open(path, "rb") as f:
            head = f.read(8)
    except OSError:
        return False
    magic = head[:4]
    if magic == b"\xca\xfe\xba\xbe":
        # Binario universal (fat); los .class de Java tienen la misma firma pero un número grande
        return len(head) == 8 and int.from_bytes(head[4:8], "big") < 30
    return magic in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe")


def dependencies(path):
    # Solo la arquitectura que se compila; en binarios universales evita las cabeceras por arquitectura
    out = subprocess.run(["otool", "-arch", ARCH, "-L", path], capture_output=True, text=True).stdout.splitlines()
    deps = []
    for line in out[1:]:
        line = line.strip()
        if line:
            deps.append(line.split(" (compatibility")[0].strip())
    return deps


def install_id(path):
    out = subprocess.run(["otool", "-arch", ARCH, "-D", path], capture_output=True, text=True).stdout.splitlines()
    return out[1].strip() if len(out) > 1 else None


def main():
    root = os.path.realpath(sys.argv[1])
    mappings = []
    for arg in sys.argv[2:]:
        old, new = arg.split("=", 1)
        mappings.append((old.rstrip("/") + "/", os.path.realpath(new)))

    machos = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            path = os.path.join(dirpath, name)
            if not os.path.islink(path) and is_macho(path):
                machos.append(path)
    print(f"Binarios Mach-O: {len(machos)} (arquitectura {ARCH})")

    changed = 0
    for path in machos:
        args = []
        own_id = install_id(path) if path.endswith((".dylib", ".so")) else None
        if own_id and path.endswith(".dylib"):
            args += ["-id", "@rpath/" + os.path.basename(path)]
        for dep in dependencies(path):
            if dep == own_id or dep.startswith(SYSTEM_PREFIXES):
                continue
            if not any(dep.startswith(old) for old, _ in mappings):
                # Dependencia con otra ruta (p. ej. libgfortran de JAGS): usar la copia con el mismo
                # nombre que ya esté dentro de la carpeta, si existe
                candidates = [m for m in machos if os.path.basename(m) == os.path.basename(dep)]
                if candidates:
                    rel = os.path.relpath(candidates[0], os.path.dirname(path))
                    args += ["-change", dep, "@loader_path/" + rel]
                continue
            for old, new_root in mappings:
                if dep.startswith(old):
                    target = os.path.join(new_root, dep[len(old):])
                    if not os.path.exists(target):
                        # Misma biblioteca con otra ruta (p. ej. Versions/Current): buscar por nombre
                        candidates = [m for m in machos if os.path.basename(m) == os.path.basename(dep)]
                        target = candidates[0] if candidates else None
                    if target:
                        rel = os.path.relpath(os.path.realpath(target), os.path.dirname(path))
                        args += ["-change", dep, "@loader_path/" + rel]
                    break
        if args:
            subprocess.run(["chmod", "u+w", path], check=True)
            subprocess.run(["install_name_tool"] + args + [path], check=True,
                           stderr=subprocess.DEVNULL)
            changed += 1
        subprocess.run(["codesign", "--force", "--sign", "-", path], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f"Binarios modificados: {changed} (todos firmados ad hoc)")

    problems, optional = [], []
    for path in machos:
        for dep in dependencies(path):
            if dep.startswith(SYSTEM_PREFIXES) or dep == install_id(path):
                continue
            item = f"{os.path.relpath(path, root)} -> {dep}"
            (optional if dep.startswith(OPTIONAL_PREFIXES) else problems).append(item)
    if optional:
        modules = sorted({item.split(" -> ")[0] for item in optional})
        print("\nAviso: módulos opcionales que necesitan XQuartz o Tcl/Tk (EasySEM no los usa):")
        print("  " + "\n  ".join(modules))
    if problems:
        print("\nDEPENDENCIAS FUERA DE LA CARPETA (no reubicadas):")
        print("\n".join(sorted(set(problems))[:200]))
        sys.exit(1)
    print("Sin dependencias fuera de la carpeta.")


if __name__ == "__main__":
    main()
