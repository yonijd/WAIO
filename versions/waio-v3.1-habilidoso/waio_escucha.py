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

# ================= CONFIGURACION =================
VERSION = "3.1"
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

MAX_READ_DEFAULT = 500000
ABSOLUTE_MAX_READ = 10000000
TIMESTAMP_LOG = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"waio_escucha_{TIMESTAMP_LOG}.log"
STOP_FILE = SCRIPT_DIR / "STOP.trigger"
PROMPT_FILE = SCRIPT_DIR / "prompt.txt"

# Archivos de configuracion
CONFIG_FILE = SCRIPT_DIR / "waio_config.json"
HABILIDADES_FILE = SCRIPT_DIR / "habilidades" / "habilidades.json"
WISPOUT_FILE = SCRIPT_DIR / "wispout.json"
PYSEGURAS_DIR = SCRIPT_DIR / "pyseguras"
PYHABILIDADES_DIR = SCRIPT_DIR / "pyhabilidades"

# Variables globales para configuracion
perfil_activo = "estandar"
config_cache = None
habilidades_cache = None
wispout_cache = None
contador_acciones = 0

# Comandos internos que NO dependen de habilidades.json
COMANDOS_INTERNOS = [
    "listar_habilidades",
    "mensaje",
    "ejecutar_script",
    "indexar_habilidades"
]

# Comandos base (siempre disponibles, no dependen de habilidades.json)
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
    "mtime": "fecha_modificacion",
    "mensaje": "mensaje",
    "message": "mensaje",
    "decir": "mensaje",
    "append": "append_archivo",
    "append_archivo": "append_archivo",
    "renombrar": "renombrar_archivo",
    "renombrar_archivo": "renombrar_archivo",
    "contar_lineas": "contar_lineas",
    "buscar_archivos": "buscar_archivos",
    "leer_lineas": "leer_lineas",
    "ejecutar_script": "ejecutar_script",
    "listar_habilidades": "listar_habilidades",
    "list_skills": "listar_habilidades",
    "indexar_habilidades": "indexar_habilidades"
}

# ================= PROMPT POR DEFECTO =================

PROMPT_DEFAULT = """PROMPT MAESTRO: WAIO 3.1

Actua como agente de sistema para mi motor local WAIO (Web AI Orchestrator).

COMO FUNCIONA:
1. Tu generas un archivo JSON en mi carpeta Downloads
2. WAIO lo detecta y ejecuta las acciones
3. Los resultados se compilan automaticamente por escucha_output
4. Recibiras un bloque con formato: [N] TX: xxx | Accion X | Comando: xxx
5. Cada respuesta es una confirmacion. Espera la confirmacion antes de continuar.

PERFIL ACTIVO:
WAIO te mostrara el perfil activo en cada respuesta (ej: WAIO 3.1 | estandar | 1MB | papelera).
Esto define lo que puedes hacer:
- solo_lectura: Solo puedes leer y listar. Nada de escribir o borrar.
- estandar: Puedes leer, listar, buscar archivos, crear, mover, copiar y renombrar. Todo va a Papelera.
- avanzado: Todo lo anterior + eliminar archivos, eliminar carpetas y ejecutar scripts de pyseguras/.
- sin_restricciones: Todo permitido. Borrado permanente. Solo rescate.

COMANDOS DISPONIBLES:
Usa el comando listar_habilidades para ver que comandos tienes disponibles segun tu perfil.
No uses comandos que no aparezcan en la lista.
Si listar_habilidades falla o no muestra comandos, ejecuta indexar_habilidades para regenerar el catalogo.
Si indexar_habilidades falla, informa el error al usuario y sugiere revisar la carpeta .waio/habilidades/

PARAMETROS POR COMANDO (usar exactamente estos nombres):

SOLO LECTURA:
- listar_directorio: {"ruta": "carpeta"} (opcional, default: ".")
- leer_archivo: {"ruta": "archivo", "limite": 500000} (opcional, 0=completo)
- existe_archivo: {"ruta": "archivo"}
- obtener_tamano: {"ruta": "archivo"}
- fecha_modificacion: {"ruta": "archivo"}
- contar_lineas: {"ruta": "archivo"}
- leer_lineas: {"ruta": "archivo", "inicio": 1, "fin": 10} (inicio y fin opcionales)
- mensaje: {"contenido": "texto"}
- listar_habilidades: {} (sin parametros)
- buscar_archivos: {"ruta": "carpeta", "patron": "*.txt"} (patron obligatorio)

ESCRITURA (estandar):
- crear_archivo: {"ruta": "archivo", "contenido": "texto"}
- crear_carpeta: {"ruta": "carpeta"}
- mover_archivo: {"origen": "ruta", "destino": "ruta"}
- renombrar_archivo: {"ruta": "archivo", "nombre_nuevo": "nuevo_nombre"}
- copiar_archivo: {"origen": "ruta", "destino": "ruta"}
- append_archivo: {"ruta": "archivo", "contenido": "texto"}

AVANZADO:
- eliminar_archivo: {"ruta": "archivo"}
- eliminar_carpeta: {"ruta": "carpeta"}
- ejecutar_script: {"script": "nombre.py", "parametros": ["arg1", "arg2"]} (parametros opcional)

LIMITES Y RESTRICCIONES:
- Maximo acciones por transaccion: 10
- Maximo tamaño JSON: 2MB
- Timeout por accion: 30 segundos
- Limite lectura por defecto: 500,000 caracteres
- Limite lectura maximo: 10,000,000 caracteres (usar "limite": 0)
- Archivos >10MB: se truncan a 10,000,000 caracteres y se agrega mensaje: "... (truncado a 10000000 caracteres. Original: X)"
- Si excedes el limite de escritura: recibiras error
- Si una accion falla en una transaccion, las siguientes acciones igual se ejecutan. No hay rollback.

MANEJO DE ERRORES (respuestas reales de WAIO):

Error 001: Archivo no existe
Ejemplo:
Comando: leer_archivo | error
Archivo no existe: archivo.txt
Solucion: Verifica que la ruta sea correcta y el archivo exista.

Error 002: Ruta insegura (navegacion a padre)
Ejemplo:
Comando: leer_archivo | error
Navegacion a directorio padre no permitida en este perfil
Solucion: Usa rutas relativas dentro del proyecto. No uses "..".

Error 003: Comando no disponible en el perfil
Ejemplo:
Comando: eliminar_archivo | error
(El error especifico depende del comando y perfil)
Solucion: Usa listar_habilidades para ver que comandos estan disponibles en tu perfil.

Error 004: JSON invalido
Ejemplo:
Error leyendo JSON
JSON invalido - falta 'acciones'
Solucion: Revisa que el JSON este bien formado y tenga "transaccion_id" y "acciones".

Error 005: Comando inexistente
Ejemplo:
Comando: comando_inexistente | error
Comando no existe en habilidades.json: comando_inexistente
Solucion: Usa listar_habilidades para ver los comandos validos.

Error 006: Script sin permisos (en estandar)
Ejemplo:
Comando: ejecutar_script | error
Scripts no permitidos en perfil actual
Solucion: Cambia a perfil avanzado para ejecutar scripts.

Error 007: Timeout (accion tardo mas de 30 segundos)
Ejemplo:
Comando: ejecutar_script | error
Timeout: script excedio 60 segundos
Solucion: Optimiza el script o dividilo en partes mas pequeñas.

RECUPERACION Y LOGS:
- Papelera: los archivos eliminados van a la Papelera de Reciclaje de Windows. Para restaurar, abri la Papelera y selecciona "Restaurar". WAIO no tiene comando para restaurar desde la papelera.
- Logs: .waio/logs/ (historial de todas las acciones)

EJEMPLOS COMPLETOS:

EJEMPLO 1: Lectura y exploracion
{
  "transaccion_id": "tx_001",
  "acciones": [
    { "comando": "listar_directorio", "ruta": "." },
    { "comando": "leer_archivo", "ruta": "config.json", "limite": 0 }
  ]
}

EJEMPLO 2: Creacion de estructura
{
  "transaccion_id": "tx_002",
  "acciones": [
    { "comando": "crear_carpeta", "ruta": "proyecto" },
    { "comando": "crear_archivo", "ruta": "proyecto/README.md", "contenido": "# Proyecto" },
    { "comando": "crear_archivo", "ruta": "proyecto/data/ejemplo.txt", "contenido": "texto de prueba" }
  ]
}

EJEMPLO 3: Gestion de archivos
{
  "transaccion_id": "tx_003",
  "acciones": [
    { "comando": "copiar_archivo", "origen": "proyecto/README.md", "destino": "proyecto/README_backup.md" },
    { "comando": "mover_archivo", "origen": "proyecto/data/ejemplo.txt", "destino": "proyecto/ejemplo.txt" },
    { "comando": "append_archivo", "ruta": "proyecto/ejemplo.txt", "contenido": "\nLinea agregada" }
  ]
}

REGLAS ESTRICTAS:
- El JSON debe ser 100% valido
- No uses funciones, expresiones ni operadores
- Ejemplo valido: {"contenido": "texto plano"}
- Ejemplo invalido: {"contenido": "texto" * 500}
- Usa strings literales, no instrucciones de repeticion
- Usa los nombres de parametros exactos (origen/destino, no ruta_origen)
- Espera la confirmacion de WAIO antes de continuar con la siguiente accion

INSTRUCCION FINAL:
1. Primero, ejecuta listar_directorio y listar_habilidades para ver los comandos disponibles segun tu perfil.
2. Usa los comandos que aparecen en la lista.
3. Genera el JSON en un bloque de codigo limpio.
4. Para archivos grandes, usa "limite": 0 para leer el contenido completo (maximo 10MB).
5. Si una accion falla, revisa el error y corrige el JSON antes de reintentar."""

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

# ================= INDEXADOR DE HABILIDADES (interno) =================

def indexar_habilidades():
    """Indexa las habilidades desde .waio/habilidades/ y genera habilidades.json"""
    resultados = []
    errores = []
    
    RUTA_HABILIDADES = SCRIPT_DIR / "habilidades"
    RUTA_PYHABILIDADES = SCRIPT_DIR / "pyhabilidades"
    RUTA_JSON_MAESTRO = RUTA_HABILIDADES / "habilidades.json"
    
    CAMPOS_OBLIGATORIOS = [
        "nombre", "version", "autor", "categoria", "tags",
        "descripcion", "tipo", "parametros", "perfil_minimo"
    ]
    
    TIPOS_VALIDOS = ["comando_interno", "script"]
    PERFILES_VALIDOS = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]
    
    def validar_micro_json(data, carpeta_nombre):
        errores_validacion = []
        for campo in CAMPOS_OBLIGATORIOS:
            if campo not in data:
                errores_validacion.append(f"Falta campo obligatorio: '{campo}'")
        if "tipo" in data and data["tipo"] not in TIPOS_VALIDOS:
            errores_validacion.append(f"Tipo invalido: '{data['tipo']}'. Debe ser: {TIPOS_VALIDOS}")
        if "perfil_minimo" in data and data["perfil_minimo"] not in PERFILES_VALIDOS:
            errores_validacion.append(f"Perfil invalido: '{data['perfil_minimo']}'. Debe ser: {PERFILES_VALIDOS}")
        if data.get("tipo") == "script" and "script" not in data:
            errores_validacion.append("Falta 'script' para habilidad de tipo 'script'")
        if "nombre" in data and data["nombre"] != carpeta_nombre:
            errores_validacion.append(f"El nombre '{data['nombre']}' no coincide con la carpeta '{carpeta_nombre}'")
        return errores_validacion
    
    if not RUTA_HABILIDADES.exists():
        return {"error": f"No existe la carpeta: {RUTA_HABILIDADES}"}
    
    for carpeta in RUTA_HABILIDADES.iterdir():
        if not carpeta.is_dir():
            continue
        
        nombre_carpeta = carpeta.name
        json_path = carpeta / f"{nombre_carpeta}.json"
        
        if not json_path.exists():
            continue
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            errores.append(f"Error al leer JSON de {nombre_carpeta}: {str(e)}")
            continue
        
        errores_validacion = validar_micro_json(data, nombre_carpeta)
        if errores_validacion:
            for err in errores_validacion:
                errores.append(f"{nombre_carpeta}: {err}")
            continue
        
        if data.get("tipo") == "script":
            script_name = data.get("script", f"{nombre_carpeta}.py")
            data["ruta_script"] = f"{nombre_carpeta}/{script_name}"
        
        if data.get("tipo") == "script":
            script_origen = carpeta / data.get("script", f"{nombre_carpeta}.py")
            if script_origen.exists():
                RUTA_PYHABILIDADES.mkdir(parents=True, exist_ok=True)
                script_destino = RUTA_PYHABILIDADES / script_origen.name
                shutil.copy2(script_origen, script_destino)
        
        resultados.append(data)
    
    if resultados:
        categorias = {}
        for h in resultados:
            cat = h.get("categoria", "sin_categoria")
            if cat not in categorias:
                categorias[cat] = []
            categorias[cat].append(h["nombre"])
        
        index_data = {
            "_waio_firma": "WAIO-V4-HABILIDADES-2026",
            "_version": "1.0",
            "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "_total_habilidades": len(resultados),
            "categorias": categorias,
            "habilidades": {h["nombre"]: h for h in resultados}
        }
        
        RUTA_HABILIDADES.mkdir(parents=True, exist_ok=True)
        with open(RUTA_JSON_MAESTRO, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
    
    return {
        "total": len(resultados),
        "errores": errores,
        "habilidades": [h.get("nombre") for h in resultados]
    }

# ================= NUEVAS FUNCIONES V3.1 =================

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
        if HABILIDADES_FILE.exists():
            with open(HABILIDADES_FILE, "r", encoding="utf-8") as f:
                habilidades_cache = json.load(f)
            
            if habilidades_cache.get("_waio_firma") != "WAIO-V4-HABILIDADES-2026":
                escribir_log("ADVERTENCIA: habilidades.json sin firma. Usando defaults.")
                return usar_habilidades_default()
            
            comandos = habilidades_cache.get("habilidades", {})
            escribir_log(f"Habilidades cargadas: {len(comandos)} comandos")
            return habilidades_cache
        else:
            return usar_habilidades_default()
    except Exception as e:
        escribir_log(f"Error cargando habilidades: {e}")
        return usar_habilidades_default()

def usar_habilidades_default():
    return {
        "_waio_firma": "WAIO-V4-HABILIDADES-2026",
        "_version": "1.0",
        "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "_total_habilidades": 0,
        "categorias": {},
        "habilidades": {}
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
        "susurro": {"activo": True, "cada_cuantas_acciones": 3, "mensaje": "INSTRUCCION: Volcado en .waio/memoria/"},
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
                susurro = "\n" + wispout["susurro"].get("mensaje", "INSTRUCCION: Volcado en .waio/memoria/")
        
        return encabezado + cuerpo + recordatorio + susurro
    except Exception as e:
        escribir_log(f"Error formateando respuesta: {e}")
        return f"Comando: {comando} | {status}\n{output}"

def crear_archivos_si_faltan():
    try:
        if not CONFIG_FILE.exists():
            escribir_log("waio_config.json no existe, creando por defecto")
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
            wispout_default = {
                "_waio_firma": "WAIO-V3-WISPOUT-2026",
                "_comentario": "NO EDITAR LA FIRMA. WAIO la usa para validar este archivo.",
                "_version": "1.0",
                "encabezado": {"plantilla": "WAIO {version} | {perfil} | {limite} | {borrado}", "mostrar": True},
                "recordatorio": {"activo": True, "mensaje": "Espera la confirmacion de WAIO antes de continuar."},
                "susurro": {"activo": True, "cada_cuantas_acciones": 3, "mensaje": "INSTRUCCION: Volcado en .waio/memoria/"},
                "respuestas_especiales": {
                    "perfil_cambiado": "Perfil cambiado a {perfil}",
                    "comando_bloqueado": "Comando '{comando}' bloqueado",
                    "error": "Error: {error}"
                }
            }
            with open(WISPOUT_FILE, "w", encoding="utf-8") as f:
                json.dump(wispout_default, f, indent=2, ensure_ascii=False)

        if not HABILIDADES_FILE.exists():
            escribir_log("habilidades.json no existe, creando por defecto")
            habilidades_default = {
                "_waio_firma": "WAIO-V4-HABILIDADES-2026",
                "_version": "1.0",
                "_ultima_actualizacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "_total_habilidades": 0,
                "categorias": {},
                "habilidades": {}
            }
            HABILIDADES_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(HABILIDADES_FILE, "w", encoding="utf-8") as f:
                json.dump(habilidades_default, f, indent=2, ensure_ascii=False)

        PYSEGURAS_DIR.mkdir(parents=True, exist_ok=True)
        PYHABILIDADES_DIR.mkdir(parents=True, exist_ok=True)

    except Exception as e:
        escribir_log(f"Error creando archivos de configuracion: {e}")

# ================= EJECUTOR DE COMANDOS =================

def ejecutar_comando(accion, transaccion_id, accion_idx):
    comando_raw = accion.get("comando", "")
    comando = normalizar_comando(comando_raw)
    
    # Validar perfil
    valido, msg = validar_accion(comando, accion.get("ruta", "") or accion.get("origen", ""))
    if not valido:
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False
    
    # Si es comando interno, ejecutar directamente (NO depende de habilidades.json)
    if comando in COMANDOS_INTERNOS:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    
    # Si es comando base, ejecutar directamente (SIEMPRE disponible)
    if comando in COMANDOS_BASE:
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    
    # Buscar comando en habilidades
    habilidades = cargar_habilidades()
    comandos = habilidades.get("habilidades", {})
    
    if comando not in comandos:
        msg = f"Comando no existe en habilidades.json: {comando}"
        escribir_log(msg)
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False
    
    info = comandos[comando]
    tipo = info.get("tipo", "nativo")
    
    # Verificar perfil minimo requerido
    perfil_requerido = info.get("perfil_minimo", "solo_lectura")
    perfiles_orden = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]
    if perfil_activo in perfiles_orden and perfil_requerido in perfiles_orden:
        if perfiles_orden.index(perfil_activo) < perfiles_orden.index(perfil_requerido):
            msg = f"Comando '{comando}' requiere perfil {perfil_requerido}. Perfil actual: {perfil_activo}"
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            return False
    
    if tipo == "nativo":
        return ejecutar_nativo(comando, accion, transaccion_id, accion_idx)
    elif tipo == "herramienta":
        return ejecutar_herramienta(comando, accion, transaccion_id, accion_idx, info)
    else:
        msg = f"Tipo de comando desconocido: {tipo}"
        guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
        return False

def ejecutar_nativo(comando, accion, transaccion_id, accion_idx):
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

    # ========== ESPECIALES ==========

    elif comando == "mensaje":
        contenido = accion.get("contenido", "")
        if not contenido:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'contenido'")
            return False
        guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", contenido)
        return True

    elif comando == "ejecutar_script":
        script = accion.get("script")
        if not script:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Falta 'script'")
            return False
        
        perfil = obtener_perfil()
        if not perfil.get("permite_scripts", False):
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Scripts no permitidos en perfil actual")
            return False
        
        # Buscar primero en pyhabilidades/
        ruta_script = PYHABILIDADES_DIR / script
        if not ruta_script.exists():
            # Buscar en pyseguras/
            ruta_script = PYSEGURAS_DIR / script
            if not ruta_script.exists():
                msg = f"Script no encontrado en pyhabilidades/ ni pyseguras/: {script}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
                return False
        
        try:
            args = accion.get("parametros", [])
            if isinstance(args, str):
                args = [args]
            elif not isinstance(args, list):
                args = []
            
            resultado = subprocess.run(
                ["python", str(ruta_script)] + args,
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
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", "Timeout: script excedio 60 segundos")
            return False
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "listar_habilidades":
        try:
            habilidades = cargar_habilidades()
            comandos = habilidades.get("habilidades", {})
            
            orden = ["solo_lectura", "estandar", "avanzado", "sin_restricciones"]
            nivel = orden.index(perfil_activo) if perfil_activo in orden else 0
            
            disponibles = []
            
            for cmd, info in comandos.items():
                if cmd == "listar_habilidades":
                    continue
                
                perfil_requerido = info.get("perfil_minimo", "solo_lectura")
                nivel_requerido = orden.index(perfil_requerido) if perfil_requerido in orden else 0
                
                if nivel >= nivel_requerido:
                    desc = info.get("descripcion", "Sin descripcion")
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    disponibles.append(f"- {cmd}: {desc}")
            
            # Agregar comandos base (siempre disponibles)
            for cmd in COMANDOS_BASE:
                desc = "Comando base de WAIO"
                disponibles.append(f"- {cmd}: {desc}")
            
            if not disponibles:
                msg = "No hay comandos disponibles para este perfil"
            else:
                # Eliminar duplicados (por si un comando base también está en habilidades.json)
                disponibles_unicos = []
                vistos = set()
                for item in disponibles:
                    cmd = item.split(":")[0].strip("- ").strip()
                    if cmd not in vistos:
                        vistos.add(cmd)
                        disponibles_unicos.append(item)
                
                msg = f"Comandos disponibles para perfil {perfil_activo} ({len(disponibles_unicos)}):\n" + "\n".join(disponibles_unicos)
            
            guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
            
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    elif comando == "indexar_habilidades":
        try:
            resultado = indexar_habilidades()
            if resultado.get("error"):
                msg = f"Error: {resultado['error']}"
                guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
            else:
                total = resultado.get("total", 0)
                errores = resultado.get("errores", [])
                habilidades = resultado.get("habilidades", [])
                
                if habilidades:
                    lista = "\n".join([f"  - {h}" for h in habilidades])
                    if errores:
                        msg = f"Indexacion completada. {total} habilidades indexadas (con {len(errores)} errores).\n\nHabilidades indexadas:\n{lista}"
                    else:
                        msg = f"Indexacion completada. {total} habilidades indexadas.\n\nHabilidades indexadas:\n{lista}"
                else:
                    if errores:
                        msg = f"Indexacion completada con {len(errores)} errores. {total} habilidades indexadas."
                    else:
                        msg = f"Indexacion completada. {total} habilidades indexadas."
                
                guardar_resultado_json(transaccion_id, accion_idx, comando, "ok", msg)
            return True
        except Exception as e:
            guardar_resultado_json(transaccion_id, accion_idx, comando, "error", str(e))
            return False

    return False

def ejecutar_herramienta(comando, accion, transaccion_id, accion_idx, info):
    # Por ahora, las herramientas externas no estan implementadas
    msg = f"Herramienta externa no implementada: {comando}"
    escribir_log(msg)
    guardar_resultado_json(transaccion_id, accion_idx, comando, "error", msg)
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
        
        # Guardar WORK_DIR para el visor
        with open(SCRIPT_DIR / "workdir.txt", "w") as f:
            f.write(str(WORK_DIR))
        
        # Crear archivos de configuracion si faltan
        crear_archivos_si_faltan()
        
        # INDEXAR HABILIDADES AL INICIAR (siempre)
        escribir_log("Escaneando habilidades...")
        try:
            resultado = indexar_habilidades()
            if resultado.get("error"):
                escribir_log(f"ERROR: {resultado['error']}")
            else:
                total = resultado.get("total", 0)
                errores = len(resultado.get("errores", []))
                if errores > 0:
                    escribir_log(f"Habilidades cargadas: {total} (con {errores} errores)")
                else:
                    escribir_log(f"Habilidades cargadas: {total}")
        except Exception as e:
            escribir_log(f"Error indexando habilidades: {e}")
        
        # Cargar configuraciones
        cargar_config()
        cargar_habilidades()
        cargar_wispout()
        
        lanzar_visor()
        
        cargar_y_procesar_prompt()
        
        directorio_escucha = obtener_directorio_descargas()
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        JSONOUT_DIR.mkdir(parents=True, exist_ok=True)
        PYSEGURAS_DIR.mkdir(parents=True, exist_ok=True)
        PYHABILIDADES_DIR.mkdir(parents=True, exist_ok=True)
        
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
                
                # Recargar config en cada ciclo para cambios en tiempo real
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
        escribir_log(f"WAIO_ESCUCHA_{VERSION}_FINALIZADO")
        
    except Exception as e:
        escribir_log(f"ERROR FATAL: {e}")
        import traceback
        escribir_log(traceback.format_exc())
        time.sleep(5)

if __name__ == "__main__":
    main()