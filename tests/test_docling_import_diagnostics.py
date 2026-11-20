"""Docling import failures must preserve actionable information and fail closed."""
import builtins
import pytest

from course_pipeline.parsers import _docling_converter


def _fail_import(monkeypatch, error):
    original = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "docling.document_converter":
            raise error
        return original(name, *args, **kwargs)

    _docling_converter.cache_clear()
    monkeypatch.setattr(builtins, "__import__", fake_import)


def test_missing_docling_shows_install_hint(monkeypatch):
    _fail_import(monkeypatch, ModuleNotFoundError(
        "No module named 'docling'", name="docling"))
    with pytest.raises(RuntimeError, match="Docling is not installed"):
        _docling_converter()
    _docling_converter.cache_clear()


def test_missing_nested_dependency_not_misreported_as_docling(monkeypatch):
    _fail_import(monkeypatch, ModuleNotFoundError(
        "No module named 'unknown_nested'", name="unknown_nested"))
    with pytest.raises(RuntimeError, match="unknown_nested"):
        _docling_converter()
    _docling_converter.cache_clear()


def test_windows_app_control_pandas_dll_is_diagnosed(monkeypatch):
    _fail_import(monkeypatch, ImportError(
        "DLL load failed while importing ccalendar: "
        "An Application Control policy has blocked this file."))
    with pytest.raises(RuntimeError, match="Windows Application Control blocked"):
        _docling_converter()
    _docling_converter.cache_clear()


def test_other_import_errors_are_not_silent_fallbacks(monkeypatch):
    _fail_import(monkeypatch, ImportError("binary ABI version mismatch"))
    with pytest.raises(RuntimeError, match="dependency could not be imported"):
        _docling_converter()
    _docling_converter.cache_clear()
