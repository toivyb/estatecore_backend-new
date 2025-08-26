API Patch — Blueprints, JWT, CORS, Imports (2025-08-13)
=======================================================
Applies to: C:\Users\toivybraun\New folder\estatecore_backend

1) Copy patch over your project
$patchRoot = Join-Path $env:TEMP "estatecore_backend_api_patch_2025-08-13\estatecore_backend\estatecore_backend"
Copy-Item -Recurse -Force $patchRoot "C:\Users\toivybraun\New folder\estatecore_backend\estatecore_backend"

2) Install/Update deps
python -m pip install flask flask_sqlalchemy flask_migrate flask-jwt-extended flask-cors fpdf2

3) Initialize DB (SQLite default)
cd "C:\Users\toivybraun\New folder\estatecore_backend"
$env:FLASK_APP = "estatecore_backend.wsgi"
flask db init
flask db migrate -m "Initial"
flask db upgrade

# Create an admin user (one-time helper)
python - <<'PY'
from estatecore_backend.wsgi import app
from estatecore_backend.models import db, User
with app.app_context():
    if not User.query.filter_by(email="admin@example.com").first():
        u = User(email="admin@example.com"); u.set_password("admin123"); db.session.add(u); db.session.commit(); print("Admin created.")
    else:
        print("Admin exists.")
PY

4) Run and test
flask run --host 127.0.0.1 --port 5000
Invoke-RestMethod -Method GET  http://127.0.0.1:5000/api/ping
Invoke-RestMethod -Method POST http://127.0.0.1:5000/api/login -ContentType application/json `
  -Body (@{email="admin@example.com";password="admin123"} | ConvertTo-Json)
Invoke-RestMethod -Method GET http://127.0.0.1:5000/api/rent

Notes
- JWT secret defaults to SECRET_KEY; set env for production:
  $env:FLASK_SECRET_KEY = "<strong-random>"
  $env:FLASK_JWT_SECRET_KEY = "<same-or-different>"
- For Postgres:
  $env:FLASK_SQLALCHEMY_DATABASE_URI = "postgresql+psycopg://user:pass@localhost:5432/estatecore"
