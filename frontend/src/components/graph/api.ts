/**
 * API Client for LegalLens Knowledge Graph & Human-in-the-Loop Review.
 * Connects Next.js frontend to FastAPI backend service.
 */

import { CaseSummary, GraphData, ReviewItem, EntityNode, RelationshipEdge } from './types';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    let errMsg = `Request failed (${res.status} ${res.statusText})`;
    try {
      const errJson = await res.json();
      if (errJson.detail) {
        errMsg = typeof errJson.detail === 'string' ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // fallback to status text
    }
    throw new Error(errMsg);
  }
  return res.json();
}

export const graphApi = {
  /**
   * List accessible cases and summary metrics.
   */
  async getCases(): Promise<CaseSummary[]> {
    const res = await fetch(`${API_BASE}/api/v1/graph/cases`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return handleResponse<CaseSummary[]>(res);
  },

  /**
   * Retrieve complete Case Knowledge Graph.
   */
  async getCaseGraph(caseId: string): Promise<GraphData> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return handleResponse<GraphData>(res);
  },

  /**
   * Progressive neighborhood expansion.
   */
  async getNeighbors(caseId: string, nodeId: string): Promise<{
    case_id: string;
    target_node_id: string;
    neighbors: EntityNode[];
    relationships: RelationshipEdge[];
  }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/neighbors/${encodeURIComponent(nodeId)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return handleResponse<{
      case_id: string;
      target_node_id: string;
      neighbors: EntityNode[];
      relationships: RelationshipEdge[];
    }>(res);
  },

  /**
   * Upload legal document and trigger extraction pipeline (async background job).
   * Returns immediately with a job_id. Poll getJobStatus() for completion.
   */
  async uploadDocument(file: File, caseId: string): Promise<{
    job_id: string;
    status: string;
    case_id: string;
    filename: string;
    message: string;
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('case_id', caseId);

    const res = await fetch(`${API_BASE}/api/v1/graph/upload`, {
      method: 'POST',
      body: formData,
    });
    return handleResponse<{
      job_id: string;
      status: string;
      case_id: string;
      filename: string;
      message: string;
    }>(res);
  },

  /**
   * Poll background job status.
   * status: PENDING | PROCESSING | SUCCESS | PARTIAL | FAILED
   */
  async getJobStatus(jobId: string): Promise<{
    job_id: string;
    case_id: string;
    filename: string;
    status: string;
    stage: string;
    created_at: string;
    updated_at: string;
    metrics: Record<string, number | boolean>;
    error: string | null;
  }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/jobs/${encodeURIComponent(jobId)}`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return handleResponse<{
      job_id: string;
      case_id: string;
      filename: string;
      status: string;
      stage: string;
      created_at: string;
      updated_at: string;
      metrics: Record<string, number | boolean>;
      error: string | null;
    }>(res);
  },

  /**
   * Create new canonical entity node.
   */
  async createEntity(caseId: string, data: {
    canonical_name: string;
    entity_type: string;
    aliases?: string[];
    source_text?: string;
  }): Promise<EntityNode> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/entities`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<EntityNode>(res);
  },

  /**
   * Update existing entity.
   */
  async updateEntity(caseId: string, entityId: string, data: {
    canonical_name?: string;
    entity_type?: string;
    aliases?: string[];
  }): Promise<{ status: string; entity_id: string; case_id: string; updates: Record<string, unknown> }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/entities/${encodeURIComponent(entityId)}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<{ status: string; entity_id: string; case_id: string; updates: Record<string, unknown> }>(res);
  },

  /**
   * Delete entity node (detaching relationships).
   */
  async deleteEntity(caseId: string, entityId: string): Promise<{
    status: string;
    entity_id: string;
    case_id: string;
    relationships_detached: number;
  }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/entities/${encodeURIComponent(entityId)}`, {
      method: 'DELETE',
    });
    return handleResponse<{
      status: string;
      entity_id: string;
      case_id: string;
      relationships_detached: number;
    }>(res);
  },

  /**
   * Create relationship edge.
   */
  async createRelationship(caseId: string, data: {
    source_id: string;
    target_id: string;
    relationship_type: string;
    source_text?: string;
  }): Promise<RelationshipEdge> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/relationships`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<RelationshipEdge>(res);
  },

  /**
   * Delete relationship edge.
   */
  async deleteRelationship(caseId: string, relationshipId: string): Promise<{
    status: string;
    relationship_id: string;
    case_id: string;
  }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/relationships/${encodeURIComponent(relationshipId)}`, {
      method: 'DELETE',
    });
    return handleResponse<{
      status: string;
      relationship_id: string;
      case_id: string;
    }>(res);
  },

  /**
   * Save user notes for an entity.
   */
  async saveNotes(caseId: string, entityId: string, notes: string): Promise<{
    status: string;
    entity_id: string;
    notes: string;
  }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/entities/${encodeURIComponent(entityId)}/notes`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes }),
    });
    return handleResponse<{
      status: string;
      entity_id: string;
      notes: string;
    }>(res);
  },

  /**
   * Save graph view preferences.
   */
  async savePreferences(caseId: string, data: {
    custom_colors?: Record<string, string>;
    preferred_layout?: string;
  }): Promise<{ status: string; preferences: Record<string, unknown> }> {
    const res = await fetch(`${API_BASE}/api/v1/graph/${encodeURIComponent(caseId)}/preferences`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    return handleResponse<{ status: string; preferences: Record<string, unknown> }>(res);
  },

  // =========================================================================
  // Human-in-the-Loop Review Endpoints
  // =========================================================================

  async getReviewItems(caseId: string): Promise<ReviewItem[]> {
    const res = await fetch(`${API_BASE}/api/v1/review/${encodeURIComponent(caseId)}/items`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' },
    });
    return handleResponse<ReviewItem[]>(res);
  },

  async approveReviewItem(reviewId: string, reviewerId: string = 'lawyer_user', note?: string): Promise<ReviewItem> {
    const res = await fetch(`${API_BASE}/api/v1/review/items/${encodeURIComponent(reviewId)}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: reviewerId, reviewer_note: note }),
    });
    return handleResponse<ReviewItem>(res);
  },

  async rejectReviewItem(reviewId: string, reviewerId: string = 'lawyer_user', note?: string): Promise<ReviewItem> {
    const res = await fetch(`${API_BASE}/api/v1/review/items/${encodeURIComponent(reviewId)}/reject`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ reviewer_id: reviewerId, reviewer_note: note }),
    });
    return handleResponse<ReviewItem>(res);
  },

  async correctReviewItem(
    reviewId: string,
    corrections: Record<string, unknown>,
    reviewerId: string = 'lawyer_user',
    note?: string
  ): Promise<ReviewItem> {
    let url = `${API_BASE}/api/v1/review/items/${encodeURIComponent(reviewId)}/correct?reviewer_id=${encodeURIComponent(reviewerId)}`;
    if (note) url += `&reviewer_note=${encodeURIComponent(note)}`;

    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(corrections),
    });
    return handleResponse<ReviewItem>(res);
  },
};
