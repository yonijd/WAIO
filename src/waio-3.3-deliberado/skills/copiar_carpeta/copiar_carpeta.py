# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import shutil
import ast

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

def copiar_carpeta(origen, destino, sobrescribir=False):
    if not os.path.exists(origen):
        return f"ERROR: La carpeta origen no existe: {origen}"

    if not os.path.isdir(origen):
        return f"ERROR: El origen no es una carpeta: {origen}"

    if os.path.exists(destino):
        if sobrescribir:
            try:
                shutil.rmtree(destino)
            except Exception as e:
                return f"ERROR: No se pudo eliminar la carpeta destino: {e}"
        else:
            return f"ERROR: La carpeta destino ya existe: {destino}. Usa --sobrescribir para reemplazarla."

    try:
        shutil.copytree(origen, destino)
        return f"[OK] Carpeta copiada: {origen} -> {destino}"
    except Exception as e:
        return f"ERROR al copiar carpeta: {e}"

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['copiar_carpeta.py'] + args_list

    parser = argparse.ArgumentParser(description='Copia una carpeta completa recursivamente')
    parser.add_argument('--origen', required=True, help='Ruta de la carpeta origen')
    parser.add_argument('--destino', required=True, help='Ruta de la carpeta destino')
    parser.add_argument('--sobrescribir', action='store_true', help='Sobrescribir si la carpeta destino ya existe')
    args = parser.parse_args()

    origen_resuelto = resolver_ruta(args.origen)
    destino_resuelto = resolver_ruta(args.destino)

    resultado = copiar_carpeta(origen_resuelto, destino_resuelto, args.sobrescribir)
    print(resultado)
    if isinstance(resultado, str) and resultado.startswith("ERROR:"):
        sys.exit(1)
    if isinstance(resultado, str) and resultado.startswith("ERROR:"):
        sys.exit(1)

if __name__ == "__main__":
    main()
