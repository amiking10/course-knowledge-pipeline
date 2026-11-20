"""Docling production parser plus clearly labelled diagnostic PyMuPDF backend."""
from __future__ import annotations
import re
from pathlib import Path
from .core import Page


def parse_docling(path: Path) -> list[Page]:
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError('Docling unavailable: install course-knowledge-pipeline[parse]') from exc
    result = DocumentConverter().convert(str(path))
    doc = result.document
    # A per-page export preserves page boundaries and enables reliable citation.
    # This uses Docling's item provenance rather than splitting whole-document Markdown.
    grouped: dict[int,list[str]] = {}
    seen = set()
    for element, level in doc.iterate_items():
        text = getattr(element, 'text', None)
        prov = getattr(element, 'prov', None) or []
        if text and prov:
            for p in prov:
                no = int(p.page_no)
                key = (no, id(element))
                if key not in seen:
                    grouped.setdefault(no,[]).append(str(text))
                    seen.add(key)
    # Preserve page count, including visual-only pages that require review.
    expected = len(doc.pages) if hasattr(doc, 'pages') else max(grouped,default=0)
    if expected == 0: raise ValueError('Docling returned no numbered pages')
    return [Page(i,'\n'.join(grouped.get(i,[])),[],[], 'docling') for i in range(1,expected+1)]


def parse_pymupdf_diagnostic(path: Path) -> list[Page]:
    if path.suffix.lower()!='.pdf': raise ValueError('PyMuPDF diagnostic backend supports PDFs only')
    import fitz
    pages=[]
    with fitz.open(path) as doc:
        for i,p in enumerate(doc,1):
            # No OCR or image understanding; mark visually complex pages in QA.
            pages.append(Page(i,p.get_text(sort=True),[],[], 'pymupdf-diagnostic'))
    return pages


def parse(path: Path, backend: str) -> list[Page]:
    if backend=='docling': return parse_docling(path)
    if backend=='pymupdf-diagnostic': return parse_pymupdf_diagnostic(path)
    raise ValueError(f'Unknown backend: {backend}')
