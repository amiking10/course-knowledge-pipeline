from types import SimpleNamespace
import pytest
from course_pipeline import parsers

class FormulaItem:
    def __init__(self,text,page=1):
        self.label='formula'
        self.text=text
        self.prov=[SimpleNamespace(page_no=page)]

def fake_converter(items):
    doc=SimpleNamespace(pages={1:object()},iterate_items=lambda:((item,0) for item in items))
    return SimpleNamespace(convert=lambda path:SimpleNamespace(document=doc))

def test_formula_math_is_preserved_with_markdown_delimiters(monkeypatch,tmp_path):
    monkeypatch.setattr(parsers,'_docling_converter',lambda:fake_converter([
        FormulaItem(r'\\frac{a}{b}=c')]))
    pages=parsers.parse_docling(tmp_path/'fake.pdf')
    assert pages[0].body.startswith('$$')
    assert r'\\frac{a}{b}=c' in pages[0].body
    assert pages[0].body.endswith('$$')

def test_empty_formula_is_visible_and_review_flagged(monkeypatch,tmp_path):
    monkeypatch.setattr(parsers,'_docling_converter',lambda:fake_converter([FormulaItem('')]))
    pages=parsers.parse_docling(tmp_path/'fake.pdf')
    assert 'FORMULA DETECTED' in pages[0].body
    assert 'formula_structure_review_required' in pages[0].flags

def test_formula_backend_uses_enrichment(monkeypatch,tmp_path):
    flags=[]
    def fake_parse(path,formula_enrichment=False):
        flags.append(formula_enrichment)
        return [SimpleNamespace(page_no=1,body='$$x=1$$',figure_notes=[],flags=[],backend='docling')]
    monkeypatch.setattr(parsers,'parse_docling',fake_parse)
    result=parsers.parse(tmp_path/'x.pdf','docling-formula')
    assert flags==[True]
    assert result[0].body=='$$x=1$$'

def test_pdf_options_constructs_formula_enriched_converter(monkeypatch):
    import sys
    from types import ModuleType
    from course_pipeline.parsers import _docling_converter
    calls=[]
    converter_mod=ModuleType('docling.document_converter')
    class Converter:
        def __init__(self,**kw):calls.append(kw)
    converter_mod.DocumentConverter=Converter
    converter_mod.PdfFormatOption=lambda **kwargs:kwargs
    base_mod=ModuleType('docling.datamodel.base_models')
    base_mod.InputFormat=SimpleNamespace(PDF='pdf')
    options_mod=ModuleType('docling.datamodel.pipeline_options')
    class Options:
        do_formula_enrichment=False
        do_table_structure=False
    options_mod.PdfPipelineOptions=Options
    monkeypatch.setitem(sys.modules,'docling',ModuleType('docling'))
    monkeypatch.setitem(sys.modules,'docling.document_converter',converter_mod)
    monkeypatch.setitem(sys.modules,'docling.datamodel',ModuleType('docling.datamodel'))
    monkeypatch.setitem(sys.modules,'docling.datamodel.base_models',base_mod)
    monkeypatch.setitem(sys.modules,'docling.datamodel.pipeline_options',options_mod)
    _docling_converter.cache_clear()
    try:
        a=_docling_converter(True);b=_docling_converter(True)
        assert a is b
        assert len(calls)==1
        assert calls[0]['format_options']['pdf']['pipeline_options'].do_formula_enrichment
    finally:_docling_converter.cache_clear()
