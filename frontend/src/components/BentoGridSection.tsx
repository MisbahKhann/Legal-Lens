'use client';

import React from 'react';
import { 
  GitFork, 
  AlertTriangle, 
  MessageSquareQuote, 
  Clock, 
  Languages, 
  ArrowRight, 
  CheckCircle2, 
  Sparkles, 
  Scale, 
  ShieldCheck,
  Zap
} from 'lucide-react';

export const BentoGridSection = () => {
  return (
    <section className="bento-section">
      <div className="bento-container">
        
        {/* Section Header matching structural inspiration */}
        <div className="bento-header">
          <h2 className="bento-main-title">
            Build Intelligent Legal Workflows<br />
            with <span className="title-highlight">Advanced AI</span>
          </h2>
          <p className="bento-subtitle">
            Synthesize precedent case law in seconds, analyze complex contracts, and verify citations with grounded precision.
          </p>
          <a href="#capabilities" className="bento-cta-btn">
            <span>Explore Platform Capabilities</span>
            <ArrowRight size={16} />
          </a>
        </div>

        {/* 5-Card Asymmetric Bento Showcase Grid */}
        <div className="bento-grid">

          {/* CARD 1: Knowledge Graph (Left Column) */}
          <div className="bento-card card-graph">
            <div className="card-badge">
              <GitFork size={13} />
              <span>GRAPH AI</span>
            </div>
            <div className="card-header-group">
              <h3 className="card-heading">Case Knowledge Graph</h3>
              <p className="card-body">Explore multi-dimensional connections between cases, statutes, judge rulings, and evidence.</p>
            </div>
            {/* Visual Node Diagram */}
            <div className="visual-mockup graph-visual">
              <div className="node-center">
                <Scale size={16} />
                <span>Target Case</span>
              </div>
              <div className="node-child node-1">
                <span>Marbury v. State</span>
              </div>
              <div className="node-child node-2">
                <span>Statute § 402</span>
              </div>
              <div className="node-child node-3">
                <span>Appellate Rule</span>
              </div>
              <svg className="node-svg" viewBox="0 0 200 120">
                <path d="M 100 60 L 40 30 M 100 60 L 160 30 M 100 60 L 100 100" stroke="rgba(201, 162, 75, 0.4)" strokeWidth="1.5" strokeDasharray="3 3" />
              </svg>
            </div>
          </div>

          {/* CARD 2: Clause Risk Engine */}
          <div className="bento-card card-risk">
            <div className="card-badge gold">
              <AlertTriangle size={13} />
              <span>RISK MATRIX</span>
            </div>
            <div className="card-header-group">
              <h3 className="card-heading">Clause Risk Flagging</h3>
              <p className="card-body">Automated redlining and liability compliance scoring for commercial agreements.</p>
            </div>
            <div className="visual-mockup risk-visual">
              <div className="risk-line">
                <span className="line-num">14.2</span>
                <span>Liability capped at 12 months fee total...</span>
              </div>
              <div className="risk-tag-box">
                <ShieldCheck size={14} className="text-gold" />
                <span>Standard Provision — 98.4% Confidence</span>
              </div>
            </div>
          </div>

          {/* CARD 3: Grounded Q&A (Centerpiece Hero Card with Glowing Gold Divider) */}
          <div className="bento-card card-qa-centerpiece">
            <div className="glowing-beam"></div>
            <div className="card-badge hero-badge">
              <Sparkles size={13} />
              <span>CITATION GROUNDED</span>
            </div>
            <div className="card-header-group">
              <h3 className="card-heading">Grounded Legal Q&A</h3>
              <p className="card-body">Ask complex legal questions with confidence. Every response is pinned to verified court sources.</p>
            </div>
            <div className="visual-mockup qa-visual">
              <div className="qa-query">
                <MessageSquareQuote size={15} className="text-gold" />
                <span>&quot;What are the precedent standards for contract frustration?&quot;</span>
              </div>
              <div className="qa-response">
                <div className="citation-pill">
                  <CheckCircle2 size={13} />
                  <span>Delaware Chancery Court (2024) § 104</span>
                </div>
                <p>Frustration requires an unforeseen supervening event that radically alters contractual obligations...</p>
              </div>
            </div>
          </div>

          {/* CARD 4: Timeline Engine */}
          <div className="bento-card card-timeline">
            <div className="card-badge">
              <Clock size={13} />
              <span>CHRONOLOGY</span>
            </div>
            <div className="card-header-group">
              <h3 className="card-heading">Evidence Timeline</h3>
              <p className="card-body">Extract chronological milestones from discovery transcripts and deposition exhibits.</p>
            </div>
            <div className="visual-mockup timeline-visual">
              <div className="timeline-node">
                <span className="dot"></span>
                <div>
                  <strong>JAN 14, 2026</strong>
                  <p>MSA Signed & Executed</p>
                </div>
              </div>
              <div className="timeline-node">
                <span className="dot gold"></span>
                <div>
                  <strong>MAR 02, 2026</strong>
                  <p>Deposition Transcript Filed</p>
                </div>
              </div>
            </div>
          </div>

          {/* CARD 5: Plain-Language Translator */}
          <div className="bento-card card-translator">
            <div className="card-badge">
              <Languages size={13} />
              <span>PLAIN LANGUAGE</span>
            </div>
            <div className="card-header-group">
              <h3 className="card-heading">Plain-Language Translator</h3>
              <p className="card-body">Translate complex legal jargon into clear, actionable executive summaries.</p>
            </div>
            <div className="visual-mockup translator-visual">
              <div className="translator-box">
                <span className="label">Legalese:</span>
                <p className="jargon">&quot;Party A shall hold harmless Party B against indemnified claims...&quot;</p>
                <div className="arrow-divider">↓</div>
                <span className="label gold">Clear Summary:</span>
                <p className="summary">Party A covers Party B&apos;s legal losses from third-party lawsuits.</p>
              </div>
            </div>
          </div>

        </div>

        {/* Bottom 3-Column Highlights Row matching inspiration image layout */}
        <div className="bento-bottom-row">
          <div className="bottom-col">
            <div className="col-icon">
              <Zap size={20} />
            </div>
            <h4 className="col-title">Lightning-Fast Research</h4>
            <p className="col-desc">
              Search, cross-reference, and synthesize over 500,000 legal rulings in under 0.4 seconds.
            </p>
          </div>

          <div className="bottom-col">
            <div className="col-icon">
              <ShieldCheck size={20} />
            </div>
            <h4 className="col-title">Grounded AI & Zero Hallucination</h4>
            <p className="col-desc">
              Every AI response is backed by pinpoint page citations to primary case law and statutory codes.
            </p>
          </div>

          <div className="bottom-col">
            <div className="col-icon">
              <Scale size={20} />
            </div>
            <h4 className="col-title">Precision Analytics</h4>
            <p className="col-desc">
              Automated liability risk matrix scoring, indemnification redlining, and compliance verification.
            </p>
          </div>
        </div>

      </div>

      <style jsx>{`
        .bento-section {
          position: relative;
          width: 100%;
          padding: 5rem 2rem;
          z-index: 10;
        }

        .bento-container {
          max-width: 1320px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 3.5rem;
        }

        .bento-header {
          text-align: center;
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 1.25rem;
        }

        .bento-main-title {
          font-family: var(--font-sans);
          font-size: clamp(2.2rem, 4vw, 3.4rem);
          font-weight: 800;
          line-height: 1.15;
          letter-spacing: -0.03em;
          color: var(--text-cream);
        }

        .title-highlight {
          background: linear-gradient(135deg, var(--accent-gold) 0%, var(--text-cream) 50%, var(--accent-gold-bright) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        .bento-subtitle {
          font-size: 1.05rem;
          color: var(--text-cream-muted);
          max-width: 650px;
          line-height: 1.6;
        }

        .bento-cta-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.75rem 1.6rem;
          background: rgba(31, 19, 21, 0.8);
          color: var(--text-cream);
          border: 1px solid var(--accent-gold);
          border-radius: 100px;
          font-size: 0.9rem;
          font-weight: 700;
          text-decoration: none;
          transition: all 0.3s ease;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        }

        .bento-cta-btn:hover {
          background: var(--accent-burgundy);
          border-color: var(--accent-gold-bright);
          box-shadow: 0 0 25px rgba(201, 162, 75, 0.3);
          transform: translateY(-2px);
        }

        /* Bento Grid Layout */
        .bento-grid {
          display: grid;
          grid-template-columns: repeat(12, 1fr);
          gap: 1.5rem;
          width: 100%;
        }

        .bento-card {
          position: relative;
          background: rgba(31, 19, 21, 0.75);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 24px;
          padding: 1.75rem;
          display: flex;
          flex-direction: column;
          justify-content: space-between;
          overflow: hidden;
          box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
          transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .bento-card:hover {
          border-color: rgba(201, 162, 75, 0.6);
          transform: translateY(-5px);
          box-shadow: 0 20px 50px rgba(107, 31, 40, 0.35);
        }

        /* Card Span Assignments */
        .card-graph {
          grid-column: span 4;
          min-height: 320px;
        }

        .card-risk {
          grid-column: span 4;
          min-height: 320px;
        }

        .card-qa-centerpiece {
          grid-column: span 4;
          min-height: 320px;
          background: linear-gradient(135deg, rgba(31, 19, 21, 0.9), rgba(107, 31, 40, 0.5));
          border-color: var(--accent-gold);
          box-shadow: 0 0 30px rgba(201, 162, 75, 0.2);
        }

        .glowing-beam {
          position: absolute;
          top: 0;
          left: 50%;
          transform: translateX(-50%);
          width: 2px;
          height: 80px;
          background: linear-gradient(180deg, var(--accent-gold), transparent);
          box-shadow: 0 0 15px var(--accent-gold);
        }

        .card-timeline {
          grid-column: span 6;
          min-height: 300px;
        }

        .card-translator {
          grid-column: span 6;
          min-height: 300px;
        }

        /* Card Elements */
        .card-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
          padding: 0.25rem 0.65rem;
          background: rgba(201, 162, 75, 0.15);
          border: 1px solid rgba(201, 162, 75, 0.3);
          border-radius: 6px;
          font-size: 0.68rem;
          font-weight: 700;
          color: var(--accent-gold);
          align-self: flex-start;
          margin-bottom: 1rem;
        }

        .card-header-group {
          margin-bottom: 1.25rem;
        }

        .card-heading {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--text-cream);
          margin-bottom: 0.4rem;
        }

        .card-body {
          font-size: 0.85rem;
          color: var(--text-cream-muted);
          line-height: 1.5;
        }

        /* Visual Mockups inside Cards */
        .visual-mockup {
          background: rgba(20, 13, 14, 0.7);
          border: 1px solid rgba(245, 237, 225, 0.08);
          border-radius: 14px;
          padding: 1rem;
          margin-top: auto;
        }

        .graph-visual {
          position: relative;
          height: 110px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .node-center {
          background: linear-gradient(135deg, var(--accent-burgundy), var(--accent-gold));
          color: #ffffff;
          padding: 0.4rem 0.7rem;
          border-radius: 8px;
          font-size: 0.72rem;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 0.3rem;
          z-index: 2;
          box-shadow: 0 0 15px rgba(201, 162, 75, 0.4);
        }

        .node-child {
          position: absolute;
          background: rgba(31, 19, 21, 0.9);
          border: 1px solid rgba(201, 162, 75, 0.3);
          color: var(--text-cream);
          padding: 0.2rem 0.5rem;
          border-radius: 6px;
          font-size: 0.65rem;
        }

        .node-1 { top: 10px; left: 10px; }
        .node-2 { top: 10px; right: 10px; }
        .node-3 { bottom: 10px; left: 60px; }

        .node-svg {
          position: absolute;
          inset: 0;
          width: 100%;
          height: 100%;
        }

        .risk-visual {
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
        }

        .risk-line {
          font-size: 0.78rem;
          color: var(--text-cream-muted);
          display: flex;
          gap: 0.4rem;
        }

        .line-num {
          color: var(--accent-gold);
          font-weight: 700;
        }

        .risk-tag-box {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          background: rgba(201, 162, 75, 0.15);
          border-left: 3px solid var(--accent-gold);
          padding: 0.4rem 0.6rem;
          font-size: 0.72rem;
          font-weight: 700;
          color: var(--text-cream);
          border-radius: 4px;
        }

        .text-gold {
          color: var(--accent-gold);
        }

        .qa-visual {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .qa-query {
          display: flex;
          align-items: flex-start;
          gap: 0.4rem;
          font-size: 0.78rem;
          font-weight: 600;
          color: var(--text-cream);
        }

        .qa-response p {
          font-size: 0.74rem;
          color: var(--text-cream-muted);
          margin-top: 0.4rem;
          line-height: 1.4;
        }

        .citation-pill {
          display: inline-flex;
          align-items: center;
          gap: 0.3rem;
          padding: 0.2rem 0.5rem;
          background: rgba(107, 31, 40, 0.5);
          border: 1px solid var(--accent-gold);
          color: var(--accent-gold);
          border-radius: 100px;
          font-size: 0.68rem;
          font-weight: 700;
        }

        .timeline-visual {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .timeline-node {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
        }

        .dot {
          width: 8px;
          height: 8px;
          border-radius: 50%;
          background: var(--text-cream-muted);
          margin-top: 0.3rem;
        }

        .dot.gold {
          background: var(--accent-gold);
          box-shadow: 0 0 8px var(--accent-gold);
        }

        .timeline-node strong {
          font-size: 0.72rem;
          color: var(--accent-gold);
        }

        .timeline-node p {
          font-size: 0.76rem;
          color: var(--text-cream-muted);
        }

        .translator-box {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
          font-size: 0.75rem;
        }

        .translator-box .label {
          font-size: 0.68rem;
          font-weight: 700;
          color: var(--text-dim);
          text-transform: uppercase;
        }

        .translator-box .label.gold {
          color: var(--accent-gold);
        }

        .jargon {
          color: var(--text-cream-muted);
          font-style: italic;
        }

        .summary {
          color: var(--text-cream);
          font-weight: 600;
        }

        .arrow-divider {
          text-align: center;
          color: var(--accent-gold);
          font-weight: 700;
        }

        /* Bottom Highlights 3-Column Layout matching reference image */
        .bento-bottom-row {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 2.5rem;
          padding-top: 2rem;
          border-top: 1px solid rgba(201, 162, 75, 0.2);
        }

        .bottom-col {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          gap: 0.6rem;
        }

        .col-icon {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          background: rgba(107, 31, 40, 0.4);
          border: 1px solid var(--accent-gold);
          color: var(--accent-gold);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 0.25rem;
        }

        .col-title {
          font-size: 1.05rem;
          font-weight: 700;
          color: var(--text-cream);
        }

        .col-desc {
          font-size: 0.85rem;
          color: var(--text-cream-muted);
          line-height: 1.5;
        }

        /* Responsive Adjustments */
        @media (max-width: 1024px) {
          .card-graph, .card-risk, .card-qa-centerpiece {
            grid-column: span 6;
          }
          .card-qa-centerpiece {
            grid-column: span 12;
          }
          .card-timeline, .card-translator {
            grid-column: span 12;
          }
          .bento-bottom-row {
            grid-template-columns: 1fr;
            gap: 2rem;
          }
        }

        @media (max-width: 640px) {
          .card-graph, .card-risk, .card-qa-centerpiece, .card-timeline, .card-translator {
            grid-column: span 12;
          }
        }
      `}</style>
    </section>
  );
};
