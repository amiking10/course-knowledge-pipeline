param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [Parameter(Mandatory=$true)] [string]$PriorExportDir,
    [string]$DatabasePath = 'data/course-v04.sqlite3',
    [string]$Output = 'data/chatgpt-export-v04'
)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python -PathType Leaf)) { throw 'Python venv missing: install package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "Source directory missing: $SourceDir" }
if (-not (Test-Path $PriorExportDir -PathType Container)) { throw "Previous export missing: $PriorExportDir" }
$SourceDir=(Resolve-Path $SourceDir).Path
$PriorExportDir=(Resolve-Path $PriorExportDir).Path
if (-not [IO.Path]::IsPathRooted($DatabasePath)) { $DatabasePath=Join-Path $projectDir $DatabasePath }
if (-not [IO.Path]::IsPathRooted($Output)) { $Output=Join-Path $projectDir $Output }
if ($PriorExportDir.TrimEnd('\') -eq $Output.TrimEnd('\')) { throw 'Use a separate v0.4 output directory to preserve prior results.' }
& $python -m course_pipeline.cli --db $DatabasePath reconcile-export $SourceDir $PriorExportDir
if ($LASTEXITCODE -ne 0) { throw 'Hash-checked import/reconciliation failed' }
& $python -m course_pipeline.cli --db $DatabasePath export $Output
if ($LASTEXITCODE -ne 0) { throw 'Markdown export failed' }
& $python -m course_pipeline.cli --db $DatabasePath build-knowledge $Output
if ($LASTEXITCODE -ne 0) { throw 'Evidence knowledge export failed' }
& $python -m course_pipeline.cli --db $DatabasePath build-index $Output
if ($LASTEXITCODE -ne 0) { throw 'Topic index failed' }
& $python -m course_pipeline.cli --db $DatabasePath quality-report $Output
if ($LASTEXITCODE -ne 0) { throw 'QA report failed' }
& $python -m course_pipeline.cli --db $DatabasePath review-queue $SourceDir (Join-Path $Output 'review')
if ($LASTEXITCODE -ne 0) { throw 'Review queue failed' }
& $python -m course_pipeline.cli --db $DatabasePath export-pdf $SourceDir (Join-Path $Output 'course_original_visuals.pdf')
if ($LASTEXITCODE -ne 0) { throw 'PDF visual bundle failed' }
Write-Host "v0.4 project export available at: $Output"
