from __future__ import annotations

import re
from dataclasses import dataclass

CATEGORY_MAP: dict[str, set[str]] = {
    "software_engineering": {
        "Software",
        "Software Engineering",
    },
    "data_science_ai_ml": {
        "AI/ML/Data",
        "Data Science, AI & Machine Learning",
    },
    "quantitative_finance": {
        "Quant",
        "Quantitative Finance",
    },
    "product_management": {
        "Product",
        "Product Management",
    },
    "hardware_engineering": {
        "Hardware",
        "Hardware Engineering",
    },
}

US_STATE_PATTERN = re.compile(
    r",\s*(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|"
    r"MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY|DC)\b"
)
CANADA_PATTERN = re.compile(
    r",\s*(ON|BC|AB|QC|MB|SK|NS|NB|NL|PE|NT|YT|NU)\b|Canada",
    re.IGNORECASE,
)
NO_SPONSORSHIP_MARKERS = ("🛂", "does not offer sponsorship", "no sponsorship")
US_CITIZEN_MARKERS = ("🇺🇸", "u.s. citizenship", "us citizenship")


@dataclass(frozen=True)
class ListingRecord:
    id: str
    company_name: str
    title: str
    locations: list[str]
    terms: list[str]
    url: str
    category: str
    date_posted: int | None
    active: bool
    sponsorship: str | None
    is_visible: bool


def normalize_category(raw_category: str) -> str:
    return raw_category.strip()


def infer_category_key(raw_category: str) -> str | None:
    normalized = normalize_category(raw_category)
    for key, labels in CATEGORY_MAP.items():
        if normalized in labels:
            return key
    lowered = normalized.lower()
    if "product" in lowered:
        return "product_management"
    if "quant" in lowered:
        return "quantitative_finance"
    if any(token in lowered for token in ("data", "ml", "ai")):
        return "data_science_ai_ml"
    if "hardware" in lowered:
        return "hardware_engineering"
    if "software" in lowered:
        return "software_engineering"
    return None


def title_has_no_sponsorship(title: str) -> bool:
    lowered = title.lower()
    return any(marker in lowered for marker in NO_SPONSORSHIP_MARKERS)


def title_requires_us_citizen(title: str) -> bool:
    lowered = title.lower()
    return any(marker in lowered for marker in US_CITIZEN_MARKERS)


def is_north_america_location(location: str) -> bool:
    if not location:
        return False
    if "remote" in location.lower():
        return True
    if US_STATE_PATTERN.search(location):
        return True
    if CANADA_PATTERN.search(location):
        return True
    if ", USA" in location or ", US" in location:
        return True
    return False


def listing_document_text(company_name: str, title: str, locations: list[str]) -> str:
    return " ".join([company_name, title, " ".join(locations)]).lower()
