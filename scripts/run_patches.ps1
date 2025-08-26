\
param()

$ErrorActionPreference = 'Stop'

function Add-HelpersIfMissing {
    param([string]$Content)

    if ($Content -notmatch 'def\s+safe_drop_constraint\(') {
        # Insert helpers right after the alembic op import if present; otherwise at top.
        $helper = @'
from alembic import op

def safe_drop_constraint(table: str, name: str):
    op.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"')

def safe_drop_table(name: str):
    op.execute(f'DROP TABLE IF EXISTS "{name}" CASCADE')
'@

        if ($Content -match 'from\s+alembic\s+import\s+op[^\r\n]*\r?\n') {
            $Content = [Regex]::Replace($Content, 'from\s+alembic\s+import\s+op[^\r\n]*\r?\n',
                { param($m) $m.Value + "`r`n" + $helper + "`r`n" }, 1)
        } else {
            $Content = $helper + "`r`n" + $Content
        }
    }

    return $Content
}

function Generic-Rewrites {
    param([string]$Content)

    # 1) Replace op.drop_constraint('X','T', type_='foreignkey' ... ) with safe_drop_constraint('T','X')
    $pattern = "op\.drop_constraint\(\s*(['""])([^'""]+)\1\s*,\s*(['""])([^'""]+)\3\s*,\s*type_=['""]foreignkey['""][^)]*\)"
    $Content = [Regex]::Replace($Content, $pattern, { param($m)
        $cname = $m.Groups[2].Value
        $tname = $m.Groups[4].Value
        "safe_drop_constraint('$tname', '$cname')"
    })

    # 2) Replace op.drop_table('name') with safe_drop_table('name')
    $pattern2 = "op\.drop_table\(\s*(['""])([^'""]+)\1\s*\)"
    $Content = [Regex]::Replace($Content, $pattern2, { param($m)
        $tname = $m.Groups[2].Value
        "safe_drop_table('$tname')"
    })

    return $Content
}

function Patch-File {
    param([string]$Path)

    $orig = Get-Content -Raw -Encoding UTF8 -Path $Path

    # Only try to patch if file seems relevant
    if ($orig -notmatch 'op\.drop_constraint\(.+type_=[''"]foreignkey'']' -and
        $orig -notmatch 'op\.drop_table\(') {
        return $false
    }

    $content = $orig
    $content = Add-HelpersIfMissing -Content $content
    $content = Generic-Rewrites -Content $content

    if ($content -ne $orig) {
        if (-not (Test-Path ($Path + ".bak"))) {
            Copy-Item -Path $Path -Destination ($Path + ".bak")
        }
        Set-Content -Path $Path -Value $content -Encoding UTF8
        Write-Host "Patched $Path"
        return $true
    } else {
        return $false
    }
}

$versions = Join-Path (Resolve-Path .).Path 'migrations\versions'
if (-not (Test-Path $versions)) {
    throw "Can't find 'migrations\versions' from current directory. Run this script from your project root."
}

$changed = 0
Get-ChildItem -Path $versions -Filter '*.py' | ForEach-Object {
    if (Patch-File -Path $_.FullName) {
        $changed++
    }
}

if ($changed -gt 0) {
    Write-Host "Done. Modified $changed migration file(s). Now run:  flask db upgrade" -ForegroundColor Green
} else {
    Write-Host "No migration files needed patching (nothing matched drop-constraint/table patterns)." -ForegroundColor Yellow
}
