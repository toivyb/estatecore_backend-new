
param(
    [Parameter(Mandatory=$true)][string]$BackendRoot,
    [Parameter(Mandatory=$true)][string]$FrontendRoot
)

function Backup-And-Copy($srcRel, $dstRoot) {
    $src = Join-Path $PSScriptRoot "..\$srcRel"
    $dst = Join-Path $dstRoot $srcRel
    $backupDir = Join-Path $dstRoot "_backup_$(Get-Date -Format yyyyMMdd_HHmmss)"
    if (Test-Path $dst) {
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
        $dstParent = Split-Path $dst
        $rel = Resolve-Path $dst -Relative
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    if (Test-Path $dst) {
        $backupPath = Join-Path $backupDir $srcRel
        New-Item -ItemType Directory -Force -Path (Split-Path $backupPath) | Out-Null
        Copy-Item -Recurse -Force $dst $backupPath
    }
    Copy-Item -Recurse -Force $src $dst
}

# Backend copies
Backup-And-Copy "backend\app" $BackendRoot
Backup-And-Copy "backend\migrations" $BackendRoot
Backup-And-Copy "backend\requirements.txt" $BackendRoot
Backup-And-Copy "backend\config.py" $BackendRoot
Backup-And-Copy "backend\run.py" $BackendRoot
Backup-And-Copy "backend\wsgi.py" $BackendRoot
Backup-And-Copy "deploy\.env.example" $BackendRoot

# Frontend copies
Backup-And-Copy "frontend\src\index.css" $FrontendRoot
Backup-And-Copy "frontend\tailwind.config.js" $FrontendRoot
Backup-And-Copy "frontend\postcss.config.cjs" $FrontendRoot

# Deploy samples (to a 'deploy' folder under backend root)
$deployDst = Join-Path $BackendRoot "deploy"
New-Item -ItemType Directory -Force -Path $deployDst | Out-Null
Copy-Item -Recurse -Force (Join-Path $PSScriptRoot "..\deploy\*") $deployDst

Write-Host "Patch applied. Review backups under _backup_* folders in your project roots." -ForegroundColor Green
