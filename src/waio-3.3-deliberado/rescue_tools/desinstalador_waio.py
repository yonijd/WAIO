#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026 Yonijd
# Licensed under the MIT License. See LICENSE file in the project root.

"""
desinstalador_waio.py - Desinstala WAIO por completo.

Elimina:
  - La carpeta .waio/ (con opcion de preservar trash/ y logs/)
  - Todas las entradas del menu contextual 06_WAIO en HKCU

NO elimina logs sin preguntar. NO elimina trash/ sin preguntar.
"""

import os
import sys
import shutil
import winreg
from pathlib import Path

TOOL_NAME = "WAIO"
VERSION = "3.3"
PARENT_KEY = "06_WAIO"

REG_LOCATIONS = [
    r"Software\Classes\Directory\shell",
    r"Software\Classes\Directory\Background\shell",
]


def get_waio_dir():
    return Path(os.environ["USERPROFILE"]) / ".waio"


def borrar_clave_recursiva(hive, path):
    """Borra una clave del registro y todas sus subclaves."""
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_ALL_ACCESS)
    except FileNotFoundError:
        return False
    except Exception as e:
        print(f"  [ERROR] Abriendo {path}: {e}")
        return False

    subclaves = []
    try:
        i = 0
        while True:
            try:
                sub = winreg.EnumKey(key, i)
                subclaves.append(sub)
                i += 1
            except OSError:
                break
    finally:
        winreg.CloseKey(key)

    for sub in subclaves:
        borrar_clave_recursiva(hive, f"{path}\\{sub}")

    try:
        winreg.DeleteKey(hive, path)
        print(f"  [+] Clave eliminada: {path}")
        return True
    except Exception as e:
        print(f"  [ERROR] Borrando {path}: {e}")
        return False


def remove_menu(reg_path):
    parent_path = f"{reg_path}\\{PARENT_KEY}"
    try:
        winreg.OpenKey(winreg.HKEY_CURRENT_USER, parent_path)
    except FileNotFoundError:
        print(f"  [ ] No existe: {parent_path}")
        return False
    except Exception as e:
        print(f"  [ERROR] Verificando {parent_path}: {e}")
        return False

    return borrar_clave_recursiva(winreg.HKEY_CURRENT_USER, parent_path)


def remove_files(waio_dir):
    if not waio_dir.exists():
        print(f"  [ ] No existe: {waio_dir}")
        return False

    trash_dir = waio_dir / "trash"
    logs_dir = waio_dir / "temp" / "logs"

    preservar_trash = False
    if trash_dir.exists():
        respuesta = input("  Preservar trash/ (papelera manual)? [S/n]: ").strip().lower()
        preservar_trash = (respuesta != "n")

    preservar_logs = False
    if logs_dir.exists():
        respuesta = input("  Preservar temp/logs/? [S/n]: ").strip().lower()
        preservar_logs = (respuesta != "n")

    if not preservar_trash and not preservar_logs:
        try:
            shutil.rmtree(waio_dir)
            print(f"  [+] Eliminada carpeta completa: {waio_dir}")
            return True
        except Exception as e:
            print(f"  [ERROR] Eliminando {waio_dir}: {e}")
            return False

    for item in list(waio_dir.iterdir()):
        if item.name == "trash" and preservar_trash:
            print(f"  [ ] Preservado: trash/")
            continue
        if item.name == "temp" and preservar_logs:
            temp_dir = item
            for sub in list(temp_dir.iterdir()):
                if sub.name == "logs":
                    print(f"  [ ] Preservado: temp/logs/")
                    continue
                try:
                    if sub.is_dir():
                        shutil.rmtree(sub)
                    else:
                        sub.unlink()
                except Exception as e:
                    print(f"  [ERROR] {sub}: {e}")
            continue
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            print(f"  [+] {item.name}")
        except Exception as e:
            print(f"  [ERROR] {item.name}: {e}")

    try:
        restantes = list(waio_dir.iterdir())
        if not restantes:
            waio_dir.rmdir()
            print(f"  [+] Carpeta .waio vacia eliminada")
    except Exception:
        pass

    return True


def main():
    print("=" * 60)
    print(f"   DESINSTALADOR - {TOOL_NAME} {VERSION}")
    print("=" * 60)
    print()
    print("Esto eliminara:")
    print("  - La carpeta .waio/ (con opcion de preservar trash/ y logs/)")
    print("  - Todas las entradas del menu contextual 06_WAIO")
    print()

    respuesta = input("Continuar? [s/N]: ").strip().lower()
    if respuesta != "s":
        print("Cancelado.")
        return

    waio_dir = get_waio_dir()
    print(f"\nRaiz: {waio_dir}")

    print(f"\n[1/2] Eliminando archivos...")
    remove_files(waio_dir)

    print(f"\n[2/2] Eliminando menu contextual...")
    for reg_path in REG_LOCATIONS:
        remove_menu(reg_path)

    print("\n" + "=" * 60)
    print(f"   DESINSTALACION COMPLETADA - {TOOL_NAME} {VERSION}")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
    finally:
        input("\nPresione Enter para salir...")