"""Freeze-prep documentation and onboarding safeguards; no network required."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def test_readme_is_single_entrypoint_for_fresh_windows_user():
    text=(ROOT/"README.md").read_text(encoding="utf-8")
    for expected in (
        "git clone https://github.com/amiking10/course-knowledge-pipeline.git",
        "feature/uni-verse-course-workflow",
        ".\\scripts\\setup_windows.ps1",
        ".\\scripts\\run_pipeline.ps1",
        "-Backend hybrid -WithVisualPDF",
        "outside the Git repository",
        "UPLOAD_TO_CHATGPT",
        "INTERNAL/PROJECT_INSTRUCTIONS.md",
        "QUALITY_REPORT.html",
        "replace the previous UNI-VERSE-generated files",
    ):
        assert expected in text,expected
    assert "docs/CHATGPT_PROJECT_INSTRUCTIONS.md" not in text


def test_windows_setup_is_not_fake_success():
    setup=(ROOT/"scripts"/"setup_windows.ps1").read_text(encoding="utf-8")
    assert "py" in setup
    assert "-m venv" in setup
    assert '.[parse,inspect,retrieval,dev]' in setup
    assert "pip check" in setup
    assert "tests/test_docling_smoke.py" in setup
    assert "throw" in setup


def test_course_runner_blocks_source_inside_code_checkout():
    script=(ROOT/"scripts"/"run_pipeline.ps1").read_text(encoding="utf-8")
    assert "SourceDir must be outside the UNI-VERSE repository" in script
    assert "PROJECT_INSTRUCTIONS.md" in script
    assert "UPLOAD_TO_CHATGPT" in script
    assert "-WithAIRecovery" not in (ROOT/"README.md").read_text(encoding="utf-8").split("## Advanced options")[0]


def test_only_one_canonical_instructions_template_exists():
    assert not (ROOT/"docs"/"CHATGPT_PROJECT_INSTRUCTIONS.md").exists()
    assert (ROOT/"src"/"course_pipeline"/"project_instructions.py").exists()
    assert (ROOT/"docs"/"HISTORY.md").exists()
