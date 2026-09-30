"""
Deterministic Legal Section, Article, and Clause Reference Extractor.
Extracts references like § 1983, Section 12, Article III, Sec. 4(a), Clause 2, Art. I, etc.
"""

import re
from typing import List

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity


SECTION_PATTERNS = [
    # Section symbol references: "§ 1983", "§§ 101-105"
    re.compile(
        r'(?:^|[\s\(\[\{,;])(?P<prefix>§+)\s*(?P<num>\d+[a-zA-Z0-9\-\.\(\)]*)',
        re.IGNORECASE
    ),

    # Named section references: "Section 12", "Sec. 4(a)"
    re.compile(
        r'\b(?P<prefix>Sec(?:tion|\.)?)\s*(?P<num>\d+[a-zA-Z0-9\-\.\(\)]*)',
        re.IGNORECASE
    ),

    # Article references: "Article III", "Art. I", "Article 5"
    re.compile(
        r'\b(?P<prefix>Article|Art\.)\s*(?P<num>[IVXLCDM\d]+[a-zA-Z0-9\-\.\(\)]*)',
        re.IGNORECASE
    ),

    # Clause references: "Clause 2", "Cl. 1"
    re.compile(
        r'\b(?P<prefix>Clause|Cl\.)\s*(?P<num>\d+[a-zA-Z0-9\-\.\(\)]*)',
        re.IGNORECASE
    )
]


class SectionExtractor(BaseExtractor):
    """
    Extracts structural legal section, article, and clause cross-references.
    """

    @property
    def name(self) -> str:
        return "section_extractor"

    @property
    def category(self) -> str:
        return "section_reference"

    def _normalize_ref(self, prefix: str, num: str) -> str:
        prefix_clean = prefix.lower().strip()
        num_clean = num.rstrip(".,;:")

        if "art" in prefix_clean:
            return f"Article {num_clean}"
        elif "cl" in prefix_clean:
            return f"Clause {num_clean}"
        else:
            return f"Section {num_clean}"

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            extracted_spans = set()

            for pattern in SECTION_PATTERNS:
                for match in pattern.finditer(text):
                    prefix = match.group("prefix")
                    num = match.group("num")

                    if not num or not num[0].isalnum():
                        continue

                    # Adjust start/end for leading whitespace captured in non-word boundary
                    raw_full = match.group(0)
                    prefix_start_in_match = raw_full.find(prefix)
                    start = match.start() + (prefix_start_in_match if prefix_start_in_match > 0 else 0)
                    end = match.end()

                    num_clean = num.rstrip(".,;:")
                    if raw_full.endswith((".", ",", ";", ":")) and not num_clean.endswith(raw_full[-1]):
                        end -= (len(num) - len(num_clean))

                    if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                        continue

                    raw_match = text[start:end].strip()
                    normalized_val = self._normalize_ref(prefix, num_clean)

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
                            rule_name="section_article_clause_pattern",
                            confidence=0.92,
                            entity_type=EntityType.DOCUMENT,
                            category=self.category,
                            original_value=raw_match,
                            normalized_value=normalized_val,
                            metadata={"reference_type": prefix.strip(), "number": num_clean}
                        )
                    )

        return candidates
