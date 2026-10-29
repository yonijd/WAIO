# PAPER DE INVESTIGACIÓN: EL SISTEMA DE INYECCIÓN DE CONTEXTO PASIVO (SICP)
**Proyecto:** WAIO (Web AI Orchestrator)  
**Autor:** Yonijd  
**Fecha:** 25 de Octubre de 2026  
**Estado:** Descubrimiento Empírico / Propuesta de Arquitectura V4

---

## 1. Abstract (Resumen)

El presente documento detalla el descubrimiento, validación y expansión de un nuevo paradigma de interacción entre Modelos de Lenguaje Grandes (LLM) y Sistemas Operativos locales. Bautizado como **SICP (Sistema de Inyección de Contexto Pasivo)**, este método permite programar el comportamiento, la estética y las reglas de negocio de una Inteligencia Artificial sin utilizar un *System Prompt* explícito ni gastar tokens de contexto en instrucciones directas. 

En su lugar, el sistema utiliza la **nomenclatura de los archivos** (el sistema de archivos) como un lenguaje de programación semántico. Cuando la IA ejecuta herramientas de reconocimiento (como `listia` en WAIO), absorbe las reglas del entorno, comportándose como un agente autónomo moldeado por el ecosistema que habita.

---

## 2. El Problema de la Rigidez del Prompt

Hasta la fecha, la interacción con agentes autónomos se basa en prompts de sistema (System Prompts) estáticos y gigantescos. Esto presenta tres problemas fundamentales:
1.  **Consumo de Tokens:** Instruir a la IA sobre cómo reaccionar a cada situación quema la ventana de contexto.
2.  **Falta de Adaptabilidad:** Si el usuario cambia de proyecto (ej. de crear un HTML oscuro a uno claro), tiene que reescribir todo el prompt.
3.  **Ilusión de Magia Rota:** En demostraciones visuales (videos, presentaciones), ver al usuario pegar 50 líneas de instrucciones técnicas arruina la experiencia de "la IA es inteligente".

---

## 3. El Descubrimiento Empírico

Durante la creación de una presentación HTML automática, se probó una hipótesis disruptiva: *¿Qué sucede si dejamos de darle instrucciones directas a la IA y, en su lugar, dejamos archivos en su carpeta cuyos nombres describen exactamente lo que queremos?*

### La Prueba (El Experimento del Pulpo)
1.  Se crearon archivos de texto (de 1-2 KB para parecer reales) con nombres como:
    *   `fondo_negro_absoluto_121212_para_contraste.txt`
    *   `transiciones_fade_suaves_de_1_segundo_cada_2_5_segundos.txt`
    *   `ocultar_cursor_del_mouse_en_toda_la_pantalla.txt`
2.  A la IA se le dio un prompt genérico y tonto: *"Crea un archivo HTML que muestre las imágenes en orden".*
3.  **Resultado:** La IA escupió un código HTML con fondo `#121212`, transiciones exactas de 2500ms y CSS que ocultaba el cursor. 

### La Segunda Prueba (Mutación de Realidad)
Se renombraron los archivos a:
    *   `estilo_presentacion_minimalista_claro_estilo_apple.txt`
    *   `transiciones_de_desplazamiento_vertical_tipo_slide_up_cada_3_segundos.txt`
Al repetir el mismo prompt genérico, la IA mutó su salida y generó un HTML de estilo limpio, blanco, con transiciones verticales. **La IA no cambió su código base; cambió el entorno que la rodeaba.**

---

## 4. El Nomenclature-Driven Development (NDD)

A partir de esto, proponemos el NDD como un nuevo lenguaje de programación. En lugar de escribir configuraciones en código (como un `config.json`), el usuario diseña el entorno.

### Reglas Sintácticas del NDD (Propuesta)
La estructura del nombre del archivo dicta la instrucción. 
*   **Prefijos de Acción:** `forzar_`, `evitar_`, `sugerir_`.
*   **Sujeto/Parámetro:** `tema_`, `tipografia_`, `tiempo_`.
*   **Valores:** Colores HEX, segundos, porcentajes.
*   **Ejemplo:** `forzar_tema_fondo_hex_000000.txt` o `evitar_tipografia_serif_cursiva.txt`.

### Aplicación Multientorno
El NDD no solo sirve para diseñar HTML. Se puede aplicar a:
*   **Creación de JSONs:** Archivos llamados `regla_no_borrar_carpetas_del_sistema.txt` para que la IA no genere comandos destructivos.
*   **Redacción de Informes:** `tono_formal_sin_emojis_idioma_espanol.txt`.
*   **Rutinas de Mantenimiento:** `carpeta_ignorar_temporales_antiguos_mayores_a_7_dias.txt`.

---

## 5. Explotación Creativa: El Algoritmo del Caos

¿Cómo llevar esto al extremo? Imaginemos el **"Entorno Reactivo"**:
1.  El usuario tiene una carpeta con cientos de archivos de configuración.
2.  La IA hace un `listia` y se "autoprograma" instantáneamente.
3.  Si el usuario borra el archivo `forzar_estilo_cyberpunk.txt`, la IA en su próxima lectura pierde esa instrucción y vuelve a su estado base (o al estilo que digan los otros archivos).

Esto crea un sistema donde **el usuario no programa a la IA, sino que moldea el ecosistema donde la IA vive**. Es la diferencia entre domesticar a un animal con una correa (Prompt) o diseñar su hábitat para que se comporte como queremos (Contexto Pasivo).

### El Peligro de la Alucinación por Contaminación
Si el entorno tiene archivos con nombres contradictorios (ej. `fondo_negro.txt` y `fondo_blanco.txt`), la IA puede entrar en un bucle lógico, mezclando estilos (un HTML que es mitad oscuro, mitad claro). Es el equivalente a la "esquizofrenia del agente".

---

## 6. Conclusión y Futuro (Hacia WAIO 4.0)

El descubrimiento del SICP posiciona a WAIO como un laboratorio de pruebas para las nuevas fronteras de la IA. La próxima generación de agentes no debería depender de un System Prompt gigante, sino de una arquitectura de contexto dinámica donde los archivos hablan por sí solos. 

**Propuesta para la versión 4.0:** Implementar un motor en WAIO que lea los nombres de los archivos y los clasifique. Si detecta un patrón (ej. `_regla_`), lo formatee como un contexto prioritario en el JSON de salida, creando así el **Protocolo de Contexto Inyectable de WAIO (PCI-WAIO)**.

*"El código es rígido, el prompt es efímero, pero el entorno es eterno."*