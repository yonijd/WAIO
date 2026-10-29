# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import ast
import shutil
import argparse
import subprocess


def buscar_programa(nombre):
    ruta = shutil.which(nombre)
    if ruta:
        return ruta
    ruta = shutil.which(f"{nombre}.exe")
    if ruta:
        return ruta

    bases = [
        os.environ.get("ProgramFiles", "C:/Program Files"),
        os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)"),
        os.environ.get("LOCALAPPDATA", "") + "/Programs",
    ]

    for base in bases:
        if not base or not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            try:
                for file in files:
                    if file.lower() == f"{nombre}.exe":
                        return os.path.join(root, file)
            except PermissionError:
                continue

    return None


def preparar_args():
    args_list = sys.argv[1:]

    if len(args_list) >= 2 and args_list[0] == '--parametros':
        try:
            expandido = ast.literal_eval(args_list[1])
            if isinstance(expandido, list):
                args_list = [str(x) for x in expandido]
            else:
                args_list = [str(expandido)]
        except Exception:
            args_list = []

    if args_list and not args_list[0].startswith('--'):
        args_list = ['--programa', args_list[0]] + args_list[1:]

    return args_list


def main():
    parser = argparse.ArgumentParser(
        description='Abre un programa buscando su ejecutable en el sistema.'
    )
    parser.add_argument(
        '--programa',
        required=True,
        help='Nombre del programa a abrir (ej: notepad, calc, aimp, vlc)'
    )
    parser.add_argument(
        '--parametros',
        nargs='*',
        help='Compatibilidad legacy: lista de argumentos posicionales'
    )

    args = parser.parse_args(preparar_args())

    ruta = buscar_programa(args.programa)

    if ruta:
        try:
            subprocess.Popen([ruta], shell=False)
            print(f"[OK] {args.programa} abierto desde: {ruta}")
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            sys.exit(1)
    else:
        print(f"[ERROR] No se encontró: {args.programa}")
        sys.exit(1)


if __name__ == "__main__":
    main()
