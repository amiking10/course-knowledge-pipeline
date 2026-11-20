"""Strict visual geometry candidate for Gantt segments in vector PDFs.

Do not equate a nearby tick with a scheduler transition without evidence.
Only propose complete segments when rectangular block boundaries, contained
process labels, and numeric tick positions agree within a tolerance.
"""
from __future__ import annotations
import re

PROCESS_RE=re.compile(r"^[pPtT]\d+$")
TICK_RE=re.compile(r"^\d+(?:\.\d+)?$")


def vector_gantt_candidates(page, *, tolerance:float=9.0):
    if not 1<=tolerance<=20:raise ValueError("Invalid tolerance")
    texts=page.get_text("words",sort=False)
    processes=[]
    ticks=[]
    for w in texts:
        if len(w)<5:continue
        x0,y0,x1,y1,word=w[:5]
        token=str(word).strip(" ,:;()")
        entry={"text":token,"bbox":[round(v,2) for v in (x0,y0,x1,y1)],
               "x":(x0+x1)/2,"y":(y0+y1)/2}
        if PROCESS_RE.fullmatch(token):processes.append(entry)
        if TICK_RE.fullmatch(token):ticks.append(entry)
    # Only rectangles drawn as actual vector paths can certify block edges.
    boxes=[]
    for drawing in page.get_drawings():
        for path in drawing.get("items",[]):
            if not path or path[0]!="re":continue
            rect=path[1]
            if not 10<=rect.width<=page.rect.width*.95 or not 7<=rect.height<=85:
                continue
            boxes.append({"x0":float(rect.x0),"y0":float(rect.y0),
                          "x1":float(rect.x1),"y1":float(rect.y1)})
    candidates=[];seen=set()
    for box in boxes:
        inside=[p for p in processes if box["x0"]-tolerance<=p["x"]<=box["x1"]+tolerance
                and box["y0"]-tolerance<=p["y"]<=box["y1"]+tolerance]
        if len(inside)!=1:continue
        # Tick labels must appear near a rectangle edge, *outside* the block
        # and on the same horizontal tick band. A single isolated number
        # cannot establish a segment.
        edge_ticks=[t for t in ticks if box["y0"]-24<=t["y"]<=box["y1"]+35
                    and abs(t["y"]-inside[0]["y"])>=5]
        left=[t for t in edge_ticks if abs(t["x"]-box["x0"])<=tolerance]
        right=[t for t in edge_ticks if abs(t["x"]-box["x1"])<=tolerance]
        for a in left:
            for b in right:
                if abs(a["y"]-b["y"])>12:continue
                start=float(a["text"]);end=float(b["text"])
                if start>=end:continue
                key=(round(box["x0"],1),round(box["x1"],1),inside[0]["text"],start,end)
                if key in seen:continue
                seen.add(key)
                candidates.append({
                    "process":inside[0]["text"],
                    "start_time_candidate":start,
                    "end_time_candidate":end,
                    "duration_candidate":end-start,
                    "block_bbox":[round(box[k],2) for k in ("x0","y0","x1","y1")],
                    "process_label_bbox":inside[0]["bbox"],
                    "tick_left_bbox":a["bbox"],"tick_right_bbox":b["bbox"],
                    "evidence":"vector_rectangle_label_and_both_boundary_ticks",
                    "status":"geometrically_supported_not_semantically_verified",
                })
    return candidates[:100]
