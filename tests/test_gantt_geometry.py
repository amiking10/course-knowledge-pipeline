import pymupdf
from course_pipeline.gantt_geometry import vector_gantt_candidates


def test_vector_rectangle_with_process_and_two_aligned_ticks():
    pdf=pymupdf.open()
    p=pdf.new_page(width=500,height=350)
    p.draw_rect(pymupdf.Rect(100,110,200,155),color=(0,0,0),width=1)
    p.insert_text((139,138),"p1",fontsize=12)
    # Word centres align with rectangle edges, not text origins.
    p.insert_text((97,178),"0",fontsize=11)
    p.insert_text((197,178),"4",fontsize=11)
    found=vector_gantt_candidates(p,tolerance=9)
    assert len(found)==1
    assert found[0]["process"]=="p1"
    assert found[0]["start_time_candidate"]==0
    assert found[0]["end_time_candidate"]==4
    assert found[0]["duration_candidate"]==4
    assert found[0]["status"]=="geometrically_supported_not_semantically_verified"
    pdf.close()


def test_vector_gantt_does_not_invent_times():
    pdf=pymupdf.open()
    p=pdf.new_page(width=500,height=350)
    p.draw_rect(pymupdf.Rect(100,110,200,155))
    p.insert_text((139,138),"p1")
    p.insert_text((97,178),"0")
    assert vector_gantt_candidates(p)==[]
    p.insert_text((197,178),"0")
    assert vector_gantt_candidates(p)==[]
    pdf.close()


def test_gantt_plain_text_is_not_vector_interval():
    pdf=pymupdf.open()
    p=pdf.new_page()
    p.insert_text((100,100),"p1 p2 p3")
    p.insert_text((100,125),"0 4 8 12")
    assert vector_gantt_candidates(p)==[]
    pdf.close()
