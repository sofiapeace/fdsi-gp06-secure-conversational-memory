"""Que memoria se trae a la sesion (control C1).

Hay dos canales de recuperacion, y cada prueba explota uno distinto:

  - Perfil fijado: entra en TODAS las sesiones sin pasar por la busqueda. Es el
    canal que reactiva la instruccion dormida frente a una pregunta que no se le
    parece en nada (T01).
  - Busqueda por similitud: trae lo que se parece a la pregunta. Es el canal por
    donde se cruza informacion entre usuarios cuando no hay filtro (T02).

UNSECURE: ninguno de los dos canales filtra por dueno del dato.
SECURE:   los dos filtran por tenant_id y user_id, siempre, sin excepcion.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..schema import MemoryRecord
from .store import MemoryStore


@dataclass
class Retrieved:
    record: MemoryRecord
    channel: str  # "pinned" | "similarity"
    distance: float | None = None

    def to_log(self, asking_user_id: str) -> dict[str, object]:
        """Fila del log de recuperacion.

        `cross_namespace` es la que permite calcular M2a: dice si el documento
        devuelto pertenecia a otro dueno, independientemente de lo que el modelo
        haya decidido decir despues.
        """
        return {
            "record_id": self.record.record_id,
            "owner_user_id": self.record.user_id,
            "asking_user_id": asking_user_id,
            "cross_namespace": self.record.user_id != asking_user_id,
            "channel": self.channel,
            "distance": self.distance,
            "kind": self.record.kind.value,
            "pinned": self.record.pinned,
            "content": self.record.content,
        }


class MemoryRetriever:
    def __init__(self, store: MemoryStore, *, is_secure: bool, k: int = 4) -> None:
        self.store = store
        self.is_secure = is_secure
        self.k = k

    def _namespace_filter(self, tenant_id: str, user_id: str) -> dict | None:
        if not self.is_secure:
            # Aqui esta la debilidad: la consulta vectorial sale sin filtro y el
            # indice devuelve lo que mas se parezca, sea de quien sea.
            return None
        return {"$and": [{"tenant_id": {"$eq": tenant_id}}, {"user_id": {"$eq": user_id}}]}

    def retrieve(self, query: str, *, tenant_id: str, user_id: str) -> list[Retrieved]:
        out: list[Retrieved] = []

        sql_where = {"tenant_id": tenant_id, "user_id": user_id} if self.is_secure else None
        for rec in self.store.pinned_records(where=sql_where):
            out.append(Retrieved(record=rec, channel="pinned"))

        seen = {r.record.record_id for r in out}
        where = self._namespace_filter(tenant_id, user_id)
        for rec, dist in self.store.query(query, k=self.k, where=where):
            if rec.record_id not in seen:
                out.append(Retrieved(record=rec, channel="similarity", distance=dist))
        return out


class SecureRetriever(MemoryRetriever):
    """Control C1. El filtro ya esta implementado arriba y se activa con el perfil."""
