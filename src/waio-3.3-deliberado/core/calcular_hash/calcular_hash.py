# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import hashlib
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

def calcular_hash_archivo(ruta, algoritmo='sha256'):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"

    if os.path.isdir(ruta):
        return f"ERROR: Es una carpeta, no un archivo: {ruta}"

    try:
        hash_func = hashlib.new(algoritmo)
        with open(ruta, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"

def calcular_hash_carpeta(ruta, algoritmo='sha256'):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"

    if not os.path.isdir(ruta):
        return calcular_hash_archivo(ruta, algoritmo)

    resultados = {}
    for root, dirs, files in os.walk(ruta):
        for file in files:
            ruta_completa = os.path.join(root, file)
            hash_val = calcular_hash_archivo(ruta_completa, algoritmo)
            resultados[ruta_completa] = hash_val
    return resultados

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['calcular_hash.py'] + args_list

    parser = argparse.ArgumentParser(description='Calcula hash de archivos (SHA-256, MD5, etc.)')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo o carpeta')
    parser.add_argument('--algoritmo', default='sha256', help='Algoritmo: sha256, md5, sha1, etc. (default: sha256)')
    parser.add_argument('--resumen', action='store_true', help='Mostrar solo resumen (para carpetas)')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    if os.path.isfile(ruta_resuelta):
        resultado = calcular_hash_archivo(ruta_resuelta, args.algoritmo)
        print(f"[ARCHIVO] {os.path.basename(ruta_resuelta)}")
        print(f"  {args.algoritmo}: {resultado}")
        if isinstance(resultado, str) and resultado.startswith("ERROR:"):
            sys.exit(1)
        if isinstance(resultado, str) and resultado.startswith("ERROR:"):
            sys.exit(1)
    else:
        resultados = calcular_hash_carpeta(ruta_resuelta, args.algoritmo)

        if isinstance(resultados, str):
            print(resultados)
            sys.exit(1)

        if args.resumen:
            print(f"[CARPETA] {ruta_resuelta}")
            print(f"  Total archivos: {len(resultados)}")
            for archivo, hash_val in resultados.items():
                if isinstance(hash_val, str) and not hash_val.startswith("ERROR"):
                    print(f"  [OK] {os.path.basename(archivo)}: {hash_val[:16]}...")
                else:
                    print(f"  [ERROR] {os.path.basename(archivo)}: {hash_val}")
        else:
            for archivo, hash_val in resultados.items():
                print(f"[ARCHIVO] {archivo}")
                print(f"  {args.algoritmo}: {hash_val}")

if __name__ == "__main__":
    main()
