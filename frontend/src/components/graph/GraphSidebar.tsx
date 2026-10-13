'use client';

import React, { useState } from 'react';
import { Search, RotateCcw, ChevronDown, ChevronRight } from 'lucide-react';
import { EntityNode, RelationshipEdge, ENTITY_CATEGORIES, getEntityCategory } from './types';

interface GraphSidebarProps {
  entities: EntityNode[];
  relationships: RelationshipEdge[];
  searchQuery: string;
  onSearchChange: (q: string) => void;
  onSelectSearchEntity: (entityId: string) => void;
  selectedCategories: string[];
  onToggleCategory: (cat: string) => void;
  selectedRelTypes: string[];
  onToggleRelType: (relType: string) => void;
  onResetFilters: () => void;
  neighborhoodDepth: number;
  onChangeDepth: (depth: number) => void;
}

const CATEGORY_DISPLAY_NAMES: Record<string, string> = {
  PARTY_LEGAL_ACTOR: 'People & organizations',
  CASE_MATTER: 'Case & claims',
  LEGAL_SOURCE_NORMATIVE: 'Statutes & concepts',
  DOCUMENTARY_EVIDENCE: 'Documents & evidence',
  TEMPORAL_EVENT: 'Events & dates',
};

function CollapsibleSection({
  title,
  defaultOpen = true,
  children,
  action,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="kg-sidebar-section">
      {/* Wrapper is a div so the optional action button is never nested inside another button */}
      <div className="kg-section-toggle-row">
        <button
          type="button"
          className="kg-section-toggle"
          onClick={() => setOpen((v) => !v)}
          aria-expanded={open}
        >
          {open ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          <span>{title}</span>
        </button>
        {action ? <span className="kg-section-toggle-action">{action}</span> : null}
      </div>
      {open ? <div className="kg-section-body">{children}</div> : null}
    </div>
  );
}

export const GraphSidebar: React.FC<GraphSidebarProps> = ({
  entities,
  relationships,
  searchQuery,
  onSearchChange,
  onSelectSearchEntity,
  selectedCategories,
  onToggleCategory,
  selectedRelTypes,
  onToggleRelType,
  onResetFilters,
  neighborhoodDepth,
  onChangeDepth,
}) => {
  const categoryCounts: Record<string, number> = {};
  for (const cat of Object.keys(ENTITY_CATEGORIES)) {
    categoryCounts[cat] = 0;
  }
  for (const ent of entities) {
    const cat = getEntityCategory(ent.entity_type);
    categoryCounts[cat] = (categoryCounts[cat] || 0) + 1;
  }

  const relCounts: Record<string, number> = {};
  for (const r of relationships) {
    relCounts[r.relationship_type] = (relCounts[r.relationship_type] || 0) + 1;
  }

  const searchResults = searchQuery.trim()
    ? entities
        .filter(
          (e) =>
            e.canonical_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            e.entity_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
            (e.aliases && e.aliases.some((a) => a.toLowerCase().includes(searchQuery.toLowerCase())))
        )
        .slice(0, 12)
    : [];

  return (
    <aside className="kg-sidebar" aria-label="Graph search and filters">
      <CollapsibleSection title="Find entity" defaultOpen>
        <div className="kg-search-box">
          <Search size={18} className="kg-search-icon" />
          <input
            type="search"
            className="kg-search-input"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Name, role, or alias…"
          />
        </div>

        {searchResults.length > 0 && (
          <ul className="kg-search-results">
            {searchResults.map((res) => (
              <li key={res.id}>
                <button type="button" className="kg-search-result-btn" onClick={() => onSelectSearchEntity(res.id)}>
                  <span className="kg-search-result-name">{res.canonical_name}</span>
                  <span className="kg-search-result-type">{res.entity_type}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </CollapsibleSection>

      <CollapsibleSection
        title="Entity types"
        defaultOpen
        action={
          <button type="button" className="kg-link-btn" onClick={onResetFilters} title="Reset all filters">
            <RotateCcw size={14} />
            Reset
          </button>
        }
      >
        <div className="kg-filter-group">
          {Object.entries(CATEGORY_DISPLAY_NAMES).map(([key, label]) => {
            const isChecked = selectedCategories.includes(key);
            const count = categoryCounts[key] || 0;
            return (
              <label key={key} className="kg-filter-label">
                <input type="checkbox" checked={isChecked} onChange={() => onToggleCategory(key)} />
                <span>{label}</span>
                <span className="kg-filter-count">{count}</span>
              </label>
            );
          })}
        </div>
      </CollapsibleSection>

      <CollapsibleSection title="Advanced filters" defaultOpen={false}>
        <p className="kg-sidebar-help">Hide relationship types or focus on connections near a selected entity.</p>

        <p className="kg-sidebar-subhead">Relationship types</p>
        <div className="kg-filter-group">
          {Object.keys(relCounts).length === 0 ? (
            <span className="kg-sidebar-muted">No relationships in this case yet.</span>
          ) : (
            Object.entries(relCounts).map(([relType, count]) => {
              const isChecked = selectedRelTypes.includes(relType);
              return (
                <label key={relType} className="kg-filter-label">
                  <input type="checkbox" checked={isChecked} onChange={() => onToggleRelType(relType)} />
                  <span>{relType.replace(/_/g, ' ').toLowerCase()}</span>
                  <span className="kg-filter-count">{count}</span>
                </label>
              );
            })
          )}
        </div>

        <p className="kg-sidebar-subhead">Connection depth</p>
        <p className="kg-sidebar-muted">
          {neighborhoodDepth === 0
            ? 'Showing the full filtered graph.'
            : `Showing entities within ${neighborhoodDepth} step${neighborhoodDepth > 1 ? 's' : ''} of the selected node.`}
        </p>
        <input
          type="range"
          className="kg-range"
          min="0"
          max="3"
          step="1"
          value={neighborhoodDepth}
          onChange={(e) => onChangeDepth(parseInt(e.target.value, 10))}
          aria-label="Connection depth from selected entity"
        />
        <div className="kg-range-labels">
          <span>All</span>
          <span>1</span>
          <span>2</span>
          <span>3</span>
        </div>
      </CollapsibleSection>
    </aside>
  );
};
