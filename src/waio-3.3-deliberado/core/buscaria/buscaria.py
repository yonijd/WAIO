# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import json
import ast
import time
from datetime import datetime
from pathlib import Path

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

def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def coincide_patron(nombre, patrones, case_sensitive=False):
    nombre_cmp = nombre if case_sensitive else nombre.lower()
    for patron in patrones:
        p = patron if case_sensitive else patron.lower()
        if p.startswith('*') and p.endswith('*'):
            if p[1:-1] in nombre_cmp:
                return True
        elif p.startswith('*'):
            if nombre_cmp.endswith(p[1:]):
                return True
        elif p.endswith('*'):
            if nombre_cmp.startswith(p[:-1]):
                return True
        else:
            if nombre_cmp == p:
                return True
    return False

def deberia_excluir(ruta, excluir_lista):
    for excl in excluir_lista:
        if excl in ruta:
            return True
    return False

def parsear_fecha(s, fin_dia=False):
    if not s:
        return None
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
        if fin_dia:
            dt = dt.replace(hour=23, minute=59, second=59)
        return dt.timestamp()
    except:
        return None

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['buscaria.py'] + args_list

    parser = argparse.ArgumentParser(description='Buscador recursivo optimizado para IA (salida JSON)')
    parser.add_argument('--ruta', default='.', help='Carpeta raiz donde buscar (default: .)')
    parser.add_argument('--patron', required=True, help='Patrones separados por comas (ej: *.py,*.json)')
    parser.add_argument('--profundidad', type=int, default=0, help='Profundidad maxima (0 = sin limite)')
    parser.add_argument('--ocultos', action='store_true', help='Incluir archivos y carpetas ocultas')
    parser.add_argument('--excluir', help='Carpetas a excluir separadas por comas')
    parser.add_argument('--min_bytes', type=int, help='Tamano minimo en bytes')
    parser.add_argument('--max_bytes', type=int, help='Tamano maximo en bytes')
    parser.add_argument('--desde', help='Fecha minima (YYYY-MM-DD)')
    parser.add_argument('--hasta', help='Fecha maxima (YYYY-MM-DD, incluye todo el dia)')
    parser.add_argument('--orden', choices=['nombre', 'tamano', 'fecha'], default='nombre', help='Orden de resultados')
    parser.add_argument('--desc', action='store_true', help='Orden descendente')
    parser.add_argument('--case_sensitive', action='store_true', help='Busqueda sensible a mayusculas')
    parser.add_argument('--limite_resultados', type=int, default=1000, help='Limite maximo de resultados')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)
    ruta = Path(ruta_resuelta)

    respuesta = {
        "herramienta": "buscaria",
        "version": "1.0.1",
        "timestamp": datetime.now().isoformat()
    }

    if not ruta.exists():
        respuesta["status"] = "error"
        respuesta["mensaje"] = f"La ruta no existe: {ruta_resuelta}"
        print(json.dumps(respuesta, ensure_ascii=True))
        sys.exit(1)

    if not ruta.is_dir():
        respuesta["status"] = "error"
        respuesta["mensaje"] = f"La ruta no es una carpeta: {ruta_resuelta}"
        print(json.dumps(respuesta, ensure_ascii=True))
        sys.exit(1)

    patrones = [p.strip() for p in args.patron.split(',') if p.strip()]
    if not patrones:
        respuesta["status"] = "error"
        respuesta["mensaje"] = "Debes especificar al menos un patron"
        print(json.dumps(respuesta, ensure_ascii=True))
        sys.exit(1)

    excluir_lista = [e.strip() for e in args.excluir.split(',')] if args.excluir else []
    desde_ts = parsear_fecha(args.desde)
    hasta_ts = parsear_fecha(args.hasta, fin_dia=True)

    resultados = []
    total_revisados = 0
    limite_alcanzado = False
    start_time = time.time()

    for root, dirs, files in os.walk(ruta):
        if args.profundidad > 0:
            rel = os.path.relpath(root, ruta)
            nivel = 0 if rel == '.' else rel.count(os.sep) + 1
            if nivel >= args.profundidad:
                dirs[:] = []
                continue

        if not args.ocultos:
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            files = [f for f in files if not f.startswith('.')]

        if excluir_lista:
            dirs[:] = [d for d in dirs if not deberia_excluir(os.path.join(root, d), excluir_lista)]
            if deberia_excluir(root, excluir_lista):
                continue

        for file in files:
            total_revisados += 1
            if not coincide_patron(file, patrones, args.case_sensitive):
                continue

            ruta_completa = os.path.join(root, file)
            try:
                stat = os.stat(ruta_completa)
            except (PermissionError, OSError):
                continue

            size = stat.st_size
            mtime = stat.st_mtime

            if args.min_bytes is not None and size < args.min_bytes:
                continue
            if args.max_bytes is not None and size > args.max_bytes:
                continue
            if desde_ts is not None and mtime < desde_ts:
                continue
            if hasta_ts is not None and mtime > hasta_ts:
                continue

            resultados.append({
                "nombre": file,
                "ruta_relativa": os.path.relpath(root, ruta),
                "ruta_completa": ruta_completa,
                "tamano_bytes": size,
                "tamano_human": format_size(size),
                "modificado": datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "modificado_ts": mtime
            })

            if len(resultados) >= args.limite_resultados:
                limite_alcanzado = True
                break

        if limite_alcanzado:
            break

    if args.orden == 'nombre':
        resultados.sort(key=lambda x: x['nombre'].lower(), reverse=args.desc)
    elif args.orden == 'tamano':
        resultados.sort(key=lambda x: x['tamano_bytes'], reverse=args.desc)
    elif args.orden == 'fecha':
        resultados.sort(key=lambda x: x['modificado_ts'], reverse=args.desc)

    for r in resultados:
        del r['modificado_ts']

    elapsed = time.time() - start_time

    respuesta["status"] = "ok"
    respuesta["ruta"] = str(ruta.absolute())
    respuesta["patrones"] = patrones
    respuesta["orden"] = args.orden
    respuesta["desc"] = args.desc
    respuesta["limite_alcanzado"] = limite_alcanzado
    respuesta["total_revisados"] = total_revisados
    respuesta["total_encontrados"] = len(resultados)
    respuesta["tiempo_segundos"] = round(elapsed, 3)
    respuesta["resultados"] = resultados

    print(json.dumps(respuesta, ensure_ascii=True))

if __name__ == "__main__":
    main()
