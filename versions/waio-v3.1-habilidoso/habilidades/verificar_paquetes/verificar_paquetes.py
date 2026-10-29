import sys
import subprocess
import os
import importlib

def verificar_con_pip(paquete):
    try:
        resultado = subprocess.run(
            ["pip", "show", paquete],
            capture_output=True,
            text=True,
            timeout=5
        )
        if resultado.returncode == 0:
            for linea in resultado.stdout.splitlines():
                if linea.startswith("Version:"):
                    return True, linea.split(":")[1].strip()
            return True, "instalado"
        return False, None
    except:
        return False, None

def verificar_con_import(paquete):
    try:
        modulo = importlib.import_module(paquete)
        version = getattr(modulo, "__version__", "desconocida")
        return True, version
    except ImportError:
        return False, None

def verificar_carpeta(paquete):
    try:
        import site
        for dir in site.getsitepackages():
            ruta = os.path.join(dir, paquete)
            if os.path.isdir(ruta):
                return True, ruta
            ruta_alt = os.path.join(dir, paquete.replace("-", "_").replace(".", "_"))
            if os.path.isdir(ruta_alt):
                return True, ruta_alt
    except:
        pass
    return False, None

def main():
    paquetes = sys.argv[1:] if len(sys.argv) > 1 else [
        "numpy", "requests", "rich", "tqdm",
        "pywin32", "setuptools", "pillow"
    ]

    print("VERIFICANDO PAQUETES...")
    print("-" * 40)

    for pkg in paquetes:
        ok, version = verificar_con_pip(pkg)
        if ok:
            print(f"[OK] {pkg} (pip: {version})")
            continue

        ok, version = verificar_con_import(pkg)
        if ok:
            print(f"[OK] {pkg} (import: {version})")
            continue

        ok, ruta = verificar_carpeta(pkg)
        if ok:
            print(f"[CARPETA] {pkg} (copiado manualmente en {ruta})")
            continue

        print(f"[FALTA] {pkg}")

if __name__ == "__main__":
    main()