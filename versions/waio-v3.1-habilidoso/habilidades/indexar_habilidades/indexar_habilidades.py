import os
import json
import sys
import shutil
from datetime import datetime
from pathlib import Path

# ============================================================
# CONFIGURACION
# ============================================================

RUTA_WAIO = Path(os.environ["USERPROFILE"]) / ".waio"
RUTA_HABILIDADES = RUTA_WAIO / "habilidades"
RUTA_PYHABILIDADES = RUTA_WAIO / "pyhabilidades"
RUTA_JSON_MAESTRO = RUTA_HABILIDADES / "habilidades.json"
RUTA_PROYECTO = Path(os.getcwd())

# ============================================================
# ESTRUCTURA REQUERIDA DEL MICRO JSON
# ============================================================

CAMPOS_OBLIGATORIOS = [
    "nombre", "version", "autor", "categoria", "tags",
    "descripcion", "tipo", "parametros", "perfil_minimo"
]

TIPOS_VALIDOS = ["comando_interno", "script"]
PERFILES_VALIDOS = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]

# ============================================================
# FUNCIONES
# ============================================================

def validar_micro_json(data, carpeta_nombre):
    errores = []
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in data:
            errores.append(f"Falta campo obligatorio: '{campo}'")
    if "tipo" in data and data["tipo"] not in TIPOS_VALIDOS:
        errores.append(f"Tipo invalido: '{data['tipo']}'. Debe ser: {TIPOS_VALIDOS}")
    if "perfil_minimo" in data and data["perfil_minimo"] not in PERFILES_VALIDOS:
        errores.append(f"Perfil invalido: '{data['perfil_minimo']}'. Debe ser: {PERFILES_VALIDOS}")
    if data.get("tipo") == "script" and "script" not in data:
        errores.append("Falta 'script' para habilidad de tipo 'script'")
    if "nombre" in data and data["nombre"] != carpeta_nombre:
        errores.append(f"El nombre '{data['nombre']}' no coincide con la carpeta '{carpeta_nombre}'")
    return errores

def asegurar_carpeta(ruta):
    if not ruta.exists():
        ruta.mkdir(parents=True)
        print(f"[CARPETA] Creada: {ruta}")

def indexar_habilidades():
    resultados = []
    errores = []

    if not RUTA_HABILIDADES.exists():
        return {"error": f"No existe la carpeta: {RUTA_HABILIDADES}"}

    print(f"[ESCANEANDO] {RUTA_HABILIDADES}")
    print("")

    for carpeta in RUTA_HABILIDADES.iterdir():
        if not carpeta.is_dir():
            continue
        nombre_carpeta = carpeta.name
        json_path = carpeta / f"{nombre_carpeta}.json"
        if not json_path.exists():
            print(f"[AVISO] {nombre_carpeta}: No tiene archivo .json")
            continue
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            errores.append(f"[ERROR] {nombre_carpeta}: Error al leer JSON: {str(e)}")
            continue
        errores_validacion = validar_micro_json(data, nombre_carpeta)
        if errores_validacion:
            for err in errores_validacion:
                errores.append(f"[ERROR] {nombre_carpeta}: {err}")
            continue
        if data.get("tipo") == "script":
            script_name = data.get("script", f"{nombre_carpeta}.py")
            ruta_script = f"{nombre_carpeta}/{script_name}"
            data["ruta_script"] = ruta_script
        if data.get("tipo") == "script":
            script_origen = carpeta / data.get("script", f"{nombre_carpeta}.py")
            if script_origen.exists():
                asegurar_carpeta(RUTA_PYHABILIDADES)
                script_destino = RUTA_PYHABILIDADES / script_origen.name
                shutil.copy2(script_origen, script_destino)
                print(f"[SCRIPT] Copiado: {script_origen.name} -> pyhabilidades/")
            else:
                print(f"[AVISO] {nombre_carpeta}: Script no encontrado: {script_origen.name}")
        resultados.append(data)
        print(f"[OK] {nombre_carpeta}")

    print("")

    if resultados:
        categorias = {}
        for h in resultados:
            cat = h.get("categoria", "sin_categoria")
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(h["nombre"])
        index_data = {
            "_waio_firma": "WAIO-V4-HABILIDADES-2026",
            "_version": "1.0",
            "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "_total_habilidades": len(resultados),
            "categorias": categorias,
            "habilidades": {h["nombre"]: h for h in resultados}
        }
        asegurar_carpeta(RUTA_HABILIDADES)
        with open(RUTA_JSON_MAESTRO, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        print(f"[OK] JSON maestro generado: {RUTA_JSON_MAESTRO}")
        print(f"[OK] Total habilidades: {len(resultados)}")

    if errores:
        print("")
        print("[ERRORES ENCONTRADOS]")
        for err in errores:
            print(f"  {err}")

    return {
        "total": len(resultados),
        "errores": errores
    }

def main():
    print("=" * 60)
    print("  INDEXADOR DE HABILIDADES WAIO")
    print("=" * 60)
    print("")
    print(f"[RUTA] Instalacion: {RUTA_WAIO}")
    print(f"[RUTA] Habilidades: {RUTA_HABILIDADES}")
    print(f"[RUTA] Scripts: {RUTA_PYHABILIDADES}")
    print("")
    resultado = indexar_habilidades()
    print("")
    print("=" * 60)
    if resultado.get("error"):
        print(f"[ERROR] {resultado['error']}")
        return
    if resultado.get("errores"):
        print("[ADVERTENCIA] Se encontraron errores durante la indexacion.")
    else:
        print("[OK] Indexacion completada exitosamente.")

if __name__ == "__main__":
    main()