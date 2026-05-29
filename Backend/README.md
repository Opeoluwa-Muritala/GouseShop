# GouseShop Backend

FastAPI backend for GouseShop ecommerce: auth, admin, catalog, carts, orders, payments, Cloudinary uploads, email workflows, Redis-backed rate limiting, and Alembic migrations.

For the full project guide, including frontend and Render deployment, see the root `README.md`.

## Run Locally

1. Copy `.env.example` to `.env`.
2. Install dependencies:
   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
3. Run migrations:
   ```powershell
   .\.venv\Scripts\python.exe -m alembic upgrade head
   ```
4. Start the API:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
   ```

Health check:

```text
http://127.0.0.1:8000/api/v1/health
```

Docs are disabled unless `ENABLE_API_DOCS=true`.

## Important Configuration

- `JWT_SECRET`: strong signing secret. Production rejects weak/default values.
- `CORS_ORIGINS`: explicit frontend origins.
- `ALLOWED_HOSTS`: trusted hostnames for `TrustedHostMiddleware`.
- `SESSION_COOKIE_SECURE` and `SESSION_COOKIE_SAMESITE`: auth cookie policy.
- `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD`: first admin bootstrap credentials.
- `USE_FAKE_REDIS=false` plus Redis/Upstash credentials: required for real rate limits and refresh-token revocation.
- `USE_FAKE_EXTERNAL_SERVICES=false`: required for real payment/email/storage integrations.
- Payment webhook secrets: required before relying on live provider webhooks.

## Auth Model

The API still returns token JSON for API clients, but the browser app uses:

- HttpOnly access and refresh cookies
- A readable `gouseshop_csrf` cookie
- `X-CSRF-Token` on state-changing cookie-authenticated requests

Bearer tokens are accepted for direct API testing.

## Tests

Smoke tests:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_smoke.py
```

Full tests require a dedicated online test database whose name contains `test`, Redis with `REDIS_KEY_PREFIX=test:`, and `USE_FAKE_REDIS=false`.

```powershell
.\.venv\Scripts\python.exe -m pytest
```

The test guard intentionally refuses to reset unsafe database or Redis targets.
