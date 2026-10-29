import sys
import os
import time
import argparse
from datetime import datetime
from pathlib import Path

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

class EventHandler(FileSystemEventHandler):
    def __init__(self, eventos_filtro, archivo_log):
        self.eventos_filtro = eventos_filtro
        self.archivo_log = archivo_log
        self.contador = 0

    def escribir_evento(self, tipo, ruta):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        linea = f"[{timestamp}] {tipo}: {ruta}\n"
        with open(self.archivo_log, "a", encoding="utf-8") as f:
            f.write(linea)
        print(linea.strip())
        self.contador += 1

    def on_created(self, event):
        if "creacion" in self.eventos_filtro:
            self.escribir_evento("CREADO", event.src_path)

    def on_modified(self, event):
        if "modificacion" in self.eventos_filtro:
            self.escribir_evento("MODIFICADO", event.src_path)

    def on_deleted(self, event):
        if "eliminacion" in self.eventos_filtro:
            self.escribir_evento("ELIMINADO", event.src_path)

    def on_moved(self, event):
        if "movimiento" in self.eventos_filtro:
            self.escribir_evento(f"MOVIDO ({event.src_path} -> {event.dest_path})", "")

def main():
    parser = argparse.ArgumentParser(description='Monitorea cambios en una carpeta')
    parser.add_argument('--ruta', required=True, help='Carpeta a monitorear')
    parser.add_argument('--eventos', default='creacion,modificacion,eliminacion',
                        help='Eventos a detectar: creacion,modificacion,eliminacion,movimiento (separados por coma)')
    parser.add_argument('--tiempo', type=int, default=30, help='Tiempo de monitoreo en segundos (default: 30)')
    parser.add_argument('--log', help='Archivo de log para guardar eventos (opcional)')
    args = parser.parse_args()

    ruta = Path(args.ruta)
    if not ruta.exists():
        print(f"ERROR: La carpeta no existe: {args.ruta}")
        return
    if not ruta.is_dir():
        print(f"ERROR: La ruta no es una carpeta: {args.ruta}")
        return

    eventos_filtro = [e.strip() for e in args.eventos.split(',') if e.strip()]
    
    if args.log:
        log_path = Path(args.log)
    else:
        waio_dir = Path(os.environ.get("USERPROFILE", ".")) / ".waio"
        waio_dir.mkdir(exist_ok=True)
        log_path = waio_dir / "eventos.log"

    print("=" * 70)
    print(f"  MONITOREO DE CARPETA")
    print("=" * 70)
    print(f"  Carpeta     : {ruta.absolute()}")
    print(f"  Eventos     : {', '.join(eventos_filtro)}")
    print(f"  Duracion    : {args.tiempo} segundos")
    print(f"  Log         : {log_path}")
    print("=" * 70)
    print("  Esperando eventos... (Ctrl+C para detener)")
    print("-" * 70)

    event_handler = EventHandler(eventos_filtro, str(log_path))
    observer = Observer()
    observer.schedule(event_handler, str(ruta), recursive=True)
    observer.start()

    try:
        time.sleep(args.tiempo)
    except KeyboardInterrupt:
        print("\n[INTERRUPCION] Deteniendo monitoreo...")
    finally:
        observer.stop()
        observer.join()

    print("-" * 70)
    print(f"  FIN DEL MONITOREO")
    print(f"  Total eventos detectados: {event_handler.contador}")
    if event_handler.contador > 0:
        print(f"  Log guardado en: {log_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()