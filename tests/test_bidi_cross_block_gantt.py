import pymupdf
from course_pipeline.cross_block_gantt import (
    cross_block_timeline_candidates,cross_check_table_timeline
)
from course_pipeline.bidi_reconstruction import fix_latin_runs_in_rtl_line, line_candidates


def test_latin_run_keeps_english_word_order_in_hebrew():
    assert fix_latin_runs_in_rtl_line(["אפקט","השיירה","effect","convoy"]) == [
        "אפקט","השיירה","convoy","effect"
    ]
    assert fix_latin_runs_in_rtl_line(["מימוש","FIFO"])==["מימוש","FIFO"]
    assert fix_latin_runs_in_rtl_line(["ללא","(","non-preemptive):"])==[
        "ללא","(","non-preemptive):"
    ]


def test_cross_block_gantt_detects_separate_pdf_blocks():
    d=pymupdf.open();p=d.new_page(width=700,height=400)
    # Separate text insertion calls become separate PDF blocks.
    for x,v in [(100,"0"),(200,"3"),(300,"6"),(400,"9")]:
        p.insert_text((x,225),v)
    for x,v in [(150,"p2"),(250,"p3"),(350,"p1")]:
        p.insert_text((x,195),v)
    found=cross_block_timeline_candidates(p)
    assert len(found)==1
    assert len(found[0]["interval_candidates"])==3
    assert found[0]["status"]=="cross_block_timeline_hypothesis"
    assert found[0]["interval_candidates"][0]["start_candidate"]==0
    assert found[0]["interval_candidates"][0]["end_candidate"]==3
    assert len(found[0]["process_labels"])==3
    d.close()


def test_cross_block_gantt_no_invention_without_valid_time_axis():
    d=pymupdf.open();p=d.new_page()
    p.insert_text((100,100),"p1 p2")
    p.insert_text((100,140),"0 8 4")
    assert cross_block_timeline_candidates(p)==[]
    d.close()


def test_cross_block_table_runtime_checks_do_not_verify_diagram():
    table=[{"column_semantics":["run_time"],
        "rows":[{"process":"p1","cells":[{"value":"3"}]},
                {"process":"p2","cells":[{"value":"4"}]}]}]
    diagrams=[{"process_labels":[{"value":"p1"}],
        "timeline_ticks":[{"time":0},{"time":3}],
        "interval_candidates":[{"process":"p1","duration_candidate":3}]}]
    results=cross_check_table_timeline(table,diagrams)
    assert any(c["type"]=="runtime_sum_agreement" and c["passed"]
               and "not_visual_confirmation" in c["status"] for c in results)


def test_real_bilingual_line_preserves_source_evidence():
    d=pymupdf.open();p=d.new_page()
    p.insert_text((70,75),"hello world")
    # Geometry contains English only; no false RTL result.
    assert line_candidates(p)==[]
    d.close()

def test_ambiguous_duplicate_process_labels_are_not_consistency_verified():
    d=pymupdf.open();p=d.new_page(width=700,height=400)
    for x,value in [(100,"0"),(200,"4"),(300,"8"),(400,"12")]:
        p.insert_text((x,225),value)
    for x,value in [(145,"p1"),(163,"p2"),(350,"p3")]:
        p.insert_text((x,195),value)
    rows=cross_block_timeline_candidates(p)
    assert len(rows)==1
    assert rows[0]["status"]=="ambiguous_timeline_hypothesis"
    assert rows[0]["ambiguous_intervals"]
    assert rows[0]["usable_for_consistency_checks"] is False
    checks=cross_check_table_timeline([],rows)
    assert any(c["type"]=="ambiguous_interval_assignment" and not c["passed"] for c in checks)
    d.close()
