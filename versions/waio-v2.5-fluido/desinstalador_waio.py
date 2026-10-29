#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import winreg
from pathlib import Path

TOOL_NAME = "WAIO"
PARENT_KEY = "06_WAIO"

REG_LOCATIONS = [
    r"Software\Classes\Directory\shell",
    r"Software\Classes\Directory\Background\shell"
]

def get_waio_dir():
    return Path(os.environ["USERPROFILE"]) / ".waio"

def remove_files(waio_dir):
    if waio_dir.exists():
        try:
            shutil.rmtree(waio_dir)
            print(f"+ Eliminada carpeta completa: {waio_dir}")
            return True
        except Exception as e:
            print(f"= Error eliminando {waio_dir}: {e}")
            return False
    else:
        print(f"= Carpeta .waio no encontrada")
        return False

def remove_menu(reg_path):
    parent_path = f"{reg_path}\\{PARENT_KEY}"
    
    # Eliminar submenus (incluye transclip)
    for subkey in ["shell\\iniciar_waio", "shell\\kill_waio", "shell\\transclip"]:
        try:
            cmd_path = f"{parent_path}\\{subkey}\\command"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, cmd_path)
            print(f"+ Eliminado command: {cmd_path}")
        except Exception as e:
            print(f"= No se pudo eliminar command {cmd_path}: {e}")
        
        try:
            submenu_path = f"{parent_path}\\{subkey}"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, submenu_path)
            print(f"+ Eliminado submenu: {submenu_path}")
        except Exception as e:
            print(f"= No se pudo eliminar submenu {submenu_path}: {e}")
    
    # Eliminar la clave shell (vacía)
    try:
        shell_path = f"{parent_path}\\shell"
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, shell_path)
        print(f"+ Eliminado shell: {shell_path}")
    except Exception as e:
        print(f"= No se pudo eliminar shell: {e}")
    
    # Eliminar el padre
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, parent_path)
        print(f"+ Eliminado padre: {parent_path}")
    except Exception as e:
        print(f"= No se pudo eliminar padre {parent_path}: {e}")

def main():
    print("=" * 60)
    print(f"   DESINSTALADOR - {TOOL_NAME} V2.5")
    print("=" * 60)
    
    waio_dir = get_waio_dir()
    
    print(f"\n[1/2] Eliminando archivos...")
    remove_files(waio_dir)
    
    print(f"\n[2/2] Eliminando menu contextual...")
    for reg_path in REG_LOCATIONS:
        remove_menu(reg_path)
    
    print("\n" + "=" * 60)
    print(f"   DESINSTALACION COMPLETADA")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")