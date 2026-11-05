# Política de Seguridad de WAIO

## 1. Nuestra Filosofía
WAIO es una herramienta de automatización local diseñada para darle "manos" a las IAs web. Reconocemos que el poder de ejecutar acciones en un sistema operativo conlleva riesgos. Por eso, el motor está diseñado con **seguridad por defecto**: sandbox por carpeta, perfiles de permisos, límites de escritura y borrado seguro a la papelera.

## 2. Reportar una Vulnerabilidad
Si descubrís una falla de seguridad en WAIO, por favor **NO abras un issue público**.
Usá la pestaña **Security → Advisories** del repositorio para abrir un reporte privado.
Me comprometo a:
1. Confirmar la recepción del reporte en un plazo máximo de 48 horas.
2. Investigar y desarrollar un parche si la falla es válida.
3. Darte el crédito correspondiente en el `CHANGELOG.md` cuando el parche sea publicado.

## 3. Riesgos Conocidos y Documentados
En WAIO creemos en la transparencia. Los riesgos conocidos del paradigma de agentes autónomos están documentados en la carpeta `/papers/`.

La serie `REPORT_*_PASSIVE_CONTEXT_SECURITY_FLAW` (Informe 1, Informe 2, y los que sigan) documenta la investigación en curso sobre inyección de contexto pasivo: la capacidad de inyectar instrucciones a través de nombres de archivo y otros canales del entorno, sin que el usuario las incluya en el prompt. Los informes sucesivos amplían y validan los anteriores; no los reemplazan. El Informe 1 (`INFORME_FALLA_SEGURIDAD_CONTEXTO_PASIVO.md`) describe el hallazgo inicial; el Informe 2 (`INFORME_02_FALLA_SEGURIDAD_CONTEXTO_PASIVO_VALIDACION_Y_HALLAZGOS.md`) lo valida experimentalmente y añade hallazgos derivados.

**Mitigación:** Se está trabajando en un "Sanitizador de Nombres de Archivo" para futuras versiones.

## 4. Mitigaciones Implementadas (v3.3)
- **Perfiles de Seguridad:** `readonly`, `standard`, `advanced`, `debug`.
- **Sandbox Dinámico:** La IA solo opera en la carpeta donde se inició WAIO. No hay una carpeta canónica predecible.
- **Lista Negra de Nombres Reservados:** Bloqueo de nombres como `CON`, `NUL`, `PRN` y caracteres de flujo de datos (ADS) para evitar cuelgues del sistema.
- **Validación de Rutas:** Bloqueo de *Path Traversal* (`../`) y rutas absolutas en perfiles bajos.
- **Borrado Seguro:** `eliminar_archivo` y `eliminar_carpeta` envían a la Papelera de Reciclaje. La sobrescritura (`crear_archivo` sobre un archivo existente), el `append_archivo` y el `renombrar_archivo` son directos y no pasan por papelera en el perfil `standard`. Los usuarios deben evitar activar WAIO en carpetas con archivos que no puedan permitirse perder.
- **Motor Doble Hilo:** El motor no se cuelga si un JSON es inválido.

## 5. Responsabilidad del Usuario (Licencia MIT)
WAIO se distribuye bajo la licencia **MIT**, lo que significa que se proporciona **"AS IS" (tal cual)**, sin garantías de ningún tipo.
El usuario es el único responsable del uso que le dé a la herramienta y a las skills de terceros. WAIO no se hace responsable por daños directos o indirectos, pérdida de datos o uso malintencionado del software.