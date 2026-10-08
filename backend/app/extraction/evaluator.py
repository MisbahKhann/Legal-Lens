"""
Evaluation Framework for Step 3 Deterministic Legal Entity Extraction.
Compares extracted candidate entities against gold-standard ground truth annotations
and computes Precision, Recall, and F1 Score metrics per category and overall.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from app.extraction.models import (
    ExtractedCandidateEntity,
    DeterministicExtractionResult,
)


class GoldAnnotation(BaseModel):
    """
    Manually verified gold-standard target entity annotation.
    """

    document_id: str
    page_number: int = Field(default=1, ge=1)
    category: str
    original_value: str
    normalized_value: Optional[str] = None


class CategoryMetrics(BaseModel):
    """Precision, Recall, and F1 metrics for an extraction category."""

    category: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    def compute_scores(self) -> None:
        tp = self.true_positives
        fp = self.false_positives
        fn = self.false_negatives

        self.precision = (
            tp / (tp + fp) if (tp + fp) > 0 else 1.0 if tp == 0 and fp == 0 else 0.0
        )
        self.recall = (
            tp / (tp + fn) if (tp + fn) > 0 else 1.0 if tp == 0 and fn == 0 else 0.0
        )
        if self.precision + self.recall > 0:
            self.f1_score = (
                2 * (self.precision * self.recall) / (self.precision + self.recall)
            )
        else:
            self.f1_score = 0.0


class EvaluationReport(BaseModel):
    """Full evaluation report summarizing metrics across all categories."""

    total_extracted: int = 0
    total_gold_annotations: int = 0
    category_metrics: Dict[str, CategoryMetrics] = Field(default_factory=dict)
    overall_metrics: CategoryMetrics = Field(
        default_factory=lambda: CategoryMetrics(category="OVERALL")
    )

    def print_summary(self) -> str:
        """Renders formatted evaluation report table."""
        lines = [
            "=" * 75,
            " STEP 3 DETERMINISTIC EXTRACTION EVALUATION REPORT",
            "=" * 75,
            f"{'Category':<22} | {'TP':<4} | {'FP':<4} | {'FN':<4} | {'Precision':<9} | {'Recall':<8} | {'F1-Score':<8}",
            "-" * 75,
        ]

        for cat, m in self.category_metrics.items():
            lines.append(
                f"{cat:<22} | {m.true_positives:<4} | {m.false_positives:<4} | {m.false_negatives:<4} | "
                f"{m.precision * 100:>8.2f}% | {m.recall * 100:>7.2f}% | {m.f1_score * 100:>7.2f}%"
            )

        lines.append("-" * 75)
        o = self.overall_metrics
        lines.append(
            f"{'OVERALL (TOTAL)':<22} | {o.true_positives:<4} | {o.false_positives:<4} | {o.false_negatives:<4} | "
            f"{o.precision * 100:>8.2f}% | {o.recall * 100:>7.2f}% | {o.f1_score * 100:>7.2f}%"
        )
        lines.append("=" * 75)
        return "\n".join(lines)


class ExtractionEvaluator:
    """
    Evaluator tool comparing deterministic candidate extractions against ground-truth annotations.
    """

    @staticmethod
    def _is_match(candidate: ExtractedCandidateEntity, gold: GoldAnnotation) -> bool:
        """Determines if candidate extraction matches a gold annotation."""
        if candidate.document_id != gold.document_id:
            return False
        if candidate.category != gold.category:
            return False
        if candidate.page_number != gold.page_number:
            return False

        # Match either normalized value or original value (case-insensitive substring/equality)
        cand_orig = candidate.original_value.strip().lower()
        cand_norm = str(candidate.normalized_value).strip().lower()
        gold_orig = gold.original_value.strip().lower()
        gold_norm = (gold.normalized_value or "").strip().lower()

        if gold_orig in cand_orig or cand_orig in gold_orig:
            return True
        if gold_norm and (gold_norm in cand_norm or cand_norm in gold_norm):
            return True

        return False

    def evaluate(
        self,
        results: List[DeterministicExtractionResult],
        gold_annotations: List[GoldAnnotation],
    ) -> EvaluationReport:
        """
        Calculates precision, recall, and F1 scores across all categories.
        """
        all_candidates: List[ExtractedCandidateEntity] = []
        for res in results:
            all_candidates.extend(res.candidates)

        categories = set(c.category for c in all_candidates) | set(
            g.category for g in gold_annotations
        )
        category_metrics: Dict[str, CategoryMetrics] = {
            cat: CategoryMetrics(category=cat) for cat in categories
        }

        overall_tp = 0
        overall_fp = 0
        overall_fn = 0

        for cat in categories:
            cat_cands = [c for c in all_candidates if c.category == cat]
            cat_golds = [g for g in gold_annotations if g.category == cat]

            matched_gold_indices = set()
            tp = 0
            fp = 0

            for cand in cat_cands:
                matched = False
                for idx, gold in enumerate(cat_golds):
                    if idx not in matched_gold_indices and self._is_match(cand, gold):
                        tp += 1
                        matched_gold_indices.add(idx)
                        matched = True
                        break
                if not matched:
                    fp += 1

            fn = len(cat_golds) - len(matched_gold_indices)

            m = category_metrics[cat]
            m.true_positives = tp
            m.false_positives = fp
            m.false_negatives = fn
            m.compute_scores()

            overall_tp += tp
            overall_fp += fp
            overall_fn += fn

        overall_m = CategoryMetrics(
            category="OVERALL",
            true_positives=overall_tp,
            false_positives=overall_fp,
            false_negatives=overall_fn,
        )
        overall_m.compute_scores()

        return EvaluationReport(
            total_extracted=len(all_candidates),
            total_gold_annotations=len(gold_annotations),
            category_metrics=category_metrics,
            overall_metrics=overall_m,
        )
