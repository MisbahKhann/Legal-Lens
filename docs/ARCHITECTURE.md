# Legal Intelligence & Knowledge Graph Architecture Specification

## 1. System Context & Overview
The platform is designed to process unstructured legal documents (contracts, deposition transcripts, statutory codes) and transform them into a structured, queryable **Legal Knowledge Graph (GraphRAG)**.

```mermaid
graph TD
    User([Attorney / User]) --> Frontend[Next.js / React Frontend]
    Frontend -->|REST / WebSockets| API[FastAPI Backend Engine]
    API --> Extractor[GraphRAG Triplet Extractor]
    API --> GraphDB[(Graph Database / NetworkX Engine)]
    API --> VectorDB[(Vector Store - Embeddings)]
    Extractor --> FrontierLLM[Frontier LLM - Gemini / Claude / OpenAI]