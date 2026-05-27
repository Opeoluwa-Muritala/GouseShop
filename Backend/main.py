from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.v1 import auth, cart, categories, collections, engagement, fabrics, orders, payments, products
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    description="GouseShop backend API for auth, catalog, carts, orders, payments, and engagement.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Session-Id"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(products.router, prefix="/api/v1/products", tags=["products"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(collections.router, prefix="/api/v1/collections", tags=["collections"])
app.include_router(fabrics.router, prefix="/api/v1/fabrics", tags=["fabrics"])
app.include_router(cart.router, prefix="/api/v1/cart", tags=["cart"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
app.include_router(payments.router, prefix="/api/v1/payments", tags=["payments"])
app.include_router(engagement.router, prefix="/api/v1", tags=["engagement"])

@app.get("/api/v1/health")
async def health_check():
    return {"status": "ok"}


@app.get("/", include_in_schema=False)
async def swagger_redirect():
    return RedirectResponse(url="/docs")
