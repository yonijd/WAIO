# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import sys
import subprocess
import os
import argparse
import ast

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

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

def leer_pdf(ruta_pdf):
    if not os.path.exists(ruta_pdf):
        return f"ERROR: Archivo no existe: {ruta_pdf}"

    try:
        with open(ruta_pdf, 'rb') as archivo:
            lector = PyPDF2.PdfReader(archivo)
            paginas = len(lector.pages)
            texto_completo = []

            for i, pagina in enumerate(lector.pages, 1):
                texto = pagina.extract_text()
                if texto.strip():
                    texto_completo.append(f"--- PAGINA {i} ---")
                    texto_completo.append(texto.strip())
                else:
                    texto_completo.append(f"--- PAGINA {i} (sin texto o escaneada) ---")

            if not texto_completo:
                return f"PDF leido: {ruta_pdf}\nNo se pudo extraer texto. Puede ser un PDF escaneado."

            return f"PDF leido: {ruta_pdf}\nTotal de paginas: {paginas}\n\n" + "\n\n".join(texto_completo)
    except Exception as e:
        return f"ERROR al leer PDF: {str(e)}"

def main():
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    sys.argv = ['leer_pdf.py'] + args_list

    parser = argparse.ArgumentParser(description='Extrae texto de un archivo PDF')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo PDF')
    args = parser.parse_args()

    ruta_resuelta = resolver_ruta(args.ruta)

    resultado = leer_pdf(ruta_resuelta)
    print(resultado)

if __name__ == "__main__":
    main()
