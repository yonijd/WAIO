import sys
import subprocess
import argparse

def bajar_volumen(pasos=1):
    for i in range(pasos):
        try:
            subprocess.run(["nircmd", "changesysvolume", "-1000"], capture_output=True, check=False)
            print(f"  Bajar: {i+1}/{pasos}")
        except:
            # Fallback: usar teclas de volumen
            try:
                import pyautogui
                pyautogui.press('volumedown')
                print(f"  Bajar (tecla): {i+1}/{pasos}")
            except:
                print("  Error: No se pudo bajar el volumen")
                return False
    return True

def subir_volumen(pasos=1):
    for i in range(pasos):
        try:
            subprocess.run(["nircmd", "changesysvolume", "+1000"], capture_output=True, check=False)
            print(f"  Subir: {i+1}/{pasos}")
        except:
            try:
                import pyautogui
                pyautogui.press('volumeup')
                print(f"  Subir (tecla): {i+1}/{pasos}")
            except:
                print("  Error: No se pudo subir el volumen")
                return False
    return True

def silenciar():
    try:
        subprocess.run(["nircmd", "mute"], capture_output=True, check=False)
        print("  Silenciado/Activado")
        return True
    except:
        try:
            import pyautogui
            pyautogui.press('volumemute')
            print("  Silenciado/Activado (tecla)")
            return True
        except:
            print("  Error: No se pudo silenciar")
            return False

def main():
    parser = argparse.ArgumentParser(description='Controla el volumen del sistema')
    parser.add_argument('--accion', required=True, choices=['subir', 'bajar', 'silenciar'],
                        help='Accion a realizar: subir, bajar, silenciar')
    parser.add_argument('--pasos', type=int, default=1,
                        help='Cantidad de pasos (para subir/bajar), default: 1')
    
    args = parser.parse_args()
    
    print(f"🎵 Control de volumen - Accion: {args.accion}")
    
    if args.accion == 'subir':
        subir_volumen(args.pasos)
    elif args.accion == 'bajar':
        bajar_volumen(args.pasos)
    elif args.accion == 'silenciar':
        silenciar()
    
    print("✅ Completado")

if __name__ == "__main__":
    main()