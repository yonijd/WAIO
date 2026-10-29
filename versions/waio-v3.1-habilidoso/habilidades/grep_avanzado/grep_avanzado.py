import os
import sys
import argparse
import re

def buscar_en_archivo(ruta, patron, usar_regex=False, case_sensitive=False, mostrar_lineas=False):
    try:
        with open(ruta, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
        
        if usar_regex:
            flags = 0 if case_sensitive else re.IGNORECASE
            patron_compilado = re.compile(patron, flags)
            resultados = []
            for i, linea in enumerate(lineas, 1):
                if patron_compilado.search(linea):
                    match = patron_compilado.search(linea)
                    resultados.append({
                        'linea_num': i,
                        'contenido': linea.strip(),
                        'match': match.group() if match else ''
                    })
            return resultados
        else:
            if not case_sensitive:
                patron_lower = patron.lower()
                resultados = []
                for i, linea in enumerate(lineas, 1):
                    if patron_lower in linea.lower():
                        resultados.append({
                            'linea_num': i,
                            'contenido': linea.strip()
                        })
                return resultados
            else:
                resultados = []
                for i, linea in enumerate(lineas, 1):
                    if patron in linea:
                        resultados.append({
                            'linea_num': i,
                            'contenido': linea.strip()
                        })
                return resultados
    except:
        return []

def grep_avanzado(ruta, patron, usar_regex=False, case_sensitive=False, extension=None, 
                  mostrar_lineas=False, excluir_patron=None, mostrar_contexto=0):
    if not os.path.exists(ruta):
        return f"ERROR: No existe: {ruta}"
    
    if os.path.isfile(ruta):
        resultados = buscar_en_archivo(ruta, patron, usar_regex, case_sensitive, mostrar_lineas)
        if resultados:
            return {ruta: resultados}
        return {}
    
    resultados = {}
    total_coincidencias = 0
    
    for root, dirs, files in os.walk(ruta):
        for file in files:
            if extension and not file.endswith(extension):
                continue
            
            ruta_completa = os.path.join(root, file)
            
            if excluir_patron:
                if re.search(excluir_patron, ruta_completa):
                    continue
            
            encontrados = buscar_en_archivo(ruta_completa, patron, usar_regex, case_sensitive, mostrar_lineas)
            if encontrados:
                resultados[ruta_completa] = encontrados
                total_coincidencias += len(encontrados)
    
    return resultados

def main():
    parser = argparse.ArgumentParser(description='Busqueda avanzada en archivos (grep)')
    parser.add_argument('--ruta', required=True, help='Ruta de carpeta o archivo')
    parser.add_argument('--patron', required=True, help='Patron a buscar')
    parser.add_argument('--regex', action='store_true', help='Usar expresiones regulares')
    parser.add_argument('--case_sensitive', action='store_true', help='Sensible a mayusculas')
    parser.add_argument('--extension', help='Filtrar por extension (ej: .py, .txt)')
    parser.add_argument('--excluir', help='Excluir rutas que coincidan con este patron')
    parser.add_argument('--mostrar_lineas', action='store_true', help='Mostrar contenido completo de la linea')
    parser.add_argument('--contexto', type=int, default=0, help='Lineas de contexto alrededor del match')
    args = parser.parse_args()
    
    resultados = grep_avanzado(
        args.ruta,
        args.patron,
        args.regex,
        args.case_sensitive,
        args.extension,
        args.mostrar_lineas,
        args.excluir,
        args.contexto
    )
    
    if isinstance(resultados, str):
        print(resultados)
        return
    
    if not resultados:
        print("No se encontraron coincidencias.")
        return
    
    total = 0
    for archivo, lineas in resultados.items():
        print(f"[ARCHIVO] {archivo}")
        for match in lineas:
            linea_num = match['linea_num']
            contenido = match['contenido']
            print(f"  linea {linea_num}: {contenido[:100]}{'...' if len(contenido) > 100 else ''}")
            total += 1
    
    print(f"[TOTAL] {total} coincidencias en {len(resultados)} archivos.")

if __name__ == "__main__":
    main()