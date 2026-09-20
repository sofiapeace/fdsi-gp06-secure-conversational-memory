# Mapeo a MITRE ATLAS

**Pendiente comprometido en el Hito 1.** La propuesta dice, en la seccion 6:
*"El mapeo a tecnicas de MITRE ATLAS lo documentamos en el Hito 2."* Este
documento lo cierra.

**Fuente y verificacion.** Todos los identificadores, nombres y tacticas se
verificaron directamente contra `https://atlas.mitre.org` (paginas
`/techniques` y `/mitigations`) el **19/09/2026**. Los nombres se citan como
aparecen en la matriz, en ingles. ATLAS se actualiza: antes de la entrega
conviene revalidar que los IDs sigan vigentes.

---

## Hallazgo principal

ATLAS tiene una tecnica que describe **exactamente** el problema de este
proyecto:

> **AML.T0080.000 — AI Agent Context Poisoning: Memory** (tactica: Persistence)
> *"Adversaries may manipulate the memory of a large language model (LLM) in
> order to persist changes to the LLM across future chat sessions."*

Y una mitigacion dedicada:

> **AML.M0031 — Memory Hardening**
> *"Memory Hardening protects persistent state used by AI agents, including
> saved preferences, episodic or semantic memories, conversation summaries,
> stor[ed]…"*

Esto refuerza la propuesta en dos frentes. Primero, confirma que el problema
elegido esta reconocido como tecnica propia en la taxonomia de referencia y no
es un caso de borde de la inyeccion de prompts. Segundo, da un anclaje directo
para los controles C1–C6: son una instanciacion concreta y medible de
`AML.M0031`, que la matriz enuncia a nivel de principio.

---

## Mapeo de las pruebas

| Prueba | Tecnica ATLAS | Tactica | Por que aplica |
|---|---|---|---|
| **T01** Instruccion dormida | **AML.T0051.000** LLM Prompt Injection: Direct | Execution | El usuario B escribe la instruccion como usuario legitimo del asistente. |
| **T01** | **AML.T0080.000** AI Agent Context Poisoning: Memory | Persistence | Es el nucleo de T01: la instruccion sobrevive al cierre de la sesion y se reactiva sola en sesiones futuras. La inyeccion es el vector; la persistencia en memoria es el efecto que se mide con M1. |
| **T02** Fuga entre usuarios | **AML.T0057** LLM Data Leakage | Exfiltration | *"The leaked information may come from … information from other users of the LLM."* Es literalmente el escenario de T02 y corresponde a la fuga de divulgacion (M2b). |
| **T02** | **AML.T0085.000** Data from AI Services: RAG Databases | Collection | Los sondeos de B hacen que el sistema recupere documentos de la base vectorial que pertenecen a A. Corresponde a la fuga de recuperacion (M2a). |
| **T03** Inyeccion indirecta desde documento | **AML.T0051.001** LLM Prompt Injection: Indirect | Execution | *"injected indirectly via a separate data channel … such as text pulled from documents … frequently hidden or obfuscated … for example as invisible text."* Coincide con el texto oculto del documento de T03. |
| **T03** | **AML.T0070** RAG Poisoning | Persistence | El contenido del documento queda indexado y contamina hilos futuros. |
| **T03** | **AML.T0071** False RAG Entry Injection | Defense Evasion | El texto oculto se ingiere y el modelo lo trata como un resultado legitimo de la base. |
| **T03** (consecuencia) | **AML.T0086** Exfiltration via AI Agent Tool Invocation | Exfiltration | La herramienta `enviar_correo` usada sin confirmacion es la via de salida que el ataque busca. |
| **T04** Caducidad · **T05** Borrado | *sin tecnica propia* | — | ATLAS cataloga acciones del adversario. La ausencia de caducidad y el borrado incompleto son **debilidades del sistema**, no tecnicas: habilitan la persistencia de `AML.T0080.000`. Se sustentan por el lado normativo (Ley 1581 de 2012) y por `AML.M0031`. |
| **T06** Utilidad | *no aplica* | — | Prueba de no regresion, no escenario de ataque. |

---

## Mapeo de los controles a mitigaciones ATLAS

| Control | Mitigacion ATLAS | Nombre |
|---|---|---|
| C1 Aislamiento por espacio de nombres | **AML.M0032** · **AML.M0027** · **AML.M0019** | Segmentation of AI Agent Components · Single-User AI Agent Permissions Configuration · Control Access to AI Models and Data in Production |
| C2 Memoria como dato no ejecutable | **AML.M0020** · **AML.M0033** | Generative AI Guardrails · Input and Output Validation for AI Agent Components |
| C3 Filtro de escritura tipado | **AML.M0033** · **AML.M0031** | Input and Output Validation · Memory Hardening |
| C4 Procedencia firmada | **AML.M0025** | Maintain AI Dataset Provenance |
| C5 Tiempo de vida y borrado verificable | **AML.M0031** | Memory Hardening |
| C6 Autorizacion por origen y auditoria | **AML.M0029** · **AML.M0030** · **AML.M0024** | Human In-the-Loop for AI Agent Actions · Restrict AI Agent Tool Invocation on Untrusted Data · AI Telemetry Logging |

---

## Mapeo combinado con OWASP (consolidado del Hito 1 + ATLAS)

| Prueba | OWASP LLM 2025 | OWASP Agentic | MITRE ATLAS |
|---|---|---|---|
| T01 | LLM01 Prompt Injection | ASI06 Memory & Context Poisoning | AML.T0051.000 + AML.T0080.000 |
| T02 | LLM02 Sensitive Information Disclosure · LLM08 Vector & Embedding Weaknesses | — | AML.T0057 + AML.T0085.000 |
| T03 | LLM01 | ASI06 | AML.T0051.001 + AML.T0070 + AML.T0071 |
| T04 | — | ASI06 | (habilita AML.T0080.000) |
| T05 | — | ASI06 | (habilita AML.T0080.000) |

Los tres marcos coinciden en el mismo punto: **la memoria persistente es una
superficie de escritura controlada por quien habla con el modelo**, y lo que
falta no es un filtro de contenido sino un limite de confianza.

---

## Como citar en el paper

- MITRE ATLAS. *Adversarial Threat Landscape for Artificial-Intelligence Systems.*
  `https://atlas.mitre.org` (consultado el 19/09/2026).
- Tecnicas: AML.T0051 y subtecnicas .000 / .001, AML.T0057, AML.T0070, AML.T0071,
  AML.T0080 y subtecnica .000, AML.T0085.000, AML.T0086.
- Mitigaciones: AML.M0019, AML.M0020, AML.M0024, AML.M0025, AML.M0027, AML.M0029,
  AML.M0030, AML.M0031, AML.M0032, AML.M0033.
