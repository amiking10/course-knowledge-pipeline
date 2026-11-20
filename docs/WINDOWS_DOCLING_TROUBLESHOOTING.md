# Windows: Docling native DLL blocked by Application Control

## Symptoms

An installed Docling can fail during a transitive pandas import:

```text
docling.document_converter -> docling_core -> pandas
ImportError: DLL load failed while importing ccalendar:
An Application Control policy has blocked this file.
```

This is **not** proof that Docling is missing. Its import reaches pandas and Windows blocks the native extension. UNI-VERSE refuses to silently switch to an untrusted fallback.

## Confirm the failure

From the project root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip show docling pandas
.\.venv\Scripts\python.exe -c "import pandas; print(pandas.__version__)"
.\.venv\Scripts\python.exe -c "from docling.document_converter import DocumentConverter; print('Docling import OK')"
```

If importing pandas independently triggers the same Windows policy error, the failure is outside UNI-VERSE. Have your device administrator inspect the relevant Windows event log and approve an appropriate signed binary/publisher under organizational policy.

Useful diagnostic event logs:

- Applications and Services Logs → Microsoft → Windows → CodeIntegrity → Operational
- Applications and Services Logs → Microsoft → Windows → AppLocker → EXE and DLL

Do **not** disable App Control, introduce broad application-control exceptions, or copy DLLs to unapproved locations. Reinstalling packages may not fix an organizational policy block.

## Partial test while investigating (not a release pass)

```powershell
.\.venv\Scripts\python.exe -m pytest -q --ignore=tests/test_docling_smoke.py
```

This isolates unrelated tests but does **not** establish that end-to-end hybrid parsing works. Full release sign-off requires the real Docling smoke test to pass:

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests/test_docling_smoke.py
```

If a device policy prohibits required native packages, run in an administrator-approved development environment rather than bypassing the policy. See README.md and RELEASE_CHECKLIST.md for the supported product workflow.