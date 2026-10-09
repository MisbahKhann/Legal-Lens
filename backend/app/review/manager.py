"""
Review State and Audit Manager for Step 9.
Manages candidate item lifecycle, human review decision processing,
ontology constraint validation on corrections, audit trail logging, and Neo4j graph updates.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from app.review.models import (
    ItemType,
    ReviewStatus,
    TrustStatus,
    ReviewItem,
    AuditRecord,
)
from app.schema.validator import SchemaValidator
from app.storage.neo4j_store import Neo4jGraphStore

logger = logging.getLogger(__name__)


class ReviewManager:
    """
    Central review state storage, decision engine, and audit logger.
    Enforces ontology constraints, auditability, and case isolation.
    """

    def __init__(self):
        self._items: Dict[str, ReviewItem] = {}
        self._audit_trail: List[AuditRecord] = []

    def add_review_item(self, item: ReviewItem) -> ReviewItem:
        """Adds a new ReviewItem to the in-memory store."""
        self._items[item.review_id] = item
        return item

    def add_review_items(self, items: List[ReviewItem]) -> List[ReviewItem]:
        """Adds multiple ReviewItems to the store."""
        for item in items:
            self.add_review_item(item)
        return items

    def get_review_item(self, review_id: str) -> Optional[ReviewItem]:
        """Retrieves a single review item by ID."""
        return self._items.get(review_id)

    def get_review_items_for_case(
        self,
        case_id: str,
        status: Optional[ReviewStatus] = None,
        item_type: Optional[ItemType] = None,
    ) -> List[ReviewItem]:
        """Retrieves review items for a specific case with optional status and item_type filtering."""
        results = [item for item in self._items.values() if item.case_id == case_id]
        if status:
            results = [item for item in results if item.status == status]
        if item_type:
            results = [item for item in results if item.item_type == item_type]
        return results

    def get_audit_trail_for_case(self, case_id: str) -> List[AuditRecord]:
        """Retrieves all audit records for a specific case."""
        return [rec for rec in self._audit_trail if rec.case_id == case_id]

    def approve_item(
        self,
        review_id: str,
        reviewer_id: str,
        reviewer_note: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> ReviewItem:
        """
        Approves a candidate item, keeping the original AI/system prediction.
        Records audit entry and updates graph trust status to APPROVED.
        """
        item = self.get_review_item(review_id)
        if not item:
            raise KeyError(f"Review item '{review_id}' not found.")

        now = datetime.now(timezone.utc)
        item.status = ReviewStatus.APPROVED
        item.updated_at = now
        item.reviewed_at = now
        item.reviewed_by = reviewer_id
        item.reviewer_note = reviewer_note

        # Create audit record
        audit = AuditRecord(
            review_id=review_id,
            case_id=item.case_id,
            reviewer_id=reviewer_id,
            decision="APPROVED",
            original_value=item.original_prediction,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        # Sync to Neo4j if store available
        if neo4j_store and neo4j_store.verify_connection():
            try:
                if item.item_type == ItemType.ENTITY and item.entity_id:
                    neo4j_store.update_entity_trust_status(
                        item.entity_id, item.case_id, TrustStatus.APPROVED.value
                    )
                elif item.item_type == ItemType.RELATIONSHIP and item.relationship_id:
                    neo4j_store.update_relationship_trust_status(
                        item.relationship_id, item.case_id, TrustStatus.APPROVED.value
                    )
                elif item.item_type == ItemType.EVENT and item.event_id:
                    neo4j_store.update_timeline_event_trust_status(
                        item.event_id, item.case_id, TrustStatus.APPROVED.value
                    )
            except Exception as e:
                logger.warning("Neo4j sync warning on approve: %s", str(e))

        logger.info("Approved review item %s by %s", review_id, reviewer_id)
        return item

    def reject_item(
        self,
        review_id: str,
        reviewer_id: str,
        reviewer_note: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> ReviewItem:
        """
        Rejects a candidate item, preventing it from becoming trusted knowledge.
        Records audit entry and updates graph trust status to REJECTED.
        """
        item = self.get_review_item(review_id)
        if not item:
            raise KeyError(f"Review item '{review_id}' not found.")

        now = datetime.now(timezone.utc)
        item.status = ReviewStatus.REJECTED
        item.updated_at = now
        item.reviewed_at = now
        item.reviewed_by = reviewer_id
        item.reviewer_note = reviewer_note

        audit = AuditRecord(
            review_id=review_id,
            case_id=item.case_id,
            reviewer_id=reviewer_id,
            decision="REJECTED",
            original_value=item.original_prediction,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection():
            try:
                if item.item_type == ItemType.ENTITY and item.entity_id:
                    neo4j_store.update_entity_trust_status(
                        item.entity_id, item.case_id, TrustStatus.REJECTED.value
                    )
                elif item.item_type == ItemType.RELATIONSHIP and item.relationship_id:
                    neo4j_store.update_relationship_trust_status(
                        item.relationship_id, item.case_id, TrustStatus.REJECTED.value
                    )
                elif item.item_type == ItemType.EVENT and item.event_id:
                    neo4j_store.update_timeline_event_trust_status(
                        item.event_id, item.case_id, TrustStatus.REJECTED.value
                    )
            except Exception as e:
                logger.warning("Neo4j sync warning on reject: %s", str(e))

        logger.info("Rejected review item %s by %s", review_id, reviewer_id)
        return item

    def correct_entity(
        self,
        review_id: str,
        reviewer_id: str,
        corrected_fields: Dict[str, Any],
        reviewer_note: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> ReviewItem:
        """
        Applies corrections to an entity review item.
        Validates entity_type against ontology constraints.
        Does NOT overwrite original prediction.
        """
        item = self.get_review_item(review_id)
        if not item:
            raise KeyError(f"Review item '{review_id}' not found.")

        # Validate entity type if provided
        if "entity_type" in corrected_fields and corrected_fields["entity_type"]:
            SchemaValidator.validate_entity_type(corrected_fields["entity_type"])

        now = datetime.now(timezone.utc)
        item.status = ReviewStatus.CORRECTED
        item.corrected_value = corrected_fields
        item.updated_at = now
        item.reviewed_at = now
        item.reviewed_by = reviewer_id
        item.reviewer_note = reviewer_note

        audit = AuditRecord(
            review_id=review_id,
            case_id=item.case_id,
            reviewer_id=reviewer_id,
            decision="CORRECTED",
            original_value=item.original_prediction,
            corrected_value=corrected_fields,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection() and item.entity_id:
            try:
                neo4j_store.update_entity_trust_status(
                    item.entity_id,
                    item.case_id,
                    TrustStatus.CORRECTED.value,
                    corrected_fields=corrected_fields,
                )
            except Exception as e:
                logger.warning("Neo4j sync warning on entity correct: %s", str(e))

        logger.info("Corrected entity review item %s by %s", review_id, reviewer_id)
        return item

    def correct_relationship(
        self,
        review_id: str,
        reviewer_id: str,
        corrected_fields: Dict[str, Any],
        reviewer_note: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> ReviewItem:
        """
        Applies corrections to a relationship review item.
        Strictly validates that corrected (source_type, relationship_type, target_type)
        satisfies Step 1 ontology triplet constraints.
        """
        item = self.get_review_item(review_id)
        if not item:
            raise KeyError(f"Review item '{review_id}' not found.")

        # Determine effective source_type, rel_type, target_type for validation
        rel_type_str = corrected_fields.get(
            "relationship_type",
            item.original_prediction.get("relationship_type")
            or item.original_prediction.get("rule"),
        )
        source_type_str = corrected_fields.get(
            "source_type", item.original_prediction.get("source_type", "PARTY")
        )
        target_type_str = corrected_fields.get(
            "target_type", item.original_prediction.get("target_type", "PARTY")
        )

        # Validate controlled relationship type and triplet matrix
        rel_type_enum = SchemaValidator.validate_relationship_type(str(rel_type_str))
        source_type_enum = SchemaValidator.validate_entity_type(str(source_type_str))
        target_type_enum = SchemaValidator.validate_entity_type(str(target_type_str))

        # Enforce triplet constraints
        SchemaValidator.validate_triplet(
            source_type=source_type_enum,
            relationship_type=rel_type_enum,
            target_type=target_type_enum,
            allow_subtype_inheritance=True,
        )

        now = datetime.now(timezone.utc)
        item.status = ReviewStatus.CORRECTED
        item.corrected_value = corrected_fields
        item.updated_at = now
        item.reviewed_at = now
        item.reviewed_by = reviewer_id
        item.reviewer_note = reviewer_note

        audit = AuditRecord(
            review_id=review_id,
            case_id=item.case_id,
            reviewer_id=reviewer_id,
            decision="CORRECTED",
            original_value=item.original_prediction,
            corrected_value=corrected_fields,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection() and item.relationship_id:
            try:
                neo4j_store.update_relationship_trust_status(
                    item.relationship_id,
                    item.case_id,
                    TrustStatus.CORRECTED.value,
                    corrected_fields=corrected_fields,
                )
            except Exception as e:
                logger.warning("Neo4j sync warning on relation correct: %s", str(e))

        logger.info(
            "Corrected relationship review item %s by %s", review_id, reviewer_id
        )
        return item

    def correct_temporal(
        self,
        review_id: str,
        reviewer_id: str,
        corrected_fields: Dict[str, Any],
        reviewer_note: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> ReviewItem:
        """
        Applies corrections to temporal/timeline event review items.
        Preserves original temporal expression and prediction.
        """
        item = self.get_review_item(review_id)
        if not item:
            raise KeyError(f"Review item '{review_id}' not found.")

        now = datetime.now(timezone.utc)
        item.status = ReviewStatus.CORRECTED
        item.corrected_value = corrected_fields
        item.updated_at = now
        item.reviewed_at = now
        item.reviewed_by = reviewer_id
        item.reviewer_note = reviewer_note

        audit = AuditRecord(
            review_id=review_id,
            case_id=item.case_id,
            reviewer_id=reviewer_id,
            decision="CORRECTED",
            original_value=item.original_prediction,
            corrected_value=corrected_fields,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection() and item.event_id:
            try:
                neo4j_store.update_timeline_event_trust_status(
                    item.event_id,
                    item.case_id,
                    TrustStatus.CORRECTED.value,
                    corrected_fields=corrected_fields,
                )
            except Exception as e:
                logger.warning("Neo4j sync warning on temporal correct: %s", str(e))

        logger.info("Corrected temporal review item %s by %s", review_id, reviewer_id)
        return item

    def merge_entities(
        self,
        case_id: str,
        primary_entity_id: str,
        secondary_entity_id: str,
        reviewer_id: str,
        reviewer_note: Optional[str] = None,
        review_id: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> AuditRecord:
        """
        Merges secondary entity into primary canonical entity.
        Redirects relationships, preserves historical extraction evidence,
        and logs audit decision. Enforces case isolation.
        """
        now = datetime.now(timezone.utc)

        if review_id:
            item = self.get_review_item(review_id)
            if item:
                if item.case_id != case_id:
                    raise ValueError(
                        f"Case mismatch: review item case '{item.case_id}' != request case '{case_id}'"
                    )
                item.status = ReviewStatus.APPROVED
                item.updated_at = now
                item.reviewed_at = now
                item.reviewed_by = reviewer_id
                item.reviewer_note = reviewer_note

        merge_payload = {
            "primary_entity_id": primary_entity_id,
            "secondary_entity_id": secondary_entity_id,
            "action": "MERGE",
        }

        audit = AuditRecord(
            review_id=review_id or f"rev_merge_{secondary_entity_id}",
            case_id=case_id,
            reviewer_id=reviewer_id,
            decision="MERGE",
            original_value=merge_payload,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection():
            try:
                neo4j_store.merge_entities_in_graph(
                    case_id, primary_entity_id, secondary_entity_id
                )
            except Exception as e:
                logger.warning("Neo4j merge warning: %s", str(e))

        logger.info(
            "Merged entity %s into %s for case %s by %s",
            secondary_entity_id,
            primary_entity_id,
            case_id,
            reviewer_id,
        )
        return audit

    def keep_entities_separate(
        self,
        case_id: str,
        entity_id_1: str,
        entity_id_2: str,
        reviewer_id: str,
        reviewer_note: Optional[str] = None,
        review_id: Optional[str] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ) -> AuditRecord:
        """
        Explicitly marks two entities to remain separate canonical entities.
        Records human decision and updates status. Enforces case isolation.
        """
        now = datetime.now(timezone.utc)

        if review_id:
            item = self.get_review_item(review_id)
            if item:
                if item.case_id != case_id:
                    raise ValueError(
                        f"Case mismatch: review item case '{item.case_id}' != request case '{case_id}'"
                    )
                item.status = ReviewStatus.APPROVED
                item.updated_at = now
                item.reviewed_at = now
                item.reviewed_by = reviewer_id
                item.reviewer_note = reviewer_note

        payload = {
            "entity_id_1": entity_id_1,
            "entity_id_2": entity_id_2,
            "action": "KEEP_SEPARATE",
        }

        audit = AuditRecord(
            review_id=review_id or f"rev_sep_{entity_id_1}_{entity_id_2}",
            case_id=case_id,
            reviewer_id=reviewer_id,
            decision="KEEP_SEPARATE",
            original_value=payload,
            reviewer_note=reviewer_note,
            timestamp=now,
        )
        self._audit_trail.append(audit)

        if neo4j_store and neo4j_store.verify_connection():
            try:
                neo4j_store.update_entity_trust_status(
                    entity_id_1, case_id, TrustStatus.KEPT_SEPARATE.value
                )
                neo4j_store.update_entity_trust_status(
                    entity_id_2, case_id, TrustStatus.KEPT_SEPARATE.value
                )
            except Exception as e:
                logger.warning("Neo4j keep separate warning: %s", str(e))

        logger.info(
            "Kept entities %s and %s separate for case %s by %s",
            entity_id_1,
            entity_id_2,
            case_id,
            reviewer_id,
        )
        return audit
