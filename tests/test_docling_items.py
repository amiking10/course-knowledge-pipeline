from types import SimpleNamespace
from course_pipeline import parsers

class TableItem:
    def __init__(self,pages=(1,),fail=False):
        self.prov=[SimpleNamespace(page_no=n) for n in pages]
        self.label='table'
        self.fail=fail
    def export_to_markdown(self,doc):
        if self.fail:raise ValueError('test error')
        return '| Process | Burst |\n|---|---|\n| p1 | 24 |\n| p2 | 3 |'

class PictureItem:
    def __init__(self,page=1):
        self.prov=[SimpleNamespace(page_no=page)]
        self.label='picture'

class PlainItem:
    def __init__(self,text,page=1):
        self.text=text;self.prov=[SimpleNamespace(page_no=page)]
        self.label='text'

def make_converter(items,total=2):
    document=SimpleNamespace(pages={i:object() for i in range(1,total+1)})
    document.iterate_items=lambda :((item,0) for item in items)
    return SimpleNamespace(convert=lambda path:SimpleNamespace(document=document))

def test_tables_and_pictures_are_retained(monkeypatch,tmp_path):
    converter=make_converter([PlainItem('Scheduling'),TableItem(),PictureItem(1)],2)
    monkeypatch.setattr(parsers,'_docling_converter',lambda:converter)
    result=parsers.parse_docling(tmp_path/'dummy.pdf')
    assert len(result)==2
    assert '| p1 | 24 |' in result[0].body
    assert 'FIGURE DETECTED' in result[0].body
    assert 'figure_content_review_required' in result[0].flags
    assert result[0].figure_notes
    assert not result[1].body

def test_table_failure_is_explicitly_flagged(monkeypatch,tmp_path):
    monkeypatch.setattr(parsers,'_docling_converter',
                        lambda:make_converter([TableItem(fail=True)],1))
    result=parsers.parse_docling(tmp_path/'dummy.pdf')
    assert 'TABLE DETECTED' in result[0].body
    assert 'table_structure_review_required' in result[0].flags

def test_mult_page_items_not_silently_dropped(monkeypatch,tmp_path):
    monkeypatch.setattr(parsers,'_docling_converter',
                        lambda:make_converter([TableItem((1,2))],2))
    result=parsers.parse_docling(tmp_path/'dummy.pdf')
    assert all('multi_page_item_review_required' in p.flags for p in result)
    assert all('p1 | 24' in p.body for p in result)
