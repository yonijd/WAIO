import os
import sys
import subprocess
import shutil

def instalar_si_falta(modulo, paquete=None):
    if paquete is None:
        paquete = modulo
    try:
        __import__(modulo)
        return True
    except ImportError:
        print(f"[INSTALANDO] {paquete}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", paquete])
        try:
            __import__(modulo)
            return True
        except ImportError:
            return False

def detectar_tipo_archivo(ruta):
    ext = os.path.splitext(ruta)[1].lower()
    tipos = {
        '.pdf': 'PDF',
        '.docx': 'Word',
        '.xlsx': 'Excel',
        '.pptx': 'PowerPoint',
        '.txt': 'Texto',
        '.py': 'Python',
        '.json': 'JSON',
        '.xml': 'XML',
        '.html': 'HTML',
        '.htm': 'HTML',
        '.css': 'CSS',
        '.js': 'JavaScript',
        '.csv': 'CSV',
        '.md': 'Markdown',
        '.yaml': 'YAML',
        '.yml': 'YAML',
        '.toml': 'TOML',
        '.jpg': 'Imagen',
        '.jpeg': 'Imagen',
        '.png': 'Imagen',
        '.gif': 'Imagen',
        '.bmp': 'Imagen',
        '.webp': 'Imagen',
        '.ico': 'Imagen',
        '.mp3': 'Audio',
        '.wav': 'Audio',
        '.flac': 'Audio',
        '.mp4': 'Video',
        '.avi': 'Video',
        '.mkv': 'Video',
        '.mov': 'Video',
        '.zip': 'ZIP',
        '.rar': 'RAR',
        '.7z': '7Z',
        '.exe': 'Ejecutable',
        '.msi': 'Instalador',
        '.bat': 'Script BAT',
        '.ps1': 'Script PowerShell',
        '.sh': 'Script Shell',
    }
    return tipos.get(ext, 'Desconocido')

def abrir_archivo(ruta):
    if not os.path.exists(ruta):
        return f"[ERROR] Archivo no existe: {ruta}"
    
    if os.path.isdir(ruta):
        return f"[ERROR] Es una carpeta: {ruta}. Usa abrir_programa.exe para carpetas."
    
    tipo = detectar_tipo_archivo(ruta)
    
    try:
        os.startfile(ruta)
        return f"[OK] {tipo} abierto: {ruta}"
    except Exception as e:
        return f"[ERROR] No se pudo abrir {ruta}: {str(e)}"

def main():
    if len(sys.argv) < 2:
        print("[ERROR] Debes especificar un archivo")
        print("  Ejemplo: abrir_archivo.py documento.pdf")
        print("  Ejemplo: abrir_archivo.py imagen.jpg")
        return
    
    ruta = sys.argv[1]
    resultado = abrir_archivo(ruta)
    print(resultado)

if __name__ == "__main__":
    main()