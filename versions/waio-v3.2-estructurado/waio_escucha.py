# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import winreg
import subprocess
from pathlib import Path
from datetime import datetime

VERSION = "3.2"
TIEMPO_ESPERA_SEG = 2
EXTENSION = "*.json"

SCRIPT_DIR = Path(sys.argv[0]).parent.resolve()

WORK_DIR = SCRIPT_DIR
if len(sys.argv) > 2 and sys.argv[1] == "--cwd":
    try:
        WORK_DIR = Path(sys.argv[2]).resolve()
    except Exception as e:
        print(f"Error cambiando directorio: {e}")

os.chdir(WORK_DIR)

JSONOUT_DIR = SCRIPT_DIR / "temp" / "jsonout"
OUTPUT_DIR = SCRIPT_DIR / "temp" / "output"
LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

MAX_READ_DEFAULT = 500000
ABSOLUTE_MAX_READ = 10000000
TIMESTAMP_LOG = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"waio_escucha_{TIMESTAMP_LOG}.log"
STOP_FILE = SCRIPT_DIR / "STOP.trigger"
PROMPT_FILE = SCRIPT_DIR / "config" / "prompt.txt"

CONFIG_FILE = SCRIPT_DIR / "config" / "waio_config.json"
SKILLS_FILE = SCRIPT_DIR / "data" / "skills.json"
WISPOUT_FILE = SCRIPT_DIR / "config" / "wispout.json"

SKILLS_DIR = SCRIPT_DIR / "skills"
CORE_DIR = SCRIPT_DIR / "core"
WORKDIR_FILE = SCRIPT_DIR / "temp" / "workdir.txt"
LOCK_FILE = SCRIPT_DIR / "temp" / "waio.lock"

perfil_activo = "estandar"
config_cache = None
habilidades_cache = None
wispout_cache = None
contador_acciones = 0

COMANDOS_INTERNOS = [
    "skills",
    "listar_skills",
    "list_skills",
    "info",
    "ayuda",
    "help",
    "?",
    "indexar",
    "index",
    "ejecutar",
    "run",
    "mensaje"
]

COMANDOS_BASE = [
    "listar_directorio",
    "leer_archivo",
    "existe_archivo",
    "obtener_tamano",
    "fecha_modificacion",
    "contar_lineas",
    "buscar_archivos",
    "leer_lineas",
    "crear_archivo",
    "crear_carpeta",
    "mover_archivo",
    "renombrar_archivo",
    "copiar_archivo",
    "append_archivo",
    "eliminar_archivo",
    "eliminar_carpeta"
]

MAPEO_COMANDOS = {
    "listar_directorio": "listar_directorio",
    "leer_archivo": "leer_archivo",
    "crear_archivo": "crear_archivo",
    "crear_carpeta": "crear_carpeta",
    "eliminar_archivo": "eliminar_archivo",
    "eliminar_carpeta": "eliminar_carpeta",
    "mover_archivo": "mover_archivo",
    "copiar_archivo": "copiar_archivo",
    "renombrar_archivo": "renombrar_archivo",
    "existe_archivo": "existe_archivo",
    "buscar_archivos": "buscar_archivos",
    "mensaje": "mensaje",
    "contar_lineas": "contar_lineas",
    "leer_lineas": "leer_lineas",
    "obtener_tamano": "obtener_tamano",
    "fecha_modificacion": "fecha_modificacion",
    "append_archivo": "append_archivo",
    "skills": "skills",
    "listar_skills": "skills",
    "list_skills": "skills",
    "info": "skills",
    "ayuda": "ayuda",
    "help": "ayuda",
    "?": "ayuda",
    "indexar": "indexar",
    "index": "indexar",
    "ejecutar": "ejecutar",
    "run": "ejecutar",
    "listar": "listar_directorio",
    "ls": "listar_directorio",
    "dir": "listar_directorio",
    "leer": "leer_archivo",
    "cat": "leer_archivo",
    "read": "leer_archivo",
    "crear": "crear_archivo",
    "touch": "crear_archivo",
    "create": "crear_archivo",
    "mkdir": "crear_carpeta",
    "make_dir": "crear_carpeta",
    "eliminar": "eliminar_archivo",
    "rm": "eliminar_archivo",
    "del": "eliminar_archivo",
    "delete": "eliminar_archivo",
    "rmdir": "eliminar_carpeta",
    "delete_dir": "eliminar_carpeta",
    "mover": "mover_archivo",
    "mv": "mover_archivo",
    "move": "mover_archivo",
    "copiar": "copiar_archivo",
    "cp": "copiar_archivo",
    "copy": "copiar_archivo",
    "renombrar": "renombrar_archivo",
    "rename": "renombrar_archivo",
    "ren": "renombrar_archivo",
    "existe": "existe_archivo",
    "test": "existe_archivo",
    "exists": "existe_archivo",
    "buscar": "buscar_archivos",
    "find": "buscar_archivos",
    "search": "buscar_archivos",
    "echo": "mensaje",
    "say": "mensaje",
    "count": "contar_lineas",
    "wc": "contar_lineas",
    "head": "leer_lineas",
    "read_lines": "leer_lineas",
    "tamano": "obtener_tamano",
    "size": "obtener_tamano",
    "modificado": "fecha_modificacion",
    "modified": "fecha_modificacion",
    "agregar": "append_archivo",
    "append": "append_archivo",
    "listar_habilidades": "skills",
    "indexar_habilidades": "indexar",
    "leer_skill": "skills",
    "read_skill": "skills"
}

PROMPT_DEFAULT = """PROMPT MAESTRO: WAIO 3.2

Eres un agente de sistema para WAIO (Web AI Orchestrator). Tu tarea es generar JSON para ejecutar acciones en el sistema local.

COMO FUNCIONA:
1. Generas un archivo JSON con una transaccion_id y una lista de acciones.
2. WAIO detecta el JSON en la carpeta Downloads (o la configurada) y ejecuta las acciones.
3. WAIO devuelve un JSON con los resultados en temp/output/.
4. Cada accion es un objeto con "comando" y los parametros que requiere.

ESTRUCTURA DE CARPETAS:
- core/       -> Comandos base del sistema (indexar)
- skills/     -> Skills del usuario (cada una en su carpeta con JSON + .py)
- data/       -> skills.json (catalogo unificado generado por indexar)
- config/     -> Configuracion (waio_config.json, wispout.json, prompt.txt)
- temp/       -> Archivos temporales (jsonout/, output/, logs/)
- trash/      -> Papelera manual

PERFILES DE SEGURIDAD:
WAIO tiene 4 perfiles que determinan que comandos puedes usar.

- solo_lectura: Solo lectura y listado. No puedes modificar ni borrar.
- estandar: Lectura, escritura, creacion, copia, movimiento. Todo va a Papelera. NO puedes ejecutar scripts.
- avanzado: Todo lo anterior + eliminacion directa, ejecucion de scripts y rutas absolutas.
- sin_restricciones: Acceso total. Borrado permanente. Solo para pruebas avanzadas.

COMANDOS DISPONIBLES (con alias):

COMANDOS BASE (OPERACIONES DE SISTEMA):

listar_directorio (listar, ls, dir)
  - Lista archivos y carpetas en una ruta.
  - Parametros: {"ruta": "carpeta"} (opcional, default: ".")

leer_archivo (leer, cat, read)
  - Lee el contenido de un archivo de texto.
  - Parametros: {"ruta": "archivo", "limite": 500000} (limite opcional, 0=completo)

crear_archivo (crear, touch, create)
  - Crea un archivo con el contenido especificado.
  - Parametros: {"ruta": "archivo", "contenido": "texto"}

crear_carpeta (mkdir, make_dir)
  - Crea una nueva carpeta.
  - Parametros: {"ruta": "carpeta"}

mover_archivo (mover, mv, move)
  - Mueve o renombra un archivo o carpeta.
  - Parametros: {"origen": "ruta", "destino": "ruta"}

copiar_archivo (copiar, cp, copy)
  - Copia un archivo.
  - Parametros: {"origen": "ruta", "destino": "ruta"}

renombrar_archivo (renombrar, rename, ren)
  - Renombra un archivo.
  - Parametros: {"ruta": "archivo", "nombre_nuevo": "nuevo_nombre"}

eliminar_archivo (eliminar, rm, del, delete)
  - Elimina un archivo (a Papelera).
  - Parametros: {"ruta": "archivo"}

eliminar_carpeta (rmdir, delete_dir)
  - Elimina una carpeta (a Papelera).
  - Parametros: {"ruta": "carpeta"}

existe_archivo (existe, test, exists)
  - Verifica si un archivo o carpeta existe.
  - Parametros: {"ruta": "archivo"}

obtener_tamano (tamano, size)
  - Devuelve el tamaño de un archivo en bytes.
  - Parametros: {"ruta": "archivo"}

fecha_modificacion (modificado, modified)
  - Devuelve la fecha de ultima modificacion.
  - Parametros: {"ruta": "archivo"}

contar_lineas (contar, wc, count)
  - Cuenta las lineas de un archivo de texto.
  - Parametros: {"ruta": "archivo"}

buscar_archivos (buscar, find, search)
  - Busca archivos por nombre o patron.
  - Parametros: {"ruta": "carpeta", "patron": "*.txt"}

leer_lineas (head, read_lines)
  - Lee un rango especifico de lineas.
  - Parametros: {"ruta": "archivo", "inicio": 1, "fin": 10}

append_archivo (agregar, append)
  - Agrega contenido al final de un archivo.
  - Parametros: {"ruta": "archivo", "contenido": "texto"}

mensaje (echo, say)
  - Envia un mensaje al usuario (respuesta interna).
  - Parametros: {"contenido": "texto"}

COMANDOS ESPECIALES:

skills (listar_skills, list_skills, info)
  - Sin parametros: Muestra lista de skills disponibles.
  - Con parametro 'nombre': Muestra el JSON de esa skill.
  - Ejemplo: {"comando": "skills"}
  - Ejemplo: {"comando": "skills", "nombre": "voz"}

ayuda (help, ?)
  - Muestra esta guia de ayuda.
  - Ejemplo: {"comando": "ayuda"}

indexar (index)
  - Regenera el catalogo de skills escaneando core/ y skills/.
  - Sin parametros.
  - Ejemplo: {"comando": "indexar"}

ejecutar (run)
  - Ejecuta un script. Busca en: skills.json, core/, skills/, workdir.
  - Parametros: {"script": "nombre", "parametros": ["arg1", "arg2"]}
  - Ejemplo: {"comando": "ejecutar", "script": "hola_mundo.py"}

COMANDOS POR PERFIL:

- solo_lectura: skills, ayuda, indexar, listar_directorio, leer_archivo, existe_archivo, obtener_tamano, fecha_modificacion, contar_lineas, buscar_archivos, leer_lineas, mensaje
- estandar: Lo anterior + crear_archivo, crear_carpeta, mover_archivo, copiar_archivo, renombrar_archivo, append_archivo
- avanzado: Todo lo anterior + eliminar_archivo, eliminar_carpeta, ejecutar (todos los scripts)
- sin_restricciones: Todo permitido.

EJEMPLO DE JSON:
{
  "transaccion_id": "tx_ejemplo_001",
  "acciones": [
    {"comando": "skills"},
    {"comando": "crear_carpeta", "ruta": "proyecto"},
    {"comando": "ejecutar", "script": "hola_mundo.py"}
  ]
}

REGLAS ESTRICTAS:
- El JSON debe ser 100% valido.
- No uses funciones, expresiones ni operadores.
- Usa strings literales, no instrucciones de repeticion.
- Usa los nombres de parametros exactos (origen/destino, no ruta_origen).
- Espera la confirmacion de WAIO antes de continuar.

INSTRUCCION FINAL:
1. Primero, ejecuta skills para ver los comandos disponibles segun tu perfil.
2. Si no ves todas las skills, ejecuta indexar para regenerar el catalogo.
3. Genera el JSON en un bloque de codigo limpio.
4. Para archivos grandes, usa "limite": 0 para leer completo (maximo 10MB).
5. Si una accion falla, revisa el error y corrige el JSON antes de reintentar."""

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
    perfil = obtener_perfil()
    sandbox = perfil.get("sandbox", True)
    try:
        ruta = Path(ruta_str)
        if sandbox:
            if ruta.is_absolute():
                escribir_log(f"SEGURIDAD: Ruta absoluta rechazada: {ruta_str}")
                return None
            ruta = (WORK_DIR / ruta).resolve()
            ruta.relative_to(WORK_DIR)
            return ruta
        else:
            if ruta.is_absolute():
                return ruta.resolve()
            return (WORK_DIR / ruta).resolve()
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

def guardar_resultado_json(transaccion_id, accion_idx, comando, status, output):
    try:
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        nombre_archivo = f"{transaccion_id}_{accion_idx}_{timestamp}.json"
        archivo_json = OUTPUT_DIR / nombre_archivo
        respuesta_formateada = formatear_respuesta(comando, status, output)
        datos = {
            "transaccion_id": transaccion_id,
            "accion_idx": accion_idx,
            "comando": comando,
            "status": status,
            "output": respuesta_formateada,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "waio_version": VERSION
        }
        temp_file = OUTPUT_DIR / f"{nombre_archivo}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        temp_file.rename(archivo_json)
        escribir_log(f"JSON creado: {nombre_archivo} (status: {status})")
    except Exception as e:
        escribir_log(f"Error guardando JSON: {e}")

def eliminar_seguro(ruta):
    perfil = obtener_perfil()
    modo = perfil.get("borrado", "papelera")
    if modo == "permanente":
        try:
            if ruta.is_file():
                ruta.unlink()
            else:
                shutil.rmtree(ruta)
            escribir_log(f"Eliminado permanente: {ruta}")
            return True, f"Eliminado permanente: {ruta.name}"
        except Exception as e:
            return False, str(e)
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

def cargar_y_procesar_prompt():
    try:
        if not PROMPT_FILE.exists():
            PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROMPT_FILE, "w", encoding="utf-8") as f:
                f.write(PROMPT_DEFAULT)
            escribir_log("prompt.txt creado por defecto")
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            contenido = f.read()
        perfil = obtener_perfil()
        limite = perfil.get("limite_escritura_bytes", 1048576)
        if limite >= 1048576:
            limite_str = f"{limite // 1048576}MB"
        elif limite >= 1024:
            limite_str = f"{limite // 1024}KB"
        else:
            limite_str = f"{limite}B"
        info_adicional = f"\n\nPERFIL ACTIVO: {perfil_activo}\nLIMITE ESCRITURA: {limite_str}\nBORRADO: {perfil.get('borrado', 'papelera')}"
        contenido += info_adicional
        guardar_resultado_json("system_prompt", 1, "prompt", "ok", contenido)
        escribir_log("Prompt procesado y enviado a output")
    except Exception as e:
        escribir_log(f"Error procesando prompt: {e}")

def cargar_config():
    global perfil_activo, config_cache
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config_cache = json.load(f)
            if config_cache.get("_waio_firma") != "WAIO-V3-CONFIG-2026":
                escribir_log("ADVERTENCIA: waio_config.json sin firma. Usando defaults.")
                return usar_config_default()
            perfil_activo = config_cache.get("perfil_activo", "estandar")
            escribir_log(f"Config cargada. Perfil: {perfil_activo}")
            return config_cache
        else:
            return usar_config_default()
    except Exception as e:
        escribir_log(f"Error cargando config: {e}")
        return usar_config_default()

def usar_config_default():
    global perfil_activo
    perfil_activo = "estandar"
    return {
        "perfil_activo": "estandar",
        "perfiles": {
            "estandar": {
                "sandbox": True,
                "permite_rutas_absolutas": False,
                "permite_navegacion_padre": False,
                "borrado": "papelera",
                "comandos_bloqueados": [],
                "limite_escritura_bytes": 1048576,
                "limite_lectura_bytes": 1048576,
                "carpetas_prohibidas": [],
                "permite_scripts": False,
                "permite_consola": False
            }
        }
    }

def cargar_habilidades():
    global habilidades_cache
    try:
        if SKILLS_FILE.exists():
            with open(SKILLS_FILE, "r", encoding="utf-8") as f:
                habilidades_cache = json.load(f)
            if habilidades_cache.get("_waio_firma") != "WAIO-V5-SKILLS-2026":
                escribir_log("ADVERTENCIA: skills.json sin firma. Usando defaults.")
                return usar_habilidades_default()
            total = habilidades_cache.get("_total_skills", 0)
            escribir_log(f"Skills cargadas: {total}")
            return habilidades_cache
        else:
            return usar_habilidades_default()
    except Exception as e:
        escribir_log(f"Error cargando skills: {e}")
        return usar_habilidades_default()

def usar_habilidades_default():
    return {
        "_waio_firma": "WAIO-V5-SKILLS-2026",
        "_version": "1.0",
        "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "_total_skills": 0,
        "categorias": {},
        "resumen_por_perfil": {},
        "skills": {}
    }

def cargar_wispout():
    global wispout_cache
    try:
        if WISPOUT_FILE.exists():
            with open(WISPOUT_FILE, "r", encoding="utf-8") as f:
                wispout_cache = json.load(f)
            if wispout_cache.get("_waio_firma") != "WAIO-V3-WISPOUT-2026":
                escribir_log("ADVERTENCIA: wispout.json sin firma. Usando defaults.")
                return usar_wispout_default()
            escribir_log("wispout.json cargado")
            return wispout_cache
        else:
            return usar_wispout_default()
    except Exception as e:
        escribir_log(f"Error cargando wispout: {e}")
        return usar_wispout_default()

def usar_wispout_default():
    return {
        "encabezado": {"plantilla": "WAIO {version} | {perfil} | {limite} | {borrado}", "mostrar": True},
        "recordatorio": {"activo": True, "mensaje": "Espera la confirmacion de WAIO antes de continuar."},
        "susurro": {"activo": True, "cada_cuantas_acciones": 3, "mensaje": "INSTRUCCION: Se breve, no alucines."},
        "respuestas_especiales": {
            "perfil_cambiado": "Perfil cambiado a {perfil}",
            "comando_bloqueado": "Comando '{comando}' bloqueado",
            "error": "Error: {error}"
        }
    }

def obtener_perfil():
    try:
        config = cargar_config()
        perfiles = config.get("perfiles", {})
        return perfiles.get(perfil_activo, {})
    except Exception as e:
        escribir_log(f"Error obteniendo perfil: {e}")
        return {"sandbox": True, "borrado": "papelera"}

def validar_accion(comando, ruta=""):
    try:
        perfil = obtener_perfil()
        if comando in perfil.get("comandos_bloqueados", []):
            return False, f"Comando '{comando}' bloqueado en perfil {perfil_activo}"
        if comando in ["ejecutar", "run"]:
            if not perfil.get("permite_scripts", False):
                return False, "Scripts no permitidos en perfil actual"
        if not perfil.get("permite_rutas_absolutas", False):
            if ruta and len(ruta) > 1 and ruta[1] == ":":
                return False, "Rutas absolutas no permitidas en este perfil"
        if not perfil.get("permite_navegacion_padre", False):
            if ruta and ".." in ruta:
                return False, "Navegacion a directorio padre no permitida en este perfil"
        for prohibida in perfil.get("carpetas_prohibidas", []):
            if ruta and ruta.lower().startswith(prohibida.lower()):
                return False, f"Carpeta prohibida: {prohibida}"
        return True, "OK"
    except Exception as e:
        escribir_log(f"Error en validacion: {e}")
        return False, str(e)

def formatear_respuesta(comando, status, output):
    global contador_acciones
    try:
        wispout = cargar_wispout()
        perfil = obtener_perfil()
        limite = perfil.get("limite_escritura_bytes", 1048576)
        if limite >= 1048576:
            limite_str = f"{limite // 1048576}MB"
        elif limite >= 1024:
            limite_str = f"{limite // 1024}KB"
        else:
            limite_str = f"{limite}B"
        borrado = perfil.get("borrado", "papelera")
        encabezado = ""
        if wispout.get("encabezado", {}).get("mostrar", True):
            plantilla = wispout["encabezado"].get("plantilla", "WAIO {version} | {perfil} | {limite} | {borrado}")
            encabezado = plantilla.format(
                version=VERSION,
                perfil=perfil_activo,
                limite=limite_str,
                borrado=borrado
            ) + "\n"
        cuerpo = f"Comando: {comando} | {status}\n{output}"
        recordatorio = ""
        if wispout.get("recordatorio", {}).get("activo", True):
            recordatorio = "\n" + wispout["recordatorio"].get("mensaje", "Espera la confirmacion de WAIO antes de continuar.")
        susurro = ""
        if wispout.get("susurro", {}).get("activo", True):
            cada = wispout["susurro"].get("cada_cuantas_acciones", 3)
            contador_acciones += 1
            if contador_acciones % cada == 0:
                susurro = "\n" + wispout["susurro"].get("mensaje", "INSTRUCCION: Se breve, no alucines.")
        return encabezado + cuerpo + recordatorio + susurro
    except Exception as e:
        escribir_log(f"Error formateando respuesta: {e}")
        return f"Comando: {comando} | {status}\n{output}"

def crear_archivos_si_faltan():
    try:
        if not CONFIG_FILE.exists():
            escribir_log("waio_config.json no existe, creando por defecto")
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            config_default = {
                "_waio_firma": "WAIO-V3-CONFIG-2026",
                "_comentario": "NO EDITAR LA FIRMA. WAIO la usa para validar este archivo.",
                "_version": "1.0",
                "perfil_activo": "estandar",
                "perfiles": {
                    "solo_lectura": {
                        "_descripcion": "SOLO LECTURA. Puede ver y listar, pero no modificar ni borrar.",
                        "sandbox": True,
                        "permite_rutas_absolutas": False,
                        "permite_navegacion_padre": False,
                        "borrado": "papelera",
                        "comandos_bloqueados": ["crear_archivo", "crear_carpeta", "eliminar_archivo", "eliminar_carpeta", "mover_archivo", "copiar_archivo"],
                        "limite_escritura_bytes": 0,
                        "limite_lectura_bytes": 500000,
                        "carpetas_prohibidas": [],
                        "permite_scripts": False,
                        "permite_consola": False
                    },
                    "estandar": {
                        "_descripcion": "SEGURO. Puede leer, escribir y borrar en el proyecto. Todo va a Papelera.",
                        "sandbox": True,
                        "permite_rutas_absolutas": False,
                        "permite_navegacion_padre": False,
                        "borrado": "papelera",
                        "comandos_bloqueados": [],
                        "limite_escritura_bytes": 1048576,
                        "limite_lectura_bytes": 1048576,
                        "carpetas_prohibidas": [],
                        "permite_scripts": False,
                        "permite_consola": False
                    },
                    "avanzado": {
                        "_descripcion": "DESARROLLADOR. Puede leer y escribir en todo el disco (excepto Windows). Ejecuta scripts.",
                        "sandbox": False,
                        "permite_rutas_absolutas": True,
                        "permite_navegacion_padre": True,
                        "borrado": "papelera",
                        "comandos_bloqueados": [],
                        "limite_escritura_bytes": 10485760,
                        "limite_lectura_bytes": 10485760,
                        "carpetas_prohibidas": ["C:\\Windows", "C:\\Windows\\System32", "C:\\Windows\\System", "C:\\Program Files", "C:\\Program Files (x86)", "C:\\ProgramData"],
                        "permite_scripts": True,
                        "permite_consola": False
                    },
                    "sin_restricciones": {
                        "_descripcion": "PELIGROSO. Acceso total. Borrado PERMANENTE. Solo rescate.",
                        "sandbox": False,
                        "permite_rutas_absolutas": True,
                        "permite_navegacion_padre": True,
                        "borrado": "permanente",
                        "comandos_bloqueados": [],
                        "limite_escritura_bytes": 0,
                        "limite_lectura_bytes": 10485760,
                        "carpetas_prohibidas": [],
                        "permite_scripts": True,
                        "permite_consola": True
                    }
                }
            }
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_default, f, indent=2, ensure_ascii=False)
        if not WISPOUT_FILE.exists():
            escribir_log("wispout.json no existe, creando por defecto")
            WISPOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            wispout_default = {
                "_waio_firma": "WAIO-V3-WISPOUT-2026",
                "_comentario": "NO EDITAR LA FIRMA. WAIO la usa para validar este archivo.",
                "_version": "1.0",
                "encabezado": {"plantilla": "WAIO {version} | {perfil} | {limite} | {borrado}", "mostrar": True},
                "recordatorio": {"activo": True, "mensaje": "Espera la confirmacion de WAIO antes de continuar."},
                "susurro": {"activo": True, "cada_cuantas_acciones": 3, "mensaje": "INSTRUCCION: Se breve, no alucines."},
                "respuestas_especiales": {
                    "perfil_cambiado": "Perfil cambiado a {perfil}",
                    "comando_bloqueado": "Comando '{comando}' bloqueado",
                    "error": "Error: {error}"
                }
            }
            with open(WISPOUT_FILE, "w", encoding="utf-8") as f:
                json.dump(wispout_default, f, indent=2, ensure_ascii=False)
    except Exception as e:
        escribir_log(f"Error creando archivos de configuracion: {e}")

def ejecutar_comando(accion, transaccion_id, accion_idx):
    comando_raw = accion.get("comando", "")
    comando = normalizar_comando(comando_raw)
    valido, msg = validar_accion(comando, accion.get("ruta", "") or accion.get("origen", ""))
    if not valido:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False
    if comando in COMANDOS_INTERNOS:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    if comando in COMANDOS_BASE:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    habilidades = cargar_habilidades()
    comandos = habilidades.get("skills", {})
    if comando not in comandos:
        msg = f"Comando no existe en skills.json: {comando}"
        escribir_log(msg)
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False
    info = comandos[comando]
    tipo = info.get("tipo", "nativo")
    perfil_requerido = info.get("perfil_minimo", "solo_lectura")
    perfiles_orden = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]
    if perfil_activo in perfiles_orden and perfil_requerido in perfiles_orden:
        if perfiles_orden.index(perfil_activo) < perfiles_orden.index(perfil_requerido):
            msg = f"Comando '{comando}' requiere perfil {perfil_requerido}. Perfil actual: {perfil_activo}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
    if tipo == "nativo":
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    elif tipo == "script":
        return ejecutar_script_desde_catalogo(comando, accion, transaccion_id, accion_idx, info)
    else:
        msg = f"Tipo de comando desconocido: {tipo}"
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False

def ejecutar_script_desde_catalogo(comando, accion, transaccion_id, accion_idx, info):
    try:
        ruta_relativa = info.get("ruta_script")
        if not ruta_relativa:
            msg = f"Script '{comando}' no tiene ruta_script definida"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        ruta_script = SCRIPT_DIR / ruta_relativa
        if not ruta_script.exists():
            msg = f"Script no encontrado: {ruta_script}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
        args = []
        for key, value in accion.items():
            if key not in ["comando", "transaccion_id"]:
                if isinstance(value, bool):
                    if value:
                        args.append(f"--{key}")
                else:
                    args.append(f"--{key}")
                    args.append(str(value))
        resultado = subprocess.run(
            [sys.executable, str(ruta_script)] + args,
            capture_output=True,
            text=True,
            timeout=60
        )
        if resultado.returncode == 0:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", resultado.stdout)
        else:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", resultado.stderr)
        return True
    except subprocess.TimeoutExpired:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Timeout: 60 segundos")
        return False
    except Exception as e:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
        return False

def ejecutar_nativo(comando, accion, transaccion_id, accion_idx):
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
    elif comando == "append_archivo":
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
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(contenido)
            msg = f"Contenido agregado a: {ruta.name}"
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
    elif comando == "renombrar_archivo":
        ruta_str = accion.get("ruta")
        nombre_nuevo = accion.get("nombre_nuevo")
        if not ruta_str or not nombre_nuevo:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'ruta' o 'nombre_nuevo'")
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
            destino = ruta.parent / nombre_nuevo
            shutil.move(str(ruta), str(destino))
            msg = f"Renombrado: {ruta.name} -> {nombre_nuevo}"
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
    elif comando == "buscar_archivos":
        ruta_str = accion.get("ruta", ".")
        patron = accion.get("patron", "*")
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                msg = f"Directorio no existe: {ruta_str}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            resultados = list(ruta.glob(patron))
            lista = ", ".join([f.name for f in resultados]) if resultados else "vacio"
            escribir_log(f"Busqueda {patron} en {ruta_str}: {lista}")
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
    elif comando == "leer_lineas":
        ruta_str = accion.get("ruta")
        inicio = accion.get("inicio", 1)
        fin = accion.get("fin", None)
        if not ruta_str:
            msg = "Falta 'ruta' en leer_lineas"
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
                lineas = f.readlines()
            total = len(lineas)
            if fin is None or fin > total:
                fin = total
            if inicio < 1:
                inicio = 1
            if inicio > total:
                msg = f"Linea de inicio {inicio} excede total {total}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
            seleccion = lineas[inicio-1:fin]
            resultado = "".join(seleccion)
            msg = f"Lineas {inicio}-{fin} de {total}:\n{resultado}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False
    elif comando == "contar_lineas":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            msg = "Falta 'ruta' en contar_lineas"
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
                lineas = f.readlines()
            total = len(lineas)
            msg = f"{total} lineas"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
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
    elif comando == "mensaje":
        contenido = accion.get("contenido", "")
        if not contenido:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'contenido'")
            return False
        guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", contenido)
        return True
    elif comando == "skills" or comando == "listar_skills" or comando == "list_skills" or comando == "info":
        nombre = accion.get("nombre")
        if nombre:
            ruta_json = None
            for carpeta in [SKILLS_DIR, CORE_DIR]:
                posible = carpeta / nombre / f"{nombre}.json"
                if posible.exists():
                    ruta_json = posible
                    break
            if not ruta_json:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"JSON de skill no encontrado: {nombre}")
                return False
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    info = json.load(f)
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", json.dumps(info, indent=2, ensure_ascii=False))
                return True
            except Exception as e:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
                return False
        else:
            base_comandos = [
                "listar_directorio", "leer_archivo", "crear_archivo", "crear_carpeta",
                "mover_archivo", "copiar_archivo", "renombrar_archivo", "eliminar_archivo",
                "eliminar_carpeta", "existe_archivo", "obtener_tamano", "fecha_modificacion",
                "contar_lineas", "buscar_archivos", "leer_lineas", "append_archivo",
                "mensaje", "skills", "ayuda", "indexar", "ejecutar"
            ]
            resultado = "COMANDOS BASE (siempre disponibles):\n"
            for cmd in base_comandos:
                resultado += f"  - {cmd}\n"
            habilidades = cargar_habilidades()
            if habilidades.get("_total_skills", 0) > 0:
                skills = habilidades.get("skills", {})
                resultado += "\nSKILLS DISPONIBLES:\n"
                disponibles = []
                for cmd, info in skills.items():
                    if cmd in ["skills", "indexar"]:
                        continue
                    perfil_requerido = info.get("perfil_minimo", "solo_lectura")
                    if perfil_activo >= perfil_requerido:
                        disponibles.append(f"  - {cmd}: {info.get('descripcion', 'Sin descripcion')}")
                if disponibles:
                    resultado += "\n".join(disponibles)
                else:
                    resultado += "  (No hay skills disponibles para tu perfil)"
            else:
                resultado += "\nSKILLS DISPONIBLES:\n  (No hay skills. Ejecuta 'indexar' para generar el catalogo.)"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", resultado)
            return True
    elif comando == "ayuda" or comando == "help" or comando == "?":
        mensaje = """WAIO 3.2 - AYUDA RAPIDA

COMANDOS BASE:
  listar_directorio, leer_archivo, crear_archivo, crear_carpeta,
  mover_archivo, copiar_archivo, renombrar_archivo,
  eliminar_archivo, eliminar_carpeta, existe_archivo,
  obtener_tamano, fecha_modificacion, contar_lineas,
  buscar_archivos, leer_lineas, append_archivo, mensaje

COMANDOS ESPECIALES:
  skills            -> Lista skills disponibles
  skills voz        -> Muestra JSON de la skill 'voz'
  indexar           -> Regenera el catalogo de skills
  ejecutar          -> Ejecuta un script (skills/, core/, workdir)
  ayuda             -> Muestra esta ayuda

PERFILES:
  solo_lectura      -> Solo lectura y listado
  estandar          -> Lectura, escritura, todo a Papelera
  avanzado          -> Todo lo anterior + eliminacion y scripts
  sin_restricciones -> Acceso total

EJEMPLO:
  {"comando": "skills"}
  {"comando": "skills", "nombre": "voz"}
  {"comando": "indexar"}
  {"comando": "ejecutar", "script": "hola_mundo.py"}
"""
        guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", mensaje)
        return True
    elif comando == "indexar" or comando == "index":
        try:
            script_path = SCRIPT_DIR / "core" / "indexar" / "indexar.py"
            if not script_path.exists():
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "indexar.py no encontrado")
                return False
            resultado = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, timeout=60)
            if resultado.returncode == 0:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", resultado.stdout)
            else:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", resultado.stderr)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False
    elif comando == "ejecutar" or comando == "run":
        script = accion.get("script")
        if not script:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'script'")
            return False
        args = accion.get("parametros", [])
        if isinstance(args, str):
            args = [args]
        elif not isinstance(args, list):
            args = []
        ruta_script = None
        nombre_limpio = script
        if nombre_limpio.endswith('.py'):
            nombre_limpio = nombre_limpio[:-3]
        if SKILLS_FILE.exists():
            try:
                with open(SKILLS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                skills = data.get("skills", {})
                if nombre_limpio in skills:
                    ruta_relativa = skills[nombre_limpio].get("ruta_script")
                    if ruta_relativa:
                        ruta_script = SCRIPT_DIR / ruta_relativa
            except:
                pass
        if not ruta_script or not ruta_script.exists():
            for carpeta in [SKILLS_DIR, CORE_DIR]:
                if not carpeta.exists():
                    continue
                for subcarpeta in carpeta.iterdir():
                    if subcarpeta.is_dir() and subcarpeta.name == nombre_limpio:
                        for ext in ['.py', '.pyw']:
                            p = subcarpeta / f"{nombre_limpio}{ext}"
                            if p.exists():
                                ruta_script = p
                                break
                        if ruta_script:
                            break
                if ruta_script:
                    break
        if not ruta_script or not ruta_script.exists():
            work_dir = WORK_DIR
            if WORKDIR_FILE.exists():
                try:
                    work_dir = Path(WORKDIR_FILE.read_text().strip())
                except:
                    pass
            for p in [work_dir / script, work_dir / f"{nombre_limpio}.py"]:
                if p.exists():
                    ruta_script = p
                    break
        if not ruta_script or not ruta_script.exists():
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Script no encontrado: {script}")
            return False
        try:
            resultado = subprocess.run(
                [sys.executable, str(ruta_script)] + args,
                capture_output=True,
                text=True,
                timeout=60
            )
            if resultado.returncode == 0:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", resultado.stdout)
            else:
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", resultado.stderr)
            return True
        except subprocess.TimeoutExpired:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Timeout: 60 segundos")
            return False
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False
    return False

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
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq pythonw.exe'], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if 'pythonw.exe' not in result.stdout:
            subprocess.Popen(['pythonw', str(visor_path)], creationflags=subprocess.CREATE_NO_WINDOW)
            escribir_log("Visor iniciado")
        else:
            escribir_log("Visor ya corriendo")
    except Exception as e:
        escribir_log(f"Error lanzando visor: {e}")

def main():
    try:
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
        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, "r") as f:
                    pid_viejo = int(f.read().strip())
                subprocess.run(["taskkill", "/PID", str(pid_viejo), "/F"], capture_output=True)
                LOCK_FILE.unlink()
                escribir_log(f"Instancia anterior (PID {pid_viejo}) cerrada.")
            except Exception as e:
                escribir_log(f"Error cerrando instancia anterior: {e}")
                try:
                    LOCK_FILE.unlink()
                except:
                    pass
        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        escribir_log(f"Lock creado. PID: {os.getpid()}")
        WORKDIR_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WORKDIR_FILE, "w") as f:
            f.write(str(WORK_DIR))
        crear_archivos_si_faltan()
        escribir_log("Verificando catalogo de skills...")
        if not SKILLS_FILE.exists():
            escribir_log("skills.json no existe. Indexando...")
            try:
                indexer = SCRIPT_DIR / "core" / "indexar" / "indexar.py"
                if indexer.exists():
                    resultado = subprocess.run([sys.executable, str(indexer)], capture_output=True, text=True, timeout=60)
                    if resultado.returncode == 0:
                        escribir_log("Indexacion completada.")
                    else:
                        escribir_log(f"Error en indexacion: {resultado.stderr}")
                else:
                    escribir_log("indexar.py no encontrado en core/indexar/")
            except Exception as e:
                escribir_log(f"Error indexando: {e}")
        else:
            escribir_log("skills.json encontrado.")
        cargar_config()
        cargar_habilidades()
        cargar_wispout()
        lanzar_visor()
        cargar_y_procesar_prompt()
        directorio_escucha = obtener_directorio_descargas()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        JSONOUT_DIR.mkdir(parents=True, exist_ok=True)
        escribir_log("=" * 50)
        escribir_log(f"WAIO_ESCUCHA_{VERSION}_INICIADO")
        escribir_log(f"Log: {LOG_FILE}")
        escribir_log(f"Script: {SCRIPT_DIR}")
        escribir_log(f"Work dir: {WORK_DIR}")
        escribir_log(f"Escuchando: {directorio_escucha}")
        escribir_log(f"Perfil activo: {perfil_activo}")
        escribir_log(f"Limite lectura: {MAX_READ_DEFAULT} (default) / {ABSOLUTE_MAX_READ} (max)")
        escribir_log("=" * 50)
        ultimo_procesado = None
        errores_consecutivos = 0
        while True:
            try:
                if verificar_stop():
                    break
                cargar_config()
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
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            escribir_log("Lock eliminado.")
        escribir_log(f"WAIO_ESCUCHA_{VERSION}_FINALIZADO")
    except Exception as e:
        escribir_log(f"ERROR FATAL: {e}")
        import traceback
        escribir_log(traceback.format_exc())
        if LOCK_FILE.exists():
            try:
                LOCK_FILE.unlink()
            except:
                pass
        time.sleep(5)

if __name__ == "__main__":
    main()