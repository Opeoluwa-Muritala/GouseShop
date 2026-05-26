import asyncio
from io import BytesIO
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


def _validate_cloudinary_settings() -> None:
    if not settings.cloudinary_cloud_name or not settings.cloudinary_api_key or not settings.cloudinary_api_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary is not configured",
        )


async def upload_image(filename: str, content_type: str, content: bytes) -> dict:
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")
    if len(content) > settings.cloudinary_max_upload_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Image is too large")

    image_id = uuid4().hex
    public_id = f"{settings.cloudinary_folder}/{image_id}"

    if settings.use_fake_external_services:
        return {
            "public_id": public_id,
            "url": f"https://res.cloudinary.com/demo/image/upload/{public_id}/{filename}",
            "secure_url": f"https://res.cloudinary.com/demo/image/upload/{public_id}/{filename}",
            "resource_type": "image",
            "format": filename.rsplit(".", 1)[-1].lower() if "." in filename else None,
            "width": None,
            "height": None,
        }

    _validate_cloudinary_settings()

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary SDK is not installed",
        ) from exc

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )

    result = await asyncio.to_thread(
        cloudinary.uploader.upload,
        BytesIO(content),
        public_id=image_id,
        folder=settings.cloudinary_folder,
        resource_type="image",
        overwrite=False,
    )
    return {
        "public_id": result.get("public_id"),
        "url": result.get("url"),
        "secure_url": result.get("secure_url"),
        "resource_type": result.get("resource_type"),
        "format": result.get("format"),
        "width": result.get("width"),
        "height": result.get("height"),
    }


async def delete_image(public_id: str) -> bool:
    if settings.use_fake_external_services:
        return True

    _validate_cloudinary_settings()

    try:
        import cloudinary
        import cloudinary.uploader
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary SDK is not installed",
        ) from exc

    cloudinary.config(
        cloud_name=settings.cloudinary_cloud_name,
        api_key=settings.cloudinary_api_key,
        api_secret=settings.cloudinary_api_secret,
        secure=True,
    )
    result = await asyncio.to_thread(cloudinary.uploader.destroy, public_id, resource_type="image")
    return result.get("result") in {"ok", "not found"}


async def delete_image_if_configured(public_id: str | None) -> bool:
    if not public_id:
        return True
    return await delete_image(public_id)
