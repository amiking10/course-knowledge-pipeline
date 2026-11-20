param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$OutputRoot = 'data/courses',
    [string]$CourseName,
    [string]$DatabasePath,
    [string]$Output,
    [ValidateSet('docling','hybrid','docling-formula','hybrid-formula','pymupdf-diagnostic')] [string]$Backend = 'hybrid',
    [switch]$WithVisualPDF
)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python -PathType Leaf)) { throw 'Create .venv and install the UNI-VERSE package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "Source directory not found: $SourceDir" }
$SourceDir = (Resolve-Path $SourceDir).Path
if (-not $CourseName) { $CourseName = Split-Path $SourceDir -Leaf }
$safeName = ($CourseName -replace '[^\p{L}\p{Nd}_-]', '_').Trim('_')
if (-not $safeName -or $safeName -eq '.' -or $safeName -eq '..') { throw 'Provide a valid -CourseName.' }
if (-not [IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot = Join-Path $projectDir $OutputRoot }
$courseRoot = Join-Path $OutputRoot $safeName
if (-not $Output) { $Output = $courseRoot }
elseif (-not [IO.Path]::IsPathRooted($Output)) { $Output = Join-Path $projectDir $Output }
if (-not $DatabasePath) { $DatabasePath = Join-Path $courseRoot 'course.sqlite3' }
elseif (-not [IO.Path]::IsPathRooted($DatabasePath)) { $DatabasePath = Join-Path $projectDir $DatabasePath }
$Output = [IO.Path]::GetFullPath($Output)
$DatabasePath = [IO.Path]::GetFullPath($DatabasePath)
New-Item -ItemType Directory -Force -Path $Output | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $DatabasePath -Parent) | Out-Null
Write-Host "UNI-VERSE | Course: $CourseName"
Write-Host "Source: $SourceDir"
Write-Host "Output folder: $Output"
Write-Host "Local SQLite (do not upload): $DatabasePath"
function Run-Stage {
    param([int]$Start, [int]$End, [string]$Name, [string[]]$Command)
    Write-Host ('[{0,3}%] {1}...' -f $Start, $Name)
    Write-Progress -Activity 'UNI-VERSE course preparation' -Status $Name -PercentComplete $Start
    & $python @Command
    if ($LASTEXITCODE -ne 0) { throw "UNI-VERSE stage failed: $Name (exit code $LASTEXITCODE)" }
    Write-Host ('[{0,3}%] {1} complete' -f $End, $Name)
    Write-Progress -Activity 'UNI-VERSE course preparation' -Status "$Name complete" -PercentComplete $End
}
try {
    Run-Stage 0 10 'Scanning source files' @('-m','course_pipeline.cli','--db',$DatabasePath,'scan',$SourceDir)
    Run-Stage 10 70 'Parsing changed or new files (see per-document progress below)' @('-m','course_pipeline.cli','--db',$DatabasePath,'parse',$SourceDir,'--backend',$Backend,'--progress')
    Run-Stage 70 77 'Exporting page-linked Markdown' @('-m','course_pipeline.cli','--db',$DatabasePath,'export',$Output)
    if ($WithVisualPDF) {
        Run-Stage 77 84 'Building original visual PDF' @('-m','course_pipeline.cli','--db',$DatabasePath,'export-pdf',$SourceDir,(Join-Path $Output 'course_original_visuals.pdf'))
    } else {
        # Avoid retaining an outdated visual archive from a previous run.
        foreach ($name in @('course_original_visuals.pdf','course_original_visuals.manifest.json')) {
            $old = Join-Path $Output $name
            if (Test-Path $old) { Remove-Item -LiteralPath $old -Force }
        }
        Write-Host '[ 84%] Visual PDF not requested; use -WithVisualPDF to preserve diagrams.'
    }
    Run-Stage 84 89 'Building course knowledge evidence' @('-m','course_pipeline.cli','--db',$DatabasePath,'build-knowledge',$Output)
    Run-Stage 89 92 'Building course topic index' @('-m','course_pipeline.cli','--db',$DatabasePath,'build-index',$Output)
    Run-Stage 92 95 'Generating quality report' @('-m','course_pipeline.cli','--db',$DatabasePath,'quality-report',$Output)
    Run-Stage 95 98 'Building review queue' @('-m','course_pipeline.cli','--db',$DatabasePath,'review-queue',$SourceDir,(Join-Path $Output 'review'))
    $verifyArgs = @('-m','course_pipeline.cli','--db',$DatabasePath,'verify-export',$Output,'--source-dir',$SourceDir)
    if ($WithVisualPDF) { $verifyArgs += '--require-visuals' }
    Run-Stage 98 100 'Verifying export integrity' $verifyArgs
    Write-Host '[100%] UNI-VERSE export complete.'
    Write-Host "Upload Markdown bundles, INDEX.md, COURSE_INDEX.md and the original visual PDF from: $Output"
    Write-Host 'Do not upload course.sqlite3; review QUALITY_REPORT.html before relying on answers.'
} finally {
    Write-Progress -Activity 'UNI-VERSE course preparation' -Completed
}
