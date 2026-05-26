# GouseShop Backend

FastAPI backend for GouseShop, with authentication, catalog, cart, orders, payments, Cloudinary product images, and deployment configuration for Render.

## Stack

- FastAPI
- SQLAlchemy async ORM
- Alembic migrations
- PostgreSQL in production
- SQLite for local development
- JWT authentication
- Paystack payment initialization and verification
- Flutterwave integration scaffolding
- Cloudinary image upload
- Optional Redis/Celery support

## Project Structure

```text
GouseShop/
  Backend/
    app/
      api/v1/          API routes
      core/            settings, database, security, redis, rate limits
      models/          SQLAlchemy models
      schemas/         Pydantic schemas
      services/        business logic and provider integrations
      tasks/           Celery tasks
    alembic/           database migrations
    main.py            FastAPI app entrypoint
    requirements.txt   Python dependencies
  render.yaml          Render Blueprint
  runtime.txt          Render Python runtime
```

## Local Setup

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

## Required Environment Variables

Create `Backend\.env` locally. On Render, enter secrets in the Dashboard when applying `render.yaml`.

Core:

```env
APP_NAME=GouseShop Backend
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./gouseshop.db
JWT_SECRET=change-me
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30
PASSWORD_RESET_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
USE_FAKE_EXTERNAL_SERVICES=false
USE_FAKE_REDIS=true
```

Cloudinary:

```env
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
CLOUDINARY_FOLDER=gouseshop
CLOUDINARY_MAX_UPLOAD_BYTES=5242880
```

Paystack:

```env
PAYSTACK_SECRET_KEY=
PAYSTACK_PUBLIC_KEY=
PAYSTACK_WEBHOOK_SECRET=
PAYMENT_CALLBACK_URL=http://localhost:3000/payment/callback
```

Flutterwave:

```env
FLUTTERWAVE_SECRET_KEY=
FLUTTERWAVE_PUBLIC_KEY=
FLUTTERWAVE_WEBHOOK_SECRET=
FLUTTERWAVE_CLIENT_ID=
FLUTTERWAVE_CLIENT_SECRET=
```

Email:

```env
RESEND_API_KEY=
EMAIL_FROM=GouseShop <no-reply@gouseshop.local>
EMAIL_REPLY_TO=
```

## Authentication Test

Login:

```powershell
$token = (Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/auth/login" -Method Post -ContentType "application/json" -Body (@{email="user@example.com";password="password"} | ConvertTo-Json)).access_token
```

Use the token:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/orders" `
  -Headers @{ Authorization = "Bearer $token" }
```

## Image Upload Test

Requires an admin user and an existing product slug.

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/products/admin/test-product/images" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $token" } `
  -Form @{
    file = Get-Item "C:\path\to\image.jpg"
    alt = "Product image"
    sort_order = "0"
    is_primary = "true"
  }
```

The upload endpoint stores Cloudinary metadata in `product_images`.

## Payment Testing

Paystack hosted checkout is supported through:

```text
POST /api/v1/payments/initiate
GET  /api/v1/payments/verify/{reference}
```

Initiate Paystack:

```powershell
$paystack = Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/payments/initiate" `
  -Method Post `
  -Headers @{ Authorization = "Bearer $token" } `
  -ContentType "application/json" `
  -Body '{"order_id":1,"provider":"paystack","country":"NG","currency":"NGN"}'

$paystack.provider_checkout_url
```

Verify after checkout:

```powershell
Invoke-RestMethod `
  -Uri "http://127.0.0.1:8000/api/v1/payments/verify/$($paystack.provider_reference)" `
  -Headers @{ Authorization = "Bearer $token" }
```

Flutterwave note: the code can generate OAuth client-credentials tokens and attempt provider calls. Flutterwave v4 direct card charging requires customer creation, encrypted card/payment method creation, charge creation, possible PIN/3DS continuation, and webhook handling. Do not collect raw card data on this backend without a PCI-safe design.

## Database Migrations

Run locally:

```powershell
cd Backend
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Render runs migrations automatically before starting Uvicorn:

```bash
python -m alembic upgrade head && python -m uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Tests

```powershell
cd Backend
.\.venv\Scripts\python.exe -m pytest
```

## Render Deployment

This repository includes a Render Blueprint:

```text
render.yaml
```

It creates:

- one FastAPI web service
- one managed PostgreSQL database

The web service:

- installs `Backend/requirements.txt`
- runs Alembic migrations
- starts Uvicorn on Render's `$PORT`
- checks `/api/v1/health`

### Render Steps

1. Push this repository to GitHub, GitLab, or Bitbucket.
2. Open Render Dashboard.
3. Create a new Blueprint.
4. Select the repository.
5. Confirm Render detects `render.yaml`.
6. Fill every environment variable marked as secret.
7. Apply the Blueprint.
8. Wait for the deploy to become live.
9. Open:

```text
https://YOUR_RENDER_SERVICE.onrender.com/api/v1/health
```

Expected:

```json
{"status":"ok"}
```

### Important Render Environment Values

Set `CORS_ORIGINS` to your frontend domains as JSON:

```env
["https://your-frontend.com","http://localhost:3000"]
```

Set `PAYMENT_CALLBACK_URL` to the frontend route that handles payment returns:

```env
https://your-frontend.com/payment/callback
```

For testing without Redis on Render:

```env
USE_FAKE_REDIS=true
```

For production background jobs, provision Redis and set:

```env
USE_FAKE_REDIS=false
REDIS_URL=your-render-redis-url
```

## Production Checklist

- Use PostgreSQL, not SQLite.
- Set strong `JWT_SECRET`.
- Restrict `CORS_ORIGINS` to real frontend domains.
- Set `USE_FAKE_EXTERNAL_SERVICES=false`.
- Rotate any credentials that were shared during testing.
- Configure payment webhook secrets before relying on webhooks.
- Add Redis before enabling Celery workers.
- Add error monitoring and structured logs.
- Add database backups before production launch.
- Run smoke tests after each deploy.
