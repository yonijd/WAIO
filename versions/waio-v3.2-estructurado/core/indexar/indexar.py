# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(sys.argv[0]).parent.parent.parent.resolve()
SKILLS_DIR = SCRIPT_DIR / "skills"
CORE_DIR = SCRIPT_DIR / "core"
DATA_DIR = SCRIPT_DIR / "data"
SKILLS_JSON = DATA_DIR / "skills.json"

CAMPOS_OBLIGATORIOS = ["nombre", "tipo", "perfil_minimo"]
TIPOS_VALIDOS = ["comando_interno", "script"]
PERFILES_VALIDOS = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]

def indexar():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    skills_validas = []
    errores = []
    nombres = set()

    for carpeta in [CORE_DIR, SKILLS_DIR]:
        if not carpeta.exists():
            continue
        for subcarpeta in carpeta.iterdir():
            if not subcarpeta.is_dir():
                continue
            nombre_carpeta = subcarpeta.name
            json_path = subcarpeta / f"{nombre_carpeta}.json"
            if not json_path.exists():
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                errores.append(f"{nombre_carpeta}: Error al leer JSON: {str(e)}")
                continue
            valido, mensaje = validar_json(data, nombre_carpeta)
            if not valido:
                errores.append(f"{nombre_carpeta}: {mensaje}")
                continue
            if data.get("tipo") == "script":
                script_name = data.get("script", f"{nombre_carpeta}.py")
                script_path = subcarpeta / script_name
                if not script_path.exists():
                    errores.append(f"{nombre_carpeta}: Script no encontrado: {script_name}")
                    continue
                data["ruta_script"] = f"{carpeta.name}/{nombre_carpeta}/{script_name}"
            else:
                data["ruta_script"] = None
            if nombre_carpeta in nombres:
                for i, s in enumerate(skills_validas):
                    if s["nombre"] == nombre_carpeta:
                        skills_validas[i] = data
                        break
            else:
                nombres.add(nombre_carpeta)
                skills_validas.append(data)

    categorias = {}
    perfiles_count = {"solo_lectura": 0, "estandar": 0, "avanzado": 0, "sin_restricciones": 0}
    for s in skills_validas:
        cat = s.get("categoria", "sin_categoria")
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(s["nombre"])
        perfil = s.get("perfil_minimo", "solo_lectura")
        if perfil in perfiles_count:
            perfiles_count[perfil] += 1

    index_data = {
        "_waio_firma": "WAIO-V5-SKILLS-2026",
        "_version": "1.0",
        "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "_total_skills": len(skills_validas),
        "categorias": categorias,
        "resumen_por_perfil": perfiles_count,
        "skills": {s["nombre"]: s for s in skills_validas}
    }

    with open(SKILLS_JSON, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    return {
        "estado": "completado",
        "total_skills": len(skills_validas),
        "skills_indexadas": [s["nombre"] for s in skills_validas],
        "errores": errores,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def validar_json(data, carpeta_nombre):
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in data:
            return False, f"Falta campo obligatorio: '{campo}'"
    if data.get("tipo") not in TIPOS_VALIDOS:
        return False, f"Tipo invalido: '{data.get('tipo')}'"
    if data.get("perfil_minimo") not in PERFILES_VALIDOS:
        return False, f"Perfil invalido: '{data.get('perfil_minimo')}'"
    if data.get("tipo") == "script" and "script" not in data:
        return False, "Falta 'script' para habilidad de tipo 'script'"
    if data.get("nombre") != carpeta_nombre:
        return False, f"El nombre '{data['nombre']}' no coincide con la carpeta '{carpeta_nombre}'"
    return True, "OK"

if __name__ == "__main__":
    resultado = indexar()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))