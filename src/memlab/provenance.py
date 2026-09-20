"""Procedencia firmada (control C4).

HMAC-SHA256 sobre el JSON canonico del registro. El perfil Unsecure no firma
nada, que es lo que permite que el texto oculto de un documento entre al almacen
como si fuera un hecho dicho por el usuario (T03).

Nota de diseno para C5: la prueba de borrado NO debe llevar un SHA-256 plano del
contenido. Un hash plano sobre un dato corto y de baja entropia -una direccion,
un numero de tarjeta- se invierte por fuerza bruta en segundos, y el log de
auditoria de solo-agregado terminaria siendo una copia recuperable justo de lo
que se prometio borrar. Por eso `deletion_proof` usa HMAC con la clave del
sistema y no un hash publico.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any


def canonical(record: dict[str, Any]) -> bytes:
    return json.dumps(record, sort_keys=True, separators=(",", ":"), default=str).encode()


def sign(record: dict[str, Any], key: bytes) -> str:
    return hmac.new(key, canonical(record), hashlib.sha256).hexdigest()


def verify(record: dict[str, Any], signature: str, key: bytes) -> bool:
    return hmac.compare_digest(sign(record, key), signature)


def deletion_proof(record_id: str, content: str, key: bytes, layers: list[str], ts: str) -> dict:
    """Prueba de borrado para el log de auditoria (C5, Hito 3)."""
    return {
        "record_id": record_id,
        "content_hmac": hmac.new(key, content.encode(), hashlib.sha256).hexdigest(),
        "layers": layers,
        "deleted_at": ts,
    }
