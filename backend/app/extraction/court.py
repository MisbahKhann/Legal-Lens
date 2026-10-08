"""
Deterministic Court Name Extractor using controlled vocabularies and abbreviation rules.
Normalizes federal (SCOTUS, Circuit Courts, District Courts like S.D.N.Y., N.D. Cal.) and state court names.
"""

import re
from typing import List, Tuple, Dict, Any

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

# Controlled list of court patterns and canonical normalized representations
CONTROLLED_COURT_PATTERNS: List[Tuple[str, re.Pattern, Dict[str, Any]]] = [
    # Supreme Court of the United States
    (
        "Supreme Court of the United States",
        re.compile(
            r"\b(?:Supreme\s+Court\s+of\s+the\s+United\s+States|United\s+States\s+Supreme\s+Court|U\.?\s*S\.?\s*Supreme\s+Court|U\.?\s*S\.?\s*Sup\.?\s*Ct\.?|SCOTUS)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_FEDERAL", "court_level": "SUPREME"},
    ),
    # Federal Circuit Courts of Appeals
    (
        "United States Court of Appeals for the D.C. Circuit",
        re.compile(
            r"\b(?:United\s+States\s+Court\s+of\s+Appeals\s+for\s+the\s+D\.?C\.?\s*Circuit|D\.?C\.?\s*Circuit(?:\s+Court\s+of\s+Appeals)?|D\.?C\.?\s*Cir\.?)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_FEDERAL", "court_level": "APPELLATE", "circuit": "D.C."},
    ),
    (
        "United States Court of Appeals for the Federal Circuit",
        re.compile(
            r"\b(?:United\s+States\s+Court\s+of\s+Appeals\s+for\s+the\s+Federal\s+Circuit|Federal\s+Circuit(?:\s+Court\s+of\s+Appeals)?|Fed\.?\s*Cir\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "APPELLATE",
            "circuit": "Federal",
        },
    ),
    # Federal District Courts Abbreviations (S.D.N.Y., N.D. Cal., C.D. Cal., E.D. Tex., D.D.C., D. Del.)
    (
        "United States District Court for the Southern District of New York",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Southern\s+District\s+of\s+New\s+York|U\.?\s*S\.?\s*Dist\.?\s*Ct\.?,?\s*S\.?\s*D\.?\s*N\.?\s*Y\.?|S\.?\s*D\.?\s*N\.?\s*Y\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "S.D.N.Y.",
        },
    ),
    (
        "United States District Court for the Eastern District of New York",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Eastern\s+District\s+of\s+New\s+York|E\.?\s*D\.?\s*N\.?\s*Y\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "E.D.N.Y.",
        },
    ),
    (
        "United States District Court for the Northern District of California",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Northern\s+District\s+of\s+California|N\.?\s*D\.?\s*Cal\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "N.D. Cal.",
        },
    ),
    (
        "United States District Court for the Central District of California",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Central\s+District\s+of\s+California|C\.?\s*D\.?\s*Cal\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "C.D. Cal.",
        },
    ),
    (
        "United States District Court for the Southern District of Texas",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Southern\s+District\s+of\s+Texas|S\.?\s*D\.?\s*Tex\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "S.D. Tex.",
        },
    ),
    (
        "United States District Court for the Eastern District of Texas",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?Eastern\s+District\s+of\s+Texas|E\.?\s*D\.?\s*Tex\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "E.D. Tex.",
        },
    ),
    (
        "United States District Court for the District of Delaware",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?District\s+of\s+Delaware|D\.?\s*Del\.?)\b",
            re.IGNORECASE,
        ),
        {
            "jurisdiction": "US_FEDERAL",
            "court_level": "DISTRICT",
            "district": "D. Del.",
        },
    ),
    (
        "United States District Court for the District of Columbia",
        re.compile(
            r"\b(?:United\s+States\s+District\s+Court\s+(?:for\s+the\s+)?District\s+of\s+Columbia|D\.?\s*D\.?\s*C\.?)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_FEDERAL", "court_level": "DISTRICT", "district": "D.D.C."},
    ),
    # Generic Federal District / Circuit Court Patterns
    (
        "United States District Court",
        re.compile(
            r"\bUnited\s+States\s+District\s+Court(?:\s+for\s+the\s+[A-Za-z\s]+District\s+of\s+[A-Za-z\s]+)?\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_FEDERAL", "court_level": "DISTRICT"},
    ),
    # State Supreme Courts
    (
        "Supreme Court of California",
        re.compile(
            r"\b(?:Supreme\s+Court\s+of\s+California|California\s+Supreme\s+Court|Cal\.?\s*Supreme\s+Court)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_STATE", "state": "CA", "court_level": "SUPREME"},
    ),
    (
        "Supreme Court of Texas",
        re.compile(
            r"\b(?:Supreme\s+Court\s+of\s+Texas|Texas\s+Supreme\s+Court|Tex\.?\s*Supreme\s+Court)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_STATE", "state": "TX", "court_level": "SUPREME"},
    ),
    (
        "New York Court of Appeals",
        re.compile(
            r"\b(?:New\s+York\s+Court\s+of\s+Appeals|N\.?\s*Y\.?\s*Court\s+of\s+Appeals)\b",
            re.IGNORECASE,
        ),
        {"jurisdiction": "US_STATE", "state": "NY", "court_level": "SUPREME"},
    ),
]

# Standard Nth Circuit Court regex pattern e.g. "9th Circuit", "Ninth Circuit Court of Appeals", "1st Cir."
NUMBERED_CIRCUIT_PATTERN = re.compile(
    r"\b(?:United\s+States\s+Court\s+of\s+Appeals\s+for\s+the\s+)?"
    r"(?P<num>1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th|11th|First|Second|Third|Fourth|Fifth|Sixth|Seventh|Eighth|Ninth|Tenth|Eleventh)\s+"
    r"(?:Circuit(?:\s+Court\s+of\s+Appeals)?|Cir\.?)\b",
    re.IGNORECASE,
)

CIRCUIT_NUM_MAP = {
    "1st": "First",
    "first": "First",
    "2nd": "Second",
    "second": "Second",
    "3rd": "Third",
    "third": "Third",
    "4th": "Fourth",
    "fourth": "Fourth",
    "5th": "Fifth",
    "fifth": "Fifth",
    "6th": "Sixth",
    "sixth": "Sixth",
    "7th": "Seventh",
    "seventh": "Seventh",
    "8th": "Eighth",
    "eighth": "Eighth",
    "9th": "Ninth",
    "ninth": "Ninth",
    "10th": "Tenth",
    "tenth": "Tenth",
    "11th": "Eleventh",
    "eleventh": "Eleventh",
}


class CourtExtractor(BaseExtractor):
    """
    Extracts federal and state court names and standardizes abbreviations.
    """

    @property
    def name(self) -> str:
        return "court_extractor"

    @property
    def category(self) -> str:
        return "court_name"

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            extracted_spans = set()

            # 1. Match specific controlled court patterns
            for norm_court_name, pattern, court_meta in CONTROLLED_COURT_PATTERNS:
                for match in pattern.finditer(text):
                    start, end = match.span()

                    if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                        continue

                    raw_match = match.group(0).strip()
                    extracted_spans.add((start, end))

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
                            rule_name="controlled_court_pattern",
                            confidence=0.96,
                            entity_type=EntityType.COURT,
                            category=self.category,
                            original_value=raw_match,
                            normalized_value=norm_court_name,
                            metadata=dict(court_meta),
                        )
                    )

            # 2. Match numbered circuit courts e.g. "9th Cir.", "Ninth Circuit"
            for match in NUMBERED_CIRCUIT_PATTERN.finditer(text):
                start, end = match.span()

                if any(s <= start < e or s < end <= e for s, e in extracted_spans):
                    continue

                raw_match = match.group(0).strip()
                num_raw = match.group("num")
                num_norm = CIRCUIT_NUM_MAP.get(num_raw.lower(), num_raw.capitalize())
                norm_court_name = (
                    f"United States Court of Appeals for the {num_norm} Circuit"
                )

                extracted_spans.add((start, end))

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
                        rule_name="numbered_circuit_court_pattern",
                        confidence=0.97,
                        entity_type=EntityType.COURT,
                        category=self.category,
                        original_value=raw_match,
                        normalized_value=norm_court_name,
                        metadata={
                            "jurisdiction": "US_FEDERAL",
                            "court_level": "APPELLATE",
                            "circuit": num_norm,
                        },
                    )
                )

        return candidates
