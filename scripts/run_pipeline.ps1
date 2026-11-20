param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$Db = 'data/course.sqlite3',
    [string]$Output = 'data/chatgpt-export',
    [ValidateSet('docling','pymupdf-diagnostic')] [string]$Backend = 'docling'
)
$ErrorActionPreference = 'Stop'
$python = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Create a Python venv in .venv and install the package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "No source folder: $SourceDir" }
& $python -m course_pipeline.cli --db $Db scan $SourceDir
if ($LASTEXITCODE -ne 0) { throw 'Source scan failed' }
& $python -m course_pipeline.cli --db $Db parse $SourceDir --backend $Backend
if ($LASTEXITCODE -ne 0) { throw 'Parsing stage failed' }
& $python -m course_pipeline.cli --db $Db export $Output
if ($LASTEXITCODE -ne 0) { throw 'Export failed' }
Write-Host "Export available at: $Output"
