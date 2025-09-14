# ---- CONFIG ----
$projectRoot = "C:\Users\FSSP\estatecore_project\estatecore_backend"   # <- adjust if you used a different path
$dbUrl       = "postgresql://postgres:postgres@localhost:5432/estatecore"
$adminEmail  = "admin@example.com"
$adminPass   = "Admin123!"

# ---- 0) Verify project layout (must exist) ----
if (-not (Test-Path "$projectRoot\estatecore_backend\wsgi.py")) {
  Write-Error "Expected $projectRoot\estatecore_backend\wsgi.py . Fix your path and rerun."
  exit 1
}

# ---- 1) Python venv + deps (pinned by your requirements.txt) ----
Set-Location $projectRoot
if (Test-Path ".venv") { Remove-Item ".venv" -Recurse -Force }
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r "$projectRoot\requirements.txt"

# ---- 2) PostgreSQL sanity + DB create (requires Postgres installed) ----
$psql = (Get-Command psql.exe -ErrorAction SilentlyContinue)
if (-not $psql) { Write-Error "psql not found. Install PostgreSQL and ensure psql.exe is in PATH, then rerun."; exit 1 }

# Make sure server is running (service name may be 'postgresql-x64-17')
$svc = Get-Service | Where-Object { $_.Name -like "postgresql*" }
if ($svc -and $svc.Status -ne "Running") { Start-Service $svc.Name }

# Create DB if missing
try {
  & psql -U postgres -h localhost -p 5432 -t -c "SELECT 1" | Out-Null
} catch { Write-Error "Cannot connect to Postgres on 5432 with user postgres. Fix credentials/service."; exit 1 }

$exists = & psql -U postgres -h localhost -p 5432 -t -A -c "SELECT 1 FROM pg_database WHERE datname='estatecore';"
if (-not $exists) {
  & psql -U postgres -h localhost -p 5432 -c "CREATE DATABASE estatecore;"
}

# ---- 3) Env vars for this session ----
$env:FLASK_APP   = "estatecore_backend.wsgi"
$env:DATABASE_URL= $dbUrl
$env:SECRET_KEY  = "dev-secret"
$env:JWT_SECRET  = "dev-jwt"

# ---- 4) Migrations ----
flask db upgrade

# ---- 5) Seed admin user ----
python "$projectRoot\estatecore_backend\scripts\seed_demo.py"

# ---- 6) Import sanity + route list ----
python - << 'PY'
from estatecore_backend.wsgi import app
print("WSGI import OK")
print("Sample routes:", sorted([r.rule for r in app.url_map.iter_rules() if r.rule in ("/healthz","/api/login")]))
PY

# ---- 7) Run server on 8080 (background) ----
$server = Start-Process -FilePath python -ArgumentList "-m","flask","run","--port","8080","--host","0.0.0.0" -PassThru
Start-Sleep -Seconds 3

# ---- 8) Smoke checks ----
try {
  $h = Invoke-RestMethod -Uri "http://127.0.0.1:8080/healthz" -TimeoutSec 5
  "healthz: $($h.status)"
} catch { "healthz failed: $($_.Exception.Message)" }

try {
  $resp = Invoke-RestMethod -Method POST -Uri "http://127.0.0.1:8080/api/login" `
    -ContentType application/json `
    -Body (@{ email=$adminEmail; password=$adminPass } | ConvertTo-Json)
  "login: OK (token len $($resp.token.Length))"
} catch { "login failed: $($_.Exception.Message)" }

Write-Host "`nServer PID: $($server.Id). Stop with: Stop-Process $($server.Id)"
