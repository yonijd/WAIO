# -*- coding: utf-8 -*-
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

TIMEOUT_SEG = 5
REFRESCO_MS = 0.5
MAX_BUFFER_ITEMS = 50

SCRIPT_DIR = Path(sys.argv[0]).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "temp" / "output"
LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOCK_FILE = SCRIPT_DIR / "escucha.lock"
STOP_FILE = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
WISPOUT_FILE = SCRIPT_DIR / "config" / "wispout.json"

LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / f"escucha_output_{datetime.now().strftime('%Y%m%d')}.log"

def escribir_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {mensaje}\n")
    except:
        pass

def sonido_confirmacion():
    try:
        if WISPOUT_FILE.exists():
            with open(WISPOUT_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            if not config.get("sonido", {}).get("activo", True):
                return
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except:
        pass

def copiar_portapapeles(texto):
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        
        data = (texto + '\x00').encode('utf-16-le')
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
        
        user32.CloseClipboard()
        escribir_log(f"Copiado: {len(texto)} caracteres")
        return True
    except Exception as e:
        escribir_log(f"Error ctypes: {e}")
        try:
            subprocess.run(['clip'], input=texto, text=True,
                          encoding='utf-8', errors='replace',
                          creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except:
            return False

def compilar_buffer(buffer):
    if not buffer:
        return ""
    
    if len(buffer) == 1:
        item = buffer[0]
        return item.get("output", "")
    
    partes = []
    for i, item in enumerate(buffer, 1):
        tx_id = item.get("transaccion_id", "?")
        accion_idx = item.get("accion_idx", i)
        total_acciones = item.get("total_acciones", "?")
        comando = item.get("comando", "?")
        output = item.get("output", "")
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

class EscuchaOutput:
    def __init__(self):
        self.buffer = []
        self.timer = None
        self.archivos_vistos = set()
        self.corriendo = True
        
    def reiniciar_timer(self):
        if self.timer:
            self.timer.cancel()
        self.timer = threading.Timer(TIMEOUT_SEG, self.copiar_buffer)
        self.timer.daemon = True
        self.timer.start()
        escribir_log(f"Timer: {TIMEOUT_SEG}s | Buffer: {len(self.buffer)} items")
    
    def copiar_buffer(self):
        if not self.buffer:
            return
        
        texto = compilar_buffer(self.buffer)
        if texto:
            if copiar_portapapeles(texto):
                escribir_log(f"✅ COPIA: {len(self.buffer)} items, {len(texto)} caracteres")
                for item in self.buffer:
                    escribir_log(f"   - {item['transaccion_id']} | {item['comando']}")
                sonido_confirmacion()
            else:
                escribir_log(f"❌ ERROR al copiar {len(self.buffer)} items")
        
        self.buffer = []
        self.timer = None
    
    def agregar_al_buffer(self, item):
        if not item:
            return
        
        self.buffer.append(item)
        
        if len(self.buffer) > MAX_BUFFER_ITEMS:
            escribir_log(f"Buffer lleno ({MAX_BUFFER_ITEMS}), copiando forzado")
            self.copiar_buffer()
            return
        
        escribir_log(f"📥 +{item['archivo']} | {item['transaccion_id']} | {item['comando']} | Buffer: {len(self.buffer)}")
        self.reiniciar_timer()
    
    def escanear_output(self):
        if not OUTPUT_DIR.exists():
            return []
        
        try:
            archivos = list(OUTPUT_DIR.glob("*.json"))
            archivos = [a for a in archivos if a.name != "PROMPT_WAIO.txt"]
            archivos.sort(key=lambda x: x.stat().st_mtime)
            return archivos
        except Exception as e:
            escribir_log(f"Error escaneando: {e}")
            return []
    
    def procesar_nuevos(self):
        archivos_actuales = set(self.escanear_output())
        archivos_nuevos = archivos_actuales - self.archivos_vistos
        
        for archivo in archivos_nuevos:
            if archivo.is_file() and archivo.stat().st_size > 0:
                item = procesar_json(archivo)
                if item:
                    self.agregar_al_buffer(item)
        
        self.archivos_vistos = archivos_actuales
    
    def verificar_stop(self):
        if STOP_FILE.exists():
            escribir_log("STOP signal detectada")
            self.corriendo = False
            return True
        return False
    
    def ejecutar(self):
        escribir_log("=" * 60)
        escribir_log("ESCUCHA_OUTPUT V2 INICIADO")
        escribir_log(f"Output: {OUTPUT_DIR}")
        escribir_log(f"Timeout: {TIMEOUT_SEG}s")
        escribir_log("=" * 60)
        
        self.archivos_vistos = set(self.escanear_output())
        escribir_log(f"Ignorando {len(self.archivos_vistos)} archivos existentes")
        
        while self.corriendo:
            try:
                if self.verificar_stop():
                    break
                
                self.procesar_nuevos()
                time.sleep(REFRESCO_MS)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                escribir_log(f"Error: {e}")
                time.sleep(1)
        
        if self.buffer:
            escribir_log(f"Cerrando con {len(self.buffer)} items pendientes")
            self.copiar_buffer()
        
        escribir_log("ESCUCHA_OUTPUT V2 FINALIZADO")
        escribir_log("=" * 60)

def verificar_lock():
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            try:
                subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW)
                return False
            except:
                LOCK_FILE.unlink()
        except:
            LOCK_FILE.unlink()
    
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except:
        return True

def limpiar_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except:
        pass

def main():
    if not verificar_lock():
        print("ESCUCHA_OUTPUT ya esta corriendo")
        sys.exit(0)
    
    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except:
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