
#!/usr/bin/env bash
set -euo pipefail

BACKEND_ROOT=""
FRONTEND_ROOT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --backend-root) BACKEND_ROOT="$2"; shift 2;;
    --frontend-root) FRONTEND_ROOT="$2"; shift 2;;
    *) echo "Unknown arg: $1" && exit 1;;
  esac
done

if [[ -z "${BACKEND_ROOT}" || -z "${FRONTEND_ROOT}" ]]; then
  echo "Usage: $0 --backend-root <path> --frontend-root <path>"
  exit 1
fi

backup_and_copy () {
  src_rel="$1"
  dst_root="$2"
  src="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../${src_rel}"
  dst="${dst_root}/${src_rel}"
  backup_dir="${dst_root}/_backup_$(date +%Y%m%d_%H%M%S)"

  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" ]]; then
    mkdir -p "$backup_dir/$(dirname "$src_rel")"
    cp -a "$dst" "$backup_dir/$src_rel"
  fi

  mkdir -p "$(dirname "$dst")"
  cp -a "$src" "$dst"
}

# Backend
backup_and_copy "backend/app" "$BACKEND_ROOT"
backup_and_copy "backend/migrations" "$BACKEND_ROOT"
backup_and_copy "backend/requirements.txt" "$BACKEND_ROOT"
backup_and_copy "backend/config.py" "$BACKEND_ROOT"
backup_and_copy "backend/run.py" "$BACKEND_ROOT"
backup_and_copy "backend/wsgi.py" "$BACKEND_ROOT"
backup_and_copy "deploy/.env.example" "$BACKEND_ROOT"

# Frontend
backup_and_copy "frontend/src/index.css" "$FRONTEND_ROOT"
backup_and_copy "frontend/tailwind.config.js" "$FRONTEND_ROOT"
backup_and_copy "frontend/postcss.config.cjs" "$FRONTEND_ROOT"

# Deploy samples
mkdir -p "${BACKEND_ROOT}/deploy"
cp -a "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../deploy/." "${BACKEND_ROOT}/deploy/"

echo "Patch applied. Backups saved under _backup_* in your project roots."
