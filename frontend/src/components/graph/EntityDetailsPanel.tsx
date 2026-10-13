'use client';

import React, { useState } from 'react';
import { 
  X, 
  ShieldCheck, 
  Trash2, 
  Edit3, 
  Maximize2
} from 'lucide-react';
import { EntityNode, ReviewItem, RelationshipEdge, getDefaultNodeColor } from './types';
import { NodeColorPicker } from './NodeColorPicker';
import { EntityNotesEditor } from './EntityNotesEditor';

function truncateExcerpt(text: string, maxLen = 320): string {
  const normalized = text.replace(/\s+/g, ' ').trim();
  if (normalized.length <= maxLen) return normalized;
  return `${normalized.slice(0, maxLen)}…`;
}

interface EntityDetailsPanelProps {
  entity: EntityNode | null;
  allEntities: EntityNode[];
  relationships: RelationshipEdge[];
  reviewItem?: ReviewItem | null;
  onClose: () => void;
  onApproveReview?: (reviewId: string) => Promise<void>;
  onRejectReview?: (reviewId: string) => Promise<void>;
  onChangeColor: (hex: string) => void;
  onResetColor: () => void;
  onSaveNotes: (notes: string) => Promise<void>;
  onExpandNeighbors: (nodeId: string) => void;
  onOpenEditModal: (entity: EntityNode) => void;
  onOpenDeleteModal: (entity: EntityNode) => void;
}

export const EntityDetailsPanel: React.FC<EntityDetailsPanelProps> = ({
  entity,
  allEntities: _allEntities,
  relationships,
  reviewItem,
  onClose,
  onApproveReview,
  onRejectReview,
  onChangeColor,
  onResetColor,
  onSaveNotes,
  onExpandNeighbors,
  onOpenEditModal,
  onOpenDeleteModal,
}) => {
  const [activeTab, setActiveTab] = useState<'info' | 'appearance' | 'notes'>('info');

  if (!entity) return null;

  const connectedEdges = relationships.filter(
    (r) => r.source_id === entity.id || r.target_id === entity.id
  );

  const defaultColor = getDefaultNodeColor(entity.entity_type);
  const nodeColor = entity.custom_color || defaultColor;

  return (
    <aside className="kg-inspector" aria-label="Entity Inspector Panel">
      <div className="kg-inspector-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          <span
            style={{
              width: '12px',
              height: '12px',
              borderRadius: '50%',
              backgroundColor: nodeColor,
              display: 'inline-block',
            }}
          />
          <h2 style={{ fontSize: '1rem', fontWeight: 700, margin: 0, color: 'var(--text-cream, #f5ede1)' }}>
            Selected entity
          </h2>
        </div>
        <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close inspector">
          <X size={16} />
        </button>
      </div>

      {/* Tabs */}
      <div className="kg-inspector-tabs" role="tablist">
        <button
          type="button"
          className={`kg-inspector-tab ${activeTab === 'info' ? 'active' : ''}`}
          onClick={() => setActiveTab('info')}
        >
          Details
        </button>
        <button
          type="button"
          className={`kg-inspector-tab ${activeTab === 'appearance' ? 'active' : ''}`}
          onClick={() => setActiveTab('appearance')}
        >
          Style
        </button>
        <button
          type="button"
          className={`kg-inspector-tab ${activeTab === 'notes' ? 'active' : ''}`}
          onClick={() => setActiveTab('notes')}
        >
          Notes
        </button>
      </div>

      <div className="kg-inspector-content">
        {/* TAB 1: DETAILS */}
        {activeTab === 'info' && (
          <>
            {/* Primary Name & Type */}
            <div className="kg-meta-row">
              <span className="kg-meta-label">Canonical Legal Name</span>
              <div style={{ fontSize: '1.05rem', fontWeight: 700, color: '#fff' }}>
                {entity.canonical_name}
              </div>
              <span
                className="kg-badge-type"
                style={{ backgroundColor: `${nodeColor}25`, color: nodeColor, border: `1px solid ${nodeColor}50`, marginTop: '0.3rem' }}
              >
                {entity.entity_type}
              </span>
            </div>

            {/* Aliases */}
            {entity.aliases && entity.aliases.length > 0 && (
              <div className="kg-meta-row">
                <span className="kg-meta-label">Known Aliases</span>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
                  {entity.aliases.map((alias, idx) => (
                    <span
                      key={idx}
                      style={{
                        background: 'rgba(245, 237, 225, 0.08)',
                        padding: '2px 8px',
                        borderRadius: '4px',
                        fontSize: '0.76rem',
                        color: 'var(--text-cream-muted, #d8c7b5)',
                      }}
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Confidence & Extraction Metadata */}
            <div className="kg-meta-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <span className="kg-meta-label">Confidence</span>
                <div className="kg-meta-value">
                  {entity.confidence !== undefined ? `${(entity.confidence * 100).toFixed(0)}%` : '100%'}
                </div>
              </div>
              <div>
                <span className="kg-meta-label">Extraction</span>
                <div className="kg-meta-value" style={{ fontSize: '0.78rem' }}>
                  {entity.extraction_method || 'PIPELINE_EXTRACTION'}
                </div>
              </div>
            </div>

            {/* Provenance Quotation */}
            {entity.source_text && (
              <div className="kg-provenance-box">
                <span className="kg-meta-label" style={{ color: 'var(--accent-gold, #c9a24b)' }}>
                  Evidentiary Source Provenance
                </span>
                <p className="kg-provenance-text">&ldquo;{entity.source_text}&rdquo;</p>
                <div className="kg-provenance-citation">
                  {entity.source_document_id && `Doc ID: ${entity.source_document_id.slice(0, 12)}...`}
                  {entity.source_page ? ` • Page ${entity.source_page}` : ''}
                </div>
              </div>
            )}

            {/* Human-in-the-Loop Review Box */}
            {reviewItem && (
              <div className="kg-review-box">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 600 }}>
                    <ShieldCheck size={14} color="var(--accent-gold, #c9a24b)" />
                    <span>Human Review Status</span>
                  </div>
                  <span
                    style={{
                      fontSize: '0.7rem',
                      fontWeight: 700,
                      padding: '2px 6px',
                      borderRadius: '4px',
                      background: reviewItem.status === 'APPROVED' ? '#15803d25' : reviewItem.status === 'REJECTED' ? '#b91c1c25' : '#f59e0b25',
                      color: reviewItem.status === 'APPROVED' ? '#34d399' : reviewItem.status === 'REJECTED' ? '#f87171' : '#fbbf24',
                    }}
                  >
                    {reviewItem.status}
                  </span>
                </div>

                {reviewItem.reason && (
                  <p style={{ fontSize: '0.74rem', color: 'var(--text-dim, #9e8a78)', margin: 0 }}>
                    {reviewItem.reason}
                  </p>
                )}

                {reviewItem.status === 'PENDING' && (
                  <div className="kg-review-actions">
                    <button
                      type="button"
                      className="kg-btn-approve"
                      onClick={() => onApproveReview && onApproveReview(reviewItem.review_id)}
                    >
                      Approve Assertion
                    </button>
                    <button
                      type="button"
                      className="kg-btn-reject"
                      onClick={() => onRejectReview && onRejectReview(reviewItem.review_id)}
                    >
                      Reject Assertion
                    </button>
                  </div>
                )}
              </div>
            )}

            {/* Connected Relationships List */}
            <div className="kg-meta-row">
              <span className="kg-meta-label">
                Connected Relationships ({connectedEdges.length})
              </span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem', maxHeight: '160px', overflowY: 'auto' }}>
                {connectedEdges.length === 0 ? (
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim, #9e8a78)' }}>
                    No direct relationships.
                  </span>
                ) : (
                  connectedEdges.map((rel) => {
                    const isOutgoing = rel.source_id === entity.id;
                    const otherName = isOutgoing ? rel.target_name || rel.target_id : rel.source_name || rel.source_id;
                    return (
                      <div
                        key={rel.id}
                        style={{
                          background: 'rgba(245, 237, 225, 0.04)',
                          border: '1px solid rgba(245, 237, 225, 0.08)',
                          borderRadius: '6px',
                          padding: '0.45rem 0.6rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'space-between',
                          fontSize: '0.78rem',
                        }}
                      >
                        <div>
                          <span style={{ color: 'var(--accent-gold, #c9a24b)', fontWeight: 600 }}>
                            {rel.relationship_type}
                          </span>
                          <span style={{ color: 'var(--text-dim, #9e8a78)', marginLeft: '0.35rem' }}>
                            {isOutgoing ? '→' : '←'} {otherName}
                          </span>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* Actions Toolbar */}
            <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
              <button
                type="button"
                className="kg-btn-secondary"
                style={{ flex: 1, justifyContent: 'center' }}
                onClick={() => onExpandNeighbors(entity.id)}
                title="Query backend for 1-hop connected neighbors"
              >
                <Maximize2 size={13} />
                <span>Expand</span>
              </button>
              <button
                type="button"
                className="kg-btn-secondary"
                style={{ flex: 1, justifyContent: 'center' }}
                onClick={() => onOpenEditModal(entity)}
              >
                <Edit3 size={13} />
                <span>Edit</span>
              </button>
              <button
                type="button"
                className="kg-btn-secondary"
                style={{ color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
                onClick={() => onOpenDeleteModal(entity)}
                title="Remove entity and detach relationships"
              >
                <Trash2 size={13} />
              </button>
            </div>
          </>
        )}

        {/* TAB 2: APPEARANCE */}
        {activeTab === 'appearance' && (
          <NodeColorPicker
            currentColor={entity.custom_color}
            defaultType={entity.entity_type}
            onChangeColor={onChangeColor}
            onResetColor={onResetColor}
          />
        )}

        {/* TAB 3: NOTES */}
        {activeTab === 'notes' && (
          <EntityNotesEditor
            initialNotes={entity.user_notes}
            onSaveNotes={onSaveNotes}
          />
        )}
      </div>
    </aside>
  );
};
