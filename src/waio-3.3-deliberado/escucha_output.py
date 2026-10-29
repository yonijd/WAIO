# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
escucha_output.py - Compilador de resultados de WAIO.

Monitorea temp/output/ y agrupa los resultados en un solo bloque.
Cuando pasan N segundos sin nuevos JSONs, los compila, los ordena
por (transaccion_id, accion_idx) y los copia al portapapeles.

Configurable desde waio_config.json:
  - output_buffer_max_items
  - output_buffer_timeout_seconds
  - output_scan_interval_seconds

Version v3 (B1):
  - copiar_portapapeles con ctypes (Unicode nativo) + timeout en hilo
  - copiar_buffer_safe con try/except/finally (no muere el Timer)
  - procesar_nuevos con update (no pierde archivos)
  - sonido_confirmacion con cache por mtime
  - compilar_buffer sanitiza \x00 -> [NUL]
"""

import os
import sys
import json
import time
import threading
import subprocess
import ctypes
import winsound
from pathlib import Path
from datetime import datetime

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "temp" / "output"
LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOCK_FILE = SCRIPT_DIR / "escucha.lock"
STOP_FILE = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
WISPOUT_FILE = SCRIPT_DIR / "config" / "wispout.json"
CONFIG_FILE = SCRIPT_DIR / "config" / "waio_config.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"escucha_output_{TIMESTAMP}.log"

try:
    LOG_FILE.touch()
except Exception:
    pass


# ----------------------------------------------------------------------
# Config
# ----------------------------------------------------------------------

def config_get(clave, default):
    try:
        if not CONFIG_FILE.exists():
            return default
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
        valor = config.get(clave, default)
        if valor is None:
            return default
        if isinstance(default, float):
            return float(valor)
        elif isinstance(default, int):
            return int(valor)
        return valor
    except Exception:
        return default


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def escribir_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
    except Exception:
        pass


# ----------------------------------------------------------------------
# Cache de wispout (por mtime)
# ----------------------------------------------------------------------

_wispout_cache = None
_wispout_mtime = None


def cargar_wispout():
    global _wispout_cache, _wispout_mtime
    try:
        if not WISPOUT_FILE.exists():
            return {}
        mtime = WISPOUT_FILE.stat().st_mtime
        if _wispout_cache is not None and _wispout_mtime == mtime:
            return _wispout_cache
        with open(WISPOUT_FILE, "r", encoding="utf-8") as f:
            _wispout_cache = json.load(f)
        _wispout_mtime = mtime
        return _wispout_cache
    except Exception:
        return {}


# ----------------------------------------------------------------------
# Sonido
# ----------------------------------------------------------------------

def sonido_confirmacion():
    try:
        config = cargar_wispout()
        if not config.get("sonido", {}).get("activo", True):
            return
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except Exception:
        pass


# ----------------------------------------------------------------------
# Portapapeles (ctypes, Unicode nativo, con timeout)
# ----------------------------------------------------------------------

def copiar_portapapeles(texto):
    """Copia al portapapeles usando ctypes (UTF-16 nativo) con timeout de 3s."""
    resultado = {"ok": False, "error": None}

    def _copiar():
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
            kernel32.GlobalAlloc.restype = ctypes.c_void_p
            kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalLock.restype = ctypes.c_void_p
            kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
            kernel32.GlobalUnlock.restype = ctypes.c_int
            kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
            kernel32.GlobalFree.restype = ctypes.c_void_p

            user32.OpenClipboard.argtypes = [ctypes.c_void_p]
            user32.OpenClipboard.restype = ctypes.c_int
            user32.EmptyClipboard.restype = ctypes.c_int
            user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
            user32.SetClipboardData.restype = ctypes.c_void_p
            user32.CloseClipboard.restype = ctypes.c_int

            if not user32.OpenClipboard(None):
                raise Exception("OpenClipboard fallo")
            try:
                user32.EmptyClipboard()
                data = (texto + "\x00").encode("utf-16-le")
                hmem = kernel32.GlobalAlloc(0x2002, len(data))
                if not hmem:
                    raise Exception("GlobalAlloc fallo")
                ptr = kernel32.GlobalLock(hmem)
                if not ptr:
                    kernel32.GlobalFree(hmem)
                    raise Exception("GlobalLock fallo")
                ctypes.memmove(ptr, data, len(data))
                kernel32.GlobalUnlock(hmem)
                CF_UNICODETEXT = 13
                if not user32.SetClipboardData(CF_UNICODETEXT, hmem):
                    kernel32.GlobalFree(hmem)
                    raise Exception("SetClipboardData fallo")
            finally:
                user32.CloseClipboard()
            resultado["ok"] = True
        except Exception as e:
            resultado["error"] = str(e)

    hilo = threading.Thread(target=_copiar, daemon=True)
    hilo.start()
    hilo.join(timeout=3)

    if hilo.is_alive():
        escribir_log("Copiado: timeout (3s) - ctypes colgado en OpenClipboard")
        return False

    if resultado["ok"]:
        escribir_log(f"Copiado: {len(texto)} caracteres (ctypes)")
        return True
    else:
        escribir_log(f"Error ctypes: {resultado['error']}")
        return False


# ----------------------------------------------------------------------
# Compilacion del buffer
# ----------------------------------------------------------------------

def sanitizar_nul(texto):
    if not isinstance(texto, str):
        return ""
    return texto.replace("\x00", "[NUL]")


def compilar_buffer(buffer):
    if not buffer:
        return ""

    if len(buffer) == 1:
        item = buffer[0]
        return sanitizar_nul(item.get("output", ""))

    partes = []
    for i, item in enumerate(buffer, 1):
        tx_id = item.get("transaccion_id", "?")
        accion_idx = item.get("accion_idx", i)
        total_acciones = item.get("total_acciones", "?")
        comando = item.get("comando", "?")
        output = sanitizar_nul(item.get("output", ""))
        status = item.get("status", "ok")

        if total_acciones and total_acciones != "?":
            header = f"[{i}] TX: {tx_id} | Accion {accion_idx}/{total_acciones} | Comando: {comando}"
        else:
            header = f"[{i}] TX: {tx_id} | Accion {accion_idx} | Comando: {comando}"

        if status == "error":
            partes.append(f"{header} [ERROR]\n{output}")
        else:
            partes.append(f"{header}\n{output}")

    return "\n---\n".join(partes)


def procesar_json(ruta_archivo):
    try:
        with open(ruta_archivo, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {
            "transaccion_id": data.get("transaccion_id", "sin_id"),
            "accion_idx": data.get("accion_idx", 0),
            "total_acciones": data.get("total_acciones", None),
            "comando": data.get("comando", "?"),
            "output": data.get("output", ""),
            "status": data.get("status", "ok"),
            "timestamp": data.get("timestamp", ""),
            "archivo": ruta_archivo.name
        }
    except Exception as e:
        escribir_log(f"Error leyendo {ruta_archivo.name}: {e}")
        return None


# ----------------------------------------------------------------------
# Escucha
# ----------------------------------------------------------------------

class EscuchaOutput:
    def __init__(self):
        self.buffer = []
        self.timer = None
        self.archivos_vistos = set()
        self.corriendo = True
        self.timeout_seg = config_get("output_buffer_timeout_seconds", 5.0)
        self.max_buffer = config_get("output_buffer_max_items", 50)
        self.scan_interval = config_get("output_scan_interval_seconds", 0.5)

    def reiniciar_timer(self):
        if self.timer:
            try:
                self.timer.cancel()
            except Exception:
                pass
        self.timer = threading.Timer(self.timeout_seg, self.copiar_buffer_safe)
        self.timer.daemon = True
        self.timer.start()
        escribir_log(f"Timer: {self.timeout_seg}s | Buffer: {len(self.buffer)} items")

    def copiar_buffer_safe(self):
        try:
            self.copiar_buffer()
        except Exception as e:
            escribir_log(f"Error en copiar_buffer: {e}")
        finally:
            self.buffer = []
            self.timer = None

    def copiar_buffer(self):
        if not self.buffer:
            return

        self.buffer.sort(key=lambda x: (
            x.get("transaccion_id", ""),
            x.get("accion_idx", 0)
        ))

        texto = compilar_buffer(self.buffer)
        if texto:
            if copiar_portapapeles(texto):
                escribir_log(f"COPIA: {len(self.buffer)} items, {len(texto)} caracteres")
                for item in self.buffer:
                    escribir_log(f"   - {item['transaccion_id']} | {item['comando']}")
                sonido_confirmacion()
            else:
                escribir_log(f"ERROR al copiar {len(self.buffer)} items")

    def agregar_al_buffer(self, item):
        if not item:
            return

        self.buffer.append(item)

        if len(self.buffer) >= self.max_buffer:
            escribir_log(f"Buffer lleno ({self.max_buffer}), copiando forzado")
            self.copiar_buffer_safe()
            return

        escribir_log(f"+{item['archivo']} | {item['transaccion_id']} | {item['comando']} | Buffer: {len(self.buffer)}")
        self.reiniciar_timer()

    def escanear_output(self):
        if not OUTPUT_DIR.exists():
            return []
        try:
            archivos = list(OUTPUT_DIR.glob("*.json"))
            archivos.sort(key=lambda x: x.name)
            return archivos
        except Exception as e:
            escribir_log(f"Error escaneando: {e}")
            return []

    def procesar_nuevos(self):
        archivos_actuales = self.escanear_output()
        for archivo in archivos_actuales:
            if archivo in self.archivos_vistos:
                continue
            if archivo.is_file() and archivo.stat().st_size > 0:
                item = procesar_json(archivo)
                if item:
                    self.agregar_al_buffer(item)
        self.archivos_vistos.update(archivos_actuales)

    def verificar_stop(self):
        if STOP_FILE.exists():
            escribir_log("STOP signal detectada")
            self.corriendo = False
            return True
        return False

    def ejecutar(self):
        escribir_log("=" * 60)
        escribir_log("ESCUCHA_OUTPUT INICIADO")
        escribir_log(f"Output: {OUTPUT_DIR}")
        escribir_log(f"Timeout: {self.timeout_seg}s")
        escribir_log(f"Max buffer: {self.max_buffer} items")
        escribir_log(f"Scan interval: {self.scan_interval}s")
        escribir_log("Modo portapapeles: ctypes (UTF-16, timeout 3s)")
        escribir_log("=" * 60)

        self.archivos_vistos = set(self.escanear_output())
        escribir_log(f"Ignorando {len(self.archivos_vistos)} archivos existentes")

        while self.corriendo:
            try:
                if self.verificar_stop():
                    break
                self.procesar_nuevos()
                time.sleep(self.scan_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                escribir_log(f"Error: {e}")
                time.sleep(1)

        if self.buffer:
            escribir_log(f"Cerrando con {len(self.buffer)} items pendientes")
            self.copiar_buffer_safe()

        escribir_log("ESCUCHA_OUTPUT FINALIZADO")
        escribir_log("=" * 60)


# ----------------------------------------------------------------------
# Lock
# ----------------------------------------------------------------------

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


def verificar_lock():
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, "r") as f:
                pid = int(f.read().strip())
            if pid_es_python(pid):
                return False
            escribir_log(f"Lock huerfano detectado (PID {pid})")
            LOCK_FILE.unlink()
        except Exception:
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass

    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except Exception:
        return True


def limpiar_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    if not verificar_lock():
        print("ESCUCHA_OUTPUT ya esta corriendo")
        sys.exit(0)

    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except Exception:
            pass

    app = EscuchaOutput()
    try:
        app.ejecutar()
    except Exception as e:
        escribir_log(f"Error fatal: {e}")
    finally:
        limpiar_lock()


if __name__ == "__main__":
    main()
