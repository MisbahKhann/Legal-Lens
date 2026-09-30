"""
Unit tests for Step 3 Deterministic Legal Information Extraction.
Tests all 8 candidate extraction categories + false-positive edge cases.
"""

import pytest
from app.ingestion.models import (
    LegalDocument, LegalPage, LegalTextBlock, FileType,
    DocumentMetadata, ProcessingMetadata, TextBlockType
)
from app.schema.entity_types import EntityType
from app.extraction.case_citation import CaseCitationExtractor
from app.extraction.statutory import StatutoryCitationExtractor
from app.extraction.date import DateExtractor
from app.extraction.docket import DocketExtractor
from app.extraction.section import SectionExtractor
from app.extraction.exhibit import ExhibitExtractor
from app.extraction.filing_type import FilingTypeExtractor
from app.extraction.court import CourtExtractor
from app.extraction.pipeline import DeterministicExtractionPipeline


def create_test_doc(text: str, title: str = "Test Legal Document") -> LegalDocument:
    """Helper to build a standardized LegalDocument instance for testing."""
    page = LegalPage(
        page_number=1,
        raw_text=text,
        normalized_text=text,
        blocks=[
            LegalTextBlock(
                block_id="b1",
                block_type=TextBlockType.PARAGRAPH,
                raw_text=text,
                normalized_text=text,
                page_number=1
            )
        ]
    )
    proc_meta = ProcessingMetadata(
        document_id="doc_test_100",
        filename="test_doc.pdf",
        file_type=FileType.PDF,
        page_count=1
    )
    return LegalDocument(
        document_id="doc_test_100",
        case_id="case_test_200",
        filename="test_doc.pdf",
        file_type=FileType.PDF,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        file_size_bytes=1024,
        document_metadata=DocumentMetadata(title=title),
        processing_metadata=proc_meta,
        pages=[page]
    )


class TestDeterministicExtraction:

    def test_1_case_citations(self):
        """1. Test US legal case citations extraction via Eyecite."""
        text = "In Brown v. Board of Educ., 347 U.S. 483 (1954), the Supreme Court ruled... See also 554 U.S. 570."
        doc = create_test_doc(text)
        extractor = CaseCitationExtractor()
        results = extractor.extract(doc)

        assert len(results) >= 2
        cit_vals = [r.normalized_value for r in results]
        assert "347 U.S. 483" in cit_vals
        assert "554 U.S. 570" in cit_vals
        for r in results:
            assert r.entity_type == EntityType.CASE
            assert r.category == "case_citation"
            assert r.document_id == "doc_test_100"

    def test_2_statutory_citations(self):
        """2. Test statutory & regulatory citations (42 U.S.C. § 1983, 18 U.S.C. § 1001, 12 C.F.R. § 226.1)."""
        text = "Plaintiff brought claims under 42 U.S.C. § 1983 and 18 U.S.C. § 1001. Defendant violated 12 C.F.R. § 226.1."
        doc = create_test_doc(text)
        extractor = StatutoryCitationExtractor()
        results = extractor.extract(doc)

        assert len(results) >= 3
        norm_vals = [r.normalized_value for r in results]
        assert "42 U.S.C. § 1983" in norm_vals
        assert "18 U.S.C. § 1001" in norm_vals
        assert "12 C.F.R. § 226.1" in norm_vals

    def test_3_dates(self):
        """3. Test legal dates detection & ISO 8601 normalization."""
        text = "Executed on January 15, 2024. Signed this 15th day of May, 2023. Effective 2022-12-01 or 03/14/2021."
        doc = create_test_doc(text)
        extractor = DateExtractor()
        results = extractor.extract(doc)

        iso_dates = [r.normalized_value for r in results]
        assert "2024-01-15" in iso_dates
        assert "2023-05-15" in iso_dates
        assert "2022-12-01" in iso_dates
        assert "2021-03-14" in iso_dates

    def test_4_docket_numbers(self):
        """4. Test court docket & case numbers (No. 24-CV-1234, 3:24-cv-00123, Civil Action No. 1:20-cv-09876)."""
        text = "UNITED STATES DISTRICT COURT\nCase No. 3:24-cv-00123-JMB\nCivil Action No. 1:20-cv-09876\nNo. 24-CV-1234"
        doc = create_test_doc(text)
        extractor = DocketExtractor()
        results = extractor.extract(doc)

        dockets = [r.normalized_value for r in results]
        assert "3:24-CV-00123-JMB" in dockets or "3:24-CV-00123" in [d[:14] for d in dockets]
        assert "1:20-CV-09876" in dockets
        assert "24-CV-1234" in dockets

    def test_5_section_article_references(self):
        """5. Test legal section, article, and clause references (§ 1983, Section 12, Article III, Sec. 4(a))."""
        text = "Pursuant to § 1983 and Section 12 of the agreement, under Article III of the Constitution and Sec. 4(a)."
        doc = create_test_doc(text)
        extractor = SectionExtractor()
        results = extractor.extract(doc)

        refs = [r.normalized_value for r in results]
        assert "Section 1983" in refs
        assert "Section 12" in refs
        assert "Article III" in refs
        assert "Section 4(a)" in refs

    def test_6_exhibits(self):
        """6. Test court exhibit designations (Exhibit A, Exhibit 12, Ex. B, Pl. Ex. 3)."""
        text = "As shown in Exhibit A and Ex. B, attached hereto as Exhibit 12 and Pl. Ex. 3."
        doc = create_test_doc(text)
        extractor = ExhibitExtractor()
        results = extractor.extract(doc)

        exhibits = [r.normalized_value for r in results]
        assert "Exhibit A" in exhibits
        assert "Exhibit B" in exhibits
        assert "Exhibit 12" in exhibits
        assert "Exhibit 3 (Plaintiff)" in exhibits

    def test_7_filing_types(self):
        """7. Test legal filing & document type extraction using controlled vocabularies."""
        text = "DEFENDANT'S MOTION TO DISMISS THE COMPLAINT\nDefendant hereby files this Motion for Summary Judgment."
        doc = create_test_doc(text, title="MOTION TO DISMISS")
        extractor = FilingTypeExtractor()
        results = extractor.extract(doc)

        filing_names = [r.normalized_value for r in results]
        assert "Motion to Dismiss" in filing_names
        assert "Motion for Summary Judgment" in filing_names

    def test_8_court_names(self):
        """8. Test federal and state court names & abbreviations (SCOTUS, S.D.N.Y., N.D. Cal., 9th Cir.)."""
        text = "FILED IN THE U.S. District Court for the Southern District of New York (S.D.N.Y.) and N.D. Cal., affirmed by 9th Cir."
        doc = create_test_doc(text)
        extractor = CourtExtractor()
        results = extractor.extract(doc)

        courts = [r.normalized_value for r in results]
        assert "United States District Court for the Southern District of New York" in courts
        assert "United States District Court for the Northern District of California" in courts
        assert "United States Court of Appeals for the Ninth Circuit" in courts

    def test_9_false_positives(self):
        """9. Test false-positive prevention on non-legal or ambiguous text."""
        # Plain text with street address "100 Main St", plain number "12", invalid date "02/30/2024"
        text = "The party walked 100 Main St on a sunny afternoon. The number 12 is even. Invalid date 02/30/2024."
        doc = create_test_doc(text)

        pipeline = DeterministicExtractionPipeline()
        res = pipeline.extract_candidates(doc)

        # Date extractor should not match invalid dates like 02/30/2024
        dates = [c.normalized_value for c in res.get_by_category("date")]
        assert "2024-02-30" not in dates

        # No docket or statutory citations should be extracted from plain prose
        assert len(res.get_by_category("docket_number")) == 0
        assert len(res.get_by_category("statutory_citation")) == 0

    def test_10_full_pipeline_execution(self):
        """10. Test end-to-end execution of DeterministicExtractionPipeline."""
        text = (
            "IN THE UNITED STATES DISTRICT COURT FOR THE SOUTHERN DISTRICT OF NEW YORK\n"
            "Civil Action No. 1:24-cv-00500\n\n"
            "PLAINTIFF'S COMPLAINT FOR DAMAGES\n\n"
            "1. Plaintiff brings this action pursuant to 42 U.S.C. § 1983 alleging violations occurring on January 15, 2024.\n"
            "2. In Brown v. Board of Educ., 347 U.S. 483, the Supreme Court established precedent.\n"
            "3. See Exhibit A attached hereto under Section 5."
        )
        doc = create_test_doc(text, title="PLAINTIFF'S COMPLAINT FOR DAMAGES")
        pipeline = DeterministicExtractionPipeline()
        result = pipeline.extract_candidates(doc)

        assert result.document_id == "doc_test_100"
        assert len(result.candidates) >= 6
        assert result.summary_counts.get("court_name", 0) >= 1
        assert result.summary_counts.get("docket_number", 0) >= 1
        assert result.summary_counts.get("filing_type", 0) >= 1
        assert result.summary_counts.get("statutory_citation", 0) >= 1
        assert result.summary_counts.get("date", 0) >= 1
        assert result.summary_counts.get("case_citation", 0) >= 1
        assert result.summary_counts.get("exhibit", 0) >= 1
        assert result.summary_counts.get("section_reference", 0) >= 1
