# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import json
import glob
import subprocess
import ast
from pathlib import Path
from datetime import datetime

# Obtener SCRIPT_DIR (donde esta waio_escucha.py)
SCRIPT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def leer_archivo(ruta_relativa):
    try:
        with open(os.path.join(SCRIPT_DIR, ruta_relativa), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return None

def leer_json(ruta_relativa):
    try:
        with open(os.path.join(SCRIPT_DIR, ruta_relativa), "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def formatear_tamano(bytes_val):
    if bytes_val >= 1048576:
        return f"{bytes_val // 1048576}MB"
    elif bytes_val >= 1024:
        return f"{bytes_val // 1024}KB"
    else:
        return f"{bytes_val}B"

def contar_procesos_pythonw():
    try:
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq pythonw.exe'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.count('pythonw.exe')
    except:
        return 0

def obtener_ultimo_json():
    try:
        output_dir = os.path.join(SCRIPT_DIR, "temp", "output")
        if not os.path.exists(output_dir):
            return "N/A"
        archivos = glob.glob(os.path.join(output_dir, "*.json"))
        if not archivos:
            return "N/A"
        mas_nuevo = max(archivos, key=os.path.getmtime)
        with open(mas_nuevo, "r", encoding="utf-8") as f:
            data = json.load(f)
            tx_id = data.get('transaccion_id', 'N/A')
            timestamp = data.get('timestamp', 'N/A')
            comando = data.get('comando', 'N/A')
            status = data.get('status', 'N/A')
            return f"{tx_id} | {timestamp} | {comando} | {status}"
    except:
        return "N/A"

def obtener_categorias(skills_data):
    if not skills_data:
        return "N/A"
    cats = skills_data.get("categorias", {})
    if not cats:
        return "N/A"
    return ", ".join([f"{k}({len(v)})" for k, v in cats.items()])

def main():
    # Parsear manualmente para compatibilidad con WAIO
    args_list = sys.argv[1:]
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []

    # 1. VERSION
    version = "3.2"
    try:
        with open(os.path.join(SCRIPT_DIR, "waio_escucha.py"), "r", encoding="utf-8") as f:
            for linea in f:
                if 'VERSION = "' in linea:
                    version = linea.split('"')[1]
                    break
    except:
        pass

    # 2. WORKDIR
    workdir = leer_archivo("temp/workdir.txt") or "No disponible"

    # 3. PERFIL
    config = leer_json("config/waio_config.json")
    perfil = config.get("perfil_activo", "standard") if config else "standard"
    perfiles = config.get("perfiles", {}) if config else {}
    perfil_data = perfiles.get(perfil, {})

    # 4. WISPOUT
    wispout = leer_json("config/wispout.json")
    encabezado = wispout.get("encabezado", {}).get("plantilla", "") if wispout else ""

    # 5. SKILLS
    skills_data = leer_json("data/skills.json")
    total_skills = skills_data.get("_total_skills", 0) if skills_data else 0
    ultima_act = skills_data.get("_ultima_actualizacion", "N/A") if skills_data else "N/A"
    categorias = obtener_categorias(skills_data)

    # 6. LOCKS
    locks = []
    for lock in glob.glob(os.path.join(SCRIPT_DIR, "temp", "*.lock")):
        nombre = os.path.basename(lock).replace(".lock", "").upper()
        locks.append(nombre)

    # 7. TRIGGERS
    triggers = []
    for trigger in glob.glob(os.path.join(SCRIPT_DIR, "*.trigger")):
        triggers.append(os.path.basename(trigger))

    # 8. PROCESOS
    procesos = contar_procesos_pythonw()

    # 9. ULTIMO JSON
    ultimo_json = obtener_ultimo_json()

    # CONSTRUIR SALIDA
    salida = []
    salida.append("=" * 70)
    salida.append(f"  ESTADO DE WAIO v{version}")
    salida.append("=" * 70)
    salida.append(f"  Workdir     : {workdir}")
    salida.append(f"  Perfil      : {perfil.upper()}")
    salida.append(f"  Encabezado  : {encabezado}")
    salida.append(f"  Skills      : {total_skills} (ultima act: {ultima_act})")
    salida.append(f"  Procesos    : {procesos} pythonw.exe")
    salida.append(f"  Locks       : {', '.join(locks) if locks else 'Ninguno'}")
    salida.append(f"  Triggers    : {', '.join(triggers) if triggers else 'Ninguno'}")
    salida.append(f"  Ultimo JSON : {ultimo_json}")
    salida.append("=" * 70)

    salida.append("")
    salida.append("[CONFIGURACION]")
    salida.append(f"  Sandbox     : {'Activado' if perfil_data.get('sandbox', True) else 'Desactivado'}")
    salida.append(f"  Borrado     : {perfil_data.get('borrado', 'N/A')}")
    limite_esc = perfil_data.get('limite_escritura_bytes', 0)
    limite_lec = perfil_data.get('limite_lectura_bytes', 0)
    salida.append(f"  Limite escritura: {formatear_tamano(limite_esc) if limite_esc > 0 else 'Sin limite'}")
    salida.append(f"  Limite lectura  : {formatear_tamano(limite_lec) if limite_lec > 0 else 'Sin limite'}")
    prohibidas = perfil_data.get('carpetas_prohibidas', [])
    if prohibidas:
        salida.append(f"  Carpetas prohibidas: {', '.join(prohibidas[:3])}" + ("..." if len(prohibidas) > 3 else ""))
    else:
        salida.append(f"  Carpetas prohibidas: Ninguna")
    salida.append("=" * 70)

    if wispout:
        salida.append("")
        salida.append("[WISPOUT]")
        recordatorio = wispout.get('recordatorio', {}).get('activo', True)
        salida.append(f"  Recordatorio: {'Activo' if recordatorio else 'Inactivo'}")
        susurro = wispout.get('susurro', {}).get('activo', True)
        cada = wispout.get('susurro', {}).get('cada_cuantas_acciones', 'N/A')
        salida.append(f"  Susurro     : {'Activo' if susurro else 'Inactivo'} (cada {cada} acciones)")
        salida.append("=" * 70)

    if categorias != "N/A":
        salida.append("")
        salida.append("[CATEGORIAS DE SKILLS]")
        salida.append(f"  {categorias}")
        salida.append("=" * 70)

    print("\n".join(salida))

if __name__ == "__main__":
    main()
