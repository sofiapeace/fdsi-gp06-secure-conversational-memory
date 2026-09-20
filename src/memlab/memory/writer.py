"""Que se guarda en memoria y como (control C3).

UNSECURE: la tuberia tipica de "extraer y guardar". Detecta si el turno vale la
pena recordarlo usando pistas de RETENCION -no de seguridad- y lo guarda tal
cual, sin tipar, sin validar y sin procedencia. El sistema no se pregunta en
ningun momento si el texto es un hecho del usuario o una orden dirigida al
modelo. Esa pregunta que no se hace es toda la vulnerabilidad de T01 y T03.

SECURE: el filtro tipado, que llega en el Hito 3.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..schema import DEFAULT_TTL_S, MemoryKind, MemoryRecord, Provenance, Source

#: Pistas de que el turno merece recordarse en sesiones futuras. Son las mismas
#: que usaria cualquier asistente con memoria: no discriminan orden de hecho.
_RETENTION_CUES = re.compile(
    r"\b(recuerda|recuerde|acuerdate|no olvides|ten en cuenta|"
    r"soy|me llamo|vivo en|mi |prefiero|me gusta|no me gusta|siempre|nunca|"
    r"a partir de ahora|de ahora en adelante)\b",
    re.IGNORECASE,
)

#: Pistas de que el turno es una preferencia permanente y no un dato episodico.
#: Lo que caiga aqui se fija al perfil y entra en TODAS las sesiones futuras.
#: Es una decision de utilidad, no de seguridad, y precisamente por eso el
#: sistema Unsecure fija tambien las instrucciones del atacante.
_STANDING_CUES = re.compile(
    r"\b(recuerda|recuerde|acuerdate|no olvides|siempre|nunca|prefiero|"
    r"a partir de ahora|de ahora en adelante|todas tus respuestas)\b",
    re.IGNORECASE,
)


@dataclass
class WriteVerdict:
    """Lo que el filtro decidio, y por que. Va entero al log de auditoria."""

    stored: bool
    reason: str
    record: MemoryRecord | None = None
    flags: list[str] = field(default_factory=list)


class MemoryWriter:
    """Clase base. El perfil decide cual implementacion se usa."""

    def consider(
        self,
        text: str,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str,
        created_at,
        source: Source = Source.USER_TURN,
    ) -> WriteVerdict:
        raise NotImplementedError


class UnsecureWriter(MemoryWriter):
    def consider(
        self,
        text: str,
        *,
        tenant_id: str,
        user_id: str,
        session_id: str,
        created_at,
        source: Source = Source.USER_TURN,
    ) -> WriteVerdict:
        clean = text.strip()
        if not clean or not _RETENTION_CUES.search(clean):
            return WriteVerdict(stored=False, reason="sin_pistas_de_retencion")

        record = MemoryRecord(
            tenant_id=tenant_id,
            user_id=user_id,
            session_id=session_id,
            # Todo entra como FACT: no hay nada que clasifique. Una orden del
            # atacante queda indistinguible de "soy vegetariano".
            kind=MemoryKind.FACT,
            content=clean,
            created_at=created_at,
            ttl_s=DEFAULT_TTL_S[MemoryKind.FACT],  # None: no caduca nunca
            pinned=bool(_STANDING_CUES.search(clean)),
            # Sin firma: el origen no es verificable (falta C4).
            provenance=Provenance(
                source=source, author_user_id=user_id, session_id=session_id, signature=None
            ),
        )
        return WriteVerdict(stored=True, reason="guardado_sin_validar", record=record)


class SecureWriter(MemoryWriter):
    """Control C3: filtro de escritura con esquema tipado.

    Se implementa en el Hito 3. Clasifica el candidato en hecho / instruccion /
    secreto, rechaza los dos ultimos, asigna tiempo de vida por categoria y firma
    la procedencia (C4).
    """

    def consider(self, text: str, **kwargs) -> WriteVerdict:  # noqa: D102
        raise NotImplementedError(
            "C3 (filtro de escritura tipado) se implementa en el Hito 3. "
            "El Avance 1 entrega la linea base Unsecure."
        )


def build_writer(is_secure: bool) -> MemoryWriter:
    return SecureWriter() if is_secure else UnsecureWriter()
