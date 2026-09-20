"""Tiempo de vida y borrado verificable (control C5).

La purga es una funcion pura que recibe el `now` que le den. APScheduler solo la
invoca en produccion. Asi T04 puede adelantar el reloj del laboratorio sin
depender de que un hilo de fondo vea el mismo reloj congelado.

Se implementa completo en el Hito 3. Lo que hay aqui es la parte que T05 ya
necesita para demostrar el borrado incompleto del perfil Unsecure.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .store import MemoryStore


@dataclass
class PurgeReport:
    checked: int = 0
    expired: int = 0
    purged_rows: list[str] = field(default_factory=list)
    purged_embeddings: list[str] = field(default_factory=list)


@dataclass
class DeletionResult:
    record_id: str
    row_gone: bool
    embedding_gone: bool
    cache_gone: bool

    @property
    def complete(self) -> bool:
        return self.row_gone and self.embedding_gone and self.cache_gone


class Lifecycle:
    def __init__(self, store: MemoryStore, *, is_secure: bool) -> None:
        self.store = store
        self.is_secure = is_secure

    def forget(self, record_id: str, *, session_id: str | None = None) -> DeletionResult:
        """Atiende el "olvida lo que sabes sobre X".

        UNSECURE: borrado logico de la fila. El embedding sigue en el indice y la
        cache de la sesion tambien, asi que el dato se vuelve a recuperar.
        SECURE:   borrado en las tres capas mas prueba de borrado (Hito 3).
        """
        if not self.is_secure:
            self.store.soft_delete_row(record_id)
            return DeletionResult(
                record_id=record_id,
                row_gone=not self.store.row_exists(record_id),
                embedding_gone=not self.store.embedding_exists(record_id),
                cache_gone=False,
            )
        raise NotImplementedError(
            "C5 (borrado verificable en tres capas y prueba de borrado) se "
            "implementa en el Hito 3."
        )

    def purge_expired(self, now: datetime) -> PurgeReport:
        report = PurgeReport()
        for rec in self.store.all_records():
            report.checked += 1
            if not rec.is_expired(now):
                continue
            report.expired += 1
            if not self.is_secure:
                # Sin purga: el dato vencido sigue disponible (T04, Unsecure).
                continue
            raise NotImplementedError("C5 se implementa en el Hito 3.")
        return report
