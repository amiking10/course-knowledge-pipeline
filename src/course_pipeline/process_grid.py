"""Recognize non-timeline scheduling comparison diagrams without inventing times.

Some Operating Systems slides compare FIFO and RR as process-by-process
visual grids with no explicit numeric timeline. Those should be classified as
non-numeric diagrams rather than falsely reconstructed as a Gantt chart.
"""
from __future__ import annotations
import re
from collections import defaultdict

TASK=re.compile(r"(?i)^T\d+$")


def classify_process_grid(page, *, x_tolerance=25.0, y_gap=45.0):
    if not 5<=x_tolerance<=50 or not 10<=y_gap<=100:
        raise ValueError("Invalid process-grid geometry tolerance")
    word_rows=page.get_text("words",sort=False)
    tokens=[]
    for word in word_rows:
        if len(word)<5:continue
        x0,y0,x1,y1,text=word[:5]
        text=str(text).strip(" \t,:;()")
        if TASK.fullmatch(text):
            tokens.append({"label":text.upper(),"x":(x0+x1)/2,
                 "y":(y0+y1)/2,"bbox":[round(float(v),2) for v in (x0,y0,x1,y1)]})
    if len(tokens)<10:return []
    # Form horizontal columns, then separate vertical label stacks by gaps.
    columns=[]
    for token in sorted(tokens,key=lambda t:t["x"]):
        matching=next((col for col in columns
             if abs(col["x"]-token["x"])<=x_tolerance),None)
        if matching is None:
            matching={"x":token["x"],"tokens":[]}
            columns.append(matching)
        matching["tokens"].append(token)
    stacks=[]
    for column in columns:
        sorted_rows=sorted(column["tokens"],key=lambda t:t["y"])
        groups=[]
        for token in sorted_rows:
            if not groups or token["y"]-groups[-1][-1]["y"]>y_gap:
                groups.append([])
            groups[-1].append(token)
        for group in groups:
            labels=[x["label"] for x in group]
            # Require a substantial ordered task stack, not isolated T labels.
            numeric=[int(t[1:]) for t in labels]
            if len(numeric)<3 or numeric!=sorted(set(numeric)):
                continue
            stacks.append({"task_labels":labels,
                "task_label_boxes":[t["bbox"] for t in group],
                "approx_x":round(column["x"],2),
                "approx_y":round(sum(t["y"] for t in group)/len(group),2),
                "status":"task_grid_labels_no_time_axis"})
    if len(stacks)<2:return []
    return [{
        "diagram_type":"process_grid_comparison_without_timeline",
        "stacks":sorted(stacks,key=lambda s:(s["approx_y"],s["approx_x"])),
        "numeric_intervals":[],
        "status":"source_geometry_classification_not_visual_ground_truth",
        "warning":"These rows do not establish execution durations or completion times.",
    }]
