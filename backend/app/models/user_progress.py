from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Confidence, DailySlot, ReviewStage
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
        Enum(ReviewStage, name="review_stage"),
        default=ReviewStage.NEW,
    )
    next_review: Mapped[date | None] = mapped_column(Date, nullable=True)
    last_practiced: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[Confidence | None] = mapped_column(
        Enum(Confidence, name="confidence"),
        nullable=True,
    )
    daily_slot: Mapped[DailySlot | None] = mapped_column(
        Enum(DailySlot, name="daily_slot"),
        nullable=True,
    )

    problem: Mapped["Problem"] = relationship(back_populates="progress")
