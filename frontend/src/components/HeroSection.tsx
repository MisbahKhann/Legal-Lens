'use client';

import React from 'react';
import { Navbar } from './Navbar';
import { OversizedBrandBackground } from './OversizedBrandBackground';
import { HeroBadge } from './HeroBadge';
import { SolutionSidebar } from './SolutionSidebar';
import { TrustLogos } from './TrustLogos';
import { ArrowRight, Sparkles, Compass } from 'lucide-react';

export const HeroSection = () => {
  return (
    <section className="hero-section-root">
      {/* Background Lighting & Grid Effects */}
      <div className="hero-bg-container">
        <div className="hero-grid-overlay"></div>
        <div className="hero-glow-cyan"></div>
        <div className="hero-glow-indigo"></div>
        <div className="hero-glow-gold"></div>

        {/* Top Floating Navbar */}
        <Navbar />

        {/* Editorial Canvas Container */}
        <div className="hero-canvas-frame">
          {/* Oversized Editorial Brand Text Watermark */}
          <OversizedBrandBackground />

          {/* Core Content Grid */}
          <div className="hero-content-grid">
            
            {/* LEFT COLUMN: Headline & Primary CTAs */}
            <div className="hero-left-col">
              {/* Refined Small Badge */}
              <HeroBadge />

              {/* Main Headline */}
              <h1 className="hero-headline">
                Legal Research.<br />
                <span className="headline-highlight">Reimagined.</span>
              </h1>

              {/* Supporting Description */}
              <p className="hero-description">
                Research case law, analyze contracts, trace legal timelines, and organize case evidence in one intelligent workspace built for legal professionals.
              </p>

              {/* CTA Buttons */}
              <div className="hero-cta-group">
                <a href="#explore" className="btn-primary-cta">
                  <Sparkles size={18} className="cta-sparkle" />
                  <span>Explore LegalLens</span>
                  <ArrowRight size={17} className="cta-arrow" />
                </a>

                <a href="#features" className="btn-secondary-cta">
                  <Compass size={17} className="secondary-icon" />
                  <span>Discover Features</span>
                </a>
              </div>

              {/* Partner Badges / Trust Logos */}
              <TrustLogos />
            </div>

            {/* RIGHT COLUMN: Category Icons, Spotlight & Key Metrics */}
            <div className="hero-right-col">
              <SolutionSidebar />
            </div>

          </div>
        </div>
      </div>

      <style jsx>{`
        .hero-section-root {
          position: relative;
          width: 100%;
          min-height: 100vh;
        }

        .hero-bg-container {
          position: relative;
          min-height: 100vh;
          width: 100%;
          background: transparent;
        }

        .hero-canvas-frame {
          position: relative;
          max-width: 1440px;
          margin: 0 auto;
          width: 100%;
          padding: 2rem 2.5rem 4rem 2.5rem;
          display: flex;
          flex-direction: column;
        }

        .hero-content-grid {
          position: relative;
          z-index: 10;
          display: grid;
          grid-template-columns: 1.15fr 0.85fr;
          justify-content: space-between;
          gap: 4rem;
          align-items: center;
          margin-top: 5rem;
        }

        .hero-left-col {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
          z-index: 10;
          max-width: 580px;
        }

        .hero-headline {
          font-family: var(--font-sans);
          font-size: clamp(2.75rem, 4.2vw, 4.2rem);
          font-weight: 800;
          line-height: 1.08;
          letter-spacing: -0.03em;
          color: var(--text-cream);
          margin-bottom: 1.25rem;
        }

        .headline-highlight {
          background: linear-gradient(135deg, var(--accent-gold) 0%, var(--text-cream) 40%, var(--accent-gold-bright) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          position: relative;
          display: inline-block;
        }

        .hero-description {
          font-size: 1.05rem;
          line-height: 1.65;
          color: var(--text-cream-muted);
          max-width: 480px;
          margin-bottom: 2.2rem;
          font-weight: 400;
        }

        .hero-cta-group {
          display: flex;
          align-items: center;
          gap: 1.2rem;
          flex-wrap: wrap;
        }

        .btn-primary-cta {
          display: inline-flex;
          align-items: center;
          gap: 0.65rem;
          padding: 0.9rem 1.8rem;
          background: linear-gradient(135deg, var(--accent-burgundy) 0%, var(--accent-burgundy-bright) 100%);
          color: var(--text-cream);
          font-size: 0.95rem;
          font-weight: 800;
          border-radius: 100px;
          border: 1px solid var(--accent-gold);
          text-decoration: none;
          box-shadow: 
            0 10px 30px rgba(107, 31, 40, 0.4),
            inset 0 1px 0 rgba(245, 237, 225, 0.2);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .btn-primary-cta:hover {
          transform: translateY(-2px);
          background: linear-gradient(135deg, var(--accent-burgundy-bright) 0%, #a1323f 100%);
          box-shadow: 
            0 15px 40px rgba(107, 31, 40, 0.6),
            inset 0 1px 0 rgba(245, 237, 225, 0.4);
          border-color: var(--accent-gold-bright);
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
          padding: 0.9rem 1.6rem;
          background: rgba(31, 19, 21, 0.6);
          color: var(--text-cream);
          font-size: 0.95rem;
          font-weight: 600;
          border-radius: 100px;
          border: 1px solid rgba(201, 162, 75, 0.3);
          text-decoration: none;
          backdrop-filter: blur(10px);
          transition: all 0.3s ease;
        }

        .btn-secondary-cta:hover {
          background: rgba(107, 31, 40, 0.3);
          border-color: var(--accent-gold);
          color: var(--accent-gold);
          transform: translateY(-2px);
        }

        .secondary-icon {
          color: var(--accent-gold);
        }

        .hero-right-col {
          display: flex;
          flex-direction: column;
          z-index: 10;
          max-width: 420px;
        }

        /* Responsive Breakpoints */
        @media (max-width: 1024px) {
          .hero-content-grid {
            grid-template-columns: 1fr;
            margin-top: 2.5rem;
            gap: 3rem;
          }
          .hero-right-col {
            max-width: 100%;
          }
          .hero-left-col {
            max-width: 100%;
          }
        }

        @media (max-width: 768px) {
          .hero-canvas-frame {
            padding: 1rem 1.25rem 3rem 1.25rem;
          }
          .hero-headline {
            font-size: 2.5rem;
          }
          .hero-cta-group {
            width: 100%;
          }
          .btn-primary-cta, .btn-secondary-cta {
            width: 100%;
            justify-content: center;
          }
        }
      `}</style>
    </section>
  );
};
