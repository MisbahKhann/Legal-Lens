"""
Focused Pytest Suite for Step 11 — Extraction Evaluation & Benchmarking.
Tests precision/recall/F1 metrics, zero denominator handling, entity & relationship matching rules,
entity-resolution pairwise metrics, temporal matching, provenance, escalation, graph consistency,
and JSON report generation.
"""

import json
import pytest
from pathlib import Path

from app.evaluation.models import (
    GoldEntity,
    GoldRelationship,
    GoldEvent,
    GoldEquivalencePair,
    GoldDocumentData,
    GoldDataset,
    ExtractionMetrics,
    ResolutionMetrics,
    TemporalMetrics,
    ValidationMetrics,
    ProvenanceMetrics,
    EscalationMetrics,
    GraphConsistencyMetrics,
    Step11EvaluationReport,
)
from app.evaluation.evaluator import KnowledgeGraphEvaluator
from app.evaluation.runner import EvaluationRunner
from app.extraction.ai_models import CandidateEntity, CandidateRelation
from app.resolution.models import CanonicalEntity, ResolvedRelation
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType


def test_extraction_metrics_score_computation():
    """Verifies correct calculation of TP, FP, FN, Precision, Recall, and F1."""
    m = ExtractionMetrics(
        category="TEST_CAT",
        true_positives=8,
        false_positives=2,
        false_negatives=2,
    )
    m.compute_scores()

    assert m.precision == 0.80  # 8 / 10
    assert m.recall == 0.80  # 8 / 10
    assert m.f1_score == 0.80  # 2 * 0.8 * 0.8 / 1.6
    assert m.is_calculable is True


def test_zero_denominator_safety():
    """Verifies safe handling of empty ground truth and empty predictions."""
    # Case 1: Empty predictions and empty ground truth (0/0)
    m_empty = ExtractionMetrics(
        category="EMPTY_CAT",
        true_positives=0,
        false_positives=0,
        false_negatives=0,
    )
    m_empty.compute_scores()

    assert m_empty.precision is None
    assert m_empty.recall is None
    assert m_empty.f1_score is None
    assert m_empty.is_calculable is False
    assert "0/0" in m_empty.note

    # Case 2: Zero true positives with false negatives
    m_fn = ExtractionMetrics(
        category="FN_CAT",
        true_positives=0,
        false_positives=0,
        false_negatives=5,
    )
    m_fn.compute_scores()

    assert m_fn.precision == 0.0
    assert m_fn.recall == 0.0
    assert m_fn.f1_score == 0.0
    assert m_fn.is_calculable is True


def test_entity_matching_rules():
    """Tests entity matching rules including normalization and substring alignment."""
    evaluator = KnowledgeGraphEvaluator()

    gold_entities = [
        GoldEntity(
            entity_id="g1",
            document_id="doc1",
            entity_type="COURT",
            text="SOUTHERN DISTRICT OF NEW YORK",
            normalized_value="United States District Court for the Southern District of New York",
        ),
        GoldEntity(
            entity_id="g2",
            document_id="doc1",
            entity_type="PERSON",
            text="John Doe",
        ),
    ]

    predicted_entities = [
        {
            "entity_type": "court",
            "text": "Southern District of New York",
            "document_id": "doc1",
        },
        {
            "entity_type": "person",
            "text": "John Doe",
            "document_id": "doc1",
        },
        {
            "entity_type": "person",
            "text": "Jane Smith",  # False positive
            "document_id": "doc1",
        },
    ]

    overall_m, per_cat = evaluator.evaluate_entities(predicted_entities, gold_entities)

    assert overall_m.true_positives == 2
    assert overall_m.false_positives == 1
    assert overall_m.false_negatives == 0
    assert overall_m.precision == 0.6667
    assert overall_m.recall == 1.0
    assert "COURT" in per_cat
    assert "PERSON" in per_cat


def test_relationship_matching_rules():
    """Tests relationship triplet matching logic."""
    evaluator = KnowledgeGraphEvaluator()

    gold_rels = [
        GoldRelationship(
            relation_id="gr1",
            document_id="doc1",
            source_entity_text="John Doe",
            relation_type="FILED_ACTION",
            target_entity_text="ABC Corp",
        )
    ]

    predicted_rels = [
        {
            "source_entity_text": "John Doe",
            "relation_type": "filed_action",
            "target_entity_text": "ABC Corp",
            "document_id": "doc1",
        }
    ]

    overall_m, _ = evaluator.evaluate_relationships(predicted_rels, gold_rels)

    assert overall_m.true_positives == 1
    assert overall_m.false_positives == 0
    assert overall_m.false_negatives == 0
    assert overall_m.precision == 1.0
    assert overall_m.recall == 1.0


def test_entity_resolution_pairwise_metrics():
    """Tests pairwise precision/recall/f1 calculation on gold equivalence pairs."""
    evaluator = KnowledgeGraphEvaluator()

    gold_pairs = [
        GoldEquivalencePair(
            entity_text_1="John Doe",
            entity_text_2="J. Doe",
            are_equivalent=True,
            canonical_name="John Doe",
        ),
        GoldEquivalencePair(
            entity_text_1="John Doe",
            entity_text_2="ABC Corp",
            are_equivalent=False,
        ),
    ]

    canonical_entities = [
        {
            "canonical_id": "c1",
            "canonical_name": "John Doe",
            "aliases": ["John Doe", "J. Doe"],
        },
        {
            "canonical_id": "c2",
            "canonical_name": "ABC Corp",
            "aliases": ["ABC Corp"],
        },
    ]

    res_m = evaluator.evaluate_entity_resolution(canonical_entities, gold_pairs)

    assert res_m.total_pairs_evaluated == 2
    assert res_m.true_positives == 1
    assert res_m.true_negatives == 1
    assert res_m.false_positives == 0
    assert res_m.false_negatives == 0
    assert res_m.accuracy == 1.0
    assert res_m.pairwise_f1 == 1.0


def test_temporal_event_matching():
    """Tests temporal date/event matching metrics."""
    evaluator = KnowledgeGraphEvaluator()

    gold_events = [
        GoldEvent(
            event_id="ge1",
            document_id="doc1",
            event_type="EVENT",
            description="Filing of Complaint",
            event_date="2024-01-15",
        )
    ]

    predicted_events = [
        {
            "description": "Filing of Complaint",
            "event_date": "2024-01-15",
            "source_document_id": "doc1",
        }
    ]

    t_m = evaluator.evaluate_temporal_events(predicted_events, gold_events)

    assert t_m.total_gold_events == 1
    assert t_m.matched_events_count == 1
    assert t_m.exact_date_matches == 1
    assert t_m.date_matching_precision == 1.0
    assert t_m.date_matching_recall == 1.0
    assert t_m.date_matching_f1 == 1.0


def test_provenance_and_escalation_metrics():
    """Tests provenance completeness and review escalation rate metrics."""
    evaluator = KnowledgeGraphEvaluator()

    candidates = [
        {
            "page_number": 1,
            "start_offset": 10,
            "end_offset": 20,
            "source_text": "Sample text",
        },
        {
            "page_number": 0,  # Missing page
            "source_text": "Incomplete",
        },
    ]

    prov_m = evaluator.evaluate_provenance(candidates)
    assert prov_m.total_evaluated_items == 2
    assert prov_m.fully_provenanced_items == 1
    assert prov_m.provenance_completeness_rate == 0.50

    esc_m = evaluator.evaluate_escalation(
        total_candidates=10,
        review_items=[{"review_id": "rev1"}],
    )
    assert esc_m.total_candidates_processed == 10
    assert esc_m.escalated_for_review_count == 1
    assert esc_m.escalation_rate == 0.10


def test_graph_consistency_metrics():
    """Tests in-memory knowledge graph triplet consistency checks."""
    evaluator = KnowledgeGraphEvaluator()

    canonical_entities = [
        {"canonical_id": "node1", "canonical_name": "Entity 1"},
        {"canonical_id": "node2", "canonical_name": "Entity 2"},
    ]

    resolved_relations = [
        {
            "relation_id": "rel1",
            "source_entity_id": "node1",
            "target_entity_id": "node2",
            "is_valid": True,
        },
        {
            "relation_id": "rel2",
            "source_entity_id": "node1",
            "target_entity_id": "node_missing",  # Dangling edge!
            "is_valid": False,
        },
    ]

    g_m = evaluator.evaluate_graph_consistency(canonical_entities, resolved_relations)

    assert g_m.total_nodes == 2
    assert g_m.total_edges == 2
    assert g_m.dangling_edges_count == 1
    assert g_m.invalid_triplet_types_count == 1
    assert g_m.orphan_nodes_count == 0
    assert g_m.graph_consistency_score == 0.0  # 0 valid out of 2 total


def test_full_evaluation_report_generation(tmp_path):
    """Integration test loading gold sample dataset and producing JSON evaluation report."""
    gold_file = Path("storage/eval_gold_sample.json")
    assert gold_file.exists()

    runner = EvaluationRunner()
    gold_ds = runner.load_gold_dataset(str(gold_file))

    # Evaluate using runner
    report = runner.run_evaluation(
        gold_dataset_source=gold_ds,
        predictions_source={},  # Empty predictions test
        output_dir=str(tmp_path),
    )

    assert isinstance(report, Step11EvaluationReport)
    assert report.dataset_id == "gold_std_sample_v1"
    assert report.is_illustrative_fixture is True

    # Check generated report JSON file
    report_files = list(tmp_path.glob("eval_report_*.json"))
    assert len(report_files) == 1

    summary_text = report.print_summary()
    assert "STEP 11 EXTRACTION EVALUATION REPORT" in summary_text
    assert "OVERALL ENTITIES" in summary_text


def test_compatibility_with_existing_pydantic_models():
    """Verifies evaluator works with actual Step 4 & 5 Pydantic model objects."""
    evaluator = KnowledgeGraphEvaluator()

    c_ent = CandidateEntity(
        entity_type=EntityType.COURT,
        text="SOUTHERN DISTRICT OF NEW YORK",
        document_id="doc1",
        page_number=1,
        source_text="Verbatim text",
        start_offset=0,
        end_offset=29,
        confidence=0.95,
    )

    gold_ent = GoldEntity(
        document_id="doc1",
        entity_type="COURT",
        text="SOUTHERN DISTRICT OF NEW YORK",
    )

    m, _ = evaluator.evaluate_entities(
        predicted_entities=[c_ent.model_dump()],
        gold_entities=[gold_ent],
    )

    assert m.true_positives == 1
    assert m.precision == 1.0
