"""Reloj inyectable.

El tiempo de vida (C5) se evalua en la capa de aplicacion. Si esa evaluacion
dependiera del reloj del sistema, la prueba T04 tendria que congelar el reloj del
proceso con freezegun, y la purga programada de APScheduler -que corre en otro
hilo con su propio temporizador- no veria el reloj congelado. El resultado seria
una prueba intermitente.

Por eso todo el codigo que necesita saber "que hora es" recibe un Clock.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    """Reloj real. El que se usa en produccion y en el chat interactivo."""

    def now(self) -> datetime:
        return datetime.now(timezone.utc)


class FrozenClock:
    """Reloj controlado por la prueba. T04 lo adelanta 48 h sin tocar el reloj del proceso."""

    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            start = start.replace(tzinfo=timezone.utc)
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, **delta: float) -> datetime:
        self._now += timedelta(**delta)
        return self._now
