"""Smoke contracts for the optional Windows launcher (no GUI automation required)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_launcher_delegates_to_existing_pipeline():
    cmd = (ROOT / "START_UNIVERSE.cmd").read_text(encoding="utf-8")
    launcher = (ROOT / "scripts" / "launcher_windows.ps1").read_text(encoding="utf-8")
    assert "powershell.exe -NoProfile -STA -ExecutionPolicy RemoteSigned -File" in cmd
    assert "%~dp0" in cmd
    assert "run_pipeline.ps1" in launcher
    assert "& $pipeline -SourceDir $folder -Backend hybrid -WithVisualPDF" in launcher
    assert "setup_windows.ps1" in launcher
    assert "FolderBrowserDialog" in launcher


def test_launcher_is_manual_and_keeps_project_sources_separate():
    launcher = (ROOT / "scripts" / "launcher_windows.ps1").read_text(encoding="utf-8")
    assert "UPLOAD_TO_CHATGPT" in launcher
    assert "INTERNAL\\PROJECT_INSTRUCTIONS.md" in launcher
    assert "QUALITY_REPORT.html" in launcher
    assert "Choose a course folder OUTSIDE" in launcher
    assert "never uploaded automatically" in launcher
    assert "-WithAIRecovery" not in launcher
    assert "git clone" not in launcher


def test_readme_still_offers_documented_cli():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "START_UNIVERSE.cmd" in readme
    assert "Download ZIP" in readme
    assert "Windows command-line option" in readme
    assert "run_pipeline.ps1" in readme
    assert "Python 3.11" in readme
