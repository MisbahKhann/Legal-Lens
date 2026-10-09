"""
Centralized Prompt Templates for Local LLM Extraction Fallback (Step 10).
Formulates structured, versionable prompts for Ollama and local LLM backends.
"""

from typing import List, Optional
import json
from app.llm.models import LLMFallbackRequest

SYSTEM_PROMPT = """You are a highly precise legal information extraction assistant. Your task is to resolve ambiguities in extracted legal entities, relationships, or temporal expressions.

STRICT OPERATIONAL RULES:
1. Do NOT invent facts or hallucinate entities, relationships, or dates not present in the supplied text.
2. Use ONLY the verbatim text snippet and context provided.
3. Select ONLY from the allowed ontology labels provided in the request.
4. If the provided evidence is ambiguous, conflicting, or insufficient, set decision to "UNCERTAIN" and needs_human_review to true.
5. Do NOT provide legal advice or legal opinions.
6. Return ONLY valid JSON adhering strictly to the requested JSON response schema. Do not include markdown formatting or commentary outside the JSON object.
"""


def build_fallback_prompt(request: LLMFallbackRequest) -> str:
    """
    Constructs a detailed, structured prompt for an ambiguous legal extraction fallback request.
    """
    allowed_entity_types_str = (
        ", ".join(request.allowed_entity_types)
        if request.allowed_entity_types
        else "All controlled Step 1 Entity Types"
    )
    allowed_rel_types_str = (
        ", ".join(request.allowed_relationship_types)
        if request.allowed_relationship_types
        else "All controlled Step 1 Relationship Types"
    )

    prompt = f"""
TASK: Resolve Legal Information Extraction Ambiguity

AMBIGUITY TYPE: {request.ambiguity_type.value}
SOURCE DOCUMENT ID: {request.source_document_id} (Page {request.source_page})

SOURCE TEXT SNIPPET:
\"\"\"
{request.source_text}
\"\"\"

ONTOLOGY BOUNDARIES:
- Allowed Entity Types: [{allowed_entity_types_str}]
- Allowed Relationship Types: [{allowed_rel_types_str}]

CANDIDATE EXTRACTIONS / CONTEXT:
- Candidate Entities: {json.dumps(request.candidate_entities, indent=2)}
- Candidate Relationships: {json.dumps(request.candidate_relationships, indent=2)}
- Candidate Dates/Events: {json.dumps(request.candidate_dates, indent=2)}

INSTRUCTIONS:
Analyze the source text snippet carefully against the candidates and ontology boundaries.
Determine if the ambiguity can be confidently resolved.

Provide your output as a SINGLE JSON object with the following keys:
{{
  "decision": "RESOLVED" | "UNCERTAIN" | "REJECTED",
  "selected_entity_type": string or null,
  "selected_entity_name": string or null,
  "selected_relationship_type": string or null,
  "source_entity_name": string or null,
  "target_entity_name": string or null,
  "selected_temporal_interpretation": object or null,
  "confidence": number between 0.0 and 1.0,
  "reasoning": string summarizing evidence,
  "needs_human_review": boolean
}}
"""
    return prompt.strip()
