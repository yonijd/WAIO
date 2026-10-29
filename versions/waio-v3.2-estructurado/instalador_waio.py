#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import winreg
from pathlib import Path

TOOL_NAME = "WAIO"
VERSION = "3.2"
PARENT_KEY = "06_WAIO"
PARENT_LABEL = f"WAIO"
PARENT_ICON = "shell32.dll,25"

CARPETAS_A_COPIAR = [
    "core",
    "skills",
    "rescue_tools",
    "config",
    "data",
    "temp",
    "trash"
]

FILES_TO_COPY = [
    "waio_escucha.py",
    "waio_visor.py",
    "escucha_output.py",
    "event_visor.py",
    "transclip.py",
    "desinstalador_waio.py",
    "desinstalar_waio.bat"
]

ROOTS = [
    r"Software\Classes\Directory\shell",
    r"Software\Classes\Directory\Background\shell"
]

def get_paths():
    profile = Path(os.environ["USERPROFILE"])
    waio_dir = profile / ".waio"
    src_dir = Path(__file__).parent
    return waio_dir, src_dir

def copy_folders(waio_dir, src_dir):
    for carpeta in CARPETAS_A_COPIAR:
        src = src_dir / carpeta
        dst = waio_dir / carpeta
        if src.exists():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"[+] Carpeta copiada: {carpeta}")
        else:
            dst.mkdir(parents=True, exist_ok=True)
            print(f"[+] Carpeta creada (vacia): {carpeta}")

def copy_files(waio_dir, src_dir):
    for filename in FILES_TO_COPY:
        src = src_dir / filename
        dst = waio_dir / filename
        if not src.exists():
            print(f"[ERROR] No se encuentra {filename}")
            return False
        shutil.copy2(src, dst)
        print(f"[+] {filename} copiado")
    return True

def ensure_parent_menu(root_path):
    parent_path = f"{root_path}\\{PARENT_KEY}"
    created = False
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, parent_path, 0, winreg.KEY_WRITE)
    except FileNotFoundError:
        key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, parent_path, 0, winreg.KEY_WRITE)
        created = True
    winreg.SetValueEx(key, "MUIVerb", 0, winreg.REG_SZ, PARENT_LABEL)
    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, PARENT_ICON)
    winreg.SetValueEx(key, "SubCommands", 0, winreg.REG_SZ, "")
    try:
        winreg.DeleteValue(key, "ExtendedSubCommandsKey")
    except FileNotFoundError:
        pass
    winreg.CloseKey(key)
    
    shell_path = f"{parent_path}\\shell"
    shell_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, shell_path, 0, winreg.KEY_WRITE)
    winreg.CloseKey(shell_key)
    
    status = "creado" if created else "actualizado"
    print(f"[+] Menu padre {status}: {parent_path}")

def register_entry(root_path, entry_key, label, cmd, icon):
    entry_path = f"{root_path}\\{PARENT_KEY}\\shell\\{entry_key}"
    cmd_path = f"{entry_path}\\command"
    
    key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, entry_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(key, "", 0, winreg.REG_SZ, label)
    winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)
    winreg.CloseKey(key)
    
    cmd_key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, cmd_path, 0, winreg.KEY_WRITE)
    winreg.SetValueEx(cmd_key, "", 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(cmd_key)
    
    print(f"[+] Entrada registrada: {entry_path}")

def register_menus(waio_dir):
    cmd_iniciar = f'cmd.exe /c start python "{waio_dir}\\waio_escucha.py" --cwd "%V"'
    cmd_visor = f'cmd.exe /c start pythonw "{waio_dir}\\waio_visor.py"'
    cmd_transclip = f'cmd.exe /c start pythonw "{waio_dir}\\transclip.py"'
    cmd_clip = f'cmd.exe /c start pythonw "{waio_dir}\\escucha_output.py"'
    cmd_kill = f'cmd.exe /c start python "{waio_dir}\\rescue_tools\\kill_waio.py"'
    
    for root_path in ROOTS:
        ensure_parent_menu(root_path)
        register_entry(root_path, "01_iniciar_waio", "Iniciar WAIO", cmd_iniciar, "imageres.dll,9")
        register_entry(root_path, "02_visor", "Visor", cmd_visor, "shell32.dll,34")
        register_entry(root_path, "03_transclip", "Transclip", cmd_transclip, "imageres.dll,10")
        register_entry(root_path, "04_clip_output", "Clip Output", cmd_clip, "shell32.dll,46")
        register_entry(root_path, "05_kill_waio", "Kill WAIO", cmd_kill, "shell32.dll,112")

def main():
    print("=" * 60)
    print(f"   INSTALADOR - {TOOL_NAME} {VERSION}")
    print("=" * 60)
    
    waio_dir, src_dir = get_paths()
    
    print(f"\n[1/3] Copiando carpetas a {waio_dir}...")
    copy_folders(waio_dir, src_dir)
    
    print(f"\n[2/3] Copiando archivos sueltos...")
    if not copy_files(waio_dir, src_dir):
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    print(f"\n[3/3] Registrando menu contextual...")
    register_menus(waio_dir)
    
    print("")
    print("=" * 60)
    print(f"   INSTALACION COMPLETADA - {TOOL_NAME} {VERSION}")
    print(f"   Archivos en: {waio_dir}")
    print(f"   Menu contextual: Clic derecho > WAIO")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")
