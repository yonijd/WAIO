import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path
from collections import deque

def instalar_si_falta(modulo, paquete=None):
    if paquete is None:
        paquete = modulo
    try:
        __import__(modulo)
        return True
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])
        try:
            __import__(modulo)
            return True
        except ImportError:
            return False

if not instalar_si_falta("watchdog"):
    print("ERROR: No se pudo instalar watchdog")
    sys.exit(1)

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

RUTA_WAIO = Path(os.environ.get("USERPROFILE", ".")) / ".waio"
WISP_FILE = RUTA_WAIO / "wispout.json"
LOG_DIR = RUTA_WAIO / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "eventos_monitor.log"
STOP_FILE = RUTA_WAIO / "EVENTS_STOP.trigger"
LOCK_FILE = RUTA_WAIO / "events.lock"

EVENT_BUFFER = deque(maxlen=50)
ULTIMO_EVENTO = {}

def crear_lock():
    try:
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        return True
    except:
        return False

def eliminar_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
        return True
    except:
        return False

def existe_lock():
    return LOCK_FILE.exists()

def leer_ultimas_lineas_log(n=10):
    try:
        if not LOG_FILE.exists():
            return []
        with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lineas = f.readlines()
        lineas = [l.strip() for l in lineas if l.strip()]
        return lineas[-n:] if lineas else []
    except:
        return []

def limpiar_wisp():
    """Restaura el wispout.json a su estado original (sin eventos)"""
    try:
        if WISP_FILE.exists():
            with open(WISP_FILE, 'r', encoding='utf-8') as f:
                wisp = json.load(f)
            wisp["recordatorio"]["mensaje"] = "Recomendacion: espera la confirmacion de WAIO antes de continuar."
            with open(WISP_FILE, 'w', encoding='utf-8') as f:
                json.dump(wisp, f, indent=2, ensure_ascii=False)
            print("[WISP] Recordatorio limpiado")
    except Exception as e:
        print(f"[ERROR] Limpiando wisp: {e}")

class EventHandler(FileSystemEventHandler):
    def __init__(self):
        self.contador = 0

    def on_any_event(self, event):
        if event.is_directory:
            return
        
        ignorar = [".log", ".pid", "wispout.json", "events.lock", "EVENTS_STOP.trigger", "logs"]
        if any(x in str(event.src_path) for x in ignorar):
            return
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        tipo = event.event_type.upper()
        nombre = os.path.basename(event.src_path)
        
        clave = f"{tipo}_{nombre}"
        ahora = time.time()
        if clave in ULTIMO_EVENTO and ahora - ULTIMO_EVENTO[clave] < 1:
            return
        ULTIMO_EVENTO[clave] = ahora
        
        EVENT_BUFFER.append(f"[{timestamp}] {tipo}: {nombre}")
        self.contador += 1
        actualizar_wisp()

    def on_created(self, event):
        self.on_any_event(event)

    def on_modified(self, event):
        self.on_any_event(event)

    def on_deleted(self, event):
        self.on_any_event(event)

    def on_moved(self, event):
        timestamp = datetime.now().strftime("%H:%M:%S")
        nombre_origen = os.path.basename(event.src_path)
        nombre_destino = os.path.basename(event.dest_path)
        
        clave = f"MOVED_{nombre_origen}_{nombre_destino}"
        ahora = time.time()
        if clave in ULTIMO_EVENTO and ahora - ULTIMO_EVENTO[clave] < 1:
            return
        ULTIMO_EVENTO[clave] = ahora
        
        EVENT_BUFFER.append(f"[{timestamp}] MOVED: {nombre_origen} -> {nombre_destino}")
        self.contador += 1
        actualizar_wisp()

    def on_opened(self, event):
        self.on_any_event(event)

    def on_closed(self, event):
        self.on_any_event(event)

def actualizar_wisp():
    if not EVENT_BUFFER:
        return
    
    try:
        if WISP_FILE.exists():
            with open(WISP_FILE, 'r', encoding='utf-8') as f:
                wisp = json.load(f)
        else:
            wisp = {
                "_waio_firma": "WAIO-V3-WISPOUT-2026",
                "encabezado": {"plantilla": "WAIO {version} | {perfil} | {limite} | {borrado}", "mostrar": True},
                "recordatorio": {"activo": True, "mensaje": "Espera la confirmacion de WAIO antes de continuar."},
                "susurro": {"activo": True, "cada_cuantas_acciones": 3, "mensaje": "INSTRUCCION: Volcado en .waio/memoria/"}
            }
        
        ultimas_lineas = leer_ultimas_lineas_log(3)
        if ultimas_lineas:
            eventos_texto = "\n".join(ultimas_lineas)
            mensaje = f"[MONITOR] Eventos recientes:\n{eventos_texto}"
        else:
            mensaje = "[MONITOR] Sin eventos recientes"
        
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {len(EVENT_BUFFER)} eventos\n")
            for e in list(EVENT_BUFFER):
                f.write(f"  {e}\n")
        
        EVENT_BUFFER.clear()
        
        wisp["recordatorio"]["mensaje"] = mensaje
        wisp["recordatorio"]["activo"] = True
        
        with open(WISP_FILE, 'w', encoding='utf-8') as f:
            json.dump(wisp, f, indent=2, ensure_ascii=False)
        
    except Exception as e:
        print(f"[ERROR] Actualizando wisp: {e}")

def debe_detener():
    return STOP_FILE.exists()

def main():
    if existe_lock():
        print("[EVENT VISOR] Ya hay una instancia corriendo.")
        print("  Si queres detenerla, hace click en EVENTS en el visor de WAIO.")
        sys.exit(0)
    
    if not crear_lock():
        print("[ERROR] No se pudo crear lock")
        sys.exit(1)
    
    if STOP_FILE.exists():
        STOP_FILE.unlink()
    
    print("=" * 70)
    print("  EVENT VISOR - MONITOR DE EVENTOS")
    print("=" * 70)
    print(f"  PID: {os.getpid()}")
    print(f"  Log: {LOG_FILE}")
    print(f"  WISP: {WISP_FILE}")
    print("=" * 70)
    print("  Mostrando las ultimas 3 lineas del log")
    print("  Para detener: Click en EVENTS en el visor de WAIO")
    print("  Al detener: Limpia el recordatorio de WAIO")
    print("-" * 70)

    event_handler = EventHandler()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(0.1)
            if debe_detener():
                print("\n[STOP] Deteniendo event_visor...")
                STOP_FILE.unlink()
                limpiar_wisp()  # Limpiar recordatorio al detener
                break
    except KeyboardInterrupt:
        print("\n[INTERRUPCION] Deteniendo event_visor...")
        limpiar_wisp()
    finally:
        observer.stop()
        observer.join()
        eliminar_lock()
        print(f"  Total eventos detectados: {event_handler.contador}")
        print("=" * 70)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERROR: {e}")
        eliminar_lock()