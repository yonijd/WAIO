# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

import os
import sys
import json
import re
import time
import shutil
import winreg
import subprocess
import threading
from pathlib import Path
from datetime import datetime

VERSION = "3.3"

SCRIPT_DIR = Path(__file__).parent.resolve()

WORK_DIR = SCRIPT_DIR
if len(sys.argv) > 2 and sys.argv[1] == "--cwd":
    try:
        WORK_DIR = Path(sys.argv[2]).resolve()
    except Exception as e:
        print(f"Error cambiando directorio: {e}")

try:
    os.chdir(WORK_DIR)
except Exception as e:
    print(f"Error cambiando al workdir {WORK_DIR}: {e}")
    WORK_DIR = SCRIPT_DIR

JSONOUT_DIR = SCRIPT_DIR / "temp" / "jsonout"
OUTPUT_DIR = SCRIPT_DIR / "temp" / "output"
QUEUE_DIR = SCRIPT_DIR / "temp" / "queue"
PROCESSING_DIR = SCRIPT_DIR / "temp" / "processing"
RECHAZADOS_DIR = SCRIPT_DIR / "temp" / "jsonout" / "rechazados"
LOG_DIR = SCRIPT_DIR / "temp" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

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

NOMBRES_RESERVADOS = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}

CONSOLA_COMANDOS_PERMITIDOS = [
    "pip", "python", "dir", "ls", "echo", "type", "findstr", "grep",
    "where", "which", "date", "time", "ver", "systeminfo",
    "ipconfig", "ping", "tracert", "netstat", "tasklist"
]

CONSOLA_COMANDOS_PROHIBIDOS = [
    "del", "erase", "rm", "rmdir", "format", "diskpart",
    "shutdown", "restart", "reboot", "taskkill", "kill",
    "reg", "regedit", "sc", "net", "netsh"
]

CONSOLA_CARACTERES_PROHIBIDOS = ["|", ">", "<", "&", ";", "`", "$", "\n", "\r"]

CONSOLA_TIMEOUT_DEFAULT = 10
CONSOLA_TIMEOUT_MAX = 300

TX_ID_PATTERN = re.compile(r"^[A-Za-z0-9_\-]{1,100}$")

perfil_activo = "standard"
config_cache = None
habilidades_cache = None
wispout_cache = None
contador_acciones = 0

_config_mtime = None
_habilidades_mtime = None
_wispout_mtime = None

_comandos_internos_cache = None
_mapeo_comandos_cache = None

_transacciones_recientes = []
_indice_duplicados = set()

COMANDOS_INTERNOS_BASE = {
    "skills", "listar_skills", "list_skills", "info",
    "ayuda", "help", "?", "indexar", "index", "ejecutar", "run", "mensaje"
}

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
    "eliminar_carpeta",
    "ejecutar_comando"
]

ALIAS_BASE = {
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
    "read_skill": "skills",
    "comando": "ejecutar_comando",
    "shell": "ejecutar_comando",
    "cmd": "ejecutar_comando",
    "system": "ejecutar_comando"
}

PROMPT_DEFAULT = """PROMPT MAESTRO: WAIO 3.3

Eres un agente de sistema para WAIO (Web AI Orchestrator). Tu tarea es generar JSON para ejecutar acciones en el sistema local.

COMO FUNCIONA:
1. Generas un archivo JSON con una transaccion_id y una lista de acciones.
2. WAIO detecta el JSON en la carpeta de escucha (por defecto Downloads) y ejecuta las acciones.
3. WAIO devuelve un JSON con los resultados en temp/output/.
4. Cada accion es un objeto con "comando" y los parametros que requiere.

REGLA DE IDs (OBLIGATORIA):
- Cada "transaccion_id" debe ser UNICO. No reutilices IDs de transacciones anteriores.
- NO uses los IDs de los ejemplos de este prompt. NO los copies. Inventa IDs nuevos.
- El "transaccion_id" debe ser alfanumerico con "_" y "-". No uses "/", "\\", ":", ".." ni nombres reservados.
- Formato recomendado: tx_<descripcion_corta>_<timestamp>
- Ejemplo: tx_crear_readme_20261024_031915

PERFILES DE SEGURIDAD:
WAIO tiene 4 perfiles que determinan que comandos puedes usar.

- readonly (solo lectura): Solo lectura y listado. No puedes modificar ni borrar. No ejecutas scripts.
- standard (seguro, uso normal): Lectura, escritura, creacion, copia, movimiento y eliminacion (a Papelera). Ejecutas los comandos del catalogo de standard. No ejecutas scripts arbitrarios.
- advanced (desarrollador): Todo lo anterior + ejecucion de scripts del catalogo (cualquier script). No puedes usar consola.
- debug (rescate/depuracion): Acceso total, incluida consola. Borrado permanente. Solo para rescate o pruebas avanzadas.

NOMBRES RESERVADOS DEL SISTEMA:
- No uses CON, NUL, PRN, AUX, COM1-COM9, LPT1-LPT9 como nombres de archivo o carpeta.
- Windows los intercepta y el motor se cuelga o falla.
- Tampoco uses ":" en el nombre (Windows lo interpreta como flujo alternativo).
- Si intentas usarlos, el motor rechaza la accion con error.

COMANDOS DISPONIBLES (con alias):

COMANDOS BASE (OPERACIONES DE SISTEMA):

listar_directorio (listar, ls, dir)
  - Lista archivos y carpetas en una ruta.
  - Parametros: {"ruta": "carpeta"} (opcional, default: ".")
  - En standard y superiores, se recomienda usar "listia" para mejor contexto del directorio.

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
  - Renombra un archivo. El "nombre_nuevo" debe ser un nombre simple (sin /, \\, .., :).
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

COMANDOS DEL CATALOGO (disponibles segun perfil):

El catalogo de comandos disponibles depende del perfil y de lo que este instalado.
Para ver la lista actualizada, ejecuta {"comando": "skills"}.

Ejemplos de comandos que suelen estar disponibles en standard (pueden variar):
  - listia: lista el contenido de un directorio en JSON estructurado.
  - voz: reproduce texto por voz.
  - grep: busqueda avanzada en archivos.

Si necesitas un comando que no aparece, ejecuta "skills" para ver el catalogo actual.

COMANDOS ESPECIALES:

skills (listar_skills, list_skills)
  - Sin parametros: Muestra la lista de comandos y scripts disponibles para tu perfil.
  - Ejemplo: {"comando": "skills"}

ayuda (help, ?)
  - Muestra esta guia de ayuda.
  - Ejemplo: {"comando": "ayuda"}

indexar (index)
  - Regenera el catalogo de comandos y scripts disponibles.
  - Sin parametros.
  - Ejemplo: {"comando": "indexar"}

ejecutar_comando
  - Ejecuta comandos del sistema (consola). Solo disponible en debug.
  - Si tu perfil no es debug, no lo intentes.

PARAMETRO TIMEOUT:
Cada script ya establece un timeout en su definicion. NO necesitas especificar "timeout" en la accion. Solo especificalo si necesitas MAS tiempo del que el script ya tiene.
Ejemplo:
  {"comando": "crear_archivo", "ruta": "nota.txt", "contenido": "Hola"}
En este ejemplo, "crear_archivo" es un comando base y no requiere timeout.

COMANDOS POR PERFIL:

- readonly: skills, ayuda, listar_directorio, leer_archivo, existe_archivo, obtener_tamano, fecha_modificacion, contar_lineas, buscar_archivos, leer_lineas
- standard: Lo anterior + crear_archivo, crear_carpeta, mover_archivo, copiar_archivo, renombrar_archivo, append_archivo, eliminar_archivo, eliminar_carpeta, indexar (y el catalogo de standard)
- advanced: Todo lo anterior + ejecutar (cualquier script del catalogo). No consola.
- debug: Todo permitido, incluida consola (ejecutar_comando).

EJEMPLO DE JSON (NO COPIES EL ID DE ESTE EJEMPLO. INVENTA UNO NUEVO):
{
  "transaccion_id": "tx_ejemplo_inventado_20261024_031915",
  "acciones": [
    {"comando": "skills"},
    {"comando": "crear_carpeta", "ruta": "proyecto"},
    {"comando": "crear_archivo", "ruta": "proyecto/nota.txt", "contenido": "Hola, soy WAIO"},
    {"comando": "listar_directorio", "ruta": "proyecto"},
    {"comando": "leer_archivo", "ruta": "proyecto/nota.txt"}
  ]
}

EJEMPLO DE JSON PARA STANDARD (solo comandos base + catalogo de standard):
{
  "transaccion_id": "tx_standard_ejemplo_20261024_031916",
  "acciones": [
    {"comando": "crear_archivo", "ruta": "saludo.txt", "contenido": "Hola"},
    {"comando": "append_archivo", "ruta": "saludo.txt", "contenido": "\\nSegunda linea"},
    {"comando": "contar_lineas", "ruta": "saludo.txt"},
    {"comando": "copiar_archivo", "origen": "saludo.txt", "destino": "saludo_backup.txt"},
    {"comando": "listia", "ruta": ".", "profundidad": 1}
  ]
}

REGLAS ESTRICTAS:
- El JSON debe ser 100% valido.
- No uses funciones, expresiones ni operadores.
- Usa strings literales, no instrucciones de repeticion.
- Usa los nombres de parametros exactos (origen/destino, no ruta_origen).
- NO uses IDs duplicados. NO copies el ID del ejemplo. INVENTA uno nuevo.
- NO uses nombres reservados de Windows (CON, NUL, PRN, AUX, COM1-9, LPT1-9).
- NO uses ":" en nombres de archivo o carpeta.
- En perfil advanced, NO toques C:\\Windows, C:\\Program Files, C:\\ProgramData.

INSTRUCCION DIRECTA:
Ejecuta "skills" para ver los comandos disponibles para tu perfil. Despues, genera el JSON."""


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def escribir_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as log:
            log.write(f"[{timestamp}] {mensaje}\n")
    except Exception:
        try:
            with open(LOG_FILE, "a", encoding="ascii", errors="replace") as log:
                log.write(f"[{timestamp}] {mensaje}\n")
        except Exception:
            pass


# ----------------------------------------------------------------------
# Utilidades de formato
# ----------------------------------------------------------------------

def formatear_limite(limite):
    if limite >= 1048576:
        return f"{limite // 1048576}MB"
    elif limite >= 1024:
        return f"{limite // 1024}KB"
    else:
        return f"{limite}B"


# ----------------------------------------------------------------------
# Sanitizacion de transaccion_id
# ----------------------------------------------------------------------

def es_tx_id_valido(tx_id):
    if not isinstance(tx_id, str):
        return False
    return bool(TX_ID_PATTERN.match(tx_id))


def sanitizar_tx_id(tx):
    tx = str(tx)
    tx = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', tx).strip('. ')
    if not tx or tx.upper() in NOMBRES_RESERVADOS:
        tx = "tx_sin_id"
    return tx[:100]


# ----------------------------------------------------------------------
# Carga de config / skills / wispout (con cache por mtime)
# ----------------------------------------------------------------------

def config_get(clave, default):
    try:
        config = cargar_config()
        valor = config.get(clave, default)
        if valor is None:
            return default
        if isinstance(default, float):
            return float(valor)
        elif isinstance(default, int):
            return int(valor)
        return valor
    except Exception as e:
        escribir_log(f"Error leyendo config '{clave}': {e}")
        return default


def cargar_config():
    global perfil_activo, config_cache, _config_mtime
    try:
        if not CONFIG_FILE.exists():
            return usar_config_default()

        mtime = CONFIG_FILE.stat().st_mtime
        if config_cache is not None and _config_mtime == mtime:
            return config_cache

        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config_cache = json.load(f)
        _config_mtime = mtime

        if config_cache.get("_waio_firma") != "WAIO-V3-CONFIG-2026":
            escribir_log("ADVERTENCIA: waio_config.json sin firma. Usando defaults.")
            return usar_config_default()

        perfil_nuevo = config_cache.get("perfil_activo", "standard")
        perfiles = config_cache.get("perfiles", {})
        if perfil_nuevo not in perfiles:
            escribir_log(f"ADVERTENCIA: perfil '{perfil_nuevo}' no existe. Forzando standard.")
            perfil_nuevo = "standard"
            config_cache["perfil_activo"] = "standard"

        perfil_activo = perfil_nuevo
        escribir_log(f"Config cargada. Perfil: {perfil_activo}")
        return config_cache
    except Exception as e:
        escribir_log(f"Error cargando config: {e}")
        return usar_config_default()


def usar_config_default():
    global perfil_activo
    perfil_activo = "standard"
    return {
        "_waio_firma": "WAIO-V3-CONFIG-2026",
        "_comentario": "NO EDITAR LA FIRMA. WAIO la usa para validar este archivo.",
        "_version": "3.3",
        "_notas": {
            "_limites": "limite_escritura_bytes protege el disco (evita llenarlo). limite_lectura_chars protege el contexto del LLM (evita enviar mas de lo que el modelo procesa). NO igualar ambos: 10 MB de lectura ya es el techo practico para modelos de ~1M tokens.",
            "_perfiles": "readonly = solo lectura. standard = uso normal (sandbox, Papelera). advanced = desarrollador (disco completo, sin consola). debug = rescate (consola, borrado permanente, sin restricciones por defecto).",
            "_carpetas_prohibidas": "En advanced y debug se prohiben C:\\Windows, C:\\Program Files, C:\\Program Files (x86) y C:\\ProgramData. En debug el usuario puede vaciar la lista para modo debug libre.",
            "_permite_consola": "Solo existe en advanced (false) y debug (true). En readonly y standard no aparece porque el comando no llega a esos perfiles.",
            "_limite_escritura_bytes": "readonly = 0 (no escritura, tras el fix del bug). standard = 1 MB. advanced = 10 MB. debug = 100 MB (tope de saturacion, no 'sin limite').",
            "_limite_lectura_chars": "readonly = 500000 chars. standard = 1M chars. advanced = 10M chars. debug = 10M chars. Se aplica sobre caracteres, no bytes (nombre historico)."
        },
        "perfil_activo": "standard",

        "downloads_scan_interval": 2.0,
        "downloads_stabilize_wait": 0.3,
        "error_backoff_seconds": 2.0,
        "error_backoff_max_seconds": 5.0,

        "directorio_escucha": {
            "activo": False,
            "ruta": ""
        },

        "leer_json_en_downloads": True,
        "aceptar_id_duplicado": False,

        "indexar_timeout_seconds": 120,
        "read_default_chars": 500000,
        "read_absolute_max_chars": 10000000,

        "output_buffer_max_items": 50,
        "output_buffer_timeout_seconds": 5.0,
        "output_scan_interval_seconds": 0.5,

        "visor_max_lines": 500,
        "visor_refresh_ms": 1000,
        "logs_retention_days": 7,
        "logs_level": "info",

        "ignorados_max_items": 1000,

        "max_actions_per_transaction": 100,
        "max_transactions_per_minute": 60,
        "max_output_files": 1000,
        "max_jsonout_files": 1000,

        "timeout_default_segundos": 120,
        "timeout_max_segundos": 600,

        "perfiles": {
            "readonly": {
                "_descripcion": "SOLO LECTURA (readonly). Puede ver y listar, pero no modificar ni borrar. No ejecuta scripts.",
                "sandbox": True,
                "permite_rutas_absolutas": False,
                "permite_navegacion_padre": False,
                "borrado": "papelera",
                "comandos_bloqueados": ["crear_archivo", "crear_carpeta", "eliminar_archivo", "eliminar_carpeta", "mover_archivo", "copiar_archivo", "append_archivo"],
                "limite_escritura_bytes": 0,
                "limite_lectura_chars": 500000,
                "carpetas_prohibidas": [],
                "permite_ejecutar_core": False,
                "permite_ejecutar_skills": False,
                "permite_ejecutar_workdir": False,
                "permite_ejecutar_disco": False
            },
            "standard": {
                "_descripcion": "SEGURO, USO NORMAL (standard). Lee, escribe y borra (a Papelera) dentro del workdir. Ejecuta los comandos del catalogo de standard.",
                "sandbox": True,
                "permite_rutas_absolutas": False,
                "permite_navegacion_padre": False,
                "borrado": "papelera",
                "comandos_bloqueados": [],
                "limite_escritura_bytes": 1048576,
                "limite_lectura_chars": 1048576,
                "carpetas_prohibidas": [],
                "permite_ejecutar_core": True,
                "permite_ejecutar_skills": False,
                "permite_ejecutar_workdir": False,
                "permite_ejecutar_disco": False
            },
            "advanced": {
                "_descripcion": "DESARROLLADOR (advanced). Lee y escribe en todo el disco (excepto Windows/Program Files/ProgramData). Ejecuta scripts del catalogo y del workdir. No consola.",
                "sandbox": False,
                "permite_rutas_absolutas": True,
                "permite_navegacion_padre": True,
                "borrado": "papelera",
                "comandos_bloqueados": [],
                "limite_escritura_bytes": 10485760,
                "limite_lectura_chars": 10485760,
                "carpetas_prohibidas": ["C:\\Windows", "C:\\Windows\\System32", "C:\\Windows\\System", "C:\\Program Files", "C:\\Program Files (x86)", "C:\\ProgramData"],
                "permite_ejecutar_core": True,
                "permite_ejecutar_skills": True,
                "permite_ejecutar_workdir": True,
                "permite_ejecutar_disco": False,
                "permite_consola": False
            },
            "debug": {
                "_descripcion": "RESCATE/DEPURACION (debug). Borrado PERMANENTE. Consola habilitada. Carpetas prohibidas minimas por defecto; el usuario puede vaciarlas para modo libre.",
                "sandbox": False,
                "permite_rutas_absolutas": True,
                "permite_navegacion_padre": True,
                "borrado": "permanente",
                "comandos_bloqueados": [],
                "limite_escritura_bytes": 104857600,
                "limite_lectura_chars": 10485760,
                "carpetas_prohibidas": ["C:\\Windows", "C:\\Windows\\System32", "C:\\Windows\\System", "C:\\Program Files", "C:\\Program Files (x86)", "C:\\ProgramData"],
                "permite_ejecutar_core": True,
                "permite_ejecutar_skills": True,
                "permite_ejecutar_workdir": True,
                "permite_ejecutar_disco": True,
                "permite_consola": True
            }
        }
    }


def cargar_habilidades():
    global habilidades_cache, _habilidades_mtime
    try:
        if not SKILLS_FILE.exists():
            return usar_habilidades_default()

        mtime = SKILLS_FILE.stat().st_mtime
        if habilidades_cache is not None and _habilidades_mtime == mtime:
            return habilidades_cache

        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            habilidades_cache = json.load(f)
        _habilidades_mtime = mtime

        if habilidades_cache.get("_waio_firma") != "WAIO-V3-SKILLS-2026":
            escribir_log("ADVERTENCIA: skills.json sin firma. Usando defaults.")
            return usar_habilidades_default()

        total = habilidades_cache.get("_total_skills", 0)
        escribir_log(f"Skills cargadas: {total}")
        return habilidades_cache
    except Exception as e:
        escribir_log(f"Error cargando skills: {e}")
        return usar_habilidades_default()


def usar_habilidades_default():
    return {
        "_waio_firma": "WAIO-V3-SKILLS-2026",
        "_version": "1.0",
        "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "_total_skills": 0,
        "categorias": {},
        "resumen_por_perfil": {},
        "skills": {}
    }


def cargar_wispout():
    global wispout_cache, _wispout_mtime
    try:
        if not WISPOUT_FILE.exists():
            return usar_wispout_default()

        mtime = WISPOUT_FILE.stat().st_mtime
        if wispout_cache is not None and _wispout_mtime == mtime:
            return wispout_cache

        with open(WISPOUT_FILE, "r", encoding="utf-8") as f:
            wispout_cache = json.load(f)
        _wispout_mtime = mtime

        if wispout_cache.get("_waio_firma") != "WAIO-V3-WISPOUT-2026":
            escribir_log("ADVERTENCIA: wispout.json sin firma. Usando defaults.")
            return usar_wispout_default()

        escribir_log("wispout.json cargado")
        return wispout_cache
    except Exception as e:
        escribir_log(f"Error cargando wispout: {e}")
        return usar_wispout_default()


def usar_wispout_default():
    return {
        "_waio_firma": "WAIO-V3-WISPOUT-2026",
        "_comentario": "NO EDITAR LA FIRMA. WAIO la usa para validar este archivo.",
        "_version": "1.0",
        "status": {
            "activo": True,
            "plantilla": "version: {version} | perfil: {perfil} | limite: {limite} | borrado: {borrado}"
        },
        "comando": {
            "activo": True,
            "plantilla": "{comando} | {status}"
        },
        "resultado": {
            "activo": True
        },
        "aviso": {
            "activo": False,
            "inicio_accion": 0,
            "duracion_acciones": 3,
            "cada_cuantas_acciones": 0,
            "repeticion_cada": 0,
            "mostrar_en_error": False,
            "mostrar_en_primera": False,
            "mensaje": "Revisa los logs si algo falla."
        },
        "susurro": {
            "activo": False,
            "inicio_accion": 0,
            "duracion_acciones": 0,
            "cada_cuantas_acciones": 3,
            "repeticion_cada": 0,
            "mostrar_en_error": False,
            "mostrar_en_primera": False,
            "mensaje": "INSTRUCCION: Se breve, no alucines."
        },
        "recordatorio": {
            "activo": True,
            "inicio_accion": 0,
            "duracion_acciones": 0,
            "cada_cuantas_acciones": 0,
            "repeticion_cada": 0,
            "mostrar_en_error": True,
            "mostrar_en_primera": True,
            "mensaje": "Espera la confirmacion de WAIO antes de continuar."
        },
        "respuestas_especiales": {
            "activo": False,
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


def obtener_timeout(accion, info):
    try:
        timeout_default = config_get("timeout_default_segundos", 120)
        timeout_max = config_get("timeout_max_segundos", 600)
        timeout_skill = info.get("timeout_segundos", timeout_default)
        timeout_accion = accion.get("timeout", timeout_skill)
        try:
            if timeout_accion < 0:
                escribir_log(f"ADVERTENCIA: timeout negativo ({timeout_accion}). Usando 1.")
                timeout_accion = 1
        except TypeError:
            timeout_accion = timeout_default
        return max(1, min(timeout_accion, timeout_skill, timeout_default, timeout_max))
    except Exception as e:
        escribir_log(f"Error calculando timeout: {e}")
        return 120


# ----------------------------------------------------------------------
# Lista negra de nombres reservados
# ----------------------------------------------------------------------

def es_nombre_reservado(ruta_str):
    if not ruta_str:
        return False
    try:
        import unicodedata
        nombre = Path(ruta_str).name
        if ":" in nombre:
            return True
        nombre_norm = unicodedata.normalize("NFKC", nombre).strip().upper()
        stem = Path(nombre_norm).stem
        return stem in NOMBRES_RESERVADOS
    except Exception:
        return False


# ----------------------------------------------------------------------
# Indice de duplicados
# ----------------------------------------------------------------------

def cargar_indice_duplicados():
    global indice_duplicados
    indice_duplicados = set()
    try:
        if not JSONOUT_DIR.exists():
            return
        for archivo in JSONOUT_DIR.glob("*.json"):
            try:
                with open(archivo, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                tx = datos.get("transaccion_id")
                if tx:
                    indice_duplicados.add(tx)
            except Exception:
                continue
        escribir_log(f"Indice de duplicados cargado: {len(indice_duplicados)} IDs")
    except Exception as e:
        escribir_log(f"Error cargando indice de duplicados: {e}")


def agregar_al_indice(tx_id):
    global indice_duplicados
    if tx_id:
        indice_duplicados.add(tx_id)


def es_duplicado(tx_id):
    return tx_id in indice_duplicados


# ----------------------------------------------------------------------
# Recuperacion de processing/
# ----------------------------------------------------------------------

def recuperar_processing():
    try:
        if not PROCESSING_DIR.exists():
            return
        archivos = list(PROCESSING_DIR.glob("*.json"))
        if not archivos:
            return
        escribir_log(f"CRASH: {len(archivos)} archivos en processing/ al arrancar")
        RECHAZADOS_DIR.mkdir(parents=True, exist_ok=True)
        for archivo in archivos:
            try:
                destino = RECHAZADOS_DIR / archivo.name
                if destino.exists():
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    destino = RECHAZADOS_DIR / f"{archivo.stem}_{ts}.json"
                shutil.move(str(archivo), str(destino))
                error_file = destino.with_suffix(".error.txt")
                with open(error_file, "w", encoding="utf-8") as f:
                    f.write(f"Rechazado: {datetime.now().isoformat()}\n")
                    f.write("Motivo: crasheo_a_mitad\n")
                    f.write("Acciones ejecutadas: ver output/ de esta transaccion\n")
                escribir_log(f"CRASH: {archivo.name} -> rechazados/")
            except Exception as e:
                escribir_log(f"CRASH: error moviendo {archivo.name}: {e}")
    except Exception as e:
        escribir_log(f"Error en recuperar_processing: {e}")


# ----------------------------------------------------------------------
# Directorio de escucha
# ----------------------------------------------------------------------

def obtener_directorio_descargas():
    ruta_std = Path.home() / "Downloads"
    if ruta_std.exists() and ruta_std.is_dir():
        return ruta_std
    ruta_esp = Path.home() / "Descargas"
    if ruta_esp.exists() and ruta_esp.is_dir():
        return ruta_esp
    try:
        subkey = r"Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\Shell Folders"
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        try:
            valor = winreg.QueryValueEx(clave, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            ruta_reg = Path(valor)
            if ruta_reg.exists() and ruta_reg.is_dir():
                return ruta_reg
        except Exception:
            pass
        finally:
            winreg.CloseKey(clave)
    except Exception:
        pass
    return Path.cwd()


def obtener_directorio_escucha():
    try:
        cfg = config_get("directorio_escucha", {})
        if isinstance(cfg, dict) and cfg.get("activo", False):
            ruta_cfg = cfg.get("ruta", "").strip()
            if ruta_cfg:
                ruta = Path(ruta_cfg)
                if ruta.exists() and ruta.is_dir():
                    escribir_log(f"Directorio de escucha (config): {ruta}")
                    return ruta
                else:
                    escribir_log(f"WARNING: directorio_escucha.ruta no existe: {ruta_cfg}. Usando fallback.")
    except Exception as e:
        escribir_log(f"Error leyendo directorio_escucha: {e}")
    return obtener_directorio_descargas()


# ----------------------------------------------------------------------
# Mapeo dinamico de comandos
# ----------------------------------------------------------------------

def construir_mapeo_comandos():
    global _mapeo_comandos_cache, _comandos_internos_cache
    if _mapeo_comandos_cache is not None:
        return _mapeo_comandos_cache, _comandos_internos_cache

    mapeo = {}
    for nombre in COMANDOS_BASE:
        mapeo[nombre] = nombre
    for alias, destino in ALIAS_BASE.items():
        mapeo[alias] = destino

    try:
        habilidades = cargar_habilidades()
        skills = habilidades.get("skills", {})
        for nombre, info in skills.items():
            mapeo[nombre] = nombre
            for alias in info.get("alias", []):
                if alias not in mapeo:
                    mapeo[alias] = nombre
    except Exception:
        pass

    _mapeo_comandos_cache = mapeo
    _comandos_internos_cache = set(COMANDOS_INTERNOS_BASE)
    return mapeo, _comandos_internos_cache


def normalizar_comando(comando):
    if not comando:
        return ""
    mapeo, _ = construir_mapeo_comandos()
    clave = comando.lower().strip()
    return mapeo.get(clave, clave)


# ----------------------------------------------------------------------
# Seguridad
# ----------------------------------------------------------------------

def ruta_segura(ruta_str):
    perfil = obtener_perfil()
    sandbox = perfil.get("sandbox", True)

    if perfil_activo != "debug" and es_nombre_reservado(ruta_str):
        escribir_log(f"SEGURIDAD: Nombre reservado rechazado: {ruta_str}")
        return None

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


def validar_accion(comando, accion):
    try:
        perfil = obtener_perfil()

        if comando in perfil.get("comandos_bloqueados", []):
            return False, f"Comando '{comando}' bloqueado en perfil {perfil_activo}"

        if comando in ["ejecutar", "run"]:
            if not (perfil.get("permite_ejecutar_core") or perfil.get("permite_ejecutar_skills") or perfil.get("permite_ejecutar_workdir") or perfil.get("permite_ejecutar_disco")):
                return False, "Ejecucion de scripts no permitida en perfil actual"

        campos_ruta = ["ruta", "origen", "destino", "ruta_script", "zip"]
        for campo in campos_ruta:
            valor = accion.get(campo, "")
            if not valor or not isinstance(valor, str):
                continue

            if perfil_activo != "debug" and es_nombre_reservado(valor):
                return False, f"Nombre reservado del sistema: {valor}"

            if not perfil.get("permite_rutas_absolutas", False):
                if len(valor) > 1 and valor[1] == ":":
                    return False, f"Rutas absolutas no permitidas en '{campo}'"

            if not perfil.get("permite_navegacion_padre", False):
                if ".." in valor:
                    return False, f"Navegacion a directorio padre no permitida en '{campo}'"

            for prohibida in perfil.get("carpetas_prohibidas", []):
                try:
                    prohibida_norm = Path(prohibida).resolve()
                    ruta_norm = Path(valor).resolve()
                    ruta_norm.relative_to(prohibida_norm)
                    return False, f"Carpeta prohibida: {prohibida}"
                except (ValueError, OSError):
                    continue

        if perfil_activo != "debug":
            waio_home = Path.home() / ".waio"
            try:
                for campo in campos_ruta:
                    valor = accion.get(campo, "")
                    if valor and isinstance(valor, str):
                        ruta_norm = Path(valor).resolve()
                        ruta_norm.relative_to(waio_home.resolve())
                        return False, f"Carpeta prohibida: {waio_home}"
            except (ValueError, OSError):
                pass

        return True, "OK"
    except Exception as e:
        escribir_log(f"Error en validacion: {e}")
        return False, str(e)


# ----------------------------------------------------------------------
# Formato del wisp
# ----------------------------------------------------------------------

def seccion_aplica(cfg, contador, status):
    if not cfg.get("activo", False):
        return False

    if cfg.get("mostrar_en_primera", False) and contador == 1:
        return True
    if cfg.get("mostrar_en_error", False) and status == "error":
        return True

    inicio = cfg.get("inicio_accion", 0)
    duracion = cfg.get("duracion_acciones", 0)
    cada = cfg.get("cada_cuantas_acciones", 0)
    repeticion = cfg.get("repeticion_cada", 0)

    if inicio == 0 and duracion == 0 and cada == 0 and repeticion == 0:
        return True

    if inicio > 0 and contador < inicio:
        return False

    if duracion > 0:
        fin = inicio + duracion
        if inicio <= contador < fin:
            return True
        if repeticion > 0 and contador > 0 and contador % repeticion == 0:
            return True
        if cada > 0 and contador > 0 and contador % cada == 0:
            return True
        return False

    if cada > 0 and contador > 0 and contador % cada == 0:
        return True
    if repeticion > 0 and contador > 0 and contador % repeticion == 0:
        return True

    return False


def formatear_respuesta(comando, status, output, accion_idx=1, total_acciones=1):
    global contador_acciones
    try:
        wispout = cargar_wispout()
        perfil = obtener_perfil()
        limite_str = formatear_limite(perfil.get("limite_escritura_bytes", 1048576))
        borrado = perfil.get("borrado", "papelera")

        contador_acciones += 1

        kwargs = {
            "version": VERSION,
            "perfil": perfil_activo.upper(),
            "limite": limite_str,
            "borrado": borrado,
            "comando": comando,
            "status": status,
            "accion": contador_acciones,
            "accion_idx": accion_idx,
            "total_acciones": total_acciones,
        }

        partes = []

        cfg = wispout.get("status", {})
        if cfg.get("activo", True):
            plantilla = cfg.get("plantilla", "version: {version} | perfil: {perfil} | limite: {limite} | borrado: {borrado}")
            partes.append(f"[STATUS] {plantilla.format(**kwargs)}")

        cfg = wispout.get("comando", {})
        if cfg.get("activo", True):
            plantilla = cfg.get("plantilla", "{comando} | {status}")
            partes.append(f"[COMANDO] {plantilla.format(**kwargs)}")

        cfg = wispout.get("resultado", {})
        if cfg.get("activo", True):
            partes.append(f"[RESULTADO]\n{output}")

        cfg = wispout.get("aviso", {})
        if seccion_aplica(cfg, contador_acciones, status):
            try:
                mensaje = cfg.get("mensaje", "").format(**kwargs)
                partes.append(f"[AVISO] {mensaje}")
            except Exception:
                partes.append(f"[AVISO] {cfg.get('mensaje', '')}")

        cfg = wispout.get("susurro", {})
        if seccion_aplica(cfg, contador_acciones, status):
            try:
                mensaje = cfg.get("mensaje", "").format(**kwargs)
                partes.append(f"[SUSURRO] {mensaje}")
            except Exception:
                partes.append(f"[SUSURRO] {cfg.get('mensaje', '')}")

        cfg = wispout.get("recordatorio", {})
        if seccion_aplica(cfg, contador_acciones, status):
            try:
                mensaje = cfg.get("mensaje", "").format(**kwargs)
                partes.append(f"[RECORDATORIO] {mensaje}")
            except Exception:
                partes.append(f"[RECORDATORIO] {cfg.get('mensaje', '')}")

        return "\n\n".join(partes)
    except Exception as e:
        escribir_log(f"Error formateando respuesta: {e}")
        return f"[COMANDO] {comando} | {status}\n[RESULTADO]\n{output}"


# ----------------------------------------------------------------------
# Limites de archivos
# ----------------------------------------------------------------------

def limpiar_outputs_viejos():
    try:
        max_files = config_get("max_output_files", 1000)
        if not OUTPUT_DIR.exists():
            return
        archivos = sorted(OUTPUT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime)
        if len(archivos) > max_files:
            excedente = len(archivos) - max_files
            for archivo in archivos[:excedente]:
                try:
                    archivo.unlink()
                except Exception:
                    pass
    except Exception as e:
        escribir_log(f"Error limpiando outputs viejos: {e}")


def limpiar_jsonout_viejos():
    try:
        max_files = config_get("max_jsonout_files", 1000)
        if not JSONOUT_DIR.exists():
            return
        archivos = sorted(JSONOUT_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime)
        if len(archivos) > max_files:
            excedente = len(archivos) - max_files
            for archivo in archivos[:excedente]:
                try:
                    archivo.unlink()
                except Exception:
                    pass
    except Exception as e:
        escribir_log(f"Error limpiando jsonout viejos: {e}")


def verificar_limite_transacciones():
    global _transacciones_recientes
    try:
        max_tx = config_get("max_transactions_per_minute", 60)
        ahora = time.time()
        _transacciones_recientes = [t for t in _transacciones_recientes if ahora - t < 60]
        if len(_transacciones_recientes) >= max_tx:
            return False
        _transacciones_recientes.append(ahora)
        return True
    except Exception as e:
        escribir_log(f"Error verificando limite de transacciones: {e}")
        return True


# ----------------------------------------------------------------------
# Guardar JSON de resultado
# ----------------------------------------------------------------------

def guardar_resultado_json(transaccion_id, accion_idx, comando, status, output, total_acciones=1):
    try:
        limpiar_outputs_viejos()

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        tx_seguro = sanitizar_tx_id(transaccion_id)
        nombre_archivo = f"{tx_seguro}_{accion_idx}_{timestamp}.json"
        archivo_json = OUTPUT_DIR / nombre_archivo
        respuesta_formateada = formatear_respuesta(comando, status, output, accion_idx, total_acciones)
        datos = {
            "transaccion_id": transaccion_id,
            "accion_idx": accion_idx,
            "total_acciones": total_acciones,
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


# ----------------------------------------------------------------------
# Eliminar seguro
# ----------------------------------------------------------------------

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


# ----------------------------------------------------------------------
# Kill switch
# ----------------------------------------------------------------------

def verificar_stop():
    if STOP_FILE.exists():
        return True
    return False


def limpiar_stop_signal():
    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except Exception:
            pass


# ----------------------------------------------------------------------
# Prompt
# ----------------------------------------------------------------------

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
        limite_str = formatear_limite(limite)
        info_adicional = f"\n\nPERFIL ACTIVO: {perfil_activo}\nLIMITE ESCRITURA: {limite_str}\nBORRADO: {perfil.get('borrado', 'papelera')}"
        contenido += info_adicional
        guardar_resultado_json("system_prompt", 1, "prompt", "ok", contenido, 1)
        escribir_log("Prompt procesado y enviado a output")
    except Exception as e:
        escribir_log(f"Error procesando prompt: {e}")


# ----------------------------------------------------------------------
# Crear archivos de config si faltan
# ----------------------------------------------------------------------

def crear_archivos_si_faltan():
    try:
        if not CONFIG_FILE.exists():
            escribir_log("waio_config.json no existe, creando por defecto")
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            config_default = usar_config_default()
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(config_default, f, indent=2, ensure_ascii=False)
        if not WISPOUT_FILE.exists():
            escribir_log("wispout.json no existe, creando por defecto")
            WISPOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
            wispout_default = usar_wispout_default()
            with open(WISPOUT_FILE, "w", encoding="utf-8") as f:
                json.dump(wispout_default, f, indent=2, ensure_ascii=False)
    except Exception as e:
        escribir_log(f"Error creando archivos de configuracion: {e}")


# ----------------------------------------------------------------------
# Escalera: resolver script permitido
# ----------------------------------------------------------------------

def resolver_script_permitido(script, perfil):
    nombre_limpio = script
    if nombre_limpio.endswith('.py'):
        nombre_limpio = nombre_limpio[:-3]

    if perfil.get("permite_ejecutar_core", False):
        if CORE_DIR.exists():
            for subcarpeta in CORE_DIR.iterdir():
                if subcarpeta.is_dir() and subcarpeta.name == nombre_limpio:
                    for ext in ['.py', '.pyw']:
                        p = subcarpeta / f"{nombre_limpio}{ext}"
                        if p.exists():
                            return p, "core"

    if perfil.get("permite_ejecutar_skills", False):
        habilidades = cargar_habilidades()
        skills = habilidades.get("skills", {})
        if nombre_limpio in skills:
            ruta_relativa = skills[nombre_limpio].get("ruta_script")
            if ruta_relativa:
                p = SCRIPT_DIR / ruta_relativa
                if p.exists():
                    return p, "skills"
        if SKILLS_DIR.exists():
            for subcarpeta in SKILLS_DIR.iterdir():
                if subcarpeta.is_dir() and subcarpeta.name == nombre_limpio:
                    for ext in ['.py', '.pyw']:
                        p = subcarpeta / f"{nombre_limpio}{ext}"
                        if p.exists():
                            return p, "skills"

    if perfil.get("permite_ejecutar_workdir", False):
        work_dir = WORK_DIR
        if WORKDIR_FILE.exists():
            try:
                work_dir = Path(WORKDIR_FILE.read_text().strip())
            except Exception:
                pass
        for p in [work_dir / script, work_dir / f"{nombre_limpio}.py"]:
            if p.exists() and p.is_file():
                return p, "workdir"

    if perfil.get("permite_ejecutar_disco", False):
        p = Path(script)
        if p.is_absolute() and p.exists() and p.is_file():
            for prohibida in perfil.get("carpetas_prohibidas", []):
                try:
                    p.resolve().relative_to(Path(prohibida).resolve())
                    return None, None
                except (ValueError, OSError):
                    pass
            return p, "disco"

    return None, None


# ----------------------------------------------------------------------
# Consola: validacion de tokens
# ----------------------------------------------------------------------

def consola_comando_seguro(tokens):
    if not tokens:
        return False, "Comando vacio"
    for token in tokens:
        for c in CONSOLA_CARACTERES_PROHIBIDOS:
            if c in token:
                return False, f"Caracter no permitido: '{c}'"
    comando_str = " ".join(tokens).lower()
    for prohibido in CONSOLA_COMANDOS_PROHIBIDOS:
        if re.search(rf'\b{prohibido}\b', comando_str):
            return False, f"Comando prohibido: {prohibido}"
    primer_token = tokens[0].lower()
    if primer_token not in CONSOLA_COMANDOS_PERMITIDOS:
        return False, f"Comando no permitido: {primer_token}"
    if primer_token == "python":
        for token in tokens[1:]:
            if token in ("-c", "-m"):
                return False, f"python {token} no permitido (ejecucion arbitraria)"
    if shutil.which(primer_token) is None:
        return False, f"Binario no encontrado en el PATH: {primer_token}"
    return True, "OK"


# ----------------------------------------------------------------------
# Dispatch de comandos
# ----------------------------------------------------------------------

def ejecutar_comando(accion, transaccion_id, accion_idx, total_acciones):
    comando_raw = accion.get("comando", "")
    comando = normalizar_comando(comando_raw)
    perfil = obtener_perfil()

    valido, msg = validar_accion(comando, accion)
    if not valido:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
        return False

    mapeo, internos = construir_mapeo_comandos()

    if comando in internos:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx, total_acciones)

    if comando in COMANDOS_BASE:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx, total_acciones)

    habilidades = cargar_habilidades()
    comandos = habilidades.get("skills", {})
    if comando not in comandos:
        msg = f"Comando no existe en skills.json: {comando}"
        escribir_log(msg)
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
        return False

    info = comandos[comando]
    tipo = info.get("tipo", "nativo")
    perfil_requerido = info.get("perfil_minimo", "readonly")
    perfiles_orden = ["readonly", "standard", "advanced", "debug"]
    if perfil_activo in perfiles_orden and perfil_requerido in perfiles_orden:
        if perfiles_orden.index(perfil_activo) < perfiles_orden.index(perfil_requerido):
            msg = f"Comando '{comando}' requiere perfil {perfil_requerido}. Perfil actual: {perfil_activo}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
            return False

    if tipo in ("nativo", "comando_interno"):
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx, total_acciones)
    elif tipo == "script":
        ubicacion = None
        ruta_relativa = info.get("ruta_script", "")
        if ruta_relativa.startswith("core/"):
            ubicacion = "core"
        elif ruta_relativa.startswith("skills/"):
            ubicacion = "skills"

        if ubicacion == "core" and not perfil.get("permite_ejecutar_core", False):
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Script de core/ no permitido en perfil {perfil_activo}", total_acciones)
            return False
        if ubicacion == "skills" and not perfil.get("permite_ejecutar_skills", False):
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", f"Script de skills/ no permitido en perfil {perfil_activo}", total_acciones)
            return False

        return ejecutar_script_desde_catalogo(comando, accion, transaccion_id, accion_idx, info, total_acciones)
    else:
        msg = f"Tipo de comando desconocido: {tipo}"
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
        return False


def ejecutar_script_desde_catalogo(comando, accion, transaccion_id, accion_idx, info, total_acciones):
    try:
        ruta_relativa = info.get("ruta_script")
        if not ruta_relativa:
            msg = f"Script '{comando}' no tiene ruta_script definida"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
            return False

        ruta_script = (SCRIPT_DIR / ruta_relativa).resolve()
        try:
            ruta_script.relative_to(SCRIPT_DIR.resolve())
        except ValueError:
            msg = f"Script fuera de SCRIPT_DIR: {ruta_relativa}"
            escribir_log(f"SEGURIDAD: {msg}")
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
            return False

        if not ruta_script.exists():
            msg = f"Script no encontrado: {ruta_script}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
            return False

        timeout_final = obtener_timeout(accion, info)

        args = []
        for key, value in accion.items():
            if key in ["comando", "transaccion_id", "timeout"]:
                continue
            if isinstance(value, bool):
                if value:
                    args.append(f"--{key}")
            else:
                args.append(f"--{key}")
                args.append(str(value))

        env = os.environ.copy()
        env["WAIO_WORKDIR"] = str(WORK_DIR)

        resultado = subprocess.run(
            [sys.executable, str(ruta_script)] + args,
            capture_output=True,
            text=True,
            timeout=timeout_final,
            env=env
        )
        if resultado.returncode == 0:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", resultado.stdout, total_acciones)
        else:
            salida_error = resultado.stderr if resultado.stderr.strip() else resultado.stdout
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", salida_error, total_acciones)
        return True
    except subprocess.TimeoutExpired:
        msg = f"Timeout: {timeout_final} segundos | Comando: {comando} | Accion: {accion_idx}"
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg, total_acciones)
        return False
    except Exception as e:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e), total_acciones)
        return False


# ----------------------------------------------------------------------
# Comandos nativos
# ----------------------------------------------------------------------

def ejecutar_nativo(comando, accion, transaccion_id, accion_idx, total_acciones):
    def guardar(status, output):
        guardar_resultado_json(transaccion_id, accion_idx, comando, status, output, total_acciones)

    perfil = obtener_perfil()
    limite_escritura = perfil.get("limite_escritura_bytes", None)
    limite_lectura = perfil.get("limite_lectura_chars", 0)

    if comando == "crear_archivo":
        ruta_str = accion.get("ruta")
        contenido = accion.get("contenido", "")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        tamano = len(contenido.encode("utf-8"))
        if limite_escritura is not None:
            if limite_escritura == 0:
                guardar("error", "Perfil sin permisos de escritura")
                return False
            if tamano > limite_escritura:
                guardar("error", f"Limite de escritura excedido ({formatear_limite(limite_escritura)})")
                return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "w", encoding="utf-8") as f:
                f.write(contenido)
            msg = f"Archivo creado: {ruta.name}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "append_archivo":
        ruta_str = accion.get("ruta")
        contenido = accion.get("contenido", "")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            tamano_actual = ruta.stat().st_size if ruta.exists() else 0
            nuevo_tamano = tamano_actual + len(contenido.encode("utf-8"))
            if limite_escritura is not None:
                if limite_escritura == 0:
                    guardar("error", "Perfil sin permisos de escritura")
                    return False
                if nuevo_tamano > limite_escritura:
                    guardar("error", f"Limite de escritura excedido ({formatear_limite(limite_escritura)})")
                    return False
            ruta.parent.mkdir(parents=True, exist_ok=True)
            with open(ruta, "a", encoding="utf-8") as f:
                f.write(contenido)
            msg = f"Contenido agregado a: {ruta.name}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "crear_carpeta":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            ruta.mkdir(parents=True, exist_ok=True)
            msg = f"Carpeta creada: {ruta.name}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "eliminar_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Archivo no existe: {ruta_str}")
                return False
            if not ruta.is_file():
                guardar("error", f"No es un archivo: {ruta_str}")
                return False
            ok, msg = eliminar_seguro(ruta)
            guardar("ok" if ok else "error", msg)
            return ok
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "eliminar_carpeta":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Carpeta no existe: {ruta_str}")
                return False
            if not ruta.is_dir():
                guardar("error", f"No es una carpeta: {ruta_str}")
                return False
            ok, msg = eliminar_seguro(ruta)
            guardar("ok" if ok else "error", msg)
            return ok
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "mover_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        if not origen_str or not destino_str:
            guardar("error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                guardar("error", f"Origen no existe: {origen_str}")
                return False
            if limite_escritura is not None and origen.is_file():
                if limite_escritura == 0:
                    guardar("error", "Perfil sin permisos de escritura")
                    return False
                if origen.stat().st_size > limite_escritura:
                    guardar("error", f"Limite de escritura excedido ({formatear_limite(limite_escritura)})")
                    return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(origen), str(destino))
            msg = f"Movido: {origen.name} -> {destino.name}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "renombrar_archivo":
        ruta_str = accion.get("ruta")
        nombre_nuevo = accion.get("nombre_nuevo")
        if not ruta_str or not nombre_nuevo:
            guardar("error", "Falta 'ruta' o 'nombre_nuevo'")
            return False
        if not isinstance(nombre_nuevo, str) or "/" in nombre_nuevo or "\\" in nombre_nuevo or nombre_nuevo in (".", "..") or ".." in nombre_nuevo or ":" in nombre_nuevo:
            guardar("error", f"'nombre_nuevo' debe ser un nombre simple, sin rutas ni ':': {nombre_nuevo}")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"No existe: {ruta_str}")
                return False
            destino = ruta.parent / nombre_nuevo
            shutil.move(str(ruta), str(destino))
            msg = f"Renombrado: {ruta.name} -> {nombre_nuevo}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "copiar_archivo":
        origen_str = accion.get("origen")
        destino_str = accion.get("destino")
        if not origen_str or not destino_str:
            guardar("error", "Falta 'origen' o 'destino'")
            return False
        origen = ruta_segura(origen_str)
        destino = ruta_segura(destino_str)
        if not origen or not destino:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not origen.exists():
                guardar("error", f"Origen no existe: {origen_str}")
                return False
            if not origen.is_file():
                guardar("error", f"Origen no es archivo: {origen_str}")
                return False
            if limite_escritura is not None:
                if limite_escritura == 0:
                    guardar("error", "Perfil sin permisos de escritura")
                    return False
                if origen.stat().st_size > limite_escritura:
                    guardar("error", f"Limite de escritura excedido ({formatear_limite(limite_escritura)})")
                    return False
            destino.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(origen), str(destino))
            msg = f"Copiado: {origen.name} -> {destino.name}"
            escribir_log(msg)
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "listar_directorio":
        ruta_str = accion.get("ruta", ".")
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Directorio no existe: {ruta_str}")
                return False
            items = [item.name for item in ruta.iterdir()]
            lista = ", ".join(items) if items else "vacio"
            escribir_log(f"Listado {ruta_str}: {lista}")
            guardar("ok", lista)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "buscar_archivos":
        ruta_str = accion.get("ruta", ".")
        patron = accion.get("patron", "*")
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Directorio no existe: {ruta_str}")
                return False
            resultados = list(ruta.glob(patron))
            lista = ", ".join([f.name for f in resultados]) if resultados else "vacio"
            escribir_log(f"Busqueda {patron} en {ruta_str}: {lista}")
            guardar("ok", lista)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "leer_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta' en leer_archivo")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Archivo no existe: {ruta_str}")
                return False
            with open(ruta, "r", encoding="utf-8") as f:
                contenido = f.read()

            read_default = config_get("read_default_chars", 500000)
            read_max = config_get("read_absolute_max_chars", 10000000)

            limite_solicitado = accion.get("limite", read_default)
            if limite_solicitado == 0:
                limite_a_usar = read_max
            else:
                limite_a_usar = min(limite_solicitado, read_max)

            if limite_lectura:
                limite_a_usar = min(limite_a_usar, limite_lectura)

            original_len = len(contenido)
            if original_len > limite_a_usar:
                contenido = contenido[:limite_a_usar]
                contenido += f"\n... (truncado a {limite_a_usar} caracteres. Original: {original_len})"
            guardar("ok", contenido)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "leer_lineas":
        ruta_str = accion.get("ruta")
        inicio = accion.get("inicio", 1)
        fin = accion.get("fin", None)
        if not ruta_str:
            guardar("error", "Falta 'ruta' en leer_lineas")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Archivo no existe: {ruta_str}")
                return False
            with open(ruta, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            total = len(lineas)
            if fin is None or fin > total:
                fin = total
            if inicio < 1:
                inicio = 1
            if inicio > total:
                guardar("error", f"Linea de inicio {inicio} excede total {total}")
                return False
            seleccion = lineas[inicio-1:fin]
            resultado = "".join(seleccion)
            msg = f"Lineas {inicio}-{fin} de {total}:\n{resultado}"
            guardar("ok", msg)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "contar_lineas":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta' en contar_lineas")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"Archivo no existe: {ruta_str}")
                return False
            with open(ruta, "r", encoding="utf-8") as f:
                lineas = f.readlines()
            total = len(lineas)
            guardar("ok", f"{total} lineas")
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "existe_archivo":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        existe = ruta.exists()
        guardar("ok", str(existe))
        return existe

    elif comando == "obtener_tamano":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"No existe: {ruta_str}")
                return False
            if ruta.is_file():
                tamano = ruta.stat().st_size
                guardar("ok", f"{tamano} bytes")
            else:
                tamano = sum(f.stat().st_size for f in ruta.rglob('*') if f.is_file())
                guardar("ok", f"{tamano} bytes (carpeta)")
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "fecha_modificacion":
        ruta_str = accion.get("ruta")
        if not ruta_str:
            guardar("error", "Falta 'ruta'")
            return False
        ruta = ruta_segura(ruta_str)
        if not ruta:
            guardar("error", "Ruta insegura")
            return False
        try:
            if not ruta.exists():
                guardar("error", f"No existe: {ruta_str}")
                return False
            timestamp = ruta.stat().st_mtime
            fecha = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
            guardar("ok", fecha)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando == "mensaje":
        contenido = accion.get("contenido", "")
        if not contenido:
            guardar("error", "Falta 'contenido'")
            return False
        guardar("ok", contenido)
        return True

    elif comando == "ejecutar_comando":
        if not perfil.get("permite_consola", False):
            guardar("error", f"Consola no permitida en perfil {perfil_activo}")
            return False
        tokens = accion.get("parametros", [])
        if not isinstance(tokens, list) or not tokens:
            guardar("error", "Falta 'parametros' (array de tokens)")
            return False
        tokens = [str(t) for t in tokens]
        timeout = accion.get("timeout", CONSOLA_TIMEOUT_DEFAULT)
        try:
            timeout = int(timeout)
            if timeout <= 0:
                timeout = CONSOLA_TIMEOUT_DEFAULT
            if timeout > CONSOLA_TIMEOUT_MAX:
                timeout = CONSOLA_TIMEOUT_MAX
        except (ValueError, TypeError):
            timeout = CONSOLA_TIMEOUT_DEFAULT
        seguro, mensaje = consola_comando_seguro(tokens)
        if not seguro:
            guardar("error", mensaje)
            return False
        try:
            resultado = subprocess.run(
                tokens, shell=False, capture_output=True, text=True, timeout=timeout
            )
            salida = ""
            if resultado.stdout:
                salida += resultado.stdout
            if resultado.stderr:
                salida += f"\n[STDERR] {resultado.stderr}"
            if resultado.returncode != 0:
                salida += f"\n[CODIGO] {resultado.returncode}"
            guardar("ok" if resultado.returncode == 0 else "error", salida)
            return True
        except subprocess.TimeoutExpired:
            guardar("error", f"Timeout ({timeout}s) - Comando: {' '.join(tokens)}")
            return False
        except FileNotFoundError:
            guardar("error", f"Binario no encontrado: {tokens[0]}")
            return False
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando in ("skills", "listar_skills", "list_skills", "info"):
        nombre = accion.get("nombre")
        if nombre:
            ruta_json = None
            for carpeta in [SKILLS_DIR, CORE_DIR]:
                posible = carpeta / nombre / f"{nombre}.json"
                if posible.exists():
                    ruta_json = posible
                    break
            if not ruta_json:
                guardar("error", f"JSON de skill no encontrado: {nombre}")
                return False
            try:
                with open(ruta_json, "r", encoding="utf-8") as f:
                    info_skill = json.load(f)
                guardar("ok", json.dumps(info_skill, indent=2, ensure_ascii=False))
                return True
            except Exception as e:
                guardar("error", str(e))
                return False
        else:
            base = [
                "listar_directorio", "leer_archivo", "crear_archivo", "crear_carpeta",
                "mover_archivo", "copiar_archivo", "renombrar_archivo", "eliminar_archivo",
                "eliminar_carpeta", "existe_archivo", "obtener_tamano", "fecha_modificacion",
                "contar_lineas", "buscar_archivos", "leer_lineas", "append_archivo",
                "mensaje", "skills", "ayuda", "indexar", "ejecutar"
            ]
            resultado = "COMANDOS BASE (siempre disponibles):\n"
            for cmd in base:
                resultado += f"  - {cmd}\n"

            habilidades = cargar_habilidades()
            if habilidades.get("_total_skills", 0) > 0:
                skills = habilidades.get("skills", {})
                resultado += "\nSKILLS DISPONIBLES:\n"
                disponibles = []
                perfiles_orden = ["readonly", "standard", "advanced", "debug"]
                for cmd, info_skill in skills.items():
                    if cmd in ["skills"]:
                        continue
                    if not info_skill.get("ejecutable", True):
                        continue
                    perfil_req = info_skill.get("perfil_minimo", "readonly")
                    if perfil_req not in perfiles_orden:
                        continue
                    if perfiles_orden.index(perfil_activo) >= perfiles_orden.index(perfil_req):
                        disponibles.append(f"  - {cmd}: {info_skill.get('descripcion', 'Sin descripcion')}")
                if disponibles:
                    resultado += "\n".join(disponibles)
                else:
                    resultado += "  (No hay skills disponibles para tu perfil)"
            else:
                resultado += "\nSKILLS DISPONIBLES:\n  (No hay skills. Ejecuta 'indexar' para generar el catalogo.)"
            guardar("ok", resultado)
            return True

    elif comando in ("ayuda", "help", "?"):
        mensaje = """WAIO 3.3 - AYUDA RAPIDA

COMANDOS BASE:
  listar_directorio, leer_archivo, crear_archivo, crear_carpeta,
  mover_archivo, copiar_archivo, renombrar_archivo,
  eliminar_archivo, eliminar_carpeta, existe_archivo,
  obtener_tamano, fecha_modificacion, contar_lineas,
  buscar_archivos, leer_lineas, append_archivo, mensaje,
  ejecutar_comando (solo debug)

COMANDOS ESPECIALES:
  skills            -> Lista skills disponibles
  indexar           -> Regenera el catalogo de skills
  ejecutar          -> Ejecuta un script (segun perfil)
  ayuda             -> Muestra esta ayuda

PERFILES:
  readonly      -> Solo lectura y listado
  standard      -> Lectura, escritura, todo a Papelera
  advanced      -> Todo lo anterior + scripts. Sin consola.
  debug         -> Acceso total, incluida consola

TIMEOUT:
  Cualquier accion puede incluir "timeout" para forzar un tiempo maximo.

EJEMPLO:
  {"comando": "skills"}
  {"comando": "indexar"}
  {"comando": "ejecutar", "script": "hola_mundo.py"}
"""
        guardar("ok", mensaje)
        return True

    elif comando in ("indexar", "index"):
        if not perfil.get("permite_ejecutar_core", False):
            guardar("error", f"Indexar no permitido en perfil {perfil_activo}")
            return False
        try:
            script_path = SCRIPT_DIR / "core" / "indexar" / "indexar.py"
            if not script_path.exists():
                guardar("error", "indexar.py no encontrado")
                return False
            timeout_final = config_get("indexar_timeout_seconds", 120)
            resultado = subprocess.run(
                [sys.executable, str(script_path)],
                capture_output=True, text=True, timeout=timeout_final
            )
            if resultado.returncode == 0:
                guardar("ok", resultado.stdout)
            else:
                guardar("error", resultado.stderr)
            return True
        except Exception as e:
            guardar("error", str(e))
            return False

    elif comando in ("ejecutar", "run"):
        script = accion.get("script")
        if not script:
            guardar("error", "Falta 'script'")
            return False
        args = accion.get("parametros", [])
        if isinstance(args, str):
            args = [args]
        elif not isinstance(args, list):
            args = []

        ruta_script, ubicacion = resolver_script_permitido(script, perfil)
        if not ruta_script:
            guardar("error", f"Script no encontrado o no permitido en perfil {perfil_activo}: {script}")
            return False

        escribir_log(f"Ejecutando {script} desde {ubicacion}: {ruta_script}")

        info_skill = {"nombre": script}
        timeout_final = obtener_timeout(accion, info_skill)
        try:
            env = os.environ.copy()
            env["WAIO_WORKDIR"] = str(WORK_DIR)
            resultado = subprocess.run(
                [sys.executable, str(ruta_script)] + args,
                capture_output=True,
                text=True,
                timeout=timeout_final,
                env=env
            )
            if resultado.returncode == 0:
                guardar("ok", resultado.stdout)
            else:
                guardar("error", resultado.stderr)
            return True
        except subprocess.TimeoutExpired:
            msg = f"Timeout: {timeout_final} segundos | Comando: {comando} | Accion: {accion_idx}"
            guardar("error", msg)
            return False
        except Exception as e:
            guardar("error", str(e))
            return False

    return False


# ----------------------------------------------------------------------
# Mover a rechazados
# ----------------------------------------------------------------------

def mover_a_rechazados(archivo, motivo):
    try:
        RECHAZADOS_DIR.mkdir(parents=True, exist_ok=True)
        destino = RECHAZADOS_DIR / archivo.name
        if destino.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = RECHAZADOS_DIR / f"{archivo.stem}_{ts}.json"
        shutil.move(str(archivo), str(destino))
        error_file = destino.with_suffix(".error.txt")
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"Rechazado: {datetime.now().isoformat()}\n")
            f.write(f"Motivo: {motivo}\n")
        escribir_log(f"[REJECT] {archivo.name} | motivo={motivo}")
    except Exception as e:
        escribir_log(f"Error moviendo a rechazados: {e}")


# ----------------------------------------------------------------------
# Procesamiento de JSON (desde queue/)
# ----------------------------------------------------------------------

def procesar_json(archivo_json):
    global contador_acciones

    try:
        with open(archivo_json, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except Exception as e:
        escribir_log(f"Error leyendo JSON {archivo_json.name}: {e}")
        guardar_resultado_json("error_lectura", 1, "desconocido", "error", f"No se pudo leer: {e}", 1)
        mover_a_rechazados(archivo_json, "json_invalido")
        return

    if not isinstance(datos, dict) or "acciones" not in datos:
        escribir_log(f"JSON invalido - falta 'acciones': {archivo_json.name}")
        guardar_resultado_json("error_formato", 1, "desconocido", "error", "JSON invalido: falta 'acciones'", 1)
        mover_a_rechazados(archivo_json, "json_no_waio")
        return

    transaccion_id = datos.get("transaccion_id", "sin_id")

    if not es_tx_id_valido(transaccion_id):
        escribir_log(f"TX rechazada: transaccion_id invalido: {transaccion_id}")
        guardar_resultado_json("error_tx_id", 0, "sistema", "error",
            f"Transaccion rechazada: transaccion_id invalido (debe ser alfanumerico con _ y -, max 100 chars): {transaccion_id}", 0)
        mover_a_rechazados(archivo_json, "tx_id_invalido")
        return

    acciones = datos.get("acciones", [])

    if not isinstance(acciones, list):
        escribir_log(f"'acciones' no es lista en {archivo_json.name}")
        mover_a_rechazados(archivo_json, "acciones_no_list")
        return

    max_acciones = config_get("max_actions_per_transaction", 100)
    if len(acciones) > max_acciones:
        escribir_log(f"TX rechazada: {len(acciones)} acciones excede el limite {max_acciones}")
        guardar_resultado_json(transaccion_id, 0, "sistema", "error",
            f"Transaccion rechazada: {len(acciones)} acciones, maximo {max_acciones}", 0)
        mover_a_rechazados(archivo_json, "demasiadas_acciones")
        return

    aceptar_dup = config_get("aceptar_id_duplicado", False)
    if not aceptar_dup and es_duplicado(transaccion_id):
        escribir_log(f"TX rechazada: transaccion_id duplicado: {transaccion_id}")
        guardar_resultado_json(transaccion_id, 0, "sistema", "error",
            f"Transaccion rechazada: id duplicado: {transaccion_id}", 0)
        mover_a_rechazados(archivo_json, "id_duplicado")
        return

    if not verificar_limite_transacciones():
        max_tx = config_get("max_transactions_per_minute", 60)
        escribir_log(f"TX rechazada: limite de {max_tx} transacciones por minuto")
        guardar_resultado_json(transaccion_id, 0, "sistema", "error",
            f"Limite de {max_tx} transacciones por minuto excedido", 0)
        mover_a_rechazados(archivo_json, "limite_transacciones")
        return

    contador_acciones = 0

    escribir_log(f"=== INICIO TX: {transaccion_id} ===")
    escribir_log(f"Directorio: {WORK_DIR}")
    total = len(acciones)

    for i, accion in enumerate(acciones):
        if verificar_stop():
            escribir_log("Detenido por kill switch")
            return
        comando = accion.get("comando", "?")
        escribir_log(f"Accion {i+1}/{total}: {comando}")
        try:
            ejecutar_comando(accion, transaccion_id, i+1, total)
        except Exception as e:
            escribir_log(f"Error en accion {i+1}: {e}")
            guardar_resultado_json(transaccion_id, i+1, comando, "error", str(e), total)

    escribir_log(f"=== FIN TX: {transaccion_id} ===")

    agregar_al_indice(transaccion_id)
    mover_a_jsonout(archivo_json)


def mover_a_jsonout(archivo):
    try:
        limpiar_jsonout_viejos()
        JSONOUT_DIR.mkdir(parents=True, exist_ok=True)
        destino = JSONOUT_DIR / archivo.name
        if destino.exists():
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            destino = JSONOUT_DIR / f"{archivo.stem}_{ts}.json"
        shutil.move(str(archivo), str(destino))
        escribir_log(f"[DONE] {archivo.name} -> jsonout/")
    except Exception as e:
        escribir_log(f"Error moviendo a jsonout: {e}")


def obtener_json_mas_viejo(directorio):
    try:
        archivos = []
        with os.scandir(directorio) as it:
            for entry in it:
                if entry.name.endswith('.json') and entry.is_file():
                    archivos.append((entry.path, entry.stat().st_mtime))
        if not archivos:
            return None
        mas_viejo = min(archivos, key=lambda x: x[1])
        return Path(mas_viejo[0])
    except Exception as e:
        escribir_log(f"Error escaneando {directorio}: {e}")
        return None


# ----------------------------------------------------------------------
# Clasificacion Forma A / B
# ----------------------------------------------------------------------

def es_de_waio(data):
    if not isinstance(data, dict):
        return None
    tx_id = data.get("transaccion_id")
    acciones = data.get("acciones")
    if isinstance(tx_id, str) and tx_id.strip() and isinstance(acciones, list):
        return "A"
    comando = data.get("comando")
    if isinstance(comando, str) and comando.strip():
        return "B"
    return None


# ----------------------------------------------------------------------
# Watcher: escanea Downloads, mueve a queue/
# ----------------------------------------------------------------------

def obtener_json_pendientes(directorio, ignorados):
    try:
        archivos = []
        with os.scandir(directorio) as it:
            for entry in it:
                if not entry.name.endswith('.json'):
                    continue
                if not entry.is_file():
                    continue
                try:
                    mtime = entry.stat().st_mtime
                except Exception:
                    continue
                if ignorados.get(entry.name) == mtime:
                    continue
                archivos.append((Path(entry.path), mtime))
        archivos.sort(key=lambda x: x[1])
        return [p for p, _ in archivos]
    except Exception as e:
        escribir_log(f"Error escaneando {directorio}: {e}")
        return []


def watcher_downloads():
    escribir_log("Watcher iniciado")
    directorio_escucha = obtener_directorio_escucha()
    errores_consecutivos = 0
    ignorados = {}

    while not verificar_stop():
        try:
            scan_interval = config_get("downloads_scan_interval", 2.0)
            stabilize_wait = config_get("downloads_stabilize_wait", 0.3)
            leer_json = config_get("leer_json_en_downloads", True)
            ignorados_max = config_get("ignorados_max_items", 1000)

            pendientes = obtener_json_pendientes(directorio_escucha, ignorados)

            for json_archivo in pendientes:
                if verificar_stop():
                    break
                try:
                    mtime = json_archivo.stat().st_mtime
                except Exception:
                    continue

                time.sleep(stabilize_wait)

                if leer_json:
                    try:
                        with open(json_archivo, "r", encoding="utf-8") as f:
                            datos = json.load(f)
                    except Exception as e:
                        escribir_log(f"[IGNORE] {json_archivo.name} | no parsea JSON: {e}")
                        ignorados[json_archivo.name] = mtime
                        if len(ignorados) > ignorados_max:
                            ignorados.pop(next(iter(ignorados)))
                        continue

                    forma = es_de_waio(datos)
                    if forma is None:
                        escribir_log(f"[IGNORE] {json_archivo.name} | no es de WAIO")
                        ignorados[json_archivo.name] = mtime
                        if len(ignorados) > ignorados_max:
                            ignorados.pop(next(iter(ignorados)))
                        continue
                    tx_id = datos.get("transaccion_id") or "tx_auto"
                    escribir_log(f"[IN] {json_archivo.name} | Forma {forma} | tx={tx_id}")

                QUEUE_DIR.mkdir(parents=True, exist_ok=True)
                destino = QUEUE_DIR / json_archivo.name
                if destino.exists():
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    destino = QUEUE_DIR / f"{json_archivo.stem}_{ts}.json"
                try:
                    shutil.move(str(json_archivo), str(destino))
                    escribir_log(f"[QUEUE] {json_archivo.name}")
                    ignorados.pop(json_archivo.name, None)
                except Exception as e:
                    escribir_log(f"Error moviendo {json_archivo.name} a queue/: {e}")

            errores_consecutivos = 0
            time.sleep(scan_interval)

        except Exception as e:
            errores_consecutivos += 1
            escribir_log(f"Error en watcher ({errores_consecutivos}): {e}")
            backoff = config_get("error_backoff_seconds", 2.0)
            time.sleep(backoff)

    escribir_log("Watcher detenido")


# ----------------------------------------------------------------------
# Procesador: consume queue/
# ----------------------------------------------------------------------

def procesador_cola():
    escribir_log("Procesador iniciado")

    while not verificar_stop():
        try:
            PROCESSING_DIR.mkdir(parents=True, exist_ok=True)

            json_pendiente = obtener_json_mas_viejo(QUEUE_DIR) if QUEUE_DIR.exists() else None
            if not json_pendiente:
                time.sleep(1)
                continue

            destino = PROCESSING_DIR / json_pendiente.name
            if destino.exists():
                ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                destino = PROCESSING_DIR / f"{json_pendiente.stem}_{ts}.json"
            shutil.move(str(json_pendiente), str(destino))
            escribir_log(f"[PROCESSING] {destino.name}")

            procesar_json(destino)

            time.sleep(0.1)
        except Exception as e:
            escribir_log(f"Error en procesador: {e}")
            time.sleep(1)

    escribir_log("Procesador detenido")


# ----------------------------------------------------------------------
# Lanzar visor
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


def lanzar_visor():
    try:
        visor_path = SCRIPT_DIR / 'waio_visor.py'
        if not visor_path.exists():
            escribir_log(f"Visor no encontrado: {visor_path}")
            return
        result = subprocess.run(
            ['tasklist', '/FI', 'IMAGENAME eq pythonw.exe'],
            capture_output=True, text=True,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        if 'pythonw.exe' not in result.stdout:
            subprocess.Popen(
                ['pythonw', str(visor_path)],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            escribir_log("Visor iniciado")
        else:
            escribir_log("Visor ya corriendo")
    except Exception as e:
        escribir_log(f"Error lanzando visor: {e}")


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    try:
        limpiar_stop_signal()

        if LOCK_FILE.exists():
            try:
                with open(LOCK_FILE, "r") as f:
                    pid_viejo = int(f.read().strip())
                escribir_log(f"Lock previo con PID {pid_viejo}. Intentando taskkill /F /T.")
                subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid_viejo)], capture_output=True)
                escribir_log(f"Taskkill ejecutado para PID {pid_viejo}")
                LOCK_FILE.unlink()
            except Exception as e:
                escribir_log(f"Error cerrando instancia anterior: {e}")
                try:
                    LOCK_FILE.unlink()
                except Exception:
                    pass

        LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(LOCK_FILE, "w") as f:
            f.write(str(os.getpid()))
        escribir_log(f"Lock creado. PID: {os.getpid()}")

        WORKDIR_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(WORKDIR_FILE, "w") as f:
            f.write(str(WORK_DIR))

        QUEUE_DIR.mkdir(parents=True, exist_ok=True)
        PROCESSING_DIR.mkdir(parents=True, exist_ok=True)
        RECHAZADOS_DIR.mkdir(parents=True, exist_ok=True)

        recuperar_processing()

        crear_archivos_si_faltan()
        escribir_log("Verificando catalogo de skills...")

        if not SKILLS_FILE.exists():
            escribir_log("skills.json no existe. Indexando...")
            try:
                indexer = SCRIPT_DIR / "core" / "indexar" / "indexar.py"
                if indexer.exists():
                    resultado = subprocess.run(
                        [sys.executable, str(indexer)],
                        capture_output=True, text=True, timeout=60
                    )
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
        construir_mapeo_comandos()
        cargar_indice_duplicados()

        lanzar_visor()

        escribir_log("Esperando a que escucha_output arranque...")
        _lock_escucha = SCRIPT_DIR / "escucha.lock"
        _espera_max = 10.0
        _espera = 0.0
        while _espera < _espera_max:
            if _lock_escucha.exists():
                escribir_log(f"escucha_output arranco en {_espera:.1f}s")
                break
            time.sleep(0.5)
            _espera += 0.5
        if _espera >= _espera_max:
            escribir_log("WARNING: escucha_output no arranco en 10s. Creando prompt igual.")
        time.sleep(1)
        cargar_y_procesar_prompt()

        directorio_escucha = obtener_directorio_escucha()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        JSONOUT_DIR.mkdir(parents=True, exist_ok=True)

        escribir_log("=" * 50)
        escribir_log(f"WAIO_ESCUCHA_{VERSION}_INICIADO")
        escribir_log(f"Log: {LOG_FILE}")
        escribir_log(f"Script: {SCRIPT_DIR}")
        escribir_log(f"Work dir: {WORK_DIR}")
        escribir_log(f"Escuchando: {directorio_escucha}")
        escribir_log(f"Perfil activo: {perfil_activo}")
        escribir_log(f"leer_json_en_downloads: {config_get('leer_json_en_downloads', True)}")
        escribir_log(f"aceptar_id_duplicado: {config_get('aceptar_id_duplicado', False)}")
        escribir_log(f"Scan interval: {config_get('downloads_scan_interval', 2.0)}s")
        escribir_log("=" * 50)

        hilo_watcher = threading.Thread(target=watcher_downloads, daemon=True, name="watcher")
        hilo_procesador = threading.Thread(target=procesador_cola, daemon=True, name="procesador")
        hilo_watcher.start()
        hilo_procesador.start()
        escribir_log("Hilos watcher y procesador iniciados")

        while True:
            time.sleep(1)
            if verificar_stop():
                escribir_log("STOP detectado en main")
                break

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
            except Exception:
                pass
        time.sleep(5)


if __name__ == "__main__":
    main()