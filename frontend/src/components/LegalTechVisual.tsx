'use client';

import React, { useState } from 'react';
import { 
  FileText, 
  GitFork, 
  Clock, 
  ShieldCheck, 
  CheckCircle2, 
  AlertTriangle, 
  Sparkles,
  Zap,
  Database,
  Scale
} from 'lucide-react';

export const LegalTechVisual = () => {
  const [activeTab, setActiveTab] = useState<'contract' | 'graph' | 'timeline'>('contract');

  return (
    <div className="visual-hero-container">
      {/* Visual Navigation Tabs */}
      <div className="visual-nav-tabs">
        <button 
          className={`tab-btn ${activeTab === 'contract' ? 'active' : ''}`}
          onClick={() => setActiveTab('contract')}
        >
          <FileText size={15} />
          <span>Contract AI</span>
        </button>
        <button 
          className={`tab-btn ${activeTab === 'graph' ? 'active' : ''}`}
          onClick={() => setActiveTab('graph')}
        >
          <GitFork size={15} />
          <span>Precedent Graph</span>
        </button>
        <button 
          className={`tab-btn ${activeTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          <Clock size={15} />
          <span>Evidence Timeline</span>
        </button>
      </div>

      {/* Main Glass Workspace Graphic Container */}
      <div className="workspace-card">
        {/* Top Window Bar */}
        <div className="workspace-header">
          <div className="window-dots">
            <span className="dot red"></span>
            <span className="dot yellow"></span>
            <span className="dot green"></span>
          </div>
          <div className="workspace-title">
            <Sparkles size={13} className="title-icon" />
            <span>LegalLens Intelligence Studio v3.4</span>
          </div>
          <div className="status-badge">
            <span className="status-pulse"></span>
            <span>98.6% Match Confidence</span>
          </div>
        </div>

        {/* Tab 1: Contract Analysis & AI Redline */}
        {activeTab === 'contract' && (
          <div className="workspace-content animate-fade-in">
            <div className="doc-preview-header">
              <div className="doc-meta">
                <FileText size={18} className="doc-icon" />
                <div>
                  <h4 className="doc-name">Master_Services_Agreement_2026.pdf</h4>
                  <span className="doc-sub">Section 14 — Indemnity & Liability Caps</span>
                </div>
              </div>
              <span className="ai-status-pill">
                <Zap size={13} /> AI Redlining Active
              </span>
            </div>

            {/* Document Content with AI Annotations */}
            <div className="contract-paper">
              <div className="scan-line"></div>
              
              <div className="contract-text-block">
                <p className="contract-line">
                  <span className="line-num">14.1</span> 
                  <span className="text-normal"> The Service Provider agrees to indemnify, defend, and hold harmless Customer against any third-party claims arising from </span>
                  <span className="text-highlight cyan">gross negligence or willful misconduct</span>.
                </p>
                
                <div className="ai-annotation-card cyan-border">
                  <div className="annotation-header">
                    <CheckCircle2 size={14} className="icon-cyan" />
                    <span className="annotation-title">AI Compliance Verification</span>
                    <span className="confidence-tag">99.2% Match</span>
                  </div>
                  <p className="annotation-desc">
                    Aligns with <strong>Delaware Chancery Court Precedent (2024)</strong> regarding standard indemnification boundaries.
                  </p>
                </div>

                <p className="contract-line mt-3">
                  <span className="line-num">14.2</span> 
                  <span className="text-normal"> In no event shall aggregate liability exceed the total fees paid under this Agreement during the </span>
                  <span className="text-highlight gold">prior twelve (12) month period</span>.
                </p>

                <div className="ai-annotation-card gold-border">
                  <div className="annotation-header">
                    <AlertTriangle size={14} className="icon-gold" />
                    <span className="annotation-title">Clause Risk Analysis</span>
                    <span className="risk-tag">Low Risk</span>
                  </div>
                  <p className="annotation-desc">
                    Liability cap matches 84% of top tier tech transaction benchmarks in 2025-2026.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 2: Precedent Node Graph */}
        {activeTab === 'graph' && (
          <div className="workspace-content animate-fade-in">
            <div className="graph-container">
              <div className="graph-header">
                <GitFork size={16} className="doc-icon" />
                <span className="graph-title">Citation Graph — Precedent Relationship Matrix</span>
              </div>

              {/* Node Graph Display */}
              <div className="graph-canvas">
                <svg className="graph-lines-svg" viewBox="0 0 500 240">
                  <path d="M 120 70 L 250 120 M 250 120 L 380 60 M 250 120 L 370 180 M 120 70 L 140 180 M 140 180 L 250 120" 
                    stroke="rgba(0, 240, 255, 0.3)" strokeWidth="2" strokeDasharray="4 4" className="svg-line" />
                </svg>

                <div className="node node-main" style={{ top: '45%', left: '48%' }}>
                  <Scale size={16} />
                  <span>Target Case #2026</span>
                </div>

                <div className="node node-sub node-cyan" style={{ top: '22%', left: '18%' }}>
                  <FileText size={14} />
                  <span>Marbury v. State</span>
                  <small>98% Relevancy</small>
                </div>

                <div className="node node-sub node-indigo" style={{ top: '18%', left: '72%' }}>
                  <Database size={14} />
                  <span>Statute § 402(b)</span>
                  <small>Federal Code</small>
                </div>

                <div className="node node-sub node-gold" style={{ top: '70%', left: '70%' }}>
                  <CheckCircle2 size={14} />
                  <span>Apex Tech Ruling</span>
                  <small>Appellate Precedent</small>
                </div>

                <div className="node node-sub node-cyan" style={{ top: '68%', left: '22%' }}>
                  <ShieldCheck size={14} />
                  <span>Indemnity Rule</span>
                  <small>Supreme Court</small>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Tab 3: Timeline & Evidence */}
        {activeTab === 'timeline' && (
          <div className="workspace-content animate-fade-in">
            <div className="timeline-container">
              <div className="timeline-header">
                <Clock size={16} className="doc-icon" />
                <span className="graph-title">Chronological Discovery & Evidence Timeline</span>
              </div>

              <div className="timeline-items">
                <div className="timeline-item">
                  <div className="timeline-marker cyan"></div>
                  <div className="timeline-date">JAN 14, 2026</div>
                  <div className="timeline-content">
                    <h5>Contract Execution & MSA Signed</h5>
                    <p>Document #DOC-491 verified with 14 clauses extracted.</p>
                  </div>
                </div>

                <div className="timeline-item">
                  <div className="timeline-marker indigo"></div>
                  <div className="timeline-date">MAR 02, 2026</div>
                  <div className="timeline-content">
                    <h5>Deposition Transcript Analyzed</h5>
                    <p>Witness statement cross-referenced with Email Exhibit B.</p>
                  </div>
                </div>

                <div className="timeline-item">
                  <div className="timeline-marker gold"></div>
                  <div className="timeline-date">AUG 19, 2026</div>
                  <div className="timeline-content">
                    <h5>Precedent Citation Matched</h5>
                    <p>Automated summary generated with 4 key legal precedents.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Floating Mini Overlay Badges */}
        <div className="floating-badge badge-top-right animate-float">
          <Sparkles size={14} className="icon-cyan" />
          <div>
            <div className="floating-title">AI Citation Engine</div>
            <div className="floating-sub">14,200 Precedents Synchronized</div>
          </div>
        </div>

        <div className="floating-badge badge-bottom-left">
          <ShieldCheck size={14} className="icon-cyan" />
          <div>
            <div className="floating-title">Zero Data Leakage</div>
            <div className="floating-sub">SOC2 Type II & HIPAA Certified</div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .visual-hero-container {
          width: 100%;
          position: relative;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1rem;
        }

        .visual-nav-tabs {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.3rem 0.4rem;
          background: rgba(13, 18, 31, 0.8);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-radius: 100px;
          z-index: 10;
        }

        .tab-btn {
          display: flex;
          align-items: center;
          gap: 0.45rem;
          padding: 0.45rem 1rem;
          border-radius: 100px;
          border: none;
          background: transparent;
          color: var(--text-secondary);
          font-size: 0.82rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.25 ease;
        }

        .tab-btn.active {
          background: linear-gradient(135deg, rgba(0, 240, 255, 0.2), rgba(99, 102, 241, 0.2));
          color: #ffffff;
          border: 1px solid rgba(0, 240, 255, 0.4);
          box-shadow: 0 4px 15px rgba(0, 240, 255, 0.15);
        }

        .workspace-card {
          position: relative;
          width: 100%;
          max-width: 580px;
          min-height: 420px;
          background: rgba(13, 18, 31, 0.85);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-radius: 20px;
          box-shadow: 
            0 25px 50px -12px rgba(0, 0, 0, 0.6),
            0 0 40px rgba(0, 240, 255, 0.08),
            inset 0 1px 0 rgba(255, 255, 255, 0.1);
          overflow: hidden;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .workspace-card:hover {
          border-color: rgba(0, 240, 255, 0.3);
          box-shadow: 
            0 30px 60px -12px rgba(0, 0, 0, 0.7),
            0 0 50px rgba(0, 240, 255, 0.15);
        }

        .workspace-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.85rem 1.25rem;
          background: rgba(7, 9, 14, 0.6);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }

        .window-dots {
          display: flex;
          align-items: center;
          gap: 0.4rem;
        }

        .dot {
          width: 9px;
          height: 9px;
          border-radius: 50%;
        }
        .dot.red { background: #ff5f56; }
        .dot.yellow { background: #ffbd2e; }
        .dot.green { background: #27c93f; }

        .workspace-title {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-secondary);
        }

        .title-icon {
          color: var(--accent-cyan);
        }

        .status-badge {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.2rem 0.6rem;
          background: rgba(0, 240, 255, 0.1);
          border: 1px solid rgba(0, 240, 255, 0.25);
          border-radius: 100px;
          font-size: 0.68rem;
          font-weight: 700;
          color: var(--accent-cyan);
        }

        .status-pulse {
          width: 6px;
          height: 6px;
          background: var(--accent-cyan);
          border-radius: 50%;
          box-shadow: 0 0 6px var(--accent-cyan);
        }

        .workspace-content {
          padding: 1.25rem;
        }

        .animate-fade-in {
          animation: fadeIn 0.35s ease-out forwards;
        }

        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }

        .doc-preview-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
        }

        .doc-meta {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }

        .doc-icon {
          color: var(--accent-cyan);
        }

        .doc-name {
          font-size: 0.9rem;
          font-weight: 700;
          color: #ffffff;
        }

        .doc-sub {
          font-size: 0.72rem;
          color: var(--text-muted);
        }

        .ai-status-pill {
          display: flex;
          align-items: center;
          gap: 0.3rem;
          font-size: 0.7rem;
          font-weight: 700;
          color: #00f0ff;
          background: rgba(0, 240, 255, 0.1);
          padding: 0.25rem 0.6rem;
          border-radius: 6px;
        }

        .contract-paper {
          position: relative;
          padding: 1rem;
          background: rgba(7, 9, 14, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
          overflow: hidden;
        }

        .scan-line {
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 2px;
          background: linear-gradient(90deg, transparent, var(--accent-cyan), transparent);
          box-shadow: 0 0 10px var(--accent-cyan);
          animation: scanline 4s linear infinite;
        }

        .line-num {
          font-family: monospace;
          color: var(--text-dim);
          font-weight: 600;
          margin-right: 0.4rem;
        }

        .contract-line {
          font-size: 0.82rem;
          line-height: 1.55;
          color: #cbd5e1;
        }

        .text-highlight.cyan {
          background: rgba(0, 240, 255, 0.15);
          color: #7dd3fc;
          border-bottom: 1.5px solid var(--accent-cyan);
          padding: 0 0.2rem;
          border-radius: 3px;
        }

        .text-highlight.gold {
          background: rgba(212, 175, 55, 0.15);
          color: #fde047;
          border-bottom: 1.5px solid var(--accent-gold);
          padding: 0 0.2rem;
          border-radius: 3px;
        }

        .ai-annotation-card {
          margin: 0.6rem 0;
          padding: 0.6rem 0.8rem;
          border-radius: 8px;
          background: rgba(13, 18, 31, 0.9);
          font-size: 0.78rem;
        }

        .cyan-border {
          border-left: 3px solid var(--accent-cyan);
          background: rgba(0, 240, 255, 0.05);
        }

        .gold-border {
          border-left: 3px solid var(--accent-gold);
          background: rgba(212, 175, 55, 0.05);
        }

        .annotation-header {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          margin-bottom: 0.2rem;
        }

        .annotation-title {
          font-weight: 700;
          color: #ffffff;
        }

        .confidence-tag, .risk-tag {
          margin-left: auto;
          font-size: 0.68rem;
          font-weight: 700;
          padding: 0.1rem 0.4rem;
          border-radius: 4px;
        }

        .confidence-tag {
          background: rgba(0, 240, 255, 0.2);
          color: var(--accent-cyan);
        }

        .risk-tag {
          background: rgba(212, 175, 55, 0.2);
          color: var(--accent-gold);
        }

        .annotation-desc {
          color: var(--text-secondary);
          line-height: 1.4;
          font-size: 0.75rem;
        }

        .mt-3 {
          margin-top: 0.75rem;
        }

        /* Node Graph Styling */
        .graph-container {
          min-height: 280px;
          display: flex;
          flex-direction: column;
        }

        .graph-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .graph-title {
          font-size: 0.88rem;
          font-weight: 700;
          color: #ffffff;
        }

        .graph-canvas {
          position: relative;
          height: 250px;
          background: rgba(7, 9, 14, 0.7);
          border: 1px solid rgba(255, 255, 255, 0.06);
          border-radius: 12px;
        }

        .graph-lines-svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }

        .node {
          position: absolute;
          transform: translate(-50%, -50%);
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 0.5rem 0.8rem;
          border-radius: 10px;
          font-size: 0.75rem;
          font-weight: 700;
          gap: 0.2rem;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
          transition: all 0.3s ease;
        }

        .node:hover {
          transform: translate(-50%, -50%) scale(1.08);
          z-index: 20;
        }

        .node-main {
          background: linear-gradient(135deg, #00f0ff, #6366f1);
          color: #07090e;
          border: 1px solid #ffffff;
          box-shadow: 0 0 20px rgba(0, 240, 255, 0.4);
        }

        .node-sub {
          background: rgba(13, 18, 31, 0.95);
          backdrop-filter: blur(10px);
          border: 1px solid rgba(255, 255, 255, 0.15);
          color: #ffffff;
        }

        .node-sub small {
          font-size: 0.62rem;
          font-weight: 500;
          color: var(--text-secondary);
        }

        .node-cyan { border-color: rgba(0, 240, 255, 0.5); }
        .node-indigo { border-color: rgba(99, 102, 241, 0.5); }
        .node-gold { border-color: rgba(212, 175, 55, 0.5); }

        /* Timeline Styling */
        .timeline-container {
          min-height: 280px;
        }

        .timeline-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .timeline-items {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          padding-left: 0.5rem;
        }

        .timeline-item {
          display: flex;
          gap: 1rem;
          position: relative;
        }

        .timeline-marker {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          margin-top: 0.3rem;
          flex-shrink: 0;
        }

        .timeline-marker.cyan { background: var(--accent-cyan); box-shadow: 0 0 10px var(--accent-cyan); }
        .timeline-marker.indigo { background: var(--accent-indigo); box-shadow: 0 0 10px var(--accent-indigo); }
        .timeline-marker.gold { background: var(--accent-gold); box-shadow: 0 0 10px var(--accent-gold); }

        .timeline-date {
          font-size: 0.68rem;
          font-weight: 800;
          color: var(--text-dim);
          width: 90px;
          flex-shrink: 0;
          margin-top: 0.2rem;
        }

        .timeline-content h5 {
          font-size: 0.85rem;
          font-weight: 700;
          color: #ffffff;
        }

        .timeline-content p {
          font-size: 0.75rem;
          color: var(--text-secondary);
        }

        /* Floating Overlays */
        .floating-badge {
          position: absolute;
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.5rem 0.85rem;
          background: rgba(13, 18, 31, 0.9);
          backdrop-filter: blur(16px);
          border: 1px solid rgba(255, 255, 255, 0.15);
          border-radius: 12px;
          box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
          z-index: 15;
        }

        .badge-top-right {
          top: -10px;
          right: -10px;
          border-color: rgba(0, 240, 255, 0.3);
        }

        .badge-bottom-left {
          bottom: 12px;
          right: 12px;
          border-color: rgba(99, 102, 241, 0.3);
        }

        .floating-title {
          font-size: 0.75rem;
          font-weight: 700;
          color: #ffffff;
        }

        .floating-sub {
          font-size: 0.65rem;
          color: var(--text-secondary);
        }

        .icon-cyan { color: var(--accent-cyan); }
        .icon-gold { color: var(--accent-gold); }

        @media (max-width: 640px) {
          .floating-badge {
            display: none;
          }
          .workspace-card {
            min-height: 380px;
          }
        }
      `}</style>
    </div>
  );
};
