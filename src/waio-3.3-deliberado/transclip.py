# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
transclip.py - Puente portapapeles -> Downloads para WAIO 3.3.

Caso de uso: el LLM no formateo el JSON en un bloque descargable, o dio un
JSON invalido, o queres pegar el contenido sin guardarlo a mano.

Monitorea el portapapeles. Cuando detecta contenido nuevo:
  1. Si es JSON WAIO completo (transaccion_id + acciones) -> lo guarda tal cual.
  2. Si es JSON con "comando" -> resuelve el comando contra skills.json
     (canonico -> alias -> fallback hardcodeado), reescribe al nombre canonico
     y lo envuelve en una transaccion.
  3. Si es output del motor (tiene status + output) -> lo guarda como archivo
     de texto, NO re-ejecuta el comando (evita bucle).
  4. Si es JSON externo (sin comando ni acciones) -> lo envuelve en crear_archivo.
  5. Si es texto plano -> intenta extraer/reparar JSON embebido; si no, [SKIP].

Version v3.0 (WAIO 3.3):
  - Lee skills.json (WAIO-V3-SKILLS-2026) para resolver comandos y alias.
  - Fallback a COMANDOS_SIMPLES si skills.json no existe.
  - Filtro de outputs del motor (T3).
  - verificar_lock seguro con pid_es_python (T1).
  - Sin input() bloqueante (T16).
  - Sanitiza tx_id en lugar de rechazar.
  - Repara JSON mal formado y extrae JSON embebido de texto.
"""

import tkinter as tk
from tkinter import scrolledtext
import json
import re
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path
import winreg

VERSION = "v3.0"

SCRIPT_DIR = Path(__file__).parent
SKILLS_FILE = SCRIPT_DIR / "data" / "skills.json"
STOP_FILE = SCRIPT_DIR / "TRANSCLIP_STOP.trigger"
LOCK_FILE = SCRIPT_DIR / "transclip.lock"

# Fallback hardcodeado (solo si skills.json no existe o no tiene firma V3).
# Es un subconjunto de los alias de WAIO 3.3; se mantiene por compatibilidad.
COMANDOS_SIMPLES = {
    "dir": "listar_directorio",
    "ls": "listar_directorio",
    "cat": "leer_archivo",
    "leer": "leer_archivo",
    "read": "leer_archivo",
    "existe": "existe_archivo",
    "test": "existe_archivo",
    "tamano": "obtener_tamano",
    "size": "obtener_tamano",
    "modificado": "fecha_modificacion",
    "modified": "fecha_modificacion",
    "mkdir": "crear_carpeta",
    "make_dir": "crear_carpeta",
    "copy": "copiar_archivo",
    "cp": "copiar_archivo",
    "move": "mover_archivo",
    "mv": "mover_archivo",
    "ren": "renombrar_archivo",
    "rename": "renombrar_archivo",
    "del": "eliminar_archivo",
    "rm": "eliminar_archivo",
    "rmdir": "eliminar_carpeta",
    "delete_dir": "eliminar_carpeta",
    "agregar": "append_archivo",
    "append": "append_archivo",
    "head": "leer_lineas",
    "read_lines": "leer_lineas",
    "contar": "contar_lineas",
    "wc": "contar_lineas",
    "count": "contar_lineas",
    "buscar": "buscar_archivos",
    "find": "buscar_archivos",
    "search": "buscar_archivos",
}

TX_ID_PATTERN = re.compile(r"[^A-Za-z0-9_\-]")


# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------

def escribir_log(texto):
    try:
        fecha = datetime.now().strftime("%Y%m%d")
        archivo_log = SCRIPT_DIR / "temp" / "logs" / f"transclip_{fecha}.log"
        archivo_log.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(archivo_log, "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {texto}\n")
    except Exception:
        pass


# ----------------------------------------------------------------------
# Sanitizacion de tx_id
# ----------------------------------------------------------------------

def sanitizar_tx_id(tx):
    """Convierte un tx_id crudo en uno que cumpla [A-Za-z0-9_-]{1,100}.
    No rechaza: sanitiza para no romper el flujo de urgencia.
    """
    tx = str(tx) if tx is not None else ""
    tx = TX_ID_PATTERN.sub("_", tx).strip("_")
    if not tx or len(tx) > 100:
        tx = generar_id_unico()
    return tx[:100]


def generar_id_unico():
    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"tx_clip_{ts}"


# ----------------------------------------------------------------------
# Directorio de descargas
# ----------------------------------------------------------------------

def obtener_directorio_descargas():
    ruta_std = Path.home() / "Downloads"
    if ruta_std.exists() and ruta_std.is_dir():
        return ruta_std
    ruta_esp = Path.home() / "Descargas"
    if ruta_esp.exists() and ruta_esp.is_dir():
        return ruta_esp
    try:
        subkey = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        clave = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey)
        try:
            valor = winreg.QueryValueEx(clave, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
            ruta_reg = Path(valor)
            if ruta_reg.exists() and ruta_reg.is_dir():
                winreg.CloseKey(clave)
                return ruta_reg
        except Exception:
            pass
        finally:
            try:
                winreg.CloseKey(clave)
            except Exception:
                pass
    except Exception:
        pass
    return Path.cwd()


# ----------------------------------------------------------------------
# Skills.json (WAIO 3.3)
# ----------------------------------------------------------------------

def cargar_skills():
    """Devuelve (skills, indice_alias, indice_canonico).
    Si skills.json no existe o no tiene firma V3, devuelve vacios y se usara
    el fallback hardcodeado en resolver_comando.
    """
    try:
        if not SKILLS_FILE.exists():
            escribir_log("skills.json no existe, se usara fallback hardcodeado")
            return {}, {}, {}
        with open(SKILLS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("_waio_firma") != "WAIO-V3-SKILLS-2026":
            escribir_log("skills.json sin firma WAIO-V3-SKILLS-2026, se usara fallback")
            return {}, {}, {}
        skills = data.get("skills", {})
        indice_alias = {}
        for nombre, info in skills.items():
            for alias in info.get("alias", []):
                indice_alias[alias.lower()] = nombre
        indice_canonico = {k.lower(): k for k in skills.keys()}
        escribir_log(f"skills.json cargado: {len(skills)} comandos, {len(indice_alias)} alias")
        return skills, indice_alias, indice_canonico
    except Exception as e:
        escribir_log(f"Error cargando skills.json: {e}")
        return {}, {}, {}


def resolver_comando(comando_raw, skills, indice_alias, indice_canonico):
    """Resuelve un comando crudo a su nombre canonico.
    Orden:
      1. Canonico (case-insensitive) en skills.json.
      2. Alias (case-insensitive) en skills.json.
      3. Fallback hardcodeado (COMANDOS_SIMPLES).
    Devuelve (nombre_canonico, origen) o (None, None).
    origen es "canonico", "alias", "fallback" o None.
    """
    if not comando_raw or not isinstance(comando_raw, str):
        return None, None
    clave = comando_raw.strip().lower()
    if not clave:
        return None, None
    if clave in indice_canonico:
        return indice_canonico[clave], "canonico"
    if clave in indice_alias:
        return indice_alias[clave], "alias"
    if clave in COMANDOS_SIMPLES:
        return COMANDOS_SIMPLES[clave], "fallback"
    return None, None


# ----------------------------------------------------------------------
# Reparacion / extraccion de JSON
# ----------------------------------------------------------------------

def intentar_reparar_json(texto):
    """Intenta parsear un JSON mal formado. Devuelve (datos, error)."""
    # 1. Normal
    try:
        return json.loads(texto), None
    except json.JSONDecodeError:
        pass
    # 2. Comillas simples -> dobles (solo si no hay dobles ya)
    try:
        if "'" in texto and '"' not in texto:
            reparado = texto.replace("'", '"')
            return json.loads(reparado), None
    except json.JSONDecodeError:
        pass
    # 3. Trailing commas
    try:
        reparado = re.sub(r",\s*([}\]])", r"\1", texto)
        return json.loads(reparado), None
    except json.JSONDecodeError:
        pass
    # 4. Comentarios // y #
    try:
        reparado = re.sub(r"//.*$", "", texto, flags=re.MULTILINE)
        reparado = re.sub(r"#.*$", "", reparado, flags=re.MULTILINE)
        return json.loads(reparado), None
    except json.JSONDecodeError:
        pass
    # 5. Combinacion: comillas simples + trailing commas
    try:
        reparado = texto.replace("'", '"') if '"' not in texto else texto
        reparado = re.sub(r",\s*([}\]])", r"\1", reparado)
        return json.loads(reparado), None
    except json.JSONDecodeError:
        pass
    return None, "No se pudo reparar el JSON"


def extraer_json_embebido(texto):
    """Extrae un JSON embebido en texto. Devuelve el string o None."""
    # Bloque ```json ... ```
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texto, re.DOTALL)
    if match:
        return match.group(1)
    # Primer { hasta ultimo }
    inicio = texto.find("{")
    fin = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return texto[inicio:fin + 1]
    return None


# ----------------------------------------------------------------------
# Lock (T1: sin shell=True, con pid_es_python)
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


def verificar_lock():
    if LOCK_FILE.exists():
        try:
            pid = int(LOCK_FILE.read_text().strip())
            if pid_es_python(pid):
                return False
            escribir_log(f"Lock huerfano detectado (PID {pid})")
            LOCK_FILE.unlink()
        except Exception:
            try:
                LOCK_FILE.unlink()
            except Exception:
                pass
    try:
        LOCK_FILE.write_text(str(os.getpid()))
    except Exception as e:
        escribir_log(f"Error creando lock: {e}")
    return True


def limpiar_lock():
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
    except Exception:
        pass


def verificar_stop():
    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
            return True
        except Exception:
            return True
    return False


# ----------------------------------------------------------------------
# UI
# ----------------------------------------------------------------------

class TransClip:
    def __init__(self, root):
        self.root = root
        self.root.title(f"TRANSCLIP - {VERSION}")
        self.root.geometry("750x550")
        self.root.protocol("WM_DELETE_WINDOW", self.salir)

        self.frame = tk.Frame(root)
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.log = scrolledtext.ScrolledText(self.frame, wrap=tk.WORD, width=85, height=28)
        self.log.pack(fill=tk.BOTH, expand=True)

        self.btn_salir = tk.Button(root, text="SALIR", command=self.salir,
                                   bg="red", fg="white", font=("Arial", 10, "bold"))
        self.btn_salir.pack(pady=5)

        self.directorio_descargas = obtener_directorio_descargas()
        (SCRIPT_DIR / "temp" / "logs").mkdir(parents=True, exist_ok=True)
        (SCRIPT_DIR / "temp" / "traducidos").mkdir(parents=True, exist_ok=True)

        # Cargar skills.json
        self.skills, self.indice_alias, self.indice_canonico = cargar_skills()

        escribir_log(f"INICIO | TRANSCLIP {VERSION}")
        escribir_log(f"Descargas: {self.directorio_descargas}")

        self.log.insert(tk.END, "=" * 60 + "\n")
        self.log.insert(tk.END, f"TRANSCLIP - {VERSION}\n")
        self.log.insert(tk.END, "=" * 60 + "\n")
        self.log.insert(tk.END, f"[INFO] Descargas: {self.directorio_descargas}\n")
        self.log.insert(tk.END, f"[INFO] Logs: temp/logs/transclip_YYYYMMDD.log\n")
        if self.skills:
            self.log.insert(tk.END, f"[INFO] skills.json: {len(self.skills)} comandos, {len(self.indice_alias)} alias\n")
        else:
            self.log.insert(tk.END, f"[INFO] skills.json no disponible, usando fallback hardcodeado\n")
        self.log.insert(tk.END, "[INFO] Pega un JSON (WAIO, comando o externo) y se guardara en Downloads\n")
        self.log.insert(tk.END, "-" * 60 + "\n\n")

        self.ultimo_contenido = ""
        self.verificar_portapapeles()
        self.verificar_stop_senal()

    def verificar_stop_senal(self):
        if verificar_stop():
            self.log.insert(tk.END, "\n[EXIT] Cerrando por senal externa...\n")
            escribir_log("Cerrado por senal externa")
            self.root.after(100, self.salir)
            return
        self.root.after(1000, self.verificar_stop_senal)

    def verificar_portapapeles(self):
        try:
            contenido = self.root.clipboard_get()
            if contenido != self.ultimo_contenido and contenido.strip():
                self.ultimo_contenido = contenido
                self.procesar_contenido(contenido)
        except Exception as e:
            if "empty" not in str(e).lower():
                escribir_log(f"Error portapapeles: {e}")
        self.root.after(500, self.verificar_portapapeles)

    # ------------------------------------------------------------------
    # Procesamiento
    # ------------------------------------------------------------------

    def procesar_contenido(self, contenido):
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 1. Intentar parsear directo
        datos = None
        error_json = None
        try:
            datos = json.loads(contenido)
        except json.JSONDecodeError as e:
            error_json = e

        # 2. Si fallo, intentar extraer JSON embebido del texto
        if datos is None:
            embebido = extraer_json_embebido(contenido)
            if embebido:
                datos, err = intentar_reparar_json(embebido)
                if datos is not None:
                    self.log.insert(tk.END, f"[FIX] {timestamp} - JSON extraido de texto\n")
                    escribir_log("JSON extraido de texto")
                else:
                    self.log.insert(tk.END, f"[SKIP] {timestamp} - JSON embebido invalido: {err}\n")
                    escribir_log(f"JSON embebido invalido: {err}")
                    self.log.see(tk.END)
                    return
            else:
                self.log.insert(tk.END, f"[SKIP] {timestamp} - Texto plano (ignorado)\n")
                escribir_log(f"Texto plano ignorado: {error_json}")
                self.log.see(tk.END)
                return
        else:
            pass  # parseo directo OK

        # 3. Si parseo directo fallo pero reparo OK, avisar
        if error_json and datos is not None:
            datos, err = intentar_reparar_json(contenido)
            if datos is not None:
                self.log.insert(tk.END, f"[FIX] {timestamp} - JSON reparado\n")
                escribir_log("JSON reparado")

        if not isinstance(datos, dict):
            self.log.insert(tk.END, f"[SKIP] {timestamp} - JSON no es objeto\n")
            self.log.see(tk.END)
            return

        # Caso A: JSON WAIO completo (transaccion_id + acciones)
        if "transaccion_id" in datos and "acciones" in datos:
            self.log.insert(tk.END, f"[OK] {timestamp} - JSON WAIO completo\n")
            escribir_log(f"JSON WAIO completo: {datos.get('transaccion_id', '?')}")
            self.guardar_json(datos)
            return

        # Caso B: output del motor (status + output) -> NO re-ejecutar
        if "comando" in datos and "output" in datos and "status" in datos:
            self.log.insert(tk.END, f"[SKIP] {timestamp} - Output del motor (guardado como texto)\n")
            escribir_log("Output del motor detectado, se guarda como archivo de texto")
            tx_id = sanitizar_tx_id(datos.get("transaccion_id", ""))
            waio_json = {
                "transaccion_id": tx_id,
                "acciones": [
                    {
                        "comando": "crear_archivo",
                        "ruta": f"outputs_copiados/{tx_id}.txt",
                        "contenido": str(datos.get("output", ""))
                    }
                ]
            }
            self.guardar_json(waio_json)
            return

        # Caso C: JSON con "comando" -> resolver contra skills.json
        if "comando" in datos:
            comando_raw = datos["comando"]
            nombre, origen = resolver_comando(
                comando_raw, self.skills, self.indice_alias, self.indice_canonico
            )
            if not nombre:
                self.log.insert(tk.END, f"[SKIP] {timestamp} - Comando desconocido: {comando_raw}\n")
                escribir_log(f"Comando desconocido: {comando_raw}")
                self.log.see(tk.END)
                return
            if nombre != comando_raw:
                self.log.insert(tk.END, f"[-->] {timestamp} - {comando_raw} -> {nombre} ({origen})\n")
                escribir_log(f"Resuelto: {comando_raw} -> {nombre} ({origen})")
            else:
                self.log.insert(tk.END, f"[-->] {timestamp} - Comando: {nombre}\n")
            datos["comando"] = nombre
            tx_id = generar_id_unico()
            waio_json = {
                "transaccion_id": tx_id,
                "acciones": [datos]
            }
            self.log.insert(tk.END, f"      ID: {tx_id}\n")
            self.guardar_json(waio_json)
            return

        # Caso D: JSON externo (sin comando ni acciones) -> envolver en crear_archivo
        self.log.insert(tk.END, f"[BOX] {timestamp} - JSON externo, envolviendo\n")
        tx_id = generar_id_unico()
        contenido_str = json.dumps(datos, indent=2, ensure_ascii=False)
        tamano = len(contenido_str.encode("utf-8"))
        if tamano > 1_000_000:
            self.log.insert(tk.END, f"[WARN] JSON grande ({tamano} bytes), puede exceder limite\n")
            escribir_log(f"JSON grande: {tamano} bytes")
        waio_json = {
            "transaccion_id": tx_id,
            "acciones": [
                {
                    "comando": "crear_archivo",
                    "ruta": f"externos/{tx_id}.json",
                    "contenido": contenido_str
                }
            ]
        }
        escribir_log(f"JSON externo adaptado: {tx_id}")
        self.guardar_json(waio_json)

    # ------------------------------------------------------------------
    # Guardado
    # ------------------------------------------------------------------

    def guardar_json(self, datos_json):
        try:
            tx_id = sanitizar_tx_id(datos_json.get("transaccion_id", ""))
            datos_json["transaccion_id"] = tx_id
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            nombre = f"{tx_id}_{timestamp}.json"
            ruta = self.directorio_descargas / nombre
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(datos_json, f, indent=2, ensure_ascii=False)
            self.log.insert(tk.END, f"      SAVED: {nombre}\n\n")
            self.log.see(tk.END)
            escribir_log(f"JSON guardado: {nombre}")
        except Exception as e:
            self.log.insert(tk.END, f"      ERROR guardando: {e}\n\n")
            escribir_log(f"Error guardando: {e}")
            self.log.see(tk.END)

    # ------------------------------------------------------------------
    # Salida
    # ------------------------------------------------------------------

    def salir(self):
        try:
            self.log.insert(tk.END, "\n[EXIT] Cerrando TRANSCLIP...\n")
        except Exception:
            pass
        escribir_log("FIN | TRANSCLIP cerrado")
        limpiar_lock()
        self.root.destroy()


# ----------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------

def main():
    if not verificar_lock():
        escribir_log("TRANSCLIP ya esta corriendo")
        sys.exit(1)

    if STOP_FILE.exists():
        try:
            STOP_FILE.unlink()
        except Exception:
            pass

    root = tk.Tk()
    app = TransClip(root)
    root.mainloop()


if __name__ == "__main__":
    main()