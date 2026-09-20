from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "experiments"))

from memlab.audit import AuditLog  # noqa: E402
from memlab.config import LLMBackend, Profile, Settings  # noqa: E402
from memlab.orchestrator import Orchestrator  # noqa: E402


@pytest.fixture
def lab(tmp_path):
    """Laboratorio Unsecure aislado, con el backend stub.

    Las pruebas verifican la TUBERIA -que el dato cruce de sesion, que la consulta
    vectorial no filtre por dueno-, no el comportamiento del modelo. Por eso usan
    el stub: son deterministas y corren en segundos. Las metricas del informe
    salen de los runners con el modelo real.
    """

    def _make(profile: Profile = Profile.UNSECURE) -> Orchestrator:
        settings = Settings.from_env(
            profile=profile,
            llm_backend=LLMBackend.STUB,
            data_dir=tmp_path / "data",
        )
        audit = AuditLog(tmp_path / "audit.jsonl", run_id=uuid.uuid4().hex[:8])
        return Orchestrator(settings, audit)

    return _make
