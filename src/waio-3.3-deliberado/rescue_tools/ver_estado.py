# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
ver_estado.py — Muestra el estado actual de WAIO.

Versión standalone de la skill `estado`, pensada para correr desde
rescue_tools/ con doble clic cuando el motor no está disponible.

Escribe un log en temp/logs/estado_YYYYMMDD_HHMMSS.log y muestra
el mismo contenido por consola.

A diferencia de la skill `estado`, valida PIDs de locks (no solo
existencia), reporta python.exe además de pythonw.exe, y detecta
locks huérfanos.
"""

import os
import sys
import json
import glob
import subprocess
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.parent.resolve()

LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"estado_{TIMESTAMP}.log"

# Locks conocidos: nombre visible -> ruta
LOCKS = {
    "WAIO (motor)":     SCRIPT_DIR / "temp" / "waio.lock",
    "ESCUCHA OUTPUT":   SCRIPT_DIR / "escucha.lock",
    "TRANSCLIP":        SCRIPT_DIR / "transclip.lock",
    "EVENT VISOR":      SCRIPT_DIR / "events.lock",
    "VOZ (skill)":      SCRIPT_DIR / "skills" / "voz.lock",
}

TRIGGERS = [
    "STOP.trigger",
    "TRANSCLIP_STOP.trigger",
    "ESCUCHA_STOP.trigger",
    "EVENTS_STOP.trigger",
]


def leer_archivo(ruta_relativa):
    try:
        with open(SCRIPT_DIR / ruta_relativa, "r", encoding="utf-8") as f:
            return f.read().strip()
    except Exception:
        return None


def leer_json(ruta_relativa):
    try:
        with open(SCRIPT_DIR / ruta_relativa, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def formatear_tamano(bytes_val):
    if bytes_val >= 1048576:
        return f"{bytes_val // 1048576}MB"
    elif bytes_val >= 1024:
        return f"{bytes_val // 1024}KB"
    else:
        return f"{bytes_val}B"


def pid_es_python(pid):
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return "python" in result.stdout.lower()
    except Exception:
        return False


def contar_procesos(nombre_imagen):
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {nombre_imagen}", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return result.stdout.lower().count(nombre_imagen.lower())
    except Exception:
        return 0


def obtener_ultimo_json():
    try:
        output_dir = SCRIPT_DIR / "temp" / "output"
        if not output_dir.exists():
            return "N/A"
        archivos = list(output_dir.glob("*.json"))
        if not archivos:
            return "N/A"
        mas_nuevo = max(archivos, key=lambda p: p.stat().st_mtime)
        with open(mas_nuevo, "r", encoding="utf-8") as f:
            data = json.load(f)
        tx_id = data.get("transaccion_id", "N/A")
        timestamp = data.get("timestamp", "N/A")
        comando = data.get("comando", "N/A")
        status = data.get("status", "N/A")
        return f"{tx_id} | {timestamp} | {comando} | {status}"
    except Exception:
        return "N/A"


def obtener_categorias(skills_data):
    if not skills_data:
        return "N/A"
    cats = skills_data.get("categorias", {})
    if not cats:
        return "N/A"
    return ", ".join([f"{k}({len(v)})" for k, v in cats.items()])


def detectar_version():
    version = "3.2"
    try:
        with open(SCRIPT_DIR / "waio_escucha.py", "r", encoding="utf-8") as f:
            for linea in f:
                if 'VERSION = "' in linea:
                    version = linea.split('"')[1]
                    break
    except Exception:
        pass
    return version


def construir_salida():
    lineas = []

    version = detectar_version()
    workdir = leer_archivo("temp/workdir.txt") or "No disponible"

    config = leer_json("config/waio_config.json")
    perfil = config.get("perfil_activo", "standard") if config else "standard"
    perfiles = config.get("perfiles", {}) if config else {}
    perfil_data = perfiles.get(perfil, {})

    wispout = leer_json("config/wispout.json")
    encabezado = wispout.get("encabezado", {}).get("plantilla", "") if wispout else ""

    skills_data = leer_json("data/skills.json")
    total_skills = skills_data.get("_total_skills", 0) if skills_data else 0
    ultima_act = skills_data.get("_ultima_actualizacion", "N/A") if skills_data else "N/A"
    categorias = obtener_categorias(skills_data)

    procesos_pythonw = contar_procesos("pythonw.exe")
    procesos_python = contar_procesos("python.exe")

    lineas.append("=" * 70)
    lineas.append(f"  ESTADO DE WAIO v{version}")
    lineas.append("=" * 70)
    lineas.append(f"  Fecha       : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lineas.append(f"  Raíz        : {SCRIPT_DIR}")
    lineas.append(f"  Workdir     : {workdir}")
    lineas.append(f"  Perfil      : {perfil.upper()}")
    if encabezado:
        lineas.append(f"  Encabezado  : {encabezado}")
    lineas.append(f"  Skills      : {total_skills} (ultima act: {ultima_act})")
    lineas.append(f"  pythonw.exe : {procesos_pythonw} activos")
    lineas.append(f"  python.exe  : {procesos_python} activos")
    lineas.append("=" * 70)

    lineas.append("")
    lineas.append("[PROCESOS POR LOCK]")
    for etiqueta, lock in LOCKS.items():
        if not lock.exists():
            lineas.append(f"  {etiqueta}: DETENIDO")
            continue
        try:
            pid = int(lock.read_text().strip())
        except Exception:
            lineas.append(f"  {etiqueta}: LOCK ILEGIBLE")
            continue
        if pid_es_python(pid):
            lineas.append(f"  {etiqueta}: CORRIENDO (PID {pid})")
        else:
            lineas.append(f"  {etiqueta}: LOCK HUÉRFANO (PID {pid} no existe o no es Python)")
    lineas.append("=" * 70)

    lineas.append("")
    lineas.append("[TRIGGERS]")
    alguno = False
    for nombre in TRIGGERS:
        if (SCRIPT_DIR / nombre).exists():
            lineas.append(f"  {nombre}: PRESENTE")
            alguno = True
    if not alguno:
        lineas.append("  Ninguno")
    lineas.append("=" * 70)

    lineas.append("")
    lineas.append("[CONFIGURACION DEL PERFIL]")
    lineas.append(f"  Sandbox     : {'Activado' if perfil_data.get('sandbox', True) else 'Desactivado'}")
    lineas.append(f"  Borrado     : {perfil_data.get('borrado', 'N/A')}")
    limite_esc = perfil_data.get("limite_escritura_bytes", 0)
    limite_lec = perfil_data.get("limite_lectura_bytes", 0)
    lineas.append(f"  Límite escritura: {formatear_tamano(limite_esc) if limite_esc > 0 else 'Sin límite'}")
    lineas.append(f"  Límite lectura  : {formatear_tamano(limite_lec) if limite_lec > 0 else 'Sin límite'}")
    prohibidas = perfil_data.get("carpetas_prohibidas", [])
    if prohibidas:
        resumen = ", ".join(prohibidas[:3])
        if len(prohibidas) > 3:
            resumen += f"... (+{len(prohibidas) - 3})"
        lineas.append(f"  Carpetas prohibidas: {resumen}")
    else:
        lineas.append(f"  Carpetas prohibidas: Ninguna")
    lineas.append("=" * 70)

    if wispout:
        lineas.append("")
        lineas.append("[WISPOUT]")
        recordatorio = wispout.get("recordatorio", {}).get("activo", True)
        lineas.append(f"  Recordatorio: {'Activo' if recordatorio else 'Inactivo'}")
        susurro = wispout.get("susurro", {}).get("activo", True)
        cada = wispout.get("susurro", {}).get("cada_cuantas_acciones", "N/A")
        lineas.append(f"  Susurro     : {'Activo' if susurro else 'Inactivo'} (cada {cada} acciones)")
        lineas.append("=" * 70)

    if categorias != "N/A":
        lineas.append("")
        lineas.append("[CATEGORIAS DE SKILLS]")
        lineas.append(f"  {categorias}")
        lineas.append("=" * 70)

    lineas.append("")
    lineas.append("[ULTIMO JSON PROCESADO]")
    lineas.append(f"  {obtener_ultimo_json()}")
    lineas.append("=" * 70)

    return "\n".join(lineas)


def main():
    salida = construir_salida()

    # Mostrar por consola
    print(salida)

    # Escribir log
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            f.write(salida)
            f.write("\n")
        print(f"\n[LOG] Reporte guardado en: {LOG_FILE}")
    except Exception as e:
        print(f"\n[ERROR] No se pudo guardar el log: {e}")

    input("\nPresione Enter para salir...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR FATAL] {e}")
        input("\nPresione Enter para salir...")