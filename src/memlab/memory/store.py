"""Las tres capas de almacenamiento.

  1. SQLite      - la fila con el hecho y sus metadatos.
  2. ChromaDB    - el embedding en el indice vectorial.
  3. Cache       - el contexto ya recuperado de la sesion en curso.

Las tres existen en los dos perfiles. La prueba T05 se apoya en que sean tres y
no una: el borrado "logico" tipico solo toca la primera, y el dato sigue siendo
recuperable desde la segunda.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Iterable

from ..schema import MemoryRecord, Provenance

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    record_id   TEXT PRIMARY KEY,
    tenant_id   TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    session_id  TEXT NOT NULL,
    kind        TEXT NOT NULL,
    content     TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    ttl_s       INTEGER,
    pinned      INTEGER NOT NULL DEFAULT 0,
    provenance  TEXT NOT NULL,
    deleted_at  TEXT
);
CREATE INDEX IF NOT EXISTS idx_ns ON memories(tenant_id, user_id);
"""


class MemoryStore:
    def __init__(self, data_dir: Path, collection_name: str = "memories") -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.data_dir / "memory.sqlite3"
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

        import chromadb

        self._chroma = chromadb.PersistentClient(path=str(self.data_dir / "chroma"))
        # Embeddings: all-MiniLM-L6-v2, la compilacion ONNX que trae Chroma por
        # defecto. Es el mismo modelo que declara la propuesta, sin arrastrar torch.
        self._collection = self._chroma.get_or_create_collection(
            name=collection_name, metadata={"hnsw:space": "cosine"}
        )

        #: Capa 3. Contexto ya recuperado, por session_id. Se vacia al reiniciar
        #: el proceso: esa es la definicion de "sesion nueva" de la propuesta.
        self.session_cache: dict[str, list[str]] = {}

    # ---------------------------------------------------------------- escritura

    def add(self, record: MemoryRecord) -> MemoryRecord:
        self._conn.execute(
            "INSERT OR REPLACE INTO memories "
            "(record_id, tenant_id, user_id, session_id, kind, content, created_at, ttl_s, pinned, provenance, deleted_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,NULL)",
            (
                record.record_id,
                record.tenant_id,
                record.user_id,
                record.session_id,
                record.kind.value,
                record.content,
                record.created_at.isoformat(),
                record.ttl_s,
                int(record.pinned),
                record.provenance.model_dump_json(),
            ),
        )
        self._conn.commit()
        self._collection.upsert(
            ids=[record.record_id],
            documents=[record.content],
            metadatas=[record.to_metadata()],  # type: ignore[list-item]
        )
        return record

    # ---------------------------------------------------------------- lectura

    def query(
        self, text: str, k: int, where: dict[str, Any] | None = None
    ) -> list[tuple[MemoryRecord, float]]:
        """Busqueda por similitud en el indice vectorial.

        `where` es el filtro por espacio de nombres. En el perfil Unsecure llega
        en None y por eso la busqueda cruza usuarios (T02).
        """
        kwargs: dict[str, Any] = {"query_texts": [text], "n_results": k}
        if where:
            kwargs["where"] = where
        res = self._collection.query(**kwargs)

        ids = (res.get("ids") or [[]])[0]
        dists = (res.get("distances") or [[]])[0] or [0.0] * len(ids)
        out: list[tuple[MemoryRecord, float]] = []
        for rid, dist in zip(ids, dists):
            rec = self.get(rid)
            if rec is not None:
                out.append((rec, float(dist)))
        return out

    def get(self, record_id: str) -> MemoryRecord | None:
        row = self._conn.execute(
            "SELECT * FROM memories WHERE record_id = ? AND deleted_at IS NULL", (record_id,)
        ).fetchone()
        return self._row_to_record(row) if row else None

    def pinned_records(self, where: dict[str, str] | None = None) -> list[MemoryRecord]:
        """Registros que entran en todas las sesiones.

        `where` filtra por espacio de nombres (C1). En Unsecure llega en None y
        el bloque de perfil se arma con lo de cualquiera.
        """
        sql = "SELECT * FROM memories WHERE pinned = 1 AND deleted_at IS NULL"
        params: list[str] = []
        if where:
            for col, val in where.items():
                sql += f" AND {col} = ?"
                params.append(val)
        sql += " ORDER BY created_at ASC"
        return [self._row_to_record(r) for r in self._conn.execute(sql, params)]

    def all_records(self, include_deleted: bool = False) -> list[MemoryRecord]:
        sql = "SELECT * FROM memories"
        if not include_deleted:
            sql += " WHERE deleted_at IS NULL"
        return [self._row_to_record(r) for r in self._conn.execute(sql)]

    # ---------------------------------------------------------------- borrado

    def soft_delete_row(self, record_id: str) -> bool:
        """Borrado logico: marca la fila y no toca nada mas.

        Es lo que hace el perfil Unsecure en T05, y por eso el embedding
        sobrevive y el dato se vuelve a recuperar.
        """
        cur = self._conn.execute(
            "UPDATE memories SET deleted_at = datetime('now') "
            "WHERE record_id = ? AND deleted_at IS NULL",
            (record_id,),
        )
        self._conn.commit()
        return cur.rowcount > 0

    def hard_delete_row(self, record_id: str) -> bool:
        cur = self._conn.execute("DELETE FROM memories WHERE record_id = ?", (record_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def delete_embedding(self, record_id: str) -> bool:
        self._collection.delete(ids=[record_id])
        return not self.embedding_exists(record_id)

    def embedding_exists(self, record_id: str) -> bool:
        got = self._collection.get(ids=[record_id])
        return bool(got.get("ids"))

    def row_exists(self, record_id: str, include_deleted: bool = False) -> bool:
        sql = "SELECT 1 FROM memories WHERE record_id = ?"
        if not include_deleted:
            sql += " AND deleted_at IS NULL"
        return self._conn.execute(sql, (record_id,)).fetchone() is not None

    def clear_session_cache(self, session_id: str | None = None) -> None:
        if session_id is None:
            self.session_cache.clear()
        else:
            self.session_cache.pop(session_id, None)

    def cache_contains(self, needle: str) -> bool:
        return any(needle in item for items in self.session_cache.values() for item in items)

    # ---------------------------------------------------------------- interno

    def _row_to_record(self, row: sqlite3.Row) -> MemoryRecord:
        return MemoryRecord(
            record_id=row["record_id"],
            tenant_id=row["tenant_id"],
            user_id=row["user_id"],
            session_id=row["session_id"],
            kind=row["kind"],
            content=row["content"],
            created_at=row["created_at"],
            ttl_s=row["ttl_s"],
            pinned=bool(row["pinned"]),
            provenance=Provenance(**json.loads(row["provenance"])),
        )

    def close(self) -> None:
        self._conn.close()

    def record_ids(self) -> Iterable[str]:
        return (r["record_id"] for r in self._conn.execute("SELECT record_id FROM memories"))
