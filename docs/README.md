# EstateCore Add-ons (build 2025-08-22)

This pack includes:
- `app/security.py` — `roles_required("admin")` decorator
- `app/errors.py` — JSON error handlers
- `app/routes/refresh.py` — `/api/refresh` on the existing auth blueprint
- `scripts/add_user.py`, `scripts/make_admin.py`, `scripts/seed_flags.py` — small helpers
- `deploy_templates/` — sample systemd + nginx files (optional)

## How to install (Windows paths)

**1) Copy files into your backend**

- `estatecore_backend/app/security.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\app\security.py`
- `estatecore_backend/app/errors.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\app\errors.py`
- `estatecore_backend/app/routes/refresh.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\app\routes\refresh.py`
- scripts:
  - `estatecore_backend/scripts/add_user.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\scripts\add_user.py`
  - `estatecore_backend/scripts/make_admin.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\scripts\make_admin.py`
  - `estatecore_backend/scripts/seed_flags.py` → `C:\Users\FSSP\estatecore_project\estatecore_backend\scripts\seed_flags.py`

**2) Wire error handlers (one line in `create_app`)**

Edit: `C:\Users\FSSP\estatecore_project\estatecore_backend\app\__init__.py`

```python
from app.errors import register_error_handlers

def create_app():
    app = Flask(__name__)
    ...
    register_error_handlers(app)
    return app
```

**3) Ensure the refresh route is imported**

Edit: `C:\Users\FSSP\estatecore_project\estatecore_backend\app\routes\__init__.py`

Add:
```python
from . import refresh  # noqa: F401
```

This file piggybacks on your existing `auth` blueprint, so no extra registration is needed.

**4) Lock down toggle to admins**

Edit: `C:\Users\FSSP\estatecore_project\estatecore_backend\app\routes\features.py`

```python
from app.security import roles_required

@bp.post("/features/toggle")
@roles_required("admin")
def toggle_feature():
    ...
```

**5) Seed & test**

```powershell
# (venv) in backend folder
python .\scripts\make_admin.py
python -m flask db upgrade   # ensure schema is current
python .\scripts\seed_flags.py

# Smoke
$Base="http://127.0.0.1:5050"
$login = Invoke-RestMethod "$Base/api/login" -Method POST -ContentType application/json -Body (@{ email="toivybraun@gmail.com"; password="Unique3315!" } | ConvertTo-Json)
$access = $login.access_token; $refresh = $login.refresh_token
Invoke-RestMethod "$Base/api/me" -Headers @{ Authorization = "Bearer $access" }

# refresh
$new = Invoke-RestMethod "$Base/api/refresh" -Method POST -Headers @{ Authorization = "Bearer $refresh" }
$access = $new.access_token
Invoke-RestMethod "$Base/api/features" -Headers @{ Authorization = "Bearer $access" }

# toggle (should be 200 for admin)
$body = @{ key="smoke_flag"; enabled=$false } | ConvertTo-Json
Invoke-RestMethod "$Base/api/features/toggle" -Method POST -ContentType application/json -Body $body -Headers @{ Authorization = "Bearer $access" }
```

**6) Deploy (optional templates)**

See `deploy_templates/estatecore.service` and `deploy_templates/nginx.conf` as starting points.
