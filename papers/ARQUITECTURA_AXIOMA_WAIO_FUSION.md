# ARQUITECTURA DE FUSIÓN: AXIOMA-Scribe + WAIO
**Proyecto:** La Biblioteca de Verdad Probada y el Contexto Pasivo  
**Autor:** Yonijd  
**Fecha:** 25 de Octubre de 2026  
**Propósito:** Definir el pipeline definitivo para la generación de código libre de alucinaciones mediante la combinación de análisis estático (AXIOMA) y contexto semántico (WAIO).

---

## 1. El Problema: La Alucinación y el Acoplamiento

En el desarrollo de software asistido por IA, el mayor problema no es que la IA no sepa escribir código, sino que:
1. **Alucina:** Inventa funciones o lógica que no existe en el proyecto.
2. **Desconoce el entorno:** No sabe qué herramientas o utilidades ya tiene el desarrollador.
3. **Genera deuda técnica:** Escribe código monolítico, con dependencias ocultas y variables globales difíciles de mantener.

En junio de 2026, el proyecto **AXIOMA-Scribe** intentó resolver esto fragmentando el código en bloques JSON puros. Meses después, el descubrimiento de la **Arquitectura de Contexto Pasivo (ACP)** en WAIO reveló cómo la IA puede leer el entorno. Este documento une ambas piezas.

---

## 2. La Solución: El Pipeline de Verdad Probada

El flujo de trabajo se divide en tres fases que transforman el caos en un sistema operativo semántico para la IA.

### Fase 1: Fragmentación (AXIOMA-Scribe)
El analizador estático (usando `ast` en Python) toma un archivo fuente complejo (ej. `main.py` de diagnóstico) y lo divide en bloques atómicos. 
*   **Resultado:** Archivos JSON que contienen el código limpio, sus dependencias externas reales y sus builtins.
*   **Ejemplo:** El bloque `format_bytes` se extrae sin dependencias externas, listo para ser reutilizado.

### Fase 2: Inyección de Contexto (El Estándar NDD)
Los bloques aprobados por el pipeline de AXIOMA no se guardan con nombres aleatorios. Se les aplica el **Nomenclature-Driven Development (NDD)**. El nombre del archivo debe describir su función, su estado y sus dependencias.
*   **Nombre del archivo:** `bloque_aprobado_verdad_probada_formatear_bytes_deps_0.json`
*   **Beneficio:** La IA web, al ejecutar el comando `listia` (a través de WAIO), lee este nombre y entiende instantáneamente que existe una función validada para formatear bytes, y que es independiente.

### Fase 3: Ensamblaje Semántico (WAIO + IA)
Cuando el usuario pide crear un nuevo script, el motor WAIO y la IA colaboran:
1. La IA (ej. DeepSeek) hace un `listia`.
2. Gracias al NDD, la IA **absorbe el contexto pasivo** (sabe qué bloques de verdad probada existen).
3. La IA genera un JSON de WAIO para ensamblar esos bloques, sin reescribirlos desde cero y sin alucinar dependencias.

---

## 3. El Impacto en la Memoria del Proyecto

Con este pipeline, la memoria del proyecto deja de ser un `historial.txt` o un chat perdido. El `Workdir` se convierte en una **base de datos semántica**.

*   Si el proyecto está en fase de prueba, el usuario crea el archivo `estado_proyecto_en_fase_de_auditoria.txt`.
*   Si se prohíbe el uso de librerías externas, se crea `prohibido_usar_bootstrap_usar_css_puro.txt`.
*   La IA lo lee en su próximo `listia` y adapta su código.

---

## 4. Visión a Futuro (WAIO 4.0)

La meta final es que WAIO no solo ejecute comandos, sino que administre la biblioteca AXIOMA.
*   **El Validador de Verdad:** WAIO podría bloquear la ejecución de un JSON si el bloque referenciado no tiene el prefijo `bloque_aprobado_verdad_probada_`. Esto garantiza que la IA solo use código auditado.
*   **El Sistema de Memoria Evolutiva:** El agente leerá los archivos de estado para entender el proyecto y propondrá la refactorización de bloques con alta dependencia, manteniendo la arquitectura limpia a lo largo del tiempo.

---

## 5. Conclusión

La fusión de AXIOMA-Scribe (curaduría de código) y WAIO (ejecución y contexto pasivo) representa el paso de los "chatbots que escriben código" a los **"sistemas operativos que ensamblan software"**. Es la solución definitiva a la alucinación de la IA: en lugar de pedirle que invente la rueda, le damos un garaje lleno de ruedas perfectas y le enseñamos a leer las etiquetas.

*"La IA no necesita ser más inteligente, necesita un entorno mejor diseñado."*