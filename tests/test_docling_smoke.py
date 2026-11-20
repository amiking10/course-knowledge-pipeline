"""Real parser smoke test. Runs only in the optional docling CI job."""
from pathlib import Path
import pytest


def test_docling_real_pdf_source_provenance(tmp_path: Path):
    pytest.importorskip('docling')
    fitz=pytest.importorskip('fitz')
    from course_pipeline.parsers import parse_docling

    path=tmp_path/'document.pdf'
    pdf=fitz.open()
    pdf.new_page().insert_text((60,90),'Operating systems process scheduling')
    pdf.new_page().insert_text((60,90),'Interrupt descriptor table IDT')
    pdf.save(path)
    pdf.close()
    parsed=parse_docling(path)
    assert len(parsed)==2
    assert [p.page_no for p in parsed]==[1,2]
    assert 'process' in parsed[0].body.lower()
    assert 'interrupt' in parsed[1].body.lower()
