"""
Relative Temporal Expression Parser and Reference Event Resolver.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from app.temporal.models import (
    RelativeTemporalExpression,
    NormalizedDate,
    DatePrecision,
    TemporalStatus,
    TimelineEvent,
)
from app.temporal.date_normalizer import DateNormalizer
from app.schema.entity_types import EntityType
from app.schema.provenance import Provenance

WORD_TO_NUM = {
    "a": 1,
    "an": 1,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "fourteen": 14,
    "fifteen": 15,
    "twenty": 20,
    "thirty": 30,
    "sixty": 60,
    "ninety": 90,
}

# Regex patterns for relative temporal expressions
RELATIVE_PATTERNS = [
    # "within 30 days of filing", "30 days after filing", "30 days after the hearing"
    re.compile(
        r"\b(?:within\s+)?(?P<num>\d+|[a-z]+)\s+(?P<unit>day|days|week|weeks|month|months|year|years)\s+(?P<dir>after|following|from|of)\s+(?:the\s+)?(?P<ref>[a-z_]+)\b",
        re.IGNORECASE,
    ),
    # "30 days later", "two weeks later"
    re.compile(
        r"\b(?P<num>\d+|[a-z]+)\s+(?P<unit>day|days|week|weeks|month|months|year|years)\s+later\b",
        re.IGNORECASE,
    ),
    # "within 14 days", "within 30 days"
    re.compile(
        r"\bwithin\s+(?P<num>\d+|[a-z]+)\s+(?P<unit>day|days|week|weeks|month|months|year|years)\b",
        re.IGNORECASE,
    ),
    # "before the hearing", "prior to filing", "after the judgment"
    re.compile(
        r"\b(?P<dir>before|prior to|after|following)\s+(?:the\s+)?(?P<ref>hearing|filing|judgment|complaint|trial|order)\b",
        re.IGNORECASE,
    ),
    # "yesterday", "tomorrow", "two days later"
    re.compile(r"\b(?P<word>yesterday|tomorrow)\b", re.IGNORECASE),
]


class RelativeTemporalParser:
    """
    Parses relative temporal expressions from text and resolves them against reference events/dates.
    """

    def __init__(self, date_normalizer: Optional[DateNormalizer] = None):
        self.normalizer = date_normalizer or DateNormalizer()

    def parse_expression(
        self,
        text: str,
        document_id: str,
        page_number: Optional[int] = None,
        char_span: Optional[Tuple[int, int]] = None,
        provenance: Optional[Provenance] = None,
    ) -> Optional[RelativeTemporalExpression]:
        """
        Scans text for relative temporal patterns and creates a RelativeTemporalExpression model.
        """
        for pat in RELATIVE_PATTERNS:
            match = pat.search(text)
            if not match:
                continue

            groupdict = match.groupdict()
            raw_text = match.group(0)

            # Handle yesterday / tomorrow
            if "word" in groupdict and groupdict["word"]:
                w = groupdict["word"].lower()
                delta = -1 if w == "yesterday" else 1
                return RelativeTemporalExpression(
                    raw_text=raw_text,
                    direction="OFFSET",
                    delta_days=delta,
                    temporal_status=TemporalStatus.UNRESOLVED,  # Needs anchor document date
                    source_document_id=document_id,
                    source_page=page_number,
                    char_span=char_span,
                    provenance=provenance,
                )

            # Handle before / after without offset num (e.g. "before the hearing")
            if "num" not in groupdict or not groupdict["num"]:
                direction = (
                    "BEFORE"
                    if "before" in groupdict.get("dir", "").lower()
                    or "prior" in groupdict.get("dir", "").lower()
                    else "AFTER"
                )
                ref_event = groupdict.get("ref", "").upper()
                return RelativeTemporalExpression(
                    raw_text=raw_text,
                    direction=direction,
                    reference_event_type=ref_event,
                    temporal_status=TemporalStatus.UNRESOLVED,
                    source_document_id=document_id,
                    source_page=page_number,
                    char_span=char_span,
                    provenance=provenance,
                )

            # Parse numeric count
            num_str = groupdict["num"].lower()
            num_val = int(num_str) if num_str.isdigit() else WORD_TO_NUM.get(num_str)
            if not num_val:
                continue

            unit = groupdict["unit"].lower()
            direction = "AFTER"
            if "dir" in groupdict and groupdict["dir"]:
                d_str = groupdict["dir"].lower()
                if "before" in d_str or "prior" in d_str:
                    direction = "BEFORE"

            ref_event = groupdict.get("ref", "").upper() if "ref" in groupdict else None

            delta_days = None
            delta_weeks = None
            delta_months = None
            delta_years = None

            if "day" in unit:
                delta_days = num_val
            elif "week" in unit:
                delta_weeks = num_val
                delta_days = num_val * 7
            elif "month" in unit:
                delta_months = num_val
                delta_days = num_val * 30  # Approx
            elif "year" in unit:
                delta_years = num_val
                delta_days = num_val * 365

            return RelativeTemporalExpression(
                raw_text=raw_text,
                direction=direction,
                delta_days=delta_days,
                delta_weeks=delta_weeks,
                delta_months=delta_months,
                delta_years=delta_years,
                reference_event_type=ref_event,
                temporal_status=TemporalStatus.UNRESOLVED,
                source_document_id=document_id,
                source_page=page_number,
                char_span=char_span,
                provenance=provenance,
            )

        return None

    def resolve_relative_expression(
        self,
        expr: RelativeTemporalExpression,
        known_events: List[TimelineEvent],
    ) -> RelativeTemporalExpression:
        """
        Attempts to resolve an unresolved relative expression against known events with valid dates.
        """
        if expr.temporal_status == TemporalStatus.RESOLVED and expr.resolved_date:
            return expr

        target_ref_type = expr.reference_event_type

        # Find matching reference candidate events with valid dates
        anchor_event: Optional[TimelineEvent] = None
        for ev in known_events:
            if not ev.event_date:
                continue

            # Check if event type matches target reference or if event description contains reference
            ev_type_str = ev.event_type.value.upper()
            ev_desc = ev.description.upper()

            if target_ref_type:
                if target_ref_type in ev_type_str or target_ref_type in ev_desc:
                    anchor_event = ev
                    break
            else:
                # If no explicit reference event, pick the most recent preceding event in the timeline
                anchor_event = ev

        if not anchor_event or not anchor_event.event_date:
            # Cannot resolve reference event
            expr.temporal_status = TemporalStatus.REVIEW_REQUIRED
            return expr

        try:
            # Parse anchor date
            anchor_dt = datetime.strptime(anchor_event.event_date[:10], "%Y-%m-%d")
            delta_days = expr.delta_days or 0

            if expr.direction == "BEFORE":
                target_dt = anchor_dt - timedelta(days=delta_days)
            else:
                target_dt = anchor_dt + timedelta(days=delta_days)

            res_iso = target_dt.strftime("%Y-%m-%d")

            expr.reference_event_id = anchor_event.event_id
            expr.reference_date_iso = anchor_event.event_date
            expr.resolved_date = NormalizedDate(
                raw_text=expr.raw_text,
                iso_value=res_iso,
                precision=DatePrecision.EXACT_DAY,
                year=target_dt.year,
                month=target_dt.month,
                day=target_dt.day,
                is_valid=True,
            )
            expr.temporal_status = TemporalStatus.RESOLVED

        except Exception as e:
            expr.temporal_status = TemporalStatus.REVIEW_REQUIRED

        return expr
