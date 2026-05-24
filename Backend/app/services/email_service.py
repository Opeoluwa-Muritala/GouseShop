from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email import EmailLog


async def send_email(
    session: AsyncSession, recipient: str, subject: str, template: str, context: dict | None = None
) -> EmailLog:
    log = EmailLog(
        recipient=recipient,
        subject=subject,
        template=template,
        status="sent",
        provider_message_id=f"fake_{template}",
    )
    session.add(log)
    await session.commit()
    await session.refresh(log)
    return log
