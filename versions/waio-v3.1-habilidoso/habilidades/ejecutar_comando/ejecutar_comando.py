import subprocess
import sys
import re
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

    if len(sys.argv) < 2:
        print("USO: ejecutar_comando.py <comando> [--timeout segundos]")
        return

    if "--timeout" in sys.argv:
        try:
            idx = sys.argv.index("--timeout")
            TIMEOUT = int(sys.argv[idx + 1])
            sys.argv.pop(idx)
            sys.argv.pop(idx)
        except (ValueError, IndexError):
            print("[ERROR] --timeout debe ser un numero")
            return

    comando = " ".join(sys.argv[1:])

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