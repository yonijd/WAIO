import os
import sys
import subprocess
import shutil

def buscar_programa(nombre):
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    ruta = shutil.which(f"{nombre}.exe")
    if ruta:
        return ruta
    
    bases = [
        os.environ.get("ProgramFiles", "C:/Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", "") + "/Programs",
    ]
    
    for base in bases:
        if not base or not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            try:
                for file in files:
                    if file.lower() == f"{nombre}.exe":
                        return os.path.join(root, file)
            except PermissionError:
                continue
    
    return None

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Debes especificar un programa")
        print("  Ejemplo: abrir_programa.py notepad")
        return
    
    programa = sys.argv[1]
    ruta = buscar_programa(programa)
    
    if ruta:
        try:
            subprocess.Popen([ruta], shell=False)
            print(f"[OK] {programa} abierto desde: {ruta}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")
    else:
        print(f"[ERROR] No se encontró: {programa}")

if __name__ == "__main__":
    main()