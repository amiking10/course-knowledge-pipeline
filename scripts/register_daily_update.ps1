# Optional Windows Task Scheduler registration; executes only when run explicitly.
param(
    [Parameter(Mandatory=$true)] [string]$SourceDir,
    [string]$At = '19:00',
    [string]$TaskName = 'CourseKnowledgePipeline-Update',
    [switch]$WithVisualPDF
)
$ErrorActionPreference='Stop'
$scriptPath = (Resolve-Path (Join-Path $PSScriptRoot 'run_pipeline.ps1')).Path
if (-not (Test-Path $SourceDir -PathType Container)) { throw "No source folder: $SourceDir" }
$sourcePath = (Resolve-Path $SourceDir).Path
try { $start = [datetime]::ParseExact($At,'HH:mm',[Globalization.CultureInfo]::InvariantCulture) }
catch { throw 'Use 24-hour HH:mm format, for example 19:00.' }
# EncodedCommand protects paths containing spaces/Unicode and avoids fragile quoting.
$invoke = "& '$($scriptPath.Replace("'", "''"))' -SourceDir '$($sourcePath.Replace("'", "''"))' -Backend docling"
if ($WithVisualPDF) { $invoke += ' -WithVisualPDF' }
$encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($invoke))
$action = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument "-NoProfile -NonInteractive -EncodedCommand $encoded"
$trigger = New-ScheduledTaskTrigger -Daily -At $start
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Description 'Daily incremental Docling course update' -Force | Out-Null
Write-Host "Registered daily task '$TaskName' at $At; source: $sourcePath"
Write-Host "To remove: Unregister-ScheduledTask -TaskName '$TaskName' -Confirm:`$false"
