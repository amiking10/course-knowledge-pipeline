"""Prepare pinned OmniDocBench pages as reproducible raster-input PDF cases.

The pages are created from benchmark images, not native vector PDFs. Scores
therefore describe raster-image PDFs and MUST be labeled as such.
"""
from __future__ import annotations
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath

from .public_benchmarks import pick_stratified, load_manifest


def _safe_image_path(entry: dict) -> str:
    value=entry.get('page_info',{}).get('image_path')
    if not isinstance(value,str) or not value.strip():
        raise ValueError('Missing page_info.image_path in OmniDocBench annotation')
    path=PurePosixPath(value.replace('\\','/'))
    if (path.is_absolute() or '..' in path.parts or ':' in value or value.startswith('\\\\')
        or path.suffix.lower() not in {'.png','.jpg','.jpeg'}):
        raise ValueError(f'Unsafe or unsupported image_path: {value!r}')
    # Annotation filenames are typically basenames; Hugging Face keeps them in images/.
    return str(path) if path.parts[0]=='images' else 'images/'+str(path)


def _stratum(entry: dict) -> str:
    kinds={d.get('category_type') for d in entry.get('layout_dets',[]) if not d.get('ignore')}
    if 'table' in kinds: return 'table'
    if any('equation' in (k or '') for k in kinds): return 'formula'
    if any((k or '') in {'figure','image','picture'} for k in kinds): return 'figure'
    return 'text_or_other'


def prepare_omnidocbench(output: Path, *, revision: str, count: int=200, seed: int=42,
                         repository: str='opendatalab/OmniDocBench',
                         fetch_file=None) -> dict:
    if not revision or revision in {'main','master','latest'}:
        raise ValueError('Pin a concrete Hugging Face dataset commit hash, not a moving branch')
    if repository!='opendatalab/OmniDocBench':
        raise ValueError('This adapter is verified only against the official OmniDocBench repository')
    if fetch_file is None:
        try:
            from huggingface_hub import hf_hub_download
        except ImportError as exc:
            raise RuntimeError('Install huggingface_hub for the benchmark dataset adapter') from exc
        def fetch_file(filename):
            return Path(hf_hub_download(repo_id=repository,filename=filename,repo_type='dataset',revision=revision))
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    source=Path(fetch_file('OmniDocBench.json'))
    original=source.read_bytes()
    annotations=json.loads(original)
    if not isinstance(annotations,list) or not annotations:
        raise ValueError('Expected nonempty OmniDocBench page annotation list')
    records=[];used=set()
    for entry in annotations:
        image_path=_safe_image_path(entry)
        stem=PurePosixPath(image_path).stem
        if stem in used:
            raise ValueError(f'Duplicate image basename; official evaluator would overwrite it: {stem}')
        used.add(stem)
        records.append({'id':stem,'pdf':f'pages/{stem}.pdf',
                        'image_path':image_path,'stratum':_stratum(entry),
                        'annotation':entry})
    chosen=pick_stratified(records,count,seed)
    import pymupdf
    from pymupdf import open as open_pdf, Rect
    cases=[];selection=[]
    pages_dir=output/'pages';pages_dir.mkdir(exist_ok=True)
    for record in chosen:
        image_path=record['image_path']
        image_file=Path(fetch_file(image_path))
        if not image_file.is_file():
            raise FileNotFoundError(f'Missing benchmark image: {image_path}')
        pdf_path=pages_dir/f"{record['id']}.pdf"
        image_bytes=image_file.read_bytes()
        doc=open_pdf()
        try:
            pix_info=pymupdf.Pixmap(image_bytes)
            width,height=pix_info.width,pix_info.height
            if not width or not height: raise ValueError(f'Empty image {image_path}')
            # Fixed pixel-to-point mapping, with image preserved without text OCR.
            page=doc.new_page(width=width,height=height)
            page.insert_image(Rect(0,0,width,height),stream=image_bytes)
            doc.save(pdf_path,deflate=True)
        finally:
            doc.close()
        cases.append({'id':record['id'],'pdf':record['pdf'],'stratum':record['stratum']})
        selection.append(record['annotation'])
    manifest={'dataset':'omnidocbench','revision':revision,'input_modality':'raster_image_wrapped_in_pdf',
              'seed':seed,'source_annotation_sha256':sha256(original).hexdigest(),
              'cases':cases}
    manifest_path=output/'manifest.json'
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'OmniDocBench_subset.json').write_text(
        json.dumps(selection,ensure_ascii=False,indent=2),encoding='utf-8')
    load_manifest(manifest_path)
    result={'count':len(cases),'dataset_revision':revision,'input_modality':manifest['input_modality'],
            'manifest':str(manifest_path),'ground_truth':str(output/'OmniDocBench_subset.json')}
    (output/'preparation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    return result
