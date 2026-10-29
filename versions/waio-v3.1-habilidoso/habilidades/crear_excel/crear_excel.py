import sys
import subprocess

try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

import os
import argparse
import json

def crear_excel(ruta_salida, datos):
    try:
        wb = openpyxl.Workbook()
        hoja = wb.active
        
        if isinstance(datos, str):
            try:
                datos = json.loads(datos)
            except:
                pass
        
        if isinstance(datos, list) and all(isinstance(fila, list) for fila in datos):
            for fila_idx, fila in enumerate(datos, 1):
                for col_idx, valor in enumerate(fila, 1):
                    hoja.cell(row=fila_idx, column=col_idx, value=valor)
        else:
            return f"ERROR: Formato de datos no soportado. Esperaba lista de listas. Ej: [[\"Nombre\",\"Edad\"],[\"Juan\",25]]"
        
        wb.save(ruta_salida)
        return f"[OK] Excel creado: {ruta_salida}"
    except Exception as e:
        return f"ERROR al crear Excel: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Crea un archivo Excel (.xlsx) con los datos proporcionados')
    parser.add_argument('--ruta', required=True, help='Ruta de salida del archivo Excel (.xlsx)')
    parser.add_argument('--datos', required=True, help='Datos en formato JSON (lista de listas). Ej: [["Nombre","Edad"],["Juan",25],["Ana",30]]')
    args = parser.parse_args()
    
    resultado = crear_excel(args.ruta, args.datos)
    print(resultado)

if __name__ == "__main__":
    main()