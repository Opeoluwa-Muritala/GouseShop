from ipaddress import ip_address

import httpx
from fastapi import Request


COUNTRY_CURRENCY = {
    "NG": "NGN",
    "GH": "GHS",
    "ZA": "ZAR",
    "KE": "KES",
    "US": "USD",
    "GB": "GBP",
    "CA": "CAD",
    "AU": "AUD",
}

PAYSTACK_COUNTRY_CURRENCY = {
    "NG": "NGN",
    "GH": "GHS",
    "ZA": "ZAR",
    "KE": "KES",
}

COUNTRY_HEADERS = (
    "cf-ipcountry",
    "x-vercel-ip-country",
    "cloudfront-viewer-country",
    "x-country-code",
)


def request_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else None


async def request_country_code(request: Request) -> str | None:
    for header in COUNTRY_HEADERS:
        country = request.headers.get(header)
        if country and country.upper() != "XX":
            return country.upper()

    ip = request_ip(request)
    if not ip or _is_private_ip(ip):
        return None

    try:
        async with httpx.AsyncClient(timeout=4) as client:
            response = await client.get(f"https://ipapi.co/{ip}/country/")
        if response.status_code == 200:
            country = response.text.strip().upper()
            return country if len(country) == 2 else None
    except httpx.HTTPError:
        return None

    return None


async def request_currency(request: Request, fallback: str = "NGN") -> str:
    country = await request_country_code(request)
    return COUNTRY_CURRENCY.get(country or "", fallback).upper()


async def request_paystack_currency(request: Request, fallback: str = "NGN") -> str:
    country = await request_country_code(request)
    return PAYSTACK_COUNTRY_CURRENCY.get(country or "", fallback).upper()


def _is_private_ip(value: str) -> bool:
    try:
        parsed = ip_address(value)
    except ValueError:
        return True
    return parsed.is_private or parsed.is_loopback or parsed.is_link_local
