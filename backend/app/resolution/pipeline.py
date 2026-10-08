"""
Entity Resolution Pipeline (Step 5).
Merges duplicate entities, handles aliases cautiously, and redirects relationships.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict

from app.extraction.ai_models import CandidateEntity, CandidateRelation
from app.resolution.models import CanonicalEntity, ResolvedRelation, ResolutionResult
from app.schema.entity_types import EntityType

logger = logging.getLogger(__name__)


class EntityResolutionPipeline:
    """
    Step 5 pipeline to resolve and deduplicate CandidateEntities into CanonicalEntities.
    Redirects CandidateRelations to point to CanonicalEntity IDs.
    """

    def resolve(
        self,
        document_id: str,
        case_id: Optional[str],
        entities: List[CandidateEntity],
        relations: List[CandidateRelation],
    ) -> ResolutionResult:
        logger.info(f"Starting Entity Resolution (Step 5) for document '{document_id}'")

        canonical_entities: List[CanonicalEntity] = []
        unresolved_entities: List[CandidateEntity] = []

        # Group entities by type and normalized text
        # Key: (EntityType, normalized_text.lower())
        entity_groups: Dict[Tuple[EntityType, str], List[CandidateEntity]] = (
            defaultdict(list)
        )

        for ent in entities:
            ent_text = getattr(ent, "text", getattr(ent, "original_value", ""))
            norm_text = (
                ent.normalized_value.lower()
                if getattr(ent, "normalized_value", None)
                else ent_text.lower()
            )
            norm_text = norm_text.strip()
            if not norm_text:
                continue
            entity_groups[(ent.entity_type, norm_text)].append(ent)

        # Map CandidateEntity ID to CanonicalEntity ID for relationship redirection
        candidate_to_canonical_map: Dict[str, str] = {}

        for (ent_type, norm_text), group in entity_groups.items():
            # Determine canonical name (most frequent exact casing)
            casing_counts = defaultdict(int)
            for ent in group:
                ent_name = getattr(ent, "text", getattr(ent, "original_value", ""))
                casing_counts[ent_name] += 1

            canonical_name = max(casing_counts.items(), key=lambda x: x[1])[0]
            aliases = list(
                {
                    getattr(ent, "text", getattr(ent, "original_value", ""))
                    for ent in group
                    if getattr(ent, "text", getattr(ent, "original_value", ""))
                    != canonical_name
                }
            )

            canonical_ent = CanonicalEntity(
                entity_type=ent_type,
                canonical_name=canonical_name,
                aliases=aliases,
                mentions=group,
                document_id=document_id,
                case_id=case_id,
            )
            canonical_entities.append(canonical_ent)

            for ent in group:
                ent_id = getattr(ent, "entity_id", getattr(ent, "candidate_id", None))
                if ent_id:
                    candidate_to_canonical_map[ent_id] = canonical_ent.canonical_id

        # Resolve relationships
        resolved_relations: List[ResolvedRelation] = []

        # Group relations by (relation_type, source_canonical_id, target_canonical_id)
        relation_groups: Dict[Tuple[str, str, str], List[CandidateRelation]] = (
            defaultdict(list)
        )

        for rel in relations:
            source_canon_id = candidate_to_canonical_map.get(
                rel.source_entity.entity_id
            )
            target_canon_id = candidate_to_canonical_map.get(
                rel.target_entity.entity_id
            )

            if not source_canon_id or not target_canon_id:
                # If we couldn't resolve the source or target, we skip or add to unresolved.
                continue

            key = (rel.relation_type, source_canon_id, target_canon_id)
            relation_groups[key].append(rel)

        for (rel_type, src_id, tgt_id), group in relation_groups.items():
            # Assume validation error/is_valid is consistent within exact duplicates.
            # We take the first one's validation status.
            is_valid = group[0].is_valid
            validation_error = group[0].validation_error

            resolved_rel = ResolvedRelation(
                relation_type=rel_type,
                source_entity_id=src_id,
                target_entity_id=tgt_id,
                mentions=group,
                document_id=document_id,
                case_id=case_id,
                is_valid=is_valid,
                validation_error=validation_error,
            )
            resolved_relations.append(resolved_rel)

        summary_counts = {
            "total_candidate_entities": len(entities),
            "total_canonical_entities": len(canonical_entities),
            "total_candidate_relations": len(relations),
            "total_resolved_relations": len(resolved_relations),
        }

        logger.info(
            f"Entity Resolution complete: {len(entities)} candidates -> {len(canonical_entities)} canonicals."
        )

        return ResolutionResult(
            document_id=document_id,
            case_id=case_id,
            canonical_entities=canonical_entities,
            resolved_relations=resolved_relations,
            unresolved_entities=unresolved_entities,
            summary_counts=summary_counts,
        )
