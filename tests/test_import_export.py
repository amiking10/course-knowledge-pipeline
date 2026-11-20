import json
import fitz
import pytest
from course_pipeline.core import Store,hash_file
from course_pipeline.import_export import read_prior_export,import_and_reconcile


def build_test_case(tmp_path, mismatch=False):
    root=tmp_path/'src';root.mkdir()
    pdf=root/'lec.pdf';doc=fitz.open()
    doc.new_page().insert_text((50,70),'Round Robin scheduling Q=4 p1=24 p2=3 p3=3\n'
                                  'interrupt descriptor IDT signal handler concept with longer technical descriptions and process scheduling. '
                                  'Queue rotation changes the waiting time and each process gets its next quantum.')
    doc.save(pdf);doc.close()
    old=tmp_path/'previous';old.mkdir()
    contents='## Source: lec.pdf | page 1 | id old-source-id\r\n\r\nRR\r\n'
    (old/'course_sources_001.md').write_bytes(contents.encode('utf8'))
    (old/'manifest.json').write_text(json.dumps([{'source_id':'old-source-id','source_path':'lec.pdf',
        'source_sha256':'wrong' if mismatch else hash_file(pdf),'pages':1,'backend':'docling'}]))
    return root,old


def test_import_reconciles_old_export_and_marks_review(tmp_path):
    root,old=build_test_case(tmp_path)
    index,pages=read_prior_export(old)
    assert pages['lec.pdf',1]=='RR'
    with Store(tmp_path/'course.sqlite') as store:
        results=import_and_reconcile(store,root,old)
        assert results['processed']==1
        text=store.pages(store.sources()[0]['source_id'])[0]['body']
        assert 'DOCLING EXTRACTION' in text
        assert 'Q=4' in text


def test_reject_source_hash_mismatch(tmp_path):
    root,old=build_test_case(tmp_path,True)
    with Store(tmp_path/'course.sqlite') as store:
        with pytest.raises(ValueError,match='hash mismatch'):
            import_and_reconcile(store,root,old)
        assert store.sources()[0]['last_parsed_hash'] is None


def test_detect_incomplete_previous_export(tmp_path):
    root,old=build_test_case(tmp_path)
    manifest=json.loads((old/'manifest.json').read_text());manifest[0]['pages']=2
    (old/'manifest.json').write_text(json.dumps(manifest))
    with pytest.raises(ValueError,match='Incomplete'):
        read_prior_export(old)
