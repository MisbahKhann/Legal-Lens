"""
Step 11: Extraction Evaluation & Benchmarking Package.
Exposes evaluation models, KnowledgeGraphEvaluator engine, and EvaluationRunner.
"""

from app.evaluation.models import (
    GoldEntity,
    GoldRelationship,
    GoldEvent,
    GoldEquivalencePair,
    GoldDocumentData,
    GoldDataset,
    ExtractionMetrics,
    ResolutionMetrics,
    TemporalMetrics,
    ValidationMetrics,
    ProvenanceMetrics,
    EscalationMetrics,
    GraphConsistencyMetrics,
    Step11EvaluationReport,
)
from app.evaluation.evaluator import KnowledgeGraphEvaluator
from app.evaluation.runner import EvaluationRunner

__all__ = [
    "GoldEntity",
    "GoldRelationship",
    "GoldEvent",
    "GoldEquivalencePair",
    "GoldDocumentData",
    "GoldDataset",
    "ExtractionMetrics",
    "ResolutionMetrics",
    "TemporalMetrics",
    "ValidationMetrics",
    "ProvenanceMetrics",
    "EscalationMetrics",
    "GraphConsistencyMetrics",
    "Step11EvaluationReport",
    "KnowledgeGraphEvaluator",
    "EvaluationRunner",
]
