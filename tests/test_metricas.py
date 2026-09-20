"""Las metricas se calculan solo desde la evidencia registrada."""

from __future__ import annotations

from memlab.stats import percentile, rule_of_three, wilson


def test_cero_aciertos_reproduce_la_regla_de_tres_de_la_propuesta():
    """Con 0/100, la cota superior del IC 95 % debe rondar el 3 %."""
    p = wilson(0, 100)
    assert p.pct == 0.0
    assert abs(p.ci95_high - rule_of_three(100)) < 1.0


def test_la_granularidad_de_20_sesiones_queda_expuesta():
    """1 de 20 = 5 %, justo en el umbral de H1. El intervalo lo deja ver."""
    p = wilson(1, 20)
    assert p.pct == 5.0
    assert p.ci95_high > 20, "con n=20 el intervalo es demasiado ancho para afirmar '<= 5 %'"


def test_percentil_95():
    assert percentile([float(i) for i in range(1, 101)], 95) == 95.05
    assert percentile([], 95) == 0.0
