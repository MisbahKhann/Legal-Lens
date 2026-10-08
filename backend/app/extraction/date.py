"""
Deterministic Legal Date Extractor with ISO 8601 Normalization.
Extracts common legal date formats (e.g., January 15, 2024, 15th day of January 2024, 01/15/2024, 2024-01-15).
"""

import re
from datetime import datetime
from typing import List, Optional
import dateparser

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

# Standard Month Names
MONTHS_OR = r"(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)"

# Date regex patterns tailored for legal document expressions
DATE_PATTERNS = [
    # "15th day of January, 2024" or "1st day of May 2023"
    re.compile(
        r"\b(?P<day>\d{1,2})(?:st|nd|rd|th)?\s+day\s+of\s+(?P<month>"
        + MONTHS_OR
        + r")[\.,\s]+(?P<year>\d{4})\b",
        re.IGNORECASE,
    ),
    # "January 15, 2024", "Jan 15, 2024", "January 15th, 2024"
    re.compile(
        r"\b(?P<month>"
        + MONTHS_OR
        + r")[\.,\s]+(?P<day>\d{1,2})(?:st|nd|rd|th)?[\.,\s]+(?P<year>\d{4})\b",
        re.IGNORECASE,
    ),
    # "15 January 2024", "15 Jan 2024"
    re.compile(
        r"\b(?P<day>\d{1,2})[\.,\s]+(?P<month>"
        + MONTHS_OR
        + r")[\.,\s]+(?P<year>\d{4})\b",
        re.IGNORECASE,
    ),
    # Numeric ISO format "2024-01-15"
    re.compile(r"\b(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})\b"),
    # US Numeric format "01/15/2024" or "1/15/2024"
    re.compile(r"\b(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})\b"),
    # Prefix dates like "Dated: October 5, 2023" (captured by pattern 2 as well)
]


class DateExtractor(BaseExtractor):
    """
    Extracts calendar date expressions from legal text and normalizes them to ISO 8601 (YYYY-MM-DD).
    """

    @property
    def name(self) -> str:
        return "date_extractor"

    @property
    def category(self) -> str:
        return "date"

    def _normalize_date(self, date_str: str) -> Optional[str]:
        """Attempt robust parsing to YYYY-MM-DD using dateparser / datetime."""
        # Clean ordinals (1st -> 1, 15th -> 15) and "day of"
        cleaned = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", date_str, flags=re.IGNORECASE)
        cleaned = re.sub(r"day\s+of\s+", "", cleaned, flags=re.IGNORECASE)

        try:
            parsed = dateparser.parse(
                cleaned,
                settings={
                    "PREFER_DAY_OF_MONTH": "first",
                    "REQUIRE_PARTS": ["year", "month", "day"],
                    "DATE_ORDER": "MDY",
                },
            )
            if parsed and 1800 <= parsed.year <= 2100:
                return parsed.strftime("%Y-%m-%d")
        except Exception:
            pass

        return None

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            extracted_spans = set()

            for pattern in DATE_PATTERNS:
                for match in pattern.finditer(text):
                    start, end = match.span()

                    # Avoid duplicate overlapping extractions on the same page
                    if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                        continue

                    raw_match = match.group(0).strip()
                    iso_date = self._normalize_date(raw_match)

                    if not iso_date:
                        continue

                    extracted_spans.add((start, end))

                    # Context snippet
                    snippet_start = max(0, start - 30)
                    snippet_end = min(len(text), end + 30)
                    snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

                    candidates.append(
                        ExtractedCandidateEntity(
                            document_id=document.document_id,
                            case_id=document.case_id,
                            page_number=page.page_number,
                            source_text=snippet,
                            char_span=(start, end),
                            extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                            rule_name="legal_date_pattern",
                            confidence=0.96,
                            entity_type=EntityType.DATE,
                            category=self.category,
                            original_value=raw_match,
                            normalized_value=iso_date,
                            metadata={
                                "iso_format": iso_date,
                                "raw_expression": raw_match,
                            },
                        )
                    )

        return candidates
