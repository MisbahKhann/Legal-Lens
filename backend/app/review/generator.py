"""
Review candidate generator for Step 9.
Identifies uncertain entities, relationships, temporal events, and ambiguous entity resolution candidates,
transforming them into structured ReviewItem objects with rich source provenance context.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.review.models import ItemType, ReviewStatus, ReviewItem
from app.validation.models import ValidationResult, RecordType
from app.temporal.models import CaseTimeline, TemporalStatus
from app.resolution.models import ResolutionResult

logger = logging.getLogger(__name__)


class ReviewCandidateGenerator:
    """
    Scans validation, resolution, and temporal pipeline outputs to extract
    candidates that require human-in-the-loop review.
    High-confidence deterministic extractions are explicitly excluded.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.confidence_threshold = confidence_threshold

    def generate_review_items(
        self,
        validation_result: Optional[ValidationResult] = None,
        case_timeline: Optional[CaseTimeline] = None,
        resolution_result: Optional[ResolutionResult] = None,
        case_id: Optional[str] = None,
    ) -> List[ReviewItem]:
        """
        Generates structured ReviewItem records from pipeline outputs.

        Args:
            validation_result: Output from Step 6 Validation.
            case_timeline: Output from Step 7 Temporal Timeline.
            resolution_result: Output from Step 5 Entity Resolution.
            case_id: Explicit case ID.

        Returns:
            List of ReviewItem objects with status PENDING.
        """
        resolved_case_id = case_id
        if not resolved_case_id:
            if validation_result and validation_result.case_id:
                resolved_case_id = validation_result.case_id
            elif case_timeline and case_timeline.case_id:
                resolved_case_id = case_timeline.case_id
            elif resolution_result and resolution_result.case_id:
                resolved_case_id = resolution_result.case_id
            elif validation_result and validation_result.document_id:
                resolved_case_id = f"case_{validation_result.document_id}"
            else:
                resolved_case_id = "case_default"

        review_items: List[ReviewItem] = []

        # 1. Process Step 6 ValidationRecords (REVIEW_REQUIRED & WARNING)
        if validation_result:
            for rec in validation_result.review_required + validation_result.warnings:
                item_type = (
                    ItemType.RELATIONSHIP
                    if rec.record_type == RecordType.RELATIONSHIP
                    else ItemType.ENTITY
                )

                orig_pred: Dict[str, Any] = {
                    "rule": rec.validation_rule,
                    "message": rec.message,
                }
                if rec.supporting_evidence:
                    orig_pred["evidence"] = rec.supporting_evidence

                item = ReviewItem(
                    case_id=resolved_case_id,
                    item_type=item_type,
                    status=ReviewStatus.PENDING,
                    entity_id=rec.entity_id,
                    relationship_id=rec.relationship_id,
                    confidence=rec.confidence,
                    reason=rec.message,
                    validation_rule=rec.validation_rule,
                    original_prediction=orig_pred,
                    source_document_id=rec.source_document_id
                    or validation_result.document_id,
                    source_page=rec.source_page or 1,
                    source_text=rec.source_text or "",
                    provenance_details={
                        "validation_severity": (
                            rec.severity.value
                            if hasattr(rec.severity, "value")
                            else str(rec.severity)
                        ),
                        "validation_status": (
                            rec.status.value
                            if hasattr(rec.status, "value")
                            else str(rec.status)
                        ),
                    },
                )
                review_items.append(item)

        # 2. Process Step 5 Entity Resolution Ambiguities & Low-Confidence Entities/Relations
        if resolution_result:
            # Check unresolved / ambiguous entity groups
            if (
                hasattr(resolution_result, "unresolved_entities")
                and resolution_result.unresolved_entities
            ):
                for unres in resolution_result.unresolved_entities:
                    orig_pred = (
                        unres
                        if isinstance(unres, dict)
                        else {"raw_unresolved": str(unres)}
                    )
                    item = ReviewItem(
                        case_id=resolved_case_id,
                        item_type=ItemType.ENTITY_MERGE,
                        status=ReviewStatus.PENDING,
                        reason="Ambiguous entity resolution requiring human merge or separate decision",
                        original_prediction=orig_pred,
                        source_document_id=resolution_result.document_id,
                    )
                    review_items.append(item)

            # Check low-confidence canonical entities
            for ent in resolution_result.canonical_entities:
                first_m = ent.mentions[0] if ent.mentions else None
                conf = getattr(first_m, "confidence", 1.0) if first_m else 1.0
                if conf < self.confidence_threshold:
                    item = ReviewItem(
                        case_id=resolved_case_id,
                        item_type=ItemType.ENTITY,
                        status=ReviewStatus.PENDING,
                        entity_id=ent.canonical_id,
                        confidence=conf,
                        reason=f"Low entity extraction confidence ({conf:.2f} < {self.confidence_threshold})",
                        original_prediction={
                            "entity_id": ent.canonical_id,
                            "canonical_name": ent.canonical_name,
                            "entity_type": (
                                ent.entity_type.value
                                if hasattr(ent.entity_type, "value")
                                else str(ent.entity_type)
                            ),
                            "aliases": list(ent.aliases),
                        },
                        source_document_id=ent.document_id,
                        source_text=(
                            getattr(first_m, "source_text", ent.canonical_name)
                            if first_m
                            else ent.canonical_name
                        ),
                        source_page=(
                            getattr(first_m, "source_page", 1) if first_m else 1
                        ),
                        extraction_method=getattr(
                            first_m, "extraction_method", "GLINER_RELEX"
                        ),
                    )
                    review_items.append(item)

        # 3. Process Step 7 Temporal Issues
        if case_timeline:
            # Unresolved relative date expressions
            for rel_exp in case_timeline.unresolved_expressions:
                item = ReviewItem(
                    case_id=resolved_case_id,
                    item_type=ItemType.TEMPORAL,
                    status=ReviewStatus.PENDING,
                    confidence=0.5,
                    reason=f"Unresolved relative temporal expression: '{rel_exp.raw_text}'",
                    original_prediction={
                        "expression_id": rel_exp.expression_id,
                        "raw_text": rel_exp.raw_text,
                        "direction": rel_exp.direction,
                        "reference_event_type": rel_exp.reference_event_type,
                    },
                    source_document_id=rel_exp.source_document_id,
                    source_page=rel_exp.source_page or 1,
                    source_text=rel_exp.raw_text,
                    source_span=rel_exp.char_span,
                )
                review_items.append(item)

            # Contradictory, ambiguous, or review-required timeline events
            for ev in case_timeline.events:
                if (
                    ev.temporal_status
                    in [
                        TemporalStatus.AMBIGUOUS,
                        TemporalStatus.CONTRADICTORY,
                        TemporalStatus.REVIEW_REQUIRED,
                        TemporalStatus.UNRESOLVED,
                    ]
                    or ev.confidence < self.confidence_threshold
                ):
                    item = ReviewItem(
                        case_id=resolved_case_id,
                        item_type=ItemType.EVENT,
                        status=ReviewStatus.PENDING,
                        event_id=ev.event_id,
                        entity_id=ev.canonical_entity_id,
                        confidence=ev.confidence,
                        reason=f"Temporal status '{ev.temporal_status.value}' or low confidence ({ev.confidence:.2f})",
                        original_prediction={
                            "event_id": ev.event_id,
                            "description": ev.description,
                            "event_type": (
                                ev.event_type.value
                                if hasattr(ev.event_type, "value")
                                else str(ev.event_type)
                            ),
                            "event_date": ev.event_date,
                            "start_date": ev.start_date,
                            "end_date": ev.end_date,
                            "date_precision": (
                                ev.date_precision.value
                                if hasattr(ev.date_precision, "value")
                                else str(ev.date_precision)
                            ),
                            "temporal_status": (
                                ev.temporal_status.value
                                if hasattr(ev.temporal_status, "value")
                                else str(ev.temporal_status)
                            ),
                        },
                        source_document_id=ev.source_document_id,
                        source_page=ev.source_page or 1,
                        source_text=ev.source_text or "",
                        source_span=ev.char_span,
                        extraction_method=(
                            ev.extraction_method.value
                            if hasattr(ev.extraction_method, "value")
                            else str(ev.extraction_method)
                        ),
                    )
                    review_items.append(item)

        logger.info(
            "Generated %d review items for case %s", len(review_items), resolved_case_id
        )
        return review_items
