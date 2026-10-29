import os
import sys
import argparse
import hashlib

def calcular_hash_archivo(ruta, algoritmo='sha256'):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"
    
    if os.path.isdir(ruta):
        return f"ERROR: Es una carpeta, no un archivo: {ruta}"
    
    try:
        hash_func = hashlib.new(algoritmo)
        with open(ruta, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception as e:
        return f"ERROR: {str(e)}"

def calcular_hash_carpeta(ruta, algoritmo='sha256'):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"
    
    if not os.path.isdir(ruta):
        return calcular_hash_archivo(ruta, algoritmo)
    
    resultados = {}
    for root, dirs, files in os.walk(ruta):
        for file in files:
            ruta_completa = os.path.join(root, file)
            hash_val = calcular_hash_archivo(ruta_completa, algoritmo)
            resultados[ruta_completa] = hash_val
    return resultados

def main():
    parser = argparse.ArgumentParser(description='Calcula hash de archivos (SHA-256, MD5, etc.)')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo o carpeta')
    parser.add_argument('--algoritmo', default='sha256', help='Algoritmo: sha256, md5, sha1, etc. (default: sha256)')
    parser.add_argument('--resumen', action='store_true', help='Mostrar solo resumen (para carpetas)')
    args = parser.parse_args()
    
    if os.path.isfile(args.ruta):
        resultado = calcular_hash_archivo(args.ruta, args.algoritmo)
        print(f"[ARCHIVO] {os.path.basename(args.ruta)}")
        print(f"  {args.algoritmo}: {resultado}")
    else:
        resultados = calcular_hash_carpeta(args.ruta, args.algoritmo)
        
        if args.resumen:
            print(f"[CARPETA] {args.ruta}")
            print(f"  Total archivos: {len(resultados)}")
            for archivo, hash_val in resultados.items():
                if isinstance(hash_val, str) and not hash_val.startswith("ERROR"):
                    print(f"  [OK] {os.path.basename(archivo)}: {hash_val[:16]}...")
                else:
                    print(f"  [ERROR] {os.path.basename(archivo)}: {hash_val}")
        else:
            for archivo, hash_val in resultados.items():
                print(f"[ARCHIVO] {archivo}")
                print(f"  {args.algoritmo}: {hash_val}")

if __name__ == "__main__":
    main()