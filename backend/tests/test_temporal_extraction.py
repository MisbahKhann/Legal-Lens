"""
Unit tests for Step 7: Temporal Event & Timeline Extraction.
Covers 16 required test cases specified in user requirements.
"""

import pytest
from datetime import datetime

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import Provenance, ExtractionMethod
from app.ingestion.models import LegalDocument, LegalPage
from app.extraction.ai_models import CandidateEntity, CandidateRelation
from app.resolution.models import CanonicalEntity, ResolvedRelation, ResolutionResult
from app.temporal.models import (
    DatePrecision,
    TemporalStatus,
    NormalizedDate,
    RelativeTemporalExpression,
    TimelineEvent,
    TemporalRelationship,
    CaseTimeline,
)
from app.temporal.date_normalizer import DateNormalizer
from app.temporal.relative_parser import RelativeTemporalParser
from app.temporal.event_associator import EventAssociator
from app.temporal.temporal_validator import TemporalValidator
from app.temporal.pipeline import TemporalPipeline


# 1. Exact date extraction
def test_exact_date_extraction():
    normalizer = DateNormalizer()
    res = normalizer.normalize("January 15, 2024")
    assert res.is_valid is True
    assert res.iso_value == "2024-01-15"
    assert res.precision == DatePrecision.EXACT_DAY
    assert res.year == 2024
    assert res.month == 1
    assert res.day == 15


# 2. Different US date formats
def test_us_date_formats():
    normalizer = DateNormalizer()

    formats = [
        ("January 5, 2024", "2024-01-05"),
        ("Jan. 5, 2024", "2024-01-05"),
        ("01/05/2024", "2024-01-05"),
        ("2024-01-05", "2024-01-05"),
        ("5th day of January, 2024", "2024-01-05"),
        ("5 January 2024", "2024-01-05"),
    ]

    for fmt_str, expected_iso in formats:
        res = normalizer.normalize(fmt_str)
        assert res.is_valid is True
        assert res.iso_value == expected_iso, f"Failed for format: {fmt_str}"


# 3. Partial dates
def test_partial_dates():
    normalizer = DateNormalizer()

    # Month level
    res_m = normalizer.normalize("March 2024")
    assert res_m.is_valid is True
    assert res_m.iso_value == "2024-03"
    assert res_m.precision == DatePrecision.MONTH

    # Year level
    res_y = normalizer.normalize("2024")
    assert res_y.is_valid is True
    assert res_y.iso_value == "2024"
    assert res_y.precision == DatePrecision.YEAR


# 4. Date ranges
def test_date_ranges():
    normalizer = DateNormalizer()
    res = normalizer.normalize("January 5, 2024 to January 10, 2024")
    assert res.is_valid is True
    assert res.start_date == "2024-01-05"
    assert res.end_date == "2024-01-10"


# 5. Filing date
def test_filing_date_association():
    normalizer = DateNormalizer()
    associator = EventAssociator(normalizer)

    prov = Provenance(
        case_id="c1", source_document_id="doc1", source_page=1, confidence=1.0
    )

    e_filing = CanonicalEntity(
        canonical_id="filing_1",
        entity_type=EntityType.FILING,
        canonical_name="Complaint Filed",
        document_id="doc1",
    )
    e_date = CanonicalEntity(
        canonical_id="date_1",
        entity_type=EntityType.DATE,
        canonical_name="January 5, 2024",
        document_id="doc1",
    )

    r_occ = ResolvedRelation(
        relation_type=RelationshipType.OCCURRED_ON,
        source_entity_id="filing_1",
        target_entity_id="date_1",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e_filing, e_date],
        resolved_relations=[r_occ],
    )

    events, rels = associator.process_resolution_result(res_result)
    assert len(events) == 1
    assert events[0].event_type == EntityType.FILING
    assert events[0].event_date == "2024-01-05"


# 6. Hearing date
def test_hearing_date_association():
    normalizer = DateNormalizer()
    associator = EventAssociator(normalizer)

    e_hearing = CanonicalEntity(
        canonical_id="h1",
        entity_type=EntityType.HEARING,
        canonical_name="Oral Argument Hearing",
        document_id="doc1",
    )
    e_date = CanonicalEntity(
        canonical_id="d1",
        entity_type=EntityType.DATE,
        canonical_name="March 3, 2024",
        document_id="doc1",
    )
    r_occ = ResolvedRelation(
        relation_type=RelationshipType.OCCURRED_ON,
        source_entity_id="h1",
        target_entity_id="d1",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e_hearing, e_date],
        resolved_relations=[r_occ],
    )

    events, rels = associator.process_resolution_result(res_result)
    assert len(events) == 1
    assert events[0].event_type == EntityType.HEARING
    assert events[0].event_date == "2024-03-03"


# 7. Deadline
def test_deadline_association():
    normalizer = DateNormalizer()
    associator = EventAssociator(normalizer)

    e_deadline = CanonicalEntity(
        canonical_id="dl1",
        entity_type=EntityType.DEADLINE,
        canonical_name="Answer Due Deadline",
        document_id="doc1",
    )
    e_date = CanonicalEntity(
        canonical_id="d1",
        entity_type=EntityType.DATE,
        canonical_name="February 15, 2024",
        document_id="doc1",
    )
    r_dl = ResolvedRelation(
        relation_type=RelationshipType.HAS_DEADLINE,
        source_entity_id="dl1",
        target_entity_id="d1",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e_deadline, e_date],
        resolved_relations=[r_dl],
    )

    events, rels = associator.process_resolution_result(res_result)
    assert len(events) == 1
    assert events[0].event_type == EntityType.DEADLINE
    assert events[0].event_date == "2024-02-15"


# 8. Event associated with a date
def test_event_associated_with_date():
    normalizer = DateNormalizer()
    associator = EventAssociator(normalizer)

    e_event = CanonicalEntity(
        canonical_id="ev1",
        entity_type=EntityType.EVENT,
        canonical_name="Contract Signing",
        document_id="doc1",
    )
    e_date = CanonicalEntity(
        canonical_id="d1",
        entity_type=EntityType.DATE,
        canonical_name="June 1, 2023",
        document_id="doc1",
    )
    r_occ = ResolvedRelation(
        relation_type=RelationshipType.OCCURRED_ON,
        source_entity_id="ev1",
        target_entity_id="d1",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e_event, e_date],
        resolved_relations=[r_occ],
    )

    events, rels = associator.process_resolution_result(res_result)
    assert len(events) == 1
    assert events[0].event_date == "2023-06-01"


# 9. BEFORE relationship
def test_before_relationship():
    associator = EventAssociator()
    e1 = CanonicalEntity(
        canonical_id="ev1",
        entity_type=EntityType.FILING,
        canonical_name="Filing Complaint",
        document_id="doc1",
    )
    e2 = CanonicalEntity(
        canonical_id="ev2",
        entity_type=EntityType.HEARING,
        canonical_name="Pre-trial Conference",
        document_id="doc1",
    )
    r_before = ResolvedRelation(
        relation_type=RelationshipType.BEFORE,
        source_entity_id="ev1",
        target_entity_id="ev2",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e1, e2],
        resolved_relations=[r_before],
    )

    events, rels = associator.process_resolution_result(res_result)
    assert len(rels) >= 1
    rel_types = [r.relationship_type for r in rels]
    assert RelationshipType.BEFORE in rel_types


# 10. AFTER relationship
def test_after_relationship():
    associator = EventAssociator()
    e1 = CanonicalEntity(
        canonical_id="ev1",
        entity_type=EntityType.HEARING,
        canonical_name="Trial Hearing",
        document_id="doc1",
    )
    e2 = CanonicalEntity(
        canonical_id="ev2",
        entity_type=EntityType.FILING,
        canonical_name="Initial Filing",
        document_id="doc1",
    )
    r_after = ResolvedRelation(
        relation_type=RelationshipType.AFTER,
        source_entity_id="ev1",
        target_entity_id="ev2",
        document_id="doc1",
    )

    res_result = ResolutionResult(
        document_id="doc1",
        canonical_entities=[e1, e2],
        resolved_relations=[r_after],
    )

    events, rels = associator.process_resolution_result(res_result)
    rel_types = [r.relationship_type for r in rels]
    assert RelationshipType.AFTER in rel_types


# 11. Relative date with a resolvable reference
def test_relative_date_resolvable():
    parser = RelativeTemporalParser()

    prov = Provenance(
        case_id="c1", source_document_id="doc1", source_page=1, confidence=1.0
    )
    anchor_event = TimelineEvent(
        event_id="ev_filing",
        event_type=EntityType.FILING,
        description="Filing of Complaint",
        event_date="2024-01-01",
        date_precision=DatePrecision.EXACT_DAY,
        source_document_id="doc1",
        provenance=prov,
    )

    expr = parser.parse_expression("30 days after filing", document_id="doc1")
    assert expr is not None
    assert expr.delta_days == 30

    resolved = parser.resolve_relative_expression(expr, [anchor_event])
    assert resolved.temporal_status == TemporalStatus.RESOLVED
    assert resolved.resolved_date is not None
    assert resolved.resolved_date.iso_value == "2024-01-31"


# 12. Relative date without a resolvable reference
def test_relative_date_unresolvable():
    parser = RelativeTemporalParser()
    expr = parser.parse_expression("two weeks later", document_id="doc1")
    assert expr is not None

    resolved = parser.resolve_relative_expression(expr, [])
    assert resolved.temporal_status == TemporalStatus.REVIEW_REQUIRED
    assert resolved.resolved_date is None


# 13. Contradictory dates
def test_contradictory_dates_validation():
    validator = TemporalValidator()
    prov = Provenance(
        case_id="c1", source_document_id="doc1", source_page=1, confidence=1.0
    )

    ev1 = TimelineEvent(
        canonical_entity_id="canon_1",
        event_type=EntityType.FILING,
        description="Motion to Dismiss",
        event_date="2024-01-05",
        source_document_id="doc1",
        provenance=prov,
    )
    ev2 = TimelineEvent(
        canonical_entity_id="canon_1",
        event_type=EntityType.FILING,
        description="Motion to Dismiss",
        event_date="2024-03-01",
        source_document_id="doc1",
        provenance=prov,
    )

    timeline = CaseTimeline(document_id="doc1", events=[ev1, ev2])
    records = validator.validate_timeline(timeline)

    rules = [r.validation_rule for r in records]
    assert "CONTRADICTORY_EVENT_DATES" in rules


# 14. Invalid / impossible dates
def test_invalid_impossible_date():
    normalizer = DateNormalizer()
    res = normalizer.normalize("February 30, 2024")
    assert res.is_valid is False
    assert "Invalid calendar date" in (res.validation_note or "")


# 15. Provenance preservation
from app.ingestion.models import LegalDocument, LegalPage, FileType, ProcessingMetadata


def test_provenance_preservation():
    pipeline = TemporalPipeline()

    page = LegalPage(
        page_number=3,
        raw_text="The complaint was filed on January 15, 2024.",
    )
    proc_meta = ProcessingMetadata(
        document_id="doc100",
        filename="test.pdf",
        file_type=FileType.PDF,
    )
    doc = LegalDocument(
        document_id="doc100",
        case_id="case100",
        filename="test.pdf",
        file_type=FileType.PDF,
        sha256_hash="dummy_hash",
        file_size_bytes=1024,
        processing_metadata=proc_meta,
        pages=[page],
    )

    prov = Provenance(
        case_id="case100",
        source_document_id="doc100",
        source_page=3,
        source_text="January 15, 2024",
        confidence=0.98,
        extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
    )

    e_filing = CanonicalEntity(
        canonical_id="filing_100",
        entity_type=EntityType.FILING,
        canonical_name="Complaint",
        document_id="doc100",
    )
    e_date = CanonicalEntity(
        canonical_id="date_100",
        entity_type=EntityType.DATE,
        canonical_name="January 15, 2024",
        document_id="doc100",
    )
    r_occ = ResolvedRelation(
        relation_type=RelationshipType.OCCURRED_ON,
        source_entity_id="filing_100",
        target_entity_id="date_100",
        document_id="doc100",
    )

    res_result = ResolutionResult(
        document_id="doc100",
        case_id="case100",
        canonical_entities=[e_filing, e_date],
        resolved_relations=[r_occ],
    )

    timeline = pipeline.process_timeline(doc, res_result)
    assert len(timeline.events) == 1
    ev = timeline.events[0]

    assert ev.source_document_id == "doc100"
    assert ev.provenance.source_document_id == "doc100"
    assert ev.provenance.case_id == "case100"


# 16. Timeline chronological ordering
def test_timeline_chronological_ordering():
    prov = Provenance(
        case_id="c1", source_document_id="doc1", source_page=1, confidence=1.0
    )

    ev_march = TimelineEvent(
        description="Event March",
        event_date="2024-03-01",
        date_precision=DatePrecision.EXACT_DAY,
        source_document_id="doc1",
        provenance=prov,
    )
    ev_jan = TimelineEvent(
        description="Event Jan",
        event_date="2024-01-15",
        date_precision=DatePrecision.EXACT_DAY,
        source_document_id="doc1",
        provenance=prov,
    )
    ev_nodate = TimelineEvent(
        description="Event Undated",
        event_date=None,
        date_precision=DatePrecision.UNKNOWN_PARTIAL,
        source_document_id="doc1",
        provenance=prov,
    )

    timeline = CaseTimeline(document_id="doc1", events=[ev_march, ev_nodate, ev_jan])
    sorted_evs = timeline.sort_timeline()

    assert sorted_evs[0].description == "Event Jan"
    assert sorted_evs[1].description == "Event March"
    assert sorted_evs[2].description == "Event Undated"
