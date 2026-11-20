"""Conservative extraction completeness checks; warnings are not accuracy guarantees."""
from __future__ import annotations
import json
from pathlib import Path
from .core import Page


def assess(pages: list[Page], source: Path) -> dict:
    warnings=[]
    if not pages: warnings.append({'page':None,'kind':'empty_document'})
    for p in pages:
        if not p.body.strip(): warnings.append({'page':p.page_no,'kind':'empty_text'})
        elif len(p.body.strip())<100: warnings.append({'page':p.page_no,'kind':'low_text_density'})
        if '\ufffd' in p.body: warnings.append({'page':p.page_no,'kind':'replacement_characters'})
    # Diagnostic inspection is deliberately separate from Docling's own extraction.
    if source.suffix.lower()=='.pdf':
        try:
            import fitz
            with fitz.open(source) as doc:
                if len(doc)!=len(pages):
                    warnings.append({'page':None,'kind':'page_count_mismatch',
                                     'expected':len(doc),'observed':len(pages)})
                for i,p in enumerate(doc):
                    # PDFs may have thousands of tiny vector/image assets; no image-count claim.
                    if len(pages)>i and p.rect.get_area()>0 and not pages[i].body.strip():
                        # Do not render every page during parsing: PNG creation belongs in review-queue.
                        warnings.append({'page':i+1,'kind':'visual_review_required'})
        except ImportError:
            warnings.append({'page':None,'kind':'pdf_visual_check_unavailable'})
    return {'source':source.name,'pages':len(pages),'text_chars':sum(len(p.body) for p in pages),
            'warnings':warnings,'warning_count':len(warnings)}
