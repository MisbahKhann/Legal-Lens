"""
Temporal Consistency Validator for Step 7.
Checks temporal logic, chronological consistency, invalid dates, and deadline rules.
Integrates directly with Step 6 Validation framework structures.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict

from app.validation.models import (
    ValidationRecord,
    ValidationStatus,
    ValidationSeverity,
    RecordType,
)
from app.temporal.models import (
    TimelineEvent,
    TemporalRelationship,
    RelativeTemporalExpression,
    TemporalStatus,
    CaseTimeline,
)
from app.schema.relationship_types import RelationshipType

logger = logging.getLogger(__name__)


class TemporalValidator:
    """
    Validates temporal events, date logic, and chronological consistency.
    Returns ValidationRecord objects compatible with Step 6 pipeline.
    """

    def validate_timeline(self, timeline: CaseTimeline) -> List[ValidationRecord]:
        """
        Executes all temporal consistency checks on a CaseTimeline.
        """
        records: List[ValidationRecord] = []

        # Map event_id -> TimelineEvent
        event_map: Dict[str, TimelineEvent] = {e.event_id: e for e in timeline.events}

        # 1. Check for Invalid Calendar Dates
        for event in timeline.events:
            if not event.event_date and not event.start_date:
                continue

            if event.temporal_status == TemporalStatus.REVIEW_REQUIRED or (
                event.provenance
                and "Invalid calendar date" in (event.provenance.source_text or "")
            ):
                records.append(
                    ValidationRecord(
                        record_type=RecordType.ENTITY,
                        status=ValidationStatus.INVALID,
                        severity=ValidationSeverity.HIGH,
                        validation_rule="INVALID_CALENDAR_DATE",
                        message=f"Event '{event.description}' has an invalid or impossible calendar date.",
                        entity_id=event.canonical_entity_id or event.event_id,
                    )
                )

        # 2. Check for Contradictory Dates for the same entity/event
        # Group events by canonical_entity_id
        canonical_group: Dict[str, List[TimelineEvent]] = defaultdict(list)
        for event in timeline.events:
            if event.canonical_entity_id:
                canonical_group[event.canonical_entity_id].append(event)

        for cid, group in canonical_group.items():
            dates = {e.event_date for e in group if e.event_date}
            if len(dates) > 1:
                records.append(
                    ValidationRecord(
                        record_type=RecordType.ENTITY,
                        status=ValidationStatus.REVIEW_REQUIRED,
                        severity=ValidationSeverity.HIGH,
                        validation_rule="CONTRADICTORY_EVENT_DATES",
                        message=f"Entity '{cid}' has multiple contradictory dates: {sorted(list(dates))}.",
                        entity_id=cid,
                    )
                )

        # 3. Check Unresolved Relative Temporal Expressions
        for rel_expr in timeline.unresolved_expressions:
            if rel_expr.temporal_status == TemporalStatus.REVIEW_REQUIRED:
                records.append(
                    ValidationRecord(
                        record_type=RecordType.ENTITY,
                        status=ValidationStatus.REVIEW_REQUIRED,
                        severity=ValidationSeverity.MEDIUM,
                        validation_rule="UNRESOLVED_RELATIVE_DATE",
                        message=f"Relative temporal expression '{rel_expr.raw_text}' could not be resolved to an exact date.",
                        source_document_id=rel_expr.source_document_id,
                        source_page=rel_expr.source_page,
                    )
                )

        # 4. Check Conflicting Chronology in Temporal Relationships (BEFORE / AFTER)
        for rel in timeline.temporal_relationships:
            src_ev = event_map.get(rel.source_event_id)
            tgt_ev = event_map.get(rel.target_event_id)

            if not src_ev or not tgt_ev:
                continue

            if src_ev.event_date and tgt_ev.event_date:
                # Compare ISO date strings YYYY-MM-DD
                d_src = src_ev.event_date[:10]
                d_tgt = tgt_ev.event_date[:10]

                if rel.relationship_type == RelationshipType.BEFORE:
                    if d_src > d_tgt:
                        records.append(
                            ValidationRecord(
                                record_type=RecordType.RELATIONSHIP,
                                status=ValidationStatus.REVIEW_REQUIRED,
                                severity=ValidationSeverity.HIGH,
                                validation_rule="CONFLICTING_CHRONOLOGY",
                                message=f"Conflicting chronology: '{src_ev.description}' ({d_src}) is marked BEFORE '{tgt_ev.description}' ({d_tgt}).",
                                relationship_id=rel.relationship_id,
                            )
                        )
                elif rel.relationship_type == RelationshipType.AFTER:
                    if d_src < d_tgt:
                        records.append(
                            ValidationRecord(
                                record_type=RecordType.RELATIONSHIP,
                                status=ValidationStatus.REVIEW_REQUIRED,
                                severity=ValidationSeverity.HIGH,
                                validation_rule="CONFLICTING_CHRONOLOGY",
                                message=f"Conflicting chronology: '{src_ev.description}' ({d_src}) is marked AFTER '{tgt_ev.description}' ({d_tgt}).",
                                relationship_id=rel.relationship_id,
                            )
                        )

        # 5. Check HAS_DEADLINE rules (Deadline before triggering event)
        for rel in timeline.temporal_relationships:
            if rel.relationship_type == RelationshipType.HAS_DEADLINE:
                src_ev = event_map.get(rel.source_event_id)
                tgt_ev = event_map.get(rel.target_event_id)

                if src_ev and tgt_ev and src_ev.event_date and tgt_ev.event_date:
                    d_src = src_ev.event_date[:10]
                    d_tgt = tgt_ev.event_date[:10]
                    if d_tgt < d_src:
                        records.append(
                            ValidationRecord(
                                record_type=RecordType.RELATIONSHIP,
                                status=ValidationStatus.REVIEW_REQUIRED,
                                severity=ValidationSeverity.HIGH,
                                validation_rule="DEADLINE_BEFORE_TRIGGER",
                                message=f"Deadline anomaly: Deadline '{tgt_ev.description}' ({d_tgt}) is before triggering event '{src_ev.description}' ({d_src}).",
                                relationship_id=rel.relationship_id,
                            )
                        )

        return records
