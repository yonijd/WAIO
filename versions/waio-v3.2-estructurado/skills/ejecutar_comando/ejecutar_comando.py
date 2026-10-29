# Copyright (c) 2026 Yonijd
# Licensed under the MIT License.

import subprocess
import sys
import re
import ast
import time

COMANDOS_PERMITIDOS = [
    "pip", "python", "dir", "ls", "echo", "type", "findstr", "grep",
    "where", "which", "date", "time", "ver", "systeminfo",
    "ipconfig", "ping", "tracert", "netstat", "tasklist"
]

COMANDOS_PROHIBIDOS = [
    "del", "erase", "rm", "rmdir", "format", "diskpart",
    "shutdown", "restart", "reboot", "taskkill", "kill",
    "reg", "regedit", "sc", "net", "netsh"
]

TIMEOUT = 10

def comando_seguro(comando):
    for prohibido in COMANDOS_PROHIBIDOS:
        if re.search(rf'\b{prohibido}\b', comando, re.IGNORECASE):
            return False, f"Comando prohibido: {prohibido}"

    primer_token = comando.split()[0].lower()
    if primer_token not in COMANDOS_PERMITIDOS:
        if primer_token == "python" and ("-c" in comando or "-m" in comando):
            return True, "OK"
        return False, f"Comando no permitido: {primer_token}"

    if any(c in comando for c in ['>', '&', ';']):
        return False, "Redirecciones no permitidas"

    return True, "OK"

def main():
    global TIMEOUT

    # Parsear manualmente para compatibilidad con WAIO
    args_list = sys.argv[1:]

    # Aceptar --parametros posicional o --comando string
    if len(args_list) >= 2 and args_list[0] == '--parametros':
        try:
            args_list = ast.literal_eval(args_list[1])
        except:
            args_list = []
    elif len(args_list) >= 2 and args_list[0] in ('--comando', '--comando_shell'):
        args_list = [args_list[1]]

    if len(args_list) < 1:
        print("USO: ejecutar_comando <comando> [--timeout segundos]")
        print("  Ejemplo: ejecutar_comando pip list")
        print("  Ejemplo: ejecutar_comando python --version")
        return

    # Buscar timeout en los argumentos
    if "--timeout" in args_list:
        try:
            idx = args_list.index("--timeout")
            TIMEOUT = int(args_list[idx + 1])
            args_list.pop(idx)
            args_list.pop(idx)
        except (ValueError, IndexError):
            print("[ERROR] --timeout debe ser un numero")
            return

    comando = " ".join(args_list)

    seguro, mensaje = comando_seguro(comando)
    if not seguro:
        print(f"[ERROR] {mensaje}")
        return

    print(f"[EJECUTANDO] {comando}")
    print("-" * 50)

    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=TIMEOUT
        )
        if resultado.stdout:
            print(resultado.stdout)
        if resultado.stderr:
            print("[STDERR]", resultado.stderr)
        if resultado.returncode != 0:
            print(f"[CODIGO] {resultado.returncode}")
            if resultado.stderr:
                print(f"[ERROR] {resultado.stderr.strip()}")
    except subprocess.TimeoutExpired:
        print(f"[ERROR] Timeout ({TIMEOUT}s) - Comando: {comando}")
    except Exception as e:
        print(f"[ERROR] {e}")

if __name__ == "__main__":
    main()
