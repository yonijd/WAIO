import os
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_ORIGEN = os.path.join(BASE_DIR, "waiovoz", "mensajescreados")
CARPETA_DESTINO = os.path.join(BASE_DIR, "waiovoz", "mensajesleidos")
LOG_FILE = os.path.join(BASE_DIR, "waiovoz", "voz.log")
PROCESADOS_FILE = os.path.join(BASE_DIR, "waiovoz", "procesados.json")

MAX_ARCHIVOS = 50
MAX_LOG_BYTES = 100 * 1024  # 100 KB


def limpiar_carpeta(carpeta):
    if not os.path.exists(carpeta):
        return
    try:
        archivos = sorted([f for f in os.listdir(carpeta) if f.endswith(".json")])
        if len(archivos) > MAX_ARCHIVOS:
            excedente = archivos[:len(archivos) - MAX_ARCHIVOS]
            for archivo in excedente:
                try:
                    os.remove(os.path.join(carpeta, archivo))
                except:
                    pass
    except Exception as e:
        print(f"Error limpiando {carpeta}: {e}")


def limpiar_procesados():
    if not os.path.exists(PROCESADOS_FILE):
        return
    try:
        with open(PROCESADOS_FILE, "r", encoding="utf-8") as f:
            procesados = json.load(f)
        if len(procesados) > MAX_ARCHIVOS:
            procesados = procesados[-MAX_ARCHIVOS:]
            with open(PROCESADOS_FILE, "w", encoding="utf-8") as f:
                json.dump(procesados, f, indent=2)
    except:
        pass


def limpiar_log():
    if not os.path.exists(LOG_FILE):
        return
    try:
        if os.path.getsize(LOG_FILE) > MAX_LOG_BYTES:
            backup = LOG_FILE + f".{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.rename(LOG_FILE, backup)
    except:
        pass


if __name__ == "__main__":
    limpiar_carpeta(CARPETA_ORIGEN)
    limpiar_carpeta(CARPETA_DESTINO)
    limpiar_procesados()
    limpiar_log()
    print("Limpieza completada")
