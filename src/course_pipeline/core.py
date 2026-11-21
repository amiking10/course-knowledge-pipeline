"""Source registry and incremental parse records, stored locally in SQLite."""
from __future__ import annotations
import hashlib
import json
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path

SUPPORTED = frozenset({'.pdf', '.pptx', '.docx'})
SCHEMA = '''
CREATE TABLE IF NOT EXISTS sources (
 source_id TEXT PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE,
 sha256 TEXT NOT NULL, byte_size INTEGER NOT NULL, ext TEXT NOT NULL,
 state TEXT NOT NULL CHECK (state IN ('active','missing')),
 last_backend TEXT, last_parsed_hash TEXT, last_parser_version TEXT
);
CREATE TABLE IF NOT EXISTS pages (
 source_id TEXT NOT NULL, page_no INTEGER NOT NULL,
 body TEXT NOT NULL, figure_notes TEXT NOT NULL DEFAULT '[]',
 flags TEXT NOT NULL DEFAULT '[]', backend TEXT NOT NULL,
 PRIMARY KEY(source_id,page_no),
 FOREIGN KEY(source_id) REFERENCES sources(source_id)
);
CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
 source_id UNINDEXED, page_no UNINDEXED, body, tokenize='unicode61'
);
'''
PARSER_VERSION = '2026-11-20-v9'


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


@dataclass
class Page:
    page_no: int
    body: str
    figure_notes: list[str]
    flags: list[str]
    backend: str


class Store:
    def __init__(self, db: Path):
        db = Path(db)
        db.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.execute('CREATE TABLE IF NOT EXISTS course_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)')

    def __enter__(self): return self
    def __exit__(self, *_): self.conn.close()

    def scan(self, root: Path) -> dict:
        root = Path(root).resolve()
        if not root.is_dir(): raise NotADirectoryError(root)
        bound = self.conn.execute("SELECT value FROM course_metadata WHERE key='source_root'").fetchone()
        if bound and bound['value'] != str(root):
            raise ValueError(f'Course database belongs to {bound["value"]}, not {root}. Use a separate course database.')
        if not bound:
            # Existing databases without a course binding require a source match.
            # Otherwise a copied or legacy OS database could silently contaminate RX_TX.
            old_sources = self.conn.execute("SELECT relative_path, sha256 FROM sources").fetchall()
            for old in old_sources:
                existing = (root / old['relative_path']).resolve()
                if not existing.is_relative_to(root) or not existing.is_file() or hash_file(existing) != old['sha256']:
                    raise ValueError('Database contains sources from another course; use a fresh course database.')
            with self.conn:
                self.conn.execute("INSERT INTO course_metadata(key,value) VALUES('source_root',?)", (str(root),))
        seen = set()
        result = dict(added=0, changed=0, unchanged=0, missing=0, unsupported=0)
        for path in sorted(root.rglob('*')):
            if not path.is_file() or path.is_symlink(): continue
            rel = path.relative_to(root)
            if any(part.startswith('.') or part in {'__pycache__','data','outputs'} for part in rel.parts): continue
            if path.suffix.lower() not in SUPPORTED:
                result['unsupported'] += 1
                continue
            name = rel.as_posix()
            seen.add(name)
            sha = hash_file(path)
            old = self.conn.execute('SELECT * FROM sources WHERE relative_path=?', (name,)).fetchone()
            if not old: status, sid = 'added', str(uuid.uuid4())
            elif old['sha256'] != sha or old['state'] != 'active': status, sid = 'changed',old['source_id']
            else: status, sid = 'unchanged',old['source_id']
            result[status] += 1
            with self.conn:
                self.conn.execute('''INSERT INTO sources(source_id,relative_path,sha256,byte_size,ext,state)
                VALUES(?,?,?,?,?,'active') ON CONFLICT(relative_path) DO UPDATE SET
                sha256=excluded.sha256, byte_size=excluded.byte_size, ext=excluded.ext, state='active' ''',
                (sid,name,sha,path.stat().st_size,path.suffix.lower()))
        with self.conn:
            for old in self.conn.execute("SELECT * FROM sources WHERE state='active'").fetchall():
                if old['relative_path'] not in seen:
                    self.conn.execute("UPDATE sources SET state='missing' WHERE source_id=?", (old['source_id'],))
                    result['missing'] += 1
        return result

    def pending(self, backend: str) -> list[sqlite3.Row]:
        return self.conn.execute('''SELECT * FROM sources WHERE state='active' AND
          (last_parsed_hash IS NULL OR last_parsed_hash != sha256 OR last_backend != ?
           OR last_parser_version != ?) ORDER BY relative_path''', (backend,PARSER_VERSION)).fetchall()

    def save_pages(self, sid: str, pages: list[Page], backend: str, sha: str):
        """Atomically replace parsed source, retaining old output on conversion failure."""
        if not pages: raise ValueError('Parser returned zero pages')
        numbers = [p.page_no for p in pages]
        if numbers != list(range(1, len(pages) + 1)):
            raise ValueError('Parsed pages must be consecutively numbered from one')
        with self.conn:
            self.conn.execute('DELETE FROM pages WHERE source_id=?',(sid,))
            self.conn.execute('DELETE FROM pages_fts WHERE source_id=?',(sid,))
            for p in pages:
                self.conn.execute('INSERT INTO pages VALUES(?,?,?,?,?,?)',
                                  (sid,p.page_no,p.body,json.dumps(p.figure_notes,ensure_ascii=False),
                                   json.dumps(p.flags,ensure_ascii=False),p.backend))
                self.conn.execute('INSERT INTO pages_fts(source_id,page_no,body) VALUES(?,?,?)',
                                  (sid,p.page_no,p.body))
            self.conn.execute('''UPDATE sources SET last_backend=?,last_parsed_hash=?,last_parser_version=?
                                  WHERE source_id=?''',(backend,sha,PARSER_VERSION,sid))

    def sources(self):
        return self.conn.execute('SELECT * FROM sources ORDER BY relative_path').fetchall()

    def pages(self, sid: str):
        return self.conn.execute('SELECT * FROM pages WHERE source_id=? ORDER BY page_no',(sid,)).fetchall()

    def search(self, query: str, limit: int=10):
        # FTS5 MATCH syntax may contain operators. Quote each token to treat input as text.
        tokens = [t.replace('"','') for t in query.split() if t.replace('"','')]
        if not tokens: return []
        expr = ' OR '.join('"' + t + '"' for t in tokens)
        return self.conn.execute('''SELECT p.source_id,p.page_no,p.body,s.relative_path,
           bm25(pages_fts) AS rank FROM pages_fts
           JOIN pages p ON p.source_id=pages_fts.source_id AND p.page_no=pages_fts.page_no
           JOIN sources s ON s.source_id=p.source_id
           WHERE pages_fts MATCH ? AND s.state='active'
           AND s.last_parsed_hash=s.sha256
           ORDER BY rank LIMIT ?''',(expr,limit)).fetchall()
