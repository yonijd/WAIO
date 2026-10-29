import subprocess
import sys
import os
import json
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "waiovoz")
CONFIG_FILE = os.path.join(CONFIG_DIR, "voz_config.json")

TEXTO_PRUEBA = (
    "Hola, esta es una prueba de voz.\n"
    "Estoy comprobando la voz, la velocidad y el volumen.\n"
    "Si me escuchas bien, guarda la configuracion."
)

def ejecutar_powershell(comando, capturar=False):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    if capturar:
        resultado = subprocess.run(
            ["powershell", "-Command", comando],
            capture_output=True,
            text=True,
            creationflags=flags
        )
        return resultado.stdout.strip()
    else:
        subprocess.run(
            ["powershell", "-Command", comando],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags
        )
        return ""

def listar_voces():
    cmd = (
        'Add-Type -AssemblyName System.Speech; '
        '$v = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        '$v.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }'
    )
    salida = ejecutar_powershell(cmd, capturar=True)
    return [v.strip() for v in salida.splitlines() if v.strip()]

def voz_predeterminada():
    cmd = (
        'Add-Type -AssemblyName System.Speech; '
        '(New-Object System.Speech.Synthesis.SpeechSynthesizer).Voice.Name'
    )
    return ejecutar_powershell(cmd, capturar=True)

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def guardar_config(config):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def borrar_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def hablar_con(voz, velocidad, volumen, texto):
    partes = [
        "Add-Type -AssemblyName System.Speech;",
        "$v = New-Object System.Speech.Synthesis.SpeechSynthesizer;",
        "$v.Rate = " + str(int(velocidad)) + ";",
        "$v.Volume = " + str(int(volumen)) + ";",
    ]
    if voz:
        partes.append('$v.SelectVoice("' + voz + '");')
    texto_escapado = texto.replace('"', '\\"').replace("\n", " ").replace("\r", " ")
    partes.append('$v.Speak("' + texto_escapado + '")')
    ejecutar_powershell(" ".join(partes))

class VentanaVoz:

    def __init__(self, root):
        self.root = root
        self.root.title("Configuracion de voz")
        self.root.resizable(False, False)

        self.voces = listar_voces()
        self.predeterminada = voz_predeterminada()
        self.config = cargar_config()

        marco = ttk.Frame(root, padding=10)
        marco.grid(row=0, column=0, sticky="nsew")

        ttk.Label(marco, text="Voz:").grid(row=0, column=0, sticky="w", pady=(0, 4))

        opciones = ["(predeterminada del sistema)"] + self.voces
        self.var_voz = tk.StringVar()
        self.combo_voz = ttk.Combobox(
            marco, textvariable=self.var_voz, values=opciones,
            state="readonly", width=44
        )
        self.combo_voz.grid(row=0, column=1, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(marco, text="Velocidad:").grid(row=1, column=0, sticky="w")
        self.var_vel = tk.IntVar(value=0)
        self.scale_vel = tk.Scale(
            marco, from_=-10, to=10, orient="horizontal",
            variable=self.var_vel, resolution=1, showvalue=True,
            length=260, label=""
        )
        self.scale_vel.grid(row=1, column=1, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(marco, text="Volumen:").grid(row=2, column=0, sticky="w")
        self.var_vol = tk.IntVar(value=100)
        self.scale_vol = tk.Scale(
            marco, from_=0, to=100, orient="horizontal",
            variable=self.var_vol, resolution=1, showvalue=True,
            length=260, label=""
        )
        self.scale_vol.grid(row=2, column=1, columnspan=2, sticky="we", pady=(0, 10))

        ttk.Label(marco, text="Texto de prueba:").grid(row=3, column=0, columnspan=3, sticky="w")
        self.txt = tk.Text(marco, height=3, width=48, wrap="word")
        self.txt.insert("1.0", TEXTO_PRUEBA)
        self.txt.config(state="disabled")
        self.txt.grid(row=4, column=0, columnspan=3, sticky="we", pady=(0, 10))

        botones = ttk.Frame(marco)
        botones.grid(row=5, column=0, columnspan=3, sticky="we")

        ttk.Button(botones, text="Probar", command=self.probar).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(botones, text="Guardar", command=self.guardar).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(botones, text="Recargar", command=self.recargar).pack(side="left", expand=True, fill="x", padx=2)
        ttk.Button(botones, text="Reset", command=self.reset).pack(side="left", expand=True, fill="x", padx=2)

        self.aplicar_config_a_ventana(self.config)

    def aplicar_config_a_ventana(self, config):
        voz = config.get("voz")
        if voz and voz in self.voces:
            self.var_voz.set(voz)
        else:
            self.var_voz.set("(predeterminada del sistema)")

        try:
            self.var_vel.set(int(config.get("velocidad", 0)))
        except Exception:
            self.var_vel.set(0)

        try:
            self.var_vol.set(int(config.get("volumen", 100)))
        except Exception:
            self.var_vol.set(100)

    def leer_ventana(self):
        voz_sel = self.var_voz.get()
        if voz_sel == "(predeterminada del sistema)":
            voz = None
        else:
            voz = voz_sel
        velocidad = int(self.var_vel.get())
        volumen = int(self.var_vol.get())
        return voz, velocidad, volumen

    def probar(self):
        voz, velocidad, volumen = self.leer_ventana()
        hablar_con(voz, velocidad, volumen, TEXTO_PRUEBA.replace("\n", " "))

    def guardar(self):
        voz, velocidad, volumen = self.leer_ventana()
        config = cargar_config()
        config["voz"] = voz
        config["velocidad"] = velocidad
        config["volumen"] = volumen
        config.setdefault("chars_por_segundo", 15.0)
        config.setdefault("timeout_maximo", 300)
        try:
            guardar_config(config)
            self.config = config
            messagebox.showinfo("Guardado", "Configuracion guardada.")
        except Exception as e:
            messagebox.showerror("Error", "No se pudo guardar:\n" + str(e))

    def recargar(self):
        self.config = cargar_config()
        self.aplicar_config_a_ventana(self.config)

    def reset(self):
        try:
            borrar_config()
            self.config = {}
            self.aplicar_config_a_ventana({})
            messagebox.showinfo("Reset", "Configuracion borrada. Se usara la predeterminada del sistema.")
        except Exception as e:
            messagebox.showerror("Error", "No se pudo borrar:\n" + str(e))


def main():
    root = tk.Tk()
    VentanaVoz(root)
    root.mainloop()

if __name__ == "__main__":
    main()
