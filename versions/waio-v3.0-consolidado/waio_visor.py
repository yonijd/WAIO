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
OUTPUT_DIR = str(SCRIPT_DIR / "output")
REFRESCO_MS = 1000
MAX_LINEAS = 500
MAX_CARACTERES_OUTPUT = 2000

VERSION = "3.0"

class WAIOVisor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"WAIO VISOR {VERSION}")
        self.root.geometry("950x600")
        self.root.configure(bg='black')
        
        self.ruta_output = Path(OUTPUT_DIR)
        self.ruta_output.mkdir(parents=True, exist_ok=True)
        
        self.archivos_vistos = set()
        self.transclip_running = False
        self.escucha_running = False
        
        self.text_area = scrolledtext.ScrolledText(
            self.root, wrap=tk.WORD, bg='black', fg='lime',
            font=('Consolas', 10), insertbackground='lime'
        )
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configurar colores
        self.text_area.tag_config("timestamp", foreground="cyan")
        self.text_area.tag_config("comando", foreground="yellow")
        self.text_area.tag_config("resultado", foreground="lime")
        self.text_area.tag_config("error", foreground="red")
        self.text_area.tag_config("separador", foreground="gray")
        self.text_area.tag_config("copia", foreground="magenta")
        self.text_area.tag_config("ultimo", foreground="cyan")
        
        # Frame de botones (nuevo orden)
        frame = tk.Frame(self.root, bg='black')
        frame.pack(fill=tk.X, padx=5, pady=5)
        
        btn_limpiar = tk.Button(frame, text="LIMPIAR", command=self.limpiar, bg='gray20', fg='white')
        btn_limpiar.pack(side=tk.LEFT, padx=5)
        
        btn_abrir_output = tk.Button(frame, text="ABRIR OUTPUT", command=self.abrir_output, bg='gray20', fg='white')
        btn_abrir_output.pack(side=tk.LEFT, padx=5)
        
        self.btn_transclip = tk.Button(frame, text="INICIAR TRANSCLIP", command=self.toggle_transclip, bg='gray20', fg='white')
        self.btn_transclip.pack(side=tk.LEFT, padx=5)
        
        self.btn_escucha = tk.Button(frame, text="ESCUCHA OUTPUT", command=self.toggle_escucha, bg='gray20', fg='white')
        self.btn_escucha.pack(side=tk.LEFT, padx=5)
        
        btn_copiar = tk.Button(frame, text="COPIAR TODO", command=self.copiar_todo, bg='gray20', fg='white')
        btn_copiar.pack(side=tk.LEFT, padx=5)
        
        btn_limpiar_output = tk.Button(frame, text="LIMPIAR OUTPUT", command=self.limpiar_output, bg='gray20', fg='white')
        btn_limpiar_output.pack(side=tk.LEFT, padx=5)
        
        self.label_estado = tk.Label(frame, text="Monitoreando...", bg='black', fg='gray')
        self.label_estado.pack(side=tk.RIGHT, padx=10)
        
        # Configurar cierre
        self.root.protocol("WM_DELETE_WINDOW", self.cerrar)
        
        # Verificar estado inicial y lanzar escucha_output automáticamente
        self.verificar_estado_transclip()
        self.verificar_estado_escucha()
        self.iniciar_escucha_output()  # Automático al abrir visor
        
        self.monitorear()
    
    # ================= VERIFICAR ESTADOS =================
    
    def verificar_estado_transclip(self):
        """Verifica si transclip ya esta corriendo"""
        lock_file = SCRIPT_DIR / "transclip.lock"
        if lock_file.exists():
            self.transclip_running = True
            self.btn_transclip.config(text="CERRAR TRANSCLIP", bg='darkred')
        else:
            self.transclip_running = False
            self.btn_transclip.config(text="INICIAR TRANSCLIP", bg='gray20')
    
    def verificar_estado_escucha(self):
        """Verifica si escucha_output ya esta corriendo"""
        lock_file = SCRIPT_DIR / "escucha.lock"
        if lock_file.exists():
            self.escucha_running = True
            self.btn_escucha.config(text="CERRAR ESCUCHA", bg='darkred')
        else:
            self.escucha_running = False
            self.btn_escucha.config(text="INICIAR ESCUCHA", bg='gray20')
    
    # ================= TRANSCLIP =================
    
    def toggle_transclip(self):
        """Inicia o cierra transclip"""
        if self.transclip_running:
            self.cerrar_transclip()
        else:
            self.iniciar_transclip()
    
    def iniciar_transclip(self):
        """Lanza transclip como proceso independiente"""
        try:
            transclip_path = SCRIPT_DIR / "transclip.py"
            if not transclip_path.exists():
                self.escribir("ERROR: No se encuentra transclip.py", "error")
                return
            
            subprocess.Popen(['pythonw', str(transclip_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            self.escribir("TRANSCLIP iniciado", "copia")
            self.root.after(1000, self.verificar_estado_transclip)
        except Exception as e:
            self.escribir(f"Error iniciando TRANSCLIP: {e}", "error")
    
    def cerrar_transclip(self):
        """Cierra transclip creando archivo de stop"""
        try:
            stop_file = SCRIPT_DIR / "TRANSCLIP_STOP.trigger"
            stop_file.touch()
            self.escribir("Solicitando cierre de TRANSCLIP...", "copia")
            self.root.after(2000, self.verificar_estado_transclip)
        except Exception as e:
            self.escribir(f"Error cerrando TRANSCLIP: {e}", "error")
    
    # ================= ESCUCHA OUTPUT =================
    
    def toggle_escucha(self):
        """Inicia o cierra escucha_output"""
        if self.escucha_running:
            self.cerrar_escucha_output()
        else:
            self.iniciar_escucha_output()
    
    def iniciar_escucha_output(self):
        """Lanza escucha_output como proceso independiente"""
        try:
            escucha_path = SCRIPT_DIR / "escucha_output.py"
            if not escucha_path.exists():
                self.escribir("ERROR: No se encuentra escucha_output.py", "error")
                return
            
            subprocess.Popen(['pythonw', str(escucha_path)], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
            self.escribir("Escucha Output iniciado", "copia")
            self.root.after(1000, self.verificar_estado_escucha)
        except Exception as e:
            self.escribir(f"Error iniciando Escucha Output: {e}", "error")
    
    def cerrar_escucha_output(self):
        """Cierra escucha_output creando archivo de stop"""
        try:
            stop_file = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
            stop_file.touch()
            self.escribir("Solicitando cierre de Escucha Output...", "copia")
            self.root.after(2000, self.verificar_estado_escucha)
        except Exception as e:
            self.escribir(f"Error cerrando Escucha Output: {e}", "error")
    
    # ================= FUNCIONES BASE =================
    
    def abrir_output(self):
        """Abre la carpeta output de WAIO en el explorador"""
        try:
            os.startfile(str(self.ruta_output))
            self.escribir(f"Carpeta output abierta: {self.ruta_output}", "copia")
        except Exception as e:
            self.escribir(f"Error al abrir carpeta: {e}", "error")
    
    def copiar_portapapeles(self, texto):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(texto)
            return True
        except Exception as e:
            self.escribir(f"Error copiando al portapapeles: {e}", "error")
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
        self.escribir("Pantalla limpiada")
    
    def limpiar_si_es_necesario(self):
        lineas_actuales = int(self.text_area.index('end-1c').split('.')[0])
        if lineas_actuales > MAX_LINEAS:
            self.text_area.delete(1.0, f"{MAX_LINEAS - 400}.0")
            self.escribir("(Se borraron lineas antiguas para mantener rendimiento)", "copia")
    
    def copiar_todo(self):
        texto = self.text_area.get(1.0, tk.END)
        if self.copiar_portapapeles(texto):
            self.escribir("Texto copiado al portapapeles", "copia")
    
    def limpiar_output(self):
        if messagebox.askyesno("Confirmar", f"¿Borrar todos los JSONs y TXTs de {self.ruta_output} (excepto PROMPT_WAIO.txt)?"):
            contador = 0
            for archivo in self.ruta_output.glob("*.json"):
                if archivo.name != "PROMPT_WAIO.txt":
                    try:
                        archivo.unlink()
                        contador += 1
                    except Exception as e:
                        self.escribir(f"Error borrando {archivo.name}: {e}", "error")
            for archivo in self.ruta_output.glob("*.txt"):
                if archivo.name != "PROMPT_WAIO.txt":
                    try:
                        archivo.unlink()
                        contador += 1
                    except Exception as e:
                        self.escribir(f"Error borrando {archivo.name}: {e}", "error")
            self.escribir(f"Limpiado output/ ({contador} archivos borrados)", "copia")
    
    def cerrar(self):
        """Cierra el visor, el motor, TRANSCLIP y Escucha Output"""
        self.escribir("Cerrando visor...", "copia")
        
        # Cerrar transclip
        if self.transclip_running:
            try:
                stop_file = SCRIPT_DIR / "TRANSCLIP_STOP.trigger"
                stop_file.touch()
                self.escribir("Cerrando TRANSCLIP...", "copia")
            except Exception as e:
                self.escribir(f"Error cerrando TRANSCLIP: {e}", "error")
        
        # Cerrar escucha_output
        if self.escucha_running:
            try:
                stop_file = SCRIPT_DIR / "ESCUCHA_STOP.trigger"
                stop_file.touch()
                self.escribir("Cerrando Escucha Output...", "copia")
            except Exception as e:
                self.escribir(f"Error cerrando Escucha Output: {e}", "error")
        
        # Cerrar motor
        try:
            stop_file = SCRIPT_DIR / "STOP.trigger"
            stop_file.touch()
            self.escribir("STOP.trigger creado - Motor se apagara", "copia")
        except Exception as e:
            self.escribir(f"Error al crear STOP.trigger: {e}", "error")
        
        self.root.destroy()
    
    # ================= MONITOREO Y JSON =================
    
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
                if len(output) > MAX_CARACTERES_OUTPUT:
                    output = output[:MAX_CARACTERES_OUTPUT] + "..."
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
                self.escribir(f"[COPIADO] {archivo.name} (en portapapeles)", "copia")
                texto_copia = f"Comando: {comando}\nStatus: {status}\nResultado: {output}"
                self.copiar_portapapeles(texto_copia)
            
            return True
        except Exception as e:
            self.escribir(f"Error mostrando {archivo.name}: {e}", "error")
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
            
            # Actualizar estados de los procesos
            self.verificar_estado_transclip()
            self.verificar_estado_escucha()
            
        except Exception as e:
            self.escribir(f"ERROR en monitoreo: {e}", "error")
        
        self.label_estado.config(text=f"Monitoreando... {datetime.now().strftime('%H:%M:%S')}")
        self.root.after(REFRESCO_MS, self.monitorear)

def main():
    root = tk.Tk()
    app = WAIOVisor(root)
    root.mainloop()

if __name__ == "__main__":
    main()