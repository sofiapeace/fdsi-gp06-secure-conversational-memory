"""Configuracion del laboratorio.

Un solo objeto Settings decide si corre el perfil Unsecure o el Secure. Ningun
otro modulo lee variables de entorno.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Profile(str, Enum):
    UNSECURE = "unsecure"
    SECURE = "secure"


class LLMBackend(str, Enum):
    OLLAMA = "ollama"
    #: Respondedor deterministico sin modelo. Sirve para depurar la tuberia
    #: mientras se descarga el modelo. Las corridas hechas con este backend
    #: quedan marcadas en la evidencia y compute_metrics las rechaza.
    STUB = "stub"


def _env(name: str, default: str) -> str:
    return os.environ.get(name, default)


@dataclass(frozen=True)
class Settings:
    profile: Profile = Profile.UNSECURE
    llm_backend: LLMBackend = LLMBackend.OLLAMA
    ollama_host: str = "http://localhost:11434"
    model: str = "llama3.1:8b-instruct-q4_K_M"
    seed: int = 20260919
    temperature: float = 0.0
    num_predict: int = 256
    tenant_id: str = "eci"
    retrieval_k: int = 4
    data_dir: Path = Path("./data")
    evidence_dir: Path = Path("./evidence")

    @classmethod
    def from_env(cls, **overrides: object) -> "Settings":
        base = cls(
            profile=Profile(_env("MEMLAB_PROFILE", "unsecure")),
            llm_backend=LLMBackend(_env("MEMLAB_LLM", "ollama")),
            ollama_host=_env("MEMLAB_OLLAMA_HOST", "http://localhost:11434"),
            model=_env("MEMLAB_MODEL", "llama3.1:8b-instruct-q4_K_M"),
            seed=int(_env("MEMLAB_SEED", "20260919")),
            temperature=float(_env("MEMLAB_TEMPERATURE", "0")),
            num_predict=int(_env("MEMLAB_NUM_PREDICT", "256")),
            tenant_id=_env("MEMLAB_TENANT", "eci"),
            retrieval_k=int(_env("MEMLAB_RETRIEVAL_K", "4")),
            data_dir=Path(_env("MEMLAB_DATA_DIR", "./data")),
            evidence_dir=Path(_env("MEMLAB_EVIDENCE_DIR", "./evidence")),
        )
        return base.replace(**overrides) if overrides else base

    def replace(self, **overrides: object) -> "Settings":
        from dataclasses import replace as _replace

        return _replace(self, **overrides)  # type: ignore[arg-type]

    @property
    def is_secure(self) -> bool:
        return self.profile is Profile.SECURE
