from enum import StrEnum


class ReviewStage(StrEnum):
    NEW = "new"
    ONE_DAY = "1d"
    THREE_DAY = "3d"
    SEVEN_DAY = "7d"
    FOURTEEN_DAY = "14d"
    THIRTY_DAY = "30d"
    MASTERED = "mastered"


class Confidence(StrEnum):
    STRUGGLING = "struggling"
    GETTING_THERE = "getting_there"
    SOLID = "solid"


class DailySlot(StrEnum):
    REVIEW = "review"
    FOCUSED_NEW = "focused_new"
    RANDOM_NEW = "random_new"
    DONE = "done"


class Difficulty(StrEnum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


STAGE_PROGRESSION: list[ReviewStage] = [
    ReviewStage.NEW,
    ReviewStage.ONE_DAY,
    ReviewStage.THREE_DAY,
    ReviewStage.SEVEN_DAY,
    ReviewStage.FOURTEEN_DAY,
    ReviewStage.THIRTY_DAY,
    ReviewStage.MASTERED,
]

STAGE_INTERVALS: dict[ReviewStage, int | None] = {
    ReviewStage.ONE_DAY: 1,
    ReviewStage.THREE_DAY: 3,
    ReviewStage.SEVEN_DAY: 7,
    ReviewStage.FOURTEEN_DAY: 14,
    ReviewStage.THIRTY_DAY: 30,
    ReviewStage.MASTERED: None,
}

CONFIDENCE_PRIORITY: dict[Confidence, int] = {
    Confidence.STRUGGLING: 0,
    Confidence.GETTING_THERE: 1,
    Confidence.SOLID: 2,
}

DIFFICULTY_ORDER: dict[Difficulty, int] = {
    Difficulty.EASY: 0,
    Difficulty.MEDIUM: 1,
    Difficulty.HARD: 2,
}

FOCUS_PATTERN_ORDER: list[str] = [
    "Advanced Graphs",
    "Math & Geometry",
    "Greedy",
    "Tries",
]

EXCLUDED_PATTERNS: set[str] = {
    "Linked List",
    "2-D Dynamic Programming",
}
