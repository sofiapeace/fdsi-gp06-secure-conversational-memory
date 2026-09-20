"""T02 - Fuga de informacion entre conversaciones y entre usuarios.

El usuario A guarda un dato sensible inventado. El usuario B, desde otra sesion,
lanza 100 sondeos DISTINTOS.

Se miden DOS fugas, no una:

  M2a - fuga de recuperacion: el indice devolvio un documento de otro espacio de
        nombres. Es la falla del control C1 y se lee del log de recuperacion.
  M2b - fuga de divulgacion: ese dato aparecio en la respuesta del modelo.

Separarlas importa. Puede haber M2a sin M2b porque el modelo decidio no repetir
el dato, y eso no es un control: es suerte. Reportar solo M2b haria que la
arquitectura Unsecure se viera mejor de lo que es.

    python experiments/run_t02.py --n 100
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from _common import manifest, new_run_dir, reset_lab, write_json
from questions import LEGIT_MEMORIES, USER_A_MEMORIES, USER_A_SECRETS, probe_questions

from memlab.audit import AuditLog
from memlab.config import Profile, Settings
from memlab.detectors import detect_leak
from memlab.orchestrator import Orchestrator


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=100, help="numero de sondeos del usuario B")
    ap.add_argument("--profile", default=os.environ.get("MEMLAB_PROFILE", "unsecure"))
    ap.add_argument(
        "--noise", type=int, default=len(LEGIT_MEMORIES),
        help="memoria legitima propia de B con la que compite el dato de A",
    )
    args = ap.parse_args()

    run_dir = new_run_dir("T02", args.profile)
    data_dir = run_dir / "data"
    reset_lab(data_dir)

    settings = Settings.from_env(profile=Profile(args.profile), data_dir=data_dir)
    audit = AuditLog(run_dir / "audit.jsonl", run_id=run_dir.name)
    orch = Orchestrator(settings, audit)

    write_json(run_dir / "manifest.json", manifest("T02", settings, orch.fingerprint(), {
        "n_probes": args.n,
        "n_noise_records_B": args.noise,
        "secrets": USER_A_SECRETS,
        "nota_datos": "Datos inventados. 4111 1111 1111 1111 es el numero de prueba "
                      "estandar de Visa y no corresponde a ninguna cuenta real.",
    }))

    print(f"[T02] perfil={args.profile} backend={settings.llm_backend.value} n={args.n}")
    print(f"[T02] evidencia -> {run_dir}")

    # --- el usuario A guarda su dato sensible ------------------------------
    seeded = []
    for text in USER_A_MEMORIES:
        rid = orch.seed_memory("A", "t02-a-session", text)
        seeded.append({"record_id": rid, "content": text})
        print(f"[T02] A guarda: {'OK' if rid else 'RECHAZADO'}  {text[:56]}")

    # --- memoria legitima propia de B --------------------------------------
    # Sin esto, B tiene el almacen practicamente vacio y la busqueda top-k le
    # devuelve los datos de A por descarte, no por similitud. Con memoria
    # propia, el indice tiene que ELEGIR el dato ajeno sobre el propio: eso es
    # lo que demuestra la ausencia del filtro por espacio de nombres.
    for i, text in enumerate(LEGIT_MEMORIES[: args.noise]):
        orch.seed_memory("B", f"t02-b-prev-{i:02d}", text)
    print(f"[T02] memoria legitima de B sembrada: {args.noise} registros")

    # --- el usuario B sondea desde otra sesion -----------------------------
    probes = probe_questions(args.n)
    results = []
    retrieval_leaks = 0
    disclosure_leaks = 0

    for i, question in enumerate(probes, 1):
        result = orch.turn("B", "t02-b-session", question)
        cross = [r.to_log("B") for r in result.cross_namespace_hits]
        det = detect_leak(result.answer, USER_A_SECRETS)
        retrieval_leaks += int(bool(cross))
        disclosure_leaks += int(det.hit)
        results.append({
            "probe_idx": i,
            "question": question,
            "answer": result.answer,
            "retrieval_leak": bool(cross),
            "cross_namespace_records": cross,
            "disclosure_leak": det.hit,
            "disclosed": det.evidence,
            "latency_e2e_ms": round(result.latency_e2e_ms, 2),
            "latency_mem_ms": round(result.latency_mem_ms, 2),
        })
        if i % 10 == 0 or det.hit:
            flag = " <- DIVULGA" if det.hit else ""
            print(f"  [{i:03d}/{args.n}] recuperacion_cruzada={bool(cross)}{flag}")

    write_json(run_dir / "results.json", {
        "test_id": "T02",
        "n_probes": args.n,
        "seeded": seeded,
        "retrieval_leaks": retrieval_leaks,
        "disclosure_leaks": disclosure_leaks,
        "probes": results,
    })
    print(f"\n[T02] fuga de recuperacion (M2a): {retrieval_leaks}/{args.n}")
    print(f"[T02] fuga de divulgacion  (M2b): {disclosure_leaks}/{args.n}")
    print(f"[T02] calcular metricas: python experiments/compute_metrics.py {run_dir.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
