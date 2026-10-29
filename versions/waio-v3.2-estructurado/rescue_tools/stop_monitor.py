import os
import sys
import time
import signal
from pathlib import Path

PID_FILE = Path("monitor.pid")

def main():
    if not PID_FILE.exists():
        print("No hay monitor en ejecucion.")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        
        print(f"Deteniendo monitor (PID: {pid})...")
        
        # Intentar terminar el proceso
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(1)
            print("Monitor detenido.")
        except ProcessLookupError:
            print("El proceso ya no existe.")
        except Exception as e:
            print(f"Error al detener: {e}")
        
        # Limpiar archivo PID
        if PID_FILE.exists():
            PID_FILE.unlink()
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()