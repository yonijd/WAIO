import os
import sys
import argparse
import re
import shutil
from datetime import datetime

def editar_archivo(ruta, buscar, reemplazar, usar_regex=False, dry_run=False, backup=False):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"
    
    if os.path.isdir(ruta):
        return f"ERROR: Es una carpeta, no un archivo: {ruta}"
    
    try:
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            contenido = f.read()
        
        if usar_regex:
            patron = re.compile(buscar)
            coincidencias = len(patron.findall(contenido))
            nuevo_contenido = patron.sub(reemplazar, contenido)
        else:
            coincidencias = contenido.count(buscar)
            nuevo_contenido = contenido.replace(buscar, reemplazar)
        
        if coincidencias == 0:
            return f"[INFO] No se encontraron coincidencias para: '{buscar}'"
        
        print(f"[ARCHIVO] {ruta}")
        print(f"  Coincidencias encontradas: {coincidencias}")
        
        lineas = contenido.split('\n')
        print("")
        print("[VISTA PREVIA DE CAMBIOS]")
        cambios_mostrados = 0
        for i, linea in enumerate(lineas, 1):
            if buscar in linea or (usar_regex and re.search(buscar, linea)):
                nueva_linea = linea.replace(buscar, reemplazar) if not usar_regex else re.sub(buscar, reemplazar, linea)
                print(f"  Linea {i}:")
                print(f"    - {linea[:80]}..." if len(linea) > 80 else f"    - {linea}")
                print(f"    + {nueva_linea[:80]}..." if len(nueva_linea) > 80 else f"    + {nueva_linea}")
                cambios_mostrados += 1
                if cambios_mostrados >= 3:
                    print("  ... (mas cambios no mostrados)")
                    break
        
        if backup and not dry_run:
            backup_path = f"{ruta}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(ruta, backup_path)
            print(f"")
            print(f"[BACKUP] Creado: {backup_path}")
        
        if dry_run:
            print("")
            print("[DRY RUN] No se guardaron cambios.")
            return f"[DRY RUN] {coincidencias} coincidencias encontradas. No se guardaron cambios."
        
        with open(ruta, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        
        return f"[OK] Archivo actualizado: {coincidencias} reemplazos realizados."
        
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description='Edita un archivo buscando y reemplazando texto')
    parser.add_argument('--ruta', required=True, help='Ruta del archivo a editar')
    parser.add_argument('--buscar', required=True, help='Texto a buscar')
    parser.add_argument('--reemplazar', required=True, help='Texto de reemplazo')
    parser.add_argument('--regex', action='store_true', help='Usar expresiones regulares')
    parser.add_argument('--dry_run', action='store_true', help='Simular cambios sin guardar')
    parser.add_argument('--backup', action='store_true', help='Crear backup antes de editar')
    args = parser.parse_args()
    
    resultado = editar_archivo(
        args.ruta,
        args.buscar,
        args.reemplazar,
        args.regex,
        args.dry_run,
        args.backup
    )
    print(resultado)

if __name__ == "__main__":
    main()