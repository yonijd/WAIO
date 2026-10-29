# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import os
import sys
import ast
import argparse
import subprocess


def obtener_workdir():
    try:
        with open("temp/workdir.txt", "r") as f:
            return f.read().strip()
    except Exception:
        return os.getcwd()


def resolver_ruta(ruta):
    workdir = obtener_workdir()
    if os.path.isabs(ruta):
        return ruta
    return os.path.join(workdir, ruta)


def detectar_tipo_archivo(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    tipos = {
        '.pdf': 'PDF', '.docx': 'Word', '.xlsx': 'Excel', '.pptx': 'PowerPoint',
        '.txt': 'Texto', '.py': 'Python', '.json': 'JSON', '.xml': 'XML',
        '.html': 'HTML', '.htm': 'HTML', '.css': 'CSS', '.js': 'JavaScript',
        '.csv': 'CSV', '.md': 'Markdown', '.yaml': 'YAML', '.yml': 'YAML',
        '.toml': 'TOML', '.jpg': 'Imagen', '.jpeg': 'Imagen', '.png': 'Imagen',
        '.gif': 'Imagen', '.bmp': 'Imagen', '.webp': 'Imagen', '.ico': 'Imagen',
        '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.mp4': 'Video',
        '.avi': 'Video', '.mkv': 'Video', '.mov': 'Video', '.zip': 'ZIP',
        '.rar': 'RAR', '.7z': '7Z', '.exe': 'Ejecutable', '.msi': 'Instalador',
        '.bat': 'Script BAT', '.ps1': 'Script PowerShell', '.sh': 'Script Shell',
    }
    return tipos.get(ext, 'Desconocido')


def abrir_archivo(ruta):
    ruta_resuelta = resolver_ruta(ruta)

    if not os.path.exists(ruta_resuelta):
        return f"[ERROR] Archivo no existe: {ruta_resuelta}"

    if os.path.isdir(ruta_resuelta):
        return f"[ERROR] Es una carpeta: {ruta_resuelta}. Usa abrir_programa para carpetas."

    tipo = detectar_tipo_archivo(ruta_resuelta)

    try:
        os.startfile(ruta_resuelta)
        return f"[OK] {tipo} abierto: {ruta_resuelta}"
    except Exception as e:
        return f"[ERROR] No se pudo abrir {ruta_resuelta}: {str(e)}"


def preparar_args():
    """Normaliza los argumentos que llegan desde WAIO.

    WAIO puede enviar:
      1. --ruta <archivo>            (forma normal, el motor traduce claves)
      2. --parametros '["<archivo>"]' (forma legacy)
      3. <archivo>                    (posicional suelto)
    """
    args_list = sys.argv[1:]

    # Caso 2: forma legacy con --parametros
    if len(args_list) >= 2 and args_list[0] == '--parametros':
        try:
            expandido = ast.literal_eval(args_list[1])
            if isinstance(expandido, list):
                args_list = [str(x) for x in expandido]
            else:
                args_list = [str(expandido)]
        except Exception:
            args_list = []

    # Caso 3: posicional suelto sin flag
    if args_list and not args_list[0].startswith('--'):
        args_list = ['--ruta', args_list[0]] + args_list[1:]

    return args_list


def main():
    parser = argparse.ArgumentParser(
        description='Abre un archivo con su programa asociado en Windows.'
    )
    parser.add_argument(
        '--ruta',
        required=True,
        help='Ruta del archivo a abrir (relativa al workdir o absoluta)'
    )
    parser.add_argument(
        '--parametros',
        nargs='*',
        help='Compatibilidad legacy: lista de argumentos posicionales'
    )

    args = parser.parse_args(preparar_args())

    resultado = abrir_archivo(args.ruta)
    print(resultado)


if __name__ == "__main__":
    main()