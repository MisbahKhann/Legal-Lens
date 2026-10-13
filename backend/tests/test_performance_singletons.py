"""
Performance regression tests for the singleton model-loading fix.

Root cause: GLiNERRelexExtractor and Docling DocumentConverter were re-created
on every upload, each taking 3–8 minutes on CPU. These tests verify:
  1. get_extractor() returns the same object on repeated calls (no re-load).
  2. get_cached_converter() returns the same object for the same parameters.
  3. AIExtractionPipeline uses the singleton by default (not a fresh instance).
  4. Successive AIExtractionPipeline() constructions share the same extractor.
"""

import threading
import time

import pytest

# ============================================================
# 1.  GLiNERRelexExtractor singleton
# ============================================================


def test_get_extractor_returns_singleton():
    """get_extractor() must return the same object instance on every call."""
    from app.extraction.gliner_relex import get_extractor, _extractor_singleton

    # Reset singleton for isolation (only in test context)
    import app.extraction.gliner_relex as mod

    original = mod._extractor_singleton

    try:
        # Force a fresh singleton by temporarily clearing it
        mod._extractor_singleton = None

        # Two calls — both must return the same instance
        inst1 = get_extractor()
        inst2 = get_extractor()
        assert inst1 is inst2, "get_extractor() must return the same object instance"
    finally:
        # Restore whatever was there before (avoids re-loading the real model in CI)
        mod._extractor_singleton = original


def test_get_extractor_thread_safe():
    """Concurrent calls to get_extractor() must all resolve to the same instance."""
    import app.extraction.gliner_relex as mod

    original = mod._extractor_singleton
    try:
        mod._extractor_singleton = None
        results = []

        def _call():
            results.append(get_extractor_safe())

        def get_extractor_safe():
            from app.extraction.gliner_relex import get_extractor

            return get_extractor()

        threads = [threading.Thread(target=_call) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All threads must have seen the same instance
        assert (
            len(set(id(r) for r in results)) == 1
        ), "Concurrent get_extractor() calls must all return the same instance"
    finally:
        mod._extractor_singleton = original


# ============================================================
# 2.  Docling DocumentConverter cache
# ============================================================


def test_get_cached_converter_same_params_returns_same_object():
    """get_cached_converter() with identical parameters must reuse the converter."""
    from app.ingestion.parser import get_cached_converter, _converter_cache
    from app.ingestion.ocr import OCREngineType

    # Use a different key from the real OCR path to avoid expensive Docling init in CI.
    # We still exercise the caching logic.
    key = (
        False,
        OCREngineType.RAPIDOCR,
    )  # use_ocr=False is always fast (no OCR models)

    import app.ingestion.parser as pmod

    original_cache = dict(pmod._converter_cache)
    try:
        # Remove the key so we build it fresh
        pmod._converter_cache.pop(key, None)

        c1 = get_cached_converter(use_ocr=False, ocr_engine=OCREngineType.RAPIDOCR)
        c2 = get_cached_converter(use_ocr=False, ocr_engine=OCREngineType.RAPIDOCR)
        assert (
            c1 is c2
        ), "get_cached_converter() must return the same object for the same params"
    finally:
        pmod._converter_cache = original_cache


def test_get_cached_converter_different_params_returns_different_objects():
    """Different (use_ocr, engine) pairs must produce separate converter instances."""
    from app.ingestion.parser import get_cached_converter
    from app.ingestion.ocr import OCREngineType

    import app.ingestion.parser as pmod

    original_cache = dict(pmod._converter_cache)
    try:
        pmod._converter_cache.pop((False, OCREngineType.RAPIDOCR), None)
        pmod._converter_cache.pop((False, OCREngineType.TESSERACT), None)

        c1 = get_cached_converter(use_ocr=False, ocr_engine=OCREngineType.RAPIDOCR)
        c2 = get_cached_converter(use_ocr=False, ocr_engine=OCREngineType.TESSERACT)
        assert (
            c1 is not c2
        ), "Different OCR configurations must produce distinct converter instances"
    finally:
        pmod._converter_cache = original_cache


# ============================================================
# 3.  AIExtractionPipeline uses the singleton by default
# ============================================================


def test_ai_pipeline_uses_singleton_extractor(monkeypatch):
    """
    AIExtractionPipeline() with no explicit extractor argument must reuse
    the process-wide singleton, not construct a new GLiNERRelexExtractor.
    """
    import app.extraction.gliner_relex as mod
    from app.extraction.gliner_relex import GLiNERRelexExtractor

    # Plant a sentinel singleton so we do not load the real model
    sentinel = GLiNERRelexExtractor.__new__(GLiNERRelexExtractor)
    sentinel.model_name = "sentinel"
    sentinel._model = None
    sentinel.enable_caching = True
    sentinel._cache = {}
    sentinel.entity_labels = []
    sentinel.relation_labels = []
    sentinel.entity_confidence_threshold = 0.4
    sentinel.relation_confidence_threshold = 0.4
    sentinel.device = "cpu"

    original = mod._extractor_singleton
    mod._extractor_singleton = sentinel
    try:
        from app.extraction.ai_pipeline import AIExtractionPipeline

        pipeline = AIExtractionPipeline()
        assert (
            pipeline.extractor is sentinel
        ), "AIExtractionPipeline() must use the process-wide singleton extractor"
    finally:
        mod._extractor_singleton = original


def test_two_ai_pipelines_share_same_extractor(monkeypatch):
    """Two AIExtractionPipeline() instances must share the same extractor object."""
    import app.extraction.gliner_relex as mod
    from app.extraction.gliner_relex import GLiNERRelexExtractor

    sentinel = GLiNERRelexExtractor.__new__(GLiNERRelexExtractor)
    sentinel.model_name = "sentinel"
    sentinel._model = None
    sentinel.enable_caching = True
    sentinel._cache = {}
    sentinel.entity_labels = []
    sentinel.relation_labels = []
    sentinel.entity_confidence_threshold = 0.4
    sentinel.relation_confidence_threshold = 0.4
    sentinel.device = "cpu"

    original = mod._extractor_singleton
    mod._extractor_singleton = sentinel
    try:
        from app.extraction.ai_pipeline import AIExtractionPipeline

        p1 = AIExtractionPipeline()
        p2 = AIExtractionPipeline()
        assert (
            p1.extractor is p2.extractor
        ), "Multiple AIExtractionPipeline instances must share the same extractor singleton"
    finally:
        mod._extractor_singleton = original
