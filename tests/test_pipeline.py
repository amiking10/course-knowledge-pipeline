from pathlib import Path
import pytest
from course_pipeline.core import Store,hash_file,Page
from course_pipeline.parsers import parse_pymupdf_diagnostic
from course_pipeline.quality import assess
from course_pipeline.exporter import export_project


def test_scan_incremental_missing_restore(tmp_path):
    src=tmp_path/'src';src.mkdir()
    p=src/'Lecture.PDF';p.write_bytes(b'first')
    with Store(tmp_path/'db.sqlite3') as s:
        assert s.scan(src)['added']==1
        before=s.sources()[0]
        assert s.scan(src)['unchanged']==1
        p.write_bytes(b'second')
        assert s.scan(src)['changed']==1
        assert s.sources()[0]['source_id']==before['source_id']
        p.unlink(); assert s.scan(src)['missing']==1
        p.write_bytes(b'second');assert s.scan(src)['changed']==1
        assert s.sources()[0]['state']=='active'


def test_search_export_and_replace(tmp_path):
    src=tmp_path/'src';src.mkdir();(src/'sample.pdf').write_bytes(b'x')
    with Store(tmp_path/'db.sqlite3') as s:
        s.scan(src);r=s.sources()[0]
        s.save_pages(r['source_id'],[Page(1,'kernel interrupt system',[],[],'docling')], 'docling',r['sha256'])
        assert s.search('interrupt')[0]['page_no']==1
        assert len(s.pending('docling'))==0
        d=tmp_path/'out';result=export_project(s,d)
        assert result['bundles']==1
        assert 'kernel interrupt system' in (d/'course_sources_001.md').read_text()
        s.save_pages(r['source_id'],[Page(1,'new message',[],[],'docling')], 'docling',r['sha256'])
        assert not s.search('interrupt')
        assert len(s.search('message'))==1


def test_failure_does_not_erase_old_pages(tmp_path):
    with Store(tmp_path/'db.sqlite3') as s:
        root=tmp_path/'s';root.mkdir();(root/'t.pdf').write_bytes(b'x');s.scan(root)
        row=s.sources()[0];sid=row['source_id']
        s.save_pages(sid,[Page(1,'good',[],[],'docling')], 'docling',row['sha256'])
        with pytest.raises(ValueError):s.save_pages(sid,[], 'docling',row['sha256'])
        assert s.pages(sid)[0]['body']=='good'


def test_quality_flags_empty_pages(tmp_path):
    p=tmp_path/'x.docx';p.write_bytes(b'x')
    result=assess([Page(1,'',[],[],'docling'),Page(2,'abc',[],[],'docling')],p)
    assert result['warning_count']==2


def test_diagnostic_pdf_parser(tmp_path):
    import fitz
    p=tmp_path/'test.pdf';doc=fitz.open();doc.new_page().insert_text((50,50),'interrupt hello');doc.save(p);doc.close()
    assert 'interrupt' in parse_pymupdf_diagnostic(p)[0].body


def test_stale_exports_removed_and_missing_sources_omitted(tmp_path):
    root=tmp_path/'s';root.mkdir();(root/'a.pdf').write_bytes(b'a')
    with Store(tmp_path/'db.sqlite3') as s:
        s.scan(root);r=s.sources()[0]
        s.save_pages(r['source_id'],[Page(1,'content',[],[],'docling')],'docling',r['sha256'])
        out=tmp_path/'out';out.mkdir();(out/'course_sources_999.md').write_text('STALE')
        export_project(s,out)
        assert not (out/'course_sources_999.md').exists()
        (root/'a.pdf').unlink();s.scan(root)
        assert export_project(s,out)['sources']==0
        assert not (out/'course_sources_001.md').exists()

def test_parser_backend_change_forces_reprocessing(tmp_path):
    root=tmp_path/'s';root.mkdir();(root/'a.pdf').write_bytes(b'a')
    with Store(tmp_path/'db.sqlite3') as s:
        s.scan(root);r=s.sources()[0]
        s.save_pages(r['source_id'],[Page(1,'content',[],[],'docling')],'docling',r['sha256'])
        assert not s.pending('docling')
        assert len(s.pending('pymupdf-diagnostic'))==1


def test_changed_source_never_exported_stale(tmp_path):
    root=tmp_path/'src';root.mkdir();f=root/'lecture.pdf';f.write_bytes(b'v1')
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root);row=store.sources()[0]
        store.save_pages(row['source_id'],[Page(1,'old fact',[],[],'docling')], 'docling',row['sha256'])
        f.write_bytes(b'v2');store.scan(root)
        assert not store.search('old')
        assert export_project(store,tmp_path/'export')['sources']==0


def test_page_split_retains_full_provenance(tmp_path):
    root=tmp_path/'src';root.mkdir();(root/'lecture.pdf').write_bytes(b'bytes')
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root);row=store.sources()[0]
        store.save_pages(row['source_id'],[Page(1,'X'*2500,[],[],'docling')], 'docling',row['sha256'])
        out=tmp_path/'export'
        result=export_project(store,out, max_chars=1100)
        assert result['bundles']>=3
        all_text=''.join((out/name).read_text() for name in result['bundle_files'])
        assert all_text.count('lecture.pdf | page 1')>=3
        assert all_text.count('X')==2500


def test_enrichment_must_be_reviewable(tmp_path):
    from course_pipeline.enrichment import save_notes,load_notes
    good={'source_id':'s','page_no':1,'kind':'figure','content':'graph shows three curves',
          'evidence':'manual review of rendered slide','reviewed':False}
    p=tmp_path/'notes.json';save_notes(p,[good]);assert load_notes(p)==[good]
    with pytest.raises(ValueError):save_notes(p,[{'content':'unsupported'}])


def test_hybrid_ranking_and_benchmark(tmp_path):
    import json
    from course_pipeline.retrieval import hybrid_search
    from course_pipeline.benchmark import evaluate
    root=tmp_path/'src';root.mkdir()
    (root/'doc.pdf').write_bytes(b'bytes')
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root);row=store.sources()[0]
        store.save_pages(row['source_id'],[
            Page(1,'context switching changes process execution on CPU',[],[],'docling'),
            Page(2,'the interrupt descriptor table maps interrupt vectors',[],[],'docling')],
            'docling',row['sha256'])
        hits=hybrid_search(store,'interrupt descriptor table')
        assert hits[0]['page']==2
        gold=tmp_path/'benchmark.json'
        gold.write_text(json.dumps([{'question':'interrupt descriptor table',
            'expected':[{'source':'doc.pdf','page':2}]}]))
        assert evaluate(store,gold)['hit_at_k']==1


def test_render_review(tmp_path):
    import fitz
    from course_pipeline.visuals import render_review
    doc=fitz.open();doc.new_page();f=tmp_path/'a.pdf';doc.save(f);doc.close()
    result=render_review(f,[1],tmp_path/'renders',dpi=72)
    assert result['artifacts'][0]['page']==1
    assert (tmp_path/'renders'/'page-0001.png').exists()


def test_docling_adapter_mock_provenance(monkeypatch, tmp_path):
    """API contract test with mock converter; not a real Docling extraction test."""
    import sys, types
    from course_pipeline.parsers import parse_docling
    class Item:
        text='hello lecture'; prov=[types.SimpleNamespace(page_no=2)]
    class Doc:
        pages=[object(),object()]
        def iterate_items(self):yield Item(),0
    class Converter:
        def convert(self,filename):return types.SimpleNamespace(document=Doc())
    root=types.ModuleType('docling')
    sub=types.ModuleType('docling.document_converter')
    sub.DocumentConverter=Converter
    monkeypatch.setitem(sys.modules,'docling',root)
    monkeypatch.setitem(sys.modules,'docling.document_converter',sub)
    pages=parse_docling(tmp_path/'fake.pdf')
    assert len(pages)==2
    assert pages[0].body=='' and pages[1].body=='hello lecture'
    assert pages[1].page_no==2


def test_cli_parse_failure_exit_is_nonzero(tmp_path, capsys):
    from course_pipeline.cli import main
    root=tmp_path/'sources';root.mkdir()
    (root/'not-a-real-pdf.pdf').write_bytes(b'INVALID')
    with pytest.raises(SystemExit) as exc:
        main(['--db',str(tmp_path/'db.sqlite'),'parse',str(root),
              '--backend','pymupdf-diagnostic'])
    assert exc.value.code==2
    assert 'failures' in capsys.readouterr().out


def test_visual_pdf_bundle_preserves_source_page_count_and_bookmarks(tmp_path):
    import fitz
    from course_pipeline.pdf_bundle import export_pdf_bundle
    root=tmp_path/'source';root.mkdir()
    for idx,count in [('a',2),('b',3)]:
        doc=fitz.open()
        for p in range(count):doc.new_page().insert_text((50,70),f'{idx}-page-{p+1}')
        doc.save(root/f'{idx}.pdf');doc.close()
    with Store(tmp_path/'db.sqlite') as store:
        store.scan(root)
        target=tmp_path/'merged.pdf'
        report=export_pdf_bundle(store,root,target)
        assert report['total_pages']==5
        assert [(s['merged_start_page'],s['merged_end_page']) for s in report['sources']]==[(1,2),(3,5)]
        with fitz.open(target) as merged:
            assert len(merged)==5
            assert len(merged.get_toc())==2
            assert 'b-page-1' in merged[2].get_text()
