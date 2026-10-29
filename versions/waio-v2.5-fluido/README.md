# WAIO v2.5 Fluido - Web AI Orchestrator

WAIO (Web AI Orchestrator) es un motor de automatizacion local y orquestador de comandos disenado para interactuar de forma directa entre modelos de IA (interfaces web/chatbots) y el sistema de archivos local de Windows.

En esta version v2.5 Fluido, se incluye el puente de traduccion de portapapeles TRANSCLIP, borrado seguro hacia la Papelera de Reciclaje, soporte ampliado Unicode UTF-16 y un flujo de trabajo optimizado sin fricciones.

---

## 1. COMPONENTES PRINCIPALES

La instalacion oficial de WAIO v2.5 Fluido consiste en los siguientes archivos centrales:

- **waio_escucha_v2.py**: Motor de escucha en segundo plano. Monitorea la carpeta Downloads por nuevos payloads JSON, ejecuta las acciones de lectura/escritura y genera los reportes de resultado en `output/`.
- **transclip.py**: Puente traductor de comandos simples para el portapapeles. Captura instrucciones sencillas (ej: `dir`, `copy`, `del`) y las envuelve en el formato de transaccion requerido por WAIO.
- **waio_visor.py**: Interfaz grafica (GUI) de monitoreo en tiempo real. Muestra las salidas de ejecucion, copia resultados al portapapeles y permite controlar la ejecucion de TRANSCLIP.
- **kill_waio.py**: Script de detencion rapida que genera la senal `STOP.trigger` para apagar el motor limpiamente.
- **instalador_waio.py** / **instalar_waio.bat**: Scripts de instalacion automatica que copian la suite a `%USERPROFILE%\.waio` y registran los menus contextuales de Windows.
- **desinstalador_waio.py** / **desinstalar_waio.bat**: Scripts de limpieza profunda para eliminar los archivos y las claves del Registro de Windows.
- **iniciar_transclip.bat** / **detener_escucha.bat**: Lanzador y detenedor de TRANSCLIP fuera del menu contextual.
- **PROMPT_WAIO.txt**: Prompt maestro de referencia para la IA (mismo texto que el motor autogenera en `output/`).

---

## 2. REQUISITOS DEL SISTEMA

- **Sistema Operativo**: Windows 10 / Windows 11
- **Python**: Version 3.8 o superior instalada en el PATH del sistema.
- **Librerias externas** (opcional para manejo nativo de papelera):
  ```
  pip install send2trash
  ```
  Si no esta instalada, WAIO usa una carpeta interna `trash/` como respaldo.

---

## 3. INSTALACION Y USO

### Instalacion

1. Ejecuta `instalar_waio.bat` como usuario estandar o administrador.
2. El instalador copiara los scripts a la carpeta oculta `C:\Users\<Usuario>\.waio\` y creara las subcarpetas de trabajo (`logs/`, `output/`, `jsonout/`, `trash/`).
3. Se anadira la opcion **WAIO - Web AI Orchestrator** al menu contextual del clic derecho de Windows en carpetas.

### Ejecucion desde el Menu Contextual

1. Haz clic derecho sobre cualquier carpeta en el Explorador de Windows.
2. Selecciona **WAIO - Web AI Orchestrator**.
3. Elige entre las siguientes opciones:
   - **Iniciar WAIO Aqui**: Lanza el motor de escucha en la carpeta seleccionada y abre el Visor.
   - **TRANSCLIP (WhatsApp bridge)**: Inicia el traductor de portapapeles en segundo plano.
   - **Matar WAIO (solo motor)**: Detiene el motor de ejecucion activo.

### Detencion

Puedes detener el proceso de WAIO de cualquiera de las siguientes formas:

1. **Cerrando la ventana del Visor**: crea automaticamente `STOP.trigger` y notifica al motor su apagado en menos de 2 segundos. Tambien cierra TRANSCLIP si estaba corriendo.
2. **Ejecutando `kill_waio.py`**: genera manualmente la senal de parada.
3. **Desde el menu contextual**: seleccionando **Matar WAIO (solo motor)**.
4. **Para detener solo TRANSCLIP**: doble clic en `detener_escucha.bat`, o boton **CERRAR TRANSCLIP** en el visor.

---

## 4. TRANSCLIP (Nuevo en v2.5)

TRANSCLIP es un puente de portapapeles que se ejecuta como proceso independiente. Monitorea el portapapeles cada 500 ms y, cuando detectas un JSON copiado, lo procesa automaticamente segun tres casos:

1. **JSON WAIO completo** (con `transaccion_id` + `acciones`): pasa directo a Downloads sin modificaciones.
2. **JSON con solo `comando`** (ej: `{"comando": "dir"}`): lo envuelve en una transaccion WAIO completa y lo guarda.
3. **JSON externo sin `comando`**: lo guarda como archivo en `externos/tx_xxx.json` mediante `crear_archivo`.

El texto plano (no-JSON) se ignora silenciosamente.

Esto permite que la IA genere comandos simples sin tener que armar el payload completo.

**Formas de iniciar TRANSCLIP:**
- Boton **INICIAR TRANSCLIP** en el visor (se convierte en **CERRAR TRANSCLIP** cuando esta activo).
- Doble clic en `iniciar_transclip.bat`.
- Desde el menu contextual: **TRANSCLIP (WhatsApp bridge)**.

TRANSCLIP usa un archivo `transclip.lock` con su PID para evitar instancias duplicadas.

---

## 5. ESTRUCTURA DEL PAYLOAD JSON

Para que el motor procese instrucciones, la IA debe generar un archivo JSON con la siguiente estructura estricta:

```json
{
  "transaccion_id": "tx_ejemplo_001",
  "acciones": [
    {
      "comando": "crear_carpeta",
      "ruta": "mi_proyecto"
    },
    {
      "comando": "crear_archivo",
      "ruta": "mi_proyecto/config.json",
      "contenido": "{\"version\": \"1.0\"}"
    },
    {
      "comando": "listar_directorio",
      "ruta": "mi_proyecto"
    }
  ]
}
```

**Reglas estrictas:**
- Siempre usa `transaccion_id` + `acciones`.
- Nunca uses `{"comando": "..."}` solo (eso es para TRANSCLIP, no para el motor).
- Nunca uses caracteres de control como `\x00` o `\x01` dentro de strings. Si necesitas datos binarios, codificalos en Base64.

---

## 6. COMANDOS DISPONIBLES (11)

### Comandos de Escritura

- **crear_archivo** (ruta, contenido): Crea o sobrescribe un archivo de texto.
- **crear_carpeta** (ruta): Crea una estructura de directorios.
- **eliminar_archivo** (ruta): Envia un archivo a la Papelera de Reciclaje.
- **eliminar_carpeta** (ruta): Envia una carpeta a la Papelera de Reciclaje.
- **mover_archivo** (origen, destino): Mueve o renombra archivos y directorios.
- **copiar_archivo** (origen, destino): Duplica archivos en la ruta destino.

### Comandos de Lectura

- **listar_directorio** (ruta): Devuelve el listado de archivos y carpetas.
- **leer_archivo** (ruta, limite?): Lee el contenido de un archivo.
  - Por defecto: limite de 500,000 caracteres.
  - Lectura completa (hasta 10MB): `"limite": 0`.
- **existe_archivo** (ruta): Devuelve True o False segun la existencia del elemento.
- **obtener_tamano** (ruta): Devuelve el tamano en bytes de un archivo o carpeta.
- **fecha_modificacion** (ruta): Devuelve la ultima fecha y hora de modificacion.

---

## 7. POLITICA DE SEGURIDAD

- **Rutas Relativas Unicamente**: WAIO bloquea el uso de rutas absolutas (ej. `C:\Windows`) o navegaciones tipo parent-directory (`..`). Las rutas absolutas se rechazan antes de intentar resolverlas.
- **Aislamiento**: Todas las operaciones se ejecutan estrictamente dentro del directorio de trabajo activo especificado al iniciar la herramienta.
- **Borrado Seguro**: Los comandos de eliminacion utilizan la Papelera de Reciclaje de Windows (via `send2trash`) o una carpeta interna de respaldo (`trash/`), evitando la perdida accidental irreversible de datos.
- **Escritura Atomica**: Los JSON de resultado se escriben primero a un archivo `.tmp` y luego se renombran. Esto evita archivos corruptos si el proceso muere a mitad de la escritura.
- **Portapapeles Unicode**: Los resultados se copian usando `ctypes` con UTF-16 nativo, garantizando compatibilidad total con caracteres especiales. Si falla, hay un fallback al comando `clip`.
- **Auditoria de Logs**: Cada transaccion se registra en `%USERPROFILE%\.waio\logs\waio_escucha_[timestamp].log`.
