# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import argparse
import ast
import datetime

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

def extraer_metadatos(ruta):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"

    try:
        stats = os.stat(ruta)
        resultado = []
        resultado.append(f"=== METADATOS: {ruta} ===")
        resultado.append("")
        resultado.append(f"Nombre: {os.path.basename(ruta)}")
        resultado.append(f"Ruta: {os.path.abspath(ruta)}")
        resultado.append("")
        resultado.append(f"Tipo: {'Carpeta' if os.path.isdir(ruta) else 'Archivo'}")
        resultado.append(f"Tamaño: {stats.st_size} bytes")
        resultado.append(f"Tamaño (legible): {stats.st_size / 1024:.2f} KB")
        if stats.st_size > 1048576:
            resultado.append(f"Tamaño (legible): {stats.st_size / (1024*1024):.2f} MB")
        resultado.append("")

        resultado.append(f"Creacion: {datetime.datetime.fromtimestamp(stats.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}")
        resultado.append(f"Modificacion: {datetime.datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")
        resultado.append(f"Ultimo acceso: {datetime.datetime.fromtimestamp(stats.st_atime).strftime('%Y-%m-%d %H:%M:%S')}")
        resultado.append("")

        resultado.append(f"Permisos (octal): {oct(stats.st_mode)[-3:]}")
        resultado.append(f"Propietario UID: {stats.st_uid}")
        resultado.append(f"Grupo GID: {stats.st_gid}")

        if os.path.isfile(ruta):
            nombre = os.path.basename(ruta)
            if '.' in nombre:
                extension = nombre.split('.')[-1]
                resultado.append(f"Extension: {extension}")

        if os.path.isdir(ruta):
            try:
                items = os.listdir(ruta)
                resultado.append(f"Contenido: {len(items)} elementos")
                resultado.append(f"Archivos: {sum(1 for i in items if os.path.isfile(os.path.join(ruta, i)))}")
                resultado.append(f"Carpetas: {sum(1 for i in items if os.path.isdir(os.path.join(ruta, i)))}")
            except:
                pass

        return "\n".join(resultado)
    except Exception as e:
        return f"ERROR al extraer metadatos: {str(e)}"

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['metadatos.py'] + args_list

    parser = argparse.ArgumentParser(description='Extrae metadatos de un archivo o carpeta')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo o carpeta')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    resultado = extraer_metadatos(ruta_resuelta)
    print(resultado)

if __name__ == "__main__":
    main()
