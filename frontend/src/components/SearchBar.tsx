'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Search, X, ArrowRight, CornerDownLeft } from 'lucide-react';

export interface SearchItem {
  id: string;
  title: string;
  category: 'Feature' | 'Solution' | 'Section' | 'Resource';
  description: string;
  href: string;
}

export const SEARCH_INDEX: SearchItem[] = [
  // 10 Features
  {
    id: 'f1',
    title: 'Mock Trial Argument Simulator',
    category: 'Feature',
    description: 'Practice legal arguments and explore counterarguments.',
    href: '#features',
  },
  {
    id: 'f2',
    title: 'Draft Generator (First Pass)',
    category: 'Feature',
    description: 'Generate an initial document draft for lawyer review.',
    href: '#features',
  },
  {
    id: 'f3',
    title: 'Case Knowledge Graph',
    category: 'Feature',
    description: 'Explore connections between cases, people, evidence, and events.',
    href: '#features',
  },
  {
    id: 'f4',
    title: 'Grounded Legal Q&A',
    category: 'Feature',
    description: 'Ask questions grounded in relevant legal documents and sources.',
    href: '#features',
  },
  {
    id: 'f5',
    title: 'Citation Checker',
    category: 'Feature',
    description: 'Identify citations that require verification.',
    href: '#features',
  },
  {
    id: 'f6',
    title: 'Case Similarity Search',
    category: 'Feature',
    description: 'Find potentially relevant cases with similar facts or legal issues.',
    href: '#features',
  },
  {
    id: 'f7',
    title: 'Plain-Language Translator',
    category: 'Feature',
    description: 'Make complex legal language easier to understand.',
    href: '#features',
  },
  {
    id: 'f8',
    title: 'Contract Summary Generator',
    category: 'Feature',
    description: 'Summarize key terms, obligations, and provisions.',
    href: '#features',
  },
  {
    id: 'f9',
    title: 'Trial Reminder & Document Keeping',
    category: 'Feature',
    description: 'Organize trial reminders, deadlines, and case documents.',
    href: '#features',
  },
  {
    id: 'f10',
    title: 'Clause Risk Flagging',
    category: 'Feature',
    description: 'Highlight potentially risky or ambiguous contract clauses.',
    href: '#features',
  },
  // Solutions & Core Sections
  {
    id: 's1',
    title: 'Solutions Overview',
    category: 'Solution',
    description: 'Explore legal intelligence use cases for law firms and corporate legal teams.',
    href: '#solutions',
  },
  {
    id: 's2',
    title: 'Contract Analysis & Risk Matrix',
    category: 'Solution',
    description: 'Automated contract redlining, clause comparison, and liability verification.',
    href: '#solutions',
  },
  {
    id: 's3',
    title: 'Case Precedent Discovery',
    category: 'Solution',
    description: 'Multi-jurisdictional precedent citation matching and cross-referencing.',
    href: '#solutions',
  },
  {
    id: 's4',
    title: 'Evidence Timeline Engine',
    category: 'Solution',
    description: 'Chronological discovery event mapping and deposition transcript review.',
    href: '#solutions',
  },
  {
    id: 'sec1',
    title: 'Enterprise Platform',
    category: 'Section',
    description: 'Security, deployment options, and enterprise licensing for law firms.',
    href: '#enterprise',
  },
  {
    id: 'sec2',
    title: 'Pricing & Licensing',
    category: 'Section',
    description: 'Tiered firm licensing and custom deployment inquiries.',
    href: '#pricing',
  },
  {
    id: 'r1',
    title: 'Platform Documentation',
    category: 'Resource',
    description: 'Technical architecture, integrations, and user documentation guides.',
    href: '#resources',
  },
  {
    id: 'r2',
    title: 'Platform FAQs',
    category: 'Resource',
    description: 'Common questions regarding LegalLens workflow integration and accuracy.',
    href: '#resources',
  },
];

interface SearchBarProps {
  onSelectItem?: (href: string) => void;
  isMobile?: boolean;
}

export const SearchBar: React.FC<SearchBarProps> = ({ onSelectItem, isMobile = false }) => {
  const [query, setQuery] = useState('');
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter items based on query
  const filteredResults = query.trim() === ''
    ? []
    : SEARCH_INDEX.filter((item) => {
        const q = query.toLowerCase();
        return (
          item.title.toLowerCase().includes(q) ||
          item.description.toLowerCase().includes(q) ||
          item.category.toLowerCase().includes(q)
        );
      });

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (href: string) => {
    setIsOpen(false);
    setQuery('');
    if (onSelectItem) {
      onSelectItem(href);
    } else {
      const el = document.querySelector(href);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth' });
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setIsOpen(false);
      inputRef.current?.blur();
      return;
    }

    if (!isOpen || filteredResults.length === 0) return;

    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev + 1) % filteredResults.length);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex((prev) => (prev - 1 + filteredResults.length) % filteredResults.length);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredResults[selectedIndex]) {
        handleSelect(filteredResults[selectedIndex].href);
      }
    }
  };

  return (
    <div
      ref={containerRef}
      className={`search-container ${isMobile ? 'mobile-search' : 'desktop-search'}`}
      role="search"
    >
      <div className={`search-input-wrapper ${isOpen && query ? 'focused-open' : ''}`}>
        <Search size={15} className="search-icon" aria-hidden="true" />
        <input
          ref={inputRef}
          type="text"
          role="combobox"
          aria-expanded={isOpen && query.trim() !== ''}
          aria-autocomplete="list"
          aria-controls="search-results-dropdown"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder="Search LegalLens..."
          aria-label="Search LegalLens website features and sections"
          className="search-input"
          autoComplete="off"
          spellCheck="false"
        />
        {query && (
          <button
            type="button"
            onClick={() => {
              setQuery('');
              inputRef.current?.focus();
            }}
            className="search-clear-btn"
            aria-label="Clear search input"
          >
            <X size={14} />
          </button>
        )}
      </div>

      {/* Results Dropdown Panel */}
      {isOpen && query.trim() !== '' && (
        <div
          id="search-results-dropdown"
          className="search-dropdown"
          role="listbox"
          aria-label="Search results"
        >
          {/* Transparent scope notice */}
          <div className="search-scope-notice">
            <span>Website Navigation Search</span>
            <span className="notice-sub">Features & Sections</span>
          </div>

          {filteredResults.length > 0 ? (
            <div className="results-list">
              {filteredResults.map((item, idx) => (
                <div
                  key={item.id}
                  role="option"
                  aria-selected={idx === selectedIndex}
                  onClick={() => handleSelect(item.href)}
                  onMouseEnter={() => setSelectedIndex(idx)}
                  className={`search-result-item ${idx === selectedIndex ? 'active' : ''}`}
                >
                  <div className="result-text-group">
                    <div className="result-title-row">
                      <span className="result-title">{item.title}</span>
                      <span className="result-category-tag">{item.category}</span>
                    </div>
                    <p className="result-desc">{item.description}</p>
                  </div>
                  <ArrowRight size={14} className="result-arrow" aria-hidden="true" />
                </div>
              ))}
            </div>
          ) : (
            <div className="no-results-box">
              <p className="no-results-title">No matching features or sections</p>
              <p className="no-results-hint">
                Search feature names like &ldquo;Mock Trial&rdquo;, &ldquo;Contract&rdquo;, &ldquo;Citation&rdquo;, or sections like &ldquo;Pricing&rdquo;.
              </p>
            </div>
          )}

          <div className="search-keyboard-footer">
            <span className="kbd-item"><CornerDownLeft size={10} /> to navigate</span>
            <span className="kbd-item">ESC to close</span>
          </div>
        </div>
      )}

      <style jsx>{`
        .search-container {
          position: relative;
        }

        .desktop-search {
          width: 210px;
          transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .desktop-search:focus-within {
          width: 250px;
        }

        .mobile-search {
          width: 100%;
        }

        .search-input-wrapper {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.45rem 0.85rem;
          background: rgba(20, 13, 14, 0.85);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 999px;
          transition: all 0.2s ease;
        }

        .search-input-wrapper:hover {
          border-color: rgba(201, 162, 75, 0.45);
          background: rgba(31, 19, 21, 0.9);
        }

        .search-input-wrapper:focus-within,
        .focused-open {
          border-color: var(--accent-gold);
          box-shadow: 0 0 0 2px rgba(201, 162, 75, 0.2), 0 4px 12px rgba(0, 0, 0, 0.4);
          background: rgba(20, 13, 14, 0.95);
        }

        .search-icon {
          color: var(--accent-gold);
          flex-shrink: 0;
          opacity: 0.9;
        }

        .search-input {
          width: 100%;
          background: transparent;
          border: none;
          color: var(--text-cream);
          font-size: 0.88rem;
          font-family: var(--font-sans);
          outline: none;
        }

        .search-input::placeholder {
          color: var(--text-dim);
          font-size: 0.84rem;
        }

        .search-clear-btn {
          background: transparent;
          border: none;
          color: var(--text-dim);
          cursor: pointer;
          display: flex;
          align-items: center;
          padding: 0;
          transition: color 0.15s ease;
        }

        .search-clear-btn:hover {
          color: var(--text-cream);
        }

        /* Dropdown */
        .search-dropdown {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          width: 360px;
          max-height: 440px;
          overflow-y: auto;
          background: #180f11;
          border: 1px solid rgba(201, 162, 75, 0.3);
          border-radius: 14px;
          box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
          z-index: 120;
          display: flex;
          flex-direction: column;
        }

        .mobile-search .search-dropdown {
          width: 100%;
          left: 0;
          right: auto;
        }

        .search-scope-notice {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.6rem 0.9rem;
          background: rgba(107, 31, 40, 0.25);
          border-bottom: 1px solid rgba(201, 162, 75, 0.15);
          font-size: 0.68rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.08em;
          color: var(--accent-gold);
        }

        .notice-sub {
          color: var(--text-dim);
          font-weight: 500;
          text-transform: none;
          letter-spacing: normal;
        }

        .results-list {
          display: flex;
          flex-direction: column;
          padding: 0.35rem 0;
        }

        .search-result-item {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.65rem 0.9rem;
          cursor: pointer;
          transition: background 0.15s ease;
          border-left: 2px solid transparent;
        }

        .search-result-item:hover,
        .search-result-item.active {
          background: rgba(107, 31, 40, 0.3);
          border-left-color: var(--accent-gold);
        }

        .result-text-group {
          display: flex;
          flex-direction: column;
          gap: 0.2rem;
          max-width: 90%;
        }

        .result-title-row {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .result-title {
          font-size: 0.86rem;
          font-weight: 600;
          color: var(--text-cream);
        }

        .result-category-tag {
          font-size: 0.64rem;
          font-weight: 700;
          text-transform: uppercase;
          padding: 0.1rem 0.4rem;
          border-radius: 4px;
          background: rgba(201, 162, 75, 0.15);
          color: var(--accent-gold);
        }

        .result-desc {
          font-size: 0.74rem;
          color: var(--text-cream-muted);
          line-height: 1.35;
        }

        .result-arrow {
          color: var(--accent-gold);
          opacity: 0;
          transition: all 0.15s ease;
          flex-shrink: 0;
        }

        .search-result-item.active .result-arrow {
          opacity: 1;
          transform: translateX(2px);
        }

        .no-results-box {
          padding: 1.5rem 1rem;
          text-align: center;
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .no-results-title {
          font-size: 0.88rem;
          font-weight: 600;
          color: var(--text-cream);
        }

        .no-results-hint {
          font-size: 0.76rem;
          color: var(--text-dim);
          line-height: 1.45;
        }

        .search-keyboard-footer {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 0.8rem;
          padding: 0.45rem 0.9rem;
          background: rgba(20, 13, 14, 0.9);
          border-top: 1px solid rgba(245, 237, 225, 0.08);
          font-size: 0.68rem;
          color: var(--text-dim);
        }

        .kbd-item {
          display: flex;
          align-items: center;
          gap: 0.25rem;
        }
      `}</style>
    </div>
  );
};
