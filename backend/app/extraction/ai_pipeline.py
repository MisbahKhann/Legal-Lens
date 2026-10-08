"""
AI Extraction Pipeline Orchestrator (Step 4).
Runs document chunking, GLiNER-Relex inference, constraint validation,
and merges Step 4 AI predictions with Step 3 deterministic extractions.
"""

import logging
from typing import List, Optional, Dict, Any
from collections import Counter

from app.ingestion.models import LegalDocument
from app.extraction.models import DeterministicExtractionResult
from app.extraction.pipeline import DeterministicExtractionPipeline
from app.extraction.ai_models import (
    CandidateEntity,
    CandidateRelation,
    AIExtractionResult,
    CombinedExtractionResult,
)
from app.extraction.chunker import DocumentChunker, DocumentChunk
from app.extraction.gliner_relex import GLiNERRelexExtractor

logger = logging.getLogger(__name__)


class AIExtractionPipeline:
    """
    Main orchestrator for Step 4 AI-based Entity & Relationship Extraction.
    Uses GLiNER-Relex to extract contextual legal entities and relationships from LegalDocument.
    Merges Step 4 AI results with Step 3 deterministic extractions into a unified result object.
    """

    def __init__(
        self,
        extractor: Optional[GLiNERRelexExtractor] = None,
        chunker: Optional[DocumentChunker] = None,
        deterministic_pipeline: Optional[DeterministicExtractionPipeline] = None,
    ):
        """
        Args:
            extractor: Configured GLiNERRelexExtractor instance (or creates default).
            chunker: Configured DocumentChunker instance (or creates default).
            deterministic_pipeline: Step 3 pipeline instance (or creates default).
        """
        self.extractor = extractor or GLiNERRelexExtractor()
        self.chunker = chunker or DocumentChunker()
        self.deterministic_pipeline = (
            deterministic_pipeline or DeterministicExtractionPipeline()
        )

    def extract_ai_candidates(self, document: LegalDocument) -> AIExtractionResult:
        """
        Executes Step 4 AI entity and relationship extraction on a LegalDocument.

        Args:
            document: Standardized LegalDocument from Step 2 Ingestion.

        Returns:
            AIExtractionResult containing extracted candidate entities and relations.
        """
        logger.info(
            f"Starting Step 4 AI Extraction for document '{document.document_id}' (case='{document.case_id}')."
        )

        # 1. Chunk document while preserving page/section/offset provenance
        chunks: List[DocumentChunk] = self.chunker.chunk_document(document)
        logger.info(
            f"Document '{document.document_id}' split into {len(chunks)} chunks across {len(document.pages)} pages."
        )

        all_entities: List[CandidateEntity] = []
        all_relations: List[CandidateRelation] = []
        rejected_relations: List[CandidateRelation] = []

        # 2. Iterate through chunks and run GLiNER-Relex model
        for chunk in chunks:
            try:
                entities, relations = self.extractor.extract_from_chunk(chunk)
                all_entities.extend(entities)

                for rel in relations:
                    if rel.is_valid:
                        all_relations.append(rel)
                    else:
                        rejected_relations.append(rel)

            except Exception as e:
                logger.error(f"Error extracting from chunk {chunk.chunk_id}: {e}")

        # 3. Compute summary statistics
        entity_counts = dict(Counter(e.entity_type.value for e in all_entities))
        relation_counts = dict(Counter(r.relation_type.value for r in all_relations))

        summary_counts: Dict[str, int] = {
            "total_chunks": len(chunks),
            "total_entities": len(all_entities),
            "total_valid_relations": len(all_relations),
            "total_rejected_relations": len(rejected_relations),
            **{f"entity_{k}": v for k, v in entity_counts.items()},
            **{f"relation_{k}": v for k, v in relation_counts.items()},
        }

        logger.info(
            f"Step 4 AI Extraction complete for '{document.document_id}': "
            f"{len(all_entities)} entities, {len(all_relations)} valid relations, "
            f"{len(rejected_relations)} rejected relations."
        )

        return AIExtractionResult(
            document_id=document.document_id,
            case_id=document.case_id,
            model_name=self.extractor.model_name,
            entities=all_entities,
            relations=all_relations,
            rejected_relations=rejected_relations,
            summary_counts=summary_counts,
        )

    def run_pipeline(
        self,
        document: LegalDocument,
        deterministic_result: Optional[DeterministicExtractionResult] = None,
    ) -> CombinedExtractionResult:
        """
        Full combined pipeline execution: runs Step 3 deterministic extraction (if not provided)
        and Step 4 AI extraction, uniting both into a CombinedExtractionResult.

        Args:
            document: Standardized LegalDocument from Step 2 Ingestion.
            deterministic_result: Optional pre-computed Step 3 result.

        Returns:
            CombinedExtractionResult preserving separate traceability for Step 3 and Step 4.
        """
        if deterministic_result is None:
            logger.info("Executing Step 3 Deterministic Extraction...")
            deterministic_result = self.deterministic_pipeline.extract_candidates(
                document
            )

        ai_result = self.extract_ai_candidates(document)

        combined = CombinedExtractionResult(
            document_id=document.document_id,
            case_id=document.case_id,
            deterministic_result=deterministic_result,
            ai_result=ai_result,
            total_deterministic_entities=len(deterministic_result.candidates),
            total_ai_entities=len(ai_result.entities),
            total_ai_relations=len(ai_result.relations),
        )

        logger.info(
            f"Combined Extraction pipeline completed for document '{document.document_id}': "
            f"Deterministic candidates={combined.total_deterministic_entities}, "
            f"AI entities={combined.total_ai_entities}, "
            f"AI relations={combined.total_ai_relations}."
        )

        return combined
