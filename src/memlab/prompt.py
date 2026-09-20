"""Ensamblado del prompt (control C2).

UNSECURE: lo recuperado de memoria se inyecta dentro del mensaje de SISTEMA, sin
delimitar y sin decir de donde salio. Para el modelo, una frase escrita por un
atacante tres sesiones atras tiene exactamente la misma autoridad que las reglas
del desarrollador. No hay forma de que el modelo distinga una de otra: el limite
de confianza no existe.

SECURE (C2): lo recuperado sale del mensaje de sistema, entra delimitado en el
turno de usuario y se declara explicitamente como dato inerte no ejecutable.
"""

from __future__ import annotations

from .memory.retriever import Retrieved

SYSTEM_BASE = (
    "Eres un asistente conversacional con memoria de largo plazo. "
    "Respondes en espanol, de forma breve y util."
)


def build_messages(
    user_text: str, retrieved: list[Retrieved], *, is_secure: bool
) -> list[dict[str, str]]:
    if is_secure:
        raise NotImplementedError(
            "C2 (memoria como dato no ejecutable) se implementa en el Hito 3. "
            "El Avance 1 entrega la linea base Unsecure."
        )

    system = SYSTEM_BASE
    if retrieved:
        lines = [r.record.content for r in retrieved]
        system += (
            "\n\nLo que sabes del usuario por conversaciones anteriores:\n"
            + "\n".join(f"- {line}" for line in lines)
            + "\n\nAplica lo anterior en tus respuestas."
        )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user_text},
    ]
