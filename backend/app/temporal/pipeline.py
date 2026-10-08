"""
Temporal Pipeline Orchestrator (Step 7).
Extracts, normalizes, associates, resolves relative expressions, validates,
and constructs the canonical CaseTimeline.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple

from app.ingestion.models import LegalDocument
from app.resolution.models import ResolutionResult
from app.validation.models import ValidationResult
from app.temporal.models import (
    CaseTimeline,
    TimelineEvent,
    TemporalRelationship,
    RelativeTemporalExpression,
    TemporalStatus,
    DatePrecision,
)
from app.temporal.date_normalizer import DateNormalizer
from app.temporal.relative_parser import RelativeTemporalParser
from app.temporal.event_associator import EventAssociator
from app.temporal.temporal_validator import TemporalValidator
from app.schema.entity_types import EntityType
from app.schema.provenance import Provenance, ExtractionMethod

logger = logging.getLogger(__name__)


class TemporalPipeline:
    """
    Step 7 Pipeline for Temporal Event & Timeline Extraction.
    """

    def __init__(
        self,
        date_normalizer: Optional[DateNormalizer] = None,
        relative_parser: Optional[RelativeTemporalParser] = None,
        event_associator: Optional[EventAssociator] = None,
        validator: Optional[TemporalValidator] = None,
    ):
        self.normalizer = date_normalizer or DateNormalizer()
        self.relative_parser = relative_parser or RelativeTemporalParser(
            self.normalizer
        )
        self.associator = event_associator or EventAssociator(
            self.normalizer, self.relative_parser
        )
        self.validator = validator or TemporalValidator()

    def process_timeline(
        self,
        document: LegalDocument,
        resolution_result: ResolutionResult,
        validation_result: Optional[ValidationResult] = None,
    ) -> CaseTimeline:
        """
        Main entry point for Step 7 temporal processing.

        Args:
            document: LegalDocument from Step 2.
            resolution_result: ResolutionResult from Step 5.
            validation_result: Optional ValidationResult from Step 6.

        Returns:
            CaseTimeline with sorted events, temporal relationships, and provenance.
        """
        logger.info(
            f"Starting Step 7 Temporal Pipeline for document '{document.document_id}'"
        )

        # 1. Extract events & relationships from resolution result
        timeline_events, temporal_relationships = (
            self.associator.process_resolution_result(resolution_result)
        )

        # 2. Extract relative temporal expressions from document text
        unresolved_relative: List[RelativeTemporalExpression] = []
        for page in document.pages:
            text = page.raw_text or page.normalized_text
            if not text:
                continue

            rel_expr = self.relative_parser.parse_expression(
                text=text,
                document_id=document.document_id,
                page_number=page.page_number,
                provenance=Provenance(
                    case_id=document.case_id or "default_case",
                    source_document_id=document.document_id,
                    source_page=page.page_number,
                    source_text=text[:100],
                    extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                ),
            )
            if rel_expr:
                # Attempt resolution against currently identified timeline_events
                resolved_expr = self.relative_parser.resolve_relative_expression(
                    rel_expr, timeline_events
                )

                if (
                    resolved_expr.temporal_status == TemporalStatus.RESOLVED
                    and resolved_expr.resolved_date
                ):
                    # Create derived timeline event
                    prov = Provenance(
                        case_id=document.case_id or "default_case",
                        source_document_id=document.document_id,
                        source_page=page.page_number,
                        source_text=resolved_expr.raw_text,
                        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                    )
                    derived_ev = TimelineEvent(
                        description=f"Derived Event: {resolved_expr.raw_text}",
                        event_date=resolved_expr.resolved_date.iso_value,
                        date_precision=resolved_expr.resolved_date.precision,
                        temporal_status=TemporalStatus.RESOLVED,
                        source_document_id=document.document_id,
                        source_page=page.page_number,
                        source_text=resolved_expr.raw_text,
                        derived_from=f"Derived from relative expression '{resolved_expr.raw_text}' relative to ref '{resolved_expr.reference_event_id}'",
                        provenance=prov,
                    )
                    timeline_events.append(derived_ev)
                else:
                    unresolved_relative.append(resolved_expr)

        # 3. Construct initial CaseTimeline
        case_timeline = CaseTimeline(
            document_id=document.document_id,
            case_id=document.case_id,
            events=timeline_events,
            temporal_relationships=temporal_relationships,
            unresolved_expressions=unresolved_relative,
        )

        # 4. Sort timeline chronologically
        case_timeline.sort_timeline()

        # 5. Run temporal consistency validation
        val_records = self.validator.validate_timeline(case_timeline)
        warning_msgs = [r.message for r in val_records]
        case_timeline.validation_warnings = warning_msgs

        # 6. Compute summary counts
        events_with_exact_date = sum(
            1
            for e in case_timeline.events
            if e.date_precision == DatePrecision.EXACT_DAY
        )
        events_with_partial_date = sum(
            1
            for e in case_timeline.events
            if e.date_precision in [DatePrecision.MONTH, DatePrecision.YEAR]
        )
        deadlines_count = sum(
            1
            for e in case_timeline.events
            if e.event_type in [EntityType.DEADLINE]
            or "deadline" in e.description.lower()
        )

        summary_counts: Dict[str, int] = {
            "total_temporal_expressions_detected": len(timeline_events)
            + len(unresolved_relative),
            "total_events_identified": len(case_timeline.events),
            "events_with_exact_dates": events_with_exact_date,
            "events_with_partial_dates": events_with_partial_date,
            "deadlines_count": deadlines_count,
            "temporal_relationships_count": len(case_timeline.temporal_relationships),
            "unresolved_temporal_expressions_count": len(unresolved_relative),
            "temporal_validation_warnings_count": len(warning_msgs),
        }
        case_timeline.summary_counts = summary_counts

        logger.info(
            f"Step 7 Temporal Pipeline complete: {len(case_timeline.events)} events, "
            f"{events_with_exact_date} exact dates, {len(warning_msgs)} warnings."
        )

        return case_timeline
