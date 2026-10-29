# REPORTE TECNICO - WAIO v2.5 Fluido

Auditoria tecnica de la version 2.5 Fluido del motor WAIO (Web AI Orchestrator).

---

## 1. Ficha Tecnica

| Campo | Valor |
|---|---|
| Version | v2.5 Fluido |
| Fecha de auditoria | 2026-10-12 |
| Archivos totales | 12 |
| Tamaño total | 67.29 KB |
| Tipos dominantes | .py (6), .bat (4), .txt (1), .md (1) |
| Plataforma objetivo | Windows 10/11 |
| Lenguaje | Python 3.8+ |
| Dependencias externas | Ninguna obligatoria. `send2trash` opcional. |

---

## 2. Arquitectura

WAIO v2.5 Fluido opera con **cuatro procesos coordinados** que se comunican a traves del sistema de archivos:

### 2.1 Motor (`waio_escucha_v2.py`)
Proceso principal. Escucha la carpeta Downloads en busca de archivos JSON, los valida y ejecuta las acciones que contienen. Es el unico componente con permisos de escritura real sobre el sistema de archivos, siempre confinado al `WORK_DIR`.

### 2.2 Visor (`waio_visor.py`)
Interfaz grafica en Tkinter. Monitorea la carpeta `output/` y muestra en pantalla los resultados de cada transaccion. Ademas controla el ciclo de vida de TRANSCLIP mediante un boton toggle. El motor lo lanza automaticamente al arrancar si detecta que no esta corriendo.

### 2.3 TRANSCLIP (`transclip.py`) — NUEVO en v2.5
Puente de portapapeles. Se ejecuta como proceso independiente en Tkinter. Monitorea el portapapeles cada 500 ms y traduce comandos simples al formato WAIO. No procesa archivos directamente: genera JSONs y los deja en Downloads para que el motor los levante.

Usa dos archivos de control:
- `transclip.lock`: contiene el PID de la instancia activa. Evita duplicados.
- `TRANSCLIP_STOP.trigger`: senal de parada especifica de TRANSCLIP.

### 2.4 Kill Switch (`kill_waio.py`)
Script de apagado quirurgico. Crea el archivo `STOP.trigger` que el motor detecta en su siguiente ciclo (menos de 2 segundos). No mata procesos a lo bruto: solo envia la senal de parada.

### Diagrama de flujo

```
[IA web/local]
     |
     | genera JSON (completo o simple)
     v
[Portapapeles]  <--->  [transclip.py]
     |                       |
     |                       | envuelve y guarda
     |                       v
     +--------------> [Downloads/]
                             |
                             | motor detecta (polling cada 2s)
                             v
                    [waio_escucha_v2.py] --- lanza ---> [waio_visor.py]
                             |
                             | ejecuta acciones
                             v
                    [WORK_DIR] (confinado)
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

WAIO v2.5 Fluido gestiona **cuatro carpetas** dentro de `%USERPROFILE%\.waio\`, mas una externa:

| Carpeta | Proposito | Creada por |
|---|---|---|
| `logs/` | Logs de auditoria con timestamp | Motor + TRANSCLIP |
| `output/` | Resultados JSON de comandos + `PROMPT_WAIO.txt` | Motor |
| `jsonout/` | Payloads JSON ya procesados (archivo) | Motor |
| `trash/` | Papelera manual (solo si `send2trash` no esta) | Motor |
| `Downloads/` o `Descargas/` | Carpeta de entrada (fuera de `.waio`) | Sistema |

TRANSCLIP ademas usa:

| Archivo | Proposito |
|---|---|
| `transclip.lock` | PID de la instancia activa |
| `TRANSCLIP_STOP.trigger` | Senal de parada de TRANSCLIP |
| `logs/transclip_YYYYMMDD.log` | Log diario de TRANSCLIP |
| `traducidos/` | Carpeta de trabajo de TRANSCLIP |

---

## 4. Evolucion respecto a versiones anteriores

### 4.1 Comparativa v2.0 Vision -> v2.5 Fluido

| Area | v2.0 Vision | v2.5 Fluido | Tipo |
|---|---|---|---|
| Entrada de comandos | JSON manual en Downloads | JSON manual + TRANSCLIP por portapapeles | Feature nueva |
| Limite de lectura | 100,000 por defecto | 500,000 por defecto | Ampliacion |
| Borrado | Directo (`unlink`, `rmtree`) | A Papelera (via `send2trash`) o `trash/` manual | Cambio de politica |
| Portapapeles | `clip` (no Unicode) | `ctypes` UTF-16 + fallback a `clip` | Mejora tecnica |
| Escritura de JSON | Directa | Atomica (`.tmp` + `rename`) | Robustez |
| Escaneo de Downloads | `glob` | `os.scandir` | Performance |
| Prompt maestro | Nombre con typo + archivo aparte | `PROMPT_WAIO.txt`, sin duplicado | Limpieza |
| Rechazo de rutas absolutas | Post-resolucion | Pre-resolucion (mas claro) | Refinamiento |
| Visor | 800x600, sin control de TRANSCLIP | 950x600, con toggle de TRANSCLIP | Ampliacion |
| Procesos coordinados | 3 (motor, visor, kill) | 4 (motor, visor, transclip, kill) | Crecimiento |
| Entradas de menu contextual | 2 | 3 (con TRANSCLIP) | Crecimiento |
| Log del motor | `ascii` con replace | UTF-8 puro | Mejora |

### 4.2 Comparativa ecosistema

| Pieza | v2.0 Vision | v2.5 Fluido |
|---|---|---|
| Motor | `waio_escucha_v2.py` (32.75 KB) | `waio_escucha_v2.py` (29.02 KB) |
| Visor | `waio_visor.py` (8.30 KB) | `waio_visor.py` (11.38 KB) |
| TRANSCLIP | No existe | `transclip.py` (12.01 KB) |
| Kill switch | `kill_waio.py` | `kill_waio.py` (sin cambios) |
| Instalador | 4.51 KB | 4.96 KB |
| Desinstalador | 2.47 KB | 2.70 KB |
| Prompt maestro | `promt maestro.txt` (5.55 KB) | `PROMPT_WAIO.txt` (1.58 KB) |

### 4.3 Conclusion de la evolucion

v2.5 Fluido profundiza la direccion de v2.0 Vision en lugar de cambiar de rumbo. Los tres ejes de la version son:

1. **Fluidez de entrada**: TRANSCLIP elimina la necesidad de escribir JSONs a mano. Ahora copiar un comando simple alcanza.
2. **Fluidez de lectura**: el limite sube 5x y el portapapeles soporta Unicode real.
3. **Fluidez de borrado**: los comandos de eliminacion ya no son irreversibles.

Ademas incorpora robustez (escritura atomica, lock de instancia, rechazo temprano de rutas absolutas) sin agregar complejidad al usuario.

---

## 5. Diseño de Seguridad

### 5.1 Confinamiento de rutas (`ruta_segura`)

Todas las rutas pasan por `ruta_segura()`, que:
1. Rechaza explicitamente rutas absolutas antes de intentar resolverlas.
2. Convierte rutas relativas a absolutas usando `WORK_DIR` como base.
3. Resuelve symlinks con `.resolve()`.
4. Verifica que la ruta final este dentro de `WORK_DIR` con `.relative_to()`.
5. Si falla, registra el intento en el log y retorna `None`.

Esto bloquea:
- Rutas absolutas (`C:\Windows\...`)
- Navegacion hacia atras (`../../etc/passwd`)
- Symlinks que apunten fuera del `WORK_DIR`

### 5.2 Borrado seguro

`eliminar_archivo` y `eliminar_carpeta` ya no borran directo. Usan `eliminar_seguro()`:
1. Intenta `send2trash` (Papelera de Reciclaje nativa de Windows).
2. Si no esta instalado, mueve a `trash/` con timestamp en el nombre.

Esto significa que ningun comando de la IA puede destruir datos de forma irreversible.

### 5.3 Escritura atomica de JSON

Los resultados se escriben primero a `.tmp` y luego se renombran con `.rename()`. Esto evita que un JSON quede corrupto si el proceso muere entre la apertura del archivo y el cierre.

### 5.4 Portapapeles Unicode real

El comando `clip` de Windows tiene problemas con caracteres no-ASCII. La version 2.5 usa `ctypes` para abrir el portapapeles y escribir en UTF-16 nativo. Si falla, cae al `clip` tradicional como respaldo (perdida de caracteres especiales, pero no crash).

### 5.5 Kill switch doble

Hay dos senales de parada:
- `STOP.trigger`: apaga el motor.
- `TRANSCLIP_STOP.trigger`: apaga TRANSCLIP.

Ambas se verifican periodicamente. El visor las crea al cerrarse, garantizando que no queden procesos huerfanos.

---

## 6. Bugs Conocidos y Race Conditions

### 6.1 Race condition en la sustitucion de motor (heredada de v2.0)

En `main()`, el motor nuevo crea un `STOP.trigger` para matar al motor anterior, espera 1 segundo, y lo elimina. Pero el loop del motor anterior es de 2 segundos. Si el motor anterior esta en medio de un ciclo cuando se crea el STOP, no lo vera hasta el siguiente ciclo, que puede ser hasta 2 segundos despues. Resultado: el STOP se elimina antes de que el motor anterior lo detecte.

**Impacto:** dos motores pueden quedar corriendo simultaneamente. No es critico (ambos son idempotentes), pero no es lo esperado.

**Fix posible:** esperar 3 segundos en lugar de 1, o verificar que el motor anterior efectivamente murio.

### 6.2 Titulo desactualizado en el visor

`waio_visor.py` muestra `"WAIO VISOR V1.0"` en la barra de titulo, aunque forma parte de v2.5 Fluido.

**Impacto:** cosmetico. Confunde al usuario si lo ve.

### 6.3 Alias con caracteres no-ASCII

Los alias `obtener_tamaño` (con ñ) y `fecha_modificación` (con tilde) funcionan en Python 3 con UTF-8, pero pueden dar problemas si el payload JSON se genera con encoding incorrecto.

**Impacto:** bajo. Los alias sin caracteres especiales (`obtener_tamano`, `fecha_modificacion`) funcionan siempre.

### 6.4 Doble verificacion de estado de TRANSCLIP

El visor verifica el estado de TRANSCLIP periodicamente leyendo `transclip.lock`. Si el lock queda huerfano (proceso muerto pero archivo presente), el visor muestra "CERRAR TRANSCLIP" aunque no haya nada que cerrar. La logica de limpieza del lock existe en `transclip.py` (`verificar_lock`), pero solo se ejecuta al arrancar TRANSCLIP, no al consultarlo desde el visor.

**Impacto:** cosmetico. El boton puede quedar en estado incorrecto hasta que se reinicie TRANSCLIP o se borre el lock a mano.

---

## 7. Decisiones de Diseño Notables

### 7.1 TRANSCLIP como proceso separado

TRANSCLIP podria haber sido un hilo del motor o del visor. Se eligio proceso separado por tres razones:
1. Aislamiento: si TRANSCLIP crashea, el motor sigue.
2. Independencia: se puede arrancar sin motor (util para pre-cargar comandos).
3. Tkinter requiere el hilo principal: el visor ya lo ocupa, no se puede compartir.

### 7.2 Tres casos de procesamiento en TRANSCLIP

TRANSCLIP distingue:
- **JSON WAIO completo**: pasa directo (no toca nada).
- **JSON con solo `comando`**: envuelve en transaccion nueva con ID unico.
- **JSON externo sin `comando`**: guarda el contenido como archivo via `crear_archivo`.

Esta granularidad permite que la IA emita comandos de distintos niveles sin que TRANSCLIP tenga que adivinar la intencion.

### 7.3 Lock con PID en lugar de mutex

TRANSCLIP usa `transclip.lock` con el PID escrito. Al arrancar, si el archivo existe, verifica si el PID sigue vivo con `tasklist`. Si no, lo elimina y toma el control. Es una solucion simple que evita dependencias externas.

### 7.4 Papelera via `send2trash` con fallback

`send2trash` no viene con Python. Si no esta instalado, WAIO cae a una `trash/` local con timestamp. Esto garantiza que el borrado seguro funcione en cualquier instalacion, con o sin dependencias.

### 7.5 Instalacion en `~/.waio/`

El instalador copia los archivos a `%USERPROFILE%\.waio\` en lugar de dejarlos en la carpeta de descarga. Esto permite:
- Acceso desde cualquier carpeta via menu contextual
- Persistencia entre sesiones
- Actualizacion limpia (solo re-ejecutar el instalador)

### 7.6 Menu contextual con prefijo `06_`

La clave de registro es `HKCU\Software\Classes\Directory\shell\06_WAIO\`. El prefijo `06_` ordena el submenu alfabeticamente entre otras herramientas del usuario.

---

## 8. Limitaciones Conocidas

- **Windows-only.** Usa `winreg`, `tasklist`, `clip`, `ctypes.windll` y el menu contextual de Windows. No funciona en Linux ni macOS sin modificaciones.
- **Sin autenticacion.** Cualquier archivo JSON que caiga en Downloads es procesado. No hay firma ni validacion de origen.
- **Sin limite de acciones por transaccion.** Un payload con 1000 acciones se ejecuta completo. No hay timeout por transaccion.
- **Log sin rotacion.** El log crece indefinidamente con cada ejecucion. Cada arranque crea un archivo nuevo (timestamp en el nombre), pero no hay limpieza automatica de logs viejos.
- **El visor no distingue transacciones.** Muestra todos los JSON de `output/` en orden cronologico. No agrupa por `transaccion_id`.
- **TRANSCLIP solo lee texto del portapapeles.** No soporta imagenes ni archivos binarios.

---

## 9. Proximas Mejoras Sugeridas

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

WAIO v2.5 Fluido profundiza la vision de v2.0 sin romperla. Agrega TRANSCLIP como puente de entrada de bajo esfuerzo, sube el limite de lectura 5x, introduce borrado seguro y resuelve el problema historico del portapapeles con Unicode.

Los bugs conocidos son menores y ninguno compromete la seguridad. Las limitaciones son conscientes y estan documentadas.

El crecimiento respecto a v2.0 es en profundidad mas que en superficie: los mismos 11 comandos, el mismo aislamiento por `WORK_DIR`, la misma arquitectura de kill switch, pero con mejores garantias en cada uno de esos frentes.

---

Documento elaborado: 2026-10-12
Version auditada: WAIO v2.5 Fluido
Estado: Completo y operativo.
