"""
Deterministic Docket and Case Number Extractor.
Extracts docket numbers like No. 24-CV-1234, 3:24-cv-00123, Civil Action No. 1:20-cv-09876, Case No. 2:23-cr-00456, etc.
"""

import re
from typing import List

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

DOCKET_PATTERNS = [
    # Federal Divisional format e.g. "3:24-cv-00123", "1:20-cv-09876-ABC", "Case No. 2:23-cr-00456"
    re.compile(
        r"\b(?:(?:Case|Civil Action|Docket|Misc\.)\s+)?(?:No\.|#)?\s*"
        r"(?P<docket>\d{1,2}:\d{2}-(?:cv|cr|mc|md|bk|ap)-\d{4,7}(?:-[A-Za-z0-9]+)?)\b",
        re.IGNORECASE,
    ),
    # Prefixed hyphenated format e.g. "No. 24-CV-1234", "Civil Action No. 2024-CV-0098", "Docket No. 22-1543"
    re.compile(
        r"\b(?:Case|Civil Action|Docket|Civil|Criminal)\s+(?:No\.|#)\s*"
        r"(?P<docket>[A-Za-z0-9]{1,4}[-–][A-Za-z0-9]{2,6}[-–][A-Za-z0-9]{2,7}|[0-9]{2,4}[-–][A-Za-z]{2,4}[-–][0-9]{3,6}|[0-9]{2,4}[-–][0-9]{4,7})\b",
        re.IGNORECASE,
    ),
    # Standalone "No. 24-CV-1234"
    re.compile(
        r"\bNo\.\s*(?P<docket>[0-9]{2,4}-[A-Z]{2,4}-[0-9]{3,6}|[0-9]{2,4}-[0-9]{4,7})\b",
        re.IGNORECASE,
    ),
]


class DocketExtractor(BaseExtractor):
    """
    Extracts court docket and case numbers using pattern matching.
    """

    @property
    def name(self) -> str:
        return "docket_extractor"

    @property
    def category(self) -> str:
        return "docket_number"

    def _normalize_docket(self, raw_docket: str) -> str:
        """Standardize docket string to upper-case without leading 'No.' prefixes."""
        cleaned = re.sub(
            r"^(?:Case|Civil Action|Docket|Misc\.|Civil|Criminal|No\.|#|\s)+",
            "",
            raw_docket,
            flags=re.IGNORECASE,
        ).strip()
        cleaned = cleaned.replace("–", "-")
        return cleaned.upper()

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            extracted_spans = set()

            for pattern in DOCKET_PATTERNS:
                for match in pattern.finditer(text):
                    start, end = match.span()

                    if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                        continue

                    raw_match = match.group(0).strip()
                    docket_val = match.group("docket").strip()
                    normalized_docket = self._normalize_docket(docket_val)

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
                            rule_name="docket_pattern",
                            confidence=0.97,
                            entity_type=EntityType.CASE,
                            category=self.category,
                            original_value=raw_match,
                            normalized_value=normalized_docket,
                            metadata={"docket_number": normalized_docket},
                        )
                    )

        return candidates
