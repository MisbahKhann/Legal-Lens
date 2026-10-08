"""
Deterministic Date Normalizer for US Legal Date Formats and Precision Tracking.
"""

import re
import calendar
from datetime import datetime
from typing import Optional, Tuple

import dateparser
from app.temporal.models import NormalizedDate, DatePrecision

# Month RegEx pattern
MONTHS_OR = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"
MONTH_NAME_TO_INT = {
    "january": 1,
    "jan": 1,
    "february": 2,
    "feb": 2,
    "march": 3,
    "mar": 3,
    "april": 4,
    "apr": 4,
    "may": 5,
    "june": 6,
    "jun": 6,
    "july": 7,
    "jul": 7,
    "august": 8,
    "aug": 8,
    "september": 9,
    "sep": 9,
    "sept": 9,
    "october": 10,
    "oct": 10,
    "november": 11,
    "nov": 11,
    "december": 12,
    "dec": 12,
}

# Regex patterns for range detection
RANGE_PATTERNS = [
    # "January 5, 2024 to January 10, 2024" or "from March 1, 2023 through March 15, 2023"
    re.compile(
        r"(?:from\s+)?(?P<start>.+?)\s+(?:to|through|until|-)\s+(?P<end>.+)",
        re.IGNORECASE,
    )
]

# Month-only patterns (e.g. "March 2024", "Mar 2024", "March, 2024")
MONTH_YEAR_PATTERN = re.compile(
    r"^\s*(?:in\s+)?(?P<month>" + MONTHS_OR + r")[\.,\s]+(?P<year>\d{4})\s*$",
    re.IGNORECASE,
)

# Year-only pattern (e.g. "2024", "in 2024")
YEAR_ONLY_PATTERN = re.compile(
    r"^\s*(?:in\s+|FY\s*|fiscal\s+year\s*)?(?P<year>\d{4})\s*$",
    re.IGNORECASE,
)


class DateNormalizer:
    """
    Normalizes legal date expressions into ISO 8601 strings with explicit precision and calendar validation.
    """

    @staticmethod
    def is_valid_calendar_date(year: int, month: int, day: int) -> bool:
        """Validates whether (year, month, day) forms a valid calendar date."""
        if month < 1 or month > 12 or day < 1 or day > 31:
            return False
        max_days = calendar.monthrange(year, month)[1]
        return day <= max_days

    def normalize(self, raw_text: str) -> NormalizedDate:
        """
        Parses and normalizes a raw date expression.

        Args:
            raw_text: Raw string containing a date expression.

        Returns:
            NormalizedDate instance with ISO format, precision, and validation flags.
        """
        cleaned_text = raw_text.strip()
        if not cleaned_text:
            return NormalizedDate(
                raw_text=raw_text,
                is_valid=False,
                validation_note="Empty date text",
                precision=DatePrecision.UNKNOWN_PARTIAL,
            )

        # 1. Check for Date Ranges first (e.g. "January 5, 2024 to January 10, 2024")
        for r_pat in RANGE_PATTERNS:
            match = r_pat.match(cleaned_text)
            if match:
                start_part = match.group("start").strip()
                end_part = match.group("end").strip()

                norm_start = self._normalize_single_date(start_part)
                norm_end = self._normalize_single_date(end_part)

                if (
                    norm_start.is_valid
                    and norm_end.is_valid
                    and (norm_start.iso_value or norm_end.iso_value)
                ):
                    return NormalizedDate(
                        raw_text=raw_text,
                        iso_value=norm_start.iso_value or norm_end.iso_value,
                        start_date=norm_start.iso_value,
                        end_date=norm_end.iso_value,
                        precision=norm_start.precision,
                        year=norm_start.year,
                        month=norm_start.month,
                        day=norm_start.day,
                        is_valid=True,
                    )

        # 2. Check single date normalization
        return self._normalize_single_date(cleaned_text)

    def _normalize_single_date(self, text: str) -> NormalizedDate:
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", text, flags=re.IGNORECASE)
        cleaned = re.sub(r"day\s+of\s+", "", cleaned, flags=re.IGNORECASE)
        cleaned_str = cleaned.strip()

        # Check Month-Year pattern (e.g., "March 2024")
        m_match = MONTH_YEAR_PATTERN.match(cleaned_str)
        if m_match:
            month_str = m_match.group("month").lower()
            year_val = int(m_match.group("year"))
            month_val = MONTH_NAME_TO_INT.get(month_str)
            if month_val:
                iso_str = f"{year_val:04d}-{month_val:02d}"
                return NormalizedDate(
                    raw_text=text,
                    iso_value=iso_str,
                    precision=DatePrecision.MONTH,
                    year=year_val,
                    month=month_val,
                    is_valid=True,
                )

        # Check Year-Only pattern (e.g., "2024")
        y_match = YEAR_ONLY_PATTERN.match(cleaned_str)
        if y_match:
            year_val = int(y_match.group("year"))
            if 1800 <= year_val <= 2100:
                iso_str = f"{year_val:04d}"
                return NormalizedDate(
                    raw_text=text,
                    iso_value=iso_str,
                    precision=DatePrecision.YEAR,
                    year=year_val,
                    is_valid=True,
                )

        # Direct explicit date regex extraction for calendar validation before dateparser
        # E.g. "February 30, 2024" or "02/30/2024"
        d_match = re.search(
            r"\b(?P<month>"
            + MONTHS_OR
            + r")[\.,\s]+(?P<day>\d{1,2})[\.,\s]+(?P<year>\d{4})\b",
            text,
            re.IGNORECASE,
        )
        if d_match:
            m_name = d_match.group("month").lower()
            d_val = int(d_match.group("day"))
            y_val = int(d_match.group("year"))
            m_val = MONTH_NAME_TO_INT.get(m_name)
            if m_val:
                if not self.is_valid_calendar_date(y_val, m_val, d_val):
                    return NormalizedDate(
                        raw_text=text,
                        iso_value=f"{y_val:04d}-{m_val:02d}-{d_val:02d}",
                        precision=DatePrecision.EXACT_DAY,
                        year=y_val,
                        month=m_val,
                        day=d_val,
                        is_valid=False,
                        validation_note=f"Invalid calendar date: day {d_val} out of range for month {m_val} in year {y_val}.",
                    )

        # Check numeric slash format e.g. "02/30/2024" or "15/01/2024"
        slash_match = re.search(r"\b(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<y>\d{4})\b", text)
        if slash_match:
            m_val = int(slash_match.group("m"))
            d_val = int(slash_match.group("d"))
            y_val = int(slash_match.group("y"))
            if not self.is_valid_calendar_date(y_val, m_val, d_val):
                return NormalizedDate(
                    raw_text=text,
                    iso_value=f"{y_val:04d}-{m_val:02d}-{d_val:02d}",
                    precision=DatePrecision.EXACT_DAY,
                    year=y_val,
                    month=m_val,
                    day=d_val,
                    is_valid=False,
                    validation_note=f"Invalid calendar date: {m_val}/{d_val}/{y_val}.",
                )

        # Parse full date using dateparser
        try:
            parsed = dateparser.parse(
                cleaned_str,
                settings={
                    "PREFER_DAY_OF_MONTH": "first",
                    "REQUIRE_PARTS": ["year", "month", "day"],
                    "DATE_ORDER": "MDY",
                },
            )
            if parsed and 1800 <= parsed.year <= 2100:
                iso_str = parsed.strftime("%Y-%m-%d")
                return NormalizedDate(
                    raw_text=text,
                    iso_value=iso_str,
                    precision=DatePrecision.EXACT_DAY,
                    year=parsed.year,
                    month=parsed.month,
                    day=parsed.day,
                    is_valid=True,
                )
        except Exception as e:
            pass

        return NormalizedDate(
            raw_text=text,
            is_valid=False,
            validation_note=f"Could not parse date expression: '{text}'",
            precision=DatePrecision.UNKNOWN_PARTIAL,
        )
