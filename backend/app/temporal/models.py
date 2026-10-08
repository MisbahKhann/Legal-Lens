"""
Data models for Step 7: Temporal Event & Timeline Extraction.
"""

from enum import Enum
from typing import Dict, Any, Optional, List, Tuple
from uuid import uuid4
from datetime import datetime, timezone
from pydantic import BaseModel, Field

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import Provenance, ExtractionMethod
from app.schema.temporal import TemporalProperties, EventStatus


class DatePrecision(str, Enum):
    """Granularity of extracted or normalized temporal expressions."""

    EXACT_DAY = "EXACT_DAY"  # YYYY-MM-DD
    MONTH = "MONTH"  # YYYY-MM
    YEAR = "YEAR"  # YYYY
    UNKNOWN_PARTIAL = "UNKNOWN_PARTIAL"  # Incomplete / unparseable format


class TemporalStatus(str, Enum):
    """Resolution and validation status of temporal events and expressions."""

    RESOLVED = "RESOLVED"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    CONTRADICTORY = "CONTRADICTORY"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


class NormalizedDate(BaseModel):
    """Structured representation of a normalized legal date expression."""

    raw_text: str = Field(
        ..., description="Original verbatim date string from document."
    )
    iso_value: Optional[str] = Field(
        default=None, description="ISO 8601 string (e.g. YYYY-MM-DD, YYYY-MM, YYYY)."
    )
    start_date: Optional[str] = Field(
        default=None, description="ISO start date if string represents a date range."
    )
    end_date: Optional[str] = Field(
        default=None, description="ISO end date if string represents a date range."
    )
    precision: DatePrecision = Field(
        default=DatePrecision.UNKNOWN_PARTIAL,
        description="Date precision / granularity.",
    )
    year: Optional[int] = Field(default=None, description="Extracted four-digit year.")
    month: Optional[int] = Field(default=None, description="Extracted month (1-12).")
    day: Optional[int] = Field(
        default=None, description="Extracted day of month (1-31)."
    )
    is_valid: bool = Field(
        default=True, description="False if calendar date is invalid (e.g. Feb 30)."
    )
    validation_note: Optional[str] = Field(
        default=None, description="Explanation if date is invalid/ambiguous."
    )


class RelativeTemporalExpression(BaseModel):
    """Model representing a relative temporal phrase and its resolution status."""

    expression_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for expression.",
    )
    raw_text: str = Field(
        ..., description="Original relative text snippet (e.g. '30 days after filing')."
    )
    direction: str = Field(
        default="AFTER", description="Direction: BEFORE, AFTER, IN_PERIOD, OFFSET."
    )
    delta_days: Optional[int] = Field(default=None, description="Offset in days.")
    delta_weeks: Optional[int] = Field(default=None, description="Offset in weeks.")
    delta_months: Optional[int] = Field(default=None, description="Offset in months.")
    delta_years: Optional[int] = Field(default=None, description="Offset in years.")
    reference_event_type: Optional[str] = Field(
        default=None,
        description="Target event category (e.g. 'FILING', 'HEARING', 'JUDGMENT').",
    )
    reference_event_id: Optional[str] = Field(
        default=None, description="Canonical entity ID of the anchor event if matched."
    )
    reference_date_iso: Optional[str] = Field(
        default=None, description="ISO date of the anchor event if matched."
    )
    resolved_date: Optional[NormalizedDate] = Field(
        default=None, description="Computed normalized date if successfully resolved."
    )
    temporal_status: TemporalStatus = Field(
        default=TemporalStatus.UNRESOLVED, description="Resolution status."
    )
    source_document_id: str = Field(..., description="Source document ID.")
    source_page: Optional[int] = Field(default=None, description="Page number.")
    char_span: Optional[Tuple[int, int]] = Field(
        default=None, description="Char offsets."
    )
    provenance: Optional[Provenance] = Field(
        default=None, description="Provenance record."
    )


class TimelineEvent(BaseModel):
    """
    Structured legal timeline event node representing a temporal occurrence in a case.
    """

    event_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique identifier for timeline event.",
    )
    canonical_entity_id: Optional[str] = Field(
        default=None, description="Associated Step 5 canonical entity ID if available."
    )
    event_type: EntityType = Field(
        default=EntityType.EVENT,
        description="Entity type (e.g., EVENT, FILING, HEARING, DEADLINE, CONTRACT).",
    )
    description: str = Field(
        ..., description="Human-readable event title or description."
    )
    event_date: Optional[str] = Field(
        default=None,
        description="Normalized ISO date string (YYYY-MM-DD, YYYY-MM, YYYY).",
    )
    start_date: Optional[str] = Field(
        default=None, description="ISO start date string for multi-day events."
    )
    end_date: Optional[str] = Field(
        default=None, description="ISO end date string for multi-day events."
    )
    date_precision: DatePrecision = Field(
        default=DatePrecision.UNKNOWN_PARTIAL, description="Date precision enum."
    )
    temporal_status: TemporalStatus = Field(
        default=TemporalStatus.RESOLVED, description="Temporal status."
    )
    source_document_id: str = Field(..., description="Document ID.")
    source_page: Optional[int] = Field(default=None, description="Page number.")
    source_text: Optional[str] = Field(
        default=None, description="Source verbatim text quote."
    )
    char_span: Optional[Tuple[int, int]] = Field(
        default=None, description="Char offsets."
    )
    confidence: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Confidence score."
    )
    extraction_method: ExtractionMethod = Field(
        default=ExtractionMethod.DETERMINISTIC_RULE, description="Extraction method."
    )
    related_entity_ids: List[str] = Field(
        default_factory=list,
        description="IDs of connected entities (e.g. Plaintiff, Court).",
    )
    derived_from: Optional[str] = Field(
        default=None,
        description="Traceability note if event date was derived from relative logic.",
    )
    provenance: Provenance = Field(..., description="Mandatory extraction lineage.")


class TemporalRelationship(BaseModel):
    """
    Edge connecting two timeline events or a timeline event to a date/deadline.
    """

    relationship_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Unique relationship ID."
    )
    source_event_id: str = Field(..., description="Source timeline event ID.")
    relationship_type: RelationshipType = Field(
        ...,
        description="Controlled relationship type (OCCURRED_ON, BEFORE, AFTER, HAS_DEADLINE).",
    )
    target_event_id: str = Field(
        ..., description="Target timeline event ID or Date ID."
    )
    properties: Dict[str, Any] = Field(
        default_factory=dict, description="Edge properties."
    )
    provenance: Provenance = Field(..., description="Mandatory extraction lineage.")


class CaseTimeline(BaseModel):
    """
    Complete structured case timeline object representing Step 7 output.
    """

    document_id: str = Field(..., description="ID of processed document.")
    case_id: Optional[str] = Field(default=None, description="Case ID.")
    events: List[TimelineEvent] = Field(
        default_factory=list, description="All extracted timeline events."
    )
    temporal_relationships: List[TemporalRelationship] = Field(
        default_factory=list,
        description="All extracted temporal relationships (BEFORE, AFTER, HAS_DEADLINE, etc.).",
    )
    unresolved_expressions: List[RelativeTemporalExpression] = Field(
        default_factory=list,
        description="List of relative date expressions that could not be resolved.",
    )
    validation_warnings: List[str] = Field(
        default_factory=list, description="Temporal validation warning messages."
    )
    summary_counts: Dict[str, int] = Field(
        default_factory=dict,
        description="Summary counts and metrics for timeline extraction.",
    )

    def sort_timeline(self) -> List[TimelineEvent]:
        """
        Sorts timeline events chronologically.
        Events with exact dates come first, sorted by ISO string date (event_date or start_date).
        Events without dates are retained at the end sorted by source_page / char_span / description.
        """

        def sort_key(event: TimelineEvent) -> Tuple[int, str, int, int]:
            d = event.event_date or event.start_date or ""
            if d:
                # Primary sort: Has date (0), ISO string
                page = event.source_page or 0
                span_start = event.char_span[0] if event.char_span else 0
                return (0, d, page, span_start)
            else:
                # Secondary sort: No date (1), page, span_start
                page = event.source_page or 9999
                span_start = event.char_span[0] if event.char_span else 0
                return (1, "", page, span_start)

        sorted_events = sorted(self.events, key=sort_key)
        self.events = sorted_events
        return sorted_events
