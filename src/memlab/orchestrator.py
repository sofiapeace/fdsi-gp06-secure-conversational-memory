"""Un turno de conversacion, de punta a punta.

Mide dos latencias por separado a proposito:

  L_e2e  - el turno completo, generacion incluida. Es contexto, no prueba nada.
  L_mem  - solo la ruta de memoria: recuperacion, ensamblado del prompt y filtro
           de escritura, SIN la generacion de tokens.

La hipotesis H4 habla de 300 ms adicionales en el percentil 95. Medida extremo a
extremo sobre un modelo local, la varianza de generacion es de cientos de
milisegundos o mas y entierra por completo el efecto de los controles: H4 se
volveria imposible de rechazar o confirmar. L_mem es lo unico que los controles
afectan de verdad, y por eso es la que prueba H4.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from .audit import AuditLog
from .clock import Clock, SystemClock
from .config import Settings
from .llm import build_llm
from .memory.retriever import MemoryRetriever, Retrieved
from .memory.store import MemoryStore
from .memory.writer import build_writer
from .prompt import build_messages
from .schema import Source


@dataclass
class TurnResult:
    user_id: str
    session_id: str
    user_text: str
    answer: str
    retrieved: list[Retrieved]
    messages: list[dict[str, str]]
    stored_record_id: str | None
    latency_e2e_ms: float
    latency_mem_ms: float
    backend: str
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def cross_namespace_hits(self) -> list[Retrieved]:
        return [r for r in self.retrieved if r.record.user_id != self.user_id]


class Orchestrator:
    def __init__(
        self,
        settings: Settings,
        audit: AuditLog,
        *,
        store: MemoryStore | None = None,
        clock: Clock | None = None,
    ) -> None:
        self.settings = settings
        self.audit = audit
        self.clock = clock or SystemClock()
        self.store = store or MemoryStore(settings.data_dir)
        self.retriever = MemoryRetriever(
            self.store, is_secure=settings.is_secure, k=settings.retrieval_k
        )
        self.writer = build_writer(settings.is_secure)
        self.llm = build_llm(settings)

    def turn(self, user_id: str, session_id: str, text: str) -> TurnResult:
        t_start = time.perf_counter()
        mem_ms = 0.0

        # --- recuperacion -------------------------------------------------
        t0 = time.perf_counter()
        retrieved = self.retriever.retrieve(
            text, tenant_id=self.settings.tenant_id, user_id=user_id
        )
        messages = build_messages(text, retrieved, is_secure=self.settings.is_secure)
        mem_ms += (time.perf_counter() - t0) * 1000

        self.audit.emit(
            "retrieval",
            profile=self.settings.profile.value,
            user_id=user_id,
            session_id=session_id,
            query=text,
            retrieved=[r.to_log(user_id) for r in retrieved],
            n_cross_namespace=sum(1 for r in retrieved if r.record.user_id != user_id),
        )
        self.audit.emit(
            "prompt", user_id=user_id, session_id=session_id, messages=messages
        )

        # --- generacion (fuera de L_mem) ----------------------------------
        resp = self.llm.chat(messages)
        self.audit.emit(
            "response",
            user_id=user_id,
            session_id=session_id,
            answer=resp.text,
            backend=resp.backend,
            latency_ms=resp.latency_ms,
        )

        # --- escritura ----------------------------------------------------
        t0 = time.perf_counter()
        verdict = self.writer.consider(
            text,
            tenant_id=self.settings.tenant_id,
            user_id=user_id,
            session_id=session_id,
            created_at=self.clock.now(),
            source=Source.USER_TURN,
        )
        if verdict.stored and verdict.record is not None:
            self.store.add(verdict.record)
        mem_ms += (time.perf_counter() - t0) * 1000

        self.audit.emit(
            "write_verdict",
            user_id=user_id,
            session_id=session_id,
            stored=verdict.stored,
            reason=verdict.reason,
            flags=verdict.flags,
            record_id=verdict.record.record_id if verdict.record else None,
            pinned=verdict.record.pinned if verdict.record else None,
            content=verdict.record.content if verdict.record else None,
        )

        # Capa 3: la cache de contexto de la sesion en curso.
        self.store.session_cache.setdefault(session_id, []).extend(
            r.record.content for r in retrieved
        )

        e2e_ms = (time.perf_counter() - t_start) * 1000
        self.audit.emit(
            "turn_done",
            user_id=user_id,
            session_id=session_id,
            latency_e2e_ms=e2e_ms,
            latency_mem_ms=mem_ms,
        )

        return TurnResult(
            user_id=user_id,
            session_id=session_id,
            user_text=text,
            answer=resp.text,
            retrieved=retrieved,
            messages=messages,
            stored_record_id=verdict.record.record_id if verdict.record else None,
            latency_e2e_ms=e2e_ms,
            latency_mem_ms=mem_ms,
            backend=resp.backend,
        )

    def seed_memory(
        self, user_id: str, session_id: str, text: str, *, source: Source = Source.USER_TURN
    ) -> str | None:
        """Escribe en memoria sin gastar un turno del modelo.

        T02 la usa para sembrar el dato de A: lo que se mide ahi es la
        recuperacion desde B, no lo que el modelo le conteste a A.
        """
        verdict = self.writer.consider(
            text,
            tenant_id=self.settings.tenant_id,
            user_id=user_id,
            session_id=session_id,
            created_at=self.clock.now(),
            source=source,
        )
        if verdict.stored and verdict.record is not None:
            self.store.add(verdict.record)
            self.audit.emit(
                "seed",
                user_id=user_id,
                session_id=session_id,
                record_id=verdict.record.record_id,
                pinned=verdict.record.pinned,
                content=verdict.record.content,
            )
            return verdict.record.record_id
        self.audit.emit("seed_rejected", user_id=user_id, text=text, reason=verdict.reason)
        return None

    def fingerprint(self) -> dict[str, Any]:
        return self.llm.fingerprint()
