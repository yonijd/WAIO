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
COMANDOS_DIR = SCRIPT_DIR / "comandos"
DATA_DIR = SCRIPT_DIR / "data"
SKILLS_JSON = DATA_DIR / "skills.json"

CAMPOS_OBLIGATORIOS = ["nombre", "tipo"]
TIPOS_VALIDOS = ["comando_interno", "script"]
PERFILES_VALIDOS = ["readonly", "standard", "advanced", "debug"]

def indexar():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    skills_validas = []
    errores = []
    nombres = set()

    # 1. core/ y skills/ (py + json obligatorios)
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

            if carpeta == CORE_DIR:
                data["perfil_minimo"] = "standard"
                data["ubicacion"] = "core"
            else:
                data["perfil_minimo"] = "advanced"
                data["ubicacion"] = "skills"
            data["ejecutable"] = True

            if nombre_carpeta in nombres:
                for i, s in enumerate(skills_validas):
                    if s["nombre"] == nombre_carpeta:
                        skills_validas[i] = data
                        break
            else:
                nombres.add(nombre_carpeta)
                skills_validas.append(data)

    # 2. comandos/ (solo json, informativo)
    if COMANDOS_DIR.exists():
        for subcarpeta in COMANDOS_DIR.iterdir():
            if not subcarpeta.is_dir():
                continue
            nombre_carpeta = subcarpeta.name
            json_path = subcarpeta / f"{nombre_carpeta}.json"
            if not json_path.exists():
                errores.append(f"{nombre_carpeta}: JSON no encontrado en comandos/")
                continue
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception as e:
                errores.append(f"{nombre_carpeta}: Error al leer JSON en comandos/: {str(e)}")
                continue
            valido, mensaje = validar_json(data, nombre_carpeta)
            if not valido:
                errores.append(f"{nombre_carpeta}: {mensaje}")
                continue

            data["ruta_script"] = None
            if "perfil_minimo" not in data or data["perfil_minimo"] not in PERFILES_VALIDOS:
                data["perfil_minimo"] = "standard"
            data["ubicacion"] = "comandos"
            data["ejecutable"] = False

            if nombre_carpeta in nombres:
                for i, s in enumerate(skills_validas):
                    if s["nombre"] == nombre_carpeta:
                        skills_validas[i] = data
                        break
            else:
                nombres.add(nombre_carpeta)
                skills_validas.append(data)

    # 3. Armar el catalogo
    categorias = {}
    perfiles_count = {"readonly": 0, "standard": 0, "advanced": 0, "debug": 0}
    for s in skills_validas:
        cat = s.get("categoria", "sin_categoria")
        if cat not in categorias:
            categorias[cat] = []
        categorias[cat].append(s["nombre"])
        # El resumen cuenta solo los ejecutables (core y skills), no los informativos (comandos)
        if not s.get("ejecutable", True):
            continue
        perfil = s.get("perfil_minimo", "readonly")
        if perfil in perfiles_count:
            perfiles_count[perfil] += 1

    index_data = {
        "_waio_firma": "WAIO-V3-SKILLS-2026",
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
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "aviso": "Los alias NO se aplican en caliente. Si cambiaste alias, reinicia el motor de WAIO."
    }

def validar_json(data, carpeta_nombre):
    for campo in CAMPOS_OBLIGATORIOS:
        if campo not in data:
            return False, f"Falta campo obligatorio: '{campo}'"
    if data.get("tipo") not in TIPOS_VALIDOS:
        return False, f"Tipo invalido: '{data.get('tipo')}'"
    if data.get("tipo") == "script" and "script" not in data:
        return False, "Falta 'script' para habilidad de tipo 'script'"
    if data.get("nombre") != carpeta_nombre:
        return False, f"El nombre '{data['nombre']}' no coincide con la carpeta '{carpeta_nombre}'"
    return True, "OK"

if __name__ == "__main__":
    resultado = indexar()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))