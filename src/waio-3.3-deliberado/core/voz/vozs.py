import subprocess
import sys
import os
import json
import time
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_LECTURA = os.path.join(BASE_DIR, "waiovoz", "mensajesleidos")
LOG_FILE = os.path.join(BASE_DIR, "waiovoz", "voz.log")
LOCK_FILE = os.path.join(BASE_DIR, "waiovoz", "vozs.lock")
PROCESADOS_FILE = os.path.join(BASE_DIR, "waiovoz", "procesados.json")
CONFIG_FILE = os.path.join(BASE_DIR, "waiovoz", "voz_config.json")

# Voces hardcodeadas con su velocidad base (caracteres por segundo)
VOCES = {
    "Microsoft Ana Desktop": 15.0,
    "Microsoft Helena Desktop": 14.0,
    "Microsoft Pablo": 12.0,
    "Microsoft Laura": 13.0,
    "Microsoft Zira Desktop": 16.0,
}
CHARS_POR_SEGUNDO_DEFAULT = 15.0
MARGEN = 1.4
OVERHEAD = 10
TIMEOUT_MINIMO = 15
TIMEOUT_MAXIMO = 300

def log(accion, detalle=""):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {accion}: {detalle}\n")
    except:
        pass

def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def calcular_timeout(texto, velocidad, voz_nombre):
    # Si la voz esta en el diccionario, usa su valor. Si no, usa el default.
    chars_por_seg = VOCES.get(voz_nombre, CHARS_POR_SEGUNDO_DEFAULT)
    factor = 1.0 - (velocidad / 20.0)
    if factor <= 0:
        factor = 0.1
    chars_por_seg = chars_por_seg / factor
    estimado = len(texto) / chars_por_seg
    timeout = estimado * MARGEN + OVERHEAD
    return max(TIMEOUT_MINIMO, min(TIMEOUT_MAXIMO, timeout))

def ejecutar_powershell(comando, timeout):
    subprocess.run(
        ["powershell", "-Command", comando],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW,
        timeout=timeout
    )

def hablar(texto, voz_nombre, velocidad, volumen, timeout):
    texto_seguro = texto.replace('"', '`"').replace("'", "`'")
    cmd = (
        'Add-Type -AssemblyName System.Speech; '
        '$voz = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        f'$voz.SelectVoice("{voz_nombre}"); '
        f'$voz.Rate = {velocidad}; '
        f'$voz.Volume = {volumen}; '
        f'$voz.Speak("{texto_seguro}")'
    )
    ejecutar_powershell(cmd, timeout)
    log("HABLAR", f"{len(texto)} caracteres | voz={voz_nombre} | velocidad={velocidad} | timeout={timeout:.1f}s")

def cargar_procesados():
    if os.path.exists(PROCESADOS_FILE):
        try:
            with open(PROCESADOS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except:
            pass
    return set()

def guardar_procesados(procesados):
    try:
        with open(PROCESADOS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(procesados), f, indent=2)
    except:
        pass

def main():
    log("EJECUCION", "Iniciando vozs.py")
    
    if os.path.exists(LOCK_FILE):
        log("EJECUCION", "Ya hay otro vozs.py activo. Saliendo.")
        return
    
    try:
        os.makedirs(os.path.dirname(LOCK_FILE), exist_ok=True)
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        log("EJECUCION", f"Lock creado (PID: {os.getpid()})")
    except Exception as e:
        log("ERROR LOCK", str(e))
        return
    
    try:
        if not os.path.exists(CARPETA_LECTURA):
            os.makedirs(CARPETA_LECTURA)
        
        config = cargar_config()
        procesados = cargar_procesados()
        
        while True:
            try:
                archivos = sorted([f for f in os.listdir(CARPETA_LECTURA) if f.startswith("msg_") and f.endswith(".json")])
            except Exception as e:
                log("ERROR LISTAR", str(e))
                break
                
            pendientes = [f for f in archivos if f not in procesados]
            
            if not pendientes:
                log("ESCUCHA", "No hay mensajes pendientes. Cerrando.")
                break
            
            for archivo in pendientes:
                ruta_archivo = os.path.join(CARPETA_LECTURA, archivo)
                try:
                    with open(ruta_archivo, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    texto = data.get("texto", "").strip()
                    if not texto:
                        procesados.add(archivo)
                        guardar_procesados(procesados)
                        continue
                    
                    # Parametros del mensaje (si estan)
                    voz_nombre = data.get("voz_nombre") or config.get("voz", "Microsoft Ana Desktop")
                    try:
                        velocidad = int(data.get("velocidad", config.get("velocidad", 0)))
                    except:
                        velocidad = 0
                    try:
                        volumen = int(data.get("volumen", config.get("volumen", 100)))
                    except:
                        volumen = 100
                    
                    timeout = calcular_timeout(texto, velocidad, voz_nombre)
                    log("PROCESAR", f"Reproduciendo: {len(texto)} caracteres | voz={voz_nombre} | vel={velocidad} | timeout={timeout:.1f}s")
                    hablar(texto, voz_nombre, velocidad, volumen, timeout)
                    procesados.add(archivo)
                    guardar_procesados(procesados)
                    log("PROCESAR", f"Mensaje {archivo} procesado")
                except subprocess.TimeoutExpired:
                    log("ERROR TIMEOUT", f"Timeout hablando {archivo}")
                    procesados.add(archivo)
                    guardar_procesados(procesados)
                except Exception as e:
                    log("ERROR PROCESAR", f"Error con {archivo}: {str(e)}")
                    procesados.add(archivo)
                    guardar_procesados(procesados)
            
            time.sleep(0.5)
    except KeyboardInterrupt:
        log("EJECUCION", "Interrupcion recibida")
    finally:
        try:
            os.remove(LOCK_FILE)
            log("EJECUCION", "Lock eliminado")
        except:
            pass

if __name__ == "__main__":
    main()
