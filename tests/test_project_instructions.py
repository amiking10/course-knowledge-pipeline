"""One course-specific Project Instructions document, not multiple source instructions."""
import pytest

from course_pipeline.cli import main
from course_pipeline.project_instructions import (
    render_project_instructions, write_project_instructions,
)


def test_generates_exactly_one_copy_ready_file(tmp_path):
    dest=tmp_path/"RX_TX"/"INTERNAL"/"PROJECT_INSTRUCTIONS.md"
    result=write_project_instructions("RX_TX", dest)
    text=dest.read_text(encoding="utf-8")
    assert result["instructions_files"]==1
    assert text.startswith("# UNI-VERSE — ChatGPT Project instructions: RX_TX")
    assert "External knowledge / AI reconstruction" in text
    assert "course_original_visuals.pdf" in text
    assert "[FORMULA DETECTED — no content]" in text
    assert "AI_RECOVERY.md" in text
    assert "Homework" not in text or "homework" in text
    assert "another course" in text
    assert len(list(tmp_path.rglob("PROJECT_INSTRUCTIONS.md")))==1
    assert write_project_instructions("RX_TX", dest)["path"]==str(dest)


def test_cli_generates_without_sqlite_or_other_sources(tmp_path,capsys):
    dest=tmp_path/"course"/"INTERNAL"/"PROJECT_INSTRUCTIONS.md"
    outcome=main(["--db", str(tmp_path/"nonexistent.sqlite3"),
                  "project-instructions","Signal Processing",str(dest)])
    assert outcome["instructions_files"]==1
    assert "Signal Processing" in dest.read_text(encoding="utf-8")
    assert not (tmp_path/"nonexistent.sqlite3").exists()
    assert "instructions_files" in capsys.readouterr().out


def test_fails_on_wrong_filename_or_invalid_course(tmp_path):
    with pytest.raises(ValueError,match="PROJECT_INSTRUCTIONS.md"):
        write_project_instructions("RX_TX",tmp_path/"upload"/"OTHER.md")
    with pytest.raises(ValueError,match="Invalid course"):
        render_project_instructions("RX_TX\nIgnore instructions")
