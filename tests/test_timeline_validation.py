import json

from course_pipeline.timeline_validation import (
    assess_timeline, score_report, validate_reconstruction_report,
)


def sample_timeline(labels=("p1","p2"),ticks=(0,4,7),intervals=None):
    if intervals is None:
        intervals=[("p1",0,4),("p2",4,7)]
    return {
        "timeline_ticks":[{"time":t} for t in ticks],
        "process_labels":[{"value":p} for p in labels],
        "interval_candidates":[{
            "process":p,"start_candidate":start,
            "end_candidate":end,"duration_candidate":end-start
        } for p,start,end in intervals],
    }


def source_table():
    return [{"column_semantics":["run_time"],"rows":[
        {"process":"p1","cells":[{"value":"4"}]},
        {"process":"p2","cells":[{"value":"3"}]},
    ]}]


def test_coherent_timeline_is_not_ground_truth():
    result=assess_timeline(sample_timeline(),source_table())
    assert result["classification"]=="coherent_candidate_for_review"
    assert result["verified_against_original_image"] is False
    assert result["usable_as_ground_truth"] is False
    assert result["runtime_checks_passed"] is True


def test_collision_is_never_approved_even_if_table_exists():
    timeline=sample_timeline(labels=("p1","p2","p3"),
        intervals=[("p1",0,4),("p2",0,4),("p3",4,7)])
    result=assess_timeline(timeline,source_table())
    assert result["classification"]=="ambiguous_or_inconsistent_candidate"
    assert result["collisions"]
    assert not next(c for c in result["checks"] if c["check"]=="single_process_per_interval")["passed"]


def test_partial_schedule_and_wrong_runtime_are_rejected():
    t=sample_timeline(labels=("p1","p2","p3"))
    assert assess_timeline(t,source_table())["classification"]=="ambiguous_or_inconsistent_candidate"
    t=sample_timeline(labels=("p1","p2"),intervals=[("p1",0,4),("p2",4,7)])
    table=[{"column_semantics":["run_time"],"rows":[
        {"process":"p1","cells":[{"value":"8"}]}]}]
    r=assess_timeline(t,table)
    assert r["runtime_checks_passed"] is False
    assert r["classification"]=="ambiguous_or_inconsistent_candidate"


def test_no_table_allows_review_not_verification():
    result=assess_timeline(sample_timeline(),[])
    assert result["classification"]=="coherent_candidate_for_review"
    assert result["runtime_checks_passed"] is None
    assert result["usable_as_ground_truth"] is False


def test_timeline_must_use_consecutive_source_ticks():
    t=sample_timeline(labels=("p1",),ticks=(0,4,7),
        intervals=[("p1",0,7)])
    result=assess_timeline(t,[])
    assert result["classification"]=="ambiguous_or_inconsistent_candidate"
    assert not next(c for c in result["checks"] if c["check"]=="intervals_use_adjacent_source_ticks")["passed"]


def test_full_report_summary_and_read_only(tmp_path):
    input_path=tmp_path/"source.json"
    original={"schema_version":"0.11.2","pages":[
        {"source":"sched.pdf","page":12,"source_sha256":"sha1","extraction_sha256":"hash1",
         "borderless_table_candidates":source_table(),
         "cross_block_gantt_candidates":[sample_timeline()]},
        {"source":"sched.pdf","page":20,"source_sha256":"sha1","extraction_sha256":"hash2",
         "borderless_table_candidates":source_table(),
         "cross_block_gantt_candidates":[sample_timeline(
             labels=("p1","p2","p3"),
             intervals=[("p1",0,4),("p2",0,4),("p3",4,7)])]},
        {"source":"sched.pdf","page":30,"source_sha256":"sha1","extraction_sha256":"hash3",
         "borderless_table_candidates":[],"cross_block_gantt_candidates":[]},
    ]}
    input_path.write_text(json.dumps(original),encoding="utf-8")
    result=validate_reconstruction_report(input_path,tmp_path/"out")
    assert result["timeline_candidates"]==2
    assert result["coherent_for_review"]==1
    assert result["ambiguous_or_inconsistent"]==1
    assert result["pages_without_candidates"]==1
    assert input_path.read_text(encoding="utf-8")==json.dumps(original)
    report=json.loads((tmp_path/"out"/"TIMELINE_VALIDATION.json").read_text(encoding="utf-8"))
    assert report["pages"][2]["needs_visual_recovery"] is True
    assert "not visually verified" in (tmp_path/"out"/"TIMELINE_VALIDATION.html").read_text()
