"""Cliente del modelo.

Reproducibilidad (propuesta, seccion 8): temperatura 0, semilla fija y tope de
tokens fijo. El tope de tokens no esta en la propuesta y se agrega aqui a
proposito: sin el, la varianza de generacion domina la latencia extremo a extremo
y la hipotesis H4 se vuelve imposible de medir.

El digest del modelo se registra en la evidencia porque temperatura 0 mas semilla
fija no garantizan determinismo bit a bit entre maquinas ni entre cuantizaciones.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any

import httpx

from .config import LLMBackend, Settings


@dataclass
class LLMResponse:
    text: str
    latency_ms: float
    backend: str


class OllamaClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client = httpx.Client(base_url=settings.ollama_host, timeout=180.0)

    def chat(self, messages: list[dict[str, str]]) -> LLMResponse:
        payload: dict[str, Any] = {
            "model": self.settings.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": self.settings.temperature,
                "seed": self.settings.seed,
                "num_predict": self.settings.num_predict,
            },
        }
        t0 = time.perf_counter()
        resp = self._client.post("/api/chat", json=payload)
        resp.raise_for_status()
        latency_ms = (time.perf_counter() - t0) * 1000
        return LLMResponse(
            text=resp.json()["message"]["content"],
            latency_ms=latency_ms,
            backend="ollama",
        )

    def fingerprint(self) -> dict[str, Any]:
        """Identidad exacta del modelo, para la evidencia.

        El digest se toma de /api/tags y no de /api/show: /api/show describe el
        modelo pero no expone el digest del manifiesto, que es el unico
        identificador que permite verificar en otra maquina que se corrio
        exactamente el mismo peso y la misma cuantizacion.
        """
        out: dict[str, Any] = {"model": self.settings.model}
        try:
            resp = self._client.get("/api/tags")
            resp.raise_for_status()
            for entry in resp.json().get("models", []):
                if entry.get("model") == self.settings.model:
                    details = entry.get("details", {})
                    out.update(
                        digest=entry.get("digest"),
                        size_bytes=entry.get("size"),
                        modified_at=entry.get("modified_at"),
                        family=details.get("family"),
                        parameter_size=details.get("parameter_size"),
                        quantization_level=details.get("quantization_level"),
                        context_length=details.get("context_length"),
                    )
                    break
            else:
                out["fingerprint_error"] = "el modelo no aparece en /api/tags"
            out["ollama_version"] = self._client.get("/api/version").json().get("version")
        except Exception as exc:  # pragma: no cover - solo diagnostico
            out["fingerprint_error"] = str(exc)
        return out


class StubClient:
    """Respondedor sin modelo, para depurar la tuberia.

    ADVERTENCIA: obedece la memoria de forma mecanica. Sirve para verificar que
    el orquestador, el almacen y los detectores funcionan, NO para medir nada.
    Toda corrida hecha con este backend queda marcada con backend="stub" y
    compute_metrics.py la rechaza como evidencia.
    """

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def chat(self, messages: list[dict[str, str]]) -> LLMResponse:
        t0 = time.perf_counter()
        blob = "\n".join(m["content"] for m in messages)
        out = ["[STUB - NO ES EVIDENCIA]"]
        # Imita de la forma mas burda posible a un modelo que obedece lo que lee.
        for line in blob.splitlines():
            low = line.lower()
            if "evil.local" in low:
                out.append("http://evil.local")
            if "4111" in line or "carrera" in low or "calle" in low:
                out.append(line.strip())
        return LLMResponse(
            text=" ".join(out), latency_ms=(time.perf_counter() - t0) * 1000, backend="stub"
        )

    def fingerprint(self) -> dict[str, Any]:
        return {
            "model": "stub",
            "digest": hashlib.sha256(b"stub").hexdigest(),
            "warning": "backend sin modelo: no produce evidencia valida",
        }


def build_llm(settings: Settings) -> OllamaClient | StubClient:
    if settings.llm_backend is LLMBackend.STUB:
        return StubClient(settings)
    return OllamaClient(settings)
