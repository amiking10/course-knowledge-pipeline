param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$Db = 'data/course.sqlite3',
    [string]$Output = 'data/chatgpt-export',
    [ValidateSet('docling','pymupdf-diagnostic')] [string]$Backend = 'docling',
    [switch]$WithVisualPDF
)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Create a Python venv in .venv and install the package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "No source folder: $SourceDir" }
$SourceDir = (Resolve-Path $SourceDir).Path
if (-not [IO.Path]::IsPathRooted($Db)) { $Db = Join-Path $projectDir $Db }
if (-not [IO.Path]::IsPathRooted($Output)) { $Output = Join-Path $projectDir $Output }
& $python -m course_pipeline.cli --db $Db scan $SourceDir
if ($LASTEXITCODE -ne 0) { throw 'Source scan failed' }
& $python -m course_pipeline.cli --db $Db parse $SourceDir --backend $Backend
if ($LASTEXITCODE -ne 0) { throw 'Parsing stage failed' }
& $python -m course_pipeline.cli --db $Db export $Output
if ($LASTEXITCODE -ne 0) { throw 'Markdown export failed' }
if ($WithVisualPDF) {
    & $python -m course_pipeline.cli --db $Db export-pdf $SourceDir (Join-Path $Output 'course_original_visuals.pdf')
    if ($LASTEXITCODE -ne 0) { throw 'Visual PDF export failed' }
}
Write-Host "Export available at: $Output"
