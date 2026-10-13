'use client';

import React, { useState } from 'react';
import { X, Plus, AlertCircle } from 'lucide-react';
import { ALL_ENTITY_TYPES } from './types';

interface AddEntityModalProps {
  onClose: () => void;
  onSubmit: (data: {
    canonical_name: string;
    entity_type: string;
    aliases?: string[];
    source_text?: string;
  }) => Promise<void>;
}

export const AddEntityModal: React.FC<AddEntityModalProps> = ({
  onClose,
  onSubmit,
}) => {
  const [name, setName] = useState('');
  const [type, setType] = useState('PERSON');
  const [aliases, setAliases] = useState('');
  const [sourceText, setSourceText] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMessage('Entity name is required.');
      return;
    }

    setIsSubmitting(true);
    setErrorMessage(null);
    try {
      const aliasArray = aliases
        .split(',')
        .map((a) => a.trim())
        .filter((a) => a.length > 0);

      await onSubmit({
        canonical_name: name.trim(),
        entity_type: type,
        aliases: aliasArray,
        source_text: sourceText.trim() || undefined,
      });
      onClose();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to create entity.';
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="kg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="add-entity-title">
      <div className="kg-modal-card">
        <div className="kg-modal-header">
          <div className="kg-modal-title" id="add-entity-title">
            Add Legal Entity
          </div>
          <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="kg-modal-body">
            {/* Canonical Name */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="new-entity-name">
                Entity Name *
              </label>
              <input
                id="new-entity-name"
                type="text"
                className="kg-search-input"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Acme Corporation"
                autoFocus
                disabled={isSubmitting}
              />
            </div>

            {/* Entity Type Dropdown */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="new-entity-type">
                Controlled Entity Type *
              </label>
              <select
                id="new-entity-type"
                className="kg-case-selector"
                value={type}
                onChange={(e) => setType(e.target.value)}
                disabled={isSubmitting}
                style={{ width: '100%' }}
              >
                {ALL_ENTITY_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t}
                  </option>
                ))}
              </select>
            </div>

            {/* Aliases */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="new-entity-aliases">
                Aliases (comma separated)
              </label>
              <input
                id="new-entity-aliases"
                type="text"
                className="kg-search-input"
                value={aliases}
                onChange={(e) => setAliases(e.target.value)}
                placeholder="e.g., Acme, Acme Corp, Acme Co."
                disabled={isSubmitting}
              />
            </div>

            {/* Source Text citation */}
            <div className="kg-meta-row">
              <label className="kg-meta-label" htmlFor="new-entity-quote">
                Source Citation / Text Excerpt (optional)
              </label>
              <textarea
                id="new-entity-quote"
                className="kg-notes-textarea"
                style={{ minHeight: '70px' }}
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                placeholder="Exemplary quote from contract or deposition..."
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
              <Plus size={14} />
              <span>{isSubmitting ? 'Creating...' : 'Create Entity'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
