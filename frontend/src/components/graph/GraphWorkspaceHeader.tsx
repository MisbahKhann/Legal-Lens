'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  Upload,
  Plus,
  GitFork,
  Loader2,
  ChevronDown,
  MoreHorizontal,
} from 'lucide-react';
import { CaseSummary, GraphViewMode } from './types';

interface GraphWorkspaceHeaderProps {
  cases: CaseSummary[];
  selectedCaseId: string;
  onSelectCase: (caseId: string) => void;
  viewMode: GraphViewMode;
  onChangeViewMode: (mode: GraphViewMode) => void;
  isSaving: boolean;
  lastSavedAt: number | null;
  saveError: string | null;
  onOpenUpload: () => void;
  onOpenAddEntity: () => void;
  onOpenAddRelationship: () => void;
}

const VIEW_OPTIONS: { id: GraphViewMode; label: string }[] = [
  { id: 'overview', label: 'Full case' },
  { id: 'evidence', label: 'Documents & evidence' },
  { id: 'people', label: 'People & organizations' },
  { id: 'authorities', label: 'Statutes & authorities' },
  { id: 'timeline', label: 'Events & dates' },
];

export const GraphWorkspaceHeader: React.FC<GraphWorkspaceHeaderProps> = ({
  cases,
  selectedCaseId,
  onSelectCase,
  viewMode,
  onChangeViewMode,
  isSaving,
  lastSavedAt,
  saveError,
  onOpenUpload,
  onOpenAddEntity,
  onOpenAddRelationship,
}) => {
  const [actionsOpen, setActionsOpen] = useState(false);
  const currentView = VIEW_OPTIONS.find((v) => v.id === viewMode)?.label ?? 'Full case';

  let saveLabel = 'Ready';
  if (isSaving) saveLabel = 'Saving…';
  else if (saveError) saveLabel = 'Save failed';
  else if (lastSavedAt) saveLabel = 'Saved';

  return (
    <header className="kg-topbar" aria-label="Knowledge Graph Workspace Header">
      <div className="kg-topbar-left">
        <Link href="/" className="kg-brand-link" title="Back to LegalLens home">
          <ArrowLeft size={18} />
          <span>LegalLens</span>
        </Link>

        <select
          className="kg-case-selector"
          value={selectedCaseId}
          onChange={(e) => onSelectCase(e.target.value)}
          aria-label="Select case"
        >
          {cases.length === 0 ? (
            <option value="">No cases yet</option>
          ) : (
            cases.map((c) => (
              <option key={c.case_id} value={c.case_id}>
                {c.title || c.case_id} · {c.entity_count} entities
              </option>
            ))
          )}
        </select>

        <div className="kg-view-select-wrap">
          <label className="kg-view-select-label" htmlFor="kg-view-select">
            View
          </label>
          <div className="kg-view-select-inner">
            <select
              id="kg-view-select"
              className="kg-view-select"
              value={viewMode}
              onChange={(e) => onChangeViewMode(e.target.value as GraphViewMode)}
              aria-label="Graph view filter"
            >
              {VIEW_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
            <ChevronDown size={16} className="kg-view-select-chevron" aria-hidden />
          </div>
          <span className="kg-view-select-hint">{currentView}</span>
        </div>
      </div>

      <div className="kg-topbar-right">
        <div
          className={`kg-status-badge ${isSaving ? 'saving' : ''} ${saveError ? 'error' : ''}`}
          title={saveError ?? (lastSavedAt ? 'Last change confirmed by server' : 'No pending changes')}
        >
          {isSaving ? <Loader2 size={15} className="kg-spin" /> : null}
          <span>{saveLabel}</span>
        </div>

        <button type="button" className="kg-btn-primary" onClick={onOpenUpload}>
          <Upload size={17} />
          <span>Upload</span>
        </button>

        <div className="kg-actions-menu">
          <button
            type="button"
            className="kg-btn-secondary"
            onClick={() => setActionsOpen((o) => !o)}
            aria-expanded={actionsOpen}
            aria-haspopup="true"
          >
            <MoreHorizontal size={17} />
            <span>Actions</span>
          </button>
          {actionsOpen && (
            <div className="kg-actions-dropdown" role="menu">
              <button type="button" role="menuitem" onClick={() => { setActionsOpen(false); onOpenAddEntity(); }}>
                <Plus size={16} />
                Add entity
              </button>
              <button type="button" role="menuitem" onClick={() => { setActionsOpen(false); onOpenAddRelationship(); }}>
                <GitFork size={16} />
                Add relationship
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
