"""SQLite manifest: stable file identity, content fingerprints and status."""
import sqlite3
from pathlib import Path

from .models import SourceRecord, SourceStatus

SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    relative_path TEXT NOT NULL UNIQUE,
    extension TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'missing')),
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_sources_sha256 ON sources(sha256);
CREATE INDEX IF NOT EXISTS idx_sources_status ON sources(status);
"""


class SourceRegistry:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.conn.close()

    def get(self, relative_path: str) -> SourceRecord | None:
        row = self.conn.execute(
            "SELECT * FROM sources WHERE relative_path = ?", (relative_path,)
        ).fetchone()
        return self._record(row) if row else None

    def list_all(self) -> list[SourceRecord]:
        rows = self.conn.execute("SELECT * FROM sources ORDER BY relative_path").fetchall()
        return [self._record(row) for row in rows]

    def upsert(self, record: SourceRecord) -> None:
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO sources
                (source_id, relative_path, extension, sha256, size_bytes, mtime_ns, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(relative_path) DO UPDATE SET
                  extension = excluded.extension,
                  sha256 = excluded.sha256,
                  size_bytes = excluded.size_bytes,
                  mtime_ns = excluded.mtime_ns,
                  status = excluded.status,
                  last_seen_at = CURRENT_TIMESTAMP
                """,
                (
                    record.source_id, record.relative_path, record.extension,
                    record.sha256, record.size_bytes, record.mtime_ns, record.status.value,
                ),
            )

    def mark_missing_except(self, seen: set[str]) -> int:
        """Mark previously tracked files absent. Only call after a successful scan."""
        count = 0
        with self.conn:
            rows = self.conn.execute(
                "SELECT relative_path FROM sources WHERE status = 'active'"
            ).fetchall()
            for row in rows:
                if row["relative_path"] not in seen:
                    self.conn.execute(
                        "UPDATE sources SET status = 'missing', last_seen_at = CURRENT_TIMESTAMP WHERE relative_path = ?",
                        (row["relative_path"],),
                    )
                    count += 1
        return count

    @staticmethod
    def _record(row: sqlite3.Row) -> SourceRecord:
        return SourceRecord(
            source_id=row["source_id"],
            relative_path=row["relative_path"],
            extension=row["extension"],
            sha256=row["sha256"],
            size_bytes=row["size_bytes"],
            mtime_ns=row["mtime_ns"],
            status=SourceStatus(row["status"]),
        )
