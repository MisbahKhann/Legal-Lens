"""
Step 6 Pipeline: Validation and Consistency Checking.
Validates resolved canonical entities and relations against ontology constraints,
detects contradictions, and flags missing or low-confidence information.
"""

import logging
from typing import List, Dict, Optional, Tuple, Set
from collections import defaultdict

from app.resolution.models import ResolutionResult, CanonicalEntity, ResolvedRelation
from app.validation.models import (
    ValidationResult,
    ValidationRecord,
    ValidationStatus,
    ValidationSeverity,
    RecordType,
)
from app.schema.validator import SchemaValidator, TripletConstraintViolationError
from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.constraints import RELATIONSHIP_CONSTRAINTS

logger = logging.getLogger(__name__)


class ValidationPipeline:
    """
    Step 6 validation pipeline. Applies semantic checks and business rules
    to candidates before they are inserted into Neo4j.
    """

    def __init__(self, low_confidence_threshold: float = 0.6):
        self.low_confidence_threshold = low_confidence_threshold

    def validate(self, resolution_result: ResolutionResult) -> ValidationResult:
        logger.info(
            f"Starting Step 6 Validation for document '{resolution_result.document_id}'"
        )

        val_result = ValidationResult(
            document_id=resolution_result.document_id,
            case_id=resolution_result.case_id,
        )

        valid_entities: List[CanonicalEntity] = []
        invalid_entities: List[CanonicalEntity] = []

        valid_relations: List[ResolvedRelation] = []
        invalid_relations: List[ResolvedRelation] = []

        # 1. Entity Validation
        for ent in resolution_result.canonical_entities:
            records = self._validate_entity(ent)

            # Aggregate status
            worst_status = ValidationStatus.VALID
            for r in records:
                if r.status == ValidationStatus.INVALID:
                    worst_status = ValidationStatus.INVALID
                elif (
                    r.status == ValidationStatus.REVIEW_REQUIRED
                    and worst_status != ValidationStatus.INVALID
                ):
                    worst_status = ValidationStatus.REVIEW_REQUIRED
                elif (
                    r.status == ValidationStatus.WARNING
                    and worst_status == ValidationStatus.VALID
                ):
                    worst_status = ValidationStatus.WARNING

            for r in records:
                if r.status == ValidationStatus.INVALID:
                    pass
                elif r.status == ValidationStatus.REVIEW_REQUIRED:
                    val_result.review_required.append(r)
                elif r.status == ValidationStatus.WARNING:
                    val_result.warnings.append(r)

            if worst_status == ValidationStatus.INVALID:
                invalid_entities.append(ent)
                for r in records:
                    if r.status == ValidationStatus.INVALID:
                        val_result.invalid_entities.append(ent)
                        # We only append to invalid_entities once per entity, so we break
                        break
            else:
                valid_entities.append(ent)

        val_result.validated_entities = valid_entities

        # 2. Relationship Validation
        # Map for looking up entity types
        entity_map = {e.canonical_id: e for e in resolution_result.canonical_entities}

        # Track duplicate relationships: same source, target, and type
        seen_relations: Dict[Tuple[str, str, str], List[ResolvedRelation]] = (
            defaultdict(list)
        )

        for rel in resolution_result.resolved_relations:
            records = self._validate_relation(rel, entity_map)

            key = (rel.source_entity_id, rel.target_entity_id, rel.relation_type.value)
            seen_relations[key].append(rel)

            worst_status = ValidationStatus.VALID
            for r in records:
                if r.status == ValidationStatus.INVALID:
                    worst_status = ValidationStatus.INVALID
                elif (
                    r.status == ValidationStatus.REVIEW_REQUIRED
                    and worst_status != ValidationStatus.INVALID
                ):
                    worst_status = ValidationStatus.REVIEW_REQUIRED
                elif (
                    r.status == ValidationStatus.WARNING
                    and worst_status == ValidationStatus.VALID
                ):
                    worst_status = ValidationStatus.WARNING

            for r in records:
                if r.status == ValidationStatus.REVIEW_REQUIRED:
                    val_result.review_required.append(r)
                elif r.status == ValidationStatus.WARNING:
                    val_result.warnings.append(r)

            if worst_status == ValidationStatus.INVALID:
                invalid_relations.append(rel)
                for r in records:
                    if r.status == ValidationStatus.INVALID:
                        val_result.invalid_relationships.append(rel)
                        break
            else:
                valid_relations.append(rel)

        # 3. Duplicate Relationships Check
        for key, rel_list in seen_relations.items():
            if len(rel_list) > 1:
                # Issue warning/review for duplicate relations (same fact extracted multiple times)
                duplicate_record = ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.WARNING,
                    severity=ValidationSeverity.INFO,
                    validation_rule="DUPLICATE_RELATIONSHIP",
                    message=f"Relationship extracted {len(rel_list)} times.",
                    relationship_id=rel_list[0].relation_id,
                    confidence=(
                        max(m.confidence for rel in rel_list for m in rel.mentions)
                        if any(rel.mentions for rel in rel_list)
                        else None
                    ),
                )
                val_result.warnings.append(duplicate_record)

        # 4. Contradiction Checking (Conservative)
        # e.g. Person is both Plaintiff and Defendant in the same case.
        # This requires checking the relationships involving the same person
        person_roles = defaultdict(set)
        for rel in valid_relations:
            if rel.relation_type in [
                RelationshipType.PLAINTIFF_IN,
                RelationshipType.DEFENDANT_IN,
            ]:
                person_roles[rel.source_entity_id].add(rel.relation_type)

        for pid, roles in person_roles.items():
            if (
                RelationshipType.PLAINTIFF_IN in roles
                and RelationshipType.DEFENDANT_IN in roles
            ):
                val_result.review_required.append(
                    ValidationRecord(
                        record_type=RecordType.ENTITY,
                        status=ValidationStatus.REVIEW_REQUIRED,
                        severity=ValidationSeverity.HIGH,
                        validation_rule="CONTRADICTION",
                        message="Entity is marked as both PLAINTIFF_IN and DEFENDANT_IN.",
                        entity_id=pid,
                    )
                )

        val_result.validated_relationships = valid_relations

        # Summary
        val_result.validation_summary = {
            "total_entities_checked": len(resolution_result.canonical_entities),
            "valid_entities": len(valid_entities),
            "invalid_entities": len(invalid_entities),
            "total_relations_checked": len(resolution_result.resolved_relations),
            "valid_relations": len(valid_relations),
            "invalid_relations": len(invalid_relations),
            "warnings_generated": len(val_result.warnings),
            "reviews_required": len(val_result.review_required),
        }

        logger.info(
            f"Validation complete. Valid Entities: {len(valid_entities)}, Valid Relations: {len(valid_relations)}"
        )
        return val_result

    def _validate_entity(self, ent: CanonicalEntity) -> List[ValidationRecord]:
        records = []

        # Valid Entity Type
        try:
            SchemaValidator.validate_entity_type(ent.entity_type.value)
        except Exception as e:
            records.append(
                ValidationRecord(
                    record_type=RecordType.ENTITY,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.CRITICAL,
                    validation_rule="INVALID_ENTITY_TYPE",
                    message=str(e),
                    entity_id=ent.canonical_id,
                )
            )

        # Missing Name
        if not ent.canonical_name or not ent.canonical_name.strip():
            records.append(
                ValidationRecord(
                    record_type=RecordType.ENTITY,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="MISSING_NAME",
                    message="Entity missing canonical name.",
                    entity_id=ent.canonical_id,
                )
            )

        # Provenance Check
        if not ent.mentions:
            records.append(
                ValidationRecord(
                    record_type=RecordType.ENTITY,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="MISSING_PROVENANCE",
                    message="Entity has no source mentions (provenance).",
                    entity_id=ent.canonical_id,
                )
            )
        else:
            # Check confidence
            avg_conf = sum(m.confidence for m in ent.mentions) / len(ent.mentions)
            if avg_conf < self.low_confidence_threshold:
                records.append(
                    ValidationRecord(
                        record_type=RecordType.ENTITY,
                        status=ValidationStatus.REVIEW_REQUIRED,
                        severity=ValidationSeverity.MEDIUM,
                        validation_rule="LOW_CONFIDENCE",
                        message=f"Low average confidence ({avg_conf:.2f}).",
                        entity_id=ent.canonical_id,
                        confidence=avg_conf,
                    )
                )

            # Cross-step agreement (AI vs Rule-based)
            methods = {m.extraction_method for m in ent.mentions}
            if len(methods) > 1:
                # Agreement across methods is a good thing, we could log it as INFO but we don't strictly need to.
                pass

        return records

    def _validate_relation(
        self, rel: ResolvedRelation, entity_map: Dict[str, CanonicalEntity]
    ) -> List[ValidationRecord]:
        records = []

        if not rel.is_valid:
            records.append(
                ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="PREVIOUSLY_INVALIDATED",
                    message=rel.validation_error or "Marked invalid in prior step.",
                    relationship_id=rel.relation_id,
                )
            )
            # No need to further validate an already invalid relationship
            return records

        # Valid Relationship Type
        try:
            SchemaValidator.validate_relationship_type(rel.relation_type.value)
        except Exception as e:
            records.append(
                ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.CRITICAL,
                    validation_rule="INVALID_RELATIONSHIP_TYPE",
                    message=str(e),
                    relationship_id=rel.relation_id,
                )
            )

        # Missing Source/Target
        if not rel.source_entity_id or rel.source_entity_id not in entity_map:
            records.append(
                ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="MISSING_SOURCE_ENTITY",
                    message="Source entity missing or not resolved.",
                    relationship_id=rel.relation_id,
                )
            )

        if not rel.target_entity_id or rel.target_entity_id not in entity_map:
            records.append(
                ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="MISSING_TARGET_ENTITY",
                    message="Target entity missing or not resolved.",
                    relationship_id=rel.relation_id,
                )
            )

        # Triplet constraints
        if rel.source_entity_id in entity_map and rel.target_entity_id in entity_map:
            source_type = entity_map[rel.source_entity_id].entity_type
            target_type = entity_map[rel.target_entity_id].entity_type
            try:
                SchemaValidator.validate_triplet(
                    source_type=source_type,
                    relationship_type=rel.relation_type,
                    target_type=target_type,
                )
            except TripletConstraintViolationError as e:
                records.append(
                    ValidationRecord(
                        record_type=RecordType.RELATIONSHIP,
                        status=ValidationStatus.INVALID,
                        severity=ValidationSeverity.HIGH,
                        validation_rule="INVALID_TRIPLET",
                        message=str(e),
                        relationship_id=rel.relation_id,
                    )
                )

        # Provenance Check
        if not rel.mentions:
            records.append(
                ValidationRecord(
                    record_type=RecordType.RELATIONSHIP,
                    status=ValidationStatus.INVALID,
                    severity=ValidationSeverity.HIGH,
                    validation_rule="MISSING_PROVENANCE",
                    message="Relationship has no source mentions (provenance).",
                    relationship_id=rel.relation_id,
                )
            )
        else:
            # Check confidence
            avg_conf = sum(m.confidence for m in rel.mentions) / len(rel.mentions)
            if avg_conf < self.low_confidence_threshold:
                records.append(
                    ValidationRecord(
                        record_type=RecordType.RELATIONSHIP,
                        status=ValidationStatus.REVIEW_REQUIRED,
                        severity=ValidationSeverity.MEDIUM,
                        validation_rule="LOW_CONFIDENCE",
                        message=f"Low average confidence ({avg_conf:.2f}).",
                        relationship_id=rel.relation_id,
                        confidence=avg_conf,
                    )
                )

        return records
