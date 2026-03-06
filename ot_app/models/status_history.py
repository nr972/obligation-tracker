"""Status history ORM model for obligation audit trail."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ot_app.database import Base


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    obligation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("obligations.id", ondelete="CASCADE"), nullable=False
    )
    old_status: Mapped[str] = mapped_column(String(20), nullable=False)
    new_status: Mapped[str] = mapped_column(String(20), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    obligation: Mapped["Obligation"] = relationship(  # noqa: F821
        back_populates="status_history"
    )
