# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
limpiar_waio.py — Botón de pánico.

Mata todos los procesos de WAIO (motor y satélites), limpia locks,
triggers y temporales. NO borra logs. NO borra trash.

Úsalo cuando WAIO entre en bucle o conflicto grave y no responda
al kill normal. Es destructivo por diseño: asume que algo salió mal.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.parent.resolve()

LOCKS = [
    SCRIPT_DIR / "temp" / "waio.lock",
    SCRIPT_DIR / "escucha.lock",
    SCRIPT_DIR / "transclip.lock",
    SCRIPT_DIR / "events.lock",
    SCRIPT_DIR / "skills" / "voz.lock",
]

TRIGGERS = [
    SCRIPT_DIR / "STOP.trigger",
    SCRIPT_DIR / "TRANSCLIP_STOP.trigger",
    SCRIPT_DIR / "ESCUCHA_STOP.trigger",
    SCRIPT_DIR / "EVENTS_STOP.trigger",
]

CARPETAS_TEMP = [
    SCRIPT_DIR / "temp" / "jsonout",
    SCRIPT_DIR / "temp" / "output",
]


def pid_es_python(pid):
    """Verifica que el PID exista y sea un proceso Python."""
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


def matar_por_lock(lock_path, etiqueta):
    """Lee el PID del lock y lo mata si es Python."""
    if not lock_path.exists():
        print(f"  [ ] {etiqueta}: sin lock")
        return False

    try:
        pid = int(lock_path.read_text().strip())
    except Exception as e:
        print(f"  [ERROR] {etiqueta}: lock ilegible ({e})")
        return False

    if not pid_es_python(pid):
        print(f"  [!] {etiqueta}: PID {pid} no es Python o no existe")
        return False

    try:
        subprocess.run(
            ["taskkill", "/PID", str(pid), "/F"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        print(f"  [+] {etiqueta}: PID {pid} terminado")
        return True
    except Exception as e:
        print(f"  [ERROR] {etiqueta}: taskkill falló ({e})")
        return False


def borrar_archivo(path, etiqueta):
    if not path.exists():
        return False
    try:
        path.unlink()
        print(f"  [+] {etiqueta}")
        return True
    except Exception as e:
        print(f"  [ERROR] {etiqueta}: {e}")
        return False


def vaciar_carpeta(path, etiqueta):
    if not path.exists():
        print(f"  [ ] {etiqueta}: no existe")
        return False

    contador = 0
    for item in path.iterdir():
        try:
            if item.is_file():
                item.unlink()
                contador += 1
            elif item.is_dir():
                import shutil
                shutil.rmtree(item)
                contador += 1
        except Exception as e:
            print(f"  [ERROR] {etiqueta}: {item.name} ({e})")

    print(f"  [+] {etiqueta}: {contador} items borrados")
    return contador > 0


def main():
    print("=" * 60)
    print("   LIMPIAR WAIO — Botón de pánico")
    print("=" * 60)
    print(f"Raíz: {SCRIPT_DIR}")
    print()

    if not SCRIPT_DIR.exists():
        print(f"[ERROR] No se encontró {SCRIPT_DIR}")
        input("\nPresione Enter para salir...")
        return

    # 1. Crear triggers para que los procesos vivos se apaguen solos
    print("[1] Creando triggers de parada...")
    for t in TRIGGERS:
        try:
            t.touch()
            print(f"  [+] {t.name}")
        except Exception as e:
            print(f"  [ERROR] {t.name}: {e}")

    print("\n[2] Esperando 2 segundos a que los procesos se apaguen...")
    time.sleep(2)

    # 3. Matar por PID verificado
    print("\n[3] Matando procesos WAIO por PID...")
    for lock in LOCKS:
        etiqueta = lock.stem.replace(".lock", "").upper()
        matar_por_lock(lock, etiqueta)

    # 4. Borrar locks
    print("\n[4] Eliminando locks...")
    for lock in LOCKS:
        etiqueta = lock.stem.replace(".lock", "").upper()
        borrar_archivo(lock, f"{etiqueta}.lock")

    # 5. Borrar triggers
    print("\n[5] Eliminando triggers...")
    for t in TRIGGERS:
        borrar_archivo(t, t.name)

    # 6. Vaciar temporales (jsonout y output, NO logs)
    print("\n[6] Vaciando temporales...")
    for carpeta in CARPETAS_TEMP:
        etiqueta = f"temp/{carpeta.name}/"
        vaciar_carpeta(carpeta, etiqueta)

    # 7. Reporte final
    print("\n[7] Estado final:")
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/NH"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        activos = result.stdout.lower().count("pythonw")
        print(f"  pythonw.exe activos: {activos}")
    except Exception:
        print("  No se pudo contar pythonw.exe")

    print("\nLISTO. Logs y trash preservados.")
    input("\nPresione Enter para salir...")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"[ERROR FATAL] {e}")
        input("\nPresione Enter para salir...")