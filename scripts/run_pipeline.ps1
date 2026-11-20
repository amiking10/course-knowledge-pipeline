param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$DatabasePath = 'data/course.sqlite3',
    [string]$Output = 'data/chatgpt-export',
    [ValidateSet('docling','hybrid','pymupdf-diagnostic')] [string]$Backend = 'hybrid',
    [switch]$WithVisualPDF
)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Create a Python venv in .venv and install the package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "No source folder: $SourceDir" }
$SourceDir = (Resolve-Path $SourceDir).Path
if (-not [IO.Path]::IsPathRooted($DatabasePath)) { $DatabasePath = Join-Path $projectDir $DatabasePath }
if (-not [IO.Path]::IsPathRooted($Output)) { $Output = Join-Path $projectDir $Output }
& $python -m course_pipeline.cli --db $DatabasePath scan $SourceDir
if ($LASTEXITCODE -ne 0) { throw 'Source scan failed' }
& $python -m course_pipeline.cli --db $DatabasePath parse $SourceDir --backend $Backend
if ($LASTEXITCODE -ne 0) { throw 'Parsing stage failed' }
& $python -m course_pipeline.cli --db $DatabasePath export $Output
if ($LASTEXITCODE -ne 0) { throw 'Markdown export failed' }
if ($WithVisualPDF) {
    & $python -m course_pipeline.cli --db $DatabasePath export-pdf $SourceDir (Join-Path $Output 'course_original_visuals.pdf')
    if ($LASTEXITCODE -ne 0) { throw 'Visual PDF export failed' }
}
& $python -m course_pipeline.cli --db $DatabasePath build-knowledge $Output
if ($LASTEXITCODE -ne 0) { throw 'Evidence knowledge export failed' }
& $python -m course_pipeline.cli --db $DatabasePath build-index $Output
if ($LASTEXITCODE -ne 0) { throw 'Topic index failed' }
& $python -m course_pipeline.cli --db $DatabasePath quality-report $Output
if ($LASTEXITCODE -ne 0) { throw 'Quality report failed' }
& $python -m course_pipeline.cli --db $DatabasePath review-queue $SourceDir (Join-Path $Output 'review')
if ($LASTEXITCODE -ne 0) { throw 'Review queue failed' }
Write-Host "Export available at: $Output"
