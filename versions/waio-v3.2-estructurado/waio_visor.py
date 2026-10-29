# -*- coding: utf-8 -*-
import json
import time
import subprocess
import os
from pathlib import Path
from datetime import datetime
import tkinter as tk
from tkinter import scrolledtext, messagebox

SCRIPT_DIR = Path(__file__).parent.resolve()
OUTPUT_DIR = str(SCRIPT_DIR / "temp" / "output")
REFRESCO_MS = 1000
MAX_LINEAS = 500

VERSION = "3.2"

class WAIOVisor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"WAIO VISOR {VERSION}")
        self.root.geometry("800x500")
        self.root.configure(bg='black')
        
        self.ruta_output = Path(OUTPUT_DIR)
        self.ruta_output.mkdir(parents=True, exist_ok=True)
        
        self.archivos_vistos = set()
        self.transclip_running = False
        self.escucha_running = False
        self.events_running = False
        
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg='black', fg='lime',
            font=('Consolas', 10), insertbackground='lime'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_area.tag_config("timestamp", foreground="cyan")
        self.text_area.tag_config("comando", foreground="yellow")
        self.text_area.tag_config("resultado", foreground="lime")
        self.text_area.tag_config("error", foreground="red")
        self.text_area.tag_config("separador", foreground="gray")
        self.text_area.tag_config("copia", foreground="magenta")
        self.text_area.tag_config("ultimo", foreground="cyan")
        
        frame = tk.Frame(self.root, bg='black')
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_clean = tk.Button(frame, text="CLEAN", command=self.limpiar, bg='gray20', fg='white')
        btn_clean.pack(side=tk.LEFT, padx=2)
        
        btn_output = tk.Button(frame, text="OUTPUT", command=self.abrir_output, bg='gray20', fg='white')
        btn_output.pack(side=tk.LEFT, padx=2)
        
        btn_project = tk.Button(frame, text="PROJECT", command=self.abrir_proyecto, bg='gray20', fg='white')
        btn_project.pack(side=tk.LEFT, padx=2)
        
        self.btn_transclip = tk.Button(frame, text="TRANSCLIP", command=self.toggle_transclip, bg='gray20', fg='white')
        self.btn_transclip.pack(side=tk.LEFT, padx=2)
        
        self.btn_escucha = tk.Button(frame, text="LISTEN", command=self.toggle_escucha, bg='gray20', fg='white')
        self.btn_escucha.pack(side=tk.LEFT, padx=2)
        
        self.btn_events = tk.Button(frame, text="EVENTS", command=self.toggle_events, bg='gray20', fg='white')
        self.btn_events.pack(side=tk.LEFT, padx=2)
        
        btn_copy = tk.Button(frame, text="COPY", command=self.copiar_todo, bg='gray20', fg='white')
        btn_copy.pack(side=tk.LEFT, padx=2)
        
        btn_clean_output = tk.Button(frame, text="CLEAN OUTPUT", command=self.limpiar_output, bg='gray20', fg='white')
        btn_clean_output.pack(side=tk.LEFT, padx=2)
        
        self.label_estado = tk.Label(frame, text="Monitoring...", bg='black', fg='gray')
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
        except:
            self.escribir("Workdir: No encontrado", "error")
        
        try:
            with open(SCRIPT_DIR / "config" / "waio_config.json", "r") as f:
                config = json.load(f)
                perfil = config.get("perfil_activo", "estandar")
                self.escribir(f"Perfil activo: {perfil}", "comando")
        except:
            self.escribir("Perfil: No encontrado", "error")
        
        self.monitorear()
    
    def verificar_estado_transclip(self):
        lock_file = SCRIPT_DIR / "transclip.lock"
        if lock_file.exists():
            self.transclip_running = True
            self.btn_transclip.config(text="TRANSCLIP", bg='darkred')
        else:
            self.transclip_running = False
            self.btn_transclip.config(text="TRANSCLIP", bg='gray20')
    
    def verificar_estado_escucha(self):
        lock_file = SCRIPT_DIR / "escucha.lock"
        if lock_file.exists():
            self.escucha_running = True
            self.btn_escucha.config(text="LISTEN", bg='darkred')
        else:
            self.escucha_running = False
            self.btn_escucha.config(text="LISTEN", bg='gray20')
    
    def verificar_estado_events(self):
        lock_file = SCRIPT_DIR / "events.lock"
        if lock_file.exists():
            self.events_running = True
            self.btn_events.config(text="EVENTS", bg='darkred')
        else:
            self.events_running = False
            self.btn_events.config(text="EVENTS", bg='gray20')
    
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
            subprocess.Popen(['pythonw', str(transclip_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
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
            subprocess.Popen(['pythonw', str(escucha_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
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
            subprocess.Popen(['pythonw', str(events_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
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
            except:
                pass
            os.startfile(str(SCRIPT_DIR))
            self.escribir(f"Config folder opened: {SCRIPT_DIR}", "copia")
        except Exception as e:
            self.escribir(f"Error opening project folder: {e}", "error")
    
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
        lineas_actuales = int(self.text_area.index('end-1c').split('.')[0])
        if lineas_actuales > MAX_LINEAS:
            self.text_area.delete(1.0, f"{MAX_LINEAS - 400}.0")
            self.escribir("(Old lines removed for performance)", "copia")
    
    def copiar_todo(self):
        texto = self.text_area.get(1.0, tk.END)
        if self.copiar_portapapeles(texto):
            self.escribir("Text copied to clipboard", "copia")
    
    def limpiar_output(self):
        if messagebox.askyesno("Confirm", f"Delete all JSONs and TXTs in {self.ruta_output} (except PROMPT_WAIO.txt)?"):
            contador = 0
            for archivo in self.ruta_output.glob("*.json"):
                if archivo.name != "PROMPT_WAIO.txt":
                    try:
                        archivo.unlink()
                        contador += 1
                    except Exception as e:
                        self.escribir(f"Error deleting {archivo.name}: {e}", "error")
            for archivo in self.ruta_output.glob("*.txt"):
                if archivo.name != "PROMPT_WAIO.txt":
                    try:
                        archivo.unlink()
                        contador += 1
                    except Exception as e:
                        self.escribir(f"Error deleting {archivo.name}: {e}", "error")
            self.escribir(f"Cleaned temp/output/ ({contador} files deleted)", "copia")
    
    def cerrar(self):
        self.escribir("Closing visor...", "copia")
        
        if self.transclip_running:
            try:
                stop_file = SCRIPT_DIR / "TRANSCLIP_STOP.trigger"
                stop_file.touch()
                self.escribir("Closing TRANSCLIP...", "copia")
            except Exception as e:
                self.escribir(f"Error closing TRANSCLIP: {e}", "error")
        
        if self.escucha_running:
            try:
                stop_file = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
                stop_file.touch()
                self.escribir("Closing LISTEN...", "copia")
            except Exception as e:
                self.escribir(f"Error closing LISTEN: {e}", "error")
        
        if self.events_running:
            try:
                stop_file = SCRIPT_DIR / "EVENTS_STOP.trigger"
                stop_file.touch()
                self.escribir("Closing EVENTS...", "copia")
            except Exception as e:
                self.escribir(f"Error closing EVENTS: {e}", "error")
        
        try:
            stop_file = SCRIPT_DIR / "STOP.trigger"
            stop_file.touch()
            self.escribir("STOP.trigger created - Motor will shutdown", "copia")
        except Exception as e:
            self.escribir(f"Error creating STOP.trigger: {e}", "error")
        
        self.root.destroy()
    
    def mostrar_json(self, archivo, es_ultimo=False):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            tx_id = data.get("transaccion_id", "desconocido")
            comando = data.get("comando", "?")
            status = data.get("status", "ok")
            output = data.get("output", "")
            
            self.escribir_separador()
            
            if es_ultimo:
                self.escribir(f"TRANSACCION: {tx_id} (ULTIMO)", "ultimo")
            else:
                self.escribir(f"TRANSACCION: {tx_id}", "comando")
            
            if status == "ok":
                if es_ultimo:
                    self.escribir(f"  {comando}: {output}", "ultimo")
                else:
                    self.escribir(f"  {comando}: {output}", "resultado")
            else:
                if es_ultimo:
                    self.escribir(f"  {comando}: ERROR - {output}", "error")
                else:
                    self.escribir(f"  {comando}: ERROR - {output}", "error")
            
            self.escribir_separador()
            
            if es_ultimo:
                self.escribir(f"[COPIED] {archivo.name} (en portapapeles)", "copia")
                texto_copia = f"Comando: {comando}\nStatus: {status}\nResultado: {output}"
                self.copiar_portapapeles(texto_copia)
            
            return True
        except Exception as e:
            self.escribir(f"Error showing {archivo.name}: {e}", "error")
            return False
    
    def monitorear(self):
        try:
            archivos = list(self.ruta_output.glob("*.json"))
            archivos_json = [a for a in archivos if not a.name.startswith("PROMPT")]
            archivos_json.sort(key=lambda x: x.stat().st_mtime)
            
            for archivo in archivos_json:
                if archivo.name not in self.archivos_vistos:
                    self.archivos_vistos.add(archivo.name)
                    es_ultimo = (archivo == archivos_json[-1]) if archivos_json else True
                    self.mostrar_json(archivo, es_ultimo)
            
            self.verificar_estado_transclip()
            self.verificar_estado_escucha()
            self.verificar_estado_events()
            
        except Exception as e:
            self.escribir(f"ERROR in monitor: {e}", "error")
        
        self.label_estado.config(text=f"Monitoring... {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(REFRESCO_MS, self.monitorear)

def main():
    root = tk.Tk()
    app = WAIOVisor(root)
    root.mainloop()

if __name__ == "__main__":
    main()