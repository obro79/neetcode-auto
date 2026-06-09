from datetime import date, datetime

from sqlalchemy import JSON, Boolean, Date, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class JobDigestLog(Base):
    __tablename__ = "job_digest_logs"
    __table_args__ = (
        UniqueConstraint("digest_date", "slot", name="uq_job_digest_date_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_date: Mapped[date] = mapped_column(Date, index=True)
    slot: Mapped[int] = mapped_column(Integer)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    resend_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    listing_ids: Mapped[list] = mapped_column(JSON, default=list)
    new_listing_ids: Mapped[list] = mapped_column(JSON, default=list)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
