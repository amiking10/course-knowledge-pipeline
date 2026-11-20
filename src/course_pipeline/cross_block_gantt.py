"""v0.11.2: cross-block PDF timeline *candidates* with explicit ambiguity.

Unlike text-line based methods, collect nearby word rows across unrelated
PDF drawing/text blocks. A process label between time ticks supports a
hypothesis, NOT a verified Gantt segment; source geometry is retained.
"""
from __future__ import annotations
import re

PROCESS=re.compile(r"(?i)^[pt]\d+$")
NUMBER=re.compile(r"^\d+(?:\.\d+)?$")


def _collect_rows(page, *, y_tolerance=7.0):
    words=[]
    for w in page.get_text("words",sort=False):
        if len(w)<5:continue
        x0,y0,x1,y1,txt=w[:5]
        token=str(txt).strip(" ,:;()[]")
        if not token:continue
        words.append({"text":token,"bbox":[round(float(n),2) for n in (x0,y0,x1,y1)],
                      "x":(x0+x1)*.5,"y":(y0+y1)*.5})
    # Cluster by Y in reading order without using arbitrary PDF block IDs.
    words.sort(key=lambda w:(w["y"],w["x"]))
    groups=[]
    for w in words:
        best=None
        for row in groups:
            if abs(row["y"]-w["y"])<=y_tolerance:
                best=row;break
        if best is None:
            best={"y":w["y"],"words":[]}
            groups.append(best)
        best["words"].append(w)
    for group in groups:group["words"].sort(key=lambda w:w["x"])
    return groups


def cross_block_timeline_candidates(page, *, gap=75.0, tolerance=7.0):
    if not 12<=gap<=150:raise ValueError("gap must be between 12 and 150")
    if not 2<=tolerance<=15:raise ValueError("tolerance must be between 2 and 15")
    rows=_collect_rows(page,y_tolerance=tolerance)
    times=[];labels=[]
    for row in rows:
        numbers=[w for w in row["words"] if NUMBER.fullmatch(w["text"])]
        procs=[w for w in row["words"] if PROCESS.fullmatch(w["text"])]
        if len(numbers)>=3:
            nums=[float(w["text"]) for w in numbers]
            # Left to right PDF placement; a nonmonotone sequence isn't time.
            if all(a<b for a,b in zip(nums,nums[1:])):
                times.append({"y":row["y"],"words":numbers})
        if len(procs)>=2:labels.append({"y":row["y"],"words":procs})
    candidates=[]
    used=set()
    for timeline in times:
        left=timeline["words"][0]["x"];right=timeline["words"][-1]["x"]
        close=[]
        for row in labels:
            dist=abs(timeline["y"]-row["y"])
            if not 6<=dist<=gap:continue
            aligned=[w for w in row["words"] if left-25<=w["x"]<=right+25]
            if len(aligned)<2:continue
            # Most scheduling timelines place labels just above tick labels.
            close.append((dist,row,aligned))
        if not close:continue
        close.sort(key=lambda v:v[0])
        dist,label_row,procs=close[0]
        key=(round(timeline["y"]),round(label_row["y"]))
        if key in used:continue
        used.add(key)
        intervals=[]
        for p in procs:
            plausible=[]
            for a,b in zip(timeline["words"],timeline["words"][1:]):
                if a["x"]<=p["x"]<=b["x"]:
                    plausible.append((a,b))
            if len(plausible)!=1:continue
            a,b=plausible[0]
            intervals.append({"process":p["text"],
                "start_candidate":float(a["text"]),
                "end_candidate":float(b["text"]),
                "duration_candidate":float(b["text"])-float(a["text"]),
                "label_bbox":p["bbox"],"left_tick_bbox":a["bbox"],
                "right_tick_bbox":b["bbox"],
                "status":"text_geometry_candidate_not_verified"})
        # Many adjacent process intervals require visually verified block edges.
        candidates.append({
            "timeline_ticks":[{"time":float(t["text"]),"bbox":t["bbox"]}
                              for t in timeline["words"]],
            "process_labels":[{"value":p["text"],"bbox":p["bbox"]} for p in procs],
            "interval_candidates":intervals,
            "line_gap_points":round(dist,2),
            "status":"cross_block_timeline_hypothesis",
            "warning":"Labels and tick positions are suggestive only; graphical boundaries not checked.",
        })
    return candidates[:40]


def cross_check_table_timeline(table_candidates,timeline_candidates):
    """Only deterministic consistency checks; no auto-approval of timelines."""
    checks=[]
    for candidate in timeline_candidates:
        intervals=candidate["interval_candidates"]
        if len(intervals)!=len(candidate["process_labels"]):
            checks.append({"type":"interval_coverage","passed":False,
                "reason":"Not every process label maps uniquely to adjacent ticks"})
            continue
        ticks=candidate["timeline_ticks"]
        checks.append({"type":"monotonic_timeline","passed":all(
            b["time"]>a["time"] for a,b in zip(ticks,ticks[1:]))})
        for table in table_candidates:
            semantics=table.get("column_semantics",[])
            if semantics.count("run_time")!=1:continue
            idx=semantics.index("run_time")
            runtime={}
            for row in table["rows"]:
                cells=row.get("cells",[])
                if idx<len(cells) and cells[idx] is not None:
                    try:runtime[row["process"].lower()]=float(cells[idx]["value"])
                    except (TypeError,ValueError):pass
            observed={}
            for iv in intervals:
                key=iv["process"].lower()
                observed[key]=observed.get(key,0)+iv["duration_candidate"]
            for proc,value in observed.items():
                if proc not in runtime:continue
                checks.append({
                    "type":"runtime_sum_agreement",
                    "process":proc,"table_runtime":runtime[proc],
                    "candidate_total":value,
                    "passed":abs(runtime[proc]-value)<=1e-8,
                    "status":"consistency_only_not_visual_confirmation",
                })
    return checks
