"""Conservative dual-extractor reconciliation; never silently discard evidence."""
from pathlib import Path
import re
from .comparison import compare
from .core import Page

def reconcile(docling: list[Page], native: list[Page], *, min_secondary: int=140,
              omission_ratio: float=.30) -> list[Page]:
    if len(docling) != len(native):
        raise ValueError(f'Page count discrepancy: Docling={len(docling)}, native={len(native)}')
    output=[]
    for primary, secondary in zip(docling,native):
        if primary.page_no != secondary.page_no:
            raise ValueError('Page order mismatch between extractors')
        a,b=primary.body.strip(),secondary.body.strip()
        result=compare(a,b,min_secondary=min_secondary,
                       missing_fraction_threshold=omission_ratio)
        flags=set(primary.flags)
        body=a
        if result.probable_omission and b:
            flags.update(['secondary_native_text_disagrees_review','probable_text_omission'])
            if (len(result.new_numeric_tokens) >= 2 and
                re.search(r'(?i)(?:\bq\s*=|\bp\d+\s*=|\bwaiting\s*time\s*=|\bturnaround\s*=|\bquantum\s*=|\d+\s*[+*/=]\s*\d+)', b)):
                flags.add('missing_numeric_evidence_review')
            body=(f'[DOCLING EXTRACTION — UNVERIFIED]\n{a or "[NO DOCLING TEXT]"}\n\n'
                  f'[SECONDARY PYMUPDF EXTRACTION — UNVERIFIED; CHECK ORIGINAL PAGE]\n{b}')
        elif result.ambiguous:
            flags.add('extractor_disagreement_ambiguous')
            body=(f'[DOCLING EXTRACTION — UNVERIFIED]\n{a}\n\n'
                  f'[SECONDARY PYMUPDF EXTRACTION — UNVERIFIED; CHECK ORIGINAL PAGE]\n{b}')
        elif result.order_only:
            flags.add('word_order_difference_informational')
        if not a and not b:
            flags.add('both_extractors_empty_visual_review')
        output.append(Page(primary.page_no,body,list(primary.figure_notes),sorted(flags),'hybrid'))
    return output

def parse_hybrid(path: Path) -> list[Page]:
    from .parsers import parse_docling, parse_pymupdf_diagnostic
    if Path(path).suffix.lower()!='.pdf':
        pages=parse_docling(path)
        for p in pages:p.flags.append('no_secondary_extractor_for_format')
        return pages
    return reconcile(parse_docling(path),parse_pymupdf_diagnostic(path))
