import os
import sys
import argparse
import json
from datetime import datetime

def mostrar_arbol_consola(ruta, prefijo="", es_ultimo=True, nivel=0, max_nivel=None, incluir_ocultos=False):
    """Muestra la estructura en formato arbol en consola"""
    if max_nivel is not None and nivel > max_nivel:
        return
    
    if not os.path.exists(ruta):
        print(f"ERROR: No existe: {ruta}")
        return
    
    if os.path.isfile(ruta):
        nombre = os.path.basename(ruta)
        try:
            print(f"{prefijo}-- {nombre}")
        except UnicodeEncodeError:
            print(f"{prefijo}-- [CARACTERES NO IMPRIMIBLES]")
        return
    
    try:
        elementos = os.listdir(ruta)
    except PermissionError:
        print(f"{prefijo}-- [SIN PERMISO]")
        return
    
    # Filtrar ocultos si no se incluyen
    if not incluir_ocultos:
        elementos = [e for e in elementos if not e.startswith('.')]
    
    elementos.sort(key=lambda x: x.lower())
    
    for i, elem in enumerate(elementos):
        es_ultimo_elem = i == len(elementos) - 1
        ruta_completa = os.path.join(ruta, elem)
        
        try:
            if os.path.isdir(ruta_completa):
                if es_ultimo_elem:
                    print(f"{prefijo}-- {elem}/")
                    nuevo_prefijo = prefijo + "    "
                else:
                    print(f"{prefijo}+-- {elem}/")
                    nuevo_prefijo = prefijo + "|   "
                
                mostrar_arbol_consola(ruta_completa, nuevo_prefijo, es_ultimo_elem, nivel + 1, max_nivel, incluir_ocultos)
            else:
                if es_ultimo_elem:
                    print(f"{prefijo}-- {elem}")
                else:
                    print(f"{prefijo}+-- {elem}")
        except UnicodeEncodeError:
            print(f"{prefijo}-- [CARACTERES NO IMPRIMIBLES]")
        except RecursionError:
            print(f"{prefijo}-- [DEMASIADA PROFUNDIDAD]")
            return

def obtener_estructura_json(ruta, nivel=0, max_nivel=None, incluir_ocultos=False):
    """Genera estructura en JSON"""
    if max_nivel is not None and nivel > max_nivel:
        return None
    
    if not os.path.exists(ruta):
        return None
    
    try:
        stats = os.stat(ruta)
        fecha_mod = datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except:
        fecha_mod = "DESCONOCIDO"
    
    # Si es archivo
    if os.path.isfile(ruta):
        try:
            return {
                "nombre": os.path.basename(ruta),
                "tipo": "archivo",
                "tamano": stats.st_size if stats else 0,
                "modificado": fecha_mod
            }
        except:
            return {"nombre": os.path.basename(ruta), "tipo": "archivo", "error": "No se pudo leer"}
    
    # Si es carpeta
    try:
        elementos = os.listdir(ruta)
    except PermissionError:
        return {"nombre": os.path.basename(ruta), "tipo": "carpeta", "error": "Sin permiso"}
    
    if not incluir_ocultos:
        elementos = [e for e in elementos if not e.startswith('.')]
    
    elementos.sort(key=lambda x: x.lower())
    
    contenido = []
    for elem in elementos:
        ruta_completa = os.path.join(ruta, elem)
        try:
            sub = obtener_estructura_json(ruta_completa, nivel + 1, max_nivel, incluir_ocultos)
            if sub is not None:
                contenido.append(sub)
        except RecursionError:
            contenido.append({
                "nombre": elem,
                "tipo": "error",
                "error": "Profundidad maxima excedida"
            })
    
    return {
        "nombre": os.path.basename(ruta) or ruta,
        "tipo": "carpeta",
        "ruta": os.path.abspath(ruta),
        "tamano": stats.st_size if stats else 0,
        "modificado": fecha_mod,
        "contenido": contenido
    }

def guardar_json(estructura, nombre_base):
    """Guarda la estructura en archivo JSON"""
    nombre_archivo = f"tree_{nombre_base}.json"
    try:
        with open(nombre_archivo, 'w', encoding='utf-8') as f:
            json.dump(estructura, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON guardado: {nombre_archivo}")
        return True
    except Exception as e:
        print(f"[ERROR] No se pudo guardar JSON: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description='Muestra la estructura de carpetas en forma de arbol',
        epilog='Ejemplo: mostrar_arbol.py --ruta=./WAIO --incluir_ocultos --profundidad=5'
    )
    parser.add_argument('--ruta', default='.', help='Ruta de la carpeta a analizar (default: .)')
    parser.add_argument('--profundidad', type=int, default=10, help='Profundidad maxima a mostrar (default: 10)')
    parser.add_argument('--incluir_ocultos', action='store_true', help='Incluir carpetas y archivos ocultos')
    parser.add_argument('--guardar', action='store_true', help='Guardar estructura en JSON')
    parser.add_argument('--formato', choices=['tree', 'json', 'ambos'], default='tree', 
                       help='Formato de salida: tree (arbol), json (estructurado), ambos (default: tree)')
    parser.add_argument('--sin_colores', action='store_true', help='Desactivar colores (no aplica en esta version)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.ruta):
        print(f"[ERROR] No existe la ruta: {args.ruta}")
        return
    
    ruta_abs = os.path.abspath(args.ruta)
    nombre_base = os.path.basename(ruta_abs) or "raiz"
    
    print("=" * 60)
    print(f"  MOSTRADOR DE ESTRUCTURA - ARBOL")
    print("=" * 60)
    print(f"  Ruta: {ruta_abs}")
    print(f"  Profundidad: {args.profundidad}")
    print(f"  Incluir ocultos: {args.incluir_ocultos}")
    print(f"  Formato: {args.formato}")
    print("=" * 60)
    print()
    
    # Obtener estructura en JSON (siempre para guardar o para formato json/ambos)
    estructura = None
    if args.formato in ['json', 'ambos'] or args.guardar:
        print("  Generando estructura...")
        estructura = obtener_estructura_json(ruta_abs, max_nivel=args.profundidad, incluir_ocultos=args.incluir_ocultos)
        if estructura is None:
            print("[ERROR] No se pudo generar la estructura")
            return
        print("[OK] Estructura generada")
        print()
    
    # Mostrar en arbol
    if args.formato in ['tree', 'ambos']:
        print("  [ESTRUCTURA EN ARBOL]")
        print("-" * 60)
        print(f"/-- {nombre_base}/")
        mostrar_arbol_consola(
            ruta_abs, 
            prefijo="", 
            es_ultimo=True, 
            nivel=0, 
            max_nivel=args.profundidad, 
            incluir_ocultos=args.incluir_ocultos
        )
        print("-" * 60)
        print()
    
    # Mostrar en JSON
    if args.formato == 'json':
        print("  [ESTRUCTURA EN JSON]")
        print("-" * 60)
        print(json.dumps(estructura, indent=2, ensure_ascii=False))
        print("-" * 60)
        print()
    
    # Guardar JSON
    if args.guardar and estructura is not None:
        guardar_json(estructura, nombre_base)
    
    print("=" * 60)
    print("  FIN DEL REPORTE")
    print("=" * 60)

if __name__ == "__main__":
    main()