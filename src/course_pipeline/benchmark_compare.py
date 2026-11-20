"""Paired comparison of benchmark runs, with strict source-identity checks."""
import json
from pathlib import Path
from statistics import median

def compare_runs(run_paths: list[Path], output: Path) -> dict:
    if len(run_paths)<2:raise ValueError('Need at least two runs for a comparison')
    runs=[json.loads(Path(p).read_text(encoding='utf-8')) for p in run_paths]
    expected=None;seen_names=set();tables=[]
    for run in runs:
        backend=run['backend']
        if backend in seen_names: raise ValueError(f'Duplicate parser run: {backend}')
        seen_names.add(backend)
        if run['successful']+run['failed']!=run['total_cases']:
            raise ValueError('Inconsistent status counters')
        current={(case['id'],case['source_sha256']) for case in run['cases']}
        if len(current)!=run['total_cases']:raise ValueError('Duplicate case records')
        if expected is None: expected=current
        if current!=expected:raise ValueError('Parser runs have different samples or PDF bytes')
        if (run['dataset'],run['dataset_revision'])!=(runs[0]['dataset'],runs[0]['dataset_revision']):
            raise ValueError('Dataset or revision mismatch')
        times=[c['duration_seconds'] for c in run['cases'] if c['status']=='ok']
        failed=[c['id'] for c in run['cases'] if c['status']!='ok']
        tables.append({'backend':backend,'cases':len(current),'successful':len(times),
                       'failed':len(failed),'failed_ids':failed,
                       'median_seconds_per_success':round(median(times),3) if times else None,
                       'total_seconds':round(sum(c['duration_seconds'] for c in run['cases']),3),
                       'official_score':None})
    result={'dataset':runs[0]['dataset'],'revision':runs[0]['dataset_revision'],
            'identical_source_bytes':True,'results':tables,
            'note':'Runtime comparison only; evaluate accuracy with official upstream evaluator.'}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result
