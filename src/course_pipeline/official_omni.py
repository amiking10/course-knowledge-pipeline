"""Generate and preflight a config for the upstream OmniDocBench evaluator.

The scorer is *not* reimplemented here. Upstream OmniDocBench must be installed
separately, pinned to a real commit, with its documented runtime dependencies.
"""
from __future__ import annotations
from pathlib import Path
import json
import re

def prepare_official_evaluation(ground_truth: Path, run_json: Path, output_dir: Path,
                                *, evaluator_commit: str)->dict:
    if not re.fullmatch(r'[a-fA-F0-9]{40}',evaluator_commit):
        raise ValueError('Pin the evaluator to a full 40-digit Git commit SHA')
    ground_truth=Path(ground_truth).resolve()
    run_json=Path(run_json).resolve()
    output_dir=Path(output_dir).resolve()
    if not ground_truth.is_file() or not run_json.is_file():
        raise FileNotFoundError('Ground truth and run JSON files must exist')
    truth=json.loads(ground_truth.read_text(encoding='utf-8'))
    run=json.loads(run_json.read_text(encoding='utf-8'))
    if not isinstance(truth,list) or not truth:
        raise ValueError('Expected a nonempty ground-truth page list')
    names=[Path(item['page_info']['image_path']).stem for item in truth]
    if len(names)!=len(set(names)):
        raise ValueError('Duplicate page names in official ground truth')
    cases=run.get('cases',[])
    if set(names)!={c['id'] for c in cases} or len(cases)!=len(names):
        raise ValueError('Prediction/ground-truth case sets must match exactly')
    predictions=run_json.parent/'predictions'
    missing=[]
    for case in cases:
        path=predictions/f"{case['id']}.md"
        if case.get('status')!='ok' or not path.is_file():
            missing.append(case['id'])
    if missing:
        raise ValueError(f'Cannot declare official evaluation ready: {len(missing)} missing/failed prediction(s): {missing[:8]}')
    if run.get('dataset')!='omnidocbench':
        raise ValueError('Official OmniDocBench scorer requires OmniDocBench dataset')
    output_dir.mkdir(parents=True,exist_ok=True)
    # This is the documented OmniDocBench v1.6/v1.7 end2end YAML form.
    # Absolute paths are quoted using JSON string quoting (YAML-compatible).
    def q(path): return json.dumps(str(path),ensure_ascii=False)
    config=f"""end2end_eval:
  metrics:
    text_block:
      metric: [Edit_dist]
    display_formula:
      metric: [Edit_dist, CDM]
    table:
      metric: [TEDS, Edit_dist]
    reading_order:
      metric: [Edit_dist]
  dataset:
    dataset_name: end2end_dataset
    ground_truth:
      data_path: {q(ground_truth)}
    prediction:
      data_path: {q(predictions)}
    match_method: quick_match
    match_workers: 2
    quick_match_truncated_timeout_sec: 300
    timeout_fallback_max_chunk_span: 10
    timeout_fallback_order_penalty: 0.10
"""
    config_path=output_dir/'official_end2end.yaml'
    config_path.write_text(config,encoding='utf-8')
    metadata={'dataset':'omnidocbench','dataset_revision':run['dataset_revision'],
              'evaluator_commit':evaluator_commit,'parser_backend':run['backend'],
              'case_count':len(cases),'status':'prepared_not_scored',
              'config':str(config_path),
              'command':f'python pdf_validation.py --config "{config_path}"',
              'note':'Run this from the pinned upstream OmniDocBench repository with CDM dependencies installed.'}
    (output_dir/'official_evaluation_manifest.json').write_text(
        json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    return metadata
