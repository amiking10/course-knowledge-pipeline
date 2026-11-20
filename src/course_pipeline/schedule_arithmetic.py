"""Arithmetic checks on *explicit* source-PDF scheduling formulas only.

Never synthesize numbers or promote model-generated values to ground truth.
"""
from __future__ import annotations
import re

AVERAGE=re.compile(
    r"(?i)\baverage(?:\s+waiting\s+time)?\s*=\s*"
    r"\(\s*((?:\d+(?:\.\d+)?\s*\+\s*)*\d+(?:\.\d+)?)\s*\)"
    r"\s*/\s*(\d+)\s*=\s*(\d+(?:\.\d+)?)"
)

def check_source_averages(pdf_text: str):
    results=[]
    for match in AVERAGE.finditer(pdf_text):
        terms=[float(x.strip()) for x in match.group(1).split("+")]
        count=int(match.group(2))
        asserted=float(match.group(3))
        if count==0:continue
        computed=sum(terms)/count
        results.append({
            "expression":match.group(0),
            "terms":terms,
            "denominator":count,
            "asserted_mean":asserted,
            "computed_mean":round(computed,8),
            "arithmetic_consistent":abs(computed-asserted)<=1e-6,
            "term_count_matches_denominator":len(terms)==count,
            "status":"verified_arithmetic_of_source_text_not_pdf_visual_ground_truth",
        })
    return results
