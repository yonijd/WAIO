import os
import sys
import argparse
import time
import subprocess
import platform
import shutil
from pathlib import Path
from datetime import datetime

__version__ = "1.0.2"
W = 100

def run_cmd(cmd, enc=None):
    try:
        r = subprocess.run(cmd, capture_output=True, shell=True, timeout=10)
        encoding = enc if enc else "utf-8"
        return r.stdout.decode(encoding, errors="replace").strip()
    except Exception:
        return ""

def run_ps(cmd, enc=None):
    full = f'powershell -NoProfile -Command "{cmd}"'
    return run_cmd(full, enc)

def format_bytes(b):
    try:
        b = int(b)
        if b < 1024**2:   return f"{b/1024:.2f} KB"
        elif b < 1024**3: return f"{b/1024**2:.2f} MB"
        else:             return f"{b/1024**3:.2f} GB"
    except Exception:
        return "N/D"

def section(title):
    return ["", "=" * W, f"  [{title}]", "=" * W]

def build_report():
    lines = []
    now = datetime.now()

    lines.append("=" * W)
    lines.append(f"   REPORTE SISTEMA v{__version__} PARA IA - SYSLOG")
    lines.append("=" * W)
    lines.append(f"  Fecha/Hora   : {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Equipo       : {platform.node()}")
    lines.append("=" * W)

    # OS
    lines += section("SISTEMA OPERATIVO")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                             r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        def rq(k, v, d="N/D"):
            try:    return winreg.QueryValueEx(k, v)[0]
            except: return d
        prod = rq(key, "ProductName")
        display = rq(key, "DisplayVersion")
        build = rq(key, "CurrentBuildNumber")
        ubr = rq(key, "UBR", 0)
        winreg.CloseKey(key)
        lines.append(f"  Producto     : {prod}")
        lines.append(f"  Version      : {display}  (Build {build}.{ubr})")
    except Exception as e:
        lines.append(f"  OS           : {platform.version()} [{e}]")
    lines.append(f"  Arquitectura : {platform.machine()}")
    locale_out = run_ps("(Get-Culture).Name")
    lines.append(f"  Idioma/Locale: {locale_out if locale_out else 'N/D'}")
    tz = run_ps("(Get-TimeZone).Id")
    lines.append(f"  Zona horaria : {tz if tz else 'N/D'}")

    # USUARIO
    lines += section("USUARIO Y RUTAS")
    lines.append(f"  Usuario      : {os.environ.get('USERNAME', 'N/D')}")
    lines.append(f"  USERPROFILE  : {os.environ.get('USERPROFILE', 'N/D')}")
    lines.append(f"  APPDATA      : {os.environ.get('APPDATA', 'N/D')}")
    lines.append(f"  LOCALAPPDATA : {os.environ.get('LOCALAPPDATA', 'N/D')}")
    lines.append(f"  TEMP         : {os.environ.get('TEMP', 'N/D')}")

    # CPU
    lines += section("CPU")
    try:
        cpu_name = run_ps("(Get-CimInstance Win32_Processor).Name")
        cpu_cores = run_ps("(Get-CimInstance Win32_Processor).NumberOfCores")
        cpu_threads = run_ps("(Get-CimInstance Win32_Processor).NumberOfLogicalProcessors")
        cpu_mhz = run_ps("(Get-CimInstance Win32_Processor).MaxClockSpeed")
        ghz = f"{int(cpu_mhz)/1000:.2f} GHz" if cpu_mhz.isdigit() else "N/D"
        lines.append(f"  Modelo       : {cpu_name}")
        lines.append(f"  Nucleos      : {cpu_cores} fisicos / {cpu_threads} logicos")
        lines.append(f"  Velocidad max: {ghz}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # RAM
    lines += section("MEMORIA RAM")
    try:
        import ctypes as ct
        class MEMSTATUS(ct.Structure):
            _fields_ = [("dwLength",ct.c_ulong),("dwMemoryLoad",ct.c_ulong),
                        ("ullTotalPhys",ct.c_ulonglong),("ullAvailPhys",ct.c_ulonglong),
                        ("ullTotalPageFile",ct.c_ulonglong),("ullAvailPageFile",ct.c_ulonglong),
                        ("ullTotalVirtual",ct.c_ulonglong),("ullAvailVirtual",ct.c_ulonglong),
                        ("ullAvailExtendedVirtual",ct.c_ulonglong)]
        ms = MEMSTATUS()
        ms.dwLength = ct.sizeof(ms)
        ct.windll.kernel32.GlobalMemoryStatusEx(ct.byref(ms))
        total = ms.ullTotalPhys
        avail = ms.ullAvailPhys
        used = total - avail
        lines.append(f"  Total        : {format_bytes(total)}")
        lines.append(f"  En uso       : {format_bytes(used)} ({ms.dwMemoryLoad}%)")
        lines.append(f"  Disponible   : {format_bytes(avail)}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # DISCOS
    lines += section("DISCOS")
    try:
        lines.append(f"  {'UNIDAD':<8} {'TIPO':<12} {'TOTAL':>10} {'USADO':>10} {'LIBRE':>10} {'USO%':>5}  ETIQUETA")
        lines.append("  " + "-" * 70)
        drives_raw = run_ps(
            "Get-CimInstance Win32_LogicalDisk | "
            "Select-Object DeviceID,DriveType,Size,FreeSpace,VolumeName | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        type_map = {"2":"Removible","3":"Local","4":"Red","5":"CD/DVD","6":"RAM disk"}
        for line in drives_raw.splitlines()[1:]:
            parts = [p.strip('"') for p in line.split(',')]
            if len(parts) < 5: continue
            dev, dtype, size, free, label = parts[0],parts[1],parts[2],parts[3],parts[4]
            if not size or size == '0': continue
            s = int(size); f = int(free) if free else 0
            u = s - f
            pct_d = int(u * 100 / s) if s else 0
            tname = type_map.get(dtype, dtype)
            lines.append(f"  {dev:<8} {tname:<12} {format_bytes(s):>10} {format_bytes(u):>10} {format_bytes(f):>10} {pct_d:>4}%  {label}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # GPU
    lines += section("GPU")
    try:
        gpu_raw = run_ps(
            "Get-CimInstance Win32_VideoController | "
            "Select-Object Name,AdapterRAM,DriverVersion | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        rows = [l for l in gpu_raw.splitlines()[1:] if l.strip()]
        if rows:
            for row in rows:
                parts = [p.strip('"') for p in row.split(',')]
                if len(parts) < 3: continue
                name, vram, driver = parts[0], parts[1], parts[2]
                vram_str = format_bytes(vram) if vram.isdigit() else "N/D"
                lines.append(f"  Nombre       : {name}")
                lines.append(f"  VRAM         : {vram_str}")
                lines.append(f"  Driver       : {driver}")
                lines.append("")
        else:
            lines.append("  No se detecto GPU")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # AUDIO
    lines += section("AUDIO")
    try:
        audio_raw = run_ps(
            "Get-CimInstance Win32_SoundDevice | "
            "Select-Object Name,Status | "
            "ConvertTo-Csv -NoTypeInformation"
        )
        rows = [l for l in audio_raw.splitlines()[1:] if l.strip()]
        if rows:
            for row in rows:
                parts = [p.strip('"') for p in row.split(',')]
                name = parts[0] if len(parts) > 0 else "N/D"
                status = parts[1] if len(parts) > 1 else "N/D"
                lines.append(f"  {name} [{status}]")
        else:
            lines.append("  No se detecto dispositivo de audio")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # PYTHON
    lines += section("PYTHON")
    try:
        lines.append(f"  Version      : {platform.python_version()}")
        lines.append(f"  Ejecutable   : {sys.executable}")
        lines.append(f"  Arquitectura : {platform.architecture()[0]}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # CMD
    lines += section("CMD / CONSOLA")
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                              r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
        build = winreg.QueryValueEx(key, "CurrentBuildNumber")[0]
        ubr = winreg.QueryValueEx(key, "UBR")[0]
        winreg.CloseKey(key)
        cmd_ver = f"Microsoft Windows [Version 10.0.{build}.{ubr}]"
    except Exception:
        cmd_ver = platform.version()
    lines.append(f"  CMD Version  : {cmd_ver}")

    # POWERSHELL
    lines += section("POWERSHELL")
    try:
        ps_ver = run_ps("$PSVersionTable.PSVersion.ToString()")
        ps_edition = run_ps("$PSVersionTable.PSEdition")
        ps_policy = run_ps("Get-ExecutionPolicy")
        pwsh_path = shutil.which("pwsh")
        lines.append(f"  Version      : {ps_ver if ps_ver else 'N/D'}")
        lines.append(f"  Edicion      : {ps_edition if ps_edition else 'N/D'}")
        lines.append(f"  Exec. Policy : {ps_policy if ps_policy else 'N/D'}")
        lines.append(f"  PowerShell 7 : {pwsh_path if pwsh_path else 'No instalado'}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # NET FRAMEWORK
    lines += section(".NET FRAMEWORK")
    try:
        import winreg
        net_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SOFTWARE\Microsoft\NET Framework Setup\NDP",
                                   access=winreg.KEY_READ | winreg.KEY_WOW64_32KEY)
        versions = []
        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(net_key, i)
                if subkey_name.startswith("v"):
                    try:
                        subkey = winreg.OpenKey(net_key, subkey_name)
                        ver_val = winreg.QueryValueEx(subkey, "Version")[0]
                        try:    sp_val = winreg.QueryValueEx(subkey, "SP")[0]
                        except: sp_val = 0
                        versions.append(f"{subkey_name}  Version: {ver_val}  SP: {sp_val}")
                        winreg.CloseKey(subkey)
                    except:
                        versions.append(subkey_name)
                i += 1
            except OSError:
                break
        winreg.CloseKey(net_key)
        net_core = run_cmd("dotnet --list-runtimes")
        if versions:
            lines.append("  .NET Framework:")
            for v in versions:
                lines.append(f"    {v}")
        if net_core:
            lines.append("  .NET / .NET Core runtimes:")
            for v in net_core.splitlines():
                lines.append(f"    {v}")
        if not versions and not net_core:
            lines.append("  No se detecto .NET instalado")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    # PATH
    lines += section("PATH (resumen)")
    try:
        path_val = os.environ.get("PATH", "")
        entries = [p.strip() for p in path_val.split(";") if p.strip()]
        lines.append(f"  Total entradas: {len(entries)}")
        keywords = ["python","pip","node","npm","git","java","dotnet","powershell",
                    "cuda","ffmpeg","mingw","cmake","cargo","ruby","perl","go"]
        notable = [e for e in entries if any(k in e.lower() for k in keywords)]
        if notable:
            lines.append("  Entradas notables:")
            for e in notable:
                lines.append(f"    {e}")
    except Exception as e:
        lines.append(f"  Error        : {e}")

    lines.append("")
    lines.append("=" * W)
    lines.append(f"  FIN DEL REPORTE SYSLOG v{__version__} - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("=" * W)

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Reporte completo del sistema')
    parser.add_argument('--guardar_log', action='store_true', help='Guardar log en .ialogpack/logs/')
    args = parser.parse_args()

    print("=" * W)
    print(f"   REPORTE SISTEMA v{__version__} PARA IA - SYSLOG")
    print("=" * W)
    print("  Recopilando informacion del sistema...")
    print("  Por favor espere...\n")

    start = time.time()
    report = build_report()
    elapsed = time.time() - start

    print(report)
    print(f"\n  Tiempo de escaneo: {elapsed:.3f} seg")

    if args.guardar_log:
        try:
            log_dir = Path(os.environ["USERPROFILE"]) / ".ialogpack" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            log_name = f"sys_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            log_path = log_dir / log_name
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n[OK] Log guardado: {log_path}")
        except Exception as e:
            print(f"\n[ERROR] No se pudo guardar log: {e}")

if __name__ == "__main__":
    main()