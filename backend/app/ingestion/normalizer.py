"""
Legal text normalization engine for downstream NLP processing.
Cleans whitespace, fixes line-break hyphenations, normalizes unicode ligatures,
and preserves legal citation markers while keeping raw text strictly separate.
"""

import re
import unicodedata
from app.ingestion.models import LegalDocument, LegalPage, LegalTextBlock


LIGATURE_MAP = {
    "ﬁ": "fi",
    "ﬂ": "fl",
    "æ": "ae",
    "Æ": "AE",
    "œ": "oe",
    "Œ": "OE",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬅ": "st",
    "ﬆ": "st",
    "“": '"',
    "”": '"',
    "‘": "'",
    "’": "'",
    "—": "-",
    "–": "-",
}


class LegalTextNormalizer:
    """Normalizes legal text blocks and pages without overwriting raw text."""

    def normalize_text(self, text: str) -> str:
        """Applies legal text normalization rules to a raw string."""
        if not text:
            return ""

        # 1. Unicode NFC normalization
        normalized = unicodedata.normalize("NFC", text)

        # 2. Expand common ligatures and smart quotes
        for lig, repl in LIGATURE_MAP.items():
            normalized = normalized.replace(lig, repl)

        # 3. Strip unprintable control characters (except newlines and tabs)
        normalized = "".join(ch for ch in normalized if ch == "\n" or ch == "\t" or unicodedata.category(ch)[0] != "C")

        # 4. Repair line-break hyphenations (e.g. "juris-\ndiction" -> "jurisdiction")
        normalized = re.sub(r"(\b[a-zA-Z]{2,})-\s*\n\s*([a-zA-Z]{2,}\b)", r"\1\2", normalized)

        # 5. Clean multi-spaces within lines while preserving single spacing
        lines = []
        for line in normalized.splitlines():
            line_cleaned = re.sub(r"[ \t]+", " ", line).strip()
            lines.append(line_cleaned)

        # 6. Rejoin lines preserving double newlines (paragraph splits)
        cleaned_text = "\n".join(lines)
        cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)

        return cleaned_text.strip()

    def normalize_document(self, document: LegalDocument) -> LegalDocument:
        """
        Populates normalized_text fields on every block and page in LegalDocument,
        leaving raw_text fields 100% intact.
        """
        for page in document.pages:
            normalized_block_texts = []
            for block in page.blocks:
                block.normalized_text = self.normalize_text(block.raw_text)
                normalized_block_texts.append(block.normalized_text)

            table_texts = [self.normalize_text(t.markdown_content) for t in page.tables if t.markdown_content]
            page.normalized_text = "\n\n".join(normalized_block_texts + table_texts)

        return document
