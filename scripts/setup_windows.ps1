# UNI-VERSE first-time Windows setup. Run from a cloned repository:
#   .\scripts\setup_windows.ps1
param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $root
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    throw "Python launcher 'py' was not found. Install Python 3.11 (64-bit) from https://www.python.org/downloads/windows/ with the Python launcher, reopen PowerShell and retry."
}
$version = $null
foreach ($candidate in @('3.11','3.12')) {
    & py "-$candidate" -c 'import sys; assert sys.version_info[:2] in ((3, 11),(3,12))' *> $null
    if ($LASTEXITCODE -eq 0) { $version = $candidate; break }
}
if (-not $version) {
    throw 'Install 64-bit Python 3.11 or 3.12 with the Python launcher, then retry.'
}
$python = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
    Write-Host "[1/4] Creating .venv using Python $version..."
    & py "-$version" -m venv (Join-Path $root '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Could not create virtual environment.' }
} else {
    Write-Host '[1/4] Reusing .venv.'
}
Write-Host '[2/4] Installing course parser dependencies (first run may download large packages)...'
& $python -m pip install -e '.[parse,inspect,retrieval,dev]'
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. See docs/WINDOWS_DOCLING_TROUBLESHOOTING.md.' }
Write-Host '[3/4] Checking installed package consistency and Docling import...'
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Python dependency conflict detected.' }
# No nested quotes inside -c: Windows PowerShell 5.1 may strip them when invoking python.exe.
& $python -c 'import docling.document_converter'
if ($LASTEXITCODE -eq 0) { Write-Host 'Docling import OK' }
if ($LASTEXITCODE -ne 0) { throw 'Docling import failed. See docs/WINDOWS_DOCLING_TROUBLESHOOTING.md.' }
if (-not $SkipTests) {
    Write-Host '[4/4] Running parser smoke test (may download model weights on first run)...'
    & $python -m pytest -q tests/test_docling_smoke.py
    if ($LASTEXITCODE -ne 0) { throw 'Docling smoke test failed; setup is not validated.' }
} else {
    Write-Warning '[4/4] Tests skipped by request. Setup is NOT validated.'
}
Write-Host ''
Write-Host 'UNI-VERSE local setup finished.' -ForegroundColor Green
Write-Host 'NEXT: Put PDFs in a folder OUTSIDE this Git repository, e.g. Documents\University\MyCourse.'
Write-Host 'Then run: .\scripts\run_pipeline.ps1 -SourceDir "C:\FULL\PATH\TO\MyCourse" -Backend hybrid -WithVisualPDF'
Write-Host 'See README.md for source upload and ChatGPT Project Instructions steps.'
