'use client';

import React from 'react';
import { CATEGORY_COLORS } from './types';

export const GraphLegend: React.FC = () => {
  return (
    <div className="kg-legend-overlay" aria-label="Ontology Type Legend">
      <div className="kg-legend-item">
        <span className="kg-legend-dot" style={{ backgroundColor: CATEGORY_COLORS.PARTY_LEGAL_ACTOR.base }} />
        <span>People & Actors</span>
      </div>
      <div className="kg-legend-item">
        <span className="kg-legend-dot" style={{ backgroundColor: CATEGORY_COLORS.CASE_MATTER.base }} />
        <span>Case & Claims</span>
      </div>
      <div className="kg-legend-item">
        <span className="kg-legend-dot" style={{ backgroundColor: CATEGORY_COLORS.LEGAL_SOURCE_NORMATIVE.base }} />
        <span>Statutes & Concepts</span>
      </div>
      <div className="kg-legend-item">
        <span className="kg-legend-dot" style={{ backgroundColor: CATEGORY_COLORS.DOCUMENTARY_EVIDENCE.base }} />
        <span>Evidence & Docs</span>
      </div>
      <div className="kg-legend-item">
        <span className="kg-legend-dot" style={{ backgroundColor: CATEGORY_COLORS.TEMPORAL_EVENT.base }} />
        <span>Events & Timeline</span>
      </div>
    </div>
  );
};
