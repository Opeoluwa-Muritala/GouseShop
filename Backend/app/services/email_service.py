import html

import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.email import EmailLog


def _token_from_context(context: dict | None) -> str:
    if not context:
        return ""
    return str(context.get("token") or "")


def render_email_content(template: str, context: dict | None = None) -> tuple[str, str]:
    token = _token_from_context(context)
    escaped_token = html.escape(token)
    if template == "email_verification":
        text = f"Verify your GouseShop email with this token:\n\n{token}"
        html_body = f"<p>Verify your GouseShop email with this token:</p><p><strong>{escaped_token}</strong></p>"
        return text, html_body
    if template == "password_reset":
        text = f"Reset your GouseShop password with this token:\n\n{token}"
        html_body = f"<p>Reset your GouseShop password with this token:</p><p><strong>{escaped_token}</strong></p>"
        return text, html_body
    return "You have a new GouseShop notification.", "<p>You have a new GouseShop notification.</p>"


async def _record_email(
    session: AsyncSession,
    recipient: str,
    subject: str,
    template: str,
    status_value: str,
    provider_message_id: str | None = None,
    error: str | None = None,
) -> EmailLog:
    log = EmailLog(
        recipient=recipient,
        subject=subject,
        template=template,
        status=status_value,
        provider_message_id=provider_message_id,
        error=error,
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log


async def send_email(
    session: AsyncSession, recipient: str, subject: str, template: str, context: dict | None = None
) -> EmailLog:
    text, html_body = render_email_content(template, context)
    if settings.use_fake_external_services:
        return await _record_email(
            session,
            recipient,
            subject,
            template,
            "sent",
            provider_message_id=f"fake_{template}",
        )

    payload = {
        "to": recipient,
        "subject": subject,
        "text": text,
        "html": html_body,
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(settings.email_api_url, json=payload)
    except httpx.HTTPError as exc:
        error = str(exc)
        await _record_email(session, recipient, subject, template, "failed", error=error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Email provider request failed",
        ) from exc

    if response.status_code < 200 or response.status_code >= 300:
        error = response.text[:500]
        await _record_email(session, recipient, subject, template, "failed", error=error)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Email provider rejected the message",
        )

    provider_message_id = None
    try:
        data = response.json()
    except ValueError:
        data = None
    if isinstance(data, dict):
        provider_message_id = str(data.get("id") or data.get("message_id") or "") or None

    return await _record_email(session, recipient, subject, template, "sent", provider_message_id)
