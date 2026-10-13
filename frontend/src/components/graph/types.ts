/**
 * Authoritative TypeScript Contracts for LegalLens Knowledge Graph Workspace.
 * Matches backend FastAPI schemas and authoritative US Legal Case Ontology.
 */

export interface CaseSummary {
  case_id: string;
  title: string;
  entity_count: number;
  relationship_count: number;
  timeline_event_count: number;
  document_count: number;
  updated_at: string;
}

export interface EntityNode {
  id: string;
  canonical_name: string;
  normalized_name?: string;
  entity_type: string;
  aliases?: string[];
  document_id?: string;
  source_document_id?: string;
  source_page?: number;
  source_text?: string;
  confidence?: number;
  trust_status?: string;
  extraction_method?: string;
  user_notes?: string;
  custom_color?: string;
  created_at?: string;
  updated_at?: string;
}

export interface RelationshipEdge {
  id: string;
  relationship_type: string;
  source_id: string;
  source_name?: string;
  target_id: string;
  target_name?: string;
  confidence?: number;
  source_text?: string;
  source_document_id?: string;
  source_page?: number;
  trust_status?: string;
  extraction_method?: string;
  created_at?: string;
}

export interface TimelineEvent {
  id: string;
  description: string;
  event_type: string;
  event_date?: string;
  start_date?: string;
  end_date?: string;
  date_precision?: string;
  temporal_status?: string;
  confidence?: number;
  canonical_entity_id?: string;
  associated_entity_id?: string;
  source_text?: string;
  created_at?: string;
}

export interface GraphPreferences {
  custom_colors: Record<string, string>;
  preferred_layout: 'cose' | 'breadthfirst' | 'concentric' | 'circle' | 'grid';
}

export interface GraphSummary {
  entity_count: number;
  relationship_count: number;
  timeline_event_count: number;
}

export interface GraphData {
  case_id: string;
  title?: string;
  summary: GraphSummary;
  entities: EntityNode[];
  relationships: RelationshipEdge[];
  timeline_events: TimelineEvent[];
  preferences?: GraphPreferences;
}

export type ReviewStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CORRECTED';
export type ItemType = 'ENTITY' | 'RELATIONSHIP' | 'EVENT' | 'ENTITY_MERGE' | 'ENTITY_SPLIT' | 'TEMPORAL';

export interface ReviewItem {
  review_id: string;
  case_id: string;
  item_type: ItemType;
  status: ReviewStatus;
  entity_id?: string;
  relationship_id?: string;
  event_id?: string;
  confidence?: number;
  reason?: string;
  validation_rule?: string;
  original_prediction: Record<string, unknown>;
  corrected_value?: Record<string, unknown>;
  source_document_id?: string;
  source_page?: number;
  source_text?: string;
  created_at?: string;
  reviewed_at?: string;
  reviewed_by?: string;
  reviewer_note?: string;
}

export type GraphViewMode = 
  | 'overview' 
  | 'evidence' 
  | 'people' 
  | 'authorities' 
  | 'timeline';

// Category mappings defined in Step 1 Ontology
export const ENTITY_CATEGORIES = {
  PARTY_LEGAL_ACTOR: [
    'PERSON', 'LAWYER', 'JUDGE', 'WITNESS', 'ORGANIZATION',
    'COMPANY', 'LAW_FIRM', 'GOVERNMENT_AGENCY', 'COURT'
  ],
  CASE_MATTER: [
    'CASE', 'LEGAL_ISSUE', 'CLAIM'
  ],
  LEGAL_SOURCE_NORMATIVE: [
    'STATUTE', 'REGULATION', 'LEGAL_CONCEPT'
  ],
  DOCUMENTARY_EVIDENCE: [
    'DOCUMENT', 'CONTRACT', 'EVIDENCE', 'EXHIBIT', 'FILING', 'TESTIMONY'
  ],
  TEMPORAL_EVENT: [
    'EVENT', 'DATE', 'DEADLINE', 'HEARING'
  ],
} as const;

export const CATEGORY_COLORS: Record<string, { base: string; border: string; bg: string }> = {
  PARTY_LEGAL_ACTOR: { base: '#3b82f6', border: '#60a5fa', bg: '#1e3a8a' },      // Blue
  CASE_MATTER: { base: '#10b981', border: '#34d399', bg: '#064e3b' },            // Emerald Green
  LEGAL_SOURCE_NORMATIVE: { base: '#f97316', border: '#fb923c', bg: '#7c2d12' }, // Orange/Terracotta
  DOCUMENTARY_EVIDENCE: { base: '#c9a24b', border: '#e2b857', bg: '#785618' },   // Muted Gold
  TEMPORAL_EVENT: { base: '#a855f7', border: '#c084fc', bg: '#581c87' },         // Purple
};

export function getEntityCategory(entityType: string): keyof typeof ENTITY_CATEGORIES {
  const upper = entityType.toUpperCase();
  for (const [cat, types] of Object.entries(ENTITY_CATEGORIES)) {
    if ((types as readonly string[]).includes(upper)) {
      return cat as keyof typeof ENTITY_CATEGORIES;
    }
  }
  return 'PARTY_LEGAL_ACTOR';
}

export function getDefaultNodeColor(entityType: string): string {
  const cat = getEntityCategory(entityType);
  return CATEGORY_COLORS[cat]?.base || '#c9a24b';
}

export const ALL_ENTITY_TYPES = [
  'CASE', 'PERSON', 'LAWYER', 'JUDGE', 'WITNESS',
  'ORGANIZATION', 'COMPANY', 'LAW_FIRM', 'GOVERNMENT_AGENCY', 'COURT',
  'STATUTE', 'REGULATION', 'LEGAL_CONCEPT',
  'LEGAL_ISSUE', 'CLAIM',
  'DOCUMENT', 'CONTRACT', 'EVIDENCE', 'EXHIBIT', 'FILING', 'TESTIMONY',
  'EVENT', 'DATE', 'DEADLINE', 'HEARING'
];

export const ALL_RELATIONSHIP_TYPES = [
  'PLAINTIFF_IN', 'DEFENDANT_IN', 'REPRESENTED_BY', 'DECIDED_BY', 'FILED_IN',
  'CITES', 'APPLIES', 'INTERPRETS', 'OVERRULES', 'FOLLOWS', 'DISTINGUISHES',
  'SUPPORTED_BY', 'CONTRADICTED_BY', 'EVIDENCED_BY', 'MENTIONED_IN',
  'WORKS_FOR', 'EMPLOYED_BY', 'OWNS', 'REPRESENTS',
  'OCCURRED_ON', 'OCCURRED_IN', 'BEFORE', 'AFTER', 'HAS_DEADLINE'
];
