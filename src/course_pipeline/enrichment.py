"""Human-reviewable source-grounded enrichment records.

Suggestions never replace original text. Optional visual notes are added manually
or by a separately configured vision model, with explicit provenance and review.
"""
from __future__ import annotations
import json
from pathlib import Path


REQUIRED = {'source_id', 'page_no', 'kind', 'content', 'evidence', 'reviewed'}
KINDS = {'figure', 'equation', 'concept', 'relationship', 'rtl_correction'}


def validate_note(note: dict) -> None:
    if not REQUIRED.issubset(note):
        raise ValueError('Enrichment note missing mandatory provenance/review fields')
    if note['kind'] not in KINDS or not isinstance(note['page_no'], int) or note['page_no'] < 1:
        raise ValueError('Invalid kind or page number')
    if not isinstance(note['reviewed'], bool) or not isinstance(note['content'], str):
        raise ValueError('Invalid review status or content')
    if not str(note['evidence']).strip() or not str(note['source_id']).strip():
        raise ValueError('Evidence and source ID are required')


def save_notes(path: Path, notes: list[dict]) -> None:
    for note in notes:
        validate_note(note)
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(notes, ensure_ascii=False, indent=2), encoding='utf-8')


def load_notes(path: Path) -> list[dict]:
    notes = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(notes, list):
        raise ValueError('Expected an array of notes')
    for note in notes:
        validate_note(note)
    return notes
