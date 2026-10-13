'use client';

import React, { useState } from 'react';
import { Save, Check, Loader2 } from 'lucide-react';

interface EntityNotesEditorProps {
  initialNotes?: string;
  onSaveNotes: (notes: string) => Promise<void>;
}

export const EntityNotesEditor: React.FC<EntityNotesEditorProps> = ({
  initialNotes = '',
  onSaveNotes,
}) => {
  const [prevInitial, setPrevInitial] = useState(initialNotes);
  const [notes, setNotes] = useState(initialNotes);
  const [isSaving, setIsSaving] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  if (initialNotes !== prevInitial) {
    setPrevInitial(initialNotes);
    setNotes(initialNotes);
    setHasUnsavedChanges(false);
    setSaveSuccess(false);
  }

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setNotes(e.target.value);
    setHasUnsavedChanges(e.target.value !== initialNotes);
    setSaveSuccess(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSaveNotes(notes);
      setHasUnsavedChanges(false);
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 2500);
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancel = () => {
    setNotes(initialNotes);
    setHasUnsavedChanges(false);
  };

  return (
    <div className="kg-meta-row" style={{ gap: '0.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="kg-meta-label">Investigator Notes</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.72rem' }}>
          {isSaving ? (
            <span style={{ color: '#fbbf24', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Loader2 size={11} className="animate-spin" /> Saving
            </span>
          ) : hasUnsavedChanges ? (
            <span style={{ color: '#f87171' }}>• Unsaved changes</span>
          ) : saveSuccess ? (
            <span style={{ color: '#34d399', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
              <Check size={12} /> Saved to server
            </span>
          ) : null}
        </div>
      </div>

      <textarea
        className="kg-notes-textarea"
        value={notes}
        onChange={handleChange}
        placeholder="Attach case notes, witness cross-examination strategies, or documentary references..."
      />

      {hasUnsavedChanges && (
        <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end', marginTop: '0.25rem' }}>
          <button
            type="button"
            className="kg-btn-secondary"
            style={{ padding: '0.35rem 0.65rem', fontSize: '0.76rem' }}
            onClick={handleCancel}
            disabled={isSaving}
          >
            Cancel
          </button>
          <button
            type="button"
            className="kg-btn-primary"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.76rem' }}
            onClick={handleSave}
            disabled={isSaving}
          >
            <Save size={12} />
            <span>Save Notes</span>
          </button>
        </div>
      )}
    </div>
  );
};
