'use client';

import React from 'react';
import { Sparkles } from 'lucide-react';

export const HeroBadge = () => {
  return (
    <div className="badge-wrapper">
      <div className="badge-pill">
        <span className="pulse-dot">
          <span className="pulse-ring"></span>
        </span>
        <Sparkles size={13} className="badge-icon" />
        <span className="badge-text">AI-POWERED LEGAL INTELLIGENCE</span>
      </div>

      <style jsx>{`
        .badge-wrapper {
          display: inline-flex;
          align-items: center;
          margin-bottom: 1.25rem;
        }

        .badge-pill {
          display: flex;
          align-items: center;
          gap: 0.6rem;
          padding: 0.45rem 1.1rem;
          background: rgba(31, 19, 21, 0.7);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          border: 1px solid rgba(201, 162, 75, 0.35);
          border-radius: 100px;
          box-shadow: 0 4px 20px rgba(107, 31, 40, 0.2), inset 0 1px 0 rgba(245, 237, 225, 0.1);
          transition: all 0.3s ease;
        }

        .badge-pill:hover {
          border-color: rgba(201, 162, 75, 0.6);
          box-shadow: 0 0 25px rgba(201, 162, 75, 0.25), inset 0 1px 0 rgba(245, 237, 225, 0.2);
          transform: translateY(-1px);
        }

        .pulse-dot {
          position: relative;
          width: 7px;
          height: 7px;
          background-color: var(--accent-gold);
          border-radius: 50%;
          display: inline-block;
        }

        .pulse-ring {
          position: absolute;
          inset: -3px;
          border-radius: 50%;
          border: 1px solid var(--accent-gold);
          animation: ping 2s cubic-bezier(0, 0, 0.2, 1) infinite;
        }

        @keyframes ping {
          75%, 100% {
            transform: scale(2.2);
            opacity: 0;
          }
        }

        .badge-icon {
          color: var(--accent-gold);
        }

        .badge-text {
          font-size: 0.73rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          text-transform: uppercase;
          color: var(--text-cream);
          background: linear-gradient(90deg, #f5ede1 0%, #d8c7b5 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
        }
      `}</style>
    </div>
  );
};
