"""Recursive, deterministic, content-hashed source discovery."""
import hashlib
import uuid
from pathlib import Path

from .models import ScanReport, SourceRecord, SourceStatus
from .registry import SourceRegistry

SUPPORTED_EXTENSIONS = frozenset({".pdf", ".pptx", ".docx"})
IGNORED_DIRECTORIES = frozenset({".git", ".venv", "__pycache__", ".pytest_cache"})


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scan_sources(root: Path, registry: SourceRegistry) -> ScanReport:
    """Scan one course root. Raises on unreadable sources; does not silently skip them.

    source_id is stable for a given relative path, including when its contents change.
    Moved/renamed files are represented as a missing old path and a new source.
    """
    root = Path(root).expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(f"Source directory does not exist: {root}")

    discovered = added = changed = unchanged = unsupported = 0
    seen: set[str] = set()
    paths = sorted(
        (
            p for p in root.rglob("*")
            if p.is_file()
            and not any(part.startswith(".") or part in IGNORED_DIRECTORIES for part in p.relative_to(root).parts)
            and not p.is_symlink()
        ),
        key=lambda p: p.relative_to(root).as_posix().casefold(),
    )
    for path in paths:
        ext = path.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            unsupported += 1
            continue
        relative_path = path.relative_to(root).as_posix()
        stat = path.stat()
        fingerprint = sha256_file(path)
        existing = registry.get(relative_path)
        record = SourceRecord(
            source_id=(existing.source_id if existing else str(uuid.uuid4())),
            relative_path=relative_path,
            extension=ext,
            sha256=fingerprint,
            size_bytes=stat.st_size,
            mtime_ns=stat.st_mtime_ns,
            status=SourceStatus.ACTIVE,
        )
        if existing is None:
            added += 1
        elif existing.sha256 != fingerprint or existing.status is SourceStatus.MISSING:
            changed += 1
        else:
            unchanged += 1
        registry.upsert(record)
        discovered += 1
        seen.add(relative_path)
    missing = registry.mark_missing_except(seen)
    return ScanReport(discovered, added, changed, unchanged, missing, unsupported)
