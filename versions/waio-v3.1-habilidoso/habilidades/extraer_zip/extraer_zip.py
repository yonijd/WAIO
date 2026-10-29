import os
import sys
import argparse
import zipfile

def extraer_zip(ruta_zip, destino=None, sobrescribir=False):
    if not os.path.exists(ruta_zip):
        return f"ERROR: No existe el ZIP: {ruta_zip}"
    
    if not zipfile.is_zipfile(ruta_zip):
        return f"ERROR: No es un archivo ZIP valido: {ruta_zip}"
    
    if destino is None:
        nombre_base = os.path.splitext(os.path.basename(ruta_zip))[0]
        destino = os.path.join(os.path.dirname(ruta_zip), nombre_base)
    
    if not os.path.exists(destino):
        os.makedirs(destino)
    
    try:
        with zipfile.ZipFile(ruta_zip, 'r') as zipf:
            if not sobrescribir:
                conflictos = []
                for info in zipf.infolist():
                    ruta_destino_archivo = os.path.join(destino, info.filename)
                    if os.path.exists(ruta_destino_archivo):
                        conflictos.append(info.filename)
                
                if conflictos:
                    print(f"[ADVERTENCIA] {len(conflictos)} archivos ya existen en la carpeta destino.")
                    print("  Usa --sobrescribir para reemplazarlos.")
                    for c in conflictos[:5]:
                        print(f"    - {c}")
                    if len(conflictos) > 5:
                        print(f"    ... y {len(conflictos)-5} mas.")
                    return "[CANCELADO] Extraccion cancelada."
            
            total = len(zipf.infolist())
            extraidos = 0
            for info in zipf.infolist():
                ruta_destino_archivo = os.path.join(destino, info.filename)
                if os.path.exists(ruta_destino_archivo) and not sobrescribir:
                    continue
                zipf.extract(info, destino)
                extraidos += 1
                if extraidos % 50 == 0:
                    print(f"  {extraidos}/{total} archivos extraidos...")
            
            print(f"[OK] ZIP extraido: {ruta_zip}")
            print(f"  Destino: {destino}")
            print(f"  Archivos extraidos: {extraidos}/{total}")
            
            print("")
            print("[ESTRUCTURA]")
            archivos_mostrados = 0
            for info in zipf.infolist()[:5]:
                if info.filename.endswith('/'):
                    print(f"  [CARPETA] {info.filename}")
                else:
                    print(f"  [ARCHIVO] {info.filename}")
                    archivos_mostrados += 1
            if len(zipf.infolist()) > 5:
                print(f"  ... y {len(zipf.infolist())-5} elementos mas.")
            
            return "[OK] Extraccion completada."
        
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Extrae un archivo ZIP en la carpeta destino')
    parser.add_argument('--zip', required=True, help='Ruta del archivo ZIP')
    parser.add_argument('--destino', help='Carpeta de destino (opcional)')
    parser.add_argument('--sobrescribir', action='store_true', help='Sobrescribir archivos existentes')
    args = parser.parse_args()
    
    resultado = extraer_zip(args.zip, args.destino, args.sobrescribir)
    print(resultado)

if __name__ == "__main__":
    main()