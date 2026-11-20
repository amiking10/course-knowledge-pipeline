"""Conservative Gantt validation of prior unverified PDF geometry proposals.

This module validates structural and numerical invariants, not whether a Gantt
chart was visually interpreted correctly. Keep ambiguous hypotheses separate
from usable-for-review candidates. No source extraction is mutated.
"""
from __future__ import annotations
from collections import Counter, defaultdict
from pathlib import Path
import html
import json
import math
import tempfile

EPS=1e-7


def _num(value):
    if isinstance(value, bool) or not isinstance(value,(float,int)):
        raise ValueError("Expected numeric tick or duration")
    n=float(value)
    if not math.isfinite(n):
        raise ValueError("Non-finite numerical value")
    return n


def _table_runtimes(tables):
    """Only use process runtime columns explicitly associated with headers."""
    candidates=[]
    for table in tables:
        columns=table.get("column_semantics",[])
        if not isinstance(columns,list) or columns.count("run_time")!=1:continue
        idx=columns.index("run_time")
        runtimes={}
        for row in table.get("rows",[]):
            cells=row.get("cells",[])
            key=str(row.get("process","")).lower()
            if not key or key in runtimes or idx>=len(cells) or cells[idx] is None:
                continue
            try:runtimes[key]=_num(float(cells[idx]["value"]))
            except (TypeError,ValueError,KeyError):pass
        if runtimes:candidates.append(runtimes)
    return candidates


def assess_timeline(candidate,tables):
    """Report invariants and suitability for review, never correctness."""
    findings=[]
    ticks=candidate.get("timeline_ticks",[])
    labels=candidate.get("process_labels",[])
    intervals=candidate.get("interval_candidates",[])
    if not isinstance(ticks,list) or not isinstance(labels,list) or not isinstance(intervals,list):
        raise ValueError("Invalid timeline candidate")

    try: times=[_num(t["time"]) for t in ticks]
    except (KeyError,TypeError) as exc:
        raise ValueError("Malformed timeline ticks") from exc
    strictly_increasing=(len(times)>=3 and
                         all(b-a>EPS for a,b in zip(times,times[1:])))
    findings.append({"check":"increasing_timestamps","passed":strictly_increasing})

    allowed={(round(a,8),round(b,8)) for a,b in zip(times,times[1:])}
    assigned=defaultdict(list)
    well_formed=True
    process_totals=defaultdict(float)
    for interval in intervals:
        try:
            start=_num(interval["start_candidate"])
            end=_num(interval["end_candidate"])
            label=str(interval["process"]).lower()
        except (KeyError,ValueError,TypeError):
            well_formed=False;continue
        if not label or end-start<=EPS or (round(start,8),round(end,8)) not in allowed:
            well_formed=False;continue
        assigned[(round(start,8),round(end,8))].append(label)
        process_totals[label]+=end-start
    findings.append({"check":"intervals_use_adjacent_source_ticks","passed":well_formed})
    complete=len(labels)>0 and len(intervals)==len(labels) and well_formed
    findings.append({"check":"all_process_labels_assigned","passed":complete})
    collisions=[
        {"start":a,"end":b,"processes":processes}
        for (a,b),processes in sorted(assigned.items())
        if len(processes)>1
    ]
    findings.append({"check":"single_process_per_interval","passed":not collisions})

    # A continuous chart with labels covering all adjacent intervals has
    # stronger geometric support than a partially populated set of labels.
    used=set(assigned)
    no_gaps=bool(allowed) and used==allowed
    findings.append({"check":"complete_timeline_coverage","passed":no_gaps})

    runtime_checks=[]
    for runtimes in _table_runtimes(tables):
        for process,observed in sorted(process_totals.items()):
            if process not in runtimes:continue
            runtime_checks.append({"process":process,"table_runtime":runtimes[process],
                 "proposed_total":observed,
                 "passed":abs(observed-runtimes[process])<=EPS,
                 "status":"numeric_consistency_not_ground_truth"})
    if runtime_checks:
        findings.append({"check":"compared_process_runtime_totals",
            "passed":all(x["passed"] for x in runtime_checks)})
    else:
        findings.append({"check":"compared_process_runtime_totals",
            "passed":None,"reason":"No aligned source runtime table for comparison"})

    geometry_safe=all((
        strictly_increasing,well_formed,complete,not collisions,no_gaps
    ))
    math_safe=not runtime_checks or all(c["passed"] for c in runtime_checks)
    ready=geometry_safe and math_safe
    return {
        "classification":("coherent_candidate_for_review" if ready
                          else "ambiguous_or_inconsistent_candidate"),
        "verified_against_original_image":False,
        "usable_as_ground_truth":False,
        "geometric_checks_passed":geometry_safe,
        "runtime_checks_passed":(all(c["passed"] for c in runtime_checks)
                                 if runtime_checks else None),
        "checks":findings,"collisions":collisions,
        "runtime_checks":runtime_checks,
        "source_interval_count":len(allowed),
        "proposed_interval_count":len(intervals),
    }


def score_report(data):
    if data.get("schema_version") not in ("0.11.2","0.11.3"):
        raise ValueError("Expected v0.11.2/0.11.3 reconstruction JSON")
    if not isinstance(data.get("pages"),list):
        raise ValueError("Missing pages array")
    output=[]
    for page in data["pages"]:
        candidates=page.get("cross_block_gantt_candidates",[])
        tables=page.get("borderless_table_candidates",[])
        evaluations=[assess_timeline(t,tables) for t in candidates]
        output.append({
            "source":page.get("source"),"page":page.get("page"),
            "source_sha256":page.get("source_sha256"),
            "extraction_sha256":page.get("extraction_sha256"),
            "timeline_evaluations":evaluations,
            "candidate_count":len(evaluations),
            "coherent_for_review":sum(e["classification"]=="coherent_candidate_for_review"
                                      for e in evaluations),
            "ambiguous_or_inconsistent":sum(e["classification"]=="ambiguous_or_inconsistent_candidate"
                                            for e in evaluations),
            "needs_visual_recovery":not evaluations or
                                    any(e["classification"]!="coherent_candidate_for_review"
                                        for e in evaluations),
        })
    return {
        "schema_version":"0.11.3",
        "status":"structural_consistency_validation_not_ground_truth",
        "page_count":len(output),
        "timeline_candidates":sum(p["candidate_count"] for p in output),
        "coherent_for_review":sum(p["coherent_for_review"] for p in output),
        "ambiguous_or_inconsistent":sum(p["ambiguous_or_inconsistent"] for p in output),
        "pages_without_candidates":sum(p["candidate_count"]==0 for p in output),
        "pages":output,
    }


def validate_reconstruction_report(input_file:Path,out_dir:Path):
    data=json.loads(Path(input_file).read_text(encoding="utf-8"))
    result=score_report(data)
    out_dir=Path(out_dir)
    out_dir.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",
                                      dir=out_dir,delete=False) as file:
        json.dump(result,file,ensure_ascii=False,indent=2)
        temp=Path(file.name)
    temp.replace(out_dir/"TIMELINE_VALIDATION.json")
    lines=[]
    for page in result["pages"]:
        title=html.escape(str(page["source"]))+" page "+html.escape(str(page["page"]))
        lines.append("<tr><td>"+title+"</td><td>"+str(page["candidate_count"])+
           "</td><td>"+str(page["coherent_for_review"])+
           "</td><td>"+str(page["ambiguous_or_inconsistent"])+
           "</td><td>"+("yes" if page["needs_visual_recovery"] else "no")+"</td></tr>")
    (out_dir/"TIMELINE_VALIDATION.html").write_text(
        "<!doctype html><html><head><meta charset='utf-8'><title>Gantt Validation</title></head>"+
        "<body><h1>v0.11.3: structural checks only — not visually verified</h1>"+
        "<p>No process intervals are certified from geometry alone.</p>"+
        "<table border='1'><thead><tr><th>Slide</th><th>Proposals</th>"+
        "<th>Coherent review candidates</th><th>Ambiguous</th>"+
        "<th>Needs visual recovery</th></tr></thead><tbody>"+
        "".join(lines)+"</tbody></table></body></html>",
        encoding="utf-8")
    return {k:v for k,v in result.items() if k!="pages"}
