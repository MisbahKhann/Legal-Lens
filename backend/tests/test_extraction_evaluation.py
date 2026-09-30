"""
Unit tests for Step 3 Evaluation Framework and Precision/Recall calculation.
"""

from app.schema.entity_types import EntityType
from app.extraction.models import ExtractedCandidateEntity, DeterministicExtractionResult
from app.extraction.evaluator import GoldAnnotation, ExtractionEvaluator


def test_evaluation_metric_calculation():
    """Tests evaluation metrics calculation (Precision, Recall, F1) against gold standard annotations."""
    doc_id = "doc_eval_001"

    candidates = [
        ExtractedCandidateEntity(
            document_id=doc_id,
            page_number=1,
            source_text="42 U.S.C. § 1983",
            entity_type=EntityType.STATUTE,
            category="statutory_citation",
            original_value="42 U.S.C. § 1983",
            normalized_value="42 U.S.C. § 1983"
        ),
        ExtractedCandidateEntity(
            document_id=doc_id,
            page_number=1,
            source_text="January 15, 2024",
            entity_type=EntityType.DATE,
            category="date",
            original_value="January 15, 2024",
            normalized_value="2024-01-15"
        ),
        ExtractedCandidateEntity(
            document_id=doc_id,
            page_number=1,
            source_text="False positive item 999",
            entity_type=EntityType.STATUTE,
            category="statutory_citation",
            original_value="999",
            normalized_value="999"
        ),
    ]

    gold_annotations = [
        GoldAnnotation(
            document_id=doc_id,
            page_number=1,
            category="statutory_citation",
            original_value="42 U.S.C. § 1983",
            normalized_value="42 U.S.C. § 1983"
        ),
        GoldAnnotation(
            document_id=doc_id,
            page_number=1,
            category="date",
            original_value="January 15, 2024",
            normalized_value="2024-01-15"
        ),
        GoldAnnotation(
            document_id=doc_id,
            page_number=1,
            category="docket_number",
            original_value="No. 24-CV-1234",
            normalized_value="24-CV-1234"
        ),
    ]

    result = DeterministicExtractionResult(
        document_id=doc_id,
        candidates=candidates
    )

    evaluator = ExtractionEvaluator()
    report = evaluator.evaluate([result], gold_annotations)

    # Statutory citation: 1 candidate matches gold, 1 FP -> Precision 0.5, Recall 1.0, F1 0.67
    stat_m = report.category_metrics["statutory_citation"]
    assert stat_m.true_positives == 1
    assert stat_m.false_positives == 1
    assert stat_m.false_negatives == 0
    assert abs(stat_m.precision - 0.5) < 0.01
    assert abs(stat_m.recall - 1.0) < 0.01

    # Date: 1 candidate matches gold -> Precision 1.0, Recall 1.0, F1 1.0
    date_m = report.category_metrics["date"]
    assert date_m.true_positives == 1
    assert date_m.false_positives == 0
    assert date_m.false_negatives == 0
    assert abs(date_m.precision - 1.0) < 0.01

    # Docket number: 0 candidates extracted, 1 gold -> Recall 0.0, FN 1
    dock_m = report.category_metrics["docket_number"]
    assert dock_m.true_positives == 0
    assert dock_m.false_negatives == 1

    # Overall Metrics
    overall = report.overall_metrics
    assert overall.true_positives == 2
    assert overall.false_positives == 1
    assert overall.false_negatives == 1
    assert abs(overall.precision - (2 / 3)) < 0.01
    assert abs(overall.recall - (2 / 3)) < 0.01

    # Check formatted report text string output
    report_text = report.print_summary()
    assert "STEP 3 DETERMINISTIC EXTRACTION EVALUATION REPORT" in report_text
    assert "OVERALL" in report_text
