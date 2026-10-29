# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import hashlib
import ast
from collections import defaultdict

def obtener_workdir():
    try:
        with open("temp/workdir.txt", "r") as f:
            return f.read().strip()
    except:
        return os.getcwd()

def resolver_ruta(ruta):
    workdir = obtener_workdir()
    if os.path.isabs(ruta):
        return ruta
    return os.path.join(workdir, ruta)

def calcular_hash_archivo(ruta):
    try:
        hash_func = hashlib.sha256()
        with open(ruta, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except:
        return None

def buscar_duplicados(ruta, mostrar_tamano=False):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"

    if not os.path.isdir(ruta):
        return f"ERROR: No es una carpeta: {ruta}"

    por_tamano = defaultdict(list)
    total_archivos = 0

    for root, dirs, files in os.walk(ruta):
        for file in files:
            ruta_completa = os.path.join(root, file)
            try:
                tamano = os.path.getsize(ruta_completa)
                por_tamano[tamano].append(ruta_completa)
                total_archivos += 1
            except:
                pass

    duplicados = []
    for tamano, archivos in por_tamano.items():
        if len(archivos) < 2:
            continue

        por_hash = defaultdict(list)
        for archivo in archivos:
            hash_val = calcular_hash_archivo(archivo)
            if hash_val:
                por_hash[hash_val].append(archivo)

        for hash_val, archivos_hash in por_hash.items():
            if len(archivos_hash) > 1:
                duplicados.append({
                    'hash': hash_val,
                    'tamano': tamano,
                    'archivos': archivos_hash
                })

    return {
        'total_archivos': total_archivos,
        'duplicados': duplicados
    }

def main():
    # Parsear manualmente para compatibilidad con WAIO
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    # Reconstruir sys.argv para argparse
    sys.argv = ['buscar_duplicados.py'] + args_list

    parser = argparse.ArgumentParser(description='Busca archivos duplicados en una carpeta')
    parser.add_argument('--ruta', default='.', help='Ruta de la carpeta a analizar')
    parser.add_argument('--mostrar_tamano', action='store_true', help='Mostrar tamaño de los duplicados')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    resultado = buscar_duplicados(ruta_resuelta, args.mostrar_tamano)

    if isinstance(resultado, str):
        print(resultado)
        return

    print("[ANALIZANDO] " + ruta_resuelta)
    print(f"  Total archivos: {resultado['total_archivos']}")
    print("")

    if not resultado['duplicados']:
        print("No se encontraron duplicados.")
        return

    total_duplicados = sum(len(g['archivos']) for g in resultado['duplicados'])
    print(f"[DUPLICADOS] {total_duplicados} archivos en {len(resultado['duplicados'])} grupos")
    print("")

    for i, grupo in enumerate(resultado['duplicados'], 1):
        print(f"GRUPO {i}:")
        if args.mostrar_tamano:
            print(f"  Tamaño: {grupo['tamano']} bytes ({grupo['tamano']/1024:.2f} KB)")
        print(f"  Hash: {grupo['hash'][:16]}...")
        for archivo in grupo['archivos']:
            print(f"    {archivo}")
        print("")

    print("[RECOMENDACION] Usa 'eliminar_archivo' para borrar los duplicados que no necesites.")

if __name__ == "__main__":
    main()