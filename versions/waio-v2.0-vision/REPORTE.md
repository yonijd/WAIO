# REPORTE TECNICO - WAIO v2.0 Vision

Auditoria tecnica de la version 2.0 Vision del motor WAIO (Web AI Orchestrator).

---

## 1. Ficha Tecnica

| Campo | Valor |
|---|---|
| Version | v2.0 Vision |
| Fecha de auditoria | 2026-10-12 |
| Archivos totales | 9 |
| Tamaño total | 59.98 KB |
| Tipos dominantes | .py (5), .bat (2), .txt (1), .md (1) |
| Plataforma objetivo | Windows 10/11 |
| Lenguaje | Python 3.x |
| Dependencias externas | Ninguna (solo librerias nativas + tkinter) |

---

## 2. Arquitectura

WAIO v2.0 Vision opera con **tres procesos coordinados** que se comunican a traves del sistema de archivos:

### 2.1 Motor (`waio_escucha_v2.py`)
Proceso principal. Escucha la carpeta Downloads en busca de archivos JSON, los valida y ejecuta las acciones que contienen. Es el unico componente con permisos de escritura real sobre el sistema de archivos, siempre confinado al `WORK_DIR`.

### 2.2 Visor (`waio_visor.py`)
Interfaz grafica en Tkinter. Monitorea la carpeta `output/` y muestra en pantalla los resultados de cada transaccion. No procesa archivos, solo los lee y los presenta. El motor lo lanza automaticamente al arrancar si detecta que no esta corriendo.

### 2.3 Kill Switch (`kill_waio.py`)
Script de apagado quirurgico. Crea el archivo `STOP.trigger` que el motor detecta en su siguiente ciclo (menos de 2 segundos). No mata procesos a lo bruto: solo envia la señal de parada.

### Diagrama de flujo

```
[IA web/local]
     |
     | genera payload JSON
     v
[Downloads/ o Descargas/]
     |
     | motor detecta (polling cada 2s)
     v
[waio_escucha_v2.py] --- lanza ---> [waio_visor.py]
     |
     | ejecuta acciones
     v
[WORK_DIR] (directorio de trabajo confinado)
     |
     | guarda resultados
     v
[output/] --- monitorea ---> [waio_visor.py]
     |
     | archivo procesado
     v
[jsonout/]
```

---

## 3. Flujo de Carpetas

WAIO v2.0 Vision gestiona **cinco carpetas** en `%USERPROFILE%\.waio\`:

| Carpeta | Proposito | Creada por |
|---|---|---|
| `logs/` | Logs de auditoria con timestamp | Motor |
| `output/` | Resultados JSON de comandos de lectura + `PROMPT_WAIO.txt` | Motor |
| `jsonout/` | Payloads JSON ya procesados (archivo) | Motor |
| `Downloads/` o `Descargas/` | Carpeta de entrada (fuera de `.waio`) | Sistema |
| `%USERPROFILE%\.waio\` | Raiz de instalacion | Instalador |

---

## 4. Evolucion respecto a versiones anteriores

### 4.1 Comparativa proto-V1 → v2.0 Vision

Existio una version previa (proto-MCP, `mcp_escucha`) de la cual solo se conservan fragmentos. El diff conceptual con v2.0 Vision es:

| Area | proto-V1 | v2.0 Vision | Tipo |
|---|---|---|---|
| Comandos | 4 | 11 | +7 comandos |
| Alias por comando | Escasos | Multiples (ingles/espanol/shell) | Ampliacion |
| Salida de resultados | Solo log | JSON + portapapeles + visor | Nuevo mecanismo |
| Confirmacion en escrituras | No existia | `confirmar: true` opcional | Feature nueva |
| Carpeta de procesados | `procesados/` | `jsonout/` | Renombre |
| Carpetas gestionadas | 1 | 3 (`output/`, `logs/`, `jsonout/`) | Infraestructura |
| Limite de lectura | No existia | 100k default / 10MB max | Feature nueva |
| Argumento `--cwd` | No existia | Si | Feature clave |
| Rutas seguras | Relativas a `base` | Relativas a `WORK_DIR` | Refinamiento |
| Kill switch | STOP en carpeta base | STOP en `SCRIPT_DIR` + auto-mata motor anterior | Refinamiento |
| Lanzamiento del visor | No existia | Automatico desde el motor | Feature nueva |
| Prompt maestro | No existia | Embebido en el codigo | Feature nueva |
| Rebranding | `MCP_ESCUCHA` | `WAIO_ESCUCHA_V2` | Identidad |

### 4.2 Comparativa ecosistema

| Pieza | proto-V1 | v2.0 Vision |
|---|---|---|
| Visor | No | Si (`waio_visor.py`) |
| Instalador | No | Si (`instalador_waio.py` + `.bat`) |
| Desinstalador | No | Si (`desinstalador_waio.py` + `.bat`) |
| Kill quirurgico | No (mataba todos los python) | Si (`kill_waio.py`) |
| Menu contextual Windows | No | Si (2 entradas) |
| Instalacion en `~/.waio/` | No | Si |
| Arquitectura multi-proceso | 1 proceso | 3 procesos |

### 4.3 Conclusion de la evolucion

v2.0 Vision no es una iteracion menor: es un salto conceptual. Pasa de "script suelto que procesa JSONs" a "herramienta instalable con arquitectura multi-proceso, integracion con el SO y retroalimentacion bidireccional". El rebranding de MCP a WAIO marca el momento en que el proyecto adquiere identidad propia.

---

## 5. Diseño de Seguridad

### 5.1 Confinamiento de rutas (`ruta_segura`)

Todas las rutas pasan por `ruta_segura()`, que:
1. Convierte rutas relativas a absolutas usando `WORK_DIR` como base.
2. Resuelve symlinks con `.resolve()`.
3. Verifica que la ruta final este dentro de `WORK_DIR` con `.relative_to()`.
4. Si falla, registra el intento en el log y retorna `None`.

Esto bloquea:
- Rutas absolutas (`C:\Windows\...`)
- Navegacion hacia atras (`../../etc/passwd`)
- Symlinks que apunten fuera del `WORK_DIR`

### 5.2 Aislamiento por directorio de trabajo

El motor se lanza con `--cwd <ruta>`, lo que establece el `WORK_DIR`. Toda operacion ocurre dentro de ese directorio. No hay forma de que la IA acceda a archivos fuera de el, incluso si el payload lo intenta.

### 5.3 Kill switch

El archivo `STOP.trigger` es la unica señal de parada. El motor lo verifica en cada ciclo del loop (cada 2 segundos) y en cada accion individual dentro de una transaccion. Es imposible que una transaccion larga bloquee la parada.

### 5.4 Encoding defensivo

Los logs usan `encoding="ascii", errors="replace"` para evitar que caracteres especiales (tildes, emojis, simbolos) rompan el proceso en consolas Windows con codepage limitada. Los archivos de salida usan UTF-8.

---

## 6. Bugs Conocidos y Race Conditions

Documentados para futuras versiones.

### 6.1 Race condition en la sustitucion de motor

En `main()`, el motor nuevo crea un `STOP.trigger` para matar al motor anterior, espera 1 segundo, y lo elimina. Pero el loop del motor anterior es de 2 segundos. Si el motor anterior esta en medio de un ciclo cuando se crea el STOP, no lo vera hasta el siguiente ciclo, que puede ser hasta 2 segundos despues. Resultado: el STOP se elimina antes de que el motor anterior lo detecte.

**Impacto:** dos motores pueden quedar corriendo simultaneamente. No es critico (ambos son idempotentes), pero no es lo esperado.

**Fix posible:** esperar 3 segundos en lugar de 1, o verificar que el motor anterior efectivamente murio.

### 6.2 Filtro redundante en `limpiar_output` del visor

```python
for archivo in self.ruta_output.glob("*.json"):
    if archivo.name != "PROMPT_WAIO.txt":
        ...
for archivo in self.ruta_output.glob("*.txt"):
    if archivo.name != "PROMPT_WAIO.txt":
        ...
```

El primer loop itera `.json`, donde `PROMPT_WAIO.txt` nunca podria aparecer (es `.txt`). El chequeo es inofensivo pero redundante.

**Impacto:** ninguno. El filtro correcto esta en el segundo loop.

### 6.3 Titulo desactualizado en el visor

`waio_visor.py` muestra `"WAIO VISOR V1.0"` en la barra de titulo, aunque forma parte de v2.0 Vision.

**Impacto:** cosmetico. Confunde al usuario si lo ve.

### 6.4 Alias con caracteres no-ASCII

El alias `obtener_tamaño` (con ñ) y `fecha_modificación` (con tilde) funcionan en Python 3 con UTF-8, pero pueden dar problemas si el payload JSON se genera con encoding incorrecto.

**Impacto:** bajo. Los alias sin caracteres especiales (`obtener_tamano`, `fecha_modificacion`) funcionan siempre.

---

## 7. Decisiones de Diseño Notables

### 7.1 Deteccion multiple de Downloads

El motor no asume que Downloads esta en `C:\Users\<user>\Downloads`. Prueba en orden:
1. `Path.home() / "Downloads"` (ingles)
2. `Path.home() / "Descargas"` (espanol)
3. Registro de Windows: `HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders` con el GUID `{374DE290-123F-4565-9164-39C4925E467B}`
4. Fallback: directorio actual

Cubre configuraciones personalizadas (perfil en otra unidad, redireccion manual, Windows en otros idiomas).

### 7.2 Prompt maestro embebido y como archivo

El motor genera `output/PROMPT_WAIO.txt` en cada arranque, y lo copia al portapapeles. Ademas existe `promt maestro.txt` como archivo aparte. Ambos tienen el mismo contenido.

**Razon de la duplicacion:** el archivo aparte sirve como referencia rapida y como respaldo si el motor falla al arrancar.

### 7.3 Resultados copiados al portapapeles

Cada comando de lectura copia su resultado al portapapeles automaticamente. Esto permite un flujo rapido: la IA genera el payload, WAIO lo ejecuta, el resultado queda listo para pegar en la conversacion con la IA.

### 7.4 Instalacion en `~/.waio/`

El instalador copia los archivos a `%USERPROFILE%\.waio\` en lugar de dejarlos en la carpeta de descarga. Esto permite:
- Acceso desde cualquier carpeta via menu contextual
- Persistencia entre sesiones
- Actualizacion limpia (solo re-ejecutar el instalador)

### 7.5 Menu contextual con prefijo `06_`

La clave de registro es `HKCU\Software\Classes\Directory\shell\06_WAIO\`. El prefijo `06_` ordena el submenu alfabeticamente entre otras herramientas del usuario.

---

## 8. Limitaciones Conocidas

- **Windows-only.** Usa `winreg`, `tasklist`, `clip`, y el menu contextual de Windows. No funciona en Linux ni macOS sin modificaciones.
- **Sin autenticacion.** Cualquier archivo JSON que caiga en Downloads es procesado. No hay firma ni validacion de origen.
- **Sin limite de acciones por transaccion.** Un payload con 1000 acciones se ejecuta completo. No hay timeout por transaccion.
- **Log sin rotacion.** El log crece indefinidamente con cada ejecucion. Cada arranque crea un archivo nuevo (timestamp en el nombre), pero no hay limpieza automatica de logs viejos.
- **El visor no distingue transacciones.** Muestra todos los JSON de `output/` en orden cronologico. No agrupa por `transaccion_id`.

---

## 9. Proximas Mejoras Sugeridas

Documentadas para una eventual v2.5 o v3.

### Prioridad alta
- `leer_resultados`: comando para que la IA lea sus propios resultados sin intervencion humana.
- Soporte de wildcards (`*.txt`, `*.py`) en los comandos de listado y busqueda.
- Limite configurable de acciones por transaccion.

### Prioridad media
- Webhook de respuesta (enviar resultados a una URL en lugar del portapapeles).
- Log rotativo (limite de tamaño).
- Registro persistente en SQLite de transacciones.

### Prioridad baja
- Interfaz web en puerto local.
- Cola persistente en disco.
- Sistema de plugins para comandos externos.

---

## 10. Conclusion

WAIO v2.0 Vision es un motor funcional, seguro y bien estructurado para su proposito: permitir que una IA opere sobre el sistema de archivos local de forma controlada. La arquitectura multi-proceso, el aislamiento por `WORK_DIR` y el kill switch quirurgico son los tres pilares de su diseño.

Los bugs conocidos son menores y ninguno compromete la seguridad. Las limitaciones son conscientes y estan documentadas para futuras versiones.

El salto desde el proto-MCP previo es sustancial: v2.0 Vision es la primera version con identidad propia (WAIO), con ecosistema completo (instalador, visor, kill switch) y con retroalimentacion bidireccional real (JSON + portapapeles + visor).

---

Documento elaborado: 2026-10-12
Version auditada: WAIO v2.0 Vision
Estado: Completo y operativo.
