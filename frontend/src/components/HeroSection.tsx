'use client';

import React from 'react';
import { OversizedBrandBackground } from './OversizedBrandBackground';
import { ArrowRight, Sparkles, Compass } from 'lucide-react';

interface HeroSectionProps {
  onRequestDemo?: () => void;
}

export const HeroSection: React.FC<HeroSectionProps> = ({ onRequestDemo }) => {
  const handleDemoClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    if (onRequestDemo) {
      e.preventDefault();
      onRequestDemo();
    }
  };

  return (
    <section className="hero-section-root" id="overview">
      <div className="hero-bg-container">
        {/* Subtle Brand Watermark behind foreground */}
        <OversizedBrandBackground />

        {/* Localized contrast vignette for crisp text legibility over architecture */}
        <div className="hero-contrast-vignette" aria-hidden="true" />

        {/* Core Hero Content */}
        <div className="hero-canvas-frame">
          <div className="hero-content-stack">
            {/* Main Headline */}
            <h1 className="hero-headline">
              Legal intelligence,<br />
              <span className="headline-emphasis">clearly connected.</span>
            </h1>

            {/* Supporting Description */}
            <p className="hero-description">
              Research cases, understand contracts, and organize legal evidence in one intelligent workspace.
            </p>

            {/* Restrained CTAs */}
            <div className="hero-cta-group">
              <a
                href="#demo"
                onClick={handleDemoClick}
                className="btn-primary-cta"
                id="hero-request-demo-btn"
              >
                <Sparkles size={16} className="cta-sparkle" aria-hidden="true" />
                <span>Request a Demo</span>
                <ArrowRight size={16} className="cta-arrow" aria-hidden="true" />
              </a>

              <a
                href="#features"
                className="btn-secondary-cta"
                id="hero-explore-features-btn"
              >
                <Compass size={16} className="secondary-icon" aria-hidden="true" />
                <span>Explore Features</span>
              </a>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .hero-section-root {
          position: relative;
          width: 100%;
          min-height: calc(100vh - 80px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 2rem 1.5rem 6rem 1.5rem;
        }

        .hero-bg-container {
          position: relative;
          width: 100%;
          max-width: 1380px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        /* Localized subtle dark vignette behind text to guarantee legibility */
        .hero-contrast-vignette {
          position: absolute;
          inset: -15% -20%;
          background: radial-gradient(
            ellipse 65% 55% at 50% 50%,
            rgba(20, 13, 14, 0.78) 0%,
            rgba(20, 13, 14, 0.45) 55%,
            transparent 85%
          );
          pointer-events: none;
          z-index: 2;
        }

        .hero-canvas-frame {
          position: relative;
          z-index: 10;
          width: 100%;
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 3rem 1rem 2rem 1rem;
        }

        .hero-content-stack {
          max-width: 860px;
          margin: 0 auto;
          display: flex;
          flex-direction: column;
          align-items: center;
        }

        .hero-headline {
          font-family: var(--font-sans);
          font-size: clamp(2.75rem, 5.8vw, 4.85rem);
          font-weight: 800;
          line-height: 1.1;
          letter-spacing: -0.035em;
          color: var(--text-cream);
          margin-bottom: 1.5rem;
          text-wrap: balance;
          text-shadow: 0 4px 24px rgba(0, 0, 0, 0.6);
        }

        .headline-emphasis {
          color: var(--accent-gold);
          display: inline-block;
          font-weight: 800;
        }

        .hero-description {
          font-size: clamp(1.1rem, 2vw, 1.3rem);
          line-height: 1.6;
          color: var(--text-cream-muted);
          max-width: 640px;
          margin: 0 auto 2.5rem auto;
          font-weight: 400;
          text-wrap: balance;
          text-shadow: 0 2px 16px rgba(0, 0, 0, 0.7);
        }

        .hero-cta-group {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 1.25rem;
          flex-wrap: wrap;
        }

        .btn-primary-cta {
          display: inline-flex;
          align-items: center;
          gap: 0.65rem;
          padding: 0.95rem 2rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          font-size: 0.98rem;
          font-weight: 600;
          border-radius: 999px;
          border: 1px solid var(--accent-gold);
          text-decoration: none;
          box-shadow: 
            0 8px 24px rgba(107, 31, 40, 0.45),
            0 2px 8px rgba(0, 0, 0, 0.4);
          transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
          cursor: pointer;
        }

        .btn-primary-cta:hover {
          background: var(--accent-burgundy-bright);
          border-color: var(--accent-gold-bright);
          color: #ffffff;
          transform: translateY(-2px);
          box-shadow: 
            0 12px 30px rgba(107, 31, 40, 0.6),
            0 0 20px rgba(201, 162, 75, 0.3);
        }

        .btn-primary-cta:active {
          transform: translateY(0);
        }

        .btn-primary-cta:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 3px;
        }

        .cta-sparkle {
          color: var(--accent-gold);
        }

        .cta-arrow {
          transition: transform 0.2s ease;
        }

        .btn-primary-cta:hover .cta-arrow {
          transform: translateX(4px);
        }

        .btn-secondary-cta {
          display: inline-flex;
          align-items: center;
          gap: 0.55rem;
          padding: 0.95rem 1.85rem;
          background: rgba(20, 13, 14, 0.65);
          color: var(--text-cream);
          font-size: 0.98rem;
          font-weight: 500;
          border-radius: 999px;
          border: 1px solid rgba(201, 162, 75, 0.3);
          text-decoration: none;
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          transition: all 0.25s ease;
        }

        .btn-secondary-cta:hover {
          background: rgba(31, 19, 21, 0.9);
          border-color: var(--accent-gold);
          color: var(--accent-gold);
          transform: translateY(-2px);
        }

        .btn-secondary-cta:active {
          transform: translateY(0);
        }

        .btn-secondary-cta:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 3px;
        }

        .secondary-icon {
          color: var(--accent-gold);
        }

        @media (max-width: 768px) {
          .hero-section-root {
            padding: 1.5rem 1rem 4rem 1rem;
            min-height: auto;
          }
          .hero-headline {
            font-size: 2.6rem;
            margin-bottom: 1.25rem;
          }
          .hero-description {
            font-size: 1.05rem;
            margin-bottom: 2rem;
          }
          .hero-cta-group {
            width: 100%;
            flex-direction: column;
            gap: 0.85rem;
          }
          .btn-primary-cta, .btn-secondary-cta {
            width: 100%;
            justify-content: center;
          }
        }

        @media (prefers-reduced-motion: reduce) {
          .btn-primary-cta, .btn-secondary-cta, .cta-arrow {
            transition: none;
            transform: none !important;
          }
        }
      `}</style>
    </section>
  );
};
