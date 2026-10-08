"""
Event Associator and Temporal Relationship Extractor.
Associates extracted dates with legal events and builds temporal graph edges.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.provenance import Provenance, ExtractionMethod
from app.resolution.models import ResolutionResult, CanonicalEntity, ResolvedRelation
from app.temporal.models import (
    TimelineEvent,
    TemporalRelationship,
    DatePrecision,
    TemporalStatus,
    NormalizedDate,
)
from app.temporal.date_normalizer import DateNormalizer
from app.temporal.relative_parser import RelativeTemporalParser

logger = logging.getLogger(__name__)

# Entity types that represent substantive legal occurrences/events
EVENT_ENTITY_TYPES = {
    EntityType.EVENT,
    EntityType.HEARING,
    EntityType.FILING,
    EntityType.DEADLINE,
    EntityType.CONTRACT,
    EntityType.TESTIMONY,
    EntityType.DOCUMENT,
    EntityType.CASE,
}


class EventAssociator:
    """
    Associates normalized dates with legal events and constructs temporal relationships.
    """

    def __init__(
        self,
        date_normalizer: Optional[DateNormalizer] = None,
        relative_parser: Optional[RelativeTemporalParser] = None,
    ):
        self.normalizer = date_normalizer or DateNormalizer()
        self.relative_parser = relative_parser or RelativeTemporalParser(
            self.normalizer
        )

    def process_resolution_result(
        self, resolution_result: ResolutionResult
    ) -> Tuple[List[TimelineEvent], List[TemporalRelationship]]:
        """
        Transforms resolved canonical entities and relations into TimelineEvents and TemporalRelationships.
        """
        timeline_events: List[TimelineEvent] = []
        temporal_relationships: List[TemporalRelationship] = []

        # Map canonical_id -> CanonicalEntity
        canonical_map: Dict[str, CanonicalEntity] = {
            e.canonical_id: e for e in resolution_result.canonical_entities
        }

        # Map canonical_id -> TimelineEvent
        entity_to_timeline_event: Dict[str, TimelineEvent] = {}

        # 1. Identify DATE entities and normalize them
        date_entities: Dict[str, NormalizedDate] = {}
        for ent in resolution_result.canonical_entities:
            if ent.entity_type == EntityType.DATE:
                norm = self.normalizer.normalize(ent.canonical_name)
                date_entities[ent.canonical_id] = norm

        # 2. Extract OCCURRED_ON and HAS_DEADLINE relationships connecting events to DATEs
        event_date_map: Dict[str, Tuple[NormalizedDate, CanonicalEntity]] = {}
        for rel in resolution_result.resolved_relations:
            if rel.relation_type in [
                RelationshipType.OCCURRED_ON,
                RelationshipType.HAS_DEADLINE,
            ]:
                src_ent = canonical_map.get(rel.source_entity_id)
                tgt_ent = canonical_map.get(rel.target_entity_id)

                if src_ent and tgt_ent and tgt_ent.entity_type == EntityType.DATE:
                    norm = date_entities.get(
                        tgt_ent.canonical_id
                    ) or self.normalizer.normalize(tgt_ent.canonical_name)
                    event_date_map[src_ent.canonical_id] = (norm, tgt_ent)

        # 3. Create TimelineEvents for substantive legal event entities
        for ent in resolution_result.canonical_entities:
            # Skip pure DATE entities from becoming events by themselves unless associated or explicit
            if ent.entity_type == EntityType.DATE:
                continue

            # Check if this entity is an event type or has temporal properties/associations
            is_substantive_event = ent.entity_type in EVENT_ENTITY_TYPES
            has_date_association = ent.canonical_id in event_date_map

            if not is_substantive_event and not has_date_association:
                continue

            # Primary mention provenance
            primary_mention = ent.mentions[0] if ent.mentions else None
            m_page = (
                getattr(primary_mention, "page_number", None)
                if primary_mention
                else None
            )
            m_text = (
                getattr(
                    primary_mention,
                    "source_text",
                    getattr(
                        primary_mention,
                        "original_value",
                        getattr(primary_mention, "text", ent.canonical_name),
                    ),
                )
                if primary_mention
                else ent.canonical_name
            )
            m_span = (
                getattr(primary_mention, "char_span", None) if primary_mention else None
            )
            m_conf = (
                getattr(primary_mention, "confidence", 1.0) if primary_mention else 1.0
            )
            m_method = (
                getattr(
                    primary_mention,
                    "extraction_method",
                    ExtractionMethod.DETERMINISTIC_RULE,
                )
                if primary_mention
                else ExtractionMethod.DETERMINISTIC_RULE
            )

            prov = Provenance(
                case_id=resolution_result.case_id or "default_case",
                source_document_id=resolution_result.document_id,
                source_page=m_page,
                source_text=m_text,
                char_span=m_span,
                confidence=m_conf,
                extraction_method=m_method,
            )

            event_date_str = None
            start_date_str = None
            end_date_str = None
            precision = DatePrecision.UNKNOWN_PARTIAL
            status = TemporalStatus.RESOLVED

            if ent.canonical_id in event_date_map:
                norm_d, date_node = event_date_map[ent.canonical_id]
                event_date_str = norm_d.iso_value
                start_date_str = norm_d.start_date
                end_date_str = norm_d.end_date
                precision = norm_d.precision
                if not norm_d.is_valid:
                    status = TemporalStatus.REVIEW_REQUIRED

            timeline_ev = TimelineEvent(
                canonical_entity_id=ent.canonical_id,
                event_type=ent.entity_type,
                description=f"{ent.entity_type.value}: {ent.canonical_name}",
                event_date=event_date_str,
                start_date=start_date_str,
                end_date=end_date_str,
                date_precision=precision,
                temporal_status=status,
                source_document_id=resolution_result.document_id,
                source_page=m_page,
                source_text=m_text,
                char_span=m_span,
                confidence=m_conf,
                extraction_method=m_method,
                related_entity_ids=[ent.canonical_id],
                provenance=prov,
            )
            timeline_events.append(timeline_ev)
            entity_to_timeline_event[ent.canonical_id] = timeline_ev

        # 4. Extract BEFORE/AFTER and HAS_DEADLINE temporal relationships between timeline events
        for rel in resolution_result.resolved_relations:
            if rel.relation_type in [
                RelationshipType.BEFORE,
                RelationshipType.AFTER,
                RelationshipType.HAS_DEADLINE,
                RelationshipType.OCCURRED_ON,
                RelationshipType.OCCURRED_IN,
            ]:
                src_tev = entity_to_timeline_event.get(rel.source_entity_id)
                tgt_tev = entity_to_timeline_event.get(rel.target_entity_id)

                if src_tev and tgt_tev:
                    primary_m = rel.mentions[0] if rel.mentions else None
                    rm_page = (
                        getattr(primary_m, "page_number", None) if primary_m else None
                    )
                    rm_text = (
                        getattr(primary_m, "source_text", None) if primary_m else None
                    )
                    rm_span = (
                        getattr(primary_m, "char_span", None) if primary_m else None
                    )
                    rm_conf = (
                        getattr(primary_m, "confidence", 1.0) if primary_m else 1.0
                    )
                    rm_method = (
                        getattr(
                            primary_m,
                            "extraction_method",
                            ExtractionMethod.GLINER_RELEX,
                        )
                        if primary_m
                        else ExtractionMethod.GLINER_RELEX
                    )

                    r_prov = Provenance(
                        case_id=resolution_result.case_id or "default_case",
                        source_document_id=resolution_result.document_id,
                        source_page=rm_page,
                        source_text=rm_text,
                        char_span=rm_span,
                        confidence=rm_conf,
                        extraction_method=rm_method,
                    )
                    t_rel = TemporalRelationship(
                        source_event_id=src_tev.event_id,
                        relationship_type=rel.relation_type,
                        target_event_id=tgt_tev.event_id,
                        provenance=r_prov,
                    )
                    temporal_relationships.append(t_rel)

        # 5. Infer BEFORE/AFTER relationships based on explicit dates if supported
        dated_events = [
            e
            for e in timeline_events
            if e.event_date and e.temporal_status == TemporalStatus.RESOLVED
        ]
        dated_events.sort(key=lambda x: x.event_date)

        for i in range(len(dated_events) - 1):
            e1 = dated_events[i]
            e2 = dated_events[i + 1]
            if e1.event_date != e2.event_date:
                # Add inferred BEFORE relationship
                r_prov = Provenance(
                    case_id=resolution_result.case_id or "default_case",
                    source_document_id=resolution_result.document_id,
                    source_page=e1.source_page,
                    source_text=f"Inferred chronology between {e1.description} ({e1.event_date}) and {e2.description} ({e2.event_date})",
                    confidence=0.9,
                    extraction_method=ExtractionMethod.DETERMINISTIC_RULE,
                )
                t_rel = TemporalRelationship(
                    source_event_id=e1.event_id,
                    relationship_type=RelationshipType.BEFORE,
                    target_event_id=e2.event_id,
                    properties={"inferred_from_dates": True},
                    provenance=r_prov,
                )
                temporal_relationships.append(t_rel)

        return timeline_events, temporal_relationships
