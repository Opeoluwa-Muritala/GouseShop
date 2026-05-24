# GouseShop Backend

FastAPI backend for the Fashion Store architecture.

## First milestone

- Project scaffolding and API modules
- Async SQLAlchemy connectivity, with SQLite-friendly local defaults
- Auth with JWT tokens
- Product, category, collection, fabric models and CRUD seams
- Cart and order flows with reserved stock logic
- Payment, wishlist, review, waitlist, newsletter tables and endpoints
- Fake-friendly Redis/payment/email/storage adapters for local testing
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

With the default `.env.example`, the app uses SQLite and in-memory fake external services so it can start without PostgreSQL, Redis, Celery, Paystack, Flutterwave, Cloudinary, or Resend.

## Production notes

- Set `DATABASE_URL` to PostgreSQL, for example `postgresql+asyncpg://...`.
- Set `USE_FAKE_EXTERNAL_SERVICES=false` when Redis and provider credentials are configured.
- Start a Celery worker with:
  ```bash
  celery -A app.tasks.celery_app.celery_app worker --loglevel=info
  ```

## Notes

- This milestone contains the core architecture and first runnable product/order/payment seams.
- Real provider API calls and deeper admin tooling are next hardening steps.
