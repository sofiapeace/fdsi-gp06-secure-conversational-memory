"""Utilidades compartidas por los runners de experimentos."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SRC = REPO / "src"
sys.path.insert(0, str(SRC))


def git_sha() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=REPO, capture_output=True, text=True, check=True,
        ).stdout.strip()
    except Exception:
        return "sin-git"


def new_run_dir(test_id: str, profile: str, evidence_dir: Path | None = None) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    base = evidence_dir or (REPO / "evidence" / "runs")
    run_dir = base / f"{stamp}-{test_id}-{profile}-{git_sha()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def manifest(test_id: str, settings, fingerprint: dict, extra: dict | None = None) -> dict:
    """Todo lo necesario para repetir la corrida en otra maquina."""
    return {
        "test_id": test_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "git_sha": git_sha(),
        "profile": settings.profile.value,
        "llm_backend": settings.llm_backend.value,
        "model": fingerprint,
        "seed": settings.seed,
        "temperature": settings.temperature,
        "num_predict": settings.num_predict,
        "retrieval_k": settings.retrieval_k,
        "tenant_id": settings.tenant_id,
        "python": sys.version.split()[0],
        **(extra or {}),
    }


def reset_lab(data_dir: Path) -> None:
    import shutil

    if data_dir.exists():
        shutil.rmtree(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
