# UNI-VERSE minimal Windows launcher. The supported parser remains run_pipeline.ps1.
# No new UI dependencies, no external services, and no hidden model/API calls.
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python = Join-Path $repo '.venv\Scripts\python.exe'
$pipeline = Join-Path $PSScriptRoot 'run_pipeline.ps1'
$setup = Join-Path $PSScriptRoot 'setup_windows.ps1'

function Pause-ForUser {
    [void](Read-Host 'Press Enter to continue')
}

function Choose-CourseFolder {
    Add-Type -AssemblyName System.Windows.Forms
    $picker = New-Object System.Windows.Forms.FolderBrowserDialog
    $picker.Description = 'Select your course folder with PDF, DOCX or PPTX files (outside UNI-VERSE)'
    $picker.ShowNewFolderButton = $true
    $suggestion = Join-Path $HOME 'Documents\University'
    if (Test-Path -LiteralPath $suggestion -PathType Container) {
        $picker.SelectedPath = $suggestion
    }
    try {
        if ($picker.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
            return $picker.SelectedPath
        }
        return $null
    } finally {
        $picker.Dispose()
    }
}

function Install-Engine {
    Write-Host ''
    Write-Host 'Installing/checking UNI-VERSE (first time may need internet and take a while)...' -ForegroundColor Cyan
    try {
        & $setup
        if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
            throw 'Python environment was not created.'
        }
        Write-Host 'Setup completed.' -ForegroundColor Green
    } catch {
        Write-Host ('Setup failed: ' + $_.Exception.Message) -ForegroundColor Red
        Write-Host 'See README.md and docs/WINDOWS_DOCLING_TROUBLESHOOTING.md.'
    }
    Pause-ForUser
}

function Prepare-Course {
    $folder = Choose-CourseFolder
    if (-not $folder) {
        Write-Host 'No folder selected. Nothing was changed.'
        Pause-ForUser
        return
    }

    # Reject accidental selection of the checkout (or a parent of it).
    $selected = [IO.Path]::GetFullPath($folder).TrimEnd([IO.Path]::DirectorySeparatorChar)
    $sourcePrefix = $selected + [IO.Path]::DirectorySeparatorChar
    $repoPrefix = $repo.TrimEnd([IO.Path]::DirectorySeparatorChar) + [IO.Path]::DirectorySeparatorChar
    if ($selected.Equals($repo, [StringComparison]::OrdinalIgnoreCase) -or
        $selected.StartsWith($repoPrefix, [StringComparison]::OrdinalIgnoreCase) -or
        $repo.StartsWith($sourcePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Write-Host 'Choose a course folder OUTSIDE the UNI-VERSE program folder.' -ForegroundColor Yellow
        Pause-ForUser
        return
    }

    # Check for obvious mistakes before installing dependencies or starting a parse.
    $docs = @(Get-ChildItem -LiteralPath $folder -Recurse -File -ErrorAction Stop |
        Where-Object { $_.Extension.ToLowerInvariant() -in @('.pdf', '.pptx', '.docx') })
    if ($docs.Count -eq 0) {
        Write-Host 'No PDF, PPTX or DOCX files were found in this folder.' -ForegroundColor Yellow
        Write-Host 'Place course documents in this folder, then select it again.'
        Pause-ForUser
        return
    }

    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        Write-Host 'UNI-VERSE is not installed yet.' -ForegroundColor Yellow
        $answer = Read-Host 'Install it now? (Y/n)'
        if ($answer -and $answer -notmatch '^[Yy]$') { return }
        try {
            & $setup
            if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'Setup did not create Python.' }
        } catch {
            Write-Host ('Setup failed: ' + $_.Exception.Message) -ForegroundColor Red
            Pause-ForUser
            return
        }
    }

    Write-Host ''
    Write-Host ("Preparing {0} document(s) from:" -f $docs.Count) -ForegroundColor Cyan
    Write-Host $folder
    Write-Host 'Original documents will stay where they are.'
    try {
        # This is the same tested pipeline used by the documented CLI workflow.
        & $pipeline -SourceDir $folder -Backend hybrid -WithVisualPDF
    } catch {
        Write-Host ('Course preparation failed: ' + $_.Exception.Message) -ForegroundColor Red
        Write-Host 'No ChatGPT files have been uploaded. Review the message above.'
        Pause-ForUser
        return
    }

    $courseName = Split-Path -Path $folder -Leaf
    $safeName = ($courseName -replace '[^\p{L}\p{Nd}_-]', '_').Trim('_')
    $courseRoot = Join-Path (Join-Path $repo 'data\courses') $safeName
    $uploadDir = Join-Path $courseRoot 'UPLOAD_TO_CHATGPT'
    $instructions = Join-Path $courseRoot 'INTERNAL\PROJECT_INSTRUCTIONS.md'
    $quality = Join-Path $courseRoot 'INTERNAL\QUALITY_REPORT.html'

    if (-not (Test-Path -LiteralPath $instructions -PathType Leaf) -or
        -not (Test-Path -LiteralPath $uploadDir -PathType Container)) {
        Write-Host 'The pipeline ended, but its expected output was not found.' -ForegroundColor Red
        Pause-ForUser
        return
    }
    Write-Host ''
    Write-Host 'COURSE READY — next steps:' -ForegroundColor Green
    Write-Host '1. Copy the text in PROJECT_INSTRUCTIONS.md to ChatGPT Project > Instructions.'
    Write-Host '2. Upload the files in the opened UPLOAD_TO_CHATGPT folder to Project Sources.'
    Write-Host '3. Review QUALITY_REPORT.html for suspicious formulas/figures.'
    Write-Host 'Project sources are never uploaded automatically.'
    try {
        Start-Process -FilePath 'explorer.exe' -ArgumentList ('"{0}"' -f $uploadDir)
        Start-Process -FilePath 'notepad.exe' -ArgumentList ('"{0}"' -f $instructions)
        if (Test-Path -LiteralPath $quality -PathType Leaf) {
            Write-Host ('Quality report: ' + $quality)
        }
    } catch {
        Write-Host ('Could not open the output windows: ' + $_.Exception.Message) -ForegroundColor Yellow
        Write-Host ('Upload directory: ' + $uploadDir)
        Write-Host ('Instructions file: ' + $instructions)
    }
    Pause-ForUser
}

if (-not (Test-Path -LiteralPath $pipeline -PathType Leaf) -or
    -not (Test-Path -LiteralPath $setup -PathType Leaf)) {
    throw 'The UNI-VERSE scripts are missing. Clone the whole repository.'
}

while ($true) {
    Clear-Host
    Write-Host '======================================' -ForegroundColor Cyan
    Write-Host '          UNI-VERSE'
    Write-Host '======================================' -ForegroundColor Cyan
    Write-Host '1. Prepare or update a course'
    Write-Host '2. Install / check UNI-VERSE'
    Write-Host '3. Exit'
    Write-Host ''
    $choice = Read-Host 'Choose 1, 2 or 3'
    switch ($choice) {
        '1' { Prepare-Course }
        '2' { Install-Engine }
        '3' { exit 0 }
        default {
            Write-Host 'Choose 1, 2 or 3.' -ForegroundColor Yellow
            Pause-ForUser
        }
    }
}
