"""Docling production parser plus clearly labelled diagnostic PyMuPDF backend."""
from __future__ import annotations
import re
from functools import lru_cache
from pathlib import Path
from .core import Page


@lru_cache(maxsize=4)
def _docling_converter(formula_enrichment: bool=False, no_ocr: bool=False):
    """Reuse a single Docling converter across pages in the same process."""
    try:
        from docling.document_converter import DocumentConverter
    except ModuleNotFoundError as exc:
        if exc.name == "docling":
            raise RuntimeError(
                "Docling is not installed. Install the [parse] extra: "
                "python -m pip install -e '.[parse]'"
            ) from exc
        raise RuntimeError(
            f"Docling dependency import failed (missing module {exc.name!r}). "
            "Check the complete underlying exception and your Python environment."
        ) from exc
    except (ImportError, OSError) as exc:
        detail = str(exc)
        if "Application Control policy" in detail or "blocked this file" in detail:
            raise RuntimeError(
                "Windows Application Control blocked a native DLL required by "
                f"Docling or its dependencies: {detail}. This is an operating-system "
                "execution policy restriction, not proof that Docling is missing. "
                "Ask your device administrator to review the App Control/AppLocker "
                "event for the blocked dependency, or use an approved execution "
                "environment. Do not disable security controls or silently switch "
                "to the diagnostic parser."
            ) from exc
        raise RuntimeError(
            "Docling is installed but a dependency could not be imported: "
            f"{type(exc).__name__}: {detail}. Check dependency compatibility "
            "and the underlying traceback; reinstalling Docling alone may not help."
        ) from exc
    if formula_enrichment or no_ocr:
        from docling.document_converter import PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        options=PdfPipelineOptions()
        options.do_formula_enrichment=bool(formula_enrichment)
        options.do_table_structure=True
        if no_ocr:
            options.do_ocr=False
        return DocumentConverter(format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=options)})
    return DocumentConverter()


def parse_docling(path: Path, formula_enrichment: bool=False, no_ocr: bool=False) -> list[Page]:
    converter=_docling_converter(formula_enrichment=formula_enrichment, no_ocr=True) if no_ocr else (_docling_converter(formula_enrichment=True) if formula_enrichment else _docling_converter())
    result = converter.convert(str(path))
    doc = result.document
    # Per-page provenance avoids splitting whole-document Markdown by guessed headings.
    grouped: dict[int,list[str]] = {}
    flags_by_page: dict[int,set[str]] = {}
    figures_by_page: dict[int,list[str]] = {}
    seen = set()
    for element, level in doc.iterate_items():
        prov = getattr(element,'prov',None) or []
        if not prov:continue
        page_nos = sorted({int(p.page_no) for p in prov})
        typ = type(element).__name__.lower()
        label = str(getattr(element,'label','')).lower()
        is_table = typ == 'tableitem' or 'table' in label
        is_picture = typ == 'pictureitem' or 'picture' in label or 'figure' in label
        is_formula = 'formula' in typ or 'formula' in label or 'equation' in label
        body = ''
        if is_table:
            try:
                body = element.export_to_markdown(doc=doc).strip()
            except Exception:
                for no in page_nos:flags_by_page.setdefault(no,set()).add('table_structure_review_required')
                body = '[TABLE DETECTED — cannot serialize; inspect original page]'
            if not body:
                for no in page_nos:flags_by_page.setdefault(no,set()).add('table_structure_review_required')
                body = '[TABLE DETECTED — empty serialization; inspect original page]'
        elif is_formula:
            formula=str(getattr(element,'text',None) or '').strip()
            if not formula:
                body='[FORMULA DETECTED — no content; inspect original page]'
                for no in page_nos:
                    flags_by_page.setdefault(no,set()).add('formula_structure_review_required')
            elif formula.startswith(('$',r'\[',r'\(')):
                body=formula
            else:
                body=f'$$\n{formula}\n$$'
        elif is_picture:
            body = '[FIGURE DETECTED — inspect original page]'
            for no in page_nos:
                flags_by_page.setdefault(no,set()).add('figure_content_review_required')
                figures_by_page.setdefault(no,[]).append('Picture or figure detected in original PDF')
        else:
            text = getattr(element,'text',None)
            if text:body=str(text).strip()
        if not body: continue
        if len(page_nos)>1:
            for no in page_nos:flags_by_page.setdefault(no,set()).add('multi_page_item_review_required')
        for no in page_nos:
            key=(no,id(element))
            if key not in seen:
                grouped.setdefault(no,[]).append(body)
                seen.add(key)
    expected=len(doc.pages) if hasattr(doc,'pages') else max(grouped,default=0)
    if expected==0:raise ValueError('Docling returned no numbered pages')
    return [Page(i,'\n\n'.join(grouped.get(i,[])),figures_by_page.get(i,[]),
                 sorted(flags_by_page.get(i,set())),'docling')
            for i in range(1,expected+1)]

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
    if backend=='docling-no-ocr': return parse_docling(path,no_ocr=True)
    if backend=='hybrid-no-ocr':
        from .hybrid import reconcile
        if path.suffix.lower()!='.pdf':
            return parse_docling(path,no_ocr=True)
        return reconcile(parse_docling(path,no_ocr=True),parse_pymupdf_diagnostic(path))
    if backend=='docling': return parse_docling(path)
    if backend=='docling-formula': return parse_docling(path,formula_enrichment=True)
    if backend=='hybrid-formula':
        from .hybrid import reconcile
        return reconcile(parse_docling(path,formula_enrichment=True),parse_pymupdf_diagnostic(path))
    if backend=='hybrid':
        from .hybrid import parse_hybrid
        return parse_hybrid(path)
    if backend=='pymupdf-diagnostic': return parse_pymupdf_diagnostic(path)
    raise ValueError(f'Unknown backend: {backend}')
