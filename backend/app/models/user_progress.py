from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Confidence, DailySlot, ReviewStage, enum_values
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.problem import Problem


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (UniqueConstraint("problem_id", name="uq_user_progress_problem"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    solved: Mapped[bool] = mapped_column(Boolean, default=False)
    review_stage: Mapped[ReviewStage] = mapped_column(
        Enum(ReviewStage, name="review_stage", values_callable=enum_values),
        default=ReviewStage.NEW,
    )
    next_review: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_practiced: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[Confidence | None] = mapped_column(
        Enum(Confidence, name="confidence", values_callable=enum_values),
        nullable=True,
    )
    daily_slot: Mapped[DailySlot | None] = mapped_column(
        Enum(DailySlot, name="daily_slot", values_callable=enum_values),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    problem: Mapped["Problem"] = relationship(back_populates="progress")
