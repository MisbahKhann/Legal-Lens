"""
Deterministic Court Exhibit Extractor.
Extracts references like Exhibit A, Exhibit 12, Ex. B, Exhibit A-1, Pl. Ex. 3, Def. Ex. A, etc.
"""

import re
from typing import List

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

EXHIBIT_PATTERN = re.compile(
    r"\b(?P<party>Plaintiff\'s|Defendant\'s|Pl\.|Def\.|Trial|Joint)?\s*"
    r"(?:Exhibit|Ex\.)\s*"
    r"(?P<label>[A-Za-z0-9]+(?:[\-\.][A-Za-z0-9]+)?)",
    re.IGNORECASE,
)


class ExhibitExtractor(BaseExtractor):
    """
    Extracts documentary exhibit designations referenced in legal documents.
    """

    @property
    def name(self) -> str:
        return "exhibit_extractor"

    @property
    def category(self) -> str:
        return "exhibit"

    def _normalize_exhibit(self, party: str, label: str) -> str:
        label_clean = label.strip().upper()
        if not party:
            return f"Exhibit {label_clean}"

        party_clean = party.lower().strip()
        if "pl" in party_clean:
            return f"Exhibit {label_clean} (Plaintiff)"
        elif "def" in party_clean:
            return f"Exhibit {label_clean} (Defendant)"
        elif "trial" in party_clean:
            return f"Exhibit {label_clean} (Trial)"
        elif "joint" in party_clean:
            return f"Exhibit {label_clean} (Joint)"

        return f"Exhibit {label_clean}"

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            extracted_spans = set()

            for match in EXHIBIT_PATTERN.finditer(text):
                start, end = match.span()

                if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                    continue

                party = match.group("party") or ""
                label = match.group("label") or ""

                if not label:
                    continue

                raw_match = match.group(0).strip()
                normalized_val = self._normalize_exhibit(party, label)

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
                        rule_name="exhibit_designation_pattern",
                        confidence=0.96,
                        entity_type=EntityType.EXHIBIT,
                        category=self.category,
                        original_value=raw_match,
                        normalized_value=normalized_val,
                        metadata={"label": label.upper(), "party": party},
                    )
                )

        return candidates
