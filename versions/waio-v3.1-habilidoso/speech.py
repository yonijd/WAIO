import os
import sys
import json
import subprocess
from pathlib import Path

def hablar(texto):
    try:
        comando = f'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{texto}")'
        subprocess.run(["powershell", "-Command", comando], capture_output=True)
        return True
    except Exception as e:
        print(f"Error al hablar: {e}")
        return False

def main():
    # Buscar en .waio/jsonout/
    waio_dir = Path(os.environ["USERPROFILE"]) / ".waio"
    jsonout_dir = waio_dir / "jsonout"
    
    if not jsonout_dir.exists():
        print(f"No existe la carpeta: {jsonout_dir}")
        return
    
    json_files = list(jsonout_dir.glob("*.json"))
    if not json_files:
        print("No hay archivos JSON en jsonout/")
        return
    
    ultimo = max(json_files, key=lambda x: x.stat().st_mtime)
    
    try:
        with open(ultimo, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        mensaje = data.get("contenido", "")
        
        if mensaje:
            print(f"Leyendo: {mensaje[:80]}...")
            hablar(mensaje)
        else:
            print("No hay mensaje para leer")
    except Exception as e:
        print(f"Error al leer JSON: {e}")

if __name__ == "__main__":
    main()