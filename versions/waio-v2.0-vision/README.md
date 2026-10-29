# WAIO (Web AI Orchestrator) - v2.0 Vision

WAIO (Web AI Orchestrator) v2.0 Vision es un marco de trabajo seguro y ligero para Windows que actua como puente de automatizacion entre modelos de Inteligencia Artificial (interfaces web o locales) y tu sistema de archivos local. Permite a la IA ejecutar operaciones de lectura, escritura, gestion de archivos y diagnostico en tu PC de forma completamente estructurada y controlada mediante cargas JSON.

---

## Caracteristicas Principales

- Orquestacion mediante JSON: Ejecucion secuencial de comandos mediante transacciones estructuradas (transaccion_id y acciones).
- Seguridad por Aislamiento: Operacion restringida a rutas relativas dentro del directorio de trabajo (WORK_DIR). Prohibicion estricta de rutas absolutas y navegacion hacia atras (..).
- Monitoreo en Tiempo Real: Incluye una interfaz grafica integrada (waio_visor.py) en Tkinter que visualiza en verde la salida de las transacciones y permite copiar los resultados al portapapeles. El motor lo lanza automaticamente al arrancar si no esta corriendo.
- Escucha Automatica: Detecta automaticamente los archivos JSON descargados en la carpeta Downloads / Descargas del usuario.
- Integracion con el Sistema: Menu contextual nativo de Windows (Clic derecho > WAIO - Web AI Orchestrator) para iniciar el motor en cualquier carpeta.
- Mecanismo de Parada de Emergencia (Kill Switch): Creacion y deteccion de STOP.trigger para apagar instancias previas o detener el motor de forma instantanea.

---

## Requisitos

- Windows (probado en Windows 10/11).
- Python 3.x instalado y disponible en el PATH.
- tkinter (viene incluido con la instalacion estandar de Python en Windows).

---

## Estructura del Proyecto

waio-v2.0-vision/
|
|-- waio_escucha_v2.py       # Motor principal de escucha, validacion y ejecucion de comandos JSON.
|-- waio_visor.py            # Interfaz grafica (GUI) de monitoreo en tiempo real.
|-- kill_waio.py             # Script de apagado rapido (genera STOP.trigger para detener el motor).
|-- instalador_waio.py       # Script de registro en el Registro de Windows (HKEY_CURRENT_USER).
|-- instalar_waio.bat        # Ejecutable Batch del instalador.
|-- desinstalador_waio.py    # Script de limpieza de archivos en %USERPROFILE%\.waio y registro.
|-- desinstalar_waio.bat     # Ejecutable Batch del desinstalador.
|-- promt maestro.txt        # Prompt maestro de referencia para la IA (mismo texto que el motor autogenera).
`-- README.md                # Este archivo.

---

## Instalacion

1. Descarga o clona la carpeta "waio-v2.0-vision".
2. Haz doble clic en instalar_waio.bat.
3. El instalador copiara los archivos esenciales a la carpeta global %USERPROFILE%\.waio y registrara las entradas en el registro de Windows para carpetas y fondo de pantalla del explorador.

Al finalizar, tendras disponible el menu contextual al hacer clic derecho sobre cualquier carpeta.

---

## Desinstalacion

1. Haz doble clic en desinstalar_waio.bat.
2. El desinstalador eliminara la carpeta %USERPROFILE%\.waio y las entradas del menu contextual en el registro de Windows.

---

## Mapeo de Comandos Disponibles (11 Comandos)

El motor admite 11 comandos principales con sus respectivos alias en ingles y espanol:

Comandos de Escritura:
- crear_archivo (alias: create_file, write, write_file): Crea un archivo con el contenido especificado.
- crear_carpeta (alias: create_folder, mkdir): Crea una estructura de carpetas.
- eliminar_archivo (alias: delete_file, rm, del): Elimina un archivo especifico.
- eliminar_carpeta (alias: delete_folder, rmdir, rd): Elimina una carpeta y su contenido.
- mover_archivo (alias: move, mv, rename): Mueve o renombra archivos o carpetas.
- copiar_archivo (alias: copy, cp): Copia un archivo a una nueva ruta.

Comandos de Lectura (Siempre devuelven respuesta JSON):
- listar_directorio (alias: list_dir, ls): Muestra el contenido del directorio.
- leer_archivo (alias: read_file, read): Lee el contenido de un archivo (limite por defecto: 100000 caracteres; limite: 0 para archivo completo hasta 10MB).
- existe_archivo (alias: exists, check): Retorna True o False segun la existencia de la ruta.
- obtener_tamano (alias: size, get_size, obtener_tamaño): Devuelve el tamano en bytes del archivo o carpeta.
- fecha_modificacion (alias: modified, mtime, fecha_modificación): Devuelve la fecha de ultima modificacion (YYYY-MM-DD HH:MM:SS).

---

## Formato del Payload JSON

Para enviar ordenes a WAIO, la IA debe generar un archivo con extension .json en la carpeta de Descargas del sistema con la siguiente estructura:

{
  "transaccion_id": "tx_ejemplo_001",
  "acciones": [
    {
      "comando": "listar_directorio",
      "ruta": "."
    },
    {
      "comando": "crear_archivo",
      "ruta": "notas/resumen.txt",
      "contenido": "Texto generado por la IA",
      "confirmar": true
    }
  ]
}

---

## Detencion del Motor

Puedes detener el proceso de WAIO de cualquiera de las siguientes formas:
1. Cerrando la ventana del Visor (waio_visor.py): Creara automaticamente el archivo STOP.trigger notificando al motor su apague en menos de 2 segundos.
2. Ejecutando kill_waio.py: Genera manualmente la senal de parada.
3. Mediante el menu contextual: Seleccionando "Matar WAIO (solo motor)".

---

## Politicas de Seguridad

- Seguridad de Rutas: Cualquier intento de acceder a rutas fuera del directorio de trabajo (ej. C:\Windows, D:\, ../) sera bloqueado inmediatamente e informado en el log de auditoria.
- Auditoria de Logs: Cada transaccion se registra en %USERPROFILE%\.waio\logs\waio_escucha_[timestamp].log.
- Portapapeles: Las salidas de comandos se copian de forma transparente al portapapeles de Windows para una rapida interaccion con la IA.