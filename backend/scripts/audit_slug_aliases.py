"""Audit LeetCode URL slugs vs NeetCode catalog slugs and suggest aliases."""

from __future__ import annotations

import json
import re
from urllib.parse import urlparse

from app.core.srs_config import get_srs_config

LEETCODE_SLUG_RE = re.compile(r"/problems/([^/]+)/?")


def leetcode_slug(url: str) -> str | None:
    path = urlparse(url).path
    match = LEETCODE_SLUG_RE.search(path)
    return match.group(1) if match else None


def main() -> None:
    config = get_srs_config()
    catalog_path = config.resolve_catalog_path()
    payload = json.loads(catalog_path.read_text(encoding="utf-8"))

    mismatches: list[tuple[str, str, str]] = []
    for item in payload["problems"]:
        catalog_slug = item["slug"]
        lc_slug = leetcode_slug(item["leetcode_url"])
        if lc_slug and lc_slug != catalog_slug:
            mismatches.append((lc_slug, catalog_slug, item["name"]))

    configured = config.slug_aliases
    missing = [(lc, cat, name) for lc, cat, name in mismatches if configured.get(lc) != cat]

    print(f"Catalog: {catalog_path}")
    print(f"Total slug mismatches (LeetCode URL vs catalog): {len(mismatches)}")
    print(f"Missing or incorrect in slug_aliases: {len(missing)}")
    print()

    if missing:
        print("Suggested slug_aliases entries:")
        for lc, cat, name in sorted(missing):
            print(f"  {lc}: {cat}  # {name}")
    else:
        print("All mismatches are covered by slug_aliases.")


if __name__ == "__main__":
    main()
