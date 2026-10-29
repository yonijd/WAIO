import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from collections import Counter

__version__ = "1.0.0"

def format_size(b):
    if b < 1024:
        return f"{b} B"
    elif b < 1024**2:
        return f"{b/1024:.2f} KB"
    elif b < 1024**3:
        return f"{b/1024**2:.2f} MB"
    else:
        return f"{b/1024**3:.2f} GB"

def get_top_extensions(files, top=4):
    exts = [Path(f).suffix.lower() for f in files if Path(f).suffix]
    counted = Counter(exts).most_common(top)
    return " ".join([f"{e}({n})" for e, n in counted])

def scan_deep(root_path):
    root = Path(root_path)
    sections = []
    global_files = 0
    global_dirs = 0
    global_size = 0

    try:
        top_entries = sorted(root.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
    except Exception as e:
        return [], 0, 0, 0, str(e)

    for entry in top_entries:
        if entry.is_dir():
            global_dirs += 1
            sec_files = []
            sec_size = 0
            sec_dirs = 0

            try:
                for sub_root, sub_dirs, sub_files in os.walk(entry):
                    sec_dirs += len(sub_dirs)
                    for fname in sub_files:
                        fpath = Path(sub_root) / fname
                        try:
                            stat = fpath.stat()
                            fsize = stat.st_size
                            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                            sec_files.append({
                                "name": fname,
                                "ext": fpath.suffix.lower() if fpath.suffix else "FILE",
                                "size": fsize,
                                "mtime": mtime
                            })
                            sec_size += fsize
                            global_size += fsize
                            global_files += 1
                        except Exception:
                            continue
            except Exception:
                pass

            top_exts = get_top_extensions([f["name"] for f in sec_files])
            sections.append({
                "name": entry.name,
                "is_dir": True,
                "files": sec_files,
                "size": sec_size,
                "subdirs": sec_dirs,
                "top_exts": top_exts
            })

        elif entry.is_file():
            try:
                stat = entry.stat()
                fsize = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                sections.append({
                    "name": entry.name,
                    "is_dir": False,
                    "ext": entry.suffix.lower() if entry.suffix else "FILE",
                    "size": fsize,
                    "mtime": mtime
                })
                global_size += fsize
                global_files += 1
            except Exception:
                continue

    return sections, global_files, global_dirs, global_size, None

def build_report(root_path, sections, global_files, global_dirs, global_size, elapsed):
    root = Path(root_path)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    W = 100
    lines = []

    lines.append("=" * W)
    lines.append(f"   REPORTE PROFUNDO PARA IA - DEEPLOG v{__version__}")
    lines.append("=" * W)
    lines.append(f"  Carpeta raiz : {root.absolute()}")
    lines.append(f"  Fecha/Hora   : {now}")
    lines.append(f"  Total global : {global_files:,} arch | {global_dirs:,} carpetas | {format_size(global_size)}")

    all_files_flat = []
    for s in sections:
        if s["is_dir"]:
            all_files_flat += [f["name"] for f in s["files"]]
        else:
            all_files_flat.append(s["name"])
    lines.append(f"  Tipos dom.   : {get_top_extensions(all_files_flat, 6)}")
    lines.append(f"  Tiempo scan  : {elapsed:.3f} seg")
    lines.append("=" * W)

    lines.append("")
    lines.append("  [ESTRUCTURA]")
    lines.append(f"  {'CARPETA/ARCHIVO':<45} {'ARCH':>6}  {'TAMANO':>10}  TIPOS DOMINANTES")
    lines.append("  " + "-" * (W - 2))

    for s in sections:
        if s["is_dir"]:
            name_str = f"{s['name']}/"
            if len(name_str) > 44:
                name_str = name_str[:41] + ".../"
            lines.append(f"  {name_str:<45} {len(s['files']):>6}  {format_size(s['size']):>10}  {s['top_exts']}")
        else:
            name_str = s["name"]
            if len(name_str) > 44:
                name_str = name_str[:41] + "..."
            lines.append(f"  {name_str:<45} {'':>6}  {format_size(s['size']):>10}  {s['ext']}")

    lines.append("  " + "-" * (W - 2))
    lines.append("")
    lines.append("=" * W)
    lines.append("  [DETALLE POR CARPETA]")
    lines.append("=" * W)

    wn = 46
    wt = 6
    ws = 10
    wm = 16

    for s in sections:
        if not s["is_dir"]:
            continue
        lines.append("")
        lines.append(f"  --- {s['name']} ---  ({len(s['files'])} arch | {s['subdirs']} subcarpetas | {format_size(s['size'])})")
        lines.append(f"  {'NOMBRE':<{wn}}  {'TIPO':^{wt}}  {'TAMANO':>{ws}}  {'MODIFICADO':^{wm}}")
        lines.append("  " + "-" * (wn + wt + ws + wm + 8))

        for f in sorted(s["files"], key=lambda x: (x["ext"], x["name"].lower())):
            name = f["name"]
            if len(name) > wn - 3:
                name = name[:wn - 6] + "..."
            ext = f["ext"][:wt] if len(f["ext"]) > wt else f["ext"]
            lines.append(f"  {name:<{wn}}  {ext:^{wt}}  {format_size(f['size']):>{ws}}  {f['mtime']:^{wm}}")

        lines.append("  " + "-" * (wn + wt + ws + wm + 8))

    lines.append("")
    lines.append("=" * W)
    lines.append(f"  FIN DEL REPORTE - {global_files:,} archivos en {global_dirs:,} carpetas - {format_size(global_size)}")
    lines.append("=" * W)

    return "\n".join(lines)

def main():
    parser = argparse.ArgumentParser(description='Escaneo profundo de carpetas para IA')
    parser.add_argument('--ruta', required=True, help='Ruta de la carpeta a escanear')
    parser.add_argument('--guardar_log', action='store_true', help='Guardar log en .ialogpack/logs/')
    args = parser.parse_args()

    target = Path(args.ruta)
    if not target.is_dir():
        print(f"Error: '{args.ruta}' no es una carpeta valida.")
        return

    start = time.time()
    sections, gf, gd, gs, err = scan_deep(target)
    elapsed = time.time() - start

    if err:
        print(f"Error al escanear: {err}")
        return

    report = build_report(target, sections, gf, gd, gs, elapsed)
    print(report)

    if args.guardar_log:
        try:
            log_dir = Path(os.environ["USERPROFILE"]) / ".ialogpack" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            folder_clean = "".join([c if c.isalnum() else "_" for c in target.name]) if target.name else "raiz"
            log_name = f"deeplog_{folder_clean}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
            log_path = log_dir / log_name
            with open(log_path, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"\n[+] Log guardado: {log_path}")
        except Exception as e:
            print(f"\n[!] No se pudo guardar log: {e}")

if __name__ == "__main__":
    main()