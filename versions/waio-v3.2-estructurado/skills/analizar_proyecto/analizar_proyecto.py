# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import ast
import time
from pathlib import Path
from datetime import datetime
from collections import Counter

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

def format_size(b):
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.2f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.2f} MB"
    else:
        return f"{b/1024**3:.2f} GB"

def get_top_extensions(files, top=4):
    exts = [Path(f).suffix.lower() for f in files if Path(f).suffix]
    counted = Counter(exts).most_common(top)
    return " ".join([f"{e}({n})" for e, n in counted])

def analizar_proyecto(ruta, max_profundidad=3):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"

    if not os.path.isdir(ruta):
        return f"ERROR: No es una carpeta: {ruta}"

    resultado = []
    resultado.append("=" * 60)
    resultado.append("  ANALISIS DE PROYECTO")
    resultado.append("=" * 60)
    resultado.append(f"  Ruta: {os.path.abspath(ruta)}")
    resultado.append("")

    total_archivos = 0
    total_carpetas = 0
    extensiones = Counter()
    tamano_total = 0
    carpetas_profundidad = Counter()

    for root, dirs, files in os.walk(ruta):
        rel_path = os.path.relpath(root, ruta)
        if rel_path == '.':
            profundidad = 0
        else:
            profundidad = rel_path.count(os.sep) + 1

        carpetas_profundidad[profundidad] += 1
        total_carpetas += 1

        for file in files:
            total_archivos += 1
            ext = os.path.splitext(file)[1]
            if ext:
                extensiones[ext] += 1
            else:
                extensiones["sin_extension"] += 1

            try:
                ruta_completa = os.path.join(root, file)
                tamano_total += os.path.getsize(ruta_completa)
            except:
                pass

        if profundidad >= max_profundidad:
            dirs.clear()

    resultado.append("[RESUMEN GENERAL]")
    resultado.append("-" * 30)
    resultado.append(f"Total carpetas: {total_carpetas}")
    resultado.append(f"Total archivos: {total_archivos}")
    resultado.append(f"Tamaño total: {format_size(tamano_total)}")
    resultado.append("")

    resultado.append("[EXTENSIONES ENCONTRADAS]")
    resultado.append("-" * 30)
    for ext, count in extensiones.most_common(10):
        resultado.append(f"  {ext}: {count} archivos")
    resultado.append("")

    resultado.append("[PROFUNDIDAD DE CARPETAS]")
    resultado.append("-" * 30)
    for prof, count in sorted(carpetas_profundidad.items()):
        if prof == 0:
            resultado.append(f"  Raiz: {count} carpeta")
        else:
            resultado.append(f"  Nivel {prof}: {count} carpetas")

    resultado.append("=" * 60)
    return "\n".join(resultado)

def main():
    # Parsear manualmente para compatibilidad con WAIO
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    # Reconstruir sys.argv para argparse
    sys.argv = ['analizar_proyecto.py'] + args_list

    parser = argparse.ArgumentParser(description='Analiza la estructura de un proyecto')
    parser.add_argument('--ruta', default='.', help='Ruta del proyecto a analizar')
    parser.add_argument('--profundidad', type=int, default=3, help='Profundidad maxima a analizar (default: 3)')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    resultado = analizar_proyecto(ruta_resuelta, args.profundidad)
    print(resultado)

if __name__ == "__main__":
    main()