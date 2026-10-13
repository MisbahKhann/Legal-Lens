'use client';

import React from 'react';
import { ZoomIn, ZoomOut, Maximize, RotateCcw, Network, Layers } from 'lucide-react';

interface GraphToolbarProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFitView: () => void;
  onResetView: () => void;
  layoutMode: string;
  onChangeLayout: (layout: string) => void;
}

export const GraphToolbar: React.FC<GraphToolbarProps> = ({
  onZoomIn,
  onZoomOut,
  onFitView,
  onResetView,
  layoutMode,
  onChangeLayout,
}) => {
  return (
    <div className="kg-floating-toolbar" role="toolbar" aria-label="Graph controls">
      <button type="button" className="kg-tool-btn" onClick={onZoomIn} title="Zoom in">
        <ZoomIn size={20} />
      </button>
      <button type="button" className="kg-tool-btn" onClick={onZoomOut} title="Zoom out">
        <ZoomOut size={20} />
      </button>
      <button type="button" className="kg-tool-btn" onClick={onFitView} title="Fit graph in view">
        <Maximize size={18} />
        <span className="kg-tool-label">Fit</span>
      </button>
      <button type="button" className="kg-tool-btn" onClick={onResetView} title="Reset filters and show full graph">
        <RotateCcw size={18} />
        <span className="kg-tool-label">Reset</span>
      </button>

      <div className="kg-tool-separator" />

      <button
        type="button"
        className={`kg-tool-btn ${layoutMode === 'cose' ? 'active' : ''}`}
        onClick={() => onChangeLayout('cose')}
        title="Network layout"
      >
        <Network size={20} />
      </button>
      <button
        type="button"
        className={`kg-tool-btn ${layoutMode === 'breadthfirst' ? 'active' : ''}`}
        onClick={() => onChangeLayout('breadthfirst')}
        title="Hierarchy layout"
      >
        <Layers size={20} />
      </button>
    </div>
  );
};
