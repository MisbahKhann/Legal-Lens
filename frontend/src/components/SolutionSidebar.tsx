'use client';

import React, { useState } from 'react';
import { 
  FileText, 
  GitFork, 
  Clock, 
  Scale, 
  ArrowUpRight, 
  ArrowRight
} from 'lucide-react';

export const SolutionSidebar = () => {
  const [activeCategory, setActiveCategory] = useState(0);

  const categories = [
    { icon: FileText, label: 'Contract AI', desc: 'Automated contract redlining & clause risk extraction.' },
    { icon: GitFork, label: 'Precedents', desc: 'Multi-jurisdictional precedent citation matching.' },
    { icon: Clock, label: 'Timelines', desc: 'Chronological discovery event mapping.' },
    { icon: Scale, label: 'Statutes', desc: 'Statutory compliance & regulatory search.' },
  ];

  return (
    <aside className="solution-sidebar">
      {/* Icon Selector Pills */}
      <div className="icon-selector-row">
        {categories.map((cat, idx) => {
          const IconComp = cat.icon;
          const isActive = activeCategory === idx;
          return (
            <button
              key={idx}
              className={`icon-circle-btn ${isActive ? 'active' : ''}`}
              onClick={() => setActiveCategory(idx)}
              title={cat.label}
              aria-label={cat.label}
            >
              <IconComp size={17} />
            </button>
          );
        })}
      </div>

      {/* Featured Service Spotlight */}
      <div className="spotlight-block">
        <a href="#solutions" className="spotlight-title-link">
          <ArrowUpRight size={18} className="title-arrow" />
          <h3 className="spotlight-title">Enterprise Legal Intelligence</h3>
        </a>

        <p className="spotlight-desc">
          Empowering law firms and corporate counsel to navigate legal complexities with AI-driven case synthesis and precision analytics.
        </p>

        {/* Feature List Items with Arrow */}
        <ul className="feature-arrow-list">
          <li className="arrow-item">
            <ArrowRight size={14} className="list-arrow" />
            <span>Contract Risk Analysis & Redlining</span>
          </li>
          <li className="arrow-item">
            <ArrowRight size={14} className="list-arrow" />
            <span>Multi-Jurisdiction Precedent Search</span>
          </li>
          <li className="arrow-item">
            <ArrowRight size={14} className="list-arrow" />
            <span>Chronological Evidence Timeline</span>
          </li>
          <li className="arrow-item">
            <ArrowRight size={14} className="list-arrow" />
            <span>Statutory Compliance Intelligence</span>
          </li>
        </ul>
      </div>

      {/* Key Metrics Stats (Bottom Right) */}
      <div className="metrics-block">
        <div className="metric-item">
          <span className="metric-label">cases processed</span>
          <span className="metric-value">10K+</span>
        </div>
        <div className="metric-item">
          <span className="metric-label">accuracy rate</span>
          <span className="metric-value">98.6%</span>
        </div>
      </div>

      <style jsx>{`
        .solution-sidebar {
          display: flex;
          flex-direction: column;
          gap: 2rem;
          height: 100%;
          justify-content: space-between;
          padding-top: 0.5rem;
        }

        .icon-selector-row {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .icon-circle-btn {
          width: 44px;
          height: 44px;
          border-radius: 50%;
          background: rgba(31, 19, 21, 0.6);
          border: 1px solid rgba(201, 162, 75, 0.25);
          color: var(--text-cream-muted);
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .icon-circle-btn:hover {
          background: rgba(107, 31, 40, 0.4);
          border-color: var(--accent-gold);
          color: var(--accent-gold);
          transform: translateY(-2px);
          box-shadow: 0 4px 15px rgba(201, 162, 75, 0.2);
        }

        .icon-circle-btn.active {
          background: linear-gradient(135deg, var(--accent-burgundy), var(--accent-gold));
          border-color: var(--accent-gold-bright);
          color: #ffffff;
          box-shadow: 0 0 20px rgba(201, 162, 75, 0.3);
        }

        .spotlight-block {
          display: flex;
          flex-direction: column;
          gap: 1.1rem;
        }

        .spotlight-title-link {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          color: var(--text-cream);
          text-decoration: none;
          transition: color 0.2s ease;
        }

        .spotlight-title-link:hover {
          color: var(--accent-gold);
        }

        .spotlight-title-link:hover .title-arrow {
          transform: translate(2px, -2px);
          color: var(--accent-gold);
        }

        .title-arrow {
          color: var(--accent-gold);
          transition: transform 0.2s ease;
        }

        .spotlight-title {
          font-size: 1.15rem;
          font-weight: 700;
          letter-spacing: -0.01em;
          color: inherit;
        }

        .spotlight-desc {
          font-size: 0.88rem;
          line-height: 1.6;
          color: var(--text-cream-muted);
        }

        .feature-arrow-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
          margin-top: 0.25rem;
        }

        .arrow-item {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          font-size: 0.84rem;
          font-weight: 500;
          color: var(--text-cream-muted);
          transition: all 0.2s ease;
          cursor: pointer;
        }

        .arrow-item:hover {
          color: var(--text-cream);
          transform: translateX(4px);
        }

        .list-arrow {
          color: var(--accent-gold);
          opacity: 0.85;
          transition: transform 0.2s ease;
        }

        .arrow-item:hover .list-arrow {
          transform: translateX(3px);
          opacity: 1;
        }

        .metrics-block {
          display: flex;
          align-items: flex-end;
          gap: 2.5rem;
          padding-top: 1rem;
          border-top: 1px solid rgba(201, 162, 75, 0.2);
        }

        .metric-item {
          display: flex;
          flex-direction: column;
          gap: 0.25rem;
        }

        .metric-label {
          font-size: 0.72rem;
          font-weight: 600;
          color: var(--text-dim);
          text-transform: lowercase;
          letter-spacing: 0.02em;
        }

        .metric-value {
          font-size: 2.2rem;
          font-weight: 800;
          letter-spacing: -0.03em;
          color: var(--text-cream);
          line-height: 1;
          background: linear-gradient(180deg, #f5ede1 0%, #c9a24b 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }

        @media (max-width: 1024px) {
          .metrics-block {
            gap: 1.5rem;
          }
          .metric-value {
            font-size: 1.8rem;
          }
        }
      `}</style>
    </aside>
  );
};
