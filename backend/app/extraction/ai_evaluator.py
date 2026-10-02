"""
AI Evaluation and Reporting module for Step 4 AI Extraction pipeline.
Allows extracted candidate entities and relations to be compared against expected ground-truth benchmarks.
"""

from typing import List, Dict, Any, Set, Tuple, Optional
from pydantic import BaseModel, Field

from app.extraction.ai_models import AIExtractionResult, CandidateEntity, CandidateRelation


class EvaluationMetric(BaseModel):
    """Container for Precision, Recall, and F1 evaluation metrics."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    def compute(self) -> None:
        """Computes Precision, Recall, and F1 score."""
        tp = self.true_positives
        fp = self.false_positives
        fn = self.false_negatives

        self.precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 0.0
        self.recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 0.0
        if (self.precision + self.recall) > 0:
            self.f1_score = round(2 * (self.precision * self.recall) / (self.precision + self.recall), 4)
        else:
            self.f1_score = 0.0


class EvaluationReport(BaseModel):
    """Complete evaluation report comparing predicted extractions against ground truth."""
    document_id: str
    entity_metrics: EvaluationMetric = Field(default_factory=EvaluationMetric)
    relation_metrics: EvaluationMetric = Field(default_factory=EvaluationMetric)
    detailed_entity_matches: List[Dict[str, Any]] = Field(default_factory=list)
    detailed_relation_matches: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_expected_entities: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_expected_relations: List[Dict[str, Any]] = Field(default_factory=list)


class AIEvaluator:
    """
    Evaluates Step 4 AI extractions against expected entities and relations ground-truth dataset.
    """

    @classmethod
    def evaluate(
        cls,
        prediction: AIExtractionResult,
        expected_entities: List[Dict[str, Any]],
        expected_relations: List[Dict[str, Any]]
    ) -> EvaluationReport:
        """
        Compares predicted AIExtractionResult against ground truth entities and relations.

        Args:
            prediction: AIExtractionResult from Step 4.
            expected_entities: List of expected entity dicts: [{"entity_type": "PERSON", "text": "...", "page_number": 1}]
            expected_relations: List of expected relation dicts: [{"relation_type": "WORKS_FOR", "source_text": "...", "target_text": "..."}]

        Returns:
            EvaluationReport containing detailed metrics and matches.
        """
        report = EvaluationReport(document_id=prediction.document_id)

        # 1. Evaluate Entities
        matched_expected_ent_indices: Set[int] = set()
        tp_ent = 0
        fp_ent = 0

        for pred_ent in prediction.entities:
            matched_idx = cls._match_entity(pred_ent, expected_entities, matched_expected_ent_indices)
            if matched_idx is not None:
                tp_ent += 1
                matched_expected_ent_indices.add(matched_idx)
                report.detailed_entity_matches.append({
                    "status": "TRUE_POSITIVE",
                    "predicted": pred_ent.model_dump(mode="json"),
                    "expected": expected_entities[matched_idx]
                })
            else:
                fp_ent += 1
                report.detailed_entity_matches.append({
                    "status": "FALSE_POSITIVE",
                    "predicted": pred_ent.model_dump(mode="json")
                })

        fn_ent = len(expected_entities) - len(matched_expected_ent_indices)
        for i, exp_ent in enumerate(expected_entities):
            if i not in matched_expected_ent_indices:
                report.unmatched_expected_entities.append(exp_ent)

        report.entity_metrics.true_positives = tp_ent
        report.entity_metrics.false_positives = fp_ent
        report.entity_metrics.false_negatives = fn_ent
        report.entity_metrics.compute()

        # 2. Evaluate Relations
        matched_expected_rel_indices: Set[int] = set()
        tp_rel = 0
        fp_rel = 0

        for pred_rel in prediction.relations:
            matched_idx = cls._match_relation(pred_rel, expected_relations, matched_expected_rel_indices)
            if matched_idx is not None:
                tp_rel += 1
                matched_expected_rel_indices.add(matched_idx)
                report.detailed_relation_matches.append({
                    "status": "TRUE_POSITIVE",
                    "predicted": pred_rel.model_dump(mode="json"),
                    "expected": expected_relations[matched_idx]
                })
            else:
                fp_rel += 1
                report.detailed_relation_matches.append({
                    "status": "FALSE_POSITIVE",
                    "predicted": pred_rel.model_dump(mode="json")
                })

        fn_rel = len(expected_relations) - len(matched_expected_rel_indices)
        for i, exp_rel in enumerate(expected_relations):
            if i not in matched_expected_rel_indices:
                report.unmatched_expected_relations.append(exp_rel)

        report.relation_metrics.true_positives = tp_rel
        report.relation_metrics.false_positives = fp_rel
        report.relation_metrics.false_negatives = fn_rel
        report.relation_metrics.compute()

        return report

    @classmethod
    def _match_entity(
        cls,
        pred_ent: CandidateEntity,
        expected_entities: List[Dict[str, Any]],
        already_matched: Set[int]
    ) -> Optional[int]:
        """Fuzzy matches candidate entity against ground truth list."""
        for i, exp in enumerate(expected_entities):
            if i in already_matched:
                continue

            exp_type = str(exp.get("entity_type", "")).upper()
            exp_text = str(exp.get("text", "")).strip().lower()
            exp_page = exp.get("page_number")

            if pred_ent.entity_type.value == exp_type:
                pred_text = pred_ent.text.strip().lower()
                if pred_text == exp_text or exp_text in pred_text or pred_text in exp_text:
                    if exp_page is None or pred_ent.page_number == exp_page:
                        return i
        return None

    @classmethod
    def _match_relation(
        cls,
        pred_rel: CandidateRelation,
        expected_relations: List[Dict[str, Any]],
        already_matched: Set[int]
    ) -> Optional[int]:
        """Fuzzy matches candidate relation against ground truth list."""
        for i, exp in enumerate(expected_relations):
            if i in already_matched:
                continue

            exp_rel_type = str(exp.get("relation_type", "")).upper()
            exp_src = str(exp.get("source_text", exp.get("source", ""))).strip().lower()
            exp_tgt = str(exp.get("target_text", exp.get("target", ""))).strip().lower()

            if pred_rel.relation_type.value == exp_rel_type:
                pred_src = pred_rel.source_entity.text.strip().lower()
                pred_tgt = pred_rel.target_entity.text.strip().lower()

                src_match = pred_src == exp_src or exp_src in pred_src or pred_src in exp_src
                tgt_match = pred_tgt == exp_tgt or exp_tgt in pred_tgt or pred_tgt in exp_tgt

                if src_match and tgt_match:
                    return i
        return None
