# GouseShop

GouseShop is a full-stack ecommerce application for fashion retail. It includes a React/Vite storefront, a FastAPI backend, admin catalog/order tooling, cart and order flows, Cloudinary product image uploads, Paystack and Flutterwave payment integrations, email workflows, Redis-backed rate limiting, and a Render Blueprint for deployment.

## Stack

- Frontend: React 19, Vite 8, lucide-react
- Backend: FastAPI, SQLAlchemy async ORM, Alembic, Pydantic
- Data: PostgreSQL in production, SQLite-friendly local defaults
- Cache/rate limits: Redis or Upstash Redis REST
- Payments: Paystack and Flutterwave
- Media: Cloudinary
- Deployment: Render Blueprint, optional Fly backend config

## Repository Layout

```text
GouseShop/
  Backend/
    app/
      api/v1/        API routes
      core/          config, database, security, Redis, rate limiting
      models/        SQLAlchemy models
      schemas/       Pydantic schemas
      services/      auth, catalog, order, payment, email, Cloudinary logic
      tasks/         Celery task wiring
    alembic/         migrations
    tests/           backend tests
    main.py          FastAPI app entrypoint
  Frontend/
    src/             React app, pages, components, API client
    package.json     frontend dependencies and scripts
  render.yaml        Render Blueprint
  runtime.txt        Python runtime hint
```

## Local Backend

From `Backend`:

```powershell
cd C:\Users\LENOVO\Desktop\GouseShop\Backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --port 8000
```

Health check:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/v1/health
```

API docs are disabled by default. For local development only, set:

```env
ENABLE_API_DOCS=true
```

Then open:

```text
http://127.0.0.1:8000/docs
```

## Local Frontend

From `Frontend`:

```powershell
cd C:\Users\LENOVO\Desktop\GouseShop\Frontend
npm ci
npm run dev
```

Set `VITE_API_URL` if the backend is not running at the default:

```env
VITE_API_URL=http://127.0.0.1:8000/api/v1
```

Production build:

```powershell
npm run build
```

## Environment Variables

Copy `Backend\.env.example` to `Backend\.env` for local backend development. In Render, fill variables marked `sync: false` in the Dashboard.

Core:

```env
APP_NAME=GouseShop Backend
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./gouseshop.db
JWT_SECRET=replace-with-a-long-random-secret
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_ORIGIN_REGEX=
ALLOWED_HOSTS=localhost,127.0.0.1,testserver
ENABLE_API_DOCS=true
SESSION_COOKIE_SECURE=false
SESSION_COOKIE_SAMESITE=lax
USE_FAKE_REDIS=true
USE_FAKE_EXTERNAL_SERVICES=true
```

Admin bootstrap:

```env
ADMIN_BOOTSTRAP_EMAIL=owner@example.com
ADMIN_BOOTSTRAP_PASSWORD=strongpass123
```

The first successful `/admin/login` with those credentials creates the bootstrap admin. In production, known default or weak bootstrap passwords are rejected.

Redis:

```env
REDIS_URL=redis://localhost:6379/0
UPSTASH_REDIS_REST_URL=
UPSTASH_REDIS_REST_TOKEN=
REDIS_KEY_PREFIX=gouseshop:
```

Cloudinary:

```env
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=gouseshop
CLOUDINARY_MAX_UPLOAD_BYTES=5242880
```

Payments:

```env
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
PAYSTACK_WEBHOOK_SECRET=
FLUTTERWAVE_SECRET_KEY=
FLUTTERWAVE_PUBLIC_KEY=
FLUTTERWAVE_WEBHOOK_SECRET=
FLUTTERWAVE_CLIENT_ID=
FLUTTERWAVE_CLIENT_SECRET=
PAYMENT_CALLBACK_URL=http://localhost:3000/payment/callback
```

Email:

```env
RESEND_API_KEY=
EMAIL_API_URL=https://email-api-4ykn.onrender.com
EMAIL_FROM=GouseShop <no-reply@gouseshop.local>
EMAIL_REPLY_TO=
```

## Authentication And CSRF

The backend returns token JSON for API compatibility, but the browser app uses HttpOnly cookies:

- `gouseshop_access`: access token, HttpOnly
- `gouseshop_refresh`: refresh token, HttpOnly
- `gouseshop_csrf`: readable CSRF token

The frontend API client sends `credentials: "include"` and attaches `X-CSRF-Token` for state-changing requests. If you call protected POST/PATCH/DELETE endpoints manually using cookies, include the CSRF header.

Bearer tokens are still accepted for direct API testing:

```powershell
$login = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/auth/login" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{email="user@example.com";password="secret123"} | ConvertTo-Json)

$token = $login.access_token

Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/auth/me" `
  -Headers @{ Authorization = "Bearer $token" }
```

## Admin

Set `ADMIN_BOOTSTRAP_EMAIL` and `ADMIN_BOOTSTRAP_PASSWORD`, then open:

```text
/admin/login
```

Admin capabilities include product creation/deletion, admin image upload, order listing, and order status updates. Admin image uploads are rate-limited, size-limited, and checked for basic image signatures before Cloudinary upload.

## Payments

Main endpoints:

```text
POST /api/v1/payments/initiate
GET  /api/v1/payments/verify/{reference}
POST /api/v1/payments/webhook/paystack
POST /api/v1/payments/webhook/flutterwave
POST /api/v1/payments/refund
```

Payment hardening notes:

- Users can verify only their own payment references; admins can verify any payment.
- Public payment responses do not expose raw provider payloads.
- Webhooks validate provider signatures before reconciling payment and order state.
- Client-supplied currency/country tampering is rejected; order currency is server-owned.

## Render Deployment

`render.yaml` defines:

- Static frontend service using `npm ci && npm run build`
- FastAPI backend service
- Managed PostgreSQL database
- Backend migrations before app startup
- `/api/v1/health` health check

Render steps:

1. Push the repo to GitHub, GitLab, or Bitbucket.
2. Create a new Render Blueprint.
3. Select the repo and confirm `render.yaml`.
4. Fill every secret or `sync: false` variable.
5. Set `VITE_API_URL` on the frontend to the backend `/api/v1` URL.
6. Set `PAYMENT_CALLBACK_URL` to the frontend payment callback route.
7. Deploy and confirm `/api/v1/health`.

Important production values:

```env
ENVIRONMENT=production
ENABLE_API_DOCS=false
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_SAMESITE=none
USE_FAKE_EXTERNAL_SERVICES=false
USE_FAKE_REDIS=false
```

Use a long random `JWT_SECRET`, explicit `CORS_ORIGINS`, and real payment webhook secrets and Redis/Upstash credentials. On Render, `ALLOWED_HOSTS=*` is used so Render's proxy and health checks do not get rejected by host validation; browser access is still constrained by CORS.

## Tests

Smoke tests that do not reset the database:

```powershell
cd Backend
.\.venv\Scripts\python.exe -m pytest tests\test_smoke.py
```

Full backend tests require dedicated online test resources. The test guard refuses to reset SQLite, any database whose name does not contain `test`, or Redis keys whose prefix does not start with `test:`.

Required test environment:

```env
DATABASE_URL=postgresql+asyncpg://.../gouseshop_test
USE_FAKE_REDIS=false
REDIS_KEY_PREFIX=test:
JWT_SECRET=test-secret
USE_FAKE_EXTERNAL_SERVICES=true
```

Run:

```powershell
cd Backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend build check:

```powershell
cd Frontend
npm run build
```

## Security Checklist

- Use PostgreSQL in production.
- Keep API docs disabled or protected in production.
- Use a strong `JWT_SECRET`; production startup rejects weak/default secrets.
- Restrict CORS and trusted hosts to real deployment domains.
- Use HttpOnly auth cookies and CSRF headers for browser sessions.
- Configure admin bootstrap through environment variables only.
- Configure Paystack and Flutterwave webhook secrets before accepting live payments.
- Keep provider response payloads out of public API responses.
- Use Redis/Upstash for rate limiting and refresh-token revocation.
- Rotate any credentials used during testing.
- Run smoke tests after each deploy.
- Add monitoring, structured logs, and database backups before launch.
