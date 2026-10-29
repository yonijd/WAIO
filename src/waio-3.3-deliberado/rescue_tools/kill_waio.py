# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
kill_waio.py — Detiene TODO WAIO de raíz, por capas de agresión creciente.

Capas:
  Capa 1 (básica):     STOP.trigger + matar PIDs de locks + borrar locks. Borra triggers al final.
  Capa 2 (profunda):   + matar python/pythonw con nombres de WAIO en cmdline.
                         Refuerzo: si no encuentra, mata todos los pythonw.exe.
  Capa 3 (total):      + matar TODOS los python.exe/pythonw.exe con /F /T.
  Capa 3b (extrema):   + matar cmd/powershell con nombres de WAIO en cmdline.

Reglas:
  - NUNCA mata el propio proceso (os.getpid()).
  - Log a archivo desde el inicio, con flush.
  - Pausa SIEMPRE al final (finally).
  - Locks se borran después de matar el PID (o si el PID no existe).
  - Triggers se borran al final de Capa 1.
  - todo_limpio = no quedan procesos WAIO vivos (locks y triggers no cuentan).
"""

import os
import sys
import time
import subprocess
import re
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.parent.resolve()
MI_PID = os.getpid()

LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"kill_waio_{TIMESTAMP}.log"

ESPERA_TRIGGER = 3
ESPERA_ENTRE_CAPAS = 1

LOCKS = [
    (SCRIPT_DIR / "temp" / "waio.lock", "MOTOR"),
    (SCRIPT_DIR / "escucha.lock", "ESCUCHA_OUTPUT"),
    (SCRIPT_DIR / "transclip.lock", "TRANSCLIP"),
    (SCRIPT_DIR / "events.lock", "EVENT_VISOR"),
    (SCRIPT_DIR / "skills" / "voz.lock", "VOZ"),
]

TRIGGERS = [
    SCRIPT_DIR / "STOP.trigger",
    SCRIPT_DIR / "TRANSCLIP_STOP.trigger",
    SCRIPT_DIR / "ESCUCHA_STOP.trigger",
    SCRIPT_DIR / "EVENTS_STOP.trigger",
]

NOMBRES_WAIO = [
    ".waio",
    "waio_visor",
    "waio_escucha",
    "escucha_output",
    "transclip",
    "event_visor",
    "kill_waio",
    "limpiar_waio",
    "ver_estado",
    "desinstalador_waio",
    "instalador_waio",
]


def log(msg=""):
    print(msg, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
            f.flush()
    except Exception:
        pass


def ejecutar(cmd, timeout=10):
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        return r.returncode, (r.stdout or ""), (r.stderr or "")
    except subprocess.TimeoutExpired:
        return -1, "", "timeout"
    except Exception as e:
        return -1, "", str(e)


def pid_existe(pid):
    rc, out, _ = ejecutar(["tasklist", "/FI", f"PID eq {pid}", "/NH"])
    if rc != 0:
        return False
    return str(pid) in out and "no hay tareas" not in out.lower()


def pid_es_python(pid):
    rc, out, _ = ejecutar(["tasklist", "/FI", f"PID eq {pid}", "/NH"])
    if rc != 0:
        return False
    out_lower = out.lower()
    return "python.exe" in out_lower or "pythonw.exe" in out_lower


def obtener_commandline(pid, timeout=3):
    if pid == MI_PID:
        return None
    ps_cmd = f"(Get-CimInstance Win32_Process -Filter \"ProcessId = {pid}\").CommandLine"
    rc, out, _ = ejecutar(["powershell", "-NoProfile", "-Command", ps_cmd], timeout=timeout)
    if rc == 0 and out.strip():
        return out.strip()
    return None


def matar_pid(pid, etiqueta, forzar_arbol=True):
    if pid == MI_PID:
        log(f"  [SKIP] {etiqueta}: PID {pid} es el propio kill_waio, no se mata")
        return False
    args = ["taskkill", "/F", "/PID", str(pid)]
    if forzar_arbol:
        args.insert(2, "/T")
    rc, out, err = ejecutar(args)
    if rc == 0:
        log(f"  [+] {etiqueta}: PID {pid} terminado")
        return True
    err_msg = (err.strip() or out.strip())
    log(f"  [ERROR] {etiqueta}: PID {pid} no se pudo matar ({err_msg})")
    return False


def cmdline_es_waio(cmdline):
    if not cmdline:
        return False
    cl = cmdline.lower()
    return any(n in cl for n in NOMBRES_WAIO)


def borrar_lock(lock_path, etiqueta):
    """Borra un lock. Devuelve True si lo borró."""
    if not lock_path.exists():
        return False
    try:
        lock_path.unlink()
        log(f"  [+] {etiqueta}.lock borrado")
        return True
    except Exception as e:
        log(f"  [ERROR] {etiqueta}.lock: {e}")
        return False


def borrar_triggers():
    log("  [*] Borrando triggers...")
    for t in TRIGGERS:
        if t.exists():
            try:
                t.unlink()
                log(f"  [+] {t.name} borrado")
            except Exception as e:
                log(f"  [ERROR] {t.name}: {e}")


# ----------------------------------------------------------------------
# Detección
# ----------------------------------------------------------------------

def listar_python_waio():
    log("  [*] Buscando python/pythonw con nombres de WAIO en cmdline...")
    resultado = []
    for nombre in ("python.exe", "pythonw.exe"):
        rc, out, _ = ejecutar(["tasklist", "/FI", f"IMAGENAME eq {nombre}", "/NH"])
        if rc != 0:
            continue
        for linea in out.splitlines():
            m = re.match(r"(\S+)\s+(\d+)\s+", linea)
            if not m:
                continue
            pid = int(m.group(2))
            if pid == MI_PID:
                log(f"    [SKIP] PID {pid} es el propio kill_waio")
                continue
            log(f"    [*] Consultando cmdline de PID {pid} ({nombre})...")
            cmdline = obtener_commandline(pid, timeout=3)
            if cmdline and cmdline_es_waio(cmdline):
                resultado.append((pid, cmdline))
            elif cmdline is None:
                log(f"    [!] PID {pid}: no se pudo obtener cmdline (¿proceso colgado?)")
    return resultado


def listar_todos_python():
    log("  [*] Listando todos los python.exe/pythonw.exe...")
    resultado = []
    for nombre in ("python.exe", "pythonw.exe"):
        rc, out, _ = ejecutar(["tasklist", "/FI", f"IMAGENAME eq {nombre}", "/NH"])
        if rc != 0:
            continue
        for linea in out.splitlines():
            m = re.match(r"(\S+)\s+(\d+)\s+", linea)
            if not m:
                continue
            pid = int(m.group(2))
            if pid == MI_PID:
                continue
            cmdline = obtener_commandline(pid, timeout=3) or ""
            resultado.append((pid, nombre, cmdline))
    return resultado


def listar_waio_no_python():
    log("  [*] Buscando cmd/powershell con WAIO en cmdline...")
    resultado = []
    for nombre in ("cmd.exe", "powershell.exe", "pwsh.exe", "conhost.exe"):
        rc, out, _ = ejecutar(["tasklist", "/FI", f"IMAGENAME eq {nombre}", "/NH"])
        if rc != 0:
            continue
        for linea in out.splitlines():
            m = re.match(r"(\S+)\s+(\d+)\s+", linea)
            if not m:
                continue
            pid = int(m.group(2))
            if pid == MI_PID:
                continue
            cmdline = obtener_commandline(pid, timeout=2)
            if cmdline and cmdline_es_waio(cmdline):
                resultado.append((pid, nombre, cmdline))
    return resultado


def reescanear():
    waio = listar_python_waio()
    todos = listar_todos_python()
    locks_vivos = [(p, e) for p, e in LOCKS if p.exists()]
    triggers_vivos = [t for t in TRIGGERS if t.exists()]
    return waio, todos, locks_vivos, triggers_vivos


# ----------------------------------------------------------------------
# Capas
# ----------------------------------------------------------------------

def capa_1():
    log("\n" + "=" * 60)
    log("   CAPA 1 — Detención básica (triggers + locks)")
    log("=" * 60)

    log("\n[1.1] Creando triggers de parada...")
    for t in TRIGGERS:
        try:
            t.touch()
            log(f"  [+] {t.name}")
        except Exception as e:
            log(f"  [ERROR] {t.name}: {e}")

    log(f"\n[1.2] Esperando {ESPERA_TRIGGER}s a que los procesos se apaguen solos...")
    for i in range(ESPERA_TRIGGER):
        time.sleep(1)
        log(f"  ... {i+1}s")

    log("\n[1.3] Matando procesos por PID de locks y borrando locks...")
    for lock_path, etiqueta in LOCKS:
        if not lock_path.exists():
            log(f"  [ ] {etiqueta}: sin lock")
            continue
        try:
            pid = int(lock_path.read_text().strip())
        except Exception as e:
            log(f"  [ERROR] {etiqueta}: lock ilegible ({e})")
            borrar_lock(lock_path, etiqueta)
            continue
        log(f"  [*] {etiqueta}: lock dice PID {pid}, verificando...")
        if not pid_existe(pid):
            log(f"  [ ] {etiqueta}: PID {pid} ya no existe")
            borrar_lock(lock_path, etiqueta)
            continue
        if not pid_es_python(pid):
            log(f"  [!] {etiqueta}: PID {pid} no es Python, no se mata")
            borrar_lock(lock_path, etiqueta)
            continue
        matar_pid(pid, etiqueta)
        borrar_lock(lock_path, etiqueta)

    log("\n[1.4] Borrando triggers (ya cumplieron su función)...")
    borrar_triggers()


def capa_2():
    log("\n" + "=" * 60)
    log("   CAPA 2 — Detección por línea de comandos")
    log("=" * 60)

    procesos = listar_python_waio()
    if procesos:
        log(f"\n[2.1] Encontrados {len(procesos)} procesos WAIO:")
        for pid, cmdline in procesos:
            cmdline_short = cmdline[:100] + "..." if len(cmdline) > 100 else cmdline
            log(f"  [?] PID {pid}: {cmdline_short}")
        log(f"\n[2.2] Matando...")
        for pid, _ in procesos:
            matar_pid(pid, f"WAIO PID {pid}")

    log("\n[2.3] Refuerzo: matando todos los pythonw.exe restantes...")
    rc, out, _ = ejecutar(["tasklist", "/FI", "IMAGENAME eq pythonw.exe", "/NH"])
    if rc == 0:
        pids = []
        for linea in out.splitlines():
            m = re.match(r"(\S+)\s+(\d+)\s+", linea)
            if not m:
                continue
            pid = int(m.group(2))
            if pid == MI_PID:
                continue
            pids.append(pid)
        log(f"  [*] pythonw vivos: {len(pids)}")
        for pid in pids:
            log(f"    pythonw PID {pid}")
        for pid in pids:
            if pid_existe(pid):
                matar_pid(pid, f"pythonw PID {pid} (refuerzo)")
    else:
        log("  [ ] No hay pythonw.exe")


def capa_3():
    log("\n" + "=" * 60)
    log("   CAPA 3 — Kill masivo de TODOS los Python (árbol completo)")
    log("=" * 60)
    log("\nADVERTENCIA: esta capa mata TODOS los python.exe/pythonw.exe del sistema.")

    procesos = listar_todos_python()
    if not procesos:
        log("\n  [ ] No hay procesos python/pythonw en el sistema")
        return

    log(f"\n[3.1] Encontrados {len(procesos)} procesos python/pythonw:")
    for pid, nombre, cmdline in procesos:
        cmdline_short = cmdline[:100] + "..." if len(cmdline) > 100 else cmdline
        log(f"  [?] {nombre} PID {pid}: {cmdline_short}")

    log(f"\n[3.2] Matando TODOS con /F /T...")
    for pid, nombre, _ in procesos:
        matar_pid(pid, f"{nombre} PID {pid}", forzar_arbol=True)


def capa_3b():
    log("\n" + "=" * 60)
    log("   CAPA 3b — Kill de cmd/powershell con WAIO (solo si quedó algo)")
    log("=" * 60)

    procesos = listar_waio_no_python()
    if not procesos:
        log("\n  [ ] No hay cmd/powershell con WAIO en cmdline")
        return

    log(f"\n[3b.1] Encontrados {len(procesos)} procesos:")
    for pid, nombre, cmdline in procesos:
        cmdline_short = cmdline[:100] + "..." if len(cmdline) > 100 else cmdline
        log(f"  [?] {nombre} PID {pid}: {cmdline_short}")

    log(f"\n[3b.2] Matando TODOS con /F /T...")
    for pid, nombre, _ in procesos:
        matar_pid(pid, f"{nombre} PID {pid}", forzar_arbol=True)


# ----------------------------------------------------------------------
# Verificación
# ----------------------------------------------------------------------

def verificar_y_reportar():
    log("\n" + "=" * 60)
    log("   VERIFICACIÓN")
    log("=" * 60)

    waio, todos, locks, triggers = reescanear()

    if waio:
        log(f"\n  [!] Quedan {len(waio)} procesos WAIO:")
        for pid, cmdline in waio:
            log(f"      PID {pid}: {cmdline[:100]}")
    else:
        log("\n  [+] No quedan procesos WAIO")

    if todos:
        log(f"\n  [!] Quedan {len(todos)} procesos Python en el sistema:")
        for pid, nombre, cmdline in todos:
            log(f"      {nombre} PID {pid}: {cmdline[:100]}")
    else:
        log("\n  [+] No quedan procesos Python en el sistema")

    if locks:
        log(f"\n  [!] Quedan {len(locks)} locks:")
        for p, e in locks:
            log(f"      {e}: {p}")
    else:
        log("\n  [+] No quedan locks")

    if triggers:
        log(f"\n  [!] Quedan {len(triggers)} triggers:")
        for t in triggers:
            log(f"      {t.name}")
    else:
        log("\n  [+] No quedan triggers")

    # todo_limpio = no quedan procesos WAIO vivos (locks/triggers no cuentan)
    todo_limpio = not waio
    return todo_limpio, todos


def borrar_residuales():
    log("\n[LIMPIEZA] Borrando locks y triggers residuales...")
    for lock_path, etiqueta in LOCKS:
        borrar_lock(lock_path, etiqueta)
    borrar_triggers()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    log("=" * 60)
    log("   KILL WAIO — Detención por capas")
    log("=" * 60)
    log(f"Fecha: {datetime.now().isoformat()}")
    log(f"PID propio: {MI_PID}")
    log(f"Raíz: {SCRIPT_DIR}")
    log(f"Log: {LOG_FILE}")
    log("")
    log("Estrategia:")
    log("  Capa 1: STOP.trigger + matar PIDs de locks + borrar locks.")
    log("  Capa 2: + buscar python/pythonw con WAIO en cmdline.")
    log("  Capa 3: + matar TODOS los python.exe/pythonw.exe con /F /T.")
    log("  Capa 3b: + matar cmd/powershell con WAIO (solo si Capa 3 dejó algo).")
    log("  El propio kill_waio NUNCA se mata.")
    log("  Los triggers se borran al final de Capa 1.")
    log("  todo_limpio = no quedan procesos WAIO vivos (locks/triggers no cuentan).")
    log("")

    if not SCRIPT_DIR.exists():
        log(f"[ERROR] No se encontró {SCRIPT_DIR}")
        return

    log("=" * 60)
    log("   ESTADO INICIAL")
    log("=" * 60)
    waio, todos, locks, triggers = reescanear()
    log(f"\n  Procesos WAIO: {len(waio)}")
    for pid, cmdline in waio:
        log(f"    PID {pid}: {cmdline[:100]}")
    log(f"  Procesos Python totales: {len(todos)}")
    for pid, nombre, cmdline in todos:
        log(f"    {nombre} PID {pid}: {cmdline[:100]}")
    log(f"  Locks: {len(locks)}")
    for p, e in locks:
        log(f"    {e}: {p}")
    log(f"  Triggers: {len(triggers)}")
    for t in triggers:
        log(f"    {t.name}")

    if not waio and not locks and not triggers and not todos:
        log("\n[+] WAIO no está corriendo. Nada que hacer.")
        return

    capa_1()
    time.sleep(ESPERA_ENTRE_CAPAS)
    limpio, todos = verificar_y_reportar()

    if limpio:
        borrar_residuales()
        log("\n" + "=" * 60)
        log("   [+] WAIO detenido en CAPA 1 (básica).")
        log("=" * 60)
        return

    log("\n[!] Quedan procesos WAIO vivos. Subiendo a CAPA 2...")
    capa_2()
    time.sleep(ESPERA_ENTRE_CAPAS)
    limpio, todos = verificar_y_reportar()

    if limpio:
        borrar_residuales()
        log("\n" + "=" * 60)
        log("   [+] WAIO detenido en CAPA 2 (profunda).")
        log("=" * 60)
        return

    log("\n[!] Quedan procesos WAIO vivos. Subiendo a CAPA 3...")
    capa_3()
    time.sleep(ESPERA_ENTRE_CAPAS)
    limpio, todos = verificar_y_reportar()

    if limpio:
        borrar_residuales()
        log("\n" + "=" * 60)
        log("   [+] WAIO detenido en CAPA 3 (total).")
        log("=" * 60)
        return

    log("\n[!] Quedan procesos WAIO vivos. Subiendo a CAPA 3b (extrema)...")
    capa_3b()
    time.sleep(ESPERA_ENTRE_CAPAS)
    limpio, todos = verificar_y_reportar()

    if limpio:
        borrar_residuales()
        log("\n" + "=" * 60)
        log("   [+] WAIO detenido en CAPA 3b (extrema).")
        log("=" * 60)
        return

    borrar_residuales()
    waio_final, todos_final, locks_final, triggers_final = reescanear()
    log("\n" + "=" * 60)
    if not waio_final and not todos_final:
        log("   [+] WAIO detenido (con residuales limpiados).")
    else:
        log("   [!] No se pudo detener todo. Revisar manualmente.")
    log("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log(f"\n[ERROR FATAL] {e}")
        log(traceback.format_exc())
    finally:
        log(f"\n[FIN] Log guardado en: {LOG_FILE}")
        input("\nPresione Enter para salir...")