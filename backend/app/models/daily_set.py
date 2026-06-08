from datetime import date, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Enum, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import DailySlot, enum_values
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.problem import Problem


class DailySet(Base):
    __tablename__ = "daily_sets"
    __table_args__ = (UniqueConstraint("set_date", name="uq_daily_sets_set_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    set_date: Mapped[date] = mapped_column(Date, unique=True, index=True)
    focus_pattern: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    items: Mapped[list["DailySetItem"]] = relationship(
        back_populates="daily_set",
        cascade="all, delete-orphan",
    )


class DailySetItem(Base):
    __tablename__ = "daily_set_items"
    __table_args__ = (
        UniqueConstraint("daily_set_id", "problem_id", name="uq_daily_set_problem"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    daily_set_id: Mapped[int] = mapped_column(ForeignKey("daily_sets.id"), index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), index=True)
    slot: Mapped[DailySlot] = mapped_column(
        Enum(DailySlot, name="daily_slot_item", values_callable=enum_values)
    )

    daily_set: Mapped["DailySet"] = relationship(back_populates="items")
    problem: Mapped["Problem"] = relationship(back_populates="daily_set_items")
