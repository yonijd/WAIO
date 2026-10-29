import tkinter as tk
from tkinter import scrolledtext
import json
import re
import os
import subprocess
from datetime import datetime
from pathlib import Path
import winreg

# ============================================================
# CONFIGURACION
# ============================================================

VERSION = "v2.5"

# Comandos WAIO directos (se pasan sin traduccion)
COMANDOS_WAIO_DIRECTOS = [
    "listar_directorio", "leer_archivo", "crear_carpeta", "crear_archivo",
    "copiar_archivo", "mover_archivo", "existe_archivo",
    "obtener_tamano", "fecha_modificacion", "eliminar_archivo", "eliminar_carpeta"
]

# Comandos simples (se traducen a WAIO)
COMANDOS_SIMPLES = {
    # Lectura
    "dir": "listar_directorio",
    "ls": "listar_directorio",
    "type": "leer_archivo",
    "cat": "leer_archivo",
    "exists": "existe_archivo",
    "size": "obtener_tamano",
    "modified": "fecha_modificacion",
    # Escritura
    "mkdir": "crear_carpeta",
    "md": "crear_carpeta",
    "copy": "copiar_archivo",
    "cp": "copiar_archivo",
    "move": "mover_archivo",
    "mv": "mover_archivo",
    "ren": "mover_archivo",
    "del": "eliminar_archivo",
    "rm": "eliminar_archivo",
    "rmdir": "eliminar_carpeta",
    "rd": "eliminar_carpeta",
}

# Comandos que requieren 2 parametros
COMANDOS_DOS_PARAMS = ["copiar_archivo", "mover_archivo"]

# ============================================================
# FUNCIONES DE SISTEMA
# ============================================================

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
        except:
            pass
        winreg.CloseKey(clave)
    except:
        pass
    return Path.cwd()

def escribir_log(texto):
    try:
        fecha = datetime.now().strftime("%Y%m%d")
        archivo_log = Path(Path(__file__).parent / "logs" / f"transclip_{fecha}.log")
        archivo_log.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(archivo_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {texto}\n")
    except:
        pass

def generar_id_unico():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
    return f"tx_clip_{timestamp}"

def parsear_comando_simple(texto_completo):
    texto_completo = texto_completo.strip()
    partes = texto_completo.split(maxsplit=1)
    comando = partes[0].lower()
    resto = partes[1] if len(partes) > 1 else ""
    
    resto = re.sub(r'\s*/[a-zA-Z]+', '', resto).strip()
    
    if comando in ["copy", "cp", "move", "mv", "ren"]:
        params = resto.split()
        if len(params) >= 2:
            return comando, [params[0], params[1]]
        else:
            return comando, []
    
    return comando, resto

def traducir_comando_simple(comando_raw):
    comando_base, params = parsear_comando_simple(comando_raw)
    
    if comando_base not in COMANDOS_SIMPLES:
        return None
    
    comando_waio = COMANDOS_SIMPLES[comando_base]
    accion = {"comando": comando_waio}
    
    if comando_waio in ["listar_directorio", "leer_archivo", "existe_archivo",
                        "obtener_tamano", "fecha_modificacion", "crear_carpeta",
                        "eliminar_archivo", "eliminar_carpeta"]:
        ruta = params if isinstance(params, str) else "."
        if not ruta:
            ruta = "."
        accion["ruta"] = ruta
    elif comando_waio in COMANDOS_DOS_PARAMS:
        if isinstance(params, list) and len(params) >= 2:
            accion["origen"] = params[0]
            accion["destino"] = params[1]
        else:
            accion["origen"] = ""
            accion["destino"] = ""
    
    return accion

def verificar_stop():
    waio_dir = Path(Path(__file__).parent)
    stop_file = waio_dir / "TRANSCLIP_STOP.trigger"
    if stop_file.exists():
        try:
            stop_file.unlink()
            return True
        except:
            return True
    return False

def verificar_lock():
    waio_dir = Path(Path(__file__).parent)
    lock_file = waio_dir / "transclip.lock"
    
    if lock_file.exists():
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            try:
                subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True)
                return False
            except:
                lock_file.unlink()
        except:
            lock_file.unlink()
    
    try:
        with open(lock_file, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        escribir_log(f"Error creando lock: {e}")
    
    return True

def limpiar_lock():
    try:
        waio_dir = Path(Path(__file__).parent)
        lock_file = waio_dir / "transclip.lock"
        if lock_file.exists():
            lock_file.unlink()
    except:
        pass

# ============================================================
# CLASE PRINCIPAL
# ============================================================

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
        
        (Path(__file__).parent / "logs").mkdir(exist_ok=True)
        (Path(__file__).parent / "traducidos").mkdir(exist_ok=True)
        
        escribir_log(f"INICIO | TRANSCLIP {VERSION}")
        escribir_log(f"Descargas: {self.directorio_descargas}")
        
        self.log.insert(tk.END, "="*60 + "\n")
        self.log.insert(tk.END, f"TRANSCLIP - {VERSION}\n")
        self.log.insert(tk.END, "="*60 + "\n")
        self.log.insert(tk.END, f"[INFO] Descargas: {self.directorio_descargas}\n")
        self.log.insert(tk.END, "[INFO] Logs: logs/transclip_YYYYMMDD.log\n")
        self.log.insert(tk.END, "[INFO] Traduce cualquier JSON con 'comando' a formato WAIO\n")
        self.log.insert(tk.END, "-"*60 + "\n\n")
        
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
    
    def procesar_contenido(self, contenido):
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        try:
            datos = json.loads(contenido)
            
            # REGLA PRINCIPAL: Si es JSON, envolver siempre en formato WAIO
            # Solo los JSON que YA TIENEN transaccion_id + acciones pasan directo
            
            # Caso 1: Ya es WAIO completo
            if "transaccion_id" in datos and "acciones" in datos:
                self.log.insert(tk.END, f"[OK] {timestamp} - JSON WAIO completo\n")
                escribir_log(f"JSON WAIO completo: {datos.get('transaccion_id', '?')}")
                self.guardar_json(datos)
                return
            
            # Caso 2: Tiene "comando" - envolver automaticamente
            if "comando" in datos:
                comando_raw = datos["comando"]
                self.log.insert(tk.END, f"[-->] {timestamp} - Envolviendo comando: {comando_raw[:50]}\n")
                
                # El JSON original se convierte en una accion dentro de la estructura WAIO
                transaccion_id = generar_id_unico()
                waio_json = {
                    "transaccion_id": transaccion_id,
                    "acciones": [datos]  # El JSON original completo como una accion
                }
                self.log.insert(tk.END, f"      ID: {transaccion_id}\n")
                escribir_log(f"Envueltor: {comando_raw} -> ID: {transaccion_id}")
                self.guardar_json(waio_json)
                return
            
            # Caso 3: JSON externo sin comando - envolver en crear_archivo
            self.log.insert(tk.END, f"[BOX] {timestamp} - JSON externo, envolviendo\n")
            transaccion_id = generar_id_unico()
            waio_json = {
                "transaccion_id": transaccion_id,
                "acciones": [
                    {
                        "comando": "crear_archivo",
                        "ruta": f"externos/{transaccion_id}.json",
                        "contenido": json.dumps(datos, indent=2, ensure_ascii=False)
                    }
                ]
            }
            escribir_log(f"JSON externo adaptado: {transaccion_id}")
            self.guardar_json(waio_json)
            
        except json.JSONDecodeError as e:
            self.log.insert(tk.END, f"[SKIP] {timestamp} - Texto plano (ignorado)\n")
            escribir_log(f"Texto plano ignorado")
            self.log.see(tk.END)
        except Exception as e:
            self.log.insert(tk.END, f"[ERROR] {timestamp} - {str(e)[:100]}\n")
            escribir_log(f"Error procesando: {e}")
            self.log.see(tk.END)
    
    def guardar_json(self, datos_json):
        try:
            transaccion_id = datos_json.get('transaccion_id', 'sin_id')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            nombre = f"{transaccion_id}_{timestamp}.json"
            ruta = self.directorio_descargas / nombre
            
            with open(ruta, 'w', encoding='utf-8') as f:
                json.dump(datos_json, f, indent=2, ensure_ascii=False)
            
            self.log.insert(tk.END, f"      SAVED: {nombre}\n\n")
            self.log.see(tk.END)
            escribir_log(f"JSON guardado: {nombre}")
        except Exception as e:
            self.log.insert(tk.END, f"      ERROR guardando: {e}\n\n")
            escribir_log(f"Error guardando: {e}")
            self.log.see(tk.END)
    
    def salir(self):
        self.log.insert(tk.END, "\n[EXIT] Cerrando TRANSCLIP...\n")
        escribir_log("FIN | TRANSCLIP cerrado")
        limpiar_lock()
        self.root.destroy()

if __name__ == "__main__":
    if not verificar_lock():
        print("TRANSCLIP ya esta corriendo")
        input("Presione Enter para salir...")
        import sys
        sys.exit(1)
    
    root = tk.Tk()
    app = TransClip(root)
    root.mainloop()