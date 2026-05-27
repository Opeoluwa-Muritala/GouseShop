# GouseShop Backend

FastAPI backend for the Fashion Store architecture.

## First milestone

- Project scaffolding and API modules
- Async SQLAlchemy connectivity, with SQLite-friendly local defaults
- Auth with JWT tokens
- Product, category, collection, fabric models and CRUD seams
- Cart and order flows with reserved stock logic
- Payment, wishlist, review, waitlist, newsletter tables and endpoints
- Real Redis-backed rate limit and token revocation support
- Alembic migrations

## Run locally

1. Copy `.env.example` to `.env`
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create the database and run migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the app:
   ```bash
   uvicorn main:app --reload
   ```
5. Open Swagger UI:
   ```text
   http://localhost:8000/docs
   ```

Configuration is read from environment variables. For a full run, provide PostgreSQL and Redis URLs plus the provider credentials listed below.

## Required environment variables

- `DATABASE_URL`: online PostgreSQL database URL, preferably `postgresql+asyncpg://...`.
- `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`: Upstash Redis REST credentials.
- `REDIS_URL`: standard Redis URL fallback when Upstash REST credentials are not set.
- `USE_FAKE_REDIS=false`: required for real Redis-backed rate limits and refresh-token revocation.
- `REDIS_KEY_PREFIX`: namespace for all app Redis keys, for example `gouseshop:`.
- `JWT_SECRET`: strong random secret for signing JWTs.
- `CORS_ORIGINS`: comma-separated frontend origins allowed to call the API.
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`: required for real product image uploads.
- `EMAIL_API_URL`: email delivery API, default `https://email-api-4ykn.onrender.com`.

## Optional integration environment variables

- `USE_FAKE_EXTERNAL_SERVICES=false`: required for real payment/email/storage integrations.
- `PAYSTACK_SECRET_KEY`, `PAYSTACK_PUBLIC_KEY`, `PAYSTACK_WEBHOOK_SECRET`: Paystack checkout, verification, webhook, and refund support.
- `FLUTTERWAVE_SECRET_KEY` or `FLUTTERWAVE_CLIENT_ID` plus `FLUTTERWAVE_CLIENT_SECRET`, plus `FLUTTERWAVE_PUBLIC_KEY` and `FLUTTERWAVE_WEBHOOK_SECRET`: Flutterwave checkout, verification, webhook, and refund support.
- `EMAIL_FROM` and optional `EMAIL_REPLY_TO`: reserved for email metadata when the provider supports it.

## Redis with Upstash

Use Upstash by setting:

```bash
USE_FAKE_REDIS=false
UPSTASH_REDIS_REST_URL=https://your-upstash-endpoint.upstash.io
UPSTASH_REDIS_REST_TOKEN=your-token
REDIS_KEY_PREFIX=gouseshop:
```

When Upstash variables are present, the app uses the async Upstash REST client. If they are absent, it falls back to `REDIS_URL` with `redis.asyncio`.

## Complete run checklist

- Set all required environment variables.
- Run migrations before starting the API:
  ```bash
  alembic upgrade head
  ```
- Optional worker for async jobs:
  ```bash
  celery -A app.tasks.celery_app.celery_app worker --loglevel=info
  ```

## Run tests with the online test database

Tests use the configured online `DATABASE_URL` and `REDIS_URL`; they do not create an offline SQLite database. Use dedicated test resources only.

Required:

- `DATABASE_URL`: must point to an online database whose database name contains `test`.
- `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`, or `REDIS_URL`: must point to a Redis instance safe for tests.
- `USE_FAKE_REDIS=false`: required for DB tests.
- `REDIS_KEY_PREFIX`: must start with `test:` so cleanup only deletes test keys.
- Migrations already applied to that test database with `alembic upgrade head`.
- `JWT_SECRET=test-secret` or another test secret.
- `USE_FAKE_EXTERNAL_SERVICES=true` is recommended for fast, isolated tests.

Run:

```bash
pytest -q
```

The test guard refuses to run cleanup against SQLite, a database whose name does not contain `test`, or a Redis prefix that does not start with `test:`.

## Production notes

- Set `DATABASE_URL` to PostgreSQL, for example `postgresql+asyncpg://...`.
- Set `USE_FAKE_REDIS=false` and provide `REDIS_URL`.
- Set `USE_FAKE_EXTERNAL_SERVICES=false` when provider credentials are configured.
- Start a Celery worker with:
  ```bash
  celery -A app.tasks.celery_app.celery_app worker --loglevel=info
  ```

## Notes

- This milestone contains the core architecture and first runnable product/order/payment seams.
- Real provider API calls and deeper admin tooling are next hardening steps.
