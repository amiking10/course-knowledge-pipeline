import pymupdf
from course_pipeline.process_grid import classify_process_grid


def test_process_grid_detects_four_fifo_rr_task_stacks_without_times():
    doc=pymupdf.open()
    page=doc.new_page(width=700,height=650)
    for x in (100,440):
        for offset in (0,230):
            for i in range(1,6):
                page.insert_text((x,80+offset+i*21),f"T{i}")
    grids=classify_process_grid(page)
    assert len(grids)==1
    assert len(grids[0]["stacks"])==4
    assert all(stack["task_labels"]==["T1","T2","T3","T4","T5"]
               for stack in grids[0]["stacks"])
    assert grids[0]["numeric_intervals"]==[]
    assert grids[0]["diagram_type"]=="process_grid_comparison_without_timeline"
    doc.close()


def test_process_grid_avoids_isolated_process_letters():
    doc=pymupdf.open();page=doc.new_page()
    for i in range(1,6):
        page.insert_text((60,60+i*20),f"T{i}")
    assert classify_process_grid(page)==[]
    doc.close()
