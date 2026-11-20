"""Reproducible PDF benchmark runner; never impersonates official benchmark scores.

Manifest format: {"dataset":"omnidocbench","revision":"<pinned revision>",
 "cases":[{"id":"page_0001","pdf":"pages/page_0001.pdf","stratum":"formula"}]}.
A case is one PDF page. Model predictions are written as <id>.md.
Run the dataset owner's official evaluator on predictions for official scores.
"""
from __future__ import annotations
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import random
import re
import time

from .parsers import parse
from .comparison import tokens


ALLOWED_DATASETS = {'omnidocbench','olmocr-bench','course-gold'}
ALLOWED_BACKENDS = {'docling','hybrid','pymupdf-diagnostic'}
ID_PATTERN = re.compile(r'^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$')


def load_manifest(path: Path) -> dict:
    path=Path(path)
    obj=json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(obj,dict) or obj.get('dataset') not in ALLOWED_DATASETS:
        raise ValueError('Unknown benchmark dataset')
    if not isinstance(obj.get('revision'),str) or not obj['revision'].strip():
        raise ValueError('Dataset revision is required for reproducibility')
    cases=obj.get('cases')
    if not isinstance(cases,list) or not cases:
        raise ValueError('Nonempty cases array required')
    seen=set()
    for case in cases:
        if not isinstance(case,dict) or not ID_PATTERN.fullmatch(str(case.get('id',''))):
            raise ValueError('Invalid benchmark case ID')
        if case['id'] in seen: raise ValueError('Duplicate benchmark case ID')
        seen.add(case['id'])
        rel=Path(case.get('pdf',''))
        if not rel.parts or rel.is_absolute() or '..' in rel.parts or rel.suffix.lower()!='.pdf':
            raise ValueError('Case PDF must be a safe relative .pdf path')
        if not isinstance(case.get('stratum'),str) or not case['stratum'].strip():
            raise ValueError('Every case requires a stratum')
    return obj


def pick_stratified(cases: list[dict], size: int, seed: int = 42) -> list[dict]:
    if size<1 or size>len(cases): raise ValueError('Sample size must be within case count')
    groups=defaultdict(list)
    for case in cases:groups[case['stratum']].append(case)
    rng=random.Random(seed)
    for group in groups.values():group.sort(key=lambda c:c['id']);rng.shuffle(group)
    result=[]
    keys=sorted(groups)
    # Round robin provides broad coverage without hiding undersampled strata.
    while len(result)<size:
        for key in keys:
            if groups[key] and len(result)<size:result.append(groups[key].pop())
    return sorted(result,key=lambda c:c['id'])


def token_diagnostics(prediction: str, reference: str) -> dict:
    """Auxiliary token overlap ONLY; not OmniDocBench CDM/TEDS/ED or olmOCR scoring."""
    from collections import Counter
    predicted=Counter(tokens(prediction));ground=Counter(tokens(reference))
    overlap=sum((predicted & ground).values())
    total=sum(ground.values());produced=sum(predicted.values())
    return {'reference_tokens':total,'predicted_tokens':produced,
            'token_recall':round(overlap/total,4) if total else None,
            'token_precision':round(overlap/produced,4) if produced else None,
            'metric':'diagnostic_token_overlap_not_official'}


def run_manifest(manifest_path: Path, output: Path, backend: str='hybrid',
                 *, sample: int|None=None, seed: int=42) -> dict:
    if backend not in ALLOWED_BACKENDS: raise ValueError('Unsupported parser backend')
    manifest_path=Path(manifest_path).resolve()
    manifest=load_manifest(manifest_path)
    root=manifest_path.parent
    cases=manifest['cases'] if sample is None else pick_stratified(manifest['cases'],sample,seed)
    output=Path(output).resolve()
    output.mkdir(parents=True,exist_ok=True)
    pred_dir=output/'predictions';pred_dir.mkdir(exist_ok=True)
    results=[]
    for case in cases:
        path=(root/case['pdf']).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise FileNotFoundError(f'Benchmark PDF missing or outside manifest root: {case["id"]}')
        started=time.perf_counter()
        digest=sha256(path.read_bytes()).hexdigest()
        record={'id':case['id'],'stratum':case['stratum'],'pdf':case['pdf'],
                'source_sha256':digest,'status':'error'}
        try:
            pages=parse(path,backend)
            if len(pages)!=1:
                raise ValueError(f'Expected a single-page PDF, received {len(pages)} pages')
            prediction=pages[0].body
            (pred_dir/f'{case["id"]}.md').write_text(prediction,encoding='utf-8')
            record.update(status='ok',page_count=1,prediction_file=f'predictions/{case["id"]}.md',
                          characters=len(prediction))
        except Exception as exc:
            record['error']=f'{type(exc).__name__}: {exc}'
        record['duration_seconds']=round(time.perf_counter()-started,3)
        results.append(record)
    ok=sum(x['status']=='ok' for x in results)
    report={'dataset':manifest['dataset'],'dataset_revision':manifest['revision'],
            'backend':backend,'seed':seed,'sample_requested':sample,'total_cases':len(results),
            'successful':ok,'failed':len(results)-ok,'cases':results,
            'official_score':None,'note':'Run dataset owner official scorer on the predicted Markdown. Missing outputs must count as failures.'}
    (output/'run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    return report
