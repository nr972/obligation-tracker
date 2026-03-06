"""Contract ORM model."""

from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ot_app.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    counterparty: Mapped[str] = mapped_column(String(500), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(100), nullable=False)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notice_period_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    file_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    health_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    obligations: Mapped[list["Obligation"]] = relationship(  # noqa: F821
        back_populates="contract", cascade="all, delete-orphan"
    )
