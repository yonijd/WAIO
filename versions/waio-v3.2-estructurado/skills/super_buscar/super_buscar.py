# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import time
import ast
from datetime import datetime
from pathlib import Path

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

def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def coincide_patron(nombre, patrones):
    for patron in patrones:
        if patron.startswith('*') and patron.endswith('*'):
            medio = patron[1:-1]
            if medio in nombre:
                return True
        elif patron.startswith('*'):
            if nombre.endswith(patron[1:]):
                return True
        elif patron.endswith('*'):
            if nombre.startswith(patron[:-1]):
                return True
        else:
            if nombre == patron:
                return True
    return False

def es_oculto(ruta):
    nombre = os.path.basename(ruta)
    return nombre.startswith('.')

def deberia_excluir(ruta, excluir_lista):
    for excl in excluir_lista:
        if excl in ruta:
            return True
    return False

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['super_buscar.py'] + args_list

    parser = argparse.ArgumentParser(description='Buscador recursivo de archivos')
    parser.add_argument('--ruta', default='.', help='Carpeta raiz donde buscar')
    parser.add_argument('--patron', required=True, help='Patron de busqueda (ej: *.py, config.*). Multiples separados por comas')
    parser.add_argument('--recursivo', action='store_true', default=True, help='Buscar en subcarpetas')
    parser.add_argument('--ocultos', action='store_true', help='Incluir archivos y carpetas ocultas')
    parser.add_argument('--excluir', help='Carpetas a excluir separadas por comas (ej: node_modules,__pycache__)')
    parser.add_argument('--limite_resultados', type=int, default=1000, help='Limite maximo de resultados')
    parser.add_argument('--guardar_log', action='store_true', help='Guardar resultado en archivo de log')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)
    ruta = Path(ruta_resuelta)

    if not ruta.exists():
        print(f"ERROR: La ruta no existe: {ruta_resuelta}")
        return
    if not ruta.is_dir():
        print(f"ERROR: La ruta no es una carpeta: {ruta_resuelta}")
        return

    patrones = [p.strip() for p in args.patron.split(',') if p.strip()]
    if not patrones:
        print("ERROR: Debes especificar al menos un patron de busqueda")
        return

    excluir_lista = [e.strip() for e in args.excluir.split(',')] if args.excluir else []

    print("=" * 80)
    print(f"   SUPER BUSCADOR v1.0")
    print("=" * 80)
    print(f"  Carpeta raiz : {ruta.absolute()}")
    print(f"  Patrones     : {', '.join(patrones)}")
    print(f"  Recursivo    : {args.recursivo}")
    print(f"  Ocultos      : {'Si' if args.ocultos else 'No'}")
    if excluir_lista:
        print(f"  Excluir      : {', '.join(excluir_lista)}")
    print(f"  Limite       : {args.limite_resultados} resultados")
    print("=" * 80)
    print()

    resultados = []
    total_revisados = 0
    start_time = time.time()

    if args.recursivo:
        walker = os.walk(ruta)
    else:
        walker = [(ruta, [], [f.name for f in ruta.iterdir() if f.is_file()])]

    for root, dirs, files in walker:
        if not args.ocultos:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

        if excluir_lista:
            dirs[:] = [d for d in dirs if not deberia_excluir(os.path.join(root, d), excluir_lista)]
            if deberia_excluir(root, excluir_lista):
                continue

        for file in files:
            total_revisados += 1
            if coincide_patron(file, patrones):
                ruta_completa = os.path.join(root, file)
                try:
                    stat = os.stat(ruta_completa)
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    resultados.append({
                        "nombre": file,
                        "ruta": root,
                        "tamano": size,
                        "modificado": mtime
                    })
                except PermissionError:
                    continue

                if len(resultados) >= args.limite_resultados:
                    print(f"WARNING: Se alcanzo el limite de {args.limite_resultados} resultados.")
                    break

        if len(resultados) >= args.limite_resultados:
            break

    elapsed = time.time() - start_time

    print()
    print("=" * 80)
    print(f"  RESULTADOS ({len(resultados)} archivos encontrados)")
    print("=" * 80)
    print()

    if resultados:
        print(f"{'NOMBRE':<35} {'RUTA':<30} {'TAMANO':>10}  {'MODIFICADO':<16}")
        print("-" * 90)
        for r in resultados[:100]:
            nombre = r['nombre'][:32] + '...' if len(r['nombre']) > 35 else r['nombre']
            ruta_short = r['ruta'][:27] + '...' if len(r['ruta']) > 30 else r['ruta']
            print(f"{nombre:<35} {ruta_short:<30} {format_size(r['tamano']):>10}  {r['modificado']:<16}")
        if len(resultados) > 100:
            print(f"... y {len(resultados) - 100} resultados mas")
    else:
        print("  No se encontraron coincidencias.")

    print()
    print("=" * 80)
    print(f"  RESUMEN:")
    print(f"  - Total archivos revisados: {total_revisados}")
    print(f"  - Total encontrados: {len(resultados)}")
    print(f"  - Tiempo de escaneo: {elapsed:.2f} seg")
    print("=" * 80)

    if args.guardar_log:
        try:
            log_dir = Path(os.environ["USERPROFILE"]) / ".waio" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            now = datetime.now()
            log_name = f"super_buscar_{now.strftime('%Y%m%d_%H%M%S')}.log"
            log_path = log_dir / log_name
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(f"SUPER BUSCADOR v1.0\n")
                f.write(f"Fecha: {now.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Carpeta: {ruta.absolute()}\n")
                f.write(f"Patron: {args.patron}\n")
                f.write(f"Archivos encontrados: {len(resultados)}\n\n")
                for r in resultados:
                    f.write(f"{r['nombre']} | {r['ruta']} | {format_size(r['tamano'])} | {r['modificado']}\n")
            print(f"[LOG] Guardado en: {log_path}")
        except Exception as e:
            print(f"[ERROR] No se pudo guardar log: {e}")

if __name__ == "__main__":
    main()
