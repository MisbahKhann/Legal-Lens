"""
Deterministic Statutory and Regulatory Citation Extractor.
Extracts references like 42 U.S.C. § 1983, 18 U.S.C. § 1001, 28 U.S.C. § 1331, 12 C.F.R. § 226.1, etc.
"""

import re
from typing import List, Dict, Any

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

# Federal U.S. Code & C.F.R. pattern
USC_CFR_PATTERN = re.compile(
    r"\b(?P<title>\d+)\s+"
    r"(?P<code>U\.?\s*S\.?\s*C\.?|C\.?\s*F\.?\s*R\.?)\s*"
    r"(?:App\.?\s*)?"
    r"(?:(?:§+|Sec(?:tion|\.)?)\s*)?"
    r"(?P<section>\d+[a-zA-Z0-9\-\.\(\)]*)",
    re.IGNORECASE,
)

# State Code / Statute pattern
STATE_STATUTE_PATTERN = re.compile(
    r"\b(?P<code>[A-Z][a-zA-Z\.\s]{1,25}(?:Stat|Code|Law|Act|Regs)\.?)\s*"
    r"(?:§+|Sec(?:tion|\.)?)\s*"
    r"(?P<section>\d+[a-zA-Z0-9\-\.\(\)]*)"
)


class StatutoryCitationExtractor(BaseExtractor):
    """
    Extracts statutory and regulatory citations (U.S. Code, C.F.R., State Statutes).
    """

    @property
    def name(self) -> str:
        return "statutory_citation_extractor"

    @property
    def category(self) -> str:
        return "statutory_citation"

    def _clean_section(self, section: str) -> str:
        """Strip trailing sentence punctuation from section strings."""
        return section.rstrip(".,;:)")

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            # Process U.S. Code & C.F.R.
            for match in USC_CFR_PATTERN.finditer(text):
                start, end = match.span()
                raw_match = match.group(0)

                title = match.group("title").strip()
                code_raw = (
                    match.group("code").upper().replace(" ", "").replace(".", ". ")
                )
                if "CFR" in code_raw.replace(" ", "").replace(".", ""):
                    code_norm = "C.F.R."
                    entity_type = EntityType.REGULATION
                else:
                    code_norm = "U.S.C."
                    entity_type = EntityType.STATUTE

                section = self._clean_section(match.group("section"))
                if not section:
                    continue

                # Adjust end index if trailing punctuation was stripped
                if raw_match.endswith((".", ",", ";", ":")) and not section.endswith(
                    raw_match[-1]
                ):
                    raw_match = raw_match.rstrip(".,;:")
                    end = start + len(raw_match)

                normalized_val = f"{title} {code_norm} § {section}"

                # Context snippet
                snippet_start = max(0, start - 40)
                snippet_end = min(len(text), end + 40)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

                metadata = {
                    "title_number": title,
                    "code": code_norm,
                    "section": section,
                    "jurisdiction": "US_FEDERAL",
                }

                candidates.append(
                    ExtractedCandidateEntity(
                        document_id=document.document_id,
                        case_id=document.case_id,
                        page_number=page.page_number,
                        source_text=snippet,
                        char_span=(start, end),
                        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                        rule_name="usc_cfr_statute_pattern",
                        confidence=0.98,
                        entity_type=entity_type,
                        category=self.category,
                        original_value=raw_match,
                        normalized_value=normalized_val,
                        metadata=metadata,
                    )
                )

            # Process State Statutes
            for match in STATE_STATUTE_PATTERN.finditer(text):
                start, end = match.span()

                if any(
                    c.char_span
                    and not (end <= c.char_span[0] or start >= c.char_span[1])
                    for c in candidates
                ):
                    continue

                raw_match = match.group(0)
                code_raw = match.group("code").strip()
                section = self._clean_section(match.group("section"))
                if not section:
                    continue

                if raw_match.endswith((".", ",", ";", ":")) and not section.endswith(
                    raw_match[-1]
                ):
                    raw_match = raw_match.rstrip(".,;:")
                    end = start + len(raw_match)

                normalized_val = f"{code_raw} § {section}"

                snippet_start = max(0, start - 40)
                snippet_end = min(len(text), end + 40)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

                candidates.append(
                    ExtractedCandidateEntity(
                        document_id=document.document_id,
                        case_id=document.case_id,
                        page_number=page.page_number,
                        source_text=snippet,
                        char_span=(start, end),
                        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                        rule_name="state_statute_pattern",
                        confidence=0.90,
                        entity_type=EntityType.STATUTE,
                        category=self.category,
                        original_value=raw_match,
                        normalized_value=normalized_val,
                        metadata={
                            "code": code_raw,
                            "section": section,
                            "jurisdiction": "US_STATE",
                        },
                    )
                )

        return candidates
