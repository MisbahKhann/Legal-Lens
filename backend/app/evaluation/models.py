"""
Data models and schemas for Step 11: Extraction Evaluation & Benchmarking.
Provides gold-standard dataset representations, component metric containers handling
zero denominators safely, and full evaluation report models.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Union, Tuple
from uuid import uuid4
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Ground-Truth Gold-Standard Dataset Models
# ---------------------------------------------------------------------------


class GoldEntity(BaseModel):
    """Ground-truth expected entity annotation."""

    entity_id: str = Field(
        default_factory=lambda: f"gold_ent_{uuid4().hex[:8]}",
        description="Unique identifier for gold entity.",
    )
    document_id: str = Field(..., description="Target document ID.")
    entity_type: str = Field(
        ..., description="Expected entity type (e.g. COURT, STATUTE, PARTY, PERSON)."
    )
    text: str = Field(..., description="Expected entity verbatim text or name.")
    normalized_value: Optional[str] = Field(
        default=None, description="Expected normalized value if applicable."
    )
    page_number: Optional[int] = Field(
        default=None, ge=1, description="Source page number."
    )
    start_offset: Optional[int] = Field(
        default=None, ge=0, description="Char start offset."
    )
    end_offset: Optional[int] = Field(
        default=None, ge=0, description="Char end offset."
    )


class GoldRelationship(BaseModel):
    """Ground-truth expected relationship annotation."""

    relation_id: str = Field(
        default_factory=lambda: f"gold_rel_{uuid4().hex[:8]}",
        description="Unique identifier for gold relationship.",
    )
    document_id: str = Field(..., description="Target document ID.")
    source_entity_text: str = Field(..., description="Source entity text or ID.")
    relation_type: str = Field(
        ..., description="Expected relationship type (e.g. FILED_IN, CITES, APPLIES)."
    )
    target_entity_text: str = Field(..., description="Target entity text or ID.")
    page_number: Optional[int] = Field(
        default=None, ge=1, description="Source page number."
    )


class GoldEvent(BaseModel):
    """Ground-truth expected timeline event annotation."""

    event_id: str = Field(
        default_factory=lambda: f"gold_evt_{uuid4().hex[:8]}",
        description="Unique identifier for gold event.",
    )
    document_id: str = Field(..., description="Target document ID.")
    event_type: str = Field(
        default="EVENT", description="Event category (e.g. FILING, HEARING, EVENT)."
    )
    description: str = Field(..., description="Event description or title.")
    event_date: Optional[str] = Field(
        default=None,
        description="Expected ISO date string (YYYY-MM-DD, YYYY-MM, YYYY).",
    )
    start_date: Optional[str] = Field(
        default=None, description="Expected ISO start date if range."
    )
    end_date: Optional[str] = Field(
        default=None, description="Expected ISO end date if range."
    )
    page_number: Optional[int] = Field(
        default=None, ge=1, description="Source page number."
    )


class GoldEquivalencePair(BaseModel):
    """Ground-truth entity resolution equivalence assertion."""

    document_id: Optional[str] = Field(
        default=None, description="Source document ID if document-bound."
    )
    entity_text_1: str = Field(..., description="First entity mention text.")
    entity_text_2: str = Field(..., description="Second entity mention text.")
    are_equivalent: bool = Field(
        default=True,
        description="True if entities refer to same real-world entity, False if distinct.",
    )
    canonical_name: Optional[str] = Field(
        default=None, description="Expected canonical name if equivalent."
    )


class GoldDocumentData(BaseModel):
    """Gold-standard annotations for a single legal document."""

    document_id: str = Field(..., description="Target document ID.")
    case_id: Optional[str] = Field(default=None, description="Case identifier.")
    entities: List[GoldEntity] = Field(
        default_factory=list, description="Expected entities."
    )
    relationships: List[GoldRelationship] = Field(
        default_factory=list, description="Expected relationships."
    )
    events: List[GoldEvent] = Field(
        default_factory=list, description="Expected timeline events."
    )
    equivalence_pairs: List[GoldEquivalencePair] = Field(
        default_factory=list, description="Expected entity resolution pairs."
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional document ground-truth metadata."
    )


class GoldDataset(BaseModel):
    """Complete gold-standard evaluation dataset."""

    dataset_id: str = Field(
        default="gold_std_v1", description="Identifier for dataset."
    )
    description: str = Field(
        default="Gold standard dataset for legal knowledge graph evaluation.",
        description="Dataset description.",
    )
    is_illustrative: bool = Field(
        default=False,
        description="Flag indicating if dataset is an illustrative sample fixture.",
    )
    documents: List[GoldDocumentData] = Field(
        default_factory=list, description="List of annotated documents."
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Dataset creation timestamp.",
    )


# ---------------------------------------------------------------------------
# Metric Containers with Zero-Denominator Safety
# ---------------------------------------------------------------------------


class ExtractionMetrics(BaseModel):
    """Precision, Recall, and F1 metrics for entity/relationship extraction."""

    category: str = Field(default="OVERALL", description="Category or scope name.")
    true_positives: int = Field(default=0, ge=0)
    false_positives: int = Field(default=0, ge=0)
    false_negatives: int = Field(default=0, ge=0)
    precision: Optional[float] = Field(default=None)
    recall: Optional[float] = Field(default=None)
    f1_score: Optional[float] = Field(default=None)
    is_calculable: bool = Field(
        default=True,
        description="False if metric could not be calculated (e.g. empty ground truth & predictions).",
    )
    note: Optional[str] = Field(
        default=None, description="Explanation for metric state."
    )

    def compute_scores(self) -> None:
        """Computes precision, recall, and F1 score safely handling zero denominators."""
        tp = self.true_positives
        fp = self.false_positives
        fn = self.false_negatives

        # Zero denominator check: no predictions and no ground truth
        if tp == 0 and fp == 0 and fn == 0:
            self.precision = None
            self.recall = None
            self.f1_score = None
            self.is_calculable = False
            self.note = "No predictions and no ground truth available (0/0)."
            return

        self.is_calculable = True

        # Precision calculation
        if (tp + fp) > 0:
            self.precision = round(tp / (tp + fp), 4)
        else:
            self.precision = 0.0

        # Recall calculation
        if (tp + fn) > 0:
            self.recall = round(tp / (tp + fn), 4)
        else:
            self.recall = 0.0

        # F1 calculation
        if (self.precision is not None and self.recall is not None) and (
            self.precision + self.recall > 0
        ):
            self.f1_score = round(
                2 * (self.precision * self.recall) / (self.precision + self.recall), 4
            )
        else:
            self.f1_score = 0.0


class ResolutionMetrics(BaseModel):
    """Metrics for Entity Resolution / Deduplication."""

    total_pairs_evaluated: int = Field(default=0, ge=0)
    true_positives: int = Field(default=0, ge=0)
    false_positives: int = Field(default=0, ge=0)
    false_negatives: int = Field(default=0, ge=0)
    true_negatives: int = Field(default=0, ge=0)
    pairwise_precision: Optional[float] = Field(default=None)
    pairwise_recall: Optional[float] = Field(default=None)
    pairwise_f1: Optional[float] = Field(default=None)
    accuracy: Optional[float] = Field(default=None)
    is_calculable: bool = Field(default=True)
    note: Optional[str] = Field(default=None)

    def compute_scores(self) -> None:
        tp, fp, fn, tn = (
            self.true_positives,
            self.false_positives,
            self.false_negatives,
            self.true_negatives,
        )
        total = tp + fp + fn + tn
        self.total_pairs_evaluated = total

        if total == 0:
            self.pairwise_precision = None
            self.pairwise_recall = None
            self.pairwise_f1 = None
            self.accuracy = None
            self.is_calculable = False
            self.note = "No equivalence pairs evaluated."
            return

        self.is_calculable = True
        self.pairwise_precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        self.pairwise_recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0

        p, r = self.pairwise_precision, self.pairwise_recall
        if p + r > 0:
            self.pairwise_f1 = round(2 * (p * r) / (p + r), 4)
        else:
            self.pairwise_f1 = 0.0

        self.accuracy = round((tp + tn) / total, 4)


class TemporalMetrics(BaseModel):
    """Metrics for Temporal Event & Date Extraction."""

    total_gold_events: int = Field(default=0, ge=0)
    total_predicted_events: int = Field(default=0, ge=0)
    matched_events_count: int = Field(default=0, ge=0)
    exact_date_matches: int = Field(default=0, ge=0)
    partial_date_matches: int = Field(default=0, ge=0)
    date_matching_precision: Optional[float] = Field(default=None)
    date_matching_recall: Optional[float] = Field(default=None)
    date_matching_f1: Optional[float] = Field(default=None)
    is_calculable: bool = Field(default=True)
    note: Optional[str] = Field(default=None)

    def compute_scores(self) -> None:
        p_cnt = self.total_predicted_events
        g_cnt = self.total_gold_events
        m_cnt = self.matched_events_count

        if p_cnt == 0 and g_cnt == 0:
            self.date_matching_precision = None
            self.date_matching_recall = None
            self.date_matching_f1 = None
            self.is_calculable = False
            self.note = "No temporal events evaluated."
            return

        self.is_calculable = True
        self.date_matching_precision = round(m_cnt / p_cnt, 4) if p_cnt > 0 else 0.0
        self.date_matching_recall = round(m_cnt / g_cnt, 4) if g_cnt > 0 else 0.0

        p, r = self.date_matching_precision, self.date_matching_recall
        if p + r > 0:
            self.date_matching_f1 = round(2 * (p * r) / (p + r), 4)
        else:
            self.date_matching_f1 = 0.0


class ValidationMetrics(BaseModel):
    """Metrics for Ontology & Schema Validation."""

    total_items_validated: int = Field(default=0, ge=0)
    valid_items_count: int = Field(default=0, ge=0)
    invalid_items_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    review_required_count: int = Field(default=0, ge=0)
    invalid_rate: Optional[float] = Field(default=None)
    valid_rate: Optional[float] = Field(default=None)

    def compute_scores(self) -> None:
        tot = self.total_items_validated
        if tot == 0:
            self.invalid_rate = None
            self.valid_rate = None
            return
        self.invalid_rate = round(self.invalid_items_count / tot, 4)
        self.valid_rate = round(self.valid_items_count / tot, 4)


class ProvenanceMetrics(BaseModel):
    """Metrics for Extraction Provenance Completeness."""

    total_evaluated_items: int = Field(default=0, ge=0)
    items_with_page_number: int = Field(default=0, ge=0)
    items_with_offsets: int = Field(default=0, ge=0)
    items_with_source_text: int = Field(default=0, ge=0)
    fully_provenanced_items: int = Field(default=0, ge=0)
    provenance_completeness_rate: Optional[float] = Field(default=None)

    def compute_scores(self) -> None:
        tot = self.total_evaluated_items
        if tot == 0:
            self.provenance_completeness_rate = None
            return
        self.provenance_completeness_rate = round(self.fully_provenanced_items / tot, 4)


class EscalationMetrics(BaseModel):
    """Metrics for Human-Review Escalation."""

    total_candidates_processed: int = Field(default=0, ge=0)
    escalated_for_review_count: int = Field(default=0, ge=0)
    approved_without_review_count: int = Field(default=0, ge=0)
    escalation_rate: Optional[float] = Field(default=None)

    def compute_scores(self) -> None:
        tot = self.total_candidates_processed
        if tot == 0:
            self.escalation_rate = None
            return
        self.escalation_rate = round(self.escalated_for_review_count / tot, 4)


class GraphConsistencyMetrics(BaseModel):
    """Metrics for Knowledge Graph Consistency (in-memory, no Neo4j required)."""

    total_nodes: int = Field(default=0, ge=0)
    total_edges: int = Field(default=0, ge=0)
    dangling_edges_count: int = Field(
        default=0, ge=0, description="Edges referencing non-existent nodes."
    )
    orphan_nodes_count: int = Field(
        default=0, ge=0, description="Nodes with zero connected edges."
    )
    invalid_triplet_types_count: int = Field(
        default=0, ge=0, description="Triplets violating Step 1 domain/range rules."
    )
    graph_consistency_score: Optional[float] = Field(
        default=None, description="Ratio of valid edges to total edges (0.0 to 1.0)."
    )

    def compute_scores(self) -> None:
        tot_e = self.total_edges
        if tot_e == 0:
            self.graph_consistency_score = 1.0 if self.total_nodes > 0 else None
            return
        invalid_e = self.dangling_edges_count + self.invalid_triplet_types_count
        valid_e = max(0, tot_e - invalid_e)
        self.graph_consistency_score = round(valid_e / tot_e, 4)


# ---------------------------------------------------------------------------
# Complete Step 11 Evaluation Report Model
# ---------------------------------------------------------------------------


class Step11EvaluationReport(BaseModel):
    """
    Comprehensive, reproducible evaluation report for Step 11.
    Includes run metadata, per-component metrics, zero-denominator notes,
    and formatted summary output.
    """

    run_id: str = Field(
        default_factory=lambda: f"eval_run_{uuid4().hex[:12]}",
        description="Unique evaluation execution ID.",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution timestamp in UTC.",
    )
    dataset_id: str = Field(..., description="Gold-standard dataset identifier.")
    is_illustrative_fixture: bool = Field(
        default=False,
        description="Indicates if evaluation ran against illustrative sample data.",
    )
    num_documents_evaluated: int = Field(default=0, ge=0)
    model_configuration: Dict[str, Any] = Field(
        default_factory=dict, description="Model and pipeline settings evaluated."
    )

    metric_definitions: Dict[str, str] = Field(
        default_factory=lambda: {
            "Precision": "TP / (TP + FP) — proportion of predicted extractions that are correct.",
            "Recall": "TP / (TP + FN) — proportion of ground-truth annotations correctly identified.",
            "F1_Score": "Harmonic mean of Precision and Recall: 2 * (P * R) / (P + R).",
            "Pairwise_Resolution": "Pairwise precision and recall on candidate entity equivalence pairs.",
            "Temporal_Matching": "Matching predictions against expected events and ISO dates.",
            "Provenance_Completeness": "Proportion of extractions with page_number, offsets, and source_text.",
            "Graph_Consistency": "In-memory graph triplet validity score without requiring live Neo4j.",
        }
    )
    matching_rules: Dict[str, str] = Field(
        default_factory=lambda: {
            "Entity_Matching": "Exact or normalized substring match on text, document ID, and entity_type.",
            "Relationship_Matching": "Match source entity text, relation_type, and target entity text.",
            "Temporal_Matching": "ISO date string equality or normalized date substring match.",
            "Resolution_Matching": "Cluster membership verification against gold equivalence pairs.",
        }
    )

    excluded_or_failed_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Counts of skipped, missing, or unscorable examples.",
    )

    # Component Level Metrics
    entity_metrics: ExtractionMetrics = Field(
        default_factory=lambda: ExtractionMetrics(category="ENTITY_OVERALL")
    )
    relationship_metrics: ExtractionMetrics = Field(
        default_factory=lambda: ExtractionMetrics(category="RELATIONSHIP_OVERALL")
    )
    resolution_metrics: ResolutionMetrics = Field(default_factory=ResolutionMetrics)
    temporal_metrics: TemporalMetrics = Field(default_factory=TemporalMetrics)
    validation_metrics: ValidationMetrics = Field(default_factory=ValidationMetrics)
    provenance_metrics: ProvenanceMetrics = Field(default_factory=ProvenanceMetrics)
    escalation_metrics: EscalationMetrics = Field(default_factory=EscalationMetrics)
    graph_consistency_metrics: GraphConsistencyMetrics = Field(
        default_factory=GraphConsistencyMetrics
    )

    # Detailed per-category breakdowns
    per_category_entity: Dict[str, ExtractionMetrics] = Field(default_factory=dict)
    per_category_relationship: Dict[str, ExtractionMetrics] = Field(
        default_factory=dict
    )

    def print_summary(self) -> str:
        """Generates a clean, readable ASCII evaluation summary report."""
        lines = [
            "=" * 78,
            " LEGAL LENS — STEP 11 EXTRACTION EVALUATION REPORT",
            "=" * 78,
            f" Run ID       : {self.run_id}",
            f" Timestamp    : {self.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f" Dataset ID   : {self.dataset_id}"
            + (" (ILLUSTRATIVE SAMPLE)" if self.is_illustrative_fixture else ""),
            f" Documents    : {self.num_documents_evaluated}",
            "-" * 78,
            " 1. LEGAL ENTITY EXTRACTION METRICS",
            "-" * 78,
            f" {'Category':<22} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8}",
            "-" * 78,
        ]

        def fmt_val(v: Optional[float]) -> str:
            return f"{v * 100:>7.2f}%" if v is not None else "    N/A  "

        for cat, m in self.per_category_entity.items():
            lines.append(
                f" {cat:<22} | {m.true_positives:<4} | {m.false_positives:<4} | {m.false_negatives:<4} | "
                f"{fmt_val(m.precision):>9} | {fmt_val(m.recall):>8} | {fmt_val(m.f1_score):>8}"
            )

        e = self.entity_metrics
        lines.append("-" * 78)
        lines.append(
            f" {'OVERALL ENTITIES':<22} | {e.true_positives:<4} | {e.false_positives:<4} | {e.false_negatives:<4} | "
            f"{fmt_val(e.precision):>9} | {fmt_val(e.recall):>8} | {fmt_val(e.f1_score):>8}"
        )

        lines.extend(
            [
                "-" * 78,
                " 2. RELATIONSHIP EXTRACTION METRICS",
                "-" * 78,
                f" {'Category':<22} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8}",
                "-" * 78,
            ]
        )

        for cat, m in self.per_category_relationship.items():
            lines.append(
                f" {cat:<22} | {m.true_positives:<4} | {m.false_positives:<4} | {m.false_negatives:<4} | "
                f"{fmt_val(m.precision):>9} | {fmt_val(m.recall):>8} | {fmt_val(m.f1_score):>8}"
            )

        r = self.relationship_metrics
        lines.append("-" * 78)
        lines.append(
            f" {'OVERALL RELATIONS':<22} | {r.true_positives:<4} | {r.false_positives:<4} | {r.false_negatives:<4} | "
            f"{fmt_val(r.precision):>9} | {fmt_val(r.recall):>8} | {fmt_val(r.f1_score):>8}"
        )

        res = self.resolution_metrics
        t = self.temporal_metrics
        v = self.validation_metrics
        p = self.provenance_metrics
        esc = self.escalation_metrics
        g = self.graph_consistency_metrics

        lines.extend(
            [
                "=" * 78,
                " 3. PIPELINE COMPONENT METRICS",
                "-" * 78,
                f" Entity Resolution Pairwise F1 : {fmt_val(res.pairwise_f1)} (Evaluated Pairs: {res.total_pairs_evaluated})",
                f" Temporal Date/Event Matching F1: {fmt_val(t.date_matching_f1)} (Matched Events: {t.matched_events_count}/{t.total_gold_events})",
                f" Schema Validation Valid Rate  : {fmt_val(v.valid_rate)} (Invalid Items: {v.invalid_items_count})",
                f" Provenance Completeness Rate  : {fmt_val(p.provenance_completeness_rate)} (Complete: {p.fully_provenanced_items}/{p.total_evaluated_items})",
                f" Human-Review Escalation Rate  : {fmt_val(esc.escalation_rate)} (Escalated: {esc.escalated_for_review_count})",
                f" Graph Triplet Consistency     : {fmt_val(g.graph_consistency_score)} (Dangling Edges: {g.dangling_edges_count})",
                "=" * 78,
            ]
        )
        return "\n".join(lines)
