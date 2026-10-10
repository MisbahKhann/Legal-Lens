'use client';

import React, { useState } from 'react';
import { Scale, Sparkles, Menu, X, ArrowUpRight } from 'lucide-react';

export const Navbar = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <header className="navbar-container">
      <div className="navbar-inner">
        {/* Brand Logo */}
        <a href="#" className="navbar-logo">
          <div className="logo-icon-wrapper">
            <Scale className="logo-icon" size={20} />
            <div className="logo-glow"></div>
          </div>
          <div className="logo-text-group">
            <span className="logo-title">Legal<span className="logo-highlight">Lens</span></span>
            <span className="logo-badge-tiny">AI</span>
          </div>
        </a>

        {/* Desktop Navigation Links */}
        <nav className="navbar-links">
          <a href="#platform" className="nav-link active">Platform</a>
          <a href="#contract-ai" className="nav-link">Contract Analysis</a>
          <a href="#case-law" className="nav-link">Case Precedents</a>
          <a href="#timeline" className="nav-link">Timeline Engine</a>
          <a href="#enterprise" className="nav-link">Enterprise</a>
        </nav>

        {/* Right CTA Actions */}
        <div className="navbar-actions">
          <a href="#demo" className="btn-call-us">
            <Sparkles size={14} className="btn-icon" />
            <span>Request Demo</span>
            <ArrowUpRight size={14} className="arrow-icon" />
          </a>
          <button 
            className="mobile-menu-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-label="Toggle menu"
          >
            {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-drawer">
          <a href="#platform" onClick={() => setMobileMenuOpen(false)}>Platform</a>
          <a href="#contract-ai" onClick={() => setMobileMenuOpen(false)}>Contract Analysis</a>
          <a href="#case-law" onClick={() => setMobileMenuOpen(false)}>Case Precedents</a>
          <a href="#timeline" onClick={() => setMobileMenuOpen(false)}>Timeline Engine</a>
          <a href="#enterprise" onClick={() => setMobileMenuOpen(false)}>Enterprise</a>
          <a href="#demo" className="mobile-cta-btn" onClick={() => setMobileMenuOpen(false)}>
            Request Demo
          </a>
        </div>
      )}

      <style jsx>{`
        .navbar-container {
          width: 100%;
          padding: 1.5rem 2.5rem;
          position: relative;
          z-index: 50;
        }

        .navbar-inner {
          max-width: 1380px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.85rem 1.5rem;
          background: rgba(31, 19, 21, 0.75);
          backdrop-filter: blur(16px);
          -webkit-backdrop-filter: blur(16px);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 100px;
          box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
        }

        .navbar-logo {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          text-decoration: none;
        }

        .logo-icon-wrapper {
          position: relative;
          width: 36px;
          height: 36px;
          border-radius: 50%;
          background: linear-gradient(135deg, rgba(107, 31, 40, 0.5), rgba(201, 162, 75, 0.3));
          border: 1px solid var(--accent-gold);
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--accent-gold);
        }

        .logo-glow {
          position: absolute;
          inset: 0;
          border-radius: 50%;
          background: var(--accent-gold);
          filter: blur(8px);
          opacity: 0.25;
        }

        .logo-text-group {
          display: flex;
          align-items: center;
          gap: 0.35rem;
        }

        .logo-title {
          font-size: 1.3rem;
          font-weight: 800;
          letter-spacing: -0.02em;
          color: var(--text-cream);
        }

        .logo-highlight {
          color: var(--accent-gold);
        }

        .logo-badge-tiny {
          font-size: 0.65rem;
          font-weight: 700;
          background: rgba(201, 162, 75, 0.15);
          color: var(--accent-gold);
          border: 1px solid rgba(201, 162, 75, 0.4);
          padding: 0.1rem 0.4rem;
          border-radius: 6px;
          letter-spacing: 0.05em;
        }

        .navbar-links {
          display: flex;
          align-items: center;
          gap: 2.2rem;
        }

        .nav-link {
          font-size: 0.92rem;
          font-weight: 500;
          color: var(--text-cream-muted);
          transition: all 0.2s ease;
          position: relative;
        }

        .nav-link:hover, .nav-link.active {
          color: var(--text-cream);
        }

        .nav-link.active::after {
          content: '';
          position: absolute;
          bottom: -6px;
          left: 50%;
          transform: translateX(-50%);
          width: 18px;
          height: 2px;
          background: var(--accent-gold);
          border-radius: 2px;
          box-shadow: 0 0 8px var(--accent-gold);
        }

        .btn-call-us {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.6rem 1.3rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          border: 1px solid rgba(201, 162, 75, 0.4);
          border-radius: 100px;
          font-size: 0.88rem;
          font-weight: 600;
          transition: all 0.3s ease;
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        }

        .btn-call-us:hover {
          background: var(--accent-burgundy-bright);
          border-color: var(--accent-gold);
          color: #ffffff;
          box-shadow: 0 0 20px rgba(201, 162, 75, 0.3);
          transform: translateY(-1px);
        }

        .btn-icon {
          color: var(--accent-gold);
        }

        .arrow-icon {
          opacity: 0.8;
          transition: transform 0.2s ease;
        }

        .btn-call-us:hover .arrow-icon {
          transform: translate(2px, -2px);
          opacity: 1;
        }

        .mobile-menu-btn {
          display: none;
          background: transparent;
          border: none;
          color: var(--text-cream);
          cursor: pointer;
        }

        .mobile-drawer {
          display: flex;
          flex-direction: column;
          gap: 1.2rem;
          padding: 1.5rem;
          background: rgba(31, 19, 21, 0.95);
          backdrop-filter: blur(20px);
          border: 1px solid rgba(201, 162, 75, 0.2);
          border-radius: 16px;
          margin-top: 0.75rem;
        }

        .mobile-drawer a {
          color: var(--text-cream-muted);
          font-weight: 500;
          font-size: 1rem;
        }

        .mobile-cta-btn {
          text-align: center;
          padding: 0.75rem;
          background: var(--accent-gold);
          color: #140d0e !important;
          font-weight: 700 !important;
          border-radius: 8px;
        }

        @media (max-width: 1024px) {
          .navbar-links {
            display: none;
          }
          .mobile-menu-btn {
            display: block;
          }
          .navbar-container {
            padding: 1rem 1.25rem;
          }
        }
      `}</style>
    </header>
  );
};
