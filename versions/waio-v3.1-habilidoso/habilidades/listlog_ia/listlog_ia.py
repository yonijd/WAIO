import os
import sys
import argparse
import json
import time
from pathlib import Path
from datetime import datetime

__version__ = "1.0.0"

def format_size(bytes_size):
    if bytes_size < 1024:
        return f"{bytes_size} B"
    elif bytes_size < 1024 * 1024:
        return f"{bytes_size / 1024:.2f} KB"
    elif bytes_size < 1024 * 1024 * 1024:
        return f"{bytes_size / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_size / (1024 * 1024 * 1024):.2f} GB"

def get_directory_info(target_path, max_depth=None, include_hidden=False, current_depth=0, detalles=False):
    if max_depth is not None and current_depth >= max_depth:
        try:
            stats = os.stat(target_path)
            return {
                "nombre": os.path.basename(target_path) or target_path,
                "tipo": "carpeta",
                "tamano_bytes": stats.st_size if detalles else 0,
                "modificado": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "profundidad": current_depth,
                "contenido": []
            }
        except:
            return {
                "nombre": os.path.basename(target_path) or target_path,
                "tipo": "carpeta",
                "profundidad": current_depth,
                "contenido": []
            }

    try:
        stats = os.stat(target_path)
        items = os.listdir(target_path)
    except (PermissionError, OSError):
        return {
            "nombre": os.path.basename(target_path) or target_path,
            "tipo": "carpeta",
            "error": "Sin permiso de lectura",
            "profundidad": current_depth
        }

    if not include_hidden:
        items = [item for item in items if not item.startswith('.')]

    items.sort(key=lambda x: (not os.path.isdir(os.path.join(target_path, x)), x.lower()))

    contenido = []
    total_archivos = 0
    total_carpetas = 0
    total_tamano = 0
    tipos = {}

    for item in items:
        item_path = os.path.join(target_path, item)
        try:
            item_stats = os.stat(item_path)
            is_dir = os.path.isdir(item_path)

            if is_dir:
                total_carpetas += 1
                sub = get_directory_info(item_path, max_depth, include_hidden, current_depth + 1, detalles)
                if sub:
                    contenido.append(sub)
                    if detalles and "resumen" in sub:
                        total_archivos += sub["resumen"].get("total_archivos", 0)
                        total_carpetas += sub["resumen"].get("total_carpetas", 0)
                        total_tamano += sub["resumen"].get("total_tamano_bytes", 0)
                        for t, count in sub["resumen"].get("tipos", {}).items():
                            tipos[t] = tipos.get(t, 0) + count
            else:
                total_archivos += 1
                ext = os.path.splitext(item)[1].lower()
                if detalles:
                    total_tamano += item_stats.st_size
                    if ext:
                        tipos[ext] = tipos.get(ext, 0) + 1
                    else:
                        tipos["sin_extension"] = tipos.get("sin_extension", 0) + 1

                entry = {
                    "nombre": item,
                    "tipo": "archivo",
                    "tamano_bytes": item_stats.st_size,
                    "modificado": datetime.fromtimestamp(item_stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                }
                if detalles:
                    entry["extension"] = ext or "sin_extension"
                contenido.append(entry)

        except (PermissionError, OSError):
            try:
                is_dir = os.path.isdir(item_path)
                contenido.append({
                    "nombre": item,
                    "tipo": "carpeta" if is_dir else "archivo",
                    "error": "No se pudo leer"
                })
            except:
                contenido.append({
                    "nombre": item,
                    "tipo": "desconocido",
                    "error": "No se pudo leer"
                })
            continue

    result = {
        "nombre": os.path.basename(target_path) or target_path,
        "tipo": "carpeta",
        "profundidad": current_depth,
        "modificado": datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "contenido": contenido
    }

    if detalles:
        result["tamano_bytes"] = stats.st_size
        result["ruta_absoluta"] = os.path.abspath(target_path)
        result["resumen"] = {
            "total_archivos": total_archivos,
            "total_carpetas": total_carpetas,
            "total_tamano_bytes": total_tamano,
            "total_tamano_human": format_size(total_tamano),
            "tipos": tipos
        }

    return result

def main():
    parser = argparse.ArgumentParser(description='Listlog optimizado para IA - Salida JSON')
    parser.add_argument('--ruta', default='.', help='Ruta del directorio a listar (default: .)')
    parser.add_argument('--profundidad', type=int, default=1, help='Profundidad maxima (default: 1, 0 = todos)')
    parser.add_argument('--incluir_ocultos', action='store_true', help='Incluir ocultos')
    parser.add_argument('--detalles', action='store_true', help='Calcular tamaños de carpetas y estadisticas')
    args = parser.parse_args()

    target_path = Path(args.ruta)
    if not target_path.exists():
        error = {"error": f"La ruta '{args.ruta}' no existe"}
        print(json.dumps(error, ensure_ascii=True))
        return

    if not target_path.is_dir():
        error = {"error": f"'{args.ruta}' no es una carpeta valida"}
        print(json.dumps(error, ensure_ascii=True))
        return

    start_time = time.time()
    max_depth = None if args.profundidad == 0 else args.profundidad

    estructura = get_directory_info(target_path, max_depth, args.incluir_ocultos, 0, args.detalles)
    elapsed_time = time.time() - start_time

    response = {
        "herramienta": "listlog_ia",
        "version": __version__,
        "ruta": str(target_path),
        "profundidad": args.profundidad,
        "incluir_ocultos": args.incluir_ocultos,
        "timestamp": datetime.now().isoformat(),
        "tiempo_segundos": round(elapsed_time, 3),
        "estructura": estructura
    }

    if args.detalles:
        response["ruta_absoluta"] = str(target_path.absolute())

    print(json.dumps(response, ensure_ascii=True))

if __name__ == "__main__":
    main()