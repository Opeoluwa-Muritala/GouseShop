from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse

from app.api.v1 import auth, cart, categories, collections, engagement, fabrics, orders, payments, products
from app.core.config import settings
from app.core.security import ACCESS_COOKIE_NAME, CSRF_COOKIE_NAME

settings.validate_production_settings()

app = FastAPI(
    title=settings.app_name,
    description="GouseShop backend API for auth, catalog, carts, orders, payments, and engagement.",
    version="1.0.0",
    docs_url="/docs" if settings.enable_api_docs else None,
    redoc_url="/redoc" if settings.enable_api_docs else None,
    openapi_url="/openapi.json" if settings.enable_api_docs else None,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Session-Id", "X-CSRF-Token"],
)

from app.api.v1 import admin, auth, cart, categories, collections, engagement, fabrics, orders, payments, products


CSRF_EXEMPT_PATHS = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/forgot-password",
    "/api/v1/auth/verify-email",
    "/api/v1/auth/resend-verification",
    "/api/v1/auth/reset-password",
    "/admin/login",
}


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    if (
        request.method in {"POST", "PUT", "PATCH", "DELETE"}
        and request.url.path not in CSRF_EXEMPT_PATHS
        and request.cookies.get(ACCESS_COOKIE_NAME)
    ):
        csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)
        csrf_header = request.headers.get("x-csrf-token")
        if not csrf_cookie or not csrf_header or csrf_cookie != csrf_header:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing or invalid"},
            )

    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    return response

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])
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
    return RedirectResponse(url="/docs" if settings.enable_api_docs else "/api/v1/health")
