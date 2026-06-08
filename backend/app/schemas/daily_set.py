from pydantic import BaseModel, ConfigDict

from app.enums import DailySlot, Difficulty


class DailySetItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    slug: str
    title: str
    pattern: str
    difficulty: Difficulty
    leetcode_url: str
    neetcode_url: str
    slot: DailySlot
    completed: bool = False


class DailySetOut(BaseModel):
    set_date: str
    focus_pattern: str | None
    review: list[DailySetItemOut]
    focused_new: list[DailySetItemOut]
    random_new: list[DailySetItemOut]


class SendDailyResponse(BaseModel):
    set_date: str
    attempt: int
    sent: bool
    message: str
