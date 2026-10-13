'use client';

import React, { useState } from 'react';
import { X, GitFork, AlertCircle } from 'lucide-react';
import { EntityNode, ALL_RELATIONSHIP_TYPES } from './types';

interface AddRelationshipModalProps {
  entities: EntityNode[];
  defaultSourceId?: string;
  onClose: () => void;
  onSubmit: (data: {
    source_id: string;
    target_id: string;
    relationship_type: string;
    source_text?: string;
  }) => Promise<void>;
}

export const AddRelationshipModal: React.FC<AddRelationshipModalProps> = ({
  entities,
  defaultSourceId,
  onClose,
  onSubmit,
}) => {
  const [sourceId, setSourceId] = useState(defaultSourceId || (entities[0]?.id || ''));
  const [targetId, setTargetId] = useState(
    entities.find((e) => e.id !== (defaultSourceId || entities[0]?.id))?.id || entities[1]?.id || ''
  );
  const [relType, setRelType] = useState('REPRESENTED_BY');
  const [sourceText, setSourceText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId || !targetId) {
      setErrorMessage('Both source and target entities must be selected.');
      return;
    }

    if (sourceId === targetId) {
      setErrorMessage('Cannot create a self-loop edge (source and target must be different).');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      await onSubmit({
        source_id: sourceId,
        target_id: targetId,
        relationship_type: relType,
        source_text: sourceText.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create relationship.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="kg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-rel-title">
      <div className="kg-modal-card">
        <div className="kg-modal-header">
          <div className="kg-modal-title" id="add-rel-title">
            Add Legal Relationship
          </div>
          <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="kg-modal-body">
            {/* Source Entity */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="rel-source">
                Source Entity *
              </label>
              <select
                id="rel-source"
                className="kg-case-selector"
                value={sourceId}
                onChange={(e) => setSourceId(e.target.value)}
                disabled={isSubmitting}
                style={{ width: '100%' }}
              >
                {entities.map((ent) => (
                  <option key={ent.id} value={ent.id}>
                    {ent.canonical_name} ({ent.entity_type})
                  </option>
                ))}
              </select>
            </div>

            {/* Relationship Type */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="rel-predicate">
                Relationship Type *
              </label>
              <select
                id="rel-predicate"
                className="kg-case-selector"
                value={relType}
                onChange={(e) => setRelType(e.target.value)}
                disabled={isSubmitting}
                style={{ width: '100%' }}
              >
                {ALL_RELATIONSHIP_TYPES.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </div>

            {/* Target Entity */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="rel-target">
                Target Entity *
              </label>
              <select
                id="rel-target"
                className="kg-case-selector"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                disabled={isSubmitting}
                style={{ width: '100%' }}
              >
                {entities.map((ent) => (
                  <option key={ent.id} value={ent.id}>
                    {ent.canonical_name} ({ent.entity_type})
                  </option>
                ))}
              </select>
            </div>

            {/* Evidence quote */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="rel-evidence">
                Supporting Citation / Text (optional)
              </label>
              <textarea
                id="rel-evidence"
                className="kg-notes-textarea"
                style={{ minHeight: '65px' }}
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                placeholder="Verbatim quote establishing this legal connection..."
                disabled={isSubmitting}
              />
            </div>

            {errorMessage && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: '#f87171', fontSize: '0.8rem' }}>
                <AlertCircle size={14} />
                <span>{errorMessage}</span>
              </div>
            )}
          </div>

          <div className="kg-modal-footer">
            <button type="button" className="kg-btn-secondary" onClick={onClose} disabled={isSubmitting}>
              Cancel
            </button>
            <button type="submit" className="kg-btn-primary" disabled={isSubmitting}>
              <GitFork size={14} />
              <span>{isSubmitting ? 'Creating...' : 'Create Relationship'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
