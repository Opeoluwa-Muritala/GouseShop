from uuid import uuid4

from app.core.config import settings


async def upload_image(filename: str, content_type: str) -> dict:
    public_id = f"{settings.cloudinary_folder}/{uuid4().hex}"
    return {
        "public_id": public_id,
        "url": f"https://res.cloudinary.com/demo/image/upload/{public_id}/{filename}",
        "secure_url": f"https://res.cloudinary.com/demo/image/upload/{public_id}/{filename}",
        "resource_type": "image",
        "format": filename.rsplit(".", 1)[-1].lower() if "." in filename else None,
        "content_type": content_type,
    }


async def delete_image(public_id: str) -> bool:
    return True
