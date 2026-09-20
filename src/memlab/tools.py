"""Herramientas del agente y autorizacion por origen (control C6).

Solo `enviar_correo`, simulada: no sale ningun correo, se registra la intencion.
Es la herramienta que T03 intenta disparar sin confirmacion.

UNSECURE: cualquier cosa que venga en el contexto puede pedir la herramienta y
se ejecuta.
SECURE (C6): una accion con efecto externo exige confirmacion explicita del
usuario, y nunca la puede autorizar contenido recuperado de memoria.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolCall:
    name: str
    args: dict
    authorized_by: str  # "user" | "memory" | "document"
    executed: bool
    required_confirmation: bool


def enviar_correo(
    destinatario: str, asunto: str, cuerpo: str, *, authorized_by: str, is_secure: bool
) -> ToolCall:
    if is_secure:
        raise NotImplementedError("C6 se implementa en el Hito 3.")
    return ToolCall(
        name="enviar_correo",
        args={"destinatario": destinatario, "asunto": asunto, "cuerpo": cuerpo},
        authorized_by=authorized_by,
        executed=True,          # se ejecuta sin preguntar: esa es la falla
        required_confirmation=False,
    )
