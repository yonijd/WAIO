import sys
import subprocess

try:
    import PyPDF2
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "PyPDF2"])
    import PyPDF2

import os
import argparse

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
                    texto_completo.append(f"--- PÁGINA {i} ---")
                    texto_completo.append(texto.strip())
                else:
                    texto_completo.append(f"--- PÁGINA {i} (sin texto o escaneada) ---")
            
            if not texto_completo:
                return f"PDF leído: {ruta_pdf}\nNo se pudo extraer texto. Puede ser un PDF escaneado."
            
            return f"PDF leído: {ruta_pdf}\nTotal de páginas: {paginas}\n\n" + "\n\n".join(texto_completo)
    except Exception as e:
        return f"ERROR al leer PDF: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Extrae texto de un archivo PDF')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo PDF')
    args = parser.parse_args()
    
    resultado = leer_pdf(args.ruta)
    print(resultado)

if __name__ == "__main__":
    main()