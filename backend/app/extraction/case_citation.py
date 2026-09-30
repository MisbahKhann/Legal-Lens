"""
Deterministic US Legal Case Citation Extractor using Eyecite library.
"""

from typing import List, Dict, Any
import eyecite
from eyecite.models import FullCaseCitation, ShortCaseCitation, ResourceCitation

from app.ingestion.models import LegalDocument
from app.schema.entity_types import EntityType
from app.schema.provenance import ExtractionMethod
from app.extraction.base import BaseExtractor
from app.extraction.models import ExtractedCandidateEntity


class CaseCitationExtractor(BaseExtractor):
    """
    Extracts US legal case citations using the open-source eyecite library.
    Identifies full case citations (e.g., 347 U.S. 483), short citations, and reporter references.
    """

    @property
    def name(self) -> str:
        return "case_citation_extractor"

    @property
    def category(self) -> str:
        return "case_citation"

    def extract(self, document: LegalDocument) -> List[ExtractedCandidateEntity]:
        candidates: List[ExtractedCandidateEntity] = []

        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text or not text.strip():
                continue

            try:
                citations: List[Any] = eyecite.get_citations(text)
            except Exception:
                # Conservative fallback on error
                citations = []

            for cit in citations:
                # Extract span
                span = cit.span() if hasattr(cit, "span") else None
                start_offset, end_offset = span if span else (0, 0)

                # Original matched text
                orig_text = text[start_offset:end_offset] if span and 0 <= start_offset < end_offset <= len(text) else str(cit)

                # Normalized representation
                groups = getattr(cit, "groups", {}) or {}
                volume = groups.get("volume", "")
                reporter = groups.get("reporter", "")
                page_num = groups.get("page", "")

                if volume and reporter and page_num:
                    normalized_val = f"{volume} {reporter} {page_num}"
                elif hasattr(cit, "corrected_citation") and callable(cit.corrected_citation):
                    normalized_val = cit.corrected_citation()
                else:
                    normalized_val = orig_text.strip()

                metadata: Dict[str, Any] = {
                    "citation_type": type(cit).__name__,
                    "volume": volume,
                    "reporter": reporter,
                    "page": page_num,
                }

                meta_obj = getattr(cit, "metadata", None)
                if meta_obj:
                    if getattr(meta_obj, "year", None):
                        metadata["year"] = meta_obj.year
                    if getattr(meta_obj, "court", None):
                        metadata["court"] = meta_obj.court
                    if getattr(meta_obj, "plaintiff", None):
                        metadata["plaintiff"] = meta_obj.plaintiff
                    if getattr(meta_obj, "defendant", None):
                        metadata["defendant"] = meta_obj.defendant

                # Context snippet around extraction
                snippet_start = max(0, start_offset - 40)
                snippet_end = min(len(text), end_offset + 40)
                snippet = text[snippet_start:snippet_end].replace("\n", " ").strip()

                candidates.append(
                    ExtractedCandidateEntity(
                        document_id=document.document_id,
                        case_id=document.case_id,
                        page_number=page.page_number,
                        source_text=snippet,
                        char_span=(start_offset, end_offset) if span else None,
                        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                        rule_name="eyecite_case_citation",
                        confidence=0.95,
                        entity_type=EntityType.CASE,
                        category=self.category,
                        original_value=orig_text,
                        normalized_value=normalized_val,
                        metadata=metadata
                    )
                )

        return candidates
