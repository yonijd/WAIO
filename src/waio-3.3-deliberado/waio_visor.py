# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
waio_visor.py - Visor grafico de WAIO.

Ventana de monitoreo en tiempo real de los resultados del motor.
Muestra los JSON de temp/output/ y permite lanzar los satelites
(transclip, escucha_output, event_visor).

Al cerrarse, detiene el motor y todos los satelites.

Configurable desde waio_config.json:
  - visor_max_lines
  - visor_refresh_ms

Version v2 (B1):
  - mostrar_json respeta [SECCION]
  - monitorear con os.scandir (no re-escanea todo)
  - es_ultimo quitado (sin race)
  - verificar_estado_* solo cada 5s
  - Popen con cwd=SCRIPT_DIR
  - config_get con cache por mtime
  - limpiar_output borra .tmp
  - Boton PROMPT (abre prompt.txt)
  - cerrar() espera 1.5s
"""

import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = SCRIPT_DIR / "temp" / "output"
CONFIG_FILE = SCRIPT_DIR / "config" / "waio_config.json"

VERSION = "3.3"

_config_cache = None
_config_mtime = None


def config_get(clave, default):
    global _config_cache, _config_mtime
    try:
        if not CONFIG_FILE.exists():
            return default
        mtime = CONFIG_FILE.stat().st_mtime
        if _config_cache is not None and _config_mtime == mtime:
            config = _config_cache
        else:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                _config_cache = json.load(f)
            _config_mtime = mtime
            config = _config_cache
        valor = config.get(clave, default)
        if valor is None:
            return default
        if isinstance(default, float):
            return float(valor)
        elif isinstance(default, int):
            return int(valor)
        return valor
    except Exception:
        return default


def buscar_notepadpp():
    candidatos = [
        Path(r"C:\Program Files\Notepad++\notepad++.exe"),
        Path(r"C:\Program Files (x86)\Notepad++\notepad++.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Notepad++" / "notepad++.exe",
        Path(os.environ.get("APPDATA", "")) / "Notepad++" / "notepad++.exe",
    ]
    for c in candidatos:
        try:
            if c.exists():
                return c
        except Exception:
            continue
    return None


class WAIOVisor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"WAIO VISOR {VERSION}")
        self.root.geometry("800x500")
        self.root.configure(bg="black")

        self.ruta_output = Path(OUTPUT_DIR)
        self.ruta_output.mkdir(parents=True, exist_ok=True)

        self.archivos_vistos = set()
        self.transclip_running = False
        self.escucha_running = False
        self.events_running = False
        self.ultimo_chequeo_estado = 0.0

        self.refresh_ms = config_get("visor_refresh_ms", 1000)
        self.max_lineas = config_get("visor_max_lines", 500)

        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg="black", fg="lime",
            font=("Consolas", 10), insertbackground="lime"
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.text_area.tag_config("timestamp", foreground="cyan")
        self.text_area.tag_config("comando", foreground="yellow")
        self.text_area.tag_config("resultado", foreground="lime")
        self.text_area.tag_config("error", foreground="red")
        self.text_area.tag_config("separador", foreground="gray")
        self.text_area.tag_config("copia", foreground="magenta")
        self.text_area.tag_config("ultimo", foreground="cyan")

        frame = tk.Frame(self.root, bg="black")
        frame.pack(fill=tk.X, padx=5, pady=5)

        btn_clean = tk.Button(frame, text="CLEAN", command=self.limpiar, bg="gray20", fg="white")
        btn_clean.pack(side=tk.LEFT, padx=1)

        btn_output = tk.Button(frame, text="OUT", command=self.abrir_output, bg="gray20", fg="white")
        btn_output.pack(side=tk.LEFT, padx=1)

        btn_project = tk.Button(frame, text="PROJ", command=self.abrir_proyecto, bg="gray20", fg="white")
        btn_project.pack(side=tk.LEFT, padx=1)

        self.btn_transclip = tk.Button(frame, text="TRANS", command=self.toggle_transclip, bg="gray20", fg="white")
        self.btn_transclip.pack(side=tk.LEFT, padx=1)

        self.btn_escucha = tk.Button(frame, text="LISTEN", command=self.toggle_escucha, bg="gray20", fg="white")
        self.btn_escucha.pack(side=tk.LEFT, padx=1)

        self.btn_events = tk.Button(frame, text="EVENT", command=self.toggle_events, bg="gray20", fg="white")
        self.btn_events.pack(side=tk.LEFT, padx=1)

        btn_copy = tk.Button(frame, text="COPY", command=self.copiar_todo, bg="gray20", fg="white")
        btn_copy.pack(side=tk.LEFT, padx=1)

        btn_clean_output = tk.Button(frame, text="CLEAN OUT", command=self.limpiar_output, bg="gray20", fg="white")
        btn_clean_output.pack(side=tk.LEFT, padx=1)

        btn_conf = tk.Button(frame, text="CONF", command=lambda: self.abrir_editor("waio_config"), bg="gray20", fg="white")
        btn_conf.pack(side=tk.LEFT, padx=1)

        btn_wisp = tk.Button(frame, text="WISP", command=lambda: self.abrir_editor("wispout"), bg="gray20", fg="white")
        btn_wisp.pack(side=tk.LEFT, padx=1)

        btn_prompt = tk.Button(frame, text="PROMPT", command=self.abrir_prompt, bg="gray20", fg="white")
        btn_prompt.pack(side=tk.LEFT, padx=1)

        self.label_estado = tk.Label(frame, text="Monitoring...", bg="black", fg="gray")
        self.label_estado.pack(side=tk.RIGHT, padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)

        self.verificar_estado_transclip()
        self.verificar_estado_escucha()
        self.verificar_estado_events()

        self.iniciar_escucha_output()

        try:
            with open(SCRIPT_DIR / "temp" / "workdir.txt", "r") as f:
                work_dir = f.read().strip()
                self.escribir(f"Workdir: {work_dir}", "copia")
        except Exception:
            self.escribir("Workdir: not found", "error")

        try:
            with open(SCRIPT_DIR / "config" / "waio_config.json", "r") as f:
                config = json.load(f)
                perfil = config.get("perfil_activo", "standard")
                self.escribir(f"Active profile: {perfil.upper()}", "comando")
        except Exception:
            self.escribir("Profile: not found", "error")

        self.monitorear()

    def verificar_estado_transclip(self):
        lock_file = SCRIPT_DIR / "transclip.lock"
        if lock_file.exists():
            self.transclip_running = True
            self.btn_transclip.config(text="TRANS", bg="darkred")
        else:
            self.transclip_running = False
            self.btn_transclip.config(text="TRANS", bg="gray20")

    def verificar_estado_escucha(self):
        lock_file = SCRIPT_DIR / "escucha.lock"
        if lock_file.exists():
            self.escucha_running = True
            self.btn_escucha.config(text="LISTEN", bg="darkred")
        else:
            self.escucha_running = False
            self.btn_escucha.config(text="LISTEN", bg="gray20")

    def verificar_estado_events(self):
        lock_file = SCRIPT_DIR / "events.lock"
        if lock_file.exists():
            self.events_running = True
            self.btn_events.config(text="EVENT", bg="darkred")
        else:
            self.events_running = False
            self.btn_events.config(text="EVENT", bg="gray20")

    def toggle_transclip(self):
        if self.transclip_running:
            self.cerrar_transclip()
        else:
            self.iniciar_transclip()

    def iniciar_transclip(self):
        try:
            transclip_path = SCRIPT_DIR / "transclip.py"
            if not transclip_path.exists():
                self.escribir("ERROR: transclip.py not found", "error")
                return
            subprocess.Popen(
                ["pythonw", str(transclip_path)],
                cwd=str(SCRIPT_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.escribir("TRANSCLIP started", "copia")
            self.root.after(1000, self.verificar_estado_transclip)
        except Exception as e:
            self.escribir(f"Error starting TRANSCLIP: {e}", "error")

    def cerrar_transclip(self):
        try:
            stop_file = SCRIPT_DIR / "TRANSCLIP_STOP.trigger"
            stop_file.touch()
            self.escribir("Stopping TRANSCLIP...", "copia")
            self.root.after(2000, self.verificar_estado_transclip)
        except Exception as e:
            self.escribir(f"Error stopping TRANSCLIP: {e}", "error")

    def toggle_escucha(self):
        if self.escucha_running:
            self.cerrar_escucha_output()
        else:
            self.iniciar_escucha_output()

    def iniciar_escucha_output(self):
        try:
            escucha_path = SCRIPT_DIR / "escucha_output.py"
            if not escucha_path.exists():
                self.escribir("ERROR: escucha_output.py not found", "error")
                return
            subprocess.Popen(
                ["pythonw", str(escucha_path)],
                cwd=str(SCRIPT_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.escribir("LISTEN started", "copia")
            self.root.after(1000, self.verificar_estado_escucha)
        except Exception as e:
            self.escribir(f"Error starting LISTEN: {e}", "error")

    def cerrar_escucha_output(self):
        try:
            stop_file = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
            stop_file.touch()
            self.escribir("Stopping LISTEN...", "copia")
            self.root.after(2000, self.verificar_estado_escucha)
        except Exception as e:
            self.escribir(f"Error stopping LISTEN: {e}", "error")

    def toggle_events(self):
        if self.events_running:
            self.cerrar_events()
        else:
            self.iniciar_events()

    def iniciar_events(self):
        try:
            events_path = SCRIPT_DIR / "event_visor.py"
            if not events_path.exists():
                self.escribir("ERROR: event_visor.py not found", "error")
                return
            subprocess.Popen(
                ["pythonw", str(events_path)],
                cwd=str(SCRIPT_DIR),
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.escribir("EVENTS started", "copia")
            self.root.after(1000, self.verificar_estado_events)
        except Exception as e:
            self.escribir(f"Error starting EVENTS: {e}", "error")

    def cerrar_events(self):
        try:
            stop_file = SCRIPT_DIR / "EVENTS_STOP.trigger"
            stop_file.touch()
            self.escribir("Stopping EVENTS...", "copia")
            self.root.after(2000, self.verificar_estado_events)
        except Exception as e:
            self.escribir(f"Error stopping EVENTS: {e}", "error")

    def abrir_output(self):
        try:
            os.startfile(str(self.ruta_output))
            self.escribir(f"Output folder opened: {self.ruta_output}", "copia")
        except Exception as e:
            self.escribir(f"Error opening folder: {e}", "error")

    def abrir_proyecto(self):
        try:
            try:
                with open(SCRIPT_DIR / "temp" / "workdir.txt", "r") as f:
                    work_dir = f.read().strip()
                    if Path(work_dir).exists():
                        os.startfile(work_dir)
                        self.escribir(f"Project folder opened: {work_dir}", "copia")
                        return
            except Exception:
                pass
            os.startfile(str(SCRIPT_DIR))
            self.escribir(f"Config folder opened: {SCRIPT_DIR}", "copia")
        except Exception as e:
            self.escribir(f"Error opening project folder: {e}", "error")

    def abrir_editor(self, nombre):
        ruta_json = SCRIPT_DIR / "config" / f"{nombre}.json"
        ruta_py = SCRIPT_DIR / f"{nombre}.py"

        if not ruta_json.exists():
            self.escribir(f"Config not found: {ruta_json.name}", "error")
            return

        if ruta_py.exists():
            try:
                subprocess.Popen(
                    ["pythonw", str(ruta_py)],
                    cwd=str(SCRIPT_DIR),
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.escribir(f"{ruta_py.name} launched: {ruta_py}", "copia")
                return
            except Exception as e:
                self.escribir(f"Error launching {ruta_py.name}: {e}", "error")

        notepad = buscar_notepadpp()
        if notepad is not None:
            try:
                subprocess.Popen([str(notepad), str(ruta_json)])
                self.escribir(f"{ruta_json.name} opened with Notepad++", "copia")
                return
            except Exception as e:
                self.escribir(f"Error opening with Notepad++: {e}", "error")

        try:
            os.startfile(str(ruta_json))
            self.escribir(f"{ruta_json.name} opened with system editor", "copia")
            return
        except Exception as e:
            self.escribir(f"Error opening with system editor: {e}", "error")

        self.escribir(f"No editor found for {ruta_json.name}", "error")

    def abrir_prompt(self):
        ruta_prompt = SCRIPT_DIR / "config" / "prompt.txt"
        if not ruta_prompt.exists():
            self.escribir(f"Prompt not found: {ruta_prompt.name}", "error")
            return

        notepad = buscar_notepadpp()
        if notepad is not None:
            try:
                subprocess.Popen([str(notepad), str(ruta_prompt)])
                self.escribir(f"{ruta_prompt.name} opened with Notepad++", "copia")
                return
            except Exception as e:
                self.escribir(f"Error opening with Notepad++: {e}", "error")

        try:
            os.startfile(str(ruta_prompt))
            self.escribir(f"{ruta_prompt.name} opened with system editor", "copia")
            return
        except Exception as e:
            self.escribir(f"Error opening with system editor: {e}", "error")

        self.escribir(f"No editor found for {ruta_prompt.name}", "error")

    def copiar_portapapeles(self, texto):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(texto)
            return True
        except Exception as e:
            self.escribir(f"Clipboard error: {e}", "error")
            return False

    def escribir(self, texto, tag=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.text_area.insert(tk.END, f"[{timestamp}] ", "timestamp")
        if tag:
            self.text_area.insert(tk.END, f"{texto}\n", tag)
        else:
            self.text_area.insert(tk.END, f"{texto}\n")
        self.text_area.see(tk.END)
        self.limpiar_si_es_necesario()

    def escribir_separador(self):
        self.text_area.insert(tk.END, "-" * 70 + "\n", "separador")
        self.text_area.see(tk.END)

    def limpiar(self):
        self.text_area.delete(1.0, tk.END)
        self.escribir("Screen cleared")

    def limpiar_si_es_necesario(self):
        lineas_actuales = int(self.text_area.index("end-1c").split(".")[0])
        if lineas_actuales > self.max_lineas:
            self.text_area.delete(1.0, f"{self.max_lineas - 400}.0")
            self.escribir("(Old lines removed for performance)", "copia")

    def copiar_todo(self):
        texto = self.text_area.get(1.0, tk.END)
        if self.copiar_portapapeles(texto):
            self.escribir("Text copied to clipboard", "copia")

    def limpiar_output(self):
        if messagebox.askyesno(
            "Confirm",
            f"Delete all JSONs, TXTs and TMPs in {self.ruta_output}?"
        ):
            contador = 0
            for patron in ("*.json", "*.txt", "*.tmp"):
                for archivo in self.ruta_output.glob(patron):
                    try:
                        archivo.unlink()
                        contador += 1
                    except Exception as e:
                        self.escribir(f"Error deleting {archivo.name}: {e}", "error")
            self.archivos_vistos.clear()
            self.escribir(f"Cleaned temp/output/ ({contador} files deleted)", "copia")

    def cerrar(self):
        self.escribir("Closing visor...", "copia")

        if self.transclip_running:
            try:
                (SCRIPT_DIR / "TRANSCLIP_STOP.trigger").touch()
                self.escribir("Closing TRANSCLIP...", "copia")
            except Exception as e:
                self.escribir(f"Error closing TRANSCLIP: {e}", "error")

        if self.escucha_running:
            try:
                (SCRIPT_DIR / "ESCUCHA_STOP.trigger").touch()
                self.escribir("Closing LISTEN...", "copia")
            except Exception as e:
                self.escribir(f"Error closing LISTEN: {e}", "error")

        if self.events_running:
            try:
                (SCRIPT_DIR / "EVENTS_STOP.trigger").touch()
                self.escribir("Closing EVENTS...", "copia")
            except Exception as e:
                self.escribir(f"Error closing EVENTS: {e}", "error")

        try:
            (SCRIPT_DIR / "STOP.trigger").touch()
            self.escribir("STOP.trigger created - Motor will shutdown", "copia")
        except Exception as e:
            self.escribir(f"Error creating STOP.trigger: {e}", "error")

        self.root.after(1500, self.root.destroy)

    def mostrar_json(self, archivo):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)

            tx_id = data.get("transaccion_id", "unknown")
            comando = data.get("comando", "?")
            status = data.get("status", "ok")
            output = data.get("output", "")

            self.escribir_separador()

            self.escribir(f"TRANSACTION: {tx_id}", "comando")

            if status == "ok":
                self.escribir(output, "resultado")
            else:
                self.escribir(output, "error")

            self.escribir_separador()
            return True
        except Exception as e:
            self.escribir(f"Error showing {archivo.name}: {e}", "error")
            return False

    def monitorear(self):
        try:
            if self.ruta_output.exists():
                with os.scandir(self.ruta_output) as it:
                    for entry in it:
                        if not entry.name.endswith(".json"):
                            continue
                        if not entry.is_file():
                            continue
                        if entry.name in self.archivos_vistos:
                            continue
                        self.archivos_vistos.add(entry.name)
                        self.mostrar_json(Path(entry.path))
        except Exception as e:
            self.escribir(f"ERROR in monitor: {e}", "error")

        ahora = time.time()
        if ahora - self.ultimo_chequeo_estado >= 5.0:
            self.verificar_estado_transclip()
            self.verificar_estado_escucha()
            self.verificar_estado_events()
            self.ultimo_chequeo_estado = ahora

        self.label_estado.config(text=f"Monitoring... {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(self.refresh_ms, self.monitorear)


import time


def main():
    root = tk.Tk()
    app = WAIOVisor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
