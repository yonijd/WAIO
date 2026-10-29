import os
import sys
import argparse
import shutil

def copiar_carpeta(origen, destino, sobrescribir=False):
    if not os.path.exists(origen):
        return f"ERROR: La carpeta origen no existe: {origen}"
    
    if not os.path.isdir(origen):
        return f"ERROR: El origen no es una carpeta: {origen}"
    
    if os.path.exists(destino):
        if sobrescribir:
            try:
                shutil.rmtree(destino)
            except Exception as e:
                return f"ERROR: No se pudo eliminar la carpeta destino: {e}"
        else:
            return f"ERROR: La carpeta destino ya existe: {destino}. Usa --sobrescribir para reemplazarla."
    
    try:
        shutil.copytree(origen, destino)
        return f"[OK] Carpeta copiada: {origen} -> {destino}"
    except Exception as e:
        return f"ERROR al copiar carpeta: {e}"

def main():
    parser = argparse.ArgumentParser(description='Copia una carpeta completa recursivamente')
    parser.add_argument('--origen', required=True, help='Ruta de la carpeta origen')
    parser.add_argument('--destino', required=True, help='Ruta de la carpeta destino')
    parser.add_argument('--sobrescribir', action='store_true', help='Sobrescribir si la carpeta destino ya existe')
    args = parser.parse_args()
    
    resultado = copiar_carpeta(args.origen, args.destino, args.sobrescribir)
    print(resultado)

if __name__ == "__main__":
    main()