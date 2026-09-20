# Revisión del Hito 1 y plan de acción para el Avance 1 (Hitos 1 + 2)

> **Actualización 19/09/2026, 22:00.** Los días 0 a 3 del plan ya están
> ejecutados: el laboratorio Unsecure corre, T01 y T02 se ejecutaron sobre
> Llama 3.1 8B con evidencia versionada, y M1 y M2 están calculadas. También
> están cerrados el vacío de los controles C1–C6 y el mapeo a MITRE ATLAS.
> Queda el día 4 (integrar correcciones al documento del Hito 1) y el día 5
> (presentación y video). Ver `docs/hito2/informe-avance.md`.

Equipo FDSI-GP-06 · Isaac Burgos · Jose Lancheros · Sofía García
Fecha de elaboración: 2026-09-19 (sábado)
Fuente revisada: `docs/hito1/FDSIGP06_Propuesta_Estructurada_2.pdf`

---

## 0. Resumen ejecutivo

La propuesta es **sólida y aprobable**: tiene cadena de trazabilidad completa
(problema → arquitectura → prueba → evidencia → control → métrica), hipótesis
falsables con umbrales numéricos, línea base reportada como resultado observado
y no fijada de antemano, alcance ético bien acotado y una separación explícita
entre núcleo mínimo y ampliación. Eso es más de lo que suele traer una propuesta
de seminario.

El problema **no es el documento, es el calendario**. Según el cronograma de la
propia propuesta:

| Ventana | Compromiso | Estado real al 19/09 |
|---|---|---|
| 05–12/09 | Laboratorio Unsecure funcionando, T01 y T02 con evidencia, presentación y video del Hito 2 | **No iniciado** (repo con 1 commit, solo README) |
| 13–20/09 | Implementar C1–C6 y ejecutar T01–T06 | No iniciado |
| 21–26/09 | Análisis comparativo, paper IEEE, presentación, demo | No iniciado |

Vamos con ~1 semana de atraso sobre el frente de ingeniería. La buena noticia es
que el Avance 1 (Hitos 1 + 2) **no exige los controles implementados**: exige el
laboratorio Unsecure funcionando, T01 y T02 con evidencia, el mapeo a MITRE ATLAS
y el material de presentación. Eso sí es alcanzable en 5–6 días de trabajo
repartido entre tres personas.

**Veredicto:** el Hito 1 se cierra con 3 correcciones de documento (una de ellas
obligatoria: los controles C1–C6 nunca se definen). El Hito 2 se logra si el
laboratorio Unsecure queda corriendo **antes del martes 22/09**.

---

## 1. Qué exige cada hito (deducido del documento)

El PDF no trae la rúbrica del docente, así que esto está inferido del propio
cronograma y de las menciones dispersas al Hito 2. **Hay que contrastarlo con la
guía de la asignatura antes de congelar el alcance.**

### Hito 1 — Propuesta estructurada (entregado el 05/09)
- Secciones 1–10 según plantilla oficial. ✅ Ya están.
- Figuras 1 y 2 (arquitecturas Unsecure y Secure). ✅ Ya están en el PDF, ❌ faltan los fuentes `.drawio`.
- ❌ **Falta la definición de los controles C1–C6** (ver hallazgo A).

### Hito 2 — Avance técnico (lo que dice el documento textualmente)
1. *"dejamos el laboratorio Unsecure funcionando"* → código ejecutable y reproducible.
2. *"sacamos T01 y T02 con evidencia inicial"* → ejecución real + logs + métricas M1 y M2 de línea base.
3. *"El mapeo a técnicas de MITRE ATLAS lo documentamos en el Hito 2"* → tabla T01–T03 → técnicas ATLAS.
4. *"preparamos la presentación y el video demo del Hito 2"*.
5. Implícito: repositorio ordenado con la evidencia versionada (la propuesta se
   compromete a *"Git y GitHub para versionar código, prompts, semillas y evidencias"*).

---

## 2. Revisión del documento del Hito 1

### 2.1 Lo que está bien y hay que conservar

- **Cadena de trazabilidad explícita.** Es el criterio de aprobación y está cumplido.
- **Línea base como resultado observado.** H1 dice *"La línea base la reportamos como resultado observado y no la fijamos de antemano"*. Metodológicamente es correcto y evita acusaciones de resultado cocinado.
- **Regla de tres bien aplicada.** Con 0 aciertos en 100 ensayos, la cota superior del IC 95 % es 3/100 = 3 %. Está correcto y es exactamente lo que hay que reportar cuando el resultado es cero.
- **Núcleo mínimo vs. ampliación.** Declarar que SQLCipher, PyJWT, Presidio, Garak, promptfoo, locust, Grafana/Loki y Mistral 7B son opcionales, y que su ausencia no invalida ninguna métrica, es la mejor decisión de gestión de riesgo del documento. **Respetarla.**
- **Alcance y ética.** Laboratorio cerrado, dos usuarios simulados, datos inventados, tarjeta de prueba `4111 1111 1111 1111` (número de test estándar, no es un PAN real), dominio `evil.local`. Sin terceros. Correcto.
- **Declaración de uso de IA** con separación clara entre "IA que redacta" e "IA que es el objeto de estudio". Hay que replicarla actualizada en cada hito.

### 2.2 Hallazgos que hay que corregir

#### A. [BLOQUEANTE] Los controles C1–C6 nunca se definen
Aparecen en la prueba T03 (*"el control C6 exige confirmación explícita"*), en la
referencia 4 (*"aplican directamente a nuestros controles C3 y C5"*) y en la
cadena de trazabilidad, pero **no hay ninguna sección que los describa**. El
lector no puede evaluar el diseño ni verificar el mapeo control→prueba→métrica.

*Corrección:* añadir una sección "Controles de seguridad (C1–C6)" con una fila por
control: identificador, definición en una frase, dónde vive en la arquitectura,
qué prueba lo valida, qué métrica lo mide. Borrador base a partir de la cadena de
trazabilidad:

| ID | Control | Dónde | Valida | Mide |
|---|---|---|---|---|
| C1 | Aislamiento por espacio de nombres `tenant_id` / `user_id` / `session_id`, obligatorio en toda consulta vectorial | Retriever | T02 | M2 |
| C2 | Memoria como dato no ejecutable: se inyecta delimitada, en rol de usuario, nunca con autoridad de sistema | Ensamblador de prompt | T01, T03 | M1 |
| C3 | Filtro de escritura con esquema tipado: clasifica candidato como hecho / instrucción / secreto antes de persistir | Writer | T01, T03 | M1, M3 |
| C4 | Procedencia firmada con HMAC-SHA256 sobre el registro (origen, autor, sesión) | Store | T03 | M3 |
| C5 | Tiempo de vida por categoría y borrado verificable en las tres capas (fila, embedding, caché) | Lifecycle | T04, T05 | M4 |
| C6 | Autorización por origen para herramientas + log de auditoría de solo-agregado | Tools / Audit | T03 | M3 |

#### B. [ALTO] El tamaño de muestra hace que los umbrales sean frágiles
- **M1:** 20 sesiones ⇒ cada sesión vale 5 puntos porcentuales. "TPI ≤ 5 %" significa literalmente *como máximo 1 acierto de 20*. Un solo falso positivo de la expresión regular tumba la hipótesis.
- **M3:** recall ≥ 90 % sobre 20 maliciosos ⇒ máximo 2 falsos negativos. FPR ≤ 10 % sobre 40 normales ⇒ máximo 4 falsos positivos.

*Corrección:* subir T01 a 40 sesiones si el tiempo de ejecución lo permite
(con un modelo local de 8B, 40 sesiones son minutos, no horas), y **reportar
intervalos de confianza de Wilson** además del valor puntual. Si no se sube la
muestra, declarar explícitamente la granularidad de 5 pp como limitación.

#### C. [ALTO] "Fuga" en M2 necesita dos niveles, no uno
Hoy M2 cuenta *"cuántas respuestas contienen un dato de otro espacio de nombres"*.
Eso mezcla dos fallas distintas y hace que el control se vea mejor de lo que es:

1. **Fuga de recuperación:** el retriever devuelve un documento de otro namespace (falla de C1).
2. **Fuga de divulgación:** ese dato aparece en la respuesta del modelo.

Puede haber (1) sin (2) porque el modelo decidió no repetirlo — y eso **no es un
control, es suerte**. Hay que medir las dos y reportarlas por separado. El
documento ya insinúa esto al decir que *"El resultado se contrasta con el log de
recuperación, que guarda los documentos devueltos y su user_id"*; solo falta
convertirlo en dos métricas: `M2a` (recuperación) y `M2b` (divulgación).

#### D. [MEDIO] `freezegun` + `APScheduler` van a chocar en T04
`freezegun` manipula el reloj del proceso. La purga programada de APScheduler
corre en otro hilo con su propio temporizador y **no va a ver el reloj congelado
de forma confiable**, así que T04 puede volverse intermitente.

*Corrección:* implementar la purga como una función pura invocable —
`purge_expired(now: datetime) -> PurgeReport` — y que APScheduler solo la llame en
producción. La prueba invoca la función con el `now` que quiera. Mejor aún:
inyectar un reloj (`now_fn`) en toda la capa de memoria y usar `freezegun` solo
como verificación secundaria.

#### E. [MEDIO] La "prueba de borrado" con hash puede volverse una fuga
T05 dice que se emite una prueba de borrado *"con el hash del registro"* en un log
de solo-agregado. Si ese hash es un SHA-256 plano sobre un dato corto y de baja
entropía (una dirección, un número de tarjeta de prueba, un nombre), **es
reversible por fuerza bruta en segundos**: el log de auditoría se convierte en una
copia recuperable justo de lo que se prometió borrar.

*Corrección:* usar HMAC-SHA256 con una clave del sistema (no del registro) sobre
el JSON canónico del registro, o registrar únicamente el `record_id` + las capas
afectadas + la marca de tiempo. Esto es, además, **un hallazgo vendible en el
paper**: "el propio mecanismo de verificación de borrado puede violar el borrado".

#### F. [MEDIO] H4 es casi imposible de probar como está redactada
*"como máximo 300 ms adicionales de latencia en el percentil 95"* medido
extremo a extremo sobre un modelo local: la varianza de generación de tokens de
un 8B es de **cientos de milisegundos o segundos**, muy por encima del efecto que
producen los controles. La señal queda enterrada en el ruido.

*Corrección:* medir dos latencias y declarar la segunda como la que prueba H4:
- `L_e2e`: turno completo (dato de contexto, se reporta).
- `L_mem`: **solo la ruta de memoria** (filtro de escritura + recuperación + ensamblado del prompt), excluyendo la generación. Es lo único que los controles afectan.

Además: fijar `num_predict` (tope de tokens) para acotar la varianza de generación.

#### G. [MEDIO] El "LLM juez" dentro del filtro de escritura es circular y atacable
La sección 10 declara que Llama 3.1 8B es a la vez el objeto de estudio y el juez
del filtro C3. Dos consecuencias que hay que documentar:
1. **Circularidad:** el mismo modelo que es vulnerable decide qué se guarda.
2. **Superficie de ataque:** el texto del atacante entra al prompt del juez ⇒ el juez es inyectable. Hay que aplicarle el mismo C2 (entrada delimitada como dato) y forzar salida restringida (etiqueta de un enum, JSON con esquema Pydantic).

No invalida el diseño, pero tiene que estar en Limitaciones y amenazas a la validez.

#### H. [BAJO] Reproducibilidad del modelo
Temperatura 0 + semilla fija no garantizan determinismo bit a bit entre máquinas
ni entre cuantizaciones. *Corrección:* registrar en la evidencia el **digest
sha256 del modelo** (`ollama show`), la cuantización y la versión de Ollama.

#### I. [BAJO] Concordancia entre evaluadores en M5
La utilidad se evalúa *"con una rúbrica por dos integrantes"* pero no se dice qué
pasa cuando discrepan. *Corrección:* reportar kappa de Cohen, o al menos el número
de desacuerdos y el criterio de desempate (tercer integrante).

#### J. [BAJO] Cosas de forma
- Faltan los `.drawio` editables de las Figuras 1 y 2 en el repo (el documento se compromete a ellos en la sección 8).
- T02 debe especificar que los 100 sondeos son **prompts distintos** (o una plantilla documentada con variaciones); si son 100 repeticiones del mismo prompt, el denominador está inflado.
- Verificar contra la fuente original la fecha de la referencia 2 (London Agentic Security Summit, 09/12/2025) y el identificador de la referencia 4 (`arXiv:2601.05504`).

---

## 3. Estructura de repositorio propuesta

```
fdsi-gp06-secure-conversational-memory/
├── README.md                     # qué es, cómo se corre, cómo se reproduce
├── pyproject.toml                # uv + Python 3.11
├── Makefile                      # make lab / make t01 / make t02 / make metrics
├── docker-compose.yml            # perfiles: unsecure | secure
├── docs/
│   ├── hito1/                    # propuesta + correcciones (sección C1–C6)
│   ├── hito2/                    # informe de avance, ATLAS, presentación, guion demo
│   └── diagramas/                # figura1.drawio/.png, figura2.drawio/.png
├── src/memlab/
│   ├── config.py                 # Profile.UNSECURE | Profile.SECURE (una sola base de código)
│   ├── clock.py                  # reloj inyectable (hallazgo D)
│   ├── llm.py                    # cliente Ollama: temp 0, seed fija, num_predict fijo
│   ├── schema.py                 # MemoryRecord (Pydantic): tenant/user/session/kind/ttl/provenance
│   ├── memory/
│   │   ├── store.py              # SQLite (hechos) + ChromaDB (embeddings) + caché de sesión
│   │   ├── writer.py             # C3 — no-op en unsecure
│   │   ├── retriever.py          # C1 — sin filtro de namespace en unsecure
│   │   └── lifecycle.py          # C5 — purge_expired(now) + borrado 3 capas
│   ├── prompt.py                 # C2 — en unsecure la memoria va en rol system
│   ├── provenance.py             # C4 — HMAC-SHA256
│   ├── tools.py                  # enviar_correo simulada + C6
│   ├── audit.py                  # log JSONL de solo-agregado
│   └── orchestrator.py           # un turno de chat
├── tests/
│   ├── test_t01_instruccion_dormida.py
│   ├── test_t02_fuga_entre_usuarios.py
│   └── ...                       # T03–T06 llegan en el Hito 3
├── experiments/
│   ├── run_t01.py                # lanza 20–40 sesiones NUEVAS (proceso nuevo por sesión)
│   ├── run_t02.py                # 100 sondeos distintos
│   └── compute_metrics.py        # lee evidence/runs/** → evidence/metrics/*.json
└── evidence/
    ├── runs/<fecha>-<perfil>-<git_sha>/   # prompts, respuestas, logs de recuperación
    └── metrics/                            # m1.json, m2.json, tablas para el informe
```

**Decisión clave:** una sola base de código con dos perfiles, exactamente como
dice la propuesta. Nada de dos carpetas duplicadas: el diff entre Unsecure y
Secure tiene que ser *solo* los controles, y eso es lo que hace creíble el
experimento comparativo.

---

## 4. Plan de acción día a día

Supuesto: entrega del Avance 1 el **viernes 25/09** (confirmar con el docente).
Tres frentes en paralelo, como ya propone el documento.

### Día 0 — sábado 20/09 (½ día) · Desbloqueo
- [ ] `brew install ollama && ollama pull llama3.1:8b-instruct-q4_K_M` — **hacer esto primero**, la descarga son ~5 GB y es el único cuello de botella que no se puede acelerar. (Ollama **no está instalado** en esta máquina; Docker, uv, git y gh sí.)
- [ ] Confirmar con el docente: fecha real de entrega del Avance 1, formato (¿informe aparte o propuesta corregida?), duración del video demo.
- [ ] Scaffold del repo (estructura de §3), `pyproject.toml` con uv y Python 3.11, `Makefile`, `.gitignore`.
- [ ] Exportar Figuras 1 y 2 a `.drawio` + `.png` en `docs/diagramas/`.

### Día 1 — domingo 21/09 · Laboratorio Unsecure, parte A
- [ ] `schema.py`: `MemoryRecord` con Pydantic (`tenant_id`, `user_id`, `session_id`, `kind`, `content`, `created_at`, `ttl_s`, `provenance`). El esquema se escribe **ya**, aunque en el perfil unsecure no se valide nada: así el diff Secure es mínimo.
- [ ] `store.py`: SQLite + ChromaDB (`all-MiniLM-L6-v2`) + caché de sesión. Escritura sin validar, recuperación **sin filtro de metadatos** (la debilidad que explota T02).
- [ ] `prompt.py`: memoria recuperada inyectada en el **rol system** (la debilidad que explota T01).
- [ ] `llm.py`: Ollama con `temperature=0`, `seed` fija, `num_predict` fijo; registrar digest del modelo.
- [ ] `audit.py`: JSONL de solo-agregado con turno, memorias recuperadas + su `user_id`, prompt final y respuesta. **Sin este log no hay evidencia y no hay M2a.**

### Día 2 — lunes 22/09 · Laboratorio Unsecure, parte B + T01
- [ ] `orchestrator.py` + CLI `memlab chat --profile unsecure --user A --session S1` (esta CLI es la que se graba en el video).
- [ ] `experiments/run_t01.py`: sesión 1 inyecta la instrucción dormida; luego 20 (mejor 40) sesiones nuevas, **cada una en un proceso nuevo** con `session_id` nuevo y caché vacía, una pregunta normal distinta por sesión.
- [ ] Detector automático por expresión regular de `http://evil.local` + revisión manual de dudosos, con el veredicto de cada sesión guardado en la evidencia.
- [ ] **Hito de control: al cerrar el lunes el laboratorio Unsecure tiene que estar corriendo.** Si no, se activa el plan de contingencia (§6).

### Día 3 — martes 23/09 · T02 + métricas
- [ ] `experiments/run_t02.py`: usuario A guarda el dato sensible inventado; usuario B lanza 100 sondeos **distintos** desde otra sesión.
- [ ] Medir M2a (fuga de recuperación, desde el log) y M2b (fuga de divulgación, desde la respuesta) — hallazgo C.
- [ ] `compute_metrics.py` → `evidence/metrics/m1.json`, `m2.json`, con valor puntual + IC de Wilson (hallazgo B).
- [ ] Congelar la corrida "oficial" del Hito 2: carpeta `evidence/runs/` etiquetada con el `git_sha`, la semilla y el digest del modelo.

### Día 4 — miércoles 24/09 · Documentación
- [ ] **Corrección del Hito 1:** añadir la sección de controles C1–C6 (hallazgo A) y las notas de metodología de los hallazgos C, D, F, G.
- [ ] **Mapeo MITRE ATLAS** de T01–T03 (pendiente comprometido en el documento). Candidatos a verificar en `atlas.mitre.org` — **no copiar sin verificar los IDs contra la matriz vigente**:
  - T01 (instrucción dormida) → inyección de prompt directa + persistencia en memoria del agente.
  - T02 (fuga entre usuarios) → divulgación de información sensible por el LLM.
  - T03 (inyección indirecta desde documento) → inyección de prompt indirecta.
- [ ] Informe de avance del Hito 2: qué se construyó, cómo se corre, resultados M1/M2 de línea base, qué falta para el Hito 3.
- [ ] Declaración de uso de IA actualizada para el Hito 2.

### Día 5 — jueves 25/09 · Presentación y demo
- [ ] Presentación (sugerido: problema → arquitectura Unsecure → demo T01 en vivo → demo T02 → métricas de línea base → controles C1–C6 que vienen → ATLAS/OWASP).
- [ ] Video demo: guion escrito primero, grabación después. Lo más vendible es **T01 en vivo**: cerrar el proceso, abrirlo de nuevo, hacer una pregunta inocente y ver salir `http://evil.local`. Eso se entiende en 30 segundos.
- [ ] `git tag hito2` + release en GitHub con la evidencia adjunta.

---

## 5. Reparto sugerido (tres frentes en paralelo, como dice la propuesta)

| Frente | Responsable sugerido | Entregables |
|---|---|---|
| F1 · Orquestador y laboratorio Unsecure | — | `store.py`, `prompt.py`, `llm.py`, `orchestrator.py`, CLI |
| F2 · Evidencia, auditoría y métricas | — | `audit.py`, `run_t01.py`, `run_t02.py`, `compute_metrics.py`, `evidence/` |
| F3 · Documentación, diagramas y presentación | — | sección C1–C6, mapeo ATLAS, informe, diapositivas, guion y video |

F3 puede arrancar **hoy mismo** sin esperar a que haya código: la sección C1–C6 y
el mapeo ATLAS no dependen del laboratorio. Es la forma más barata de recuperar
tiempo.

---

## 6. Riesgos y contingencias

| Riesgo | Probabilidad | Mitigación |
|---|---|---|
| El atraso de calendario impide llegar al 25/09 | **Alta** | Respetar el núcleo mínimo de la propuesta. Nada de SQLCipher, PyJWT, Presidio, Garak, promptfoo, locust ni Grafana/Loki en el Avance 1: la propuesta ya declaró que son ampliación y que su ausencia no invalida ninguna métrica. |
| El Unsecure no alcanza TPI ≥ 70 % en T01 | Media | Es un **resultado válido**, no un fracaso: se reporta como observado (la propuesta ya se blindó diciendo que la línea base no se fija de antemano). Si aun así se quiere subir la señal: inyectar la memoria en rol system con formulación imperativa, y verificar que la recuperación efectivamente la trae (se ve en el log). |
| Determinismo insuficiente entre máquinas | Media | Una sola máquina ejecuta las corridas oficiales; digest del modelo, semilla y `git_sha` van en la evidencia. |
| Ollama + descarga del modelo se demora | Baja | Lanzar el `ollama pull` hoy, en segundo plano. |
| `freezegun` rompe T04 | Media | Reloj inyectable desde el día 1 (hallazgo D). Afecta al Hito 3, pero el diseño se decide ahora. |

---

## 7. Definición de "listo" para el Avance 1

- [ ] `git clone` + `make lab` levanta el laboratorio Unsecure en una máquina limpia.
- [ ] `make t01` y `make t02` corren solos y escriben en `evidence/runs/`.
- [ ] `evidence/metrics/m1.json` y `m2.json` con valor puntual e IC.
- [ ] Log de auditoría con prompts finales, memorias recuperadas (con su `user_id`) y respuestas de todas las sesiones.
- [ ] Documento del Hito 1 corregido, con la sección C1–C6.
- [ ] Tabla de mapeo a MITRE ATLAS de T01–T03, con IDs verificados en la fuente.
- [ ] Informe de avance del Hito 2.
- [ ] Figuras 1 y 2 con fuente `.drawio` versionado.
- [ ] Presentación + video demo.
- [ ] Declaración de uso de IA actualizada.
- [ ] Tag `hito2` en GitHub.
