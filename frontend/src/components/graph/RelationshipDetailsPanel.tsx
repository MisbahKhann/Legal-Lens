'use client';

import React from 'react';
import { X, GitFork, Trash2, ShieldCheck, ArrowRight } from 'lucide-react';
import { RelationshipEdge, ReviewItem } from './types';

interface RelationshipDetailsPanelProps {
  relationship: RelationshipEdge | null;
  reviewItem?: ReviewItem | null;
  onClose: () => void;
  onDeleteRelationship: (relId: string) => void;
  onApproveReview?: (reviewId: string) => Promise<void>;
  onRejectReview?: (reviewId: string) => Promise<void>;
}

export const RelationshipDetailsPanel: React.FC<RelationshipDetailsPanelProps> = ({
  relationship,
  reviewItem,
  onClose,
  onDeleteRelationship,
  onApproveReview,
  onRejectReview,
}) => {
  if (!relationship) return null;

  return (
    <aside className="kg-inspector" aria-label="Relationship Inspector Panel">
      <div className="kg-inspector-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <GitFork size={16} color="var(--accent-gold, #c9a24b)" />
          <h2 style={{ fontSize: '0.92rem', fontWeight: 700, margin: 0, color: 'var(--text-cream, #f5ede1)' }}>
            Relationship Inspector
          </h2>
        </div>
        <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close inspector">
          <X size={16} />
        </button>
      </div>

      <div className="kg-inspector-content">
        {/* Relationship Type */}
        <div className="kg-meta-row">
          <span className="kg-meta-label">Relationship Predicate</span>
          <div style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--accent-gold, #c9a24b)' }}>
            {relationship.relationship_type}
          </div>
        </div>

        {/* Direction: Source -> Target */}
        <div className="kg-meta-row">
          <span className="kg-meta-label">Connected Entities</span>
          <div
            style={{
              background: '#1f1315',
              border: '1px solid rgba(201, 162, 75, 0.2)',
              borderRadius: '8px',
              padding: '0.75rem',
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
            }}
          >
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim, #9e8a78)' }}>SOURCE:</span>
              <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>{relationship.source_name || relationship.source_id}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: 'var(--accent-gold, #c9a24b)', fontSize: '0.76rem' }}>
              <ArrowRight size={13} />
              <span>{relationship.relationship_type}</span>
            </div>
            <div>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-dim, #9e8a78)' }}>TARGET:</span>
              <div style={{ fontSize: '0.88rem', fontWeight: 600 }}>{relationship.target_name || relationship.target_id}</div>
            </div>
          </div>
        </div>

        {/* Confidence & Provenance */}
        <div className="kg-meta-row" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
          <div>
            <span className="kg-meta-label">Confidence</span>
            <div className="kg-meta-value">
              {relationship.confidence !== undefined ? `${(relationship.confidence * 100).toFixed(0)}%` : '100%'}
            </div>
          </div>
          <div>
            <span className="kg-meta-label">Extraction Method</span>
            <div className="kg-meta-value" style={{ fontSize: '0.78rem' }}>
              {relationship.extraction_method || 'PIPELINE_EXTRACTION'}
            </div>
          </div>
        </div>

        {/* Evidentiary Quote */}
        {relationship.source_text && (
          <div className="kg-provenance-box">
            <span className="kg-meta-label" style={{ color: 'var(--accent-gold, #c9a24b)' }}>
              Evidentiary Quote
            </span>
            <p className="kg-provenance-text">&ldquo;{relationship.source_text}&rdquo;</p>
            <div className="kg-provenance-citation">
              {relationship.source_document_id && `Doc: ${relationship.source_document_id.slice(0, 12)}...`}
              {relationship.source_page ? ` • Page ${relationship.source_page}` : ''}
            </div>
          </div>
        )}

        {/* Review Box if flagged */}
        {reviewItem && (
          <div className="kg-review-box">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 600 }}>
                <ShieldCheck size={14} color="var(--accent-gold, #c9a24b)" />
                <span>Relationship Review</span>
              </div>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, color: '#fbbf24' }}>
                {reviewItem.status}
              </span>
            </div>
            {reviewItem.status === 'PENDING' && (
              <div className="kg-review-actions">
                <button
                  type="button"
                  className="kg-btn-approve"
                  onClick={() => onApproveReview && onApproveReview(reviewItem.review_id)}
                >
                  Approve Edge
                </button>
                <button
                  type="button"
                  className="kg-btn-reject"
                  onClick={() => onRejectReview && onRejectReview(reviewItem.review_id)}
                >
                  Reject Edge
                </button>
              </div>
            )}
          </div>
        )}

        {/* Delete Edge Action */}
        <div style={{ marginTop: '1rem' }}>
          <button
            type="button"
            className="kg-btn-secondary"
            style={{ width: '100%', justifyContent: 'center', color: '#f87171', borderColor: 'rgba(239, 68, 68, 0.3)' }}
            onClick={() => onDeleteRelationship(relationship.id)}
          >
            <Trash2 size={13} />
            <span>Remove Relationship</span>
          </button>
        </div>
      </div>
    </aside>
  );
};
