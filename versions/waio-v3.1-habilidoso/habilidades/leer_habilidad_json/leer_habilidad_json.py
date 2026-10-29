import os
import sys
import json
from pathlib import Path

def leer_habilidad_json(nombre):
    waio_dir = Path(os.environ.get("USERPROFILE", ".")) / ".waio"
    ruta_json = waio_dir / "habilidades" / nombre / f"{nombre}.json"
    
    if not ruta_json.exists():
        return {"error": f"Habilidad no encontrada: {nombre}"}
    
    try:
        with open(ruta_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Error al leer JSON: {str(e)}"}

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Debes especificar el nombre de la habilidad")
        print("  Ejemplo: python leer_habilidad_json.py abrir_programa")
        return
    
    nombre = sys.argv[1]
    resultado = leer_habilidad_json(nombre)
    
    if isinstance(resultado, dict) and "error" in resultado:
        print(f"[ERROR] {resultado['error']}")
    else:
        print(json.dumps(resultado, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()