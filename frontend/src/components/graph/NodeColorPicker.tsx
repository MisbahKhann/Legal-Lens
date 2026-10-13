'use client';

import React from 'react';
import { RotateCcw } from 'lucide-react';
import { getDefaultNodeColor } from './types';

interface NodeColorPickerProps {
  currentColor?: string;
  defaultType: string;
  onChangeColor: (hex: string) => void;
  onResetColor: () => void;
}

const PRESET_PALETTE = [
  '#6B1F28', // Deep Burgundy
  '#8B2935', // Bright Burgundy
  '#C9A24B', // Muted Gold
  '#E2B857', // Bright Gold
  '#F5EDE1', // Warm Cream
  '#1E3A8A', // Slate Blue
  '#15803D', // Forest Green
  '#9A3412', // Terracotta
  '#7C3AED', // Royal Purple
  '#374151', // Charcoal
];

export const NodeColorPicker: React.FC<NodeColorPickerProps> = ({
  currentColor,
  defaultType,
  onChangeColor,
  onResetColor,
}) => {
  const defaultColor = getDefaultNodeColor(defaultType);
  const effectiveColor = currentColor || defaultColor;
  const isCustomized = Boolean(currentColor && currentColor !== defaultColor);

  return (
    <div className="kg-meta-row" style={{ gap: '0.6rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span className="kg-meta-label">Node Color Customization</span>
        {isCustomized && (
          <span style={{ fontSize: '0.68rem', color: 'var(--accent-gold, #c9a24b)', fontWeight: 600 }}>
            Customized
          </span>
        )}
      </div>

      <div className="kg-palette-grid">
        {PRESET_PALETTE.map((hex) => (
          <button
            key={hex}
            type="button"
            className={`kg-palette-swatch ${effectiveColor.toUpperCase() === hex.toUpperCase() ? 'active' : ''}`}
            style={{ backgroundColor: hex }}
            onClick={() => onChangeColor(hex)}
            title={`Set color to ${hex}`}
          />
        ))}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.25rem' }}>
        <input
          type="color"
          value={effectiveColor}
          onChange={(e) => onChangeColor(e.target.value)}
          style={{ width: '32px', height: '32px', border: 'none', background: 'transparent', cursor: 'pointer' }}
          title="Pick custom color"
        />
        <input
          type="text"
          value={effectiveColor}
          onChange={(e) => onChangeColor(e.target.value)}
          className="kg-search-input"
          style={{ width: '90px', padding: '0.3rem 0.5rem', fontSize: '0.8rem' }}
          placeholder="#HEX"
        />
        <button
          type="button"
          className="kg-btn-secondary"
          style={{ padding: '0.35rem 0.6rem', fontSize: '0.74rem', marginLeft: 'auto' }}
          onClick={onResetColor}
          title="Reset to category default color"
        >
          <RotateCcw size={12} />
          <span>Reset</span>
        </button>
      </div>
    </div>
  );
};
