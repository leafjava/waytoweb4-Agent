# reproduce.ps1 -- one-shot reproduction for judges on Windows.
# Usage: powershell -ExecutionPolicy Bypass -File scripts/reproduce.ps1
# Output: .\evidence.txt and frontend\public\runs\two_runs_*.json.

$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
$Root = (Get-Location).Path

function Step($n, $msg) { Write-Host "==> [$n/5] $msg" -ForegroundColor Cyan }

Step 1 'Installing Python deps (agent + backend)'
python -m pip install -e agent[dev] -e backend[dev] | Out-Null

Step 2 'Installing frontend deps'
Push-Location frontend
try { npm install --no-audit --no-fund --loglevel=error | Out-Null } finally { Pop-Location }

Step 3 'Booting backend on :8000'
$env:PYTHONPATH = $Root
$backend = Start-Process -FilePath python -ArgumentList @('-m','uvicorn','backend.app.main:app','--host','127.0.0.1','--port','8000','--log-level','warning') -PassThru
Start-Sleep -Seconds 5
try {
    $h = Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/api/health -TimeoutSec 5
    if ($h.StatusCode -ne 200) { throw 'backend health failed' }
} catch { throw "Backend did not start: $_" }

Step 4 'Booting frontend on :5173'
Push-Location frontend
try {
    $frontend = Start-Process -FilePath npx -ArgumentList @('vite','--host','--port','5173') -PassThru
} finally { Pop-Location }
Start-Sleep -Seconds 6

Step 5 'Running two-run controlled experiment'
python scripts/two_runs_demo.py

Write-Host '==> Capturing token table + latest two runs'
$tokenTable = (Invoke-WebRequest -UseBasicParsing -Uri http://127.0.0.1:8000/api/state/tokens -TimeoutSec 5).Content
$latest = Get-ChildItem frontend/public/runs/two_runs_*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$latestJson = Get-Content $latest.FullName -Raw

@"
=== /api/state/tokens ===
$tokenTable

=== latest two runs ===
$latestJson
"@ | Out-File -Encoding UTF8 (Join-Path $Root 'evidence.txt')

Write-Host ''
Write-Host 'All done. Output: .\evidence.txt' -ForegroundColor Green
Write-Host 'Open http://localhost:5173/ in your browser, then Ctrl-C here to stop both servers.'

try { Read-Host 'Press Enter to stop servers' | Out-Null } finally {
    Stop-Process -Id $frontend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
}