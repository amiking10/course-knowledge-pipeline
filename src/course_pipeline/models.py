"""Phase 1 records. Parsing/extraction is implemented in Phase 2."""
from dataclasses import dataclass
from enum import Enum


class SourceStatus(str, Enum):
    ACTIVE = "active"
    MISSING = "missing"


@dataclass(frozen=True)
class SourceRecord:
    source_id: str
    relative_path: str
    extension: str
    sha256: str
    size_bytes: int
    mtime_ns: int
    status: SourceStatus


@dataclass(frozen=True)
class ScanReport:
    discovered: int
    added: int
    changed: int
    unchanged: int
    missing: int
    unsupported: int
