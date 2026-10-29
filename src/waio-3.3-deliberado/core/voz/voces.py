import subprocess
import sys
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.join(BASE_DIR, "waiovoz")
CONFIG_FILE = os.path.join(CONFIG_DIR, "voz_config.json")

def ejecutar_powershell(comando):
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    resultado = subprocess.run(
        ["powershell", "-Command", comando],
        capture_output=True,
        text=True,
        creationflags=flags
    )
    return resultado.stdout.strip()

def listar_voces():
    cmd = (
        'Add-Type -AssemblyName System.Speech; '
        '$v = New-Object System.Speech.Synthesis.SpeechSynthesizer; '
        '$v.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }'
    )
    salida = ejecutar_powershell(cmd)
    return [v.strip() for v in salida.splitlines() if v.strip()]

def voz_predeterminada():
    cmd = (
        'Add-Type -AssemblyName System.Speech; '
        '(New-Object System.Speech.Synthesis.SpeechSynthesizer).Voice.Name'
    )
    return ejecutar_powershell(cmd)

def cargar_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def guardar_config(config):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def main():
    args = sys.argv[1:]
    if not args:
        print("Uso:")
        print("  voces.py listar")
        print('  voces.py usar "Nombre de la voz"')
        print("  voces.py velocidad N   (entre -10 y 10)")
        print("  voces.py volumen N     (entre 0 y 100)")
        print("  voces.py reset")
        return

    accion = args[0].lower()

    if accion == "listar":
        voces = listar_voces()
        pred = voz_predeterminada()
        print("Voces instaladas:")
        for v in voces:
            marca = "  (predeterminada del sistema)" if v == pred else ""
            print("  - " + v + marca)
        config = cargar_config()
        if config.get("voz"):
            print("")
            print("Voz configurada actualmente: " + config["voz"])
        else:
            print("")
            print("No hay voz configurada. Se usa la predeterminada del sistema.")

    elif accion == "usar":
        if len(args) < 2:
            print("Falta el nombre de la voz.")
            return
        nombre = " ".join(args[1:])
        voces = listar_voces()
        if nombre not in voces:
            print("La voz '" + nombre + "' no esta instalada.")
            print("Usa 'voces.py listar' para ver las disponibles.")
            return
        config = cargar_config()
        config["voz"] = nombre
        config.setdefault("velocidad", 0)
        config.setdefault("volumen", 100)
        config.setdefault("chars_por_segundo", 15.0)
        config.setdefault("timeout_maximo", 300)
        guardar_config(config)
        print("Voz configurada: " + nombre)

    elif accion == "velocidad":
        if len(args) < 2:
            print("Falta el valor de velocidad.")
            return
        try:
            valor = int(args[1])
        except:
            print("Valor no valido.")
            return
        if valor < -10 or valor > 10:
            print("El valor debe estar entre -10 y 10.")
            return
        config = cargar_config()
        config["velocidad"] = valor
        config.setdefault("volumen", 100)
        config.setdefault("chars_por_segundo", 15.0)
        config.setdefault("timeout_maximo", 300)
        guardar_config(config)
        print("Velocidad configurada: " + str(valor))

    elif accion == "volumen":
        if len(args) < 2:
            print("Falta el valor de volumen.")
            return
        try:
            valor = int(args[1])
        except:
            print("Valor no valido.")
            return
        if valor < 0 or valor > 100:
            print("El valor debe estar entre 0 y 100.")
            return
        config = cargar_config()
        config["volumen"] = valor
        config.setdefault("velocidad", 0)
        config.setdefault("chars_por_segundo", 15.0)
        config.setdefault("timeout_maximo", 300)
        guardar_config(config)
        print("Volumen configurado: " + str(valor))

    elif accion == "reset":
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
            print("Configuracion borrada. Se usara la predeterminada del sistema.")
        else:
            print("No habia configuracion guardada.")

    else:
        print("Accion desconocida: " + accion)

if __name__ == "__main__":
    main()
