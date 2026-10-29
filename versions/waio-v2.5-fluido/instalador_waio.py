#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import winreg
from pathlib import Path

TOOL_NAME = "WAIO"
PARENT_KEY = "06_WAIO"
PARENT_LABEL = "WAIO - Web AI Orchestrator"
PARENT_ICON = "imageres.dll,185"

# Archivos a copiar (con transclip)
FILES_TO_COPY = [
    "waio_escucha_v2.py",
    "waio_visor.py",
    "kill_waio.py",
    "transclip.py"
]

# Dos ubicaciones para el menu contextual
ROOTS = [
    r"Software\Classes\Directory\shell",
    r"Software\Classes\Directory\Background\shell"
]

def get_paths():
    profile = Path(os.environ["USERPROFILE"])
    waio_dir = profile / ".waio"
    src_dir = Path(__file__).parent
    dst_files = {}
    for f in FILES_TO_COPY:
        src = src_dir / f
        dst = waio_dir / f
        dst_files[f] = (src, dst)
    return waio_dir, dst_files, src_dir

def copy_files(waio_dir, dst_files):
    waio_dir.mkdir(parents=True, exist_ok=True)
    
    for filename, (src, dst) in dst_files.items():
        if not src.exists():
            print(f"[ERROR] No se encuentra {filename} en: {src}")
            return False
        shutil.copy2(src, dst)
        print(f"[+] {filename} copiado a: {dst}")
    
    # Crear subcarpetas necesarias
    for subdir in ["logs", "output", "jsonout", "trash"]:
        subpath = waio_dir / subdir
        subpath.mkdir(exist_ok=True)
        print(f"[+] Carpeta creada: {subpath}")
    
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
    
    # Crear la clave shell si no existe
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
    # Comando para iniciar WAIO
    cmd_iniciar = f'cmd.exe /c start python "{waio_dir}\\waio_escucha_v2.py" --cwd "%V"'
    
    # Comando para matar SOLO el motor WAIO
    cmd_kill = f'cmd.exe /c start python "{waio_dir}\\kill_waio.py"'
    
    # Comando para iniciar TRANSCLIP (sin consola)
    cmd_transclip = f'cmd.exe /c start pythonw "{waio_dir}\\transclip.py"'
    
    for root_path in ROOTS:
        ensure_parent_menu(root_path)
        register_entry(root_path, "iniciar_waio", "Iniciar WAIO Aqui", cmd_iniciar, "imageres.dll,134")
        register_entry(root_path, "transclip", "TRANSCLIP (WhatsApp bridge)", cmd_transclip, "imageres.dll,134")
        register_entry(root_path, "kill_waio", "Matar WAIO (solo motor)", cmd_kill, "imageres.dll,132")

def main():
    print("=" * 60)
    print(f"   INSTALADOR - {TOOL_NAME} V2.5")
    print("=" * 60)
    
    waio_dir, dst_files, src_dir = get_paths()
    
    print(f"\n[1/2] Copiando archivos a {waio_dir}...")
    if not copy_files(waio_dir, dst_files):
        input("\nPresione Enter para salir...")
        sys.exit(1)
    
    print(f"\n[2/2] Registrando menu contextual...")
    register_menus(waio_dir)
    
    print("")
    print("=" * 60)
    print(f"   INSTALACION COMPLETADA - {TOOL_NAME} V2.5")
    print(f"   Archivos en: {waio_dir}")
    print(f"   Menu contextual: Clic derecho > {PARENT_LABEL}")
    print("   - Iniciar WAIO Aqui")
    print("   - TRANSCLIP (WhatsApp bridge)  <- NUEVO")
    print("   - Matar WAIO (solo motor)")
    print("")
    print("   TRANSCLIP traduce comandos simples al formato WAIO")
    print("   Ej: {'comando': 'dir'} -> listar_directorio")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")