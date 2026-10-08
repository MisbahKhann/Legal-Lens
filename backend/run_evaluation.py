"""
Evaluation Script for Step 3 Deterministic Legal Information Extraction.
Runs the extraction pipeline against sample gold-annotated legal documents and outputs Precision & Recall metrics.
"""

from typing import List, Tuple
from app.ingestion.models import (
    LegalDocument,
    LegalPage,
    LegalTextBlock,
    FileType,
    DocumentMetadata,
    ProcessingMetadata,
    TextBlockType,
)
from app.extraction.pipeline import DeterministicExtractionPipeline
from app.extraction.evaluator import GoldAnnotation, ExtractionEvaluator


def build_evaluation_dataset() -> List[Tuple[LegalDocument, List[GoldAnnotation]]]:
    """Generates sample gold-standard legal documents for evaluation benchmarking."""

    # Document 1: Federal Court Complaint
    doc1_id = "eval_doc_001"
    text1 = (
        "UNITED STATES DISTRICT COURT\n"
        "SOUTHERN DISTRICT OF NEW YORK\n"
        "Civil Action No. 1:24-cv-01234\n\n"
        "JOHN DOE, Plaintiff,\n"
        "v.\n"
        "ABC CORP., Defendant.\n\n"
        "FIRST AMENDED COMPLAINT FOR DAMAGES\n\n"
        "1. Plaintiff brings this action pursuant to 42 U.S.C. § 1983 and 18 U.S.C. § 1001.\n"
        "2. The events in question occurred on January 15, 2024 in New York, NY.\n"
        "3. In accordance with precedent set in Brown v. Board of Educ., 347 U.S. 483 (1954), the court has jurisdiction.\n"
        "4. As set forth in Exhibit A attached hereto, under Section 12 of the agreement, notice was given on 02/20/2024.\n"
        "5. Under Article III of the U.S. Constitution, federal judicial power extends to this controversy."
    )

    doc1 = LegalDocument(
        document_id=doc1_id,
        case_id="case_eval_100",
        filename="complaint_001.pdf",
        file_type=FileType.PDF,
        sha256_hash="hash100",
        file_size_bytes=2048,
        document_metadata=DocumentMetadata(title="FIRST AMENDED COMPLAINT FOR DAMAGES"),
        processing_metadata=ProcessingMetadata(
            document_id=doc1_id,
            filename="complaint_001.pdf",
            file_type=FileType.PDF,
            page_count=1,
        ),
        pages=[
            LegalPage(
                page_number=1,
                raw_text=text1,
                normalized_text=text1,
                blocks=[
                    LegalTextBlock(
                        block_id="b1",
                        block_type=TextBlockType.HEADING,
                        raw_text="FIRST AMENDED COMPLAINT FOR DAMAGES",
                        page_number=1,
                    )
                ],
            )
        ],
    )

    golds1 = [
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="court_name",
            original_value="SOUTHERN DISTRICT OF NEW YORK",
            normalized_value="United States District Court for the Southern District of New York",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="docket_number",
            original_value="1:24-cv-01234",
            normalized_value="1:24-CV-01234",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="filing_type",
            original_value="Amended Complaint",
            normalized_value="Amended Complaint",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="statutory_citation",
            original_value="42 U.S.C. § 1983",
            normalized_value="42 U.S.C. § 1983",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="statutory_citation",
            original_value="18 U.S.C. § 1001",
            normalized_value="18 U.S.C. § 1001",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="date",
            original_value="January 15, 2024",
            normalized_value="2024-01-15",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="date",
            original_value="02/20/2024",
            normalized_value="2024-02-20",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="case_citation",
            original_value="347 U.S. 483",
            normalized_value="347 U.S. 483",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="exhibit",
            original_value="Exhibit A",
            normalized_value="Exhibit A",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="section_reference",
            original_value="Section 12",
            normalized_value="Section 12",
        ),
        GoldAnnotation(
            document_id=doc1_id,
            page_number=1,
            category="section_reference",
            original_value="Article III",
            normalized_value="Article III",
        ),
    ]

    # Document 2: Motion for Summary Judgment
    doc2_id = "eval_doc_002"
    text2 = (
        "UNITED STATES COURT OF APPEALS FOR THE NINTH CIRCUIT\n"
        "No. 22-55123\n\n"
        "DEFENDANT'S MOTION FOR SUMMARY JUDGMENT\n\n"
        "Filed this 10th day of March, 2023.\n"
        "Pursuant to 28 U.S.C. § 1331 and § 1983, Defendant requests entry of summary judgment.\n"
        "Refer to Ex. B and Pl. Ex. 3 for evidentiary support.\n"
        "Decided in District Court, N.D. Cal."
    )

    doc2 = LegalDocument(
        document_id=doc2_id,
        case_id="case_eval_200",
        filename="motion_002.pdf",
        file_type=FileType.PDF,
        sha256_hash="hash200",
        file_size_bytes=1500,
        document_metadata=DocumentMetadata(
            title="DEFENDANT'S MOTION FOR SUMMARY JUDGMENT"
        ),
        processing_metadata=ProcessingMetadata(
            document_id=doc2_id,
            filename="motion_002.pdf",
            file_type=FileType.PDF,
            page_count=1,
        ),
        pages=[
            LegalPage(
                page_number=1,
                raw_text=text2,
                normalized_text=text2,
                blocks=[
                    LegalTextBlock(
                        block_id="b1",
                        block_type=TextBlockType.HEADING,
                        raw_text="DEFENDANT'S MOTION FOR SUMMARY JUDGMENT",
                        page_number=1,
                    )
                ],
            )
        ],
    )

    golds2 = [
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="court_name",
            original_value="NINTH CIRCUIT",
            normalized_value="United States Court of Appeals for the Ninth Circuit",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="court_name",
            original_value="N.D. Cal.",
            normalized_value="United States District Court for the Northern District of California",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="docket_number",
            original_value="22-55123",
            normalized_value="22-55123",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="filing_type",
            original_value="Motion for Summary Judgment",
            normalized_value="Motion for Summary Judgment",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="date",
            original_value="10th day of March, 2023",
            normalized_value="2023-03-10",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="statutory_citation",
            original_value="28 U.S.C. § 1331",
            normalized_value="28 U.S.C. § 1331",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="section_reference",
            original_value="§ 1983",
            normalized_value="Section 1983",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="exhibit",
            original_value="Ex. B",
            normalized_value="Exhibit B",
        ),
        GoldAnnotation(
            document_id=doc2_id,
            page_number=1,
            category="exhibit",
            original_value="Pl. Ex. 3",
            normalized_value="Exhibit 3 (Plaintiff)",
        ),
    ]

    return [(doc1, golds1), (doc2, golds2)]


def main():
    print("Initializing Step 3 Deterministic Extraction Evaluation...")
    dataset = build_evaluation_dataset()
    pipeline = DeterministicExtractionPipeline()
    evaluator = ExtractionEvaluator()

    all_results = []
    all_golds = []

    for doc, golds in dataset:
        result = pipeline.extract_candidates(doc)
        all_results.append(result)
        all_golds.extend(golds)

    report = evaluator.evaluate(all_results, all_golds)
    print("\n" + report.print_summary())


if __name__ == "__main__":
    main()
