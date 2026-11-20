"""Optional real-source integration tests: enabled with COURSE_TEST_CORPUS directory."""
import os
from pathlib import Path
import pytest
from course_pipeline.core import Store
from course_pipeline.parsers import parse_pymupdf_diagnostic
from course_pipeline.quality import assess
from course_pipeline.exporter import export_project


@pytest.mark.skipif(not os.getenv('COURSE_TEST_CORPUS'), reason='Set COURSE_TEST_CORPUS to local PDF directory')
def test_real_os_corpus(tmp_path):
    root=Path(os.environ['COURSE_TEST_CORPUS'])
    assert root.is_dir()
    with Store(tmp_path/'course.sqlite3') as store:
        result=store.scan(root)
        assert result['added'] >= 3
        counts=[]
        for row in store.pending('pymupdf-diagnostic'):
            pages=parse_pymupdf_diagnostic(root/row['relative_path'])
            report=assess(pages,root/row['relative_path'])
            assert len(pages)==report['pages']
            assert len({p.page_no for p in pages})==len(pages)
            store.save_pages(row['source_id'],pages,'pymupdf-diagnostic',row['sha256'])
            counts.append(len(pages))
        assert sum(counts) >= 20
        out=tmp_path/'export'
        exported=export_project(store,out)
        assert exported['sources']==len(counts)
        assert (out/'manifest.json').exists()
