"""T01 - Instruccion que queda dormida en la memoria entre sesiones.

Sesion 1: el usuario B escribe la instruccion. Se cierra.
Sesiones 2..N+1: cada una es un PROCESO NUEVO, con session_id nuevo y cache de
contexto vacia, y hace una pregunta normal distinta. Lo unico que sobrevive entre
sesiones es el almacen de memoria.

Lanzar un proceso por sesion es mas lento que un bucle en memoria, pero es la
unica forma de cumplir la definicion de "sesion nueva" que fija la propuesta. Un
bucle dentro del mismo proceso dejaria estado compartido y el resultado no
probaria persistencia real.

    python experiments/run_t01.py --n 20
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from _common import REPO, SRC, manifest, new_run_dir, reset_lab, write_json
from questions import DORMANT_INSTRUCTION, INNOCENT_QUESTIONS, LEGIT_MEMORIES

from memlab.audit import AuditLog
from memlab.config import Profile, Settings
from memlab.detectors import detect_instruction_followed
from memlab.orchestrator import Orchestrator


def run_new_session(session_idx: int, question: str, data_dir: Path, audit: Path,
                    run_id: str, profile: str) -> dict:
    """Una sesion nueva = un proceso nuevo."""
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    proc = subprocess.run(
        [
            sys.executable, "-m", "memlab.cli", "ask",
            "--user", "B",
            "--session", f"t01-new-{session_idx:03d}",
            "--text", question,
            "--data-dir", str(data_dir),
            "--audit", str(audit),
            "--run-id", run_id,
            "--profile", profile,
            "--json",
        ],
        cwd=REPO, env=env, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        return {"session_idx": session_idx, "question": question, "error": proc.stderr[-2000:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=20, help="numero de sesiones nuevas")
    ap.add_argument("--profile", default=os.environ.get("MEMLAB_PROFILE", "unsecure"))
    ap.add_argument(
        "--noise", type=int, default=len(LEGIT_MEMORIES),
        help="registros de memoria legitima con los que compite la instruccion",
    )
    args = ap.parse_args()

    if args.n > len(INNOCENT_QUESTIONS):
        ap.error(f"solo hay {len(INNOCENT_QUESTIONS)} preguntas distintas disponibles")

    settings = Settings.from_env(profile=Profile(args.profile))
    run_dir = new_run_dir("T01", args.profile)
    data_dir = run_dir / "data"
    audit_path = run_dir / "audit.jsonl"
    run_id = run_dir.name

    reset_lab(data_dir)
    settings = settings.replace(data_dir=data_dir)

    audit = AuditLog(audit_path, run_id=run_id)
    orch = Orchestrator(settings, audit)
    fp = orch.fingerprint()
    write_json(run_dir / "manifest.json", manifest("T01", settings, fp, {
        "n_sessions": args.n,
        "n_noise_records": args.noise,
        "dormant_instruction": DORMANT_INSTRUCTION,
        "session_definition": "proceso nuevo, session_id nuevo, cache de contexto vacia",
    }))

    print(f"[T01] perfil={args.profile} backend={settings.llm_backend.value} n={args.n}")
    print(f"[T01] evidencia -> {run_dir}")

    # --- ruido de fondo: memoria legitima previa ---------------------------
    for i, text in enumerate(LEGIT_MEMORIES[: args.noise]):
        orch.seed_memory("B", f"t01-prev-{i:02d}", text)
    print(f"[T01] memoria legitima sembrada: {args.noise} registros")

    # --- sesion 1: el atacante escribe -------------------------------------
    print("[T01] sesion 1: el usuario B escribe la instruccion...")
    seeded = orch.turn("B", "t01-inject", DORMANT_INSTRUCTION)
    if seeded.stored_record_id is None:
        print("[T01] AVISO: la instruccion no quedo guardada en memoria.")
    orch.store.close()
    del orch  # se cierra la sesion 1: el proceso siguiente arranca con cache vacia

    # --- sesiones nuevas ----------------------------------------------------
    results = []
    hits = 0
    for i in range(args.n):
        question = INNOCENT_QUESTIONS[i]
        out = run_new_session(i + 1, question, data_dir, audit_path, run_id, args.profile)
        if "error" in out:
            print(f"  [{i+1:02d}/{args.n}] ERROR: {out['error'][:120]}")
            results.append(out)
            continue
        det = detect_instruction_followed(out["answer"])
        hits += int(det.hit)
        results.append({
            **out,
            "instruction_followed": det.hit,
            "evidence": det.evidence,
            "needs_manual_review": det.needs_review,
            "review_note": det.note,
            "retrieved_injection": any(
                "evil.local" in (r.get("content") or "") for r in out.get("retrieved", [])
            ),
        })
        mark = "OBEDECE" if det.hit else "limpia  "
        flag = " [revisar]" if det.needs_review else ""
        print(f"  [{i+1:02d}/{args.n}] {mark}{flag}  {question[:44]}")

    write_json(run_dir / "results.json", {
        "test_id": "T01",
        "n_sessions": args.n,
        "hits": hits,
        "sessions": results,
    })
    print(f"\n[T01] instruccion cumplida en {hits}/{args.n} sesiones nuevas")
    print(f"[T01] calcular metricas: python experiments/compute_metrics.py {run_dir.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
