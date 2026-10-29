# WAIO v3.0 Consolidado - Web AI Orchestrator

WAIO (Web AI Orchestrator) es un motor de automatizacion local y orquestador de comandos disenado para interactuar de forma directa entre modelos de IA (interfaces web/chatbots) y el sistema de archivos local de Windows.

La version 3.0 Consolidado es la primera version que se considero lista para publicar. Su foco esta en **corregir los bugs y problemas de seguridad de la version anterior** y en agregar **escucha_output**, un compilador de resultados que elimina la saturacion del portapapeles.

---

## 1. QUE CARACTERIZA A ESTA VERSION

### Correcciones respecto a v2.5

- **Prompt editable**: el prompt de la IA ya no vive dentro del codigo. Ahora se lee desde `.waio/prompt.txt`, que el usuario puede modificar sin tocar Python. El motor lo crea con un valor por defecto si no existe.
- **Motor sin portapapeles**: el motor ya no copia resultados al portapapeles. Esa responsabilidad paso a `escucha_output.py`, que lo hace mejor (compila, agrupa y da contexto).
- **Menu contextual numerado**: las 4 entradas del menu contextual ahora tienen prefijo numerico (`01_`, `02_`, `03_`, `04_`) para garantizar orden fijo.
- **Titulo del visor corregido**: paso de decir `WAIO VISOR V1.0` (bug arrastrado desde v2.0) a `WAIO VISOR 3.0`.
- **Herramientas de diagnostico**: se agregaron `ver_estado.bat` y `limpiar_waio.bat` para inspeccionar y limpiar el sistema.

### Novedad principal

- **`escucha_output.py`**: monitorea la carpeta `output/`, acumula los resultados JSON en un buffer y, tras 5 segundos sin novedades, los compila en un unico bloque con contexto completo (`[N] TX: xxx | Accion X/Y | Comando: xxx`). Ese bloque se copia al portapapeles, listo para pegar en la IA.

### Ademas

- **Nuevo comando `mensaje`**: permite que la IA se comunique directamente sin tocar el sistema de archivos. Total: **12 comandos**.

---

## 2. COMPONENTES PRINCIPALES

La instalacion oficial de WAIO v3.0 Consolidado consiste en los siguientes archivos centrales:

- **waio_escucha.py**: Motor de escucha. Monitorea Downloads, ejecuta los 12 comandos y escribe los resultados en `output/`. Ya no copia al portapapeles.
- **waio_visor.py**: Interfaz grafica (GUI) de monitoreo en tiempo real. Muestra resultados, controla TRANSCLIP y escucha_output, y al cerrarse apaga todos los procesos.
- **transclip.py**: Puente traductor de comandos simples para el portapapeles. Captura instrucciones sencillas y las envuelve en formato WAIO.
- **escucha_output.py**: Compilador de resultados. Agrupa multiples JSONs en un bloque con contexto antes de copiarlos.
- **kill_waio.py**: Detencion rapida del motor (crea `STOP.trigger`).
- **instalador_waio.py** / **instalar_waio.bat**: Instalacion automatica en `%USERPROFILE%\.waio` y registro del menu contextual.
- **desinstalador_waio.py** / **desinstalar_waio.bat**: Limpieza completa de archivos y registro.
- **iniciar_transclip.bat** / **detener_transclip.bat**: Lanzador y detenedor de TRANSCLIP.
- **iniciar_escucha_output.bat** / **detener_escucha_output.bat**: Lanzador y detenedor de escucha_output.
- **ver_estado.bat**: Diagnostico del sistema (procesos, locks, triggers, archivos clave). Guarda un log en `logs/estado_*.log`.
- **limpiar_waio.bat**: Mata todos los procesos WAIO y borra triggers/locks huerfanos.
- **prompt.txt** (generado en `.waio`): Prompt maestro editable por el usuario.
- **PROMPT_WAIO.txt** (en `output/`): Copia del prompt procesado, para referencia.

---

## 3. REQUISITOS DEL SISTEMA

- **Sistema Operativo**: Windows 10 / Windows 11
- **Python**: Version 3.8 o superior instalada en el PATH del sistema.
- **Librerias externas** (opcional para manejo nativo de papelera):
  ```
  pip install send2trash
  ```
  Si no esta instalada, WAIO usa una carpeta interna `trash/` como respaldo.

---

## 4. INSTALACION Y USO

### Instalacion

1. Ejecuta `instalar_waio.bat` como usuario estandar o administrador.
2. El instalador copia los scripts a la carpeta oculta `C:\Users\<Usuario>\.waio\` y crea las subcarpetas de trabajo (`logs/`, `output/`, `jsonout/`, `trash/`).
3. Se anaden 4 entradas al menu contextual del clic derecho de Windows.

### Ejecucion desde el Menu Contextual

Haz clic derecho sobre cualquier carpeta en el Explorador de Windows y selecciona **WAIO - Web AI Orchestrator 3.0**:

- **01 Iniciar WAIO Aqui**: lanza el motor en la carpeta seleccionada y abre el Visor.
- **02 TRANSCLIP (WhatsApp)**: inicia el traductor de portapapeles en segundo plano.
- **03 Escucha Output**: inicia el compilador de resultados manualmente.
- **04 Matar WAIO (motor)**: detiene solo el motor, dejando visor y demas procesos vivos.

Nota: el visor **lanza escucha_output automaticamente** al abrirse, asi que no es necesario iniciarlo a mano salvo que quieras controlarlo por separado.

### Detencion

Puedes detener WAIO de cualquiera de estas formas:

1. **Cerrando el visor**: crea `STOP.trigger`, `TRANSCLIP_STOP.trigger` y `ESCUCHA_STOP.trigger`. Todos los procesos mueren en <2 segundos.
2. **Ejecutando `kill_waio.py`**: crea solo `STOP.trigger` (mata el motor, no el visor).
3. **Desde el menu contextual**: **04 Matar WAIO (motor)**.
4. **Para detener solo TRANSCLIP**: `detener_transclip.bat` o el boton correspondiente en el visor.
5. **Para detener solo escucha_output**: `detener_escucha_output.bat` o el boton correspondiente en el visor.

---

## 5. FLUJO DE TRABAJO

### Secuencia completa (IA con generacion de JSON)

1. Clic derecho en una carpeta → **01 Iniciar WAIO Aqui**.
2. El motor arranca, mata instancias previas y abre el Visor.
3. El Visor lanza escucha_output automaticamente.
4. El motor lee `.waio/prompt.txt`, lo procesa y lo escribe en `output/`.
5. escucha_output detecta el prompt, lo compila y lo copia al portapapeles.
6. Pegas el prompt en la IA (Ctrl+V).
7. La IA genera un JSON y lo guarda en Downloads.
8. El motor detecta el JSON y lo ejecuta.
9. Los resultados se escriben en `.waio/output/`.
10. escucha_output los compila (timeout 5s) y copia el bloque al portapapeles.
11. Pegas el bloque en la IA (Ctrl+V).
12. La IA analiza y genera el siguiente JSON. Repetir desde el paso 7.

### Secuencia alternativa (WhatsApp / IA simple)

1. Usuario abre TRANSCLIP desde el menu contextual.
2. WhatsApp envia `{"comando": "dir"}`.
3. Usuario copia el comando (Ctrl+C).
4. TRANSCLIP lo detecta, lo traduce y guarda el JSON en Downloads.
5. El motor lo detecta y ejecuta (mismo flujo que arriba).

---

## 6. COMANDOS DISPONIBLES (12)

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
- **existe_archivo** (ruta): Devuelve True o False.
- **obtener_tamano** (ruta): Devuelve el tamano en bytes de un archivo o carpeta.
- **fecha_modificacion** (ruta): Devuelve la ultima fecha y hora de modificacion.

### Comando Especial

- **mensaje** (contenido): Envia un mensaje directo a la IA sin tocar el sistema de archivos.

---

## 7. ESTRUCTURA DEL PAYLOAD JSON

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
    },
    {
      "comando": "mensaje",
      "contenido": "Proyecto creado exitosamente"
    }
  ]
}
```

**Reglas estrictas:**
- Siempre usa `transaccion_id` + `acciones`.
- Nunca uses `{"comando": "..."}` solo (eso es para TRANSCLIP).
- Nunca uses caracteres de control como `\x00` o `\x01` dentro de strings. Si necesitas datos binarios, codificalos en Base64.

---

## 8. POLITICA DE SEGURIDAD

- **Rutas Relativas Unicamente**: WAIO bloquea el uso de rutas absolutas (ej. `C:\Windows`) o navegaciones tipo parent-directory (`..`). Las rutas absolutas se rechazan antes de intentar resolverlas.
- **Aislamiento**: Todas las operaciones se ejecutan estrictamente dentro del directorio de trabajo activo.
- **Borrado Seguro**: Los comandos de eliminacion usan la Papelera de Reciclaje de Windows (via `send2trash`) o una carpeta interna (`trash/`), evitando perdida irreversible.
- **Escritura Atomica**: Los JSON de resultado se escriben primero a `.tmp` y luego se renombran. Evita archivos corruptos si el proceso muere a mitad.
- **Portapapeles Unicode**: Los resultados se copian con `ctypes` UTF-16 nativo. Si falla, hay fallback al comando `clip`.
- **Instancia unica**: TRANSCLIP y escucha_output usan archivos `.lock` con PID para evitar duplicados.
- **Auditoria de Logs**: Cada proceso escribe su log en `%USERPROFILE%\.waio\logs\`.

---

## 9. ESTRUCTURA DE DIRECTORIOS

```
%USERPROFILE%\.waio\
├── waio_escucha.py              # Motor principal
├── waio_visor.py                # Visor grafico
├── transclip.py                 # Puente WhatsApp
├── escucha_output.py            # Compilador de resultados
├── kill_waio.py                 # Mata solo el motor
├── prompt.txt                   # Prompt editable por el usuario
├── logs\                        # Logs de todos los procesos
├── output\                      # Resultados de comandos (JSONs)
├── jsonout\                     # JSONs ya procesados (historial)
└── trash\                       # Fallback de borrado
```

---

## 10. LICENCIA

MIT License. Ver archivo `LICENSE` para el texto completo.
