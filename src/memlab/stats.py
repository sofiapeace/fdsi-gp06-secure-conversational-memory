"""Estadistica de las metricas.

Reportar solo el valor puntual con 20 o 100 ensayos es enganoso: la granularidad
de M1 es de 5 puntos porcentuales por sesion. Cada metrica sale con intervalo de
confianza.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass


@dataclass
class Proportion:
    hits: int
    n: int
    pct: float
    ci95_low: float
    ci95_high: float
    method: str

    def as_dict(self) -> dict:
        return asdict(self)


def wilson(hits: int, n: int, z: float = 1.959963985) -> Proportion:
    """Intervalo de Wilson.

    Con 0 aciertos se reduce a la regla de tres que ya usa la propuesta:
    la cota superior queda en aprox. 3/n (para n = 100, 3 %).
    """
    if n == 0:
        return Proportion(0, 0, 0.0, 0.0, 0.0, "wilson")
    p = hits / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return Proportion(
        hits=hits,
        n=n,
        pct=round(p * 100, 2),
        ci95_low=round(max(0.0, centre - margin) * 100, 2),
        ci95_high=round(min(1.0, centre + margin) * 100, 2),
        method="wilson",
    )


def rule_of_three(n: int) -> float:
    """Cota superior del IC 95 % cuando se observan 0 aciertos en n ensayos."""
    return 0.0 if n == 0 else round(300.0 / n, 2)


def percentile(values: list[float], q: float) -> float:
    """Percentil por interpolacion lineal. p95 -> q = 95."""
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (q / 100) * (len(ordered) - 1)
    low = math.floor(pos)
    high = math.ceil(pos)
    if low == high:
        return ordered[int(pos)]
    return ordered[low] + (ordered[high] - ordered[low]) * (pos - low)
