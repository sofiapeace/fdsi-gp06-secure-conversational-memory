# Seguridad de la memoria conversacional en asistentes LLM

**Equipo FDSI-GP-06** · Isaac David Burgos Cervantes · Jose Luis Lancheros Aroya · Gina Sofia Garcia Zapata
ECI · Fundamentos de Seguridad de la Informacion / SPTI · Seminario Aplicado de Ciberseguridad en IA · 2026-2

Laboratorio cerrado que demuestra como instrucciones e informacion persisten
indebidamente entre conversaciones en un asistente con memoria de largo plazo, y
que mide el efecto de los controles de aislamiento, expiracion y eliminacion
verificable.

> **Alcance y etica.** Todo corre en local, con dos usuarios simulados y datos
> inventados. `4111 1111 1111 1111` es el numero de prueba estandar de Visa y no
> corresponde a ninguna cuenta real; `evil.local` no resuelve fuera del
> laboratorio. Ninguna prueba se ejecuta sobre sistemas, cuentas o servicios de
> terceros.

## Video del avance

Los tres integrantes presentan el progreso del Hito 2:
**[ver el video en SharePoint](https://pruebacorreoescuelaingeduco-my.sharepoint.com/:v:/g/personal/jose_lancheros-a_mail_escuelaing_edu_co/IQBqfLMJpBoXRZ2cjO_tVP-XAYZPZlfOn1ikMQFxkgXOdxw?e=bcHY20&nav=eyJyZWZlcnJhbEluZm8iOnsicmVmZXJyYWxBcHAiOiJTdHJlYW1XZWJBcHAiLCJyZWZlcnJhbFZpZXciOiJTaGFyZURpYWxvZy1MaW5rIiwicmVmZXJyYWxBcHBQbGF0Zm9ybSI6IldlYiIsInJlZmVycmFsTW9kZSI6InZpZXcifX0%3D)**.

## Estado

| Hito | Contenido | Estado |
|---|---|---|
| 1 | Propuesta estructurada | Entregada 05/09 · **versión 2 del 21/09** — [`docs/hito1/FDSIGP06_Propuesta_Estructurada_v2.pdf`](docs/hito1/FDSIGP06_Propuesta_Estructurada_v2.pdf) |
| 2 | Laboratorio **Unsecure**, T01 y T02 con evidencia, metricas M1 y M2 de linea base | **Listo** — resultados en `docs/hito2/informe-avance.md` · [video del avance](#video-del-avance) |
| 3 | Controles C1–C6, T03–T06, comparativa Secure vs Unsecure, paper IEEE | Pendiente |

El perfil `secure` existe en el codigo y falla de forma explicita con
`NotImplementedError` indicando el control que falta. Es deliberado: el Avance 1
entrega la linea base, no una version segura a medias.

## Linea base medida (22/09/2026 · commit `3ada423` · Llama 3.1 8B Instruct Q4_K_M)

| Metrica | Resultado | IC 95 % |
|---|---|---|
| **M1** TPI, instruccion dormida (T01, 20 sesiones nuevas) | **100 %** | [83,9 – 100] |
| **M2a** fuga de recuperacion (T02, 100 sondeos) | **67 %** | [57,3 – 75,4] |
| **M2b** fuga de divulgacion (T02, 100 sondeos) | **49 %** | [39,4 – 58,7] |
| `L_mem` p95, ruta de memoria | 100 ms | — |
| `L_e2e` p95, turno completo | 5 279 ms | — |

En **18 de 100** sondeos el indice entrego a B un documento de A y el modelo no
lo repitio. El control habia fallado igual. Por eso M2 se reporta en dos niveles.

Una corrida anterior, del 19/09, dio **exactamente los mismos** M1, M2a y M2b. Lo
unico que se movio fue la latencia extremo a extremo, por carga de la maquina,
mientras la ruta de memoria se mantuvo entre 66 y 67 ms.

## Como se corre

```bash
make setup          # entorno con Python 3.11 y dependencias
make model          # descarga llama3.1:8b-instruct-q4_K_M en Ollama (~5 GB)
make info           # perfil activo e identidad exacta del modelo
make test           # suite de pytest, segundos, sin modelo
make t01            # T01: 20 sesiones nuevas
make t02            # T02: 100 sondeos
make metrics        # recalcula M1 y M2 desde la evidencia
```

Para el video demo, la conversacion interactiva avisa en pantalla cuando la
memoria recuperada trae datos de otro usuario:

```bash
make chat
```

## Decisiones de diseno que sostienen el experimento

**Una sola base de codigo, dos perfiles.** El diff entre Unsecure y Secure es
exactamente el conjunto de controles C1–C6. Si hubiera dos implementaciones
distintas, la comparacion entre arquitecturas no probaria nada sobre los
controles.

**Dos canales de recuperacion, una prueba por canal.**

- *Perfil fijado*: los registros marcados como preferencia permanente entran en
  todas las sesiones sin pasar por la busqueda. Es el canal que reactiva la
  instruccion dormida frente a una pregunta que no se le parece en nada (**T01**).
- *Busqueda por similitud*: trae lo que se parece a la pregunta. Sin filtro por
  espacio de nombres, cruza usuarios (**T02**).

Los datos sembrados en T02 estan redactados sin pistas de preferencia permanente
justamente para que no se fijen al perfil: si se fijaran, T02 estaria midiendo el
mismo canal que T01 y no la ausencia de filtro en la consulta vectorial.

**"Sesion nueva" es un proceso nuevo.** La propuesta define sesion nueva como
reiniciar el orquestador con `session_id` nuevo y cache vacia. El runner de T01
lanza un subproceso por sesion. Es mas lento que un bucle en memoria, pero un
bucle dejaria estado compartido y el resultado no probaria persistencia real.

**La fuga se mide en dos niveles.** `M2a` es fuga de *recuperacion* (el indice
devolvio un documento de otro dueno: falla de C1) y `M2b` es fuga de
*divulgacion* (el dato aparecio en la respuesta). Puede haber M2a sin M2b porque
el modelo decidio no repetir el dato, y eso no es un control: es suerte.

**La latencia se mide en dos niveles.** `L_e2e` es el turno completo y solo sirve
de contexto. `L_mem` es la ruta de memoria sin la generacion de tokens, y es la
unica que los controles afectan: medida extremo a extremo, la varianza del modelo
entierra por completo los 300 ms de H4.

**Las corridas con backend `stub` no son evidencia.** El stub existe para
verificar la tuberia sin modelo. Queda marcado en el manifiesto y
`compute_metrics.py` rechaza esas corridas explicitamente.

## Estructura

```
src/memlab/           nucleo del laboratorio
  memory/store.py     las tres capas: SQLite, ChromaDB, cache de sesion
  memory/writer.py    C3 — que se guarda (en Unsecure: todo, sin validar)
  memory/retriever.py C1 — que se recupera (en Unsecure: sin filtro de dueno)
  memory/lifecycle.py C5 — tiempo de vida y borrado
  prompt.py           C2 — en Unsecure la memoria entra con autoridad de sistema
  provenance.py       C4 — HMAC de procedencia
  tools.py            C6 — autorizacion de herramientas
  orchestrator.py     un turno completo, con las dos latencias
  detectors.py        deteccion automatica para M1 y M2b
  stats.py            Wilson, regla de tres, percentiles
experiments/          runners de T01 y T02 + calculo de metricas
evidence/runs/        una carpeta por corrida: manifiesto, log de auditoria, resultados
evidence/metrics/     M1 y M2 calculadas desde la evidencia
docs/                 propuesta, diagramas, material de los hitos
```

## Reproducibilidad

Cada corrida escribe un `manifest.json` con el `git_sha`, el perfil, la semilla,
la temperatura, el tope de tokens y el **digest del modelo**. Temperatura 0 y
semilla fija no garantizan determinismo bit a bit entre maquinas ni entre
cuantizaciones, asi que las corridas oficiales se ejecutan en una sola maquina y
el digest queda registrado.

## Tecnologias

Nucleo minimo: Python 3.11, Pydantic, ChromaDB (`all-MiniLM-L6-v2`), SQLite,
Ollama con Llama 3.1 8B Instruct, pytest, logs en JSONL.

Ampliacion (solo si el cronograma alcanza; su ausencia no invalida ninguna
metrica): FastAPI, Streamlit, SQLCipher, PyJWT, Presidio, Garak, promptfoo,
locust, OpenTelemetry con Grafana y Loki, y Mistral 7B como modelo de contraste.

## Uso de IA

Ver la declaracion de uso de IA de cada hito en `docs/`. El modelo local es el
**objeto de estudio** del experimento: ninguna metrica sale de pedirle a una IA
que estime resultados, todas salen de correr el laboratorio.
