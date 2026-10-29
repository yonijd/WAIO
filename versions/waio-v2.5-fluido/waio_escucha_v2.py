# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import winreg
import subprocess
import ctypes
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

# Configurar rutas
JSONOUT_DIR = SCRIPT_DIR / "jsonout"
OUTPUT_DIR = SCRIPT_DIR / "output"
LOG_DIR = SCRIPT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

MAX_READ_DEFAULT = 500000   # 500KB - suficiente para la mayoria
ABSOLUTE_MAX_READ = 10000000  # 10MB maximo absoluto
TIMESTAMP_LOG = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"waio_escucha_{TIMESTAMP_LOG}.log"
STOP_FILE = SCRIPT_DIR / "STOP.trigger"

# Mapeo de comandos
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

# ================= FUNCIONES =================

def obtener_directorio_descargas():
    ruta_std = Path.home() / "Downloads"
    if ruta_std.exists() and ruta_std.is_dir():
        escribir_log(f"Downloads detectado: {ruta_std}")
        return ruta_std
    ruta_esp = Path.home() / "Descargas"
    if ruta_esp.exists() and ruta_esp.is_dir():
        escribir_log(f"Descargas detectado: {ruta_esp}")
        return ruta_esp
    try:
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        try:
            valor = winreg.QueryValueEx(clave, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            ruta_reg = Path(valor)
            if ruta_reg.exists() and ruta_reg.is_dir():
                escribir_log(f"Downloads via registro: {ruta_reg}")
                return ruta_reg
        except Exception as e:
            escribir_log(f"Error registro: {e}")
        finally:
            winreg.CloseKey(clave)
    except Exception as e:
        escribir_log(f"Error abriendo registro: {e}")
    escribir_log("WARNING: Usando directorio actual")
    return Path.cwd()

def ruta_segura(ruta_str):
    try:
        ruta = Path(ruta_str)
        if ruta.is_absolute():
            escribir_log(f"SEGURIDAD: Ruta absoluta rechazada: {ruta_str}")
            return None
        ruta = (WORK_DIR / ruta).resolve()
        ruta.relative_to(WORK_DIR)
        return ruta
    except (ValueError, OSError):
        escribir_log(f"SEGURIDAD: Ruta bloqueada: {ruta_str}")
        return None

def escribir_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] {mensaje}\n")
    except:
        try:
            with open(LOG_FILE, "a", encoding="ascii", errors="replace") as log:
                log.write(f"[{timestamp}] {mensaje}\n")
        except:
            pass

def normalizar_comando(comando):
    return MAPEO_COMANDOS.get(comando.lower().strip(), comando.lower().strip())

def verificar_stop():
    if STOP_FILE.exists():
        escribir_log("KILL_SWITCH detectado")
        return True
    return False

def copiar_portapapeles_unicode(texto):
    """Copia usando ctypes UTF-16. Si falla, fallback a clip."""
    # Intento 1: ctypes (soporta Unicode)
    try:
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        
        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        
        data = (texto + '\x00').encode('utf-16-le')
        hmem = kernel32.GlobalAlloc(0x2002, len(data))  # GMEM_MOVEABLE | GMEM_ZEROINIT
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
        escribir_log("Portapapeles: ctypes UTF-16 exitoso")
        return True
    except Exception as e:
        escribir_log(f"Portapapeles ctypes fallo: {e}")
        
        # Intento 2: clip (fallback, no Unicode pero no crashea)
        try:
            subprocess.run(['clip'], input=texto, text=True,
                          encoding='utf-8', errors='replace',
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            escribir_log("Portapapeles: clip fallback exitoso (con reemplazo de caracteres)")
            return True
        except Exception as e2:
            escribir_log(f"Portapapeles clip fallback tambien fallo: {e2}")
            return False

def guardar_resultado_json(transaccion_id, accion_idx, comando, status, output):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        nombre_archivo = f"{transaccion_id}_{accion_idx}_{timestamp}.json"
        archivo_json = OUTPUT_DIR / nombre_archivo
        
        datos = {
            "transaccion_id": transaccion_id,
            "accion_idx": accion_idx,
            "comando": comando,
            "status": status,
            "output": output,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        temp_file = OUTPUT_DIR / f"{nombre_archivo}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        temp_file.rename(archivo_json)
        
        escribir_log(f"JSON creado: {nombre_archivo} (status: {status})")
        
        texto_copia = f"Comando: {comando}\nStatus: {status}\nResultado: {output}"
        copiar_portapapeles_unicode(texto_copia)
    except Exception as e:
        escribir_log(f"Error guardando JSON: {e}")

def eliminar_seguro(ruta):
    """Elimina a papelera con send2trash, fallback a trash manual"""
    try:
        from send2trash import send2trash
        send2trash(str(ruta))
        escribir_log(f"Enviado a papelera: {ruta}")
        return True, f"Enviado a papelera: {ruta.name}"
    except ImportError:
        escribir_log("send2trash no instalado, usando trash manual")
        trash_dir = SCRIPT_DIR / "trash"
        trash_dir.mkdir(exist_ok=True)
        destino = trash_dir / f"{ruta.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.move(str(ruta), str(destino))
            escribir_log(f"Movido a trash manual: {destino}")
            return True, f"Movido a trash: {destino.name}"
        except Exception as e:
            return False, str(e)
    except Exception as e:
        return False, str(e)

# ================= EJECUTOR =================

def ejecutar_comando(accion, transaccion_id, accion_idx):
    comando_raw = accion.get("comando", "")
    comando = normalizar_comando(comando_raw)
    
    if comando not in COMANDOS_PERMITIDOS:
        msg = f"Comando no soportado: {comando_raw}"
        escribir_log(msg)
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False

    # ========== ESCRITURA ==========
    
    if comando == "crear_archivo":
        ruta_str = accion.get("ruta")
        contenido = accion.get("contenido", "")
        if not ruta_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            msg = f"Archivo creado: {ruta.name}"
            escribir_log(msg)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "crear_carpeta":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            ruta.mkdir(parents=True, exist_ok=True)
            msg = f"Carpeta creada: {ruta.name}"
            escribir_log(msg)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "eliminar_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
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
            if not ruta.is_file():
                msg = f"No es un archivo: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            ok, msg = eliminar_seguro(ruta)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok" if ok else "error", msg)
            return ok
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "eliminar_carpeta":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"Carpeta no existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            if not ruta.is_dir():
                msg = f"No es una carpeta: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            ok, msg = eliminar_seguro(ruta)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok" if ok else "error", msg)
            return ok
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "mover_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        if not origen_str or not destino_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                msg = f"Origen no existe: {origen_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origen), str(destino))
            msg = f"Movido: {origen.name} -> {destino.name}"
            escribir_log(msg)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "copiar_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        if not origen_str or not destino_str:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                msg = f"Origen no existe: {origen_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            if not origen.is_file():
                msg = f"Origen no es archivo: {origen_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(origen), str(destino))
            msg = f"Copiado: {origen.name} -> {destino.name}"
            escribir_log(msg)
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
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
            
            original_len = len(contenido)
            if original_len > limite_a_usar:
                contenido = contenido[:limite_a_usar]
                contenido += f"\n... (truncado a {limite_a_usar} caracteres. Original: {original_len})"
            
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", contenido)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "existe_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta'"
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
            msg = "Falta 'ruta'"
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
            msg = "Falta 'ruta'"
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
        guardar_resultado_json("error_lectura", 1, "desconocido", "error", f"No se pudo leer: {e}")
        mover_a_jsonout(archivo_json)
        return

    if not isinstance(datos, dict) or "acciones" not in datos:
        escribir_log(f"JSON invalido - falta 'acciones': {archivo_json.name}")
        guardar_resultado_json("error_formato", 1, "desconocido", "error", "JSON invalido: falta 'acciones'")
        mover_a_jsonout(archivo_json)
        return

    transaccion_id = datos.get("transaccion_id", "sin_id")
    acciones = datos.get("acciones", [])
    
    if not isinstance(acciones, list):
        escribir_log(f"'acciones' no es lista en {archivo_json.name}")
        mover_a_jsonout(archivo_json)
        return

    escribir_log(f"=== INICIO TX: {transaccion_id} ===")
    escribir_log(f"Directorio: {WORK_DIR}")
    
    for i, accion in enumerate(acciones):
        if verificar_stop():
            escribir_log("Detenido por kill switch")
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
    JSONOUT_DIR.mkdir(parents=True, exist_ok=True)
    destino = JSONOUT_DIR / archivo.name
    try:
        if destino.exists():
            destino.unlink()
        archivo.rename(destino)
        escribir_log(f"Movido a jsonout: {destino.name}")
    except Exception as e:
        escribir_log(f"Error moviendo: {e}")
        try:
            shutil.copy2(archivo, destino)
            archivo.unlink()
            escribir_log(f"Copiado (fallback) a jsonout: {destino.name}")
        except Exception as e2:
            escribir_log(f"Error en fallback: {e2}")

def obtener_json_mas_nuevo(directorio):
    try:
        archivos = []
        with os.scandir(directorio) as it:
            for entry in it:
                if entry.name.endswith('.json') and entry.is_file():
                    archivos.append((entry.path, entry.stat().st_mtime))
        if not archivos:
            return None
        mas_nuevo = max(archivos, key=lambda x: x[1])
        return Path(mas_nuevo[0])
    except Exception as e:
        escribir_log(f"Error escaneando: {e}")
        return None

def limpiar_stop_signal():
    if STOP_FILE.exists():
        STOP_FILE.unlink()
        escribir_log("STOP.trigger eliminado")

def lanzar_visor():
    try:
        visor_path = SCRIPT_DIR / 'waio_visor.py'
        if not visor_path.exists():
            escribir_log(f"Visor no encontrado: {visor_path}")
            return
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq pythonw.exe'], 
                               capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if 'pythonw.exe' not in result.stdout:
            subprocess.Popen(['pythonw', str(visor_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            escribir_log("Visor iniciado")
        else:
            escribir_log("Visor ya corriendo")
    except Exception as e:
        escribir_log(f"Error lanzando visor: {e}")

# ================= MAIN =================

def main():
    if STOP_FILE.exists():
        escribir_log("STOP.trigger existente")
    else:
        STOP_FILE.touch()
        escribir_log("STOP.trigger creado")
        time.sleep(1)
        if STOP_FILE.exists():
            STOP_FILE.unlink()
            escribir_log("STOP.trigger eliminado")
    
    limpiar_stop_signal()
    lanzar_visor()
    
    directorio_escucha = obtener_directorio_descargas()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    JSONOUT_DIR.mkdir(parents=True, exist_ok=True)
    
    escribir_log("=" * 50)
    escribir_log("WAIO_ESCUCHA_V2_INICIADO")
    escribir_log(f"Log: {LOG_FILE}")
    escribir_log(f"Script: {SCRIPT_DIR}")
    escribir_log(f"Work dir: {WORK_DIR}")
    escribir_log(f"Escuchando: {directorio_escucha}")
    escribir_log(f"Limite lectura: {MAX_READ_DEFAULT} (default) / {ABSOLUTE_MAX_READ} (max)")
    escribir_log("=" * 50)
    
    generar_prompt_maestro()
    
    ultimo_procesado = None
    errores_consecutivos = 0
    
    while True:
        try:
            if verificar_stop():
                break
            
            json_nuevo = obtener_json_mas_nuevo(directorio_escucha)
            if json_nuevo and (ultimo_procesado is None or str(json_nuevo) != str(ultimo_procesado)):
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
            escribir_log(f"ERROR ({errores_consecutivos}): {e}")
            time.sleep(5 if errores_consecutivos > 5 else 2)
    
    limpiar_stop_signal()
    escribir_log("WAIO_ESCUCHA_V2_FINALIZADO")

def generar_prompt_maestro():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    prompt_texto = """PROMPT MAESTRO: WAIO V2.5

Actua como agente de sistema para mi motor local WAIO.

COMO FUNCIONA:
1. Tu generas un archivo JSON en mi carpeta Downloads
2. WAIO lo detecta y ejecuta las acciones
3. TODOS los comandos generan JSON de resultado en output/
4. El visor muestra resultados y copia al portapapeles

FORMATO DEL PAYLOAD (OBLIGATORIO):
{
  "transaccion_id": "tx_unico",
  "acciones": [
    { "comando": "nombre", "parametros": "valor" }
  ]
}

REGLAS ESTRICTAS:
- SIEMPRE usa transaccion_id + acciones
- NUNCA uses {"comando": "..."} solo (eso solo para TRANSCLIP)
- NUNCA uses caracteres de control como \\x00, \\x01 en strings
- Si necesitas datos binarios, conviertelos a Base64

COMANDOS DISPONIBLES (11):

ESCRITURA:
- crear_archivo (ruta, contenido)
- crear_carpeta (ruta)
- eliminar_archivo (ruta) - va a Papelera
- eliminar_carpeta (ruta) - va a Papelera
- mover_archivo (origen, destino)
- copiar_archivo (origen, destino)

LECTURA:
- listar_directorio (ruta)
- leer_archivo (ruta, limite?=100000, 0=completo)
- existe_archivo (ruta)
- obtener_tamano (ruta)
- fecha_modificacion (ruta)

LIMITE DE LECTURA:
- Default: 500,000 caracteres
- Para archivos grandes: {"limite": 0} (max 10MB)

SEGURIDAD:
- Solo rutas relativas (no C:\\, no ..)
- Todo dentro del directorio donde se inicio WAIO

EJEMPLO:
{
  "transaccion_id": "tx_001",
  "acciones": [
    { "comando": "listar_directorio", "ruta": "." },
    { "comando": "leer_archivo", "ruta": "config.json", "limite": 0 }
  ]
}

INSTRUCCION FINAL: Genera JSON valido. Comienza con listar_directorio.
"""
    
    prompt_file = OUTPUT_DIR / "PROMPT_WAIO.txt"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_texto)
    escribir_log(f"Prompt guardado: {prompt_file}")
    copiar_portapapeles_unicode(prompt_texto)

if __name__ == "__main__":
    main()