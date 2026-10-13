'use client';

import React from 'react';
import { AlertTriangle, Trash2, X } from 'lucide-react';
import { EntityNode } from './types';

interface DeleteConfirmModalProps {
  entity: EntityNode | null;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  isDeleting: boolean;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  entity,
  onClose,
  onConfirm,
  isDeleting,
}) => {
  if (!entity) return null;

  return (
    <div className="kg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="delete-confirm-title">
      <div className="kg-modal-card" style={{ maxWidth: '420px' }}>
        <div className="kg-modal-header" style={{ borderColor: 'rgba(239, 68, 68, 0.2)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171', fontWeight: 700 }} id="delete-confirm-title">
            <AlertTriangle size={18} />
            <span>Confirm Entity Deletion</span>
          </div>
          <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close modal">
            <X size={18} />
          </button>
        </div>

        <div className="kg-modal-body">
          <p style={{ fontSize: '0.88rem', color: 'var(--text-cream, #f5ede1)', lineHeight: 1.5 }}>
            Are you sure you want to remove <strong style={{ color: '#fff' }}>&quot;{entity.canonical_name}&quot;</strong> ({entity.entity_type})?
          </p>

          <div
            style={{
              background: 'rgba(239, 68, 68, 0.08)',
              borderLeft: '3px solid #ef4444',
              padding: '0.65rem 0.8rem',
              borderRadius: '0 6px 6px 0',
              fontSize: '0.78rem',
              color: '#fca5a5',
              lineHeight: 1.45,
            }}
          >
            <strong>Warning:</strong> Deleting this entity will permanently detach and remove all connecting legal relationships from the case graph in Neo4j.
          </div>
        </div>

        <div className="kg-modal-footer">
          <button type="button" className="kg-btn-secondary" onClick={onClose} disabled={isDeleting}>
            Cancel
          </button>
          <button
            type="button"
            className="kg-btn-primary"
            style={{ backgroundColor: '#dc2626', borderColor: '#b91c1c' }}
            onClick={onConfirm}
            disabled={isDeleting}
          >
            <Trash2 size={14} />
            <span>{isDeleting ? 'Deleting...' : 'Delete Entity & Edges'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
