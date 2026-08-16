# EstateCore stabilization baseline

This branch establishes Flask and PostgreSQL as the authoritative demo backend.
Appwrite, hardware relay control, LPR recognition, and mobile clients remain
experimental until their integrations have automated end-to-end tests.

## Local verification

1. Create and activate a virtual environment.
2. Run `pip install -r requirements.txt`.
3. Set `FLASK_APP=wsgi:app`.
4. Run `flask db upgrade`.
5. Run `pytest -q`.
6. Run `gunicorn wsgi:app`.

Production startup intentionally fails when `SECRET_KEY`, `JWT_SECRET_KEY`,
or `DATABASE_URL` is missing. Set `CORS_ORIGINS` to the exact frontend
origin; never use a wildcard with credentials.

## Demonstrated API slice

- `GET /api/health`
- `POST /api/auth/login`
- `GET /api/tenant/me`
- `GET|POST /api/maintenance`
- `POST /api/access/check`

The access decision requires an active credential, an active lease, and the
most recent due payment to be paid. Real door control must use a separate,
authenticated service and must not be triggered directly from this endpoint.
