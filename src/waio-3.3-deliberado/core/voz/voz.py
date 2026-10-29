import subprocess
import sys
import os
import json
import shutil
import ast
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CARPETA_ORIGEN = os.path.join(BASE_DIR, "waiovoz", "mensajescreados")
CARPETA_DESTINO = os.path.join(BASE_DIR, "waiovoz", "mensajesleidos")
VOZS_SCRIPT = os.path.join(BASE_DIR, "vozs.py")
LOCK_FILE = os.path.join(BASE_DIR, "waiovoz", "vozs.lock")

def respuesta(status, **kwargs):
    r = {
        "herramienta": "voz",
        "version": "4.2.0",
        "status": status,
        "timestamp": datetime.now().isoformat()
    }
    r.update(kwargs)
    return r

def encolar_mensaje(texto, voz_nombre=None, velocidad=None, volumen=None):
    try:
        if not os.path.exists(CARPETA_ORIGEN):
            os.makedirs(CARPETA_ORIGEN)
        if not os.path.exists(CARPETA_DESTINO):
            os.makedirs(CARPETA_DESTINO)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        nombre_archivo = f"msg_{timestamp}.json"
        ruta_origen = os.path.join(CARPETA_ORIGEN, nombre_archivo)
        ruta_destino = os.path.join(CARPETA_DESTINO, nombre_archivo)
        datos = {"texto": texto, "timestamp": timestamp}
        if voz_nombre:
            datos["voz_nombre"] = voz_nombre
        if velocidad is not None:
            datos["velocidad"] = velocidad
        if volumen is not None:
            datos["volumen"] = volumen
        with open(ruta_origen, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2)
        shutil.copy(ruta_origen, ruta_destino)
        return ruta_origen, ruta_destino
    except Exception as e:
        return None, str(e)

def main():
    args_list = sys.argv[1:]
    
    # Si viene como --parametros, expandir
    if len(args_list) > 1 and args_list[0] == '--parametros':
        try:
            expandido = ast.literal_eval(args_list[1])
            if isinstance(expandido, list):
                args_list = [str(x) for x in expandido]
            elif isinstance(expandido, str):
                args_list = [expandido]
            else:
                args_list = []
        except:
            args_list = []
    
    texto = ""
    voz_nombre = None
    velocidad = None
    volumen = None
    
    for i, arg in enumerate(args_list):
        if arg == '--texto' and i + 1 < len(args_list):
            texto = args_list[i + 1]
        elif arg == '--voz_nombre' and i + 1 < len(args_list):
            voz_nombre = args_list[i + 1]
        elif arg == '--velocidad' and i + 1 < len(args_list):
            try:
                velocidad = int(args_list[i + 1])
            except:
                pass
        elif arg == '--volumen' and i + 1 < len(args_list):
            try:
                volumen = int(args_list[i + 1])
            except:
                pass
    
    if not texto:
        print(json.dumps(respuesta("error", codigo="TEXTO_VACIO", mensaje="El texto esta vacio"), ensure_ascii=True))
        sys.exit(1)
    
    ruta_origen, ruta_destino = encolar_mensaje(texto, voz_nombre, velocidad, volumen)
    if not ruta_origen:
        print(json.dumps(respuesta("error", codigo="ENCOLADO_FALLIDO", mensaje=f"No se pudo encolar: {ruta_destino}"), ensure_ascii=True))
        return
    
    procesador_activo = os.path.exists(LOCK_FILE)
    lanzado = False
    if not procesador_activo:
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            subprocess.Popen([sys.executable, VOZS_SCRIPT], creationflags=creationflags, close_fds=True)
            lanzado = True
        except Exception as e:
            print(json.dumps(respuesta("error", codigo="PROCESADOR_ERROR", mensaje=f"No se pudo lanzar el procesador: {e}"), ensure_ascii=True))
            return
    
    print(json.dumps(respuesta(
        "ok",
        encolado=True,
        archivo=os.path.basename(ruta_origen),
        procesador_lanzado=lanzado,
        mensaje="Encolado y procesando en segundo plano." if lanzado else "Encolado. Procesador ya activo."
    ), ensure_ascii=True))

if __name__ == "__main__":
    main()
