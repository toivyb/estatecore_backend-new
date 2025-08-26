# EstateCore v1 — Ready-to-Run

## Quick Start (PowerShell)
1) Extract this folder somewhere (e.g. `C:\projects\estatecore_v1_ready`) and `cd` into it.
2) Start stack:
```
docker compose up -d --build
```
3) Bootstrap admin:
```
Invoke-RestMethod -Method POST http://localhost/api/bootstrap-admin `
  -ContentType "application/json" `
  -Body (@{email="admin@example.com"; password="admin123"} | ConvertTo-Json)
```
4) Open http://localhost and log in.

## Notes
- Backend auto-creates tables on startup; no migrations required for the demo.
- Change to SQLite quickly by setting `DATABASE_URL=sqlite:///estatecore.db` in `docker-compose.yml` backend env.
