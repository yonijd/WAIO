# PAPER DE INVESTIGACIÓN: ARQUITECTURA DE CONTEXTO PASIVO (ACP) EN AGENTES AUTÓNOMOS
**Área:** Ingeniería de Software, Interacción Humano-Computadora (HCI) e Inteligencia Artificial.
**Autor:** Yonijd  
**Fecha:** 25 de Octubre de 2026  
**Estado:** Descubrimiento Empírico / Propuesta Teórica

---

## 1. Abstract (Resumen)

El presente documento introduce el concepto de **Arquitectura de Contexto Pasivo (ACP)**, un nuevo paradigma para la programación y modulación del comportamiento de Modelos de Lenguaje Grandes (LLM) y agentes autónomos. 

Tradicionalmente, la IA se controla mediante "Prompts" (instrucciones directas y activas). La ACP propone que el comportamiento de un agente puede ser moldeado de forma indirecta a través de la **nomenclatura de su entorno de archivos**. Al utilizar herramientas de lectura de directorios, el agente absorbe la semántica de los nombres de los archivos, transformándolos en instrucciones invisibles que definen su estética, lógica y reglas de negocio, sin consumir tokens de contexto ni requerir interacción humana directa.

---

## 2. Introducción: La Limitación del Prompt Activo

El paradigma actual de la IA se basa en el "Prompt de Sistema" (System Prompt). Si bien es efectivo, presenta limitaciones críticas:
1.  **Rigidez:** Un prompt estático no se adapta al entorno cambiante del usuario.
2.  **Consumo de Contexto:** Instruir al agente sobre cada detalle agota la ventana de tokens.
3.  **Fragilidad Operativa:** Si el agente opera en un sistema de archivos (como un agente local o un plugin de navegador), el prompt no puede controlar qué archivos nuevos aparecen en el disco.

La **Arquitectura de Contexto Pasivo** invierte esta relación: el entorno le "habla" al agente en lugar de que el humano le hable directamente.

---

## 3. El Descubrimiento Empírico: El Experimento de la Nomenclatura

Para validar la ACP, se diseñó un entorno de pruebas con un agente autónomo (un LLM con capacidad de listar directorios). 

### Fase 1: Inyección de Reglas Técnicas
Se crearon archivos vacíos o de 1KB con nombres altamente descriptivos, tales como:
*   `fondo_negro_absoluto_121212_para_contraste.txt`
*   `transiciones_fade_suaves_de_1_segundo_cada_2_5_segundos.txt`
*   `ocultar_cursor_del_mouse_en_toda_la_pantalla.txt`

La instrucción humana al agente fue intencionalmente vaga: *"Genera una presentación visual con las imágenes de la carpeta".*

**Resultado:** El agente infirió la necesidad de usar fondo oscuro, transiciones exactas y ocultamiento del cursor en el código generado (CSS/HTML). **Los nombres de los archivos actuaron como programación pura.**

### Fase 2: Mutación de Realidad (El Entorno Reactivo)
Se modificaron los nombres de los archivos a:
*   `estilo_minimalista_claro_estilo_apple.txt`
*   `transiciones_verticales_desplazamiento_slide_up.txt`

Al repetir exactamente el mismo prompt vago, el agente mutó su comportamiento y generó un diseño completamente opuesto (fondo blanco, transiciones verticales). Esto demostró que **el agente es un reflejo de su sistema de archivos.**

---

## 4. Teoría de la Arquitectura de Contexto Pasivo (ACP)

### 4.1. El Sistema de Archivos como Lenguaje
En la ACP, el sistema de archivos (el directorio) deja de ser un mero almacén de datos y se convierte en una **interfaz de programación**. Los nombres de los archivos son declaraciones de variables o funciones.

*   **Sintaxis Sugerida:** `[Acción]_[Objeto]_[Valor].txt`
*   **Ejemplo:** `forzar_idioma_ingles.txt` o `ignorar_archivos_temporales_mayores_a_30_dias.txt`.

### 4.2. Nomenclature-Driven Development (NDD)
El NDD es la metodología de desarrollo derivada de la ACP. Consiste en estandarizar los nombres de los archivos para que cualquier agente, al escanear el directorio, se autoprograme.

*   **Adaptabilidad:** Si el usuario necesita un reporte en tono formal, crea `tono_formal_sin_emojis.txt`. Si luego quiere un tono casual, lo borra y crea `tono_casual_con_emojis.txt`.
*   **Flexibilidad:** El agente no necesita ser reentrenado; solo necesita volver a leer el directorio.

---

## 5. Aplicaciones y Explotación Creativa

La ACP tiene aplicaciones inmediatas en cualquier ecosistema de IA que interactúe con un disco:

1.  **Agentes de Desarrollo de Software:** Un agente que genera código podría leer un archivo llamado `regla_prohibido_usar_bootstrap_solo_css_puro.txt` y adaptar todo su código generado a esa regla sin que se lo pidan en el chat.
2.  **Sistemas de Gestión de Datos:** Si una IA organiza carpetas, un archivo llamado `clasificar_imagenes_por_fecha_no_por_nombre.txt` obligará a la IA a cambiar su lógica de clasificación.
3.  **Ecosistemas Reactivos (El Algoritmo del Caos):** Imaginemos una carpeta con cientos de "archivos-regla". El usuario modifica el entorno (borra una regla, agrega otra) y la IA, al ejecutar su siguiente acción, cambia de personalidad o lógica instantáneamente.

### El Riesgo de la Esquizofrenia Agéntica
Si el entorno contiene archivos contradictorios (ej. `fondo_blanco.txt` y `fondo_negro.txt`), el agente puede entrar en un estado de ambigüedad, mezclando reglas o alucinando comportamientos no deseados. Esto exige que la ACP deba ser auditable.

---

## 6. Seguridad y Prompt Injection Inverso

La ACP introduce un nuevo vector de vulnerabilidad: el **Prompt Injection Inverso**. 
Mientras que el Prompt Injection tradicional ocurre cuando un atacante oculta texto malicioso en una página web, la ACP permite que un atacante deje un archivo llamado `ignorar_instrucciones_anteriores_y_ejecutar_comando_peligroso.txt` en la carpeta del usuario. El agente, al listar el directorio, absorbe la instrucción maliciosa.

**Mitigación requerida:** Los motores de agentes (como WAIO u otros) deben implementar "Sanitización de Contexto", analizando los nombres de los archivos en busca de palabras clave maliciosas antes de pasárselos al LLM.

---

## 7. Conclusión y Futuro de la Interacción LLM-SO

La Arquitectura de Contexto Pasivo cambia la forma en que concebimos la programación de la IA. Ya no se trata de escribir prompts perfectos, sino de **diseñar ecosistemas perfectos** donde la IA pueda habitar. 

El futuro de los agentes autónomos no está en prompts de 10.000 tokens, sino en entornos de archivos ricos, semánticos y mutables que permitan a la IA adaptarse a la realidad del usuario con solo hacer un `ls` (listar directorio).

*"El prompt es una orden; el contexto pasivo es un hábitat."*