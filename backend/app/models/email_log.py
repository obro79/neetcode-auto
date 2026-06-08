from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class EmailLog(Base):
    __tablename__ = "email_log"
    __table_args__ = (
        UniqueConstraint("set_date", "attempt", name="uq_email_log_set_date_attempt"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    set_date: Mapped[date] = mapped_column(Date, index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempt: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    resend_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
