"""Auditable page-level secondary extraction without silently overwriting Docling.

Secondary text has independent provenance and is not assumed visually faithful.
The canonical Page.body is searchable and contains clearly labeled sections.
"""
from __future__ import annotations
from pathlib import Path
import re
from .core import Page


def normalize_tokens(text: str) -> set[str]:
    return {s.casefold() for s in re.findall(r'[\w\u0590-\u05ff]+', text, re.UNICODE) if len(s)>1}


def reconcile(docling: list[Page], native: list[Page], *, min_secondary: int=140,
              omission_ratio: float=.30) -> list[Page]:
    if len(docling) != len(native):
        raise ValueError(f'Page count discrepancy: Docling={len(docling)}, native={len(native)}')
    results=[]
    for primary, secondary in zip(docling,native):
        if primary.page_no != secondary.page_no:
            raise ValueError('Page order mismatch between extractors')
        a=primary.body.strip();b=secondary.body.strip()
        flags=list(primary.flags)
        body=a
        ratio=len(a)/max(len(b),1)
        # Require a meaningful text gap, not simply different word order.
        if len(b)>=min_secondary and ratio<omission_ratio:
            flags.append('secondary_native_text_disagrees_review')
            body=(f'[DOCLING EXTRACTION — UNVERIFIED]\n{a or "[NO DOCLING TEXT]"}\n\n'
                  f'[SECONDARY PYMUPDF EXTRACTION — UNVERIFIED; CHECK ORIGINAL PAGE]\n{b}')
        if not a and b:
            if 'secondary_native_text_disagrees_review' not in flags:
                flags.append('secondary_native_text_disagrees_review')
                body=f'[DOCLING EXTRACTION — EMPTY]\n[SECONDARY PYMUPDF EXTRACTION — UNVERIFIED]\n{b}'
        if not a and not b:
            flags.append('both_extractors_empty_visual_review')
        results.append(Page(primary.page_no,body,list(primary.figure_notes),
                            sorted(set(flags)),'hybrid'))
    return results


def parse_hybrid(path: Path) -> list[Page]:
    from .parsers import parse_docling,parse_pymupdf_diagnostic
    if Path(path).suffix.lower()!='.pdf':
        pages=parse_docling(path)
        for p in pages:p.flags.append('no_secondary_extractor_for_format')
        return pages
    return reconcile(parse_docling(path),parse_pymupdf_diagnostic(path))
