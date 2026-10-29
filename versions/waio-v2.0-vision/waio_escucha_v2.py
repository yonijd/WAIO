# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import glob
import shutil
import winreg
import subprocess
from pathlib import Path
from datetime import datetime

# ================= CONFIGURACION =================
TIEMPO_ESPERA_SEG = 2
EXTENSION = "*.json"

# Obtener directorios
SCRIPT_DIR = Path(sys.argv[0]).parent.resolve()

# Procesar argumento --cwd para directorio de trabajo
WORK_DIR = SCRIPT_DIR
if len(sys.argv) > 2 and sys.argv[1] == "--cwd":
    try:
        WORK_DIR = Path(sys.argv[2]).resolve()
    except Exception as e:
        print(f"Error cambiando directorio: {e}")

# Cambiar al directorio de trabajo
os.chdir(WORK_DIR)

# Configurar rutas relativas a SCRIPT_DIR (donde esta instalado WAIO)
JSONOUT_DIR = str(SCRIPT_DIR / "jsonout")
OUTPUT_DIR = str(SCRIPT_DIR / "output")
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

MAX_READ_DEFAULT = 100000
ABSOLUTE_MAX_READ = 10000000
TIMESTAMP_LOG = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"waio_escucha_{TIMESTAMP_LOG}.log"
STOP_FILE = str(SCRIPT_DIR / "STOP.trigger")

# Mapeo de comandos (ingles <-> español)
MAPEO_COMANDOS = {
    "create_folder": "crear_carpeta",
    "crear_carpeta": "crear_carpeta",
    "mkdir": "crear_carpeta",
    "create_file": "crear_archivo",
    "crear_archivo": "crear_archivo",
    "write_file": "crear_archivo",
    "write": "crear_archivo",
    "list_dir": "listar_directorio",
    "listar_directorio": "listar_directorio",
    "ls": "listar_directorio",
    "read_file": "leer_archivo",
    "leer_archivo": "leer_archivo",
    "read": "leer_archivo",
    "delete_file": "eliminar_archivo",
    "eliminar_archivo": "eliminar_archivo",
    "rm": "eliminar_archivo",
    "del": "eliminar_archivo",
    "delete_folder": "eliminar_carpeta",
    "eliminar_carpeta": "eliminar_carpeta",
    "rmdir": "eliminar_carpeta",
    "rd": "eliminar_carpeta",
    "move_file": "mover_archivo",
    "mover_archivo": "mover_archivo",
    "move": "mover_archivo",
    "mv": "mover_archivo",
    "rename": "mover_archivo",
    "copy_file": "copiar_archivo",
    "copiar_archivo": "copiar_archivo",
    "copy": "copiar_archivo",
    "cp": "copiar_archivo",
    "file_exists": "existe_archivo",
    "existe_archivo": "existe_archivo",
    "exists": "existe_archivo",
    "check": "existe_archivo",
    "file_size": "obtener_tamano",
    "obtener_tamano": "obtener_tamano",
    "obtener_tamaño": "obtener_tamano",
    "size": "obtener_tamano",
    "get_size": "obtener_tamano",
    "modified_date": "fecha_modificacion",
    "fecha_modificacion": "fecha_modificacion",
    "fecha_modificación": "fecha_modificacion",
    "modified": "fecha_modificacion",
    "mtime": "fecha_modificacion"
}

COMANDOS_PERMITIDOS = {
    "crear_archivo", "crear_carpeta", "listar_directorio", "leer_archivo",
    "eliminar_archivo", "eliminar_carpeta", "mover_archivo", "copiar_archivo",
    "existe_archivo", "obtener_tamano", "fecha_modificacion"
}

# ================= FUNCIONES DE DETECCION =================

def obtener_directorio_descargas():
    ruta_std = Path.home() / "Downloads"
    if ruta_std.exists() and ruta_std.is_dir():
        escribir_log(f"Downloads detectado via UserProfile: {ruta_std}")
        return ruta_std
    
    ruta_esp = Path.home() / "Descargas"
    if ruta_esp.exists() and ruta_esp.is_dir():
        escribir_log(f"Descargas detectado via UserProfile: {ruta_esp}")
        return ruta_esp
    
    try:
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        try:
            valor = winreg.QueryValueEx(clave, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            ruta_reg = Path(valor)
            if ruta_reg.exists() and ruta_reg.is_dir():
                escribir_log(f"Downloads detectado via registro: {ruta_reg}")
                return ruta_reg
        except:
            pass
        winreg.CloseKey(clave)
    except Exception as e:
        escribir_log(f"Error leyendo registro: {e}")
    
    escribir_log("WARNING: No se pudo detectar Downloads, usando directorio actual")
    return Path.cwd()

def ruta_segura(ruta_str):
    try:
        ruta = Path(ruta_str)
        if not ruta.is_absolute():
            ruta = WORK_DIR / ruta
        ruta = ruta.resolve()
        ruta.relative_to(WORK_DIR)
        return ruta
    except (ValueError, OSError):
        escribir_log(f"SEGURIDAD: Ruta bloqueada - {ruta_str}")
        return None

def escribir_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="ascii", errors="replace") as log:
            log.write(f"[{timestamp}] {mensaje}\n")
    except:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] {mensaje}\n")

def normalizar_comando(comando):
    cmd = comando.lower().strip()
    return MAPEO_COMANDOS.get(cmd, cmd)

def verificar_stop():
    stop_path = Path(STOP_FILE)
    if stop_path.exists():
        escribir_log("KILL_SWITCH detectado")
        return True
    return False

def guardar_resultado_json(transaccion_id, accion_idx, comando, status, output):
    try:
        output_path = Path(OUTPUT_DIR)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        nombre_archivo = f"{transaccion_id}_{accion_idx}_{timestamp}.json"
        archivo_json = output_path / nombre_archivo
        
        datos = {
            "transaccion_id": transaccion_id,
            "accion_idx": accion_idx,
            "comando": comando,
            "status": status,
            "output": output,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(archivo_json, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        
        escribir_log(f"JSON creado: {nombre_archivo}")
        
        texto = f"Comando: {comando}\nStatus: {status}\nResultado: {output}"
        try:
            subprocess.run(['clip'], input=texto, text=True,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            escribir_log("Resultado copiado al portapapeles")
        except Exception as e:
            escribir_log(f"Error al copiar al portapapeles: {e}")
    except Exception as e:
        escribir_log(f"Error guardando JSON: {e}")

# ================= EJECUTOR DE COMANDOS =================

def ejecutar_comando(accion, transaccion_id, accion_idx):
    comando_raw = accion.get("comando", "")
    comando = normalizar_comando(comando_raw)
    
    if comando not in COMANDOS_PERMITIDOS:
        escribir_log(f"Comando no soportado: {comando_raw}")
        return False

    # ========== ESCRITURA ==========
    
    if comando == "crear_archivo":
        ruta_str = accion.get("ruta")
        contenido = accion.get("contenido", "")
        confirmar = accion.get("confirmar", False)
        if not ruta_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            escribir_log(f"Archivo creado: {ruta.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Archivo creado: {ruta.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "crear_carpeta":
        ruta_str = accion.get("ruta")
        confirmar = accion.get("confirmar", False)
        if not ruta_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            ruta.mkdir(parents=True, exist_ok=True)
            escribir_log(f"Carpeta creada: {ruta.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Carpeta creada: {ruta.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "eliminar_archivo":
        ruta_str = accion.get("ruta")
        confirmar = accion.get("confirmar", False)
        if not ruta_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Archivo no existe: {ruta_str}")
                return False
            if not ruta.is_file():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"No es un archivo: {ruta_str}")
                return False
            ruta.unlink()
            escribir_log(f"Archivo eliminado: {ruta.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Archivo eliminado: {ruta.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "eliminar_carpeta":
        ruta_str = accion.get("ruta")
        confirmar = accion.get("confirmar", False)
        if not ruta_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Carpeta no existe: {ruta_str}")
                return False
            if not ruta.is_dir():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"No es una carpeta: {ruta_str}")
                return False
            shutil.rmtree(ruta)
            escribir_log(f"Carpeta eliminada: {ruta.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Carpeta eliminada: {ruta.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "mover_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        confirmar = accion.get("confirmar", False)
        if not origen_str or not destino_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Origen no existe: {origen_str}")
                return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origen), str(destino))
            escribir_log(f"Movido: {origen.name} -> {destino.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Movido: {origen.name} -> {destino.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "copiar_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        confirmar = accion.get("confirmar", False)
        if not origen_str or not destino_str:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Origen no existe: {origen_str}")
                return False
            if not origen.is_file():
                if confirmar:
                    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Origen no es un archivo: {origen_str}")
                return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(origen), str(destino))
            escribir_log(f"Copiado: {origen.name} -> {destino.name}")
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", f"Copiado: {origen.name} -> {destino.name}")
            return True
        except Exception as e:
            if confirmar:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    # ========== LECTURA ==========

    elif comando == "listar_directorio":
        ruta_str = accion.get("ruta", ".")
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"Directorio no existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            items = [item.name for item in ruta.iterdir()]
            lista = ", ".join(items) if items else "vacio"
            escribir_log(f"Listado {ruta_str}: {lista}")
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", lista)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "leer_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta' en leer_archivo"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"Archivo no existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()
            
            limite_solicitado = accion.get("limite", MAX_READ_DEFAULT)
            if limite_solicitado == 0:
                limite_a_usar = ABSOLUTE_MAX_READ
            else:
                limite_a_usar = min(limite_solicitado, ABSOLUTE_MAX_READ)
            
            if len(contenido) > limite_a_usar:
                contenido = contenido[:limite_a_usar]
                contenido += f"\n... (truncado a {limite_a_usar} caracteres. El archivo original tiene {len(contenido)} caracteres)"
            
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", contenido)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "existe_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta' en existe_archivo"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", "False (ruta invalida)")
            return False
        existe = ruta.exists()
        guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", str(existe))
        return existe

    elif comando == "obtener_tamano":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta' en obtener_tamano"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"No existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            if ruta.is_file():
                tamano = ruta.stat().st_size
                msg = f"{tamano} bytes"
            else:
                tamano = sum(f.stat().st_size for f in ruta.rglob('*') if f.is_file())
                msg = f"{tamano} bytes (carpeta)"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "fecha_modificacion":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta' en fecha_modificacion"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"No existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            timestamp = ruta.stat().st_mtime
            fecha = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", fecha)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    return False

# ================= PROCESAMIENTO =================

def procesar_json(archivo_json):
    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as e:
        escribir_log(f"Error leyendo JSON {archivo_json.name}: {e}")
        mover_a_jsonout(archivo_json)
        return

    if not isinstance(datos, dict) or "acciones" not in datos:
        escribir_log(f"JSON invalido - falta 'acciones': {archivo_json.name}")
        mover_a_jsonout(archivo_json)
        return

    transaccion_id = datos.get("transaccion_id", "sin_id")
    acciones = datos.get("acciones", [])
    
    if not isinstance(acciones, list):
        escribir_log(f"'acciones' no es lista en {archivo_json.name}")
        mover_a_jsonout(archivo_json)
        return

    escribir_log(f"=== INICIO TX: {transaccion_id} ===")
    escribir_log(f"Directorio de trabajo: {WORK_DIR}")
    
    for i, accion in enumerate(acciones):
        if verificar_stop():
            escribir_log("Proceso detenido por kill switch")
            return
        comando = accion.get("comando", "?")
        escribir_log(f"Accion {i+1}/{len(acciones)}: {comando}")
        try:
            ejecutar_comando(accion, transaccion_id, i+1)
        except Exception as e:
            escribir_log(f"Error en accion {i+1}: {e}")
            guardar_resultado_json(transaccion_id, i+1, comando, "error", str(e))

    escribir_log(f"=== FIN TX: {transaccion_id} ===")
    mover_a_jsonout(archivo_json)

def mover_a_jsonout(archivo):
    jsonout_dir = Path(JSONOUT_DIR)
    jsonout_dir.mkdir(parents=True, exist_ok=True)
    destino = jsonout_dir / archivo.name
    try:
        if destino.exists():
            destino.unlink()
        archivo.rename(destino)
        escribir_log(f"Archivo movido a jsonout: {destino.name}")
    except Exception as e:
        try:
            shutil.copy2(archivo, destino)
            archivo.unlink()
        except:
            pass

def obtener_json_mas_nuevo(directorio):
    patron = str(directorio / EXTENSION)
    archivos = glob.glob(patron)
    if not archivos:
        return None
    mas_nuevo = max(archivos, key=os.path.getmtime)
    return Path(mas_nuevo)

def limpiar_stop_signal():
    stop_path = Path(STOP_FILE)
    if stop_path.exists():
        stop_path.unlink()
        escribir_log("STOP.trigger eliminado")

# ================= LANZAR VISOR =================

def lanzar_visor():
    """Lanza el visor si no está corriendo"""
    try:
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq pythonw.exe'], 
                               capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if 'pythonw.exe' not in result.stdout:
            visor_path = SCRIPT_DIR / 'waio_visor.py'
            if visor_path.exists():
                subprocess.Popen(['pythonw', str(visor_path)], 
                               creationflags=subprocess.CREATE_NO_WINDOW)
                escribir_log("Visor iniciado automaticamente")
            else:
                escribir_log(f"Visor no encontrado en: {visor_path}")
        else:
            escribir_log("Visor ya estaba corriendo, reutilizando")
    except Exception as e:
        escribir_log(f"Error al lanzar visor: {e}")

# ================= MAIN =================

def main():
    # 1. Matar motor anterior (si existe)
    stop_path = Path(STOP_FILE)
    if stop_path.exists():
        # Ya hay un STOP.trigger? Lo dejamos, el motor anterior se matará solo
        escribir_log("STOP.trigger existente, motor anterior se apagara")
    else:
        # Crear STOP.trigger para matar motor anterior
        stop_path.touch()
        escribir_log("STOP.trigger creado para matar motor anterior")
        time.sleep(1)  # Esperar que el anterior se entere y muera
        # Limpiar el stop que acabamos de crear
        if stop_path.exists():
            stop_path.unlink()
            escribir_log("STOP.trigger eliminado (propio)")
    
    # 2. Limpiar cualquier stop residual
    limpiar_stop_signal()
    
    # 3. Lanzar visor (si no existe)
    lanzar_visor()
    
    # 4. Resto del código normal
    directorio_escucha = obtener_directorio_descargas()
    
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    jsonout_path = Path(JSONOUT_DIR)
    jsonout_path.mkdir(parents=True, exist_ok=True)
    
    escribir_log("=" * 50)
    escribir_log("WAIO_ESCUCHA_V2_INICIADO")
    escribir_log(f"Log: {LOG_FILE}")
    escribir_log(f"Script en: {SCRIPT_DIR}")
    escribir_log(f"Directorio de trabajo: {WORK_DIR}")
    escribir_log(f"Escuchando en: {directorio_escucha}")
    escribir_log(f"Output en: {output_path.resolve()}")
    escribir_log(f"JsonOut en: {jsonout_path.resolve()}")
    escribir_log(f"Comandos disponibles: {len(COMANDOS_PERMITIDOS)}")
    escribir_log(f"Limite lectura por defecto: {MAX_READ_DEFAULT} caracteres")
    escribir_log(f"Limite absoluto: {ABSOLUTE_MAX_READ} caracteres")
    escribir_log("=" * 50)
    
    generar_prompt_maestro()
    
    ultimo_procesado = None
    errores_consecutivos = 0
    
    while True:
        try:
            if verificar_stop():
                escribir_log("Apagando por kill switch")
                break
            
            json_nuevo = obtener_json_mas_nuevo(directorio_escucha)
            
            if json_nuevo and json_nuevo != ultimo_procesado:
                time.sleep(0.3)
                procesar_json(json_nuevo)
                ultimo_procesado = json_nuevo
                errores_consecutivos = 0
            
            time.sleep(TIEMPO_ESPERA_SEG)
            
        except KeyboardInterrupt:
            escribir_log("Detenido por usuario")
            break
        except Exception as e:
            errores_consecutivos += 1
            escribir_log(f"ERROR CRITICO ({errores_consecutivos}): {e}")
            if errores_consecutivos > 5:
                escribir_log("Demasiados errores - pausa larga")
                time.sleep(10)
            else:
                time.sleep(2)
    
    limpiar_stop_signal()
    escribir_log("WAIO_ESCUCHA_V2_FINALIZADO")

# ================= GENERACION DE PROMPT =================

def generar_prompt_maestro():
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    prompt_texto = """PROMPT MAESTRO: WAIO V2

Actua como agente de sistema para mi motor local WAIO (Web AI Orchestrator). Tu tarea es generar acciones en formato JSON para manipular archivos, carpetas y obtener informacion del sistema de forma segura.

COMO FUNCIONA:
1. Tu generas un archivo JSON en mi carpeta Downloads
2. WAIO lo detecta y ejecuta las acciones
3. Los resultados de comandos de LECTURA se guardan en la carpeta output/
4. Los comandos de ESCRITURA por defecto NO generan resultados, pero pueden hacerlo si lo pides
5. Yo te copio los resultados y tu decides el siguiente paso

FORMATO DEL PAYLOAD (OBLIGATORIO):
{
  "transaccion_id": "tx_unico_generado",
  "acciones": [
    { "comando": "nombre_comando", "ruta": "ruta_relativa", "contenido": "si_aplica" }
  ]
}

REGLAS DEL FORMATO:
- transaccion_id: Identificador unico (ej: tx_001)
- acciones: Lista de comandos en orden secuencial
- ruta: Siempre rutas relativas (ej: "docs/nota.txt")
- contenido: Solo para comandos que escriben archivos
- origen/destino: Para mover o copiar
- confirmar: (opcional) true/false - Solo para comandos de escritura. Genera JSON con resultado.
- limite: (opcional) Numero de caracteres para leer_archivo. 0 = archivo completo (max 10MB)

COMANDOS DISPONIBLES (11):

ESCRITURA:
- crear_archivo (alias: create_file, write, write_file) - parametros: ruta, contenido, confirmar?(opcional)
- crear_carpeta (alias: create_folder, mkdir) - parametros: ruta, confirmar?(opcional)
- eliminar_archivo (alias: delete_file, rm, del) - parametros: ruta, confirmar?(opcional)
- eliminar_carpeta (alias: delete_folder, rmdir, rd) - parametros: ruta, confirmar?(opcional)
- mover_archivo (alias: move, mv, rename) - parametros: origen, destino, confirmar?(opcional)
- copiar_archivo (alias: copy, cp) - parametros: origen, destino, confirmar?(opcional)

LECTURA (estos SIEMPRE generan JSON con el resultado):
- listar_directorio (alias: list_dir, ls) - parametros: ruta
- leer_archivo (alias: read_file, read) - parametros: ruta, limite?(opcional)
- existe_archivo (alias: exists, check) - parametros: ruta
- obtener_tamano (alias: size, get_size, obtener_tamaño) - parametros: ruta
- fecha_modificacion (alias: modified, mtime, fecha_modificación) - parametros: ruta

LIMITE DE LECTURA:

Por defecto, leer_archivo devuelve hasta 100,000 caracteres (suficiente para la mayoria de archivos).

Si necesitas el archivo completo (hasta 10MB), usa "limite": 0:
{
  "comando": "leer_archivo",
  "ruta": "repomix.xml",
  "limite": 0
}

Si quieres un limite personalizado (ej: 50,000 caracteres), usa "limite": 50000.

Si el archivo supera los 10MB, se truncara a 10MB por seguridad del portapapeles.

CONFIRMACION OPCIONAL EN ESCRITURAS:

Por defecto, los comandos de escritura NO generan JSON de salida para mantener el sistema eficiente.
Si necesitas confirmacion, anade "confirmar": true al comando.

EJEMPLOS:

Ejemplo 1: Crear proyecto con confirmacion
{
  "transaccion_id": "tx_proyecto_001",
  "acciones": [
    { "comando": "crear_carpeta", "ruta": "mi_proyecto", "confirmar": true },
    { "comando": "crear_archivo", "ruta": "mi_proyecto/README.md", "contenido": "# Mi Proyecto", "confirmar": true },
    { "comando": "listar_directorio", "ruta": "mi_proyecto" }
  ]
}

Ejemplo 2: Explorar (sin confirmacion, eficiente)
{
  "transaccion_id": "tx_explorar",
  "acciones": [
    { "comando": "listar_directorio", "ruta": "." },
    { "comando": "existe_archivo", "ruta": "config.json" },
    { "comando": "leer_archivo", "ruta": "config.json" }
  ]
}

Ejemplo 3: Limpiar con confirmacion solo en operacion critica
{
  "transaccion_id": "tx_limpieza",
  "acciones": [
    { "comando": "crear_carpeta", "ruta": "backup" },
    { "comando": "copiar_archivo", "origen": "datos.csv", "destino": "backup/datos.csv" },
    { "comando": "eliminar_archivo", "ruta": "temp/viejo.log", "confirmar": true },
    { "comando": "mover_archivo", "origen": "descarga.zip", "destino": "backup/archivo.zip" }
  ]
}

Ejemplo 4: Obtener informacion de archivos
{
  "transaccion_id": "tx_info",
  "acciones": [
    { "comando": "obtener_tamano", "ruta": "video.mp4" },
    { "comando": "fecha_modificacion", "ruta": "documento.txt" },
    { "comando": "existe_archivo", "ruta": "faltante.dat" }
  ]
}

Ejemplo 5: Leer archivo grande (limite por defecto 100k)
{
  "transaccion_id": "tx_leer_codigo",
  "acciones": [
    { "comando": "leer_archivo", "ruta": "waio_escucha_v2.py" }
  ]
}

Ejemplo 6: Leer archivo completo (sin limite)
{
  "transaccion_id": "tx_leer_gigante",
  "acciones": [
    { "comando": "leer_archivo", "ruta": "repomix-full.xml", "limite": 0 }
  ]
}

REGLAS DE SEGURIDAD (MUY IMPORTANTE):
1. SOLO RUTAS RELATIVAS - No uses C:\\windows ni rutas absolutas
2. NO USES ".." - Esta prohibido salir del directorio base
3. TODO se ejecuta dentro del directorio donde esta el script

RUTAS PROHIBIDAS: C:/windows/..., ../../etc/passwd, D:/archivos/...
RUTAS PERMITIDAS: mi_carpeta/, docs/nota.txt, ./

TECNICAS RECOMENDADAS:

1. Confirmacion selectiva: Usa "confirmar": true solo en operaciones criticas o cuando necesites depurar.

2. Lectura de archivos grandes: Con el limite de 100,000 caracteres, la mayoria de archivos se leen completos. Si necesitas archivos mas grandes (hasta 10MB), usa "limite": 0.

3. Verificacion de escrituras: Si no usas "confirmar", puedes verificar con una lectura posterior.

INSTRUCCION FINAL:
Genera el JSON en un bloque de codigo limpio. No anadas explicaciones largas fuera del JSON. Comienza con listar_directorio para conocer el entorno.
"""
    
    prompt_file = output_path / "PROMPT_WAIO.txt"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_texto)
    
    escribir_log(f"Prompt guardado en: {prompt_file}")
    
    try:
        subprocess.run(['clip'], input=prompt_texto, text=True,
                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        escribir_log("Prompt copiado al portapapeles")
    except Exception as e:
        escribir_log(f"Error al copiar prompt al portapapeles: {e}")
    
    return prompt_file

if __name__ == "__main__":
    main()