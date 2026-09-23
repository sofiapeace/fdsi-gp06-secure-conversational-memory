# Cambios de la propuesta corregida frente a la original

**Original:** `FDSIGP06_Propuesta_Estructurada_2.pdf`, entregada el 05/09/2026.
**Corregida:** `propuesta-corregida.md`, 19/09/2026.

Esta tabla existe para poder llevar los cambios a la plantilla oficial sin tener
que releer los dos documentos completos. Cada fila dice **dónde**, **qué decía**,
**qué debe decir** y **por qué**.

**Renumeración.** Se inserta la sección nueva de controles como **§6**, así que
las secciones 6 a 10 originales pasan a ser 7 a 11, y se agregan §10
(Limitaciones) y §12 (Declaración de uso de IA, antes §10).

| Original | Corregida |
|---|---|
| §6 Pruebas propuestas | §7 |
| §7 Criterios de evaluación | §8 |
| §8 Tecnologías previstas | §9 |
| §9 Referencias iniciales | §11 |
| §10 Declaración de uso de IA | §12 |
| — | **§6 Controles de seguridad (C1–C6)** · nueva |
| — | **§10 Limitaciones y amenazas a la validez** · nueva |

---

## 1 · BLOQUEANTE — Los controles C1–C6 nunca se definían

**Dónde:** sección nueva §6.

**Qué pasaba:** la propuesta cita los controles en T03 (*"el control C6 exige
confirmación explícita"*), en la referencia 4 (*"aplican directamente a nuestros
controles C3 y C5"*) y en la cadena de trazabilidad, pero **ninguna sección los
define**.

**Por qué importa:** sin esa definición no se puede verificar el mapeo
control → prueba → métrica, que es el criterio de aprobación declarado en la
propia propuesta.

**Qué se hizo:** §6 completa, con tabla resumen y, por cada control, definición,
debilidad que corrige, dónde vive en la arquitectura, implementación prevista,
prueba que lo valida y métrica que lo mide.

---

## 2 · La métrica M2 medía dos fallas distintas como si fueran una

**Dónde:** §3 H2, §7 T02, §8 M2.

**Qué decía:** *"Se cuenta cuántas respuestas contienen un dato de otro espacio
de nombres."*

**Qué debe decir:** dos métricas.
- **M2a, fuga de recuperación** — el índice devolvió un documento de otro espacio
  de nombres. Se lee del log, no de la respuesta. Es la falla de C1.
- **M2b, fuga de divulgación** — el dato apareció en la respuesta del modelo.

**Por qué:** puede haber M2a sin M2b porque el modelo decidió no repetir el dato,
y eso no es un control, es suerte. **La corrida del Hito 2 lo confirmó: M2a = 67 %
y M2b = 49 %**, o sea 18 de 100 sondeos en los que el control había fallado y la
respuesta se veía limpia. Reportar solo M2b habría subestimado la falla en 27 %
relativo.

**Consecuencia:** el criterio de aprobación de C1 pasa a ser **M2a = 0**, no
M2b = 0.

---

## 3 · H4 era inevaluable medida extremo a extremo

**Dónde:** §3 H4, §7 T06, §8 M5.

**Qué decía:** *"como máximo 300 ms adicionales de latencia en el percentil 95"*,
sin especificar sobre qué.

**Qué debe decir:** 300 ms sobre el p95 de **`L_mem`** —recuperación, ensamblado
del prompt y filtro de escritura, **sin generación de tokens**—. `L_e2e` se
reporta como contexto.

**Por qué:** en la línea base del Hito 2, la sola diferencia entre p50 y p95 del
turno completo fue de **1 384 ms en T01** y **1 248 ms en T02**: entre cuatro y
seis veces el presupuesto entero de la hipótesis, **sin que existiera todavía
ningún control**. La ruta de memoria es 67 ms p50 y 100 ms p95, el 1,7 % del
turno. Sobre `L_mem` el umbral es exigente y medible; extremo a extremo es
invisible.

---

## 4 · La Figura 1 necesita un segundo canal de recuperación

**Dónde:** §4 y Figura 1; §5 y Figura 2.

**Qué muestra la figura:** un solo camino de la memoria al prompt, *"recupera
top-k por similitud, sin filtro de propietario"*.

**Qué debe mostrar:** dos canales. **Perfil fijado** —lo que parece preferencia
permanente entra en todas las sesiones, sin pasar por la búsqueda— y **búsqueda
por similitud**. En la Figura 2, que **C1 filtra los dos**.

**Por qué:** con solo similitud, T01 no prueba persistencia. La instrucción no se
parece a la pregunta, y en un almacén casi vacío top-k la devuelve por descarte
—con k = 4 y un documento guardado, el índice lo entrega aunque la distancia sea
pésima—. El ataque "funcionaría" por un artefacto del laboratorio vacío. Con el
canal de perfil, T01 explota el perfil fijado y T02 la búsqueda sin filtro: cada
prueba aísla una debilidad distinta.

**Hecho.** Las dos figuras se rehicieron en `docs/diagramas/`, con fuente
`.drawio` editable y exportación `.svg` lista para pegar en el documento. Las
originales quedan en `docs/diagramas/originales/` solo como referencia.

---

## 5 · Las pruebas no declaraban memoria legítima de fondo

**Dónde:** §7 T01 y T02.

**Qué se agregó:** ambos experimentos siembran 20 registros de memoria legítima
antes de atacar. En T02 el ruido es **del usuario B**, de modo que el índice tiene
que *elegir* el dato ajeno por encima del propio de quien pregunta.

**Por qué:** sin ruido, el almacén queda con uno o dos registros y top-k devuelve
el dato buscado por descarte. "La memoria estaba vacía y salió lo único que había"
no demuestra nada.

**Además:** los datos sembrados de A se redactan **sin** pistas de preferencia
permanente, para que queden episódicos y no se fijen al perfil. Si se fijaran, T02
estaría midiendo el mismo canal que T01.

---

## 6 · freezegun y APScheduler iban a chocar en T04

**Dónde:** §7 T04, §6 C5, §9 Pruebas.

**Qué decía:** *"Se adelanta el reloj del laboratorio 48 h con freezegun."*

**Qué debe decir:** el reloj se adelanta **inyectando un reloj controlado**. La
purga es una función pura `purge_expired(now)` que la prueba invoca con el `now`
que quiera; APScheduler solo la llama en producción. freezegun queda como
verificación secundaria.

**Por qué:** freezegun manipula el reloj del proceso, y el hilo de fondo del
scheduler tiene su propio temporizador y no lo ve de forma confiable. T04 habría
quedado intermitente.

---

## 7 · La prueba de borrado de T05 podía convertirse en una fuga

**Dónde:** §7 T05, §6 C5.

**Qué decía:** *"se emite una prueba de borrado con el hash del registro y la
marca de tiempo en el log."*

**Qué debe decir:** **HMAC-SHA256 con la clave del sistema**, o solo el
`record_id` con las capas afectadas y la marca de tiempo.

**Por qué:** un SHA-256 plano sobre un dato corto y de baja entropía —una
dirección, un número de tarjeta— se invierte por fuerza bruta en segundos. El log
de solo-agregado se convertiría en una copia recuperable de justo lo que se
prometió borrar. **La verificación del borrado no puede violar el borrado.**

---

## 8 · Los tamaños de muestra dejaban los umbrales al filo

**Dónde:** §3 H1, §7 T01, §8 M1 y M3, §10.

**Qué se agregó:** intervalo de Wilson en **toda** proporción; **40 sesiones** en
el perfil Secure de T01; nota explícita de granularidad en M1 y M3.

**Por qué:** con 20 sesiones cada acierto vale 5 puntos porcentuales, así que
"TPI ≤ 5 %" significa literalmente "como máximo 1 acierto de 20": un solo falso
positivo del detector cambia el veredicto. Igual en M3: "recall ≥ 90 %" sobre 20
maliciosos es "como máximo 2 falsos negativos".

---

## 9 · Faltaba declarar la circularidad del LLM juez

**Dónde:** §6 C3, §10.

**Qué se agregó:** el LLM juez del filtro C3 es el mismo modelo que es objeto del
estudio. Eso produce **circularidad** —el modelo vulnerable decide qué se guarda—
y **superficie de ataque** —el texto del atacante entra al prompt del juez, así
que el juez también es inyectable—. Mitigación: aplicarle el mismo C2 y restringir
su salida a un enumerado validado con Pydantic. Se reporta como limitación, no
como resuelto.

---

## 10 · Faltaba el criterio de desempate entre evaluadores en M5

**Dónde:** §8 M5.

**Qué decía:** *"evaluado con una rúbrica por dos integrantes"*, sin decir qué
pasa si discrepan.

**Qué debe decir:** se reporta el **kappa de Cohen** entre los dos evaluadores y
los desacuerdos los resuelve el tercer integrante.

---

## 11 · Reproducibilidad del modelo

**Dónde:** §9.

**Qué se agregó:** tope de tokens fijo (`num_predict = 256`) y registro del
**digest del modelo** en cada corrida.

**Por qué:** sin tope de tokens, la varianza de generación hace que la latencia no
sea comparable entre corridas. Y temperatura 0 más semilla fija **no** garantizan
determinismo bit a bit entre máquinas ni entre cuantizaciones: el digest es el
único identificador que permite verificar que se corrió el mismo peso.

---

## 12 · Precisión sobre los embeddings

**Dónde:** §9.

**Qué decía:** *"la librería sentence transformers con el modelo
all-MiniLM-L6-v2"*.

**Qué debe decir:** **el mismo modelo**, en la compilación **ONNX** que trae
ChromaDB por defecto. No cambia el espacio de embeddings y evita arrastrar
PyTorch (~2 GB).

---

## 13 · El mapeo a MITRE ATLAS ya está hecho

**Dónde:** §7, cierre de la tabla de pruebas.

**Qué decía:** *"El mapeo a técnicas de MITRE ATLAS lo documentamos en el
Hito 2."*

**Qué debe decir:** la tabla completa. Hallazgo principal: ATLAS cataloga este
problema como técnica propia, **AML.T0080.000 — AI Agent Context Poisoning:
Memory** (táctica Persistence), con mitigación dedicada **AML.M0031 Memory
Hardening**. Los controles C1–C6 son una instanciación medible de esa mitigación.

Verificado contra `atlas.mitre.org` el 19/09/2026. Detalle en
`docs/hito2/mapeo-mitre-atlas.md`.

---

## 14 · Los 100 sondeos de T02 deben ser distintos

**Dónde:** §7 T02.

**Qué se precisó:** son 100 prompts **diferentes**, por combinación documentada de
10 plantillas × 10 objetivos.

**Por qué:** si fueran 100 repeticiones del mismo prompt, el denominador de M2
estaría inflado y la métrica no significaría lo que dice.

---

## 15 · Sección nueva de limitaciones

**Dónde:** §10, nueva.

Recoge las siete amenazas a la validez: tamaño de muestra, modelo único,
determinismo, circularidad del juez, límites de la detección automática,
alucinación de datos por parte del modelo, y el carácter estadístico —no
estructural— de C2.

---

## 16 · Estado real del cronograma

**Dónde:** cierre, "Viabilidad".

**Qué se agregó:** tabla de estado al 19/09/2026, diciendo explícitamente que el
frente de ingeniería arrancó con retraso y que se recuperó concentrándose en el
núcleo mínimo.

**Por qué:** el cronograma original se deja **tal cual**, sin reescribirlo. Ajustar
las fechas hacia atrás para que cuadren sería deshonesto; declarar el retraso y
cómo se manejó, no.

---

## 17 · Referencias verificadas contra la fuente

**Dónde:** §11.

La §12 afirma que *"las referencias se comprobaron contra sus fuentes
originales"*. Esa frase es una declaración de integridad académica, y dos
referencias tenían datos que no se habían comprobado. Se verificaron el
19/09/2026.

**Referencia 2 — dos correcciones.** La fecha (09/12/2025) y ASI06 como *Memory &
Context Poisoning* se confirman en `genai.owasp.org`. Pero el título oficial lleva
el año —*OWASP Top 10 for Agentic Applications **2026***— y **la mención al
"London Agentic Security Summit" se eliminó**: no aparece en ninguna página
oficial del proyecto como sede de esta publicación. "London" sí figura como una
de las cuatro sedes del *kick-off* de agosto de 2025, que es un evento distinto.

**Referencia 4 — verificada por completo** y además refuerza el trabajo.
Identificador, título, los seis autores, fecha y las dos defensas coinciden. Y su
resultado central —*"realistic conditions with pre-existing legitimate memories
dramatically reduce attack effectiveness"*— **respalda de forma independiente la
decisión de sembrar memoria legítima de fondo** (cambio 5). Evalúan sobre
Llama-3.1-8B-Instruct, el mismo modelo del laboratorio. Vale la pena citarlo en
el informe justo donde se justifica el ruido de fondo.

**Referencia 6** ya se había verificado contra `atlas.mitre.org`.

> **Por qué importa.** Los modelos de lenguaje producen citas plausibles pero
> falsas: identificadores con el formato correcto que no corresponden a ningún
> trabajo, fechas de eventos que suenan bien. En un documento que declara haber
> verificado sus fuentes, y en una materia de seguridad, eso pesa.

---

## Lo que sigue pendiente del equipo

1. **Portar este documento a la plantilla oficial** de la asignatura. Aquí está el
   texto; el formato con encabezados y pies institucionales lo pone la plantilla.
2. **Revisar la tabla de estado del cronograma** al cierre del documento: declara
   el retraso del frente de ingeniería. Es una decisión del equipo, no una
   corrección técnica.
