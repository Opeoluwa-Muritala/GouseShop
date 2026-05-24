from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import PaymentProvider, PaymentStatus


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    provider: Mapped[PaymentProvider] = mapped_column(
        Enum(PaymentProvider, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
    )
    provider_reference: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    provider_checkout_url: Mapped[str] = mapped_column(String(500), nullable=True)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False, server_default="USD")
    status: Mapped[PaymentStatus] = mapped_column(
        Enum(PaymentStatus, native_enum=False, values_callable=lambda enum: [item.value for item in enum]),
        nullable=False,
        default=PaymentStatus.PENDING,
        server_default=PaymentStatus.PENDING.value,
    )
    provider_response: Mapped[dict] = mapped_column(JSON, nullable=True)
    verified_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    order = relationship("Order", lazy="selectin")
