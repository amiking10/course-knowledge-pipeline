param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$OutputRoot = 'data/courses',
    [string]$CourseName,
    [string]$DatabasePath,
    [string]$Output,
    [ValidateSet('docling','hybrid','docling-no-ocr','hybrid-no-ocr','docling-formula','hybrid-formula','pymupdf-diagnostic')] [string]$Backend = 'hybrid',
    [switch]$WithVisualPDF,
    [switch]$SkipContentAudit,
    [switch]$WithAIRecovery,
    [ValidateRange(1,100)] [int]$AIRecoveryLimit = 19,
    [ValidateRange(1,100)] [int]$AIRecoveryMaxRequests = 19,
    [string]$AIRecoveryModel = 'gemini-2.5-flash'
)
$ErrorActionPreference = 'Stop'
$projectDir = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $python -PathType Leaf)) { throw 'Create .venv and install the UNI-VERSE package first.' }
if (-not (Test-Path $SourceDir -PathType Container)) { throw "Source directory not found: $SourceDir" }
$SourceDir = (Resolve-Path $SourceDir).Path
# Source originals must live outside this checkout. This avoids accidentally
# indexing cached exports, cloned sample files or private content into Git.
$projectPrefix = $projectDir.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
if ($SourceDir.Equals($projectDir, [StringComparison]::OrdinalIgnoreCase) -or
    $SourceDir.StartsWith($projectPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "SourceDir must be outside the UNI-VERSE repository. Put originals in Documents\\University\\COURSE (not in this Git checkout)."
}
if (-not $CourseName) { $CourseName = Split-Path $SourceDir -Leaf }
$safeName = ($CourseName -replace '[^\p{L}\p{Nd}_-]', '_').Trim('_')
if (-not $safeName -or $safeName -eq '.' -or $safeName -eq '..') { throw 'Provide a valid -CourseName.' }
if (-not [IO.Path]::IsPathRooted($OutputRoot)) { $OutputRoot = Join-Path $projectDir $OutputRoot }
$courseRoot = Join-Path $OutputRoot $safeName
# The legacy -Output override still selects the course root, never the public upload directory.
if ($Output) {
    if (-not [IO.Path]::IsPathRooted($Output)) { $Output = Join-Path $projectDir $Output }
    $courseRoot = $Output
}
$courseRoot = [IO.Path]::GetFullPath($courseRoot)
$uploadDir = Join-Path $courseRoot 'UPLOAD_TO_CHATGPT'
$internalDir = Join-Path $courseRoot 'INTERNAL'
if (-not $DatabasePath) { $DatabasePath = Join-Path $internalDir 'course.sqlite3' }
elseif (-not [IO.Path]::IsPathRooted($DatabasePath)) { $DatabasePath = Join-Path $projectDir $DatabasePath }
$DatabasePath = [IO.Path]::GetFullPath($DatabasePath)
New-Item -ItemType Directory -Force -Path $uploadDir, $internalDir | Out-Null
New-Item -ItemType Directory -Force -Path (Split-Path $DatabasePath -Parent) | Out-Null
Write-Host "UNI-VERSE | Course: $CourseName"
Write-Host "Source: $SourceDir"
Write-Host "Course root: $courseRoot"
Write-Host "ChatGPT upload folder: $uploadDir"
Write-Host "Private diagnostics: $internalDir"
Write-Host "Local SQLite (do not upload): $DatabasePath"
if ($WithAIRecovery -and -not $env:GEMINI_API_KEY) {
    throw 'AI recovery is opt-in and requires GEMINI_API_KEY. No course files were sent.'
}
# Drop old optional AI material before any verification or ordinary refresh.
$oldAI = Join-Path $uploadDir 'AI_RECOVERY.md'
if (Test-Path -LiteralPath $oldAI) { Remove-Item -LiteralPath $oldAI -Force }
if ($Backend -match 'no-ocr') {
    Write-Warning 'OCR DISABLED: scanned text and text embedded in images may be missing. Compare exported pages against originals before uploading.'
}
function Run-Stage {
    param([int]$Start, [int]$End, [string]$Name, [string[]]$Command)
    Write-Host ('[{0,3}%] {1}...' -f $Start, $Name)
    Write-Progress -Activity 'UNI-VERSE course preparation' -Status $Name -PercentComplete $Start
    $stageLogs = Join-Path $internalDir 'stage_reports'
    New-Item -ItemType Directory -Force -Path $stageLogs | Out-Null
    $slug = (($Name.ToLowerInvariant() -replace '[^a-z0-9]+', '_').Trim('_'))
    $detail = Join-Path $stageLogs ($slug + '.json')
    $commandArgs = @('-m','course_pipeline.cli','--brief','--report-file',$detail) + @($Command | Select-Object -Skip 2)
    & $python @commandArgs
    if ($LASTEXITCODE -ne 0) { throw "UNI-VERSE stage failed: $Name (exit code $LASTEXITCODE)" }
    Write-Host ('[{0,3}%] {1} complete' -f $End, $Name)
    Write-Progress -Activity 'UNI-VERSE course preparation' -Status "$Name complete" -PercentComplete $End
}
try {
    Run-Stage 0 10 'Scanning source files' @('-m','course_pipeline.cli','--db',$DatabasePath,'scan',$SourceDir)
    Run-Stage 10 70 'Parsing changed or new files (see per-document progress below)' @('-m','course_pipeline.cli','--db',$DatabasePath,'parse',$SourceDir,'--backend',$Backend,'--progress')
    Run-Stage 70 77 'Exporting page-linked Markdown' @('-m','course_pipeline.cli','--db',$DatabasePath,'export',$uploadDir)
    if ($WithVisualPDF) {
        Run-Stage 77 84 'Building original visual PDF' @('-m','course_pipeline.cli','--db',$DatabasePath,'export-pdf',$SourceDir,(Join-Path $uploadDir 'course_original_visuals.pdf'))
    } else {
        # Avoid retaining an outdated visual archive from a previous run.
        foreach ($name in @('course_original_visuals.pdf','course_original_visuals.manifest.json')) {
            $old = Join-Path $uploadDir $name
            if (Test-Path $old) { Remove-Item -LiteralPath $old -Force }
        }
        Write-Host '[ 84%] Visual PDF not requested; use -WithVisualPDF to preserve diagrams.'
    }
    Run-Stage 84 89 'Building course knowledge evidence' @('-m','course_pipeline.cli','--db',$DatabasePath,'build-knowledge',$internalDir)
    Run-Stage 89 92 'Building course topic index' @('-m','course_pipeline.cli','--db',$DatabasePath,'build-index',$internalDir)
    # Only human-readable study material belongs in the ChatGPT upload directory.
    Copy-Item -LiteralPath (Join-Path $internalDir 'COURSE_KNOWLEDGE.md') -Destination (Join-Path $uploadDir 'COURSE_KNOWLEDGE.md') -Force
    Copy-Item -LiteralPath (Join-Path $internalDir 'COURSE_INDEX.md') -Destination (Join-Path $uploadDir 'COURSE_INDEX.md') -Force
    Run-Stage 92 92 'Preparing one ChatGPT Project instructions file' @('-m','course_pipeline.cli','project-instructions',$CourseName,(Join-Path $internalDir 'PROJECT_INSTRUCTIONS.md'))
    Run-Stage 92 95 'Generating quality report' @('-m','course_pipeline.cli','--db',$DatabasePath,'quality-report',$internalDir)
    Run-Stage 95 97 'Building review queue' @('-m','course_pipeline.cli','--db',$DatabasePath,'review-queue',$SourceDir,(Join-Path $internalDir 'review'))
    $auditGenerated = $false
    if (-not $SkipContentAudit -and (Get-ChildItem -LiteralPath $SourceDir -Recurse -File -Filter '*.pdf' | Select-Object -First 1)) {
        Run-Stage 97 99 'Preparing sampled visual content audit' @('-m','course_pipeline.cli','--db',$DatabasePath,'review-gold-sample',$SourceDir,(Join-Path $internalDir 'content_audit'))
        $auditGenerated = $true
        Write-Host "Review original pages versus extracted text: $(Join-Path (Join-Path $internalDir 'content_audit') 'REVIEW.html')"
        Write-Host "Portable content audit ZIP: $(Join-Path (Join-Path $internalDir 'content_audit') 'CONTENT_AUDIT.zip')"
    } else {
        Write-Host '[ 99%] Sampled PDF content audit skipped (no PDFs or -SkipContentAudit).'
    }
    $verifyArgs = @('-m','course_pipeline.cli','--db',$DatabasePath,'verify-export',$uploadDir,'--source-dir',$SourceDir,'--quality-report',(Join-Path $internalDir 'QUALITY_REPORT.json'))
    if ($WithVisualPDF) { $verifyArgs += '--require-visuals' }
    $verifyArgs += '--strict-indexes'
    if ($WithAIRecovery) {
        Write-Warning "AI RECOVERY: up to $AIRecoveryMaxRequests original PDF pages and extraction text may be sent to Gemini. Inferences are labelled and NOT verified."
        $aiDir = Join-Path $internalDir 'ai_recovery'
        Run-Stage 99 99 'Generating AI recovery candidates' @('-m','course_pipeline.cli','--db',$DatabasePath,'ai-recovery',$SourceDir,$aiDir,'--limit',([string]$AIRecoveryLimit),'--max-requests',([string]$AIRecoveryMaxRequests),'--model',$AIRecoveryModel,'--live')
        Copy-Item -LiteralPath (Join-Path $aiDir 'AI_RECOVERY.md') -Destination $oldAI -Force
    }
    Run-Stage 99 100 'Verifying export integrity' $verifyArgs
    $userGuide = @(
        '# UNI-VERSE — Course refresh and ChatGPT upload',
        '',
        "Course source folder: ``$SourceDir``",
        '',
        '## Add new lecture files',
        '1. Copy new PDF/PPTX/DOCX files into the course source folder; nested folders are supported.',
        '2. From the UNI-VERSE repository, rerun the same PowerShell pipeline command for this course.',
        '3. New/changed documents are parsed and unchanged documents reuse the indexed extraction.',
        '4. Review INTERNAL/QUALITY_REPORT.html for extraction warnings.',
        '5. Open INTERNAL/PROJECT_INSTRUCTIONS.md and paste its entire contents into ChatGPT Project > Instructions (not Project sources).',
        '6. Replace the old course bundles/indexes and visual PDF in the matching ChatGPT Project.',
        '',
        '## Upload into ChatGPT Projects',
        '- Open UPLOAD_TO_CHATGPT and select the files there; it contains no SQLite database or review reports.',
        '- Copy the ONE INTERNAL/PROJECT_INSTRUCTIONS.md into the ChatGPT Project Instructions field; do not upload it as a source file.',
        '- Upload course_original_visuals.pdf and optionally course_original_visuals.manifest.json when available.',
        '- Keep INTERNAL private. It contains course.sqlite3, QA reports, review items and this workflow guide.',
        '- ChatGPT Project uploads are static: updating the local folder does not update the Project automatically.',
        '- Replacing source bundles is important because numbering can change when lectures are added.',
        '',
        'Passing export verification checks file integrity, not extracted content correctness.'
    )
    Set-Content -LiteralPath (Join-Path $internalDir 'COURSE_WORKFLOW.md') -Value $userGuide -Encoding utf8
    Write-Host ''
    Write-Host '============================================================'
    Write-Host '[100%] COURSE PACKAGE READY' -ForegroundColor Green
    Write-Host "Course: $CourseName"
    $sourceCount = @(Get-ChildItem -LiteralPath $SourceDir -Recurse -File | Where-Object { $_.Extension.ToLowerInvariant() -in @('.pdf','.docx','.pptx') }).Count
    $bundleCount = @(Get-ChildItem -LiteralPath $uploadDir -Filter 'course_sources_*.md' -File).Count
    Write-Host "Source documents: $sourceCount | Markdown bundles: $bundleCount"
    Write-Host "Upload files FROM: $uploadDir"
    Write-Host "Review quality report: $(Join-Path $internalDir 'QUALITY_REPORT.html')"
    Write-Host "COPY INTO PROJECT INSTRUCTIONS: $(Join-Path $internalDir 'PROJECT_INSTRUCTIONS.md')"
    if ($auditGenerated) { Write-Host "Human content audit: $(Join-Path (Join-Path $internalDir 'content_audit') 'REVIEW.html')" }
    Write-Host "Detailed stage logs: $(Join-Path $internalDir 'stage_reports')"
    if ($WithAIRecovery) { Write-Host "AI evidence report: $(Join-Path (Join-Path $internalDir 'ai_recovery') 'AI_RECOVERY.json')" }
    Write-Host 'NEXT: Review the QA report, then replace the OLD files in the same ChatGPT Project.'
    Write-Host 'Do not upload the INTERNAL directory. Automatic Project synchronization is not available.'
    Write-Host '============================================================'
} finally {
    Write-Progress -Activity 'UNI-VERSE course preparation' -Completed
}
