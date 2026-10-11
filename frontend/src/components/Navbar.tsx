'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  ChevronDown, 
  Menu, 
  X, 
  ArrowRight,
  Sparkles,
  Gavel,
  FileEdit,
  GitFork,
  MessageSquareQuote,
  CheckCircle2,
  Search as SearchIcon,
  Languages,
  FileText,
  CalendarCheck,
  AlertTriangle,
  BookOpen,
  HelpCircle,
  FileCode,
  Headphones
} from 'lucide-react';
import { SearchBar } from './SearchBar';

interface NavbarProps {
  onRequestDemo?: () => void;
  activeSection?: string;
}

interface FeatureItem {
  id: string;
  name: string;
  desc: string;
  icon: React.ElementType;
  href: string;
}

const LITIGATION_FEATURES: FeatureItem[] = [
  {
    id: 'f1',
    name: 'Mock Trial Argument Simulator',
    desc: 'Practice legal arguments and explore counterarguments.',
    icon: Gavel,
    href: '#features',
  },
  {
    id: 'f4',
    name: 'Grounded Legal Q&A',
    desc: 'Ask questions grounded in relevant legal documents and sources.',
    icon: MessageSquareQuote,
    href: '#features',
  },
  {
    id: 'f9',
    name: 'Trial Reminder & Document Keeping',
    desc: 'Organize trial reminders, deadlines, and case documents.',
    icon: CalendarCheck,
    href: '#features',
  },
  {
    id: 'f3',
    name: 'Case Knowledge Graph',
    desc: 'Explore connections between cases, people, evidence, and events.',
    icon: GitFork,
    href: '#features',
  },
];

const CONTRACT_FEATURES: FeatureItem[] = [
  {
    id: 'f2',
    name: 'Draft Generator (First Pass)',
    desc: 'Generate an initial document draft for lawyer review.',
    icon: FileEdit,
    href: '#features',
  },
  {
    id: 'f8',
    name: 'Contract Summary Generator',
    desc: 'Summarize key terms, obligations, and provisions.',
    icon: FileText,
    href: '#features',
  },
  {
    id: 'f10',
    name: 'Clause Risk Flagging',
    desc: 'Highlight potentially risky or ambiguous contract clauses.',
    icon: AlertTriangle,
    href: '#features',
  },
  {
    id: 'f7',
    name: 'Plain-Language Translator',
    desc: 'Make complex legal language easier to understand.',
    icon: Languages,
    href: '#features',
  },
];

const RESEARCH_FEATURES: FeatureItem[] = [
  {
    id: 'f6',
    name: 'Case Similarity Search',
    desc: 'Find potentially relevant cases with similar facts or legal issues.',
    icon: SearchIcon,
    href: '#features',
  },
  {
    id: 'f5',
    name: 'Citation Checker',
    desc: 'Identify citations that require verification.',
    icon: CheckCircle2,
    href: '#features',
  },
];

export const Navbar: React.FC<NavbarProps> = ({ onRequestDemo, activeSection = 'overview' }) => {
  const [openDropdown, setOpenDropdown] = useState<'solutions' | 'resources' | 'features' | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileFeaturesOpen, setMobileFeaturesOpen] = useState(false);
  const [mobileSolutionsOpen, setMobileSolutionsOpen] = useState(false);
  const [mobileResourcesOpen, setMobileResourcesOpen] = useState(false);

  const navRef = useRef<HTMLElement>(null);
  const dropdownCloseTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (navRef.current && !navRef.current.contains(e.target as Node)) {
        setOpenDropdown(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Escape key listener for open menus
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpenDropdown(null);
        setMobileMenuOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Mouse hover handlers with debouncing to prevent flicker
  const handleMouseEnter = (menu: 'solutions' | 'resources' | 'features') => {
    if (dropdownCloseTimeoutRef.current) {
      clearTimeout(dropdownCloseTimeoutRef.current);
      dropdownCloseTimeoutRef.current = null;
    }
    setOpenDropdown(menu);
  };

  const handleMouseLeave = () => {
    dropdownCloseTimeoutRef.current = setTimeout(() => {
      setOpenDropdown(null);
    }, 150);
  };

  const handleItemClick = (href: string) => {
    setOpenDropdown(null);
    setMobileMenuOpen(false);
    const target = document.querySelector(href);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth' });
    }
  };

  const handleDemoClick = (e: React.MouseEvent) => {
    e.preventDefault();
    setOpenDropdown(null);
    setMobileMenuOpen(false);
    if (onRequestDemo) onRequestDemo();
  };

  return (
    <header className="navbar-container" ref={navRef}>
      <div className="navbar-pill-inner">

        {/* Desktop Navigation Items in REQUIRED ORDER:
            1. Solutions
            2. Resources
            3. Features
            4. Enterprise
            5. Pricing
            6. Search bar
            7. Request a Demo
        */}
        <nav className="desktop-nav-group" aria-label="Main Navigation">
          
          {/* 1. Solutions Dropdown */}
          <div
            className="nav-item-dropdown-wrapper"
            onMouseEnter={() => handleMouseEnter('solutions')}
            onMouseLeave={handleMouseLeave}
          >
            <button
              type="button"
              className={`nav-button-link ${activeSection === 'solutions' || openDropdown === 'solutions' ? 'active' : ''}`}
              onClick={() => setOpenDropdown(openDropdown === 'solutions' ? null : 'solutions')}
              aria-expanded={openDropdown === 'solutions'}
              aria-haspopup="true"
              id="nav-solutions-btn"
            >
              <span>Solutions</span>
              <ChevronDown size={14} className={`dropdown-chevron ${openDropdown === 'solutions' ? 'rotated' : ''}`} />
            </button>

            {openDropdown === 'solutions' && (
              <div
                className="solutions-dropdown-panel"
                role="menu"
                aria-labelledby="nav-solutions-btn"
              >
                <div className="dropdown-category-title">Core Practice Solutions</div>
                <div className="solutions-list">
                  <a
                    href="#solutions"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}
                    className="solution-menu-item"
                  >
                    <div className="item-title">Precedent & Case Research</div>
                    <p className="item-desc">Synthesize case law, statutes, and judge rulings across jurisdictions.</p>
                  </a>
                  <a
                    href="#solutions"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}
                    className="solution-menu-item"
                  >
                    <div className="item-title">Contract Analysis & Risk Flagging</div>
                    <p className="item-desc">Automated commercial redlining, liability caps, and indemnification review.</p>
                  </a>
                  <a
                    href="#solutions"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}
                    className="solution-menu-item"
                  >
                    <div className="item-title">Case Evidence & Timeline Mapping</div>
                    <p className="item-desc">Chronological discovery mapping from depositions and trial exhibits.</p>
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* 2. Resources Dropdown */}
          <div
            className="nav-item-dropdown-wrapper"
            onMouseEnter={() => handleMouseEnter('resources')}
            onMouseLeave={handleMouseLeave}
          >
            <button
              type="button"
              className={`nav-button-link ${activeSection === 'resources' || openDropdown === 'resources' ? 'active' : ''}`}
              onClick={() => setOpenDropdown(openDropdown === 'resources' ? null : 'resources')}
              aria-expanded={openDropdown === 'resources'}
              aria-haspopup="true"
              id="nav-resources-btn"
            >
              <span>Resources</span>
              <ChevronDown size={14} className={`dropdown-chevron ${openDropdown === 'resources' ? 'rotated' : ''}`} />
            </button>

            {openDropdown === 'resources' && (
              <div
                className="resources-dropdown-panel"
                role="menu"
                aria-labelledby="nav-resources-btn"
              >
                <div className="dropdown-category-title">Platform Resources</div>
                <div className="resources-list">
                  <a
                    href="#resources"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#resources'); }}
                    className="resource-menu-item"
                  >
                    <FileCode size={18} className="resource-icon" />
                    <div>
                      <div className="item-title">Platform Documentation</div>
                      <p className="item-desc">System architecture, APIs, and security specifications.</p>
                    </div>
                  </a>
                  <a
                    href="#resources"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#resources'); }}
                    className="resource-menu-item"
                  >
                    <BookOpen size={18} className="resource-icon" />
                    <div>
                      <div className="item-title">Platform Guides</div>
                      <p className="item-desc">Workflows for attorneys, litigators, and paralegals.</p>
                    </div>
                  </a>
                  <a
                    href="#resources"
                    role="menuitem"
                    onClick={(e) => { e.preventDefault(); handleItemClick('#resources'); }}
                    className="resource-menu-item"
                  >
                    <HelpCircle size={18} className="resource-icon" />
                    <div>
                      <div className="item-title">Frequently Asked Questions</div>
                      <p className="item-desc">Verification methodology, security, and onboarding.</p>
                    </div>
                  </a>
                  <a
                    href="#demo"
                    role="menuitem"
                    onClick={handleDemoClick}
                    className="resource-menu-item"
                  >
                    <Headphones size={18} className="resource-icon" />
                    <div>
                      <div className="item-title">Technical Support & Contact</div>
                      <p className="item-desc">Inquiries for deployments and firm integrations.</p>
                    </div>
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* 3. Features (10-Feature Mega-Dropdown) */}
          <div
            className="nav-item-dropdown-wrapper"
            onMouseEnter={() => handleMouseEnter('features')}
            onMouseLeave={handleMouseLeave}
          >
            <button
              type="button"
              className={`nav-button-link ${activeSection === 'features' || openDropdown === 'features' ? 'active' : ''}`}
              onClick={() => setOpenDropdown(openDropdown === 'features' ? null : 'features')}
              aria-expanded={openDropdown === 'features'}
              aria-haspopup="true"
              id="nav-features-btn"
            >
              <span>Features</span>
              <ChevronDown size={14} className={`dropdown-chevron ${openDropdown === 'features' ? 'rotated' : ''}`} />
            </button>

            {openDropdown === 'features' && (
              <div
                className="features-mega-dropdown"
                role="menu"
                aria-labelledby="nav-features-btn"
              >
                <div className="mega-dropdown-grid">
                  
                  {/* Category 1: Litigation & Trial */}
                  <div className="feature-column">
                    <h3 className="column-header">Litigation & Trial</h3>
                    <div className="feature-list">
                      {LITIGATION_FEATURES.map((feat) => {
                        const IconComp = feat.icon;
                        return (
                          <a
                            key={feat.id}
                            href={feat.href}
                            role="menuitem"
                            onClick={(e) => { e.preventDefault(); handleItemClick(feat.href); }}
                            className="feature-entry"
                          >
                            <div className="feat-icon-box">
                              <IconComp size={16} />
                            </div>
                            <div className="feat-text-box">
                              <span className="feat-name">{feat.name}</span>
                              <span className="feat-desc">{feat.desc}</span>
                            </div>
                          </a>
                        );
                      })}
                    </div>
                  </div>

                  {/* Category 2: Contracts & Drafting */}
                  <div className="feature-column">
                    <h3 className="column-header">Contracts & Drafting</h3>
                    <div className="feature-list">
                      {CONTRACT_FEATURES.map((feat) => {
                        const IconComp = feat.icon;
                        return (
                          <a
                            key={feat.id}
                            href={feat.href}
                            role="menuitem"
                            onClick={(e) => { e.preventDefault(); handleItemClick(feat.href); }}
                            className="feature-entry"
                          >
                            <div className="feat-icon-box">
                              <IconComp size={16} />
                            </div>
                            <div className="feat-text-box">
                              <span className="feat-name">{feat.name}</span>
                              <span className="feat-desc">{feat.desc}</span>
                            </div>
                          </a>
                        );
                      })}
                    </div>
                  </div>

                  {/* Category 3: Research & Verification */}
                  <div className="feature-column">
                    <h3 className="column-header">Research & Verification</h3>
                    <div className="feature-list">
                      {RESEARCH_FEATURES.map((feat) => {
                        const IconComp = feat.icon;
                        return (
                          <a
                            key={feat.id}
                            href={feat.href}
                            role="menuitem"
                            onClick={(e) => { e.preventDefault(); handleItemClick(feat.href); }}
                            className="feature-entry"
                          >
                            <div className="feat-icon-box">
                              <IconComp size={16} />
                            </div>
                            <div className="feat-text-box">
                              <span className="feat-name">{feat.name}</span>
                              <span className="feat-desc">{feat.desc}</span>
                            </div>
                          </a>
                        );
                      })}
                    </div>

                    {/* Bottom quick banner inside col 3 */}
                    <div className="feature-footer-card">
                      <span className="footer-card-tag">ALL 10 MODULES</span>
                      <p className="footer-card-text">Every capability operates with citation-grounded precision.</p>
                      <a
                        href="#features"
                        onClick={(e) => { e.preventDefault(); handleItemClick('#features'); }}
                        className="footer-card-link"
                      >
                        <span>View Interactive Showcase</span>
                        <ArrowRight size={13} />
                      </a>
                    </div>
                  </div>

                </div>
              </div>
            )}
          </div>

          {/* 4. Enterprise Link */}
          <a
            href="#enterprise"
            className={`nav-link-item ${activeSection === 'enterprise' ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); handleItemClick('#enterprise'); }}
          >
            Enterprise
          </a>

          {/* 5. Pricing Link */}
          <a
            href="#pricing"
            className={`nav-link-item ${activeSection === 'pricing' ? 'active' : ''}`}
            onClick={(e) => { e.preventDefault(); handleItemClick('#pricing'); }}
          >
            Pricing
          </a>

          {/* 6. Interactive Search Bar */}
          <div className="navbar-search-wrapper">
            <SearchBar onSelectItem={handleItemClick} />
          </div>

          {/* 7. Primary Action: Request a Demo */}
          <button
            type="button"
            onClick={handleDemoClick}
            className="navbar-cta-button"
            id="nav-request-demo-btn"
          >
            <Sparkles size={14} className="cta-icon" aria-hidden="true" />
            <span>Request a Demo</span>
          </button>

        </nav>

        {/* Mobile View Toggle */}
        <div className="mobile-toggle-group">
          <button
            type="button"
            className="mobile-hamburger-btn"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
          >
            {mobileMenuOpen ? <X size={22} /> : <Menu size={22} />}
          </button>
        </div>

      </div>

      {/* Mobile Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="mobile-drawer-panel" role="dialog" aria-modal="true" aria-label="Mobile Navigation">
          <div className="mobile-search-box">
            <SearchBar isMobile onSelectItem={handleItemClick} />
          </div>

          <div className="mobile-links-accordion">
            
            {/* 1. Solutions */}
            <div className="mobile-acc-item">
              <button
                type="button"
                className="mobile-acc-header"
                onClick={() => setMobileSolutionsOpen(!mobileSolutionsOpen)}
              >
                <span>Solutions</span>
                <ChevronDown size={16} className={mobileSolutionsOpen ? 'rotated' : ''} />
              </button>
              {mobileSolutionsOpen && (
                <div className="mobile-sublinks">
                  <a href="#solutions" onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}>
                    Precedent & Case Research
                  </a>
                  <a href="#solutions" onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}>
                    Contract Analysis & Risk Matrix
                  </a>
                  <a href="#solutions" onClick={(e) => { e.preventDefault(); handleItemClick('#solutions'); }}>
                    Evidence Timeline Engine
                  </a>
                </div>
              )}
            </div>

            {/* 2. Resources */}
            <div className="mobile-acc-item">
              <button
                type="button"
                className="mobile-acc-header"
                onClick={() => setMobileResourcesOpen(!mobileResourcesOpen)}
              >
                <span>Resources</span>
                <ChevronDown size={16} className={mobileResourcesOpen ? 'rotated' : ''} />
              </button>
              {mobileResourcesOpen && (
                <div className="mobile-sublinks">
                  <a href="#resources" onClick={(e) => { e.preventDefault(); handleItemClick('#resources'); }}>
                    Platform Documentation
                  </a>
                  <a href="#resources" onClick={(e) => { e.preventDefault(); handleItemClick('#resources'); }}>
                    Platform Guides & FAQs
                  </a>
                  <a href="#demo" onClick={handleDemoClick}>
                    Technical Support
                  </a>
                </div>
              )}
            </div>

            {/* 3. Features (10 items) */}
            <div className="mobile-acc-item">
              <button
                type="button"
                className="mobile-acc-header"
                onClick={() => setMobileFeaturesOpen(!mobileFeaturesOpen)}
              >
                <span>Features (10 Capabilities)</span>
                <ChevronDown size={16} className={mobileFeaturesOpen ? 'rotated' : ''} />
              </button>
              {mobileFeaturesOpen && (
                <div className="mobile-sublinks">
                  {[...LITIGATION_FEATURES, ...CONTRACT_FEATURES, ...RESEARCH_FEATURES].map((f) => (
                    <a
                      key={f.id}
                      href={f.href}
                      onClick={(e) => { e.preventDefault(); handleItemClick(f.href); }}
                      className="mobile-feat-link"
                    >
                      <span className="mobile-feat-name">{f.name}</span>
                      <span className="mobile-feat-desc">{f.desc}</span>
                    </a>
                  ))}
                </div>
              )}
            </div>

            {/* 4. Enterprise */}
            <a
              href="#enterprise"
              className="mobile-direct-link"
              onClick={(e) => { e.preventDefault(); handleItemClick('#enterprise'); }}
            >
              Enterprise
            </a>

            {/* 5. Pricing */}
            <a
              href="#pricing"
              className="mobile-direct-link"
              onClick={(e) => { e.preventDefault(); handleItemClick('#pricing'); }}
            >
              Pricing
            </a>

          </div>

          <div className="mobile-cta-wrapper">
            <button
              type="button"
              onClick={handleDemoClick}
              className="mobile-demo-btn"
            >
              <Sparkles size={16} className="cta-icon" />
              <span>Request a Demo</span>
            </button>
          </div>
        </div>
      )}

      <style jsx>{`
        .navbar-container {
          position: sticky;
          top: 1rem;
          width: 100%;
          padding: 0 1.5rem;
          z-index: 90;
        }

        .navbar-pill-inner {
          max-width: 1220px;
          margin: 0 auto;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0.55rem 1.25rem;
          background: rgba(22, 14, 16, 0.86);
          backdrop-filter: blur(18px);
          -webkit-backdrop-filter: blur(18px);
          border: 1px solid rgba(201, 162, 75, 0.26);
          border-radius: 999px;
          box-shadow: 
            0 10px 32px rgba(0, 0, 0, 0.5),
            0 1px 0 rgba(245, 237, 225, 0.08);
          transition: all 0.25s ease;
        }

        .navbar-pill-inner:hover {
          border-color: rgba(201, 162, 75, 0.38);
        }

        .desktop-nav-group {
          display: flex;
          align-items: center;
          gap: 1.6rem;
          width: 100%;
          justify-content: space-between;
        }

        /* Nav Buttons & Links */
        .nav-item-dropdown-wrapper {
          position: relative;
        }

        .nav-button-link,
        .nav-link-item {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          background: transparent;
          border: none;
          color: var(--text-cream);
          font-family: var(--font-sans);
          font-size: 0.94rem;
          font-weight: 500;
          cursor: pointer;
          text-decoration: none;
          padding: 0.4rem 0.2rem;
          transition: color 0.15s ease;
          position: relative;
        }

        .nav-button-link:hover,
        .nav-link-item:hover,
        .nav-button-link.active,
        .nav-link-item.active {
          color: var(--accent-gold);
        }

        .nav-button-link.active::after,
        .nav-link-item.active::after {
          content: '';
          position: absolute;
          bottom: -2px;
          left: 50%;
          transform: translateX(-50%);
          width: 14px;
          height: 2px;
          background: var(--accent-gold);
          border-radius: 2px;
        }

        .nav-button-link:focus-visible,
        .nav-link-item:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 4px;
          border-radius: 4px;
        }

        .dropdown-chevron {
          transition: transform 0.2s ease;
          color: var(--text-dim);
        }

        .dropdown-chevron.rotated {
          transform: rotate(180deg);
          color: var(--accent-gold);
        }

        /* Dropdowns */
        .solutions-dropdown-panel,
        .resources-dropdown-panel {
          position: absolute;
          top: calc(100% + 14px);
          left: -20px;
          width: 320px;
          background: #180f11;
          border: 1px solid rgba(201, 162, 75, 0.3);
          border-radius: 16px;
          box-shadow: 0 16px 40px rgba(0, 0, 0, 0.75);
          padding: 1.25rem;
          z-index: 100;
          display: flex;
          flex-direction: column;
          gap: 0.85rem;
          animation: dropFade 0.2s ease-out;
        }

        .resources-dropdown-panel {
          width: 360px;
        }

        .dropdown-category-title {
          font-size: 0.7rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--accent-gold);
          padding-bottom: 0.4rem;
          border-bottom: 1px solid rgba(201, 162, 75, 0.15);
        }

        .solutions-list,
        .resources-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .solution-menu-item {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
          padding: 0.6rem 0.75rem;
          border-radius: 8px;
          text-decoration: none;
          transition: background 0.15s ease;
        }

        .solution-menu-item:hover {
          background: rgba(107, 31, 40, 0.3);
        }

        .resource-menu-item {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.65rem 0.75rem;
          border-radius: 8px;
          text-decoration: none;
          transition: background 0.15s ease;
        }

        .resource-menu-item:hover {
          background: rgba(107, 31, 40, 0.3);
        }

        .resource-icon {
          color: var(--accent-gold);
          flex-shrink: 0;
          margin-top: 0.15rem;
        }

        .item-title {
          font-size: 0.88rem;
          font-weight: 600;
          color: var(--text-cream);
        }

        .item-desc {
          font-size: 0.76rem;
          color: var(--text-cream-muted);
          line-height: 1.4;
        }

        /* Features Mega-Dropdown */
        .features-mega-dropdown {
          position: absolute;
          top: calc(100% + 14px);
          left: 50%;
          transform: translateX(-50%);
          width: 890px;
          background: #180f11;
          border: 1px solid rgba(201, 162, 75, 0.32);
          border-radius: 20px;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
          padding: 1.75rem;
          z-index: 100;
          animation: dropFade 0.2s ease-out;
        }

        .mega-dropdown-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1.05fr;
          gap: 1.75rem;
        }

        .feature-column {
          display: flex;
          flex-direction: column;
          gap: 0.9rem;
        }

        .column-header {
          font-size: 0.72rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.12em;
          color: var(--accent-gold);
          padding-bottom: 0.5rem;
          border-bottom: 1px solid rgba(201, 162, 75, 0.18);
        }

        .feature-list {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .feature-entry {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          padding: 0.6rem 0.65rem;
          border-radius: 10px;
          text-decoration: none;
          transition: background 0.15s ease, transform 0.15s ease;
        }

        .feature-entry:hover {
          background: rgba(107, 31, 40, 0.35);
          transform: translateX(2px);
        }

        .feat-icon-box {
          color: var(--accent-gold);
          padding: 0.3rem;
          background: rgba(201, 162, 75, 0.12);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 6px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-shrink: 0;
          margin-top: 0.1rem;
        }

        .feat-text-box {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
        }

        .feat-name {
          font-size: 0.86rem;
          font-weight: 600;
          color: var(--text-cream);
          line-height: 1.3;
        }

        .feat-desc {
          font-size: 0.73rem;
          color: var(--text-cream-muted);
          line-height: 1.35;
        }

        .feature-footer-card {
          margin-top: 0.5rem;
          padding: 0.85rem;
          background: rgba(107, 31, 40, 0.2);
          border: 1px solid rgba(201, 162, 75, 0.2);
          border-radius: 10px;
          display: flex;
          flex-direction: column;
          gap: 0.35rem;
        }

        .footer-card-tag {
          font-size: 0.64rem;
          font-weight: 700;
          letter-spacing: 0.08em;
          color: var(--accent-gold);
        }

        .footer-card-text {
          font-size: 0.74rem;
          color: var(--text-cream-muted);
          line-height: 1.4;
        }

        .footer-card-link {
          display: inline-flex;
          align-items: center;
          gap: 0.35rem;
          font-size: 0.76rem;
          font-weight: 600;
          color: var(--accent-gold);
          text-decoration: none;
          margin-top: 0.2rem;
          transition: gap 0.15s ease;
        }

        .footer-card-link:hover {
          gap: 0.55rem;
        }

        /* Search & CTA */
        .navbar-search-wrapper {
          display: flex;
          align-items: center;
        }

        .navbar-cta-button {
          display: inline-flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.58rem 1.3rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          border: 1px solid var(--accent-gold);
          border-radius: 999px;
          font-size: 0.9rem;
          font-weight: 600;
          font-family: var(--font-sans);
          cursor: pointer;
          transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
          box-shadow: 0 4px 15px rgba(107, 31, 40, 0.4);
          white-space: nowrap;
        }

        .navbar-cta-button:hover {
          background: var(--accent-burgundy-bright);
          border-color: var(--accent-gold-bright);
          transform: translateY(-1px);
          box-shadow: 
            0 6px 20px rgba(107, 31, 40, 0.6),
            0 0 15px rgba(201, 162, 75, 0.3);
        }

        .navbar-cta-button:active {
          transform: translateY(0);
        }

        .navbar-cta-button:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 3px;
        }

        .cta-icon {
          color: var(--accent-gold);
        }

        /* Mobile */
        .mobile-toggle-group {
          display: none;
        }

        .mobile-hamburger-btn {
          background: transparent;
          border: none;
          color: var(--text-cream);
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0.3rem;
        }

        .mobile-drawer-panel {
          position: absolute;
          top: calc(100% + 10px);
          left: 1.5rem;
          right: 1.5rem;
          background: #180f11;
          border: 1px solid rgba(201, 162, 75, 0.35);
          border-radius: 18px;
          padding: 1.25rem;
          box-shadow: 0 20px 50px rgba(0, 0, 0, 0.85);
          display: flex;
          flex-direction: column;
          gap: 1.25rem;
          max-height: 80vh;
          overflow-y: auto;
          animation: dropFade 0.2s ease-out;
        }

        .mobile-links-accordion {
          display: flex;
          flex-direction: column;
          gap: 0.65rem;
        }

        .mobile-acc-header {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.65rem 0.5rem;
          background: transparent;
          border: none;
          color: var(--text-cream);
          font-size: 0.96rem;
          font-weight: 600;
          text-align: left;
          cursor: pointer;
          border-bottom: 1px solid rgba(245, 237, 225, 0.08);
        }

        .mobile-sublinks {
          display: flex;
          flex-direction: column;
          gap: 0.6rem;
          padding: 0.5rem 0.75rem;
          background: rgba(20, 13, 14, 0.5);
          border-radius: 8px;
        }

        .mobile-sublinks a {
          color: var(--text-cream-muted);
          font-size: 0.86rem;
          text-decoration: none;
          padding: 0.2rem 0;
        }

        .mobile-sublinks a:hover {
          color: var(--accent-gold);
        }

        .mobile-feat-link {
          display: flex;
          flex-direction: column;
          gap: 0.15rem;
          padding: 0.35rem 0 !important;
          border-bottom: 1px solid rgba(245, 237, 225, 0.05);
        }

        .mobile-feat-name {
          font-weight: 600;
          color: var(--text-cream);
          font-size: 0.84rem;
        }

        .mobile-feat-desc {
          font-size: 0.72rem;
          color: var(--text-dim);
        }

        .mobile-direct-link {
          padding: 0.65rem 0.5rem;
          color: var(--text-cream);
          font-size: 0.96rem;
          font-weight: 600;
          text-decoration: none;
          border-bottom: 1px solid rgba(245, 237, 225, 0.08);
        }

        .mobile-demo-btn {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          padding: 0.8rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          border: 1px solid var(--accent-gold);
          border-radius: 999px;
          font-size: 0.95rem;
          font-weight: 600;
          cursor: pointer;
        }

        @keyframes dropFade {
          from { opacity: 0; transform: translateY(-8px); }
          to { opacity: 1; transform: translateY(0); }
        }

        /* Breakpoints */
        @media (max-width: 1080px) {
          .desktop-nav-group {
            display: none;
          }
          .mobile-toggle-group {
            display: block;
            margin-left: auto;
          }
          .navbar-pill-inner {
            justify-content: space-between;
          }
        }
      `}</style>
    </header>
  );
};
