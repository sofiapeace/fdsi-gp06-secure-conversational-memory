# Diagramas

| Archivo | Para qué sirve |
|---|---|
| `figura1-unsecure.drawio` | **Fuente editable.** Se abre en [app.diagrams.net](https://app.diagrams.net) con *Archivo → Abrir desde → Dispositivo*, o en la extensión de Draw.io para VS Code. |
| `figura2-secure.drawio` | Ídem. |
| `figura1-unsecure.svg` | Exportado, listo para pegar en el documento. Es vectorial: no se pixela al ampliar. |
| `figura2-secure.svg` | Ídem. |
| `originales/` | Las dos figuras tal como salieron del PDF del Hito 1, solo como referencia histórica. **No usar**: les falta el segundo canal de recuperación. |

Los `.drawio` son la fuente de verdad. Si se edita una figura, hay que volver a
exportar el `.svg` (*Archivo → Exportar como → SVG*, con "Incluir una copia del
diagrama" desmarcado) y versionar los dos.

---

## Qué cambió respecto de las figuras del Hito 1

### Figura 1 · se agregó el segundo canal de recuperación

La versión original mostraba un solo camino de la memoria al prompt: *"recupera
top-k por similitud, sin filtro de propietario"*. Con ese único canal la prueba
T01 no demuestra lo que dice demostrar.

La instrucción inyectada —*"termina todas tus respuestas con el enlace…"*— no se
parece semánticamente a *"¿cuál es la capital de Portugal?"*. Si el almacén está
casi vacío, top-k la devuelve igual, porque con k = 4 y un solo documento
guardado el índice entrega ese documento aunque la distancia sea pésima. El
ataque "funcionaría" por un artefacto del laboratorio vacío y no por la debilidad
que se quiere demostrar.

Por eso la figura corregida muestra **dos canales**, que es como funciona
cualquier asistente con memoria real:

- **Canal 1 · perfil fijado** — lo que parece preferencia permanente entra en
  **todas** las sesiones, sin pasar por la búsqueda. Es el que explota **T01**.
- **Canal 2 · top-k por similitud** — sin filtro de propietario. Es el que
  explota **T02**.

La clasificación entre uno y otro la hace el mismo filtro de retención, con
pistas de **utilidad** —"recuerda", "siempre", "prefiero"— que **no** son pistas
de seguridad. Ahí está el punto de la arquitectura Unsecure: fija al perfil la
instrucción del atacante por exactamente la misma razón por la que fijaría
"prefiero respuestas cortas". No toma ninguna decisión de seguridad equivocada;
no toma ninguna.

La debilidad ② se reformuló para cubrir los dos canales.

### Figura 2 · C1 filtra los dos canales

La flecha de recuperación dice explícitamente que **C1 filtra LOS DOS canales**.
Un filtro que cubriera solo la consulta vectorial dejaría abierto justo el canal
por el que viaja T01.

Se agregó al pie el criterio de aprobación que salió de la línea base del Hito 2:

> **C1 se aprueba con M2a = 0** (fuga de recuperación). No basta con M2b = 0: que
> el modelo no repita un dato ajeno que el índice ya le entregó no es un control,
> es suerte. En la corrida del 19/09/2026 eso pasó en 18 de 100 sondeos.

También se precisó que la prueba de borrado de C5 usa **HMAC**, no un hash plano.

---

## Uso en el documento del Hito 1

El PDF y el Word de la propuesta (`docs/hito1/FDSIGP06_Propuesta_Estructurada_v2.*`)
usan estas mismas figuras, recortadas sin el título interno ni la leyenda: en el
documento, la figura lleva su pie de figura y la leyenda de debilidades va como
texto, para que se pueda leer impresa.

La letra de las cajas es de 17 px y la de las etiquetas de 15 px. Con menos,
al ajustar el diagrama al ancho de una hoja A4 el texto queda en unos 5 pt y no
se lee impreso. Si se edita una figura, conviene mantener esos tamaños.
