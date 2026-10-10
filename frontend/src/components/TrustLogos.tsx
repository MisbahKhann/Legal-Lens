'use client';

import React from 'react';
import { ShieldCheck, Award, Building2, Scale } from 'lucide-react';

export const TrustLogos = () => {
  return (
    <div className="trust-container">
      <p className="trust-label">TRUSTED BY LEADING LAW FIRMS & LEGAL TEAMS</p>
      <div className="trust-logos-row">
        <div className="logo-item">
          <Scale size={16} className="logo-symbol" />
          <span className="logo-name">CLIFFORD & CHANCE</span>
        </div>
        <div className="logo-item">
          <Building2 size={16} className="logo-symbol" />
          <span className="logo-name">LEXISHUB</span>
        </div>
        <div className="logo-item">
          <Award size={16} className="logo-symbol" />
          <span className="logo-name">PRUDENTIAL LAW</span>
        </div>
        <div className="logo-item">
          <ShieldCheck size={16} className="logo-symbol" />
          <span className="logo-name">MEETHUB LEGAL</span>
        </div>
      </div>

      <style jsx>{`
        .trust-container {
          margin-top: 3.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.9rem;
        }

        .trust-label {
          font-size: 0.68rem;
          font-weight: 700;
          letter-spacing: 0.14em;
          color: var(--text-dim);
          text-transform: uppercase;
        }

        .trust-logos-row {
          display: flex;
          align-items: center;
          gap: 2.2rem;
          flex-wrap: wrap;
        }

        .logo-item {
          display: flex;
          align-items: center;
          gap: 0.45rem;
          color: var(--text-dim);
          transition: all 0.3s ease;
          opacity: 0.7;
        }

        .logo-item:hover {
          color: var(--text-cream);
          opacity: 1;
        }

        .logo-symbol {
          color: var(--accent-gold);
        }

        .logo-name {
          font-size: 0.92rem;
          font-weight: 700;
          letter-spacing: -0.01em;
          color: var(--text-cream-muted);
        }

        @media (max-width: 640px) {
          .trust-logos-row {
            gap: 1.2rem;
          }
          .logo-name {
            font-size: 0.82rem;
          }
        }
      `}</style>
    </div>
  );
};
