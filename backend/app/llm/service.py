"""
LLMFallbackService orchestration engine for Step 10.
Executes targeted LLM resolution, enforces Step 1 ontology validation & Step 6 schema constraints,
manages decision thresholding, preserves provenance lineage, and escalates to Step 9 Human Review.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from app.llm.config import LLMConfig, get_llm_config
from app.llm.models import (
    LLMFallbackRequest,
    LLMFallbackResponse,
    LLMDecision,
    AmbiguityType,
)
from app.llm.provider import LLMProvider, OllamaProvider
from app.schema.validator import (
    SchemaValidator,
    InvalidEntityTypeError,
    InvalidRelationshipTypeError,
    TripletConstraintViolationError,
)
from app.schema.provenance import ExtractionMethod
from app.review.models import ReviewItem, ItemType, ReviewStatus
from app.review.manager import ReviewManager
from app.storage.neo4j_store import Neo4jGraphStore

logger = logging.getLogger(__name__)


class LLMFallbackService:
    """
    Orchestration service for resolving ambiguous extractions via local LLM fallback.
    Guarantees strict ontology validation, provenance tracking, confidence thresholding,
    and seamless integration with Step 9 Human-in-the-Loop review.
    """

    def __init__(
        self,
        provider: Optional[LLMProvider] = None,
        config: Optional[LLMConfig] = None,
        review_manager: Optional[ReviewManager] = None,
        neo4j_store: Optional[Neo4jGraphStore] = None,
    ):
        self.config = config or get_llm_config()
        self.provider = provider or OllamaProvider(config=self.config)
        self.review_manager = review_manager
        self.neo4j_store = neo4j_store

    def resolve_ambiguity(self, request: LLMFallbackRequest) -> LLMFallbackResponse:
        """
        Executes targeted LLM fallback for an ambiguous extraction request.
        """
        logger.info(
            "Executing LLM fallback for case %s, ambiguity %s (doc %s)",
            request.case_id,
            request.ambiguity_type,
            request.source_document_id,
        )

        # 1. Invoke local LLM provider
        response = self.provider.generate_resolution(request)

        # 2. Validate returned ontology elements against Step 1 & Step 6 constraints
        validation_passed, validation_error = self._validate_llm_ontology(
            request, response
        )

        if not validation_passed:
            logger.warning(
                "LLM result rejected due to schema/ontology validation failure: %s",
                validation_error,
            )
            response.decision = LLMDecision.REJECTED
            response.confidence = 0.0
            response.needs_human_review = True
            response.reasoning = f"{response.reasoning} [Validation Rejected: {validation_error}]".strip()

        # 3. Apply explicit confidence & escalation decision logic
        if (
            response.decision == LLMDecision.RESOLVED
            and response.confidence >= self.config.high_confidence_threshold
            and validation_passed
        ):
            # HIGH CONFIDENCE -> Accept LLM resolution & continue through validation/storage flow
            response.needs_human_review = False
            logger.info(
                "LLM fallback resolved ambiguity with high confidence (%.2f >= %.2f)",
                response.confidence,
                self.config.high_confidence_threshold,
            )
            self._handle_high_confidence_accepted(request, response)

        elif (
            response.decision == LLMDecision.RESOLVED
            and response.confidence >= self.config.low_confidence_threshold
            and validation_passed
        ):
            # MEDIUM CONFIDENCE / UNCERTAIN -> Flag for Step 9 Human Review
            response.needs_human_review = True
            logger.info(
                "LLM fallback result requires human review (medium confidence %.2f)",
                response.confidence,
            )
            self._escalate_to_human_review(
                request,
                response,
                reason=f"LLM suggestion requires verification (medium confidence: {response.confidence:.2f})",
            )

        else:
            # LOW CONFIDENCE / INVALID / REJECTED -> Reject LLM result & Escalate to Step 9 Human Review
            response.needs_human_review = True
            if response.decision != LLMDecision.REJECTED:
                response.decision = LLMDecision.REJECTED
            logger.info(
                "LLM fallback result rejected/uncertain -> Escalated to Step 9 human review."
            )
            self._escalate_to_human_review(
                request,
                response,
                reason=f"LLM resolution failed or low confidence: {response.reasoning}",
            )

        return response

    def _validate_llm_ontology(
        self, request: LLMFallbackRequest, response: LLMFallbackResponse
    ) -> (bool, Optional[str]):
        """
        Validates LLM returned entity types and relationship types against controlled Step 1 enums.
        """
        if response.decision != LLMDecision.RESOLVED:
            return True, None  # Non-resolved output does not need ontology check

        # Check entity type if supplied
        if response.selected_entity_type:
            try:
                SchemaValidator.validate_entity_type(response.selected_entity_type)
            except InvalidEntityTypeError as e:
                return False, str(e)

        # Check relationship type if supplied
        if response.selected_relationship_type:
            try:
                rel_enum = SchemaValidator.validate_relationship_type(
                    response.selected_relationship_type
                )
                # If source and target types are available in request/candidates, validate triplet
                if request.candidate_relationships:
                    first_cand = request.candidate_relationships[0]
                    src_t = first_cand.get("source_type", "PARTY")
                    tgt_t = first_cand.get("target_type", "PARTY")
                    try:
                        src_enum = SchemaValidator.validate_entity_type(str(src_t))
                        tgt_enum = SchemaValidator.validate_entity_type(str(tgt_t))
                        SchemaValidator.validate_triplet(
                            source_type=src_enum,
                            relationship_type=rel_enum,
                            target_type=tgt_enum,
                            allow_subtype_inheritance=True,
                        )
                    except (
                        InvalidEntityTypeError,
                        TripletConstraintViolationError,
                    ) as err:
                        return False, f"Triplet validation failed: {str(err)}"
            except InvalidRelationshipTypeError as e:
                return False, str(e)

        return True, None

    def _handle_high_confidence_accepted(
        self, request: LLMFallbackRequest, response: LLMFallbackResponse
    ) -> None:
        """
        Processes high-confidence LLM suggestion: updates graph if store is available.
        Preserves provenance.
        """
        if not self.neo4j_store or not self.neo4j_store.verify_connection():
            return

        try:
            if (
                request.ambiguity_type
                in [AmbiguityType.ENTITY_TYPE, AmbiguityType.ENTITY_IDENTITY]
                and response.selected_entity_name
            ):
                entity_dict = {
                    "id": f"llm_ent_{request.request_id[:8]}",
                    "canonical_name": response.selected_entity_name,
                    "normalized_name": response.selected_entity_name.lower().strip(),
                    "entity_type": response.selected_entity_type or "PARTY",
                    "aliases": [],
                    "document_id": request.source_document_id,
                    "source_document_id": request.source_document_id,
                    "source_page": request.source_page or 1,
                    "source_text": request.source_text,
                    "confidence": response.confidence,
                    "extraction_method": ExtractionMethod.LLM_EXTRACTION.value,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                self.neo4j_store.upsert_entities([entity_dict], request.case_id)
        except Exception as e:
            logger.warning("Neo4j high-confidence LLM sync warning: %s", str(e))

    def _escalate_to_human_review(
        self,
        request: LLMFallbackRequest,
        response: LLMFallbackResponse,
        reason: str,
    ) -> Optional[ReviewItem]:
        """
        Creates or updates a Step 9 ReviewItem preserving full original context,
        LLM suggestions, and LLM provenance metadata.
        """
        if not self.review_manager:
            return None

        # Determine Step 9 ItemType
        item_type = ItemType.ENTITY
        if request.ambiguity_type == AmbiguityType.RELATIONSHIP_TYPE:
            item_type = ItemType.RELATIONSHIP
        elif request.ambiguity_type == AmbiguityType.TEMPORAL_INTERPRETATION:
            item_type = ItemType.TEMPORAL
        elif request.ambiguity_type == AmbiguityType.ENTITY_IDENTITY:
            item_type = ItemType.ENTITY_MERGE

        original_pred = {
            "ambiguity_type": request.ambiguity_type.value,
            "original_extraction_method": request.original_extraction_method,
            "candidate_entities": request.candidate_entities,
            "candidate_relationships": request.candidate_relationships,
            "candidate_dates": request.candidate_dates,
        }

        provenance_details = {
            "llm_assisted": True,
            "llm_provider": response.llm_provider,
            "llm_model": response.llm_model,
            "llm_confidence": response.confidence,
            "llm_decision": response.decision.value,
            "llm_reasoning": response.reasoning,
            "llm_suggestion": {
                "selected_entity_type": response.selected_entity_type,
                "selected_entity_name": response.selected_entity_name,
                "selected_relationship_type": response.selected_relationship_type,
                "source_entity_name": response.source_entity_name,
                "target_entity_name": response.target_entity_name,
                "selected_temporal_interpretation": response.selected_temporal_interpretation,
            },
            "original_candidates": {
                "entities": request.candidate_entities,
                "relationships": request.candidate_relationships,
                "dates": request.candidate_dates,
            },
        }

        review_item = ReviewItem(
            case_id=request.case_id,
            item_type=item_type,
            status=ReviewStatus.PENDING,
            confidence=response.confidence,
            reason=reason,
            original_prediction=original_pred,
            source_document_id=request.source_document_id,
            source_page=request.source_page or 1,
            source_text=request.source_text,
            source_span=request.char_span,
            extraction_method=ExtractionMethod.LLM_EXTRACTION.value,
            provenance_details=provenance_details,
        )

        self.review_manager.add_review_item(review_item)
        logger.info(
            "Escalated fallback request %s to Step 9 review item %s",
            request.request_id,
            review_item.review_id,
        )
        return review_item
