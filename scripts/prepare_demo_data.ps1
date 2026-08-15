param(
    [string]$DemoDir = ".\demo_data"
)

$resolvedDemoDir = [System.IO.Path]::GetFullPath($DemoDir)

if (Test-Path -LiteralPath $resolvedDemoDir) {
    $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $backupDir = "$resolvedDemoDir.backup-$timestamp"
    Move-Item -LiteralPath $resolvedDemoDir -Destination $backupDir
    Write-Host "Existing demo data moved to $backupDir"
}

New-Item -ItemType Directory -Path $resolvedDemoDir -Force | Out-Null

Write-Host "Fresh demo data directory ready: $resolvedDemoDir"
Write-Host ""
Write-Host "Start the backend in a new PowerShell terminal:"
Write-Host "  `$env:DATA_DIR = `"$resolvedDemoDir`"; uvicorn backend.main:app --reload --port 8000"
Write-Host ""
Write-Host "Start the frontend in another PowerShell terminal:"
Write-Host "  `$env:BACKEND_URL = `"http://localhost:8000`"; streamlit run frontend/app.py"
Write-Host ""
Write-Host "Open the new Streamlit URL and use Ctrl+Shift+R once if an older browser tab is open."
