# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import zipfile
import ast
from datetime import datetime

def obtener_workdir():
    wd = os.environ.get("WAIO_WORKDIR")
    if not wd:
        raise RuntimeError(
            "WAIO_WORKDIR no definida. "
            "Esta skill debe ejecutarse desde el motor de WAIO."
        )
    return wd

def resolver_ruta(ruta):
    workdir = obtener_workdir()
    if os.path.isabs(ruta):
        return ruta
    return os.path.join(workdir, ruta)

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

        tamano = os.path.getsize(destino)
        return f"[OK] ZIP creado: {destino}  Tamaño: {tamano} bytes ({tamano/1024:.2f} KB)"
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['crear_zip.py'] + args_list

    parser = argparse.ArgumentParser(description='Crea un archivo ZIP desde una carpeta o archivo')
    parser.add_argument('--origen', required=True, help='Ruta de la carpeta o archivo a comprimir')
    parser.add_argument('--destino', help='Ruta de destino del ZIP (opcional)')
    parser.add_argument('--sin_subcarpetas', action='store_true', help='No incluir subcarpetas')
    parser.add_argument('--compresion', type=int, default=6, choices=range(0, 10), help='Nivel de compresion (0-9, default: 6)')
    args = parser.parse_args()

    origen_resuelto = resolver_ruta(args.origen)
    destino_resuelto = resolver_ruta(args.destino) if args.destino else None

    resultado = crear_zip(
        origen_resuelto,
        destino_resuelto,
        not args.sin_subcarpetas,
        args.compresion
    )
    print(resultado)
    if isinstance(resultado, str) and resultado.startswith("ERROR:"):
        sys.exit(1)
    if isinstance(resultado, str) and resultado.startswith("ERROR:"):
        sys.exit(1)

if __name__ == "__main__":
    main()
