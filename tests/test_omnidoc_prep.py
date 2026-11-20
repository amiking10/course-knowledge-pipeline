import json
from pathlib import Path
import pytest

from course_pipeline.omnidoc_prep import prepare_omnidocbench, _stratum, _safe_image_path
from course_pipeline.public_benchmarks import load_manifest, run_manifest


def fake_omni_files(tmp_path):
    from PIL import Image
    root=tmp_path/'official';(root/'images').mkdir(parents=True)
    ann=[]
    for i,kind in enumerate(['table','equation_isolated','text_block','text_block']):
        name=f'images/page_{i:03d}.png'
        Image.new('RGB',(120,160),'white').save(root/name)
        ann.append({'page_info':{'image_path':name,'width':120,'height':160},
                    'layout_dets':[{'category_type':kind,'ignore':False,'order':0,'text':'hello'}]})
    (root/'OmniDocBench.json').write_text(json.dumps(ann),encoding='utf-8')
    return root


def test_omni_prep_subset_and_real_page_pdf(tmp_path):
    from pymupdf import open as open_pdf
    root=fake_omni_files(tmp_path)
    out=tmp_path/'out'
    result=prepare_omnidocbench(out,revision='aa1ee96d106dbe53d0ae59474d75c6e6d9b53fec',
                                count=3,seed=42,fetch_file=lambda rel:root/rel)
    assert result['count']==3
    assert result['input_modality']=='raster_image_wrapped_in_pdf'
    manifest=load_manifest(out/'manifest.json')
    assert len(manifest['cases'])==3
    assert set(c['stratum'] for c in manifest['cases'])=={'table','formula','text_or_other'}
    assert len(json.loads((out/'OmniDocBench_subset.json').read_text(encoding='utf-8')))==3
    for case in manifest['cases']:
        with open_pdf(out/case['pdf']) as doc:
            assert len(doc)==1
            assert doc[0].get_images()
            assert not doc[0].get_text().strip()
    run=run_manifest(out/'manifest.json',tmp_path/'pred',backend='pymupdf-diagnostic')
    assert run['successful']==3

def test_omni_prep_revision_and_path_guards(tmp_path):
    root=fake_omni_files(tmp_path)
    with pytest.raises(ValueError,match='Pin a concrete'):
        prepare_omnidocbench(tmp_path/'out',revision='main',count=2,fetch_file=lambda rel:root/rel)
    assert _stratum({'layout_dets':[{'category_type':'equation_isolated'}]})=='formula'
    with pytest.raises(ValueError,match='Unsafe'):
        _safe_image_path({'page_info':{'image_path':'../secret.png'}})
    with pytest.raises(ValueError,match='Unsafe'):
        _safe_image_path({'page_info':{'image_path':'C:\\secret.png'}})
    entries=json.loads((root/'OmniDocBench.json').read_text(encoding='utf-8'))
    entries[1]['page_info']['image_path']=entries[0]['page_info']['image_path']
    (root/'OmniDocBench.json').write_text(json.dumps(entries),encoding='utf-8')
    with pytest.raises(ValueError,match='Duplicate'):
        prepare_omnidocbench(tmp_path/'out',revision='aa1ee96',count=2,fetch_file=lambda rel:root/rel)
