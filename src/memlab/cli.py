"""Linea de comandos del laboratorio.

    memlab info                      identidad del modelo y perfil activo
    memlab reset                     borra el estado del laboratorio
    memlab seed   --user A --text …  escribe en memoria sin gastar un turno
    memlab ask    --user B --text …  UN turno y termina  <- lo usa T01
    memlab chat   --user A           conversacion interactiva <- para el video

`ask` existe porque la propuesta define "sesion nueva" como reiniciar el proceso
del orquestador con un session_id nuevo y la cache vacia. La unica forma honesta
de cumplir esa definicion es lanzar un proceso por sesion, y eso es exactamente
lo que hace el runner de T01 llamando a este subcomando.
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

from .audit import AuditLog
from .config import Settings
from .orchestrator import Orchestrator


def _build(args: argparse.Namespace) -> Orchestrator:
    overrides: dict = {}
    if args.profile:
        from .config import Profile

        overrides["profile"] = Profile(args.profile)
    if args.data_dir:
        overrides["data_dir"] = Path(args.data_dir)
    settings = Settings.from_env(**overrides)
    audit_path = Path(args.audit) if args.audit else settings.evidence_dir / "audit.jsonl"
    audit = AuditLog(audit_path, run_id=args.run_id or str(uuid.uuid4())[:8])
    return Orchestrator(settings, audit)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--profile", choices=["unsecure", "secure"], default=None)
    p.add_argument("--data-dir", default=None)
    p.add_argument("--audit", default=None, help="ruta del log de auditoria JSONL")
    p.add_argument("--run-id", default=None)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="memlab", description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_info = sub.add_parser("info", help="perfil activo e identidad del modelo")
    _add_common(p_info)

    p_reset = sub.add_parser("reset", help="borra data/ y empieza de cero")
    _add_common(p_reset)

    p_seed = sub.add_parser("seed", help="escribe en memoria sin llamar al modelo")
    _add_common(p_seed)
    p_seed.add_argument("--user", required=True)
    p_seed.add_argument("--session", default="seed")
    p_seed.add_argument("--text", required=True)

    p_ask = sub.add_parser("ask", help="un turno y termina")
    _add_common(p_ask)
    p_ask.add_argument("--user", required=True)
    p_ask.add_argument("--session", default=None)
    p_ask.add_argument("--text", required=True)
    p_ask.add_argument("--json", action="store_true", help="salida en JSON para los runners")

    p_chat = sub.add_parser("chat", help="conversacion interactiva")
    _add_common(p_chat)
    p_chat.add_argument("--user", required=True)
    p_chat.add_argument("--session", default=None)

    args = parser.parse_args(argv)

    if args.cmd == "reset":
        import shutil

        settings = Settings.from_env()
        target = Path(args.data_dir) if args.data_dir else settings.data_dir
        if target.exists():
            shutil.rmtree(target)
            print(f"borrado: {target}")
        else:
            print(f"nada que borrar en {target}")
        return 0

    orch = _build(args)

    if args.cmd == "info":
        print(json.dumps(
            {
                "profile": orch.settings.profile.value,
                "llm_backend": orch.settings.llm_backend.value,
                "seed": orch.settings.seed,
                "temperature": orch.settings.temperature,
                "num_predict": orch.settings.num_predict,
                "retrieval_k": orch.settings.retrieval_k,
                "data_dir": str(orch.settings.data_dir),
                "model": orch.fingerprint(),
            },
            indent=2, ensure_ascii=False,
        ))
        return 0

    if args.cmd == "seed":
        rid = orch.seed_memory(args.user, args.session, args.text)
        print(json.dumps({"record_id": rid, "stored": rid is not None}, ensure_ascii=False))
        return 0

    if args.cmd == "ask":
        session = args.session or f"s-{uuid.uuid4().hex[:8]}"
        result = orch.turn(args.user, session, args.text)
        if args.json:
            print(json.dumps(
                {
                    "user_id": result.user_id,
                    "session_id": result.session_id,
                    "question": result.user_text,
                    "answer": result.answer,
                    "backend": result.backend,
                    "latency_e2e_ms": round(result.latency_e2e_ms, 2),
                    "latency_mem_ms": round(result.latency_mem_ms, 2),
                    "retrieved": [r.to_log(result.user_id) for r in result.retrieved],
                    "system_prompt": result.messages[0]["content"],
                },
                ensure_ascii=False,
            ))
        else:
            print(result.answer)
        return 0

    if args.cmd == "chat":
        session = args.session or f"s-{uuid.uuid4().hex[:8]}"
        print(f"[perfil {orch.settings.profile.value} | usuario {args.user} | sesion {session}]")
        print("Ctrl-D para salir.\n")
        while True:
            try:
                text = input("tu> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                return 0
            if not text:
                continue
            result = orch.turn(args.user, session, text)
            cross = result.cross_namespace_hits
            if cross:
                owners = ", ".join(sorted({r.record.user_id for r in cross}))
                print(f"  [!] la memoria recuperada incluye datos de: {owners}")
            print(f"bot> {result.answer}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
