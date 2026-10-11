'use client';

import React from 'react';
import { Scale, ArrowUpRight } from 'lucide-react';
import { PolicyType } from './PolicyModal';

interface FooterProps {
  onRequestDemo?: () => void;
  onOpenPolicy?: (type: PolicyType) => void;
}

export const Footer: React.FC<FooterProps> = ({ onRequestDemo, onOpenPolicy }) => {
  const currentYear = 2026;

  const handleDemoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    if (onRequestDemo) onRequestDemo();
  };

  const handlePolicyClick = (e: React.MouseEvent, type: PolicyType) => {
    e.preventDefault();
    if (onOpenPolicy) onOpenPolicy(type);
  };

  return (
    <footer className="footer-root" role="contentinfo">
      <div className="footer-container">
        
        {/* Top Brand Statement Row */}
        <div className="footer-top-row">
          <div className="footer-brand-summary">
            <div className="brand-logo-inline">
              <Scale size={20} className="brand-scale-icon" aria-hidden="true" />
              <span className="brand-name">Legal<span className="brand-accent">Lens</span></span>
            </div>
            <p className="brand-tagline">
              AI-powered legal intelligence engineered for attorneys, litigation teams, and corporate legal counsel.
            </p>
          </div>

          <div className="footer-cta-box">
            <span className="cta-box-label">Ready to explore?</span>
            <button
              type="button"
              onClick={handleDemoClick}
              className="footer-demo-btn"
            >
              <span>Request a Demo</span>
              <ArrowUpRight size={14} aria-hidden="true" />
            </button>
          </div>
        </div>

        <div className="footer-divider" />

        {/* 4 Navigation Columns */}
        <div className="footer-columns-grid">
          
          {/* Column 1: Platform */}
          <div className="footer-col">
            <h3 className="footer-col-title">Platform</h3>
            <ul className="footer-link-list">
              <li><a href="#overview">Overview</a></li>
              <li><a href="#features">Features</a></li>
              <li><a href="#solutions">Solutions</a></li>
              <li><a href="#enterprise">Enterprise</a></li>
            </ul>
          </div>

          {/* Column 2: Resources */}
          <div className="footer-col">
            <h3 className="footer-col-title">Resources</h3>
            <ul className="footer-link-list">
              <li><a href="#resources">Documentation</a></li>
              <li><a href="#resources">Guides & FAQs</a></li>
              <li><a href="#demo" onClick={handleDemoClick}>Request a Demo</a></li>
              <li><a href="#demo" onClick={handleDemoClick}>Contact Us</a></li>
            </ul>
          </div>

          {/* Column 3: Company */}
          <div className="footer-col">
            <h3 className="footer-col-title">Company</h3>
            <ul className="footer-link-list">
              <li>
                <a href="#about" onClick={(e) => handlePolicyClick(e, 'about')}>
                  About LegalLens
                </a>
              </li>
              <li>
                <a href="#contact" onClick={handleDemoClick}>
                  Direct Contact
                </a>
              </li>
              <li>
                <a href="#careers" onClick={(e) => handlePolicyClick(e, 'about')}>
                  Careers <span className="footer-tag">Early Inquiries</span>
                </a>
              </li>
            </ul>
          </div>

          {/* Column 4: Legal */}
          <div className="footer-col">
            <h3 className="footer-col-title">Legal & Security</h3>
            <ul className="footer-link-list">
              <li>
                <a href="#privacy" onClick={(e) => handlePolicyClick(e, 'privacy')}>
                  Privacy Policy
                </a>
              </li>
              <li>
                <a href="#terms" onClick={(e) => handlePolicyClick(e, 'terms')}>
                  Terms of Use
                </a>
              </li>
              <li>
                <a href="#disclaimer" onClick={(e) => handlePolicyClick(e, 'disclaimer')}>
                  Legal Disclaimer
                </a>
              </li>
              <li>
                <a href="#security" onClick={(e) => handlePolicyClick(e, 'security')}>
                  Security Architecture
                </a>
              </li>
            </ul>
          </div>

        </div>

        <div className="footer-divider mt-space" />

        {/* Bottom Disclaimer and Copyright Row */}
        <div className="footer-bottom-row">
          <p className="footer-disclaimer-text">
            <strong>Legal Information Disclaimer:</strong> LegalLens provides AI-assisted legal information and document analysis. Outputs may require independent verification and professional legal judgment.
          </p>

          <div className="footer-legal-bar">
            <span className="copyright-text">
              &copy; {currentYear} LegalLens. All rights reserved.
            </span>
            <div className="bottom-links">
              <a href="#privacy" onClick={(e) => handlePolicyClick(e, 'privacy')}>Privacy</a>
              <span className="link-dot">&bull;</span>
              <a href="#terms" onClick={(e) => handlePolicyClick(e, 'terms')}>Terms</a>
              <span className="link-dot">&bull;</span>
              <a href="#disclaimer" onClick={(e) => handlePolicyClick(e, 'disclaimer')}>Disclaimer</a>
            </div>
          </div>
        </div>

      </div>

      <style jsx>{`
        .footer-root {
          position: relative;
          z-index: 20;
          width: 100%;
          background: rgba(16, 10, 12, 0.94);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-top: 1px solid rgba(201, 162, 75, 0.22);
          color: var(--text-cream);
          padding: 4.5rem 2rem 2.5rem 2rem;
          margin-top: 4rem;
        }

        .footer-container {
          max-width: 1320px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          gap: 2.5rem;
        }

        .footer-top-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 2rem;
          flex-wrap: wrap;
        }

        .footer-brand-summary {
          max-width: 520px;
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
        }

        .brand-logo-inline {
          display: flex;
          align-items: center;
          gap: 0.6rem;
        }

        .brand-scale-icon {
          color: var(--accent-gold);
        }

        .brand-name {
          font-family: var(--font-sans);
          font-size: 1.4rem;
          font-weight: 800;
          letter-spacing: -0.02em;
          color: var(--text-cream);
        }

        .brand-accent {
          color: var(--accent-gold);
        }

        .brand-tagline {
          font-size: 0.92rem;
          color: var(--text-cream-muted);
          line-height: 1.55;
        }

        .footer-cta-box {
          display: flex;
          align-items: center;
          gap: 1.25rem;
        }

        .cta-box-label {
          font-size: 0.9rem;
          font-weight: 500;
          color: var(--text-cream-muted);
        }

        .footer-demo-btn {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.65rem 1.4rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          border: 1px solid var(--accent-gold);
          border-radius: 999px;
          font-size: 0.88rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 4px 15px rgba(107, 31, 40, 0.4);
        }

        .footer-demo-btn:hover {
          background: var(--accent-burgundy-bright);
          border-color: var(--accent-gold-bright);
          transform: translateY(-1px);
        }

        .footer-divider {
          width: 100%;
          height: 1px;
          background: linear-gradient(
            90deg,
            transparent 0%,
            rgba(201, 162, 75, 0.25) 20%,
            rgba(201, 162, 75, 0.25) 80%,
            transparent 100%
          );
        }

        .mt-space {
          margin-top: 1rem;
        }

        .footer-columns-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 2.5rem;
        }

        .footer-col {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .footer-col-title {
          font-size: 0.82rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--accent-gold);
        }

        .footer-link-list {
          list-style: none;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .footer-link-list a {
          color: var(--text-cream-muted);
          text-decoration: none;
          font-size: 0.9rem;
          transition: color 0.15s ease, transform 0.15s ease;
          display: inline-flex;
          align-items: center;
          gap: 0.4rem;
        }

        .footer-link-list a:hover {
          color: var(--text-cream);
          transform: translateX(2px);
        }

        .footer-link-list a:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 3px;
        }

        .footer-tag {
          font-size: 0.65rem;
          font-weight: 600;
          padding: 0.1rem 0.4rem;
          border-radius: 4px;
          background: rgba(201, 162, 75, 0.15);
          color: var(--accent-gold);
          border: 1px solid rgba(201, 162, 75, 0.3);
        }

        .footer-bottom-row {
          display: flex;
          flex-direction: column;
          gap: 1.5rem;
        }

        .footer-disclaimer-text {
          font-size: 0.78rem;
          color: var(--text-dim);
          line-height: 1.6;
          max-width: 980px;
        }

        .footer-legal-bar {
          display: flex;
          align-items: center;
          justify-content: space-between;
          flex-wrap: wrap;
          gap: 1rem;
          padding-top: 1rem;
          border-top: 1px solid rgba(245, 237, 225, 0.06);
        }

        .copyright-text {
          font-size: 0.8rem;
          color: var(--text-dim);
        }

        .bottom-links {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .bottom-links a {
          font-size: 0.8rem;
          color: var(--text-dim);
          text-decoration: none;
          transition: color 0.15s ease;
        }

        .bottom-links a:hover {
          color: var(--accent-gold);
        }

        .link-dot {
          color: rgba(201, 162, 75, 0.3);
          font-size: 0.8rem;
        }

        @media (max-width: 900px) {
          .footer-columns-grid {
            grid-template-columns: repeat(2, 1fr);
            gap: 2rem;
          }
        }

        @media (max-width: 600px) {
          .footer-root {
            padding: 3rem 1.25rem 2rem 1.25rem;
          }
          .footer-columns-grid {
            grid-template-columns: 1fr;
            gap: 2rem;
          }
          .footer-top-row {
            flex-direction: column;
            align-items: flex-start;
          }
          .footer-legal-bar {
            flex-direction: column;
            align-items: flex-start;
          }
        }
      `}</style>
    </footer>
  );
};
