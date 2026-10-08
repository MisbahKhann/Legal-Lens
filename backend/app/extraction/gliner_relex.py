"""
GLiNER-Relex Extractor module for Step 4 AI Entity & Relationship Extraction.
Wraps local GLiNER-Relex inference with controlled ontology vocabularies,
confidence thresholding, result caching, and constraint validation.
"""

import hashlib
import logging
from typing import Dict, Any, List, Optional, Tuple, Set
import torch

from app.schema.entity_types import EntityType
from app.schema.relationship_types import RelationshipType
from app.schema.validator import SchemaValidator, TripletConstraintViolationError
from app.extraction.ai_models import (
    CandidateEntity,
    CandidateRelation,
    AIExtractionResult,
)
from app.extraction.chunker import DocumentChunk
from app.schema.provenance import ExtractionMethod

logger = logging.getLogger(__name__)


# Controlled vocabularies from Step 1 ontology
CONTROLLED_ENTITY_TYPES: List[str] = [e.value for e in EntityType]
CONTROLLED_RELATIONSHIP_TYPES: List[str] = [r.value for r in RelationshipType]


class GLiNERRelexExtractor:
    """
    Modular wrapper for local GLiNER-Relex model inference.
    Executes entity and relationship extraction on document chunks and maps model predictions
    to Step 1 controlled ontology types with strict constraint validation.
    """

    def __init__(
        self,
        model_name: str = "knowledgator/gliner-relex-large-v1.0",
        entity_confidence_threshold: float = 0.40,
        relation_confidence_threshold: float = 0.40,
        device: Optional[str] = None,
        entity_labels: Optional[List[str]] = None,
        relation_labels: Optional[List[str]] = None,
        enable_caching: bool = True,
    ):
        """
        Args:
            model_name: Hugging Face model identifier or local path for GLiNER-Relex.
            entity_confidence_threshold: Minimum confidence threshold for entities.
            relation_confidence_threshold: Minimum confidence threshold for relations.
            device: 'cuda', 'cpu', or None for automatic detection.
            entity_labels: Custom entity labels subset or None to use all Step 1 EntityTypes.
            relation_labels: Custom relation labels subset or None to use all Step 1 RelationshipTypes.
            enable_caching: Whether to cache model inference outputs by chunk text hash.
        """
        self.model_name = model_name
        self.entity_confidence_threshold = entity_confidence_threshold
        self.relation_confidence_threshold = relation_confidence_threshold
        self.enable_caching = enable_caching
        self._cache: Dict[str, Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]] = {}

        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self.entity_labels = entity_labels or CONTROLLED_ENTITY_TYPES
        self.relation_labels = relation_labels or CONTROLLED_RELATIONSHIP_TYPES
        self._model = None

    def _load_model(self) -> Any:
        """Lazy loads GLiNER model instance locally."""
        if self._model is not None:
            return self._model

        try:
            from gliner import GLiNER

            logger.info(
                f"Loading GLiNER-Relex model '{self.model_name}' on device '{self.device}'..."
            )
            self._model = GLiNER.from_pretrained(self.model_name)
            if hasattr(self._model, "to"):
                self._model.to(self.device)
            logger.info(f"Successfully loaded GLiNER-Relex model '{self.model_name}'.")
            return self._model
        except Exception as e:
            logger.error(f"Failed to load GLiNER-Relex model '{self.model_name}': {e}")
            raise RuntimeError(f"GLiNER-Relex model loading failure: {e}") from e

    def extract_from_chunk(
        self, chunk: DocumentChunk
    ) -> Tuple[List[CandidateEntity], List[CandidateRelation]]:
        """
        Extracts candidate entities and candidate relationships from a single DocumentChunk.

        Args:
            chunk: DocumentChunk with page, section, text, and offsets.

        Returns:
            Tuple of (candidate_entities, candidate_relations).
        """
        if not chunk.text or not chunk.text.strip():
            return [], []

        # Check inference cache if enabled
        chunk_hash = hashlib.sha256(chunk.text.encode("utf-8")).hexdigest()
        if self.enable_caching and chunk_hash in self._cache:
            logger.debug(
                f"Cache hit for chunk {chunk.chunk_id} (hash={chunk_hash[:8]})"
            )
            raw_entities, raw_relations = self._cache[chunk_hash]
        else:
            model = self._load_model()
            try:
                if hasattr(model, "predict_relations"):
                    prediction = model.predict_relations(
                        chunk.text,
                        labels=self.entity_labels,
                        relations=self.relation_labels,
                        threshold=min(
                            self.entity_confidence_threshold,
                            self.relation_confidence_threshold,
                        ),
                    )
                    raw_entities = prediction[0]
                    raw_relations = prediction[1]
                elif hasattr(model, "predict_entities"):
                    raw_entities = model.predict_entities(
                        chunk.text,
                        self.entity_labels,
                        threshold=self.entity_confidence_threshold,
                    )
                    raw_relations = []
                else:
                    raw_entities, raw_relations = [], []
            except Exception as e:
                logger.warning(
                    f"Error during GLiNER inference on chunk {chunk.chunk_id}: {e}"
                )
                raw_entities, raw_relations = [], []

            if self.enable_caching:
                self._cache[chunk_hash] = (raw_entities, raw_relations)

        candidate_entities, entity_key_map = self._process_raw_entities(
            chunk, raw_entities
        )
        candidate_relations = self._process_raw_relations(
            chunk, raw_relations, entity_key_map
        )

        return candidate_entities, candidate_relations

    def _process_raw_entities(
        self, chunk: DocumentChunk, raw_entities: List[Dict[str, Any]]
    ) -> Tuple[List[CandidateEntity], Dict[Tuple[int, int, str], CandidateEntity]]:
        """Processes raw entity predictions into CandidateEntity objects."""
        candidate_entities: List[CandidateEntity] = []
        entity_key_map: Dict[Tuple[int, int, str], CandidateEntity] = {}

        for raw_ent in raw_entities:
            score = float(raw_ent.get("score", raw_ent.get("confidence", 1.0)))
            if score < self.entity_confidence_threshold:
                continue

            label_str = raw_ent.get("label", "").upper()

            # Validate entity type against ontology enum
            try:
                entity_type = SchemaValidator.validate_entity_type(label_str)
            except Exception:
                logger.warning(
                    f"Skipping prediction with uncontrolled entity label '{label_str}'."
                )
                continue

            text = raw_ent.get("text", "").strip()
            if not text:
                continue

            rel_start = int(raw_ent.get("start", 0))
            rel_end = int(raw_ent.get("end", rel_start + len(text)))

            # Absolute offsets within page
            start_offset = chunk.start_char_offset + rel_start
            end_offset = chunk.start_char_offset + rel_end

            cand = CandidateEntity(
                entity_type=entity_type,
                text=text,
                normalized_value=text,
                document_id=chunk.document_id,
                case_id=chunk.case_id,
                page_number=chunk.page_number,
                section_id=chunk.section_id,
                chunk_id=chunk.chunk_id,
                source_text=chunk.text,
                start_offset=start_offset,
                end_offset=end_offset,
                confidence=round(score, 4),
                extraction_method=ExtractionMethod.GLINER_RELEX,
                metadata={
                    "raw_label": raw_ent.get("label"),
                    "chunk_offset": (rel_start, rel_end),
                },
            )

            candidate_entities.append(cand)
            entity_key_map[(rel_start, rel_end, text.lower())] = cand

        return candidate_entities, entity_key_map

    def _process_raw_relations(
        self,
        chunk: DocumentChunk,
        raw_relations: List[Dict[str, Any]],
        entity_key_map: Dict[Tuple[int, int, str], CandidateEntity],
    ) -> List[CandidateRelation]:
        """Processes raw relation predictions into CandidateRelation objects with constraint validation."""
        candidate_relations: List[CandidateRelation] = []

        for raw_rel in raw_relations:
            score = float(raw_rel.get("score", raw_rel.get("confidence", 1.0)))
            if score < self.relation_confidence_threshold:
                continue

            rel_type_str = raw_rel.get("relation", raw_rel.get("type", "")).upper()

            # Validate relationship type against ontology enum
            try:
                rel_type = SchemaValidator.validate_relationship_type(rel_type_str)
            except Exception:
                logger.warning(
                    f"Skipping prediction with uncontrolled relation label '{rel_type_str}'."
                )
                continue

            head_dict = raw_rel.get("head", {})
            tail_dict = raw_rel.get("tail", {})

            source_cand = self._get_or_create_candidate_from_dict(
                chunk, head_dict, entity_key_map
            )
            target_cand = self._get_or_create_candidate_from_dict(
                chunk, tail_dict, entity_key_map
            )

            if not source_cand or not target_cand:
                continue

            # Validate triplet constraint against Step 1 ontology
            is_valid = True
            validation_error = None
            try:
                SchemaValidator.validate_triplet(
                    source_type=source_cand.entity_type,
                    relationship_type=rel_type,
                    target_type=target_cand.entity_type,
                    allow_subtype_inheritance=True,
                )
            except TripletConstraintViolationError as e:
                is_valid = False
                validation_error = str(e)
                logger.warning(f"Invalid relation triplet detected and flagged: {e}")

            cand_rel = CandidateRelation(
                relation_type=rel_type,
                source_entity=source_cand,
                target_entity=target_cand,
                document_id=chunk.document_id,
                case_id=chunk.case_id,
                page_number=chunk.page_number,
                source_text=chunk.text,
                confidence=round(score, 4),
                extraction_method=ExtractionMethod.GLINER_RELEX,
                is_valid=is_valid,
                validation_error=validation_error,
                metadata={"raw_relation": raw_rel.get("relation")},
            )

            candidate_relations.append(cand_rel)

        return candidate_relations

    def _get_or_create_candidate_from_dict(
        self,
        chunk: DocumentChunk,
        ent_dict: Dict[str, Any],
        entity_key_map: Dict[Tuple[int, int, str], CandidateEntity],
    ) -> Optional[CandidateEntity]:
        """Looks up existing CandidateEntity or constructs one from prediction head/tail dict."""
        if not ent_dict:
            return None

        text = ent_dict.get("text", "").strip()
        if not text:
            return None

        rel_start = int(ent_dict.get("start", 0))
        rel_end = int(ent_dict.get("end", rel_start + len(text)))
        key = (rel_start, rel_end, text.lower())

        if key in entity_key_map:
            return entity_key_map[key]

        # Try fallback matching by start offset and text
        for (st, en, txt), cand in entity_key_map.items():
            if (st == rel_start or txt == text.lower()) and abs(st - rel_start) <= 5:
                return cand

        # Otherwise create a candidate entity from dict
        label_str = ent_dict.get("label", "").upper()
        try:
            entity_type = SchemaValidator.validate_entity_type(label_str)
        except Exception:
            return None

        score = float(ent_dict.get("score", 1.0))
        return CandidateEntity(
            entity_type=entity_type,
            text=text,
            normalized_value=text,
            document_id=chunk.document_id,
            case_id=chunk.case_id,
            page_number=chunk.page_number,
            section_id=chunk.section_id,
            chunk_id=chunk.chunk_id,
            source_text=chunk.text,
            start_offset=chunk.start_char_offset + rel_start,
            end_offset=chunk.start_char_offset + rel_end,
            confidence=round(score, 4),
            extraction_method=ExtractionMethod.GLINER_RELEX,
        )
