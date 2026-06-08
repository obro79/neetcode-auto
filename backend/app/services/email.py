import asyncio

import resend

from app.core.config import get_settings
from app.core.srs_config import get_srs_config
from app.schemas.daily_set import DailySetOut


def _render_section(title: str, items: list, focus_pattern: str | None = None) -> str:
    lines = [f"<h2>{title}</h2>"]
    if focus_pattern and title == "Focused New":
        lines.append(f"<p><strong>Focus pattern:</strong> {focus_pattern}</p>")
    if not items:
        lines.append("<p><em>No problems selected.</em></p>")
        return "\n".join(lines)

    lines.append("<ol>")
    for item in items:
        done_marker = " ✓" if item.completed else ""
        style = ' style="text-decoration: line-through; color: #666;"' if item.completed else ""
        lines.append(
            f"<li{style}>"
            f"{item.title}{done_marker} | {item.pattern} | {item.difficulty.value.title()} | "
            f'<a href="{item.neetcode_url}">NeetCode</a> | '
            f'<a href="{item.leetcode_url}">LeetCode</a>'
            "</li>"
        )
    lines.append("</ol>")
    return "\n".join(lines)


def build_daily_email_html(daily_set: DailySetOut) -> str:
    sections = [
        f"<p><strong>Date:</strong> {daily_set.set_date}</p>",
        _render_section("Review", daily_set.review),
        _render_section("Focused New", daily_set.focused_new, daily_set.focus_pattern),
        _render_section("Random New", daily_set.random_new),
    ]
    return "\n".join(sections)


def build_daily_email_text(daily_set: DailySetOut) -> str:
    lines = [f"Date: {daily_set.set_date}", ""]

    def add_section(title: str, items: list) -> None:
        lines.append(f"## {title}")
        if title == "Focused New" and daily_set.focus_pattern:
            lines.append(f"Focus pattern: {daily_set.focus_pattern}")
        if not items:
            lines.append("No problems selected.")
            lines.append("")
            return
        for index, item in enumerate(items, start=1):
            done_marker = " [done]" if item.completed else ""
            lines.append(
                f"{index}. {item.title}{done_marker} | {item.pattern} | "
                f"{item.difficulty.value.title()} | "
                f"NeetCode: {item.neetcode_url} | LeetCode: {item.leetcode_url}"
            )
        lines.append("")

    add_section("Review", daily_set.review)
    add_section("Focused New", daily_set.focused_new)
    add_section("Random New", daily_set.random_new)
    return "\n".join(lines)


def _send_daily_email_sync(daily_set: DailySetOut) -> str:
    settings = get_settings()
    srs = get_srs_config()
    resend.api_key = settings.resend_api_key

    subject = f"Daily NeetCode Set - {daily_set.set_date}"
    response = resend.Emails.send(
        {
            "from": settings.email_from or srs.email.from_address,
            "to": [settings.email_to or srs.email.to],
            "subject": subject,
            "html": build_daily_email_html(daily_set),
            "text": build_daily_email_text(daily_set),
        }
    )
    return response.get("id", "sent")


async def send_daily_email(daily_set: DailySetOut) -> str:
    return await asyncio.to_thread(_send_daily_email_sync, daily_set)
