from typing import TYPE_CHECKING

from sqlalchemy import Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.enums import Difficulty, enum_values
from app.models.base import Base

if TYPE_CHECKING:
    from app.models.daily_set import DailySetItem
    from app.models.user_progress import UserProgress


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(256))
    pattern: Mapped[str] = mapped_column(String(128), index=True)
    difficulty: Mapped[Difficulty] = mapped_column(
        Enum(Difficulty, name="difficulty", values_callable=enum_values)
    )
    leetcode_url: Mapped[str] = mapped_column(Text)
    neetcode_url: Mapped[str] = mapped_column(Text)
    sort_order: Mapped[int] = mapped_column(Integer, index=True)

    progress: Mapped["UserProgress"] = relationship(
        back_populates="problem",
        uselist=False,
    )
    daily_set_items: Mapped[list["DailySetItem"]] = relationship(back_populates="problem")
