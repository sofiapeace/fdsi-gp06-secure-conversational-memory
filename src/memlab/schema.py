"""Esquema tipado de los registros de memoria.

El esquema existe desde el perfil Unsecure aunque ahi no se valide nada. Es
deliberado: asi el diff entre Unsecure y Secure es el control C3 (el filtro que
decide que se guarda), no un cambio de modelo de datos. Si el esquema apareciera
solo en Secure, la comparacion entre arquitecturas dejaria de ser limpia.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum

from pydantic import BaseModel, Field


class MemoryKind(str, Enum):
    """Tipo declarado del registro.

    En Unsecure todo entra como FACT: no hay nada que clasifique. En Secure el
    filtro C3 asigna el tipo y solo FACT / PREFERENCE / TASK_CONTEXT llegan al
    almacen; INSTRUCTION y SECRET se rechazan o se guardan inertes.
    """

    FACT = "fact"
    PREFERENCE = "preference"
    TASK_CONTEXT = "task_context"
    INSTRUCTION = "instruction"
    SECRET = "secret"


#: Tiempo de vida por categoria (C5). T04 usa task_context: 24 h.
DEFAULT_TTL_S: dict[MemoryKind, int | None] = {
    MemoryKind.FACT: None,
    MemoryKind.PREFERENCE: None,
    MemoryKind.TASK_CONTEXT: 24 * 3600,
    MemoryKind.INSTRUCTION: 0,
    MemoryKind.SECRET: 0,
}


class Source(str, Enum):
    USER_TURN = "user_turn"
    DOCUMENT = "document"
    TOOL = "tool"


class Provenance(BaseModel):
    """De donde salio el registro (C4).

    `signature` es el HMAC-SHA256 sobre el JSON canonico del registro. En
    Unsecure queda en None: no hay procedencia verificable, que es justamente la
    debilidad que permite que el texto de un documento entre como si fuera un
    hecho dicho por el usuario (T03).
    """

    source: Source = Source.USER_TURN
    author_user_id: str
    session_id: str
    signature: str | None = None


class MemoryRecord(BaseModel):
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str
    user_id: str
    session_id: str
    kind: MemoryKind = MemoryKind.FACT
    content: str
    created_at: datetime
    ttl_s: int | None = None
    pinned: bool = False
    """Si el registro entra en TODAS las sesiones del usuario, sin pasar por la
    busqueda por similitud. Es el bloque de "perfil / preferencias permanentes"
    que usa cualquier asistente con memoria. Tambien es lo que hace que una
    instruccion dormida se reactive frente a una pregunta que no se le parece en
    nada (T01): sin este canal, la instruccion nunca se recuperaria."""
    provenance: Provenance

    @property
    def namespace(self) -> str:
        return f"{self.tenant_id}/{self.user_id}"

    def expires_at(self) -> datetime | None:
        if self.ttl_s is None:
            return None
        return self.created_at + timedelta(seconds=self.ttl_s)

    def is_expired(self, now: datetime) -> bool:
        exp = self.expires_at()
        return exp is not None and now >= exp

    def to_metadata(self) -> dict[str, object]:
        """Metadatos que van al indice vectorial.

        En Unsecure se escriben igual que en Secure. La diferencia no esta en que
        se guarde el user_id, sino en que la consulta lo use como filtro (C1).
        Guardarlo siempre es lo que permite demostrar la fuga: el log muestra que
        el dato de otro dueno SI estaba etiquetado y aun asi se devolvio.
        """
        return {
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "kind": self.kind.value,
            "created_at": self.created_at.isoformat(),
            "ttl_s": -1 if self.ttl_s is None else self.ttl_s,
            "pinned": self.pinned,
            "source": self.provenance.source.value,
        }


def utcnow() -> datetime:
    return datetime.now(timezone.utc)
