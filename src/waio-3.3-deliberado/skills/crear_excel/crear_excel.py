# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import sys
import subprocess
import os
import argparse
import json
import ast

try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

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

def parsear_datos(datos):
    if isinstance(datos, (list, tuple)):
        return list(datos)
    if not isinstance(datos, str):
        return None
    try:
        return json.loads(datos)
    except Exception:
        pass
    try:
        return ast.literal_eval(datos)
    except Exception:
        pass
    return None

def crear_excel(ruta_salida, datos):
    try:
        parsed = parsear_datos(datos)

        if not isinstance(parsed, list) or not all(isinstance(fila, (list, tuple)) for fila in parsed):
            return "ERROR: Formato de datos no soportado. Esperaba lista de listas. Ej: [[\"Nombre\",\"Edad\"],[\"Juan\",25]]"

        wb = openpyxl.Workbook()
        hoja = wb.active

        for fila_idx, fila in enumerate(parsed, 1):
            for col_idx, valor in enumerate(fila, 1):
                hoja.cell(row=fila_idx, column=col_idx, value=valor)

        wb.save(ruta_salida)
        return f"[OK] Excel creado: {ruta_salida}"
    except Exception as e:
        return f"ERROR al crear Excel: {str(e)}"

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['crear_excel.py'] + args_list

    parser = argparse.ArgumentParser(description='Crea un archivo Excel (.xlsx) con los datos proporcionados')
    parser.add_argument('--ruta', required=True, help='Ruta de salida del archivo Excel (.xlsx)')
    parser.add_argument('--datos', required=True, help='Datos en formato JSON (lista de listas). Ej: [["Nombre","Edad"],["Juan",25]]')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)
    resultado = crear_excel(ruta_resuelta, args.datos)
    print(resultado)
    if isinstance(resultado, str) and resultado.startswith("ERROR:"):
        sys.exit(1)
    if isinstance(resultado, str) and resultado.startswith("ERROR"):
        sys.exit(1)

if __name__ == "__main__":
    main()
