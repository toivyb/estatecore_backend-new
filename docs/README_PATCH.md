
# EstateCore — All 5 Options Patch (2025-08-08)

This bundle includes:
1. **Models/Relationships Fix** (SQLAlchemy) + clean migration scaffold
2. **Frontend Essentials**: `index.css`, `tailwind.config.js`, `postcss.config.cjs`
3. **Invite Tokens**: create/verify/consume routes + minimal UI stubs
4. **Rent Receipt PDF**: styled PDF endpoint + template
5. **Prod Setup**: Nginx + Gunicorn samples, `.env.example`

## Apply (Windows PowerShell)
```powershell
# Example: project root at C:\Users\toivy\estatecore-backend and C:\Users\toivy\estatecore-frontend
# 1) Extract this zip anywhere (e.g., Desktop)
# 2) Run from the extracted folder:
./scripts/apply_patch.ps1 -BackendRoot "C:\\Users\\toivy\\estatecore-backend" -FrontendRoot "C:\\Users\\toivy\\estatecore-frontend"
```

## Apply (macOS/Linux)
```bash
chmod +x ./scripts/apply_patch.sh
./scripts/apply_patch.sh --backend-root "/path/to/estatecore-backend" --frontend-root "/path/to/estatecore-frontend"
```

Both scripts back up any file they overwrite to `*_backup` folder under your project roots.

### After applying (backend)
```bash
# Python venv active
pip install -r requirements.txt

# Initialize or reset migrations if needed
flask db init 2>/dev/null || true
flask db migrate -m "all5_patch_relationships"
flask db upgrade

# Seed admin (optional):
python run.py --seed-admin
```

### After applying (frontend)
```bash
npm install
npm run dev   # or npm run build && npm run preview
```

### Environment
Copy `.env.example` to `.env` in backend root and set values.

### Notes
- PDF uses ReportLab (no system deps).
- Invite tokens: one-time use, TTL, property/role scoped.
- Nginx and Gunicorn files are templates—adjust paths/domains.
