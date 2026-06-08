from app.enums import DailySlot, Difficulty
from app.schemas.daily_set import DailySetItemOut, DailySetOut
from app.services.email import build_daily_email_html, build_daily_email_text


def test_build_daily_email_contains_sections() -> None:
    daily_set = DailySetOut(
        set_date="2026-06-07",
        focus_pattern="Greedy",
        review=[
            DailySetItemOut(
                slug="two-sum",
                title="Two Sum",
                pattern="Arrays & Hashing",
                difficulty=Difficulty.EASY,
                leetcode_url="https://leetcode.com/problems/two-sum/",
                neetcode_url="https://neetcode.io/problems/two-sum",
                slot=DailySlot.REVIEW,
            )
        ],
        focused_new=[],
        random_new=[],
    )
    html = build_daily_email_html(daily_set)
    text = build_daily_email_text(daily_set)
    assert "Review" in html
    assert "Two Sum" in html
    assert "Daily NeetCode Set" not in html
    assert "Two Sum" in text
    assert "Greedy" in text
