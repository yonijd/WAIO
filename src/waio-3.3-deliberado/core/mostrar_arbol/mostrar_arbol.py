# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import json
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

def mostrar_arbol_consola(ruta, prefijo="", es_ultimo=True, nivel=0, max_nivel=None, incluir_ocultos=False):
    if max_nivel is not None and nivel > max_nivel:
        return

    if not os.path.exists(ruta):
        print(f"ERROR: No existe: {ruta}")
        return

    if os.path.isfile(ruta):
        nombre = os.path.basename(ruta)
        try:
            print(f"{prefijo}-- {nombre}")
        except UnicodeEncodeError:
            print(f"{prefijo}-- [CARACTERES NO IMPRIMIBLES]")
        return

    try:
        elementos = os.listdir(ruta)
    except PermissionError:
        print(f"{prefijo}-- [SIN PERMISO]")
        return

    if not incluir_ocultos:
        elementos = [e for e in elementos if not e.startswith('.')]

    elementos.sort(key=lambda x: x.lower())

    for i, elem in enumerate(elementos):
        es_ultimo_elem = i == len(elementos) - 1
        ruta_completa = os.path.join(ruta, elem)

        try:
            if os.path.isdir(ruta_completa):
                if es_ultimo_elem:
                    print(f"{prefijo}-- {elem}/")
                    nuevo_prefijo = prefijo + "    "
                else:
                    print(f"{prefijo}+-- {elem}/")
                    nuevo_prefijo = prefijo + "|   "

                mostrar_arbol_consola(ruta_completa, nuevo_prefijo, es_ultimo_elem, nivel + 1, max_nivel, incluir_ocultos)
            else:
                if es_ultimo_elem:
                    print(f"{prefijo}-- {elem}")
                else:
                    print(f"{prefijo}+-- {elem}")
        except UnicodeEncodeError:
            print(f"{prefijo}-- [CARACTERES NO IMPRIMIBLES]")
        except RecursionError:
            print(f"{prefijo}-- [DEMASIADA PROFUNDIDAD]")
            return

def obtener_estructura_json(ruta, nivel=0, max_nivel=None, incluir_ocultos=False):
    if max_nivel is not None and nivel > max_nivel:
        return None

    if not os.path.exists(ruta):
        return None

    try:
        stats = os.stat(ruta)
        fecha_mod = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        fecha_mod = "DESCONOCIDO"

    if os.path.isfile(ruta):
        try:
            return {
                "nombre": os.path.basename(ruta),
                "tipo": "archivo",
                "tamano": stats.st_size if stats else 0,
                "modificado": fecha_mod
            }
        except:
            return {"nombre": os.path.basename(ruta), "tipo": "archivo", "error": "No se pudo leer"}

    try:
        elementos = os.listdir(ruta)
    except PermissionError:
        return {"nombre": os.path.basename(ruta), "tipo": "carpeta", "error": "Sin permiso"}

    if not incluir_ocultos:
        elementos = [e for e in elementos if not e.startswith('.')]

    elementos.sort(key=lambda x: x.lower())

    contenido = []
    for elem in elementos:
        ruta_completa = os.path.join(ruta, elem)
        try:
            sub = obtener_estructura_json(ruta_completa, nivel + 1, max_nivel, incluir_ocultos)
            if sub is not None:
                contenido.append(sub)
        except RecursionError:
            contenido.append({
                "nombre": elem,
                "tipo": "error",
                "error": "Profundidad maxima excedida"
            })

    return {
        "nombre": os.path.basename(ruta) or ruta,
        "tipo": "carpeta",
        "ruta": os.path.abspath(ruta),
        "tamano": stats.st_size if stats else 0,
        "modificado": fecha_mod,
        "contenido": contenido
    }

def guardar_json(estructura, nombre_base):
    nombre_archivo = f"tree_{nombre_base}.json"
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(estructura, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON guardado: {nombre_archivo}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo guardar JSON: {e}")
        return False

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['mostrar_arbol.py'] + args_list

    parser = argparse.ArgumentParser(
        description='Muestra la estructura de carpetas en forma de arbol',
        epilog='Ejemplo: mostrar_arbol.py --ruta=./WAIO --incluir_ocultos --profundidad=5'
    )
    parser.add_argument('--ruta', default='.', help='Ruta de la carpeta a analizar (default: .)')
    parser.add_argument('--profundidad', type=int, default=10, help='Profundidad maxima a mostrar (default: 10)')
    parser.add_argument('--incluir_ocultos', action='store_true', help='Incluir carpetas y archivos ocultos')
    parser.add_argument('--guardar', action='store_true', help='Guardar estructura en JSON')
    parser.add_argument('--formato', choices=['tree', 'json', 'ambos'], default='tree',
                       help='Formato de salida: tree (arbol), json (estructurado), ambos (default: tree)')
    parser.add_argument('--sin_colores', action='store_true', help='Desactivar colores (no aplica en esta version)')

    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    if not os.path.exists(ruta_resuelta):
        print(f"[ERROR] No existe la ruta: {ruta_resuelta}")
        sys.exit(1)

    ruta_abs = os.path.abspath(ruta_resuelta)
    nombre_base = os.path.basename(ruta_abs) or "raiz"

    print("=" * 60)
    print(f"  MOSTRADOR DE ESTRUCTURA - ARBOL")
    print("=" * 60)
    print(f"  Ruta: {ruta_abs}")
    print(f"  Profundidad: {args.profundidad}")
    print(f"  Incluir ocultos: {args.incluir_ocultos}")
    print(f"  Formato: {args.formato}")
    print("=" * 60)
    print()

    estructura = None
    if args.formato in ['json', 'ambos'] or args.guardar:
        print("  Generando estructura...")
        estructura = obtener_estructura_json(ruta_abs, max_nivel=args.profundidad, incluir_ocultos=args.incluir_ocultos)
        if estructura is None:
            print("[ERROR] No se pudo generar la estructura")
            return
        print("[OK] Estructura generada")
        print()

    if args.formato in ['tree', 'ambos']:
        print("  [ESTRUCTURA EN ARBOL]")
        print("-" * 60)
        print(f"/-- {nombre_base}/")
        mostrar_arbol_consola(
            ruta_abs,
            prefijo="",
            es_ultimo=True,
            nivel=0,
            max_nivel=args.profundidad,
            incluir_ocultos=args.incluir_ocultos
        )
        print("-" * 60)
        print()

    if args.formato == 'json':
        print("  [ESTRUCTURA EN JSON]")
        print("-" * 60)
        print(json.dumps(estructura, indent=2, ensure_ascii=False))
        print("-" * 60)
        print()

    if args.guardar and estructura is not None:
        guardar_json(estructura, nombre_base)

    print("=" * 60)
    print("  FIN DEL REPORTE")
    print("=" * 60)

if __name__ == "__main__":
    main()
