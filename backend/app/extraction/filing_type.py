"""
Deterministic Common Legal Filing and Document Type Extractor.
Uses controlled vocabularies and structural rules to identify legal filings (Complaint, Answer, Motion, Brief, Order, Judgment, etc.).
"""

import re
from typing import List, Tuple

from app.ingestion.models import LegalDocument, TextBlockType
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity

# Controlled dictionary ordered with specific multi-word types BEFORE general ones
CONTROLLED_FILING_VOCABULARY: List[Tuple[str, str, re.Pattern]] = [
    (
        "MOTION_SUMMARY_JUDGMENT",
        "Motion for Summary Judgment",
        re.compile(
            r"\b(?:Plaintiff\'s|Defendant\'s|Joint)?\s*(?:Cross-)?Motion\s+for\s+Summary\s+Judg?ment\b",
            re.IGNORECASE,
        ),
    ),
    (
        "MOTION_TO_DISMISS",
        "Motion to Dismiss",
        re.compile(
            r"\b(?:Plaintiff\'s|Defendant\'s)?\s*Motion\s+to\s+Dismiss(?:\s+the\s+Complaint)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "AMENDED_COMPLAINT",
        "Amended Complaint",
        re.compile(
            r"\b(?:First|Second|Third|Fourth)?\s*Amended\s+(?:Class\s+Action\s+)?Complaint\b",
            re.IGNORECASE,
        ),
    ),
    (
        "COMPLAINT",
        "Complaint",
        re.compile(
            r"\b(?:Class\s+Action\s+)?Complaint(?:\s+for\s+[A-Za-z\s]+)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ANSWER",
        "Answer",
        re.compile(
            r"\bAnswer(?:\s+and\s+Affirmative\s+Defenses)?(?:\s+to\s+Complaint)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "MEMORANDUM_OF_LAW",
        "Memorandum of Law",
        re.compile(
            r"\bMemorandum\s+of\s+Law\s+(?:in\s+Support|in\s+Opposition)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "BRIEF",
        "Brief",
        re.compile(
            r"\b(?:Brief\s+in\s+Support|Brief\s+in\s+Opposition|Reply\s+Brief|Amicus\s+Brief)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "ORDER",
        "Order",
        re.compile(
            r"\b(?:Court\s+)?Order\s+(?:Granting|Denying|Directing|Dismissing|Scheduling|STIPULATED)?\b",
            re.IGNORECASE,
        ),
    ),
    (
        "JUDGMENT",
        "Judgment",
        re.compile(r"\b(?:Final\s+|Consent\s+|Summary\s+)?Judg?ment\b", re.IGNORECASE),
    ),
    (
        "DECLARATION",
        "Declaration",
        re.compile(
            r"\bDeclaration\s+of\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", re.IGNORECASE
        ),
    ),
    (
        "AFFIDAVIT",
        "Affidavit",
        re.compile(r"\bAffidavit\s+(?:of\s+[A-Z][a-z]+)?\b", re.IGNORECASE),
    ),
    (
        "NOTICE_OF_APPEAL",
        "Notice of Appeal",
        re.compile(r"\bNotice\s+of\s+Appeal\b", re.IGNORECASE),
    ),
    (
        "NOTICE",
        "Notice of Motion/Filing",
        re.compile(r"\bNotice\s+of\s+(?:Motion|Filing|Appearance)\b", re.IGNORECASE),
    ),
    (
        "SUBPOENA",
        "Subpoena",
        re.compile(r"\bSubpoena(?:\s+Duces\s+Tecum)?\b", re.IGNORECASE),
    ),
    (
        "STIPULATION",
        "Stipulation",
        re.compile(r"\bStipulation(?:\s+and\s+Order)?\b", re.IGNORECASE),
    ),
    (
        "PETITION",
        "Petition",
        re.compile(r"\bPetition(?:\s+for\s+Writ\s+of\s+[A-Za-z]+)?\b", re.IGNORECASE),
    ),
    (
        "MOTION_GENERAL",
        "Motion",
        re.compile(
            r"\b(?:Emergency\s+)?Motion\s+(?:to\s+[A-Za-z]+|for\s+[A-Za-z\s]+)\b",
            re.IGNORECASE,
        ),
    ),
]


class FilingTypeExtractor(BaseExtractor):
    """
    Extracts legal document and filing types using controlled vocabularies and structural rules.
    """

    @property
    def name(self) -> str:
        return "filing_type_extractor"

    @property
    def category(self) -> str:
        return "filing_type"

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []
        extracted_spans_by_page = {}

        # 1. Inspect Document Metadata Title
        if document.document_metadata and document.document_metadata.title:
            doc_title = document.document_metadata.title
            for canon_code, norm_name, pattern in CONTROLLED_FILING_VOCABULARY:
                match = pattern.search(doc_title)
                if match:
                    candidates.append(
                        ExtractedCandidateEntity(
                            document_id=document.document_id,
                            case_id=document.case_id,
                            page_number=1,
                            source_text=f"Document Metadata Title: {doc_title}",
                            char_span=(match.start(), match.end()),
                            extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                            rule_name="document_metadata_title_filing_vocab",
                            confidence=0.99,
                            entity_type=EntityType.FILING,
                            category=self.category,
                            original_value=match.group(0),
                            normalized_value=norm_name,
                            metadata={
                                "filing_category": canon_code,
                                "source": "metadata_title",
                            },
                        )
                    )
                    break

        # 2. Inspect Pages and Headings
        for page in document.pages:
            page_num = page.page_number
            extracted_spans = extracted_spans_by_page.setdefault(page_num, set())

            for block in page.blocks:
                if block.block_type in (
                    TextBlockType.HEADING,
                    TextBlockType.HEADER,
                ) or (block.level and block.level == 1):
                    block_text = block.raw_text or block.normalized_text
                    for canon_code, norm_name, pattern in CONTROLLED_FILING_VOCABULARY:
                        for match in pattern.finditer(block_text):
                            start, end = match.span()
                            if any(
                                s <= start < e or s < end <= e
                                for s, e in extracted_spans
                            ):
                                continue

                            extracted_spans.add((start, end))
                            candidates.append(
                                ExtractedCandidateEntity(
                                    document_id=document.document_id,
                                    case_id=document.case_id,
                                    page_number=page_num,
                                    source_text=block_text.strip(),
                                    char_span=(start, end),
                                    extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                                    rule_name="heading_filing_vocab",
                                    confidence=0.95,
                                    entity_type=EntityType.FILING,
                                    category=self.category,
                                    original_value=match.group(0),
                                    normalized_value=norm_name,
                                    metadata={
                                        "filing_category": canon_code,
                                        "block_id": block.block_id,
                                    },
                                )
                            )

            # On page 1, check general text if no candidate extracted for page 1 yet
            page1_cands = [
                c
                for c in candidates
                if c.page_number == 1
                and c.rule_name != "document_metadata_title_filing_vocab"
            ]
            if page_num == 1 and len(page1_cands) == 0:
                page_text = page.raw_text or page.normalized_text
                header_snippet = page_text[:1500]
                for canon_code, norm_name, pattern in CONTROLLED_FILING_VOCABULARY:
                    for match in pattern.finditer(header_snippet):
                        start, end = match.span()
                        if any(
                            s <= start < e or s < end <= e for s, e in extracted_spans
                        ):
                            continue

                        extracted_spans.add((start, end))
                        candidates.append(
                            ExtractedCandidateEntity(
                                document_id=document.document_id,
                                case_id=document.case_id,
                                page_number=1,
                                source_text=header_snippet[
                                    max(0, start - 20) : min(
                                        len(header_snippet), end + 20
                                    )
                                ]
                                .replace("\n", " ")
                                .strip(),
                                char_span=(start, end),
                                extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                                rule_name="page1_caption_filing_vocab",
                                confidence=0.90,
                                entity_type=EntityType.FILING,
                                category=self.category,
                                original_value=match.group(0),
                                normalized_value=norm_name,
                                metadata={"filing_category": canon_code},
                            )
                        )

        return candidates
