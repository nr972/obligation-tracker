"""Obligation ORM model."""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ot_app.database import Base


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    obligation_type: Mapped[str] = mapped_column(String(100), nullable=False)
    responsible_party: Mapped[str] = mapped_column(String(200), nullable=False)
    deadline_type: Mapped[str] = mapped_column(String(50), nullable=False)
    deadline_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    recurrence_pattern: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    penalty: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    extraction_source: Mapped[str] = mapped_column(String(20), nullable=False)
    source_section: Mapped[str | None] = mapped_column(String(200), nullable=True)
    source_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    contract: Mapped["Contract"] = relationship(back_populates="obligations")  # noqa: F821
    status_history: Mapped[list["StatusHistory"]] = relationship(  # noqa: F821
        back_populates="obligation", cascade="all, delete-orphan"
    )
