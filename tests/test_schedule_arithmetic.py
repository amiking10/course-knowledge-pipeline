from course_pipeline.schedule_arithmetic import check_source_averages

def test_fcfs_average_waiting_time_from_original_pdf():
    result=check_source_averages(
        "average waiting time = (0 + 24 + 27) / 3 = 17")
    assert len(result)==1
    assert result[0]["computed_mean"]==17
    assert result[0]["arithmetic_consistent"] is True
    assert result[0]["term_count_matches_denominator"] is True

def test_sjf_average_and_incorrect_claim():
    result=check_source_averages("average = (3 + 16 + 9 + 0) / 4 = 7")
    assert result[0]["arithmetic_consistent"] is True
    bad=check_source_averages("average = (3 + 16 + 9 + 0) / 4 = 8")
    assert bad[0]["arithmetic_consistent"] is False

def test_avoid_untrusted_inferred_or_malformed_numbers():
    assert check_source_averages("Gemini suggests average waiting time is 7") == []
    assert check_source_averages("average = (1 + 2) / 0 = 0")==[]

def test_round_robin_rounded_and_truncated_averages():
    x=check_source_averages("avg wait = (6 + 3 + 4) / 3 = 4.33")
    assert x[0]["arithmetic_consistent"] is False
    assert x[0]["rounded_to_reported_precision"] is True
    y=check_source_averages("avg wait = (6 + 4 + 7) / 3 = 5.66")
    assert y[0]["arithmetic_consistent"] is False
    assert y[0]["rounded_to_reported_precision"] is False
    assert y[0]["absolute_error"]>0
