'use client';

import React from 'react';
import { 
  Gavel, 
  FileEdit, 
  GitFork, 
  MessageSquareQuote, 
  CheckCircle2, 
  Search, 
  Languages, 
  FileText, 
  CalendarCheck, 
  AlertTriangle 
} from 'lucide-react';

interface FeatureItem {
  id: string;
  name: string;
  desc: string;
  icon: React.ElementType;
}

const row1Features: FeatureItem[] = [
  {
    id: 'f1',
    name: 'Mock Trial Argument Simulator',
    desc: 'Practice arguments, explore counterarguments, and prepare for courtroom challenges.',
    icon: Gavel,
  },
  {
    id: 'f2',
    name: 'Draft Generator (First Pass)',
    desc: 'Generate an initial draft of a legal document for lawyer review and refinement.',
    icon: FileEdit,
  },
  {
    id: 'f3',
    name: 'Case Knowledge Graph',
    desc: 'Explore connections between cases, people, evidence, legal issues, and events.',
    icon: GitFork,
  },
  {
    id: 'f4',
    name: 'Grounded Legal Q&A',
    desc: 'Ask legal questions and receive answers grounded in relevant legal sources and documents.',
    icon: MessageSquareQuote,
  },
  {
    id: 'f5',
    name: 'Citation Checker',
    desc: 'Check legal citations and identify references that may need verification.',
    icon: CheckCircle2,
  },
];

const row2Features: FeatureItem[] = [
  {
    id: 'f6',
    name: 'Case Similarity Search',
    desc: 'Discover potentially relevant cases based on similarities in facts, legal issues, or reasoning.',
    icon: Search,
  },
  {
    id: 'f7',
    name: 'Plain-Language Translator',
    desc: 'Turn complex legal language into clearer, more accessible explanations.',
    icon: Languages,
  },
  {
    id: 'f8',
    name: 'Contract Summary Generator',
    desc: 'Summarize key terms, obligations, parties, and important provisions in a contract.',
    icon: FileText,
  },
  {
    id: 'f9',
    name: 'Trial Reminder & Document Keeping',
    desc: 'Organize trial-related reminders, deadlines, and case documents.',
    icon: CalendarCheck,
  },
  {
    id: 'f10',
    name: 'Clause Risk Flagging',
    desc: 'Highlight potentially risky, unusual, or ambiguous contract clauses for professional review.',
    icon: AlertTriangle,
  },
];

export const FeatureCarousels = () => {
  return (
    <section className="carousels-section">
      <div className="section-header">
        <div className="header-badge">
          <span className="badge-dot"></span>
          <span>AI-POWERED CAPABILITIES</span>
        </div>
        <h2 className="section-title">
          Comprehensive Legal Intelligence Platform
        </h2>
        <p className="section-subtitle">
          Intelligent tools engineered specifically for attorneys, litigation teams, and corporate legal counsel.
        </p>
      </div>

      <div className="carousels-container">
        {/* ROW 1: Right to Left infinite scroll */}
        <div className="carousel-track-wrapper mask-left-right">
          <div className="carousel-track track-move-left">
            {/* Double array for seamless loop */}
            {[...row1Features, ...row1Features].map((item, idx) => {
              const IconComp = item.icon;
              return (
                <div key={`r1-${idx}`} className="feature-card">
                  <div className="card-icon-box">
                    <IconComp size={20} className="card-icon" />
                  </div>
                  <div className="card-content">
                    <h3 className="card-title">{item.name}</h3>
                    <p className="card-desc">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ROW 2: Left to Right infinite scroll */}
        <div className="carousel-track-wrapper mask-left-right mt-4">
          <div className="carousel-track track-move-right">
            {/* Double array for seamless loop */}
            {[...row2Features, ...row2Features].map((item, idx) => {
              const IconComp = item.icon;
              return (
                <div key={`r2-${idx}`} className="feature-card">
                  <div className="card-icon-box">
                    <IconComp size={20} className="card-icon" />
                  </div>
                  <div className="card-content">
                    <h3 className="card-title">{item.name}</h3>
                    <p className="card-desc">{item.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <style jsx>{`
        .carousels-section {
          position: relative;
          width: 100%;
          padding: 5rem 0 3rem 0;
          z-index: 10;
        }

        .section-header {
          text-align: center;
          max-width: 800px;
          margin: 0 auto 3rem auto;
          padding: 0 1.5rem;
        }

        .header-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.35rem 0.9rem;
          background: rgba(31, 19, 21, 0.8);
          border: 1px solid rgba(201, 162, 75, 0.3);
          border-radius: 100px;
          font-size: 0.72rem;
          font-weight: 700;
          letter-spacing: 0.12em;
          color: var(--accent-gold);
          margin-bottom: 1rem;
        }

        .badge-dot {
          width: 6px;
          height: 6px;
          background: var(--accent-gold);
          border-radius: 50%;
          box-shadow: 0 0 8px var(--accent-gold);
        }

        .section-title {
          font-size: clamp(2rem, 3.5vw, 3rem);
          font-weight: 800;
          letter-spacing: -0.02em;
          color: var(--text-cream);
          margin-bottom: 0.75rem;
        }

        .section-subtitle {
          font-size: 1.05rem;
          color: var(--text-cream-muted);
          line-height: 1.6;
        }

        .carousels-container {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
          width: 100%;
          overflow: hidden;
        }

        .carousel-track-wrapper {
          position: relative;
          width: 100%;
          overflow: hidden;
        }

        .mask-left-right {
          mask-image: linear-gradient(
            to right, 
            transparent 0%, 
            black 8%, 
            black 92%, 
            transparent 100%
          );
          -webkit-mask-image: linear-gradient(
            to right, 
            transparent 0%, 
            black 8%, 
            black 92%, 
            transparent 100%
          );
        }

        .carousel-track {
          display: flex;
          align-items: center;
          gap: 1.5rem;
          width: max-content;
        }

        .track-move-left {
          animation: scrollLeft 38s linear infinite;
        }

        .track-move-right {
          animation: scrollRight 38s linear infinite;
        }

        .carousel-track-wrapper:hover .carousel-track {
          animation-play-state: paused;
        }

        @keyframes scrollLeft {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }

        @keyframes scrollRight {
          0% {
            transform: translateX(-50%);
          }
          100% {
            transform: translateX(0);
          }
        }

        .feature-card {
          flex: 0 0 340px;
          width: 340px;
          display: flex;
          align-items: flex-start;
          gap: 1rem;
          padding: 1.25rem;
          background: rgba(31, 19, 21, 0.75);
          backdrop-filter: blur(14px);
          -webkit-backdrop-filter: blur(14px);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 16px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .feature-card:hover {
          border-color: rgba(201, 162, 75, 0.6);
          background: rgba(107, 31, 40, 0.45);
          transform: translateY(-4px);
          box-shadow: 0 15px 35px rgba(107, 31, 40, 0.3);
        }

        .card-icon-box {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          background: linear-gradient(135deg, rgba(107, 31, 40, 0.6), rgba(201, 162, 75, 0.3));
          border: 1px solid var(--accent-gold);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-gold);
          flex-shrink: 0;
        }

        .card-content {
          display: flex;
          flex-direction: column;
          gap: 0.3rem;
        }

        .card-title {
          font-size: 0.95rem;
          font-weight: 700;
          color: var(--text-cream);
          letter-spacing: -0.01em;
          line-height: 1.3;
        }

        .card-desc {
          font-size: 0.78rem;
          color: var(--text-cream-muted);
          line-height: 1.45;
        }

        .mt-4 {
          margin-top: 0.25rem;
        }
      `}</style>
    </section>
  );
};
