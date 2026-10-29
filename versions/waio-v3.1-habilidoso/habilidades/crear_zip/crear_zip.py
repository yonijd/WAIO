import os
import sys
import argparse
import zipfile
from datetime import datetime

def crear_zip(origen, destino=None, incluir_subcarpetas=True, compresion=6):
    if not os.path.exists(origen):
        return f"ERROR: No existe: {origen}"
    
    if destino is None:
        nombre_base = os.path.basename(origen.rstrip('/\\'))
        destino = f"{nombre_base}.zip"
    
    if not destino.endswith('.zip'):
        destino += '.zip'
    
    try:
        with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED, compresslevel=compresion) as zipf:
            if os.path.isfile(origen):
                arcname = os.path.basename(origen)
                zipf.write(origen, arcname)
                print(f"[OK] Archivo agregado: {arcname}")
            else:
                total_archivos = 0
                for root, dirs, files in os.walk(origen):
                    if not incluir_subcarpetas and root != origen:
                        continue
                    for file in files:
                        ruta_completa = os.path.join(root, file)
                        arcname = os.path.relpath(ruta_completa, os.path.dirname(origen))
                        zipf.write(ruta_completa, arcname)
                        total_archivos += 1
                        if total_archivos % 50 == 0:
                            print(f"  {total_archivos} archivos agregados...")
                print(f"[OK] Total archivos comprimidos: {total_archivos}")
        
        tamaño = os.path.getsize(destino)
        return f"[OK] ZIP creado: {destino}  Tamaño: {tamaño} bytes ({tamaño/1024:.2f} KB)"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Crea un archivo ZIP desde una carpeta o archivo')
    parser.add_argument('--origen', required=True, help='Ruta de la carpeta o archivo a comprimir')
    parser.add_argument('--destino', help='Ruta de destino del ZIP (opcional)')
    parser.add_argument('--sin_subcarpetas', action='store_true', help='No incluir subcarpetas')
    parser.add_argument('--compresion', type=int, default=6, choices=range(0, 10), help='Nivel de compresion (0-9, default: 6)')
    args = parser.parse_args()
    
    resultado = crear_zip(
        args.origen,
        args.destino,
        not args.sin_subcarpetas,
        args.compresion
    )
    print(resultado)

if __name__ == "__main__":
    main()