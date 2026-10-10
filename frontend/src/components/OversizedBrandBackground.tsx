'use client';

import React from 'react';

export const OversizedBrandBackground = () => {
  return (
    <div className="oversized-brand-wrapper" aria-hidden="true">
      <h1 className="oversized-brand-text">LegalLens</h1>
      <div className="brand-glow-line"></div>
      
      <style jsx>{`
        .oversized-brand-wrapper {
          position: absolute;
          top: 3.5rem;
          left: 50%;
          transform: translateX(-50%);
          width: 100%;
          max-width: 1440px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          pointer-events: none;
          z-index: 1;
          user-select: none;
          overflow: hidden;
          padding: 0 1rem;
        }

        .oversized-brand-text {
          font-family: var(--font-sans);
          font-size: clamp(4.5rem, 14vw, 13.5rem);
          font-weight: 900;
          letter-spacing: -0.05em;
          text-transform: uppercase;
          line-height: 0.85;
          text-align: center;
          white-space: nowrap;
          
          background: linear-gradient(
            180deg,
            rgba(245, 237, 225, 0.09) 0%,
            rgba(201, 162, 75, 0.03) 60%,
            transparent 100%
          );
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          
          -webkit-text-stroke: 1px rgba(245, 237, 225, 0.08);
          
          text-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
          filter: drop-shadow(0 0 40px rgba(201, 162, 75, 0.08));
          opacity: 0.95;
        }

        .brand-glow-line {
          width: 60%;
          max-width: 700px;
          height: 1px;
          margin-top: -1.5rem;
          background: linear-gradient(
            90deg, 
            transparent 0%, 
            rgba(107, 31, 40, 0.5) 30%, 
            rgba(201, 162, 75, 0.6) 50%, 
            rgba(107, 31, 40, 0.5) 70%, 
            transparent 100%
          );
          box-shadow: 0 0 15px rgba(201, 162, 75, 0.3);
        }

        @media (max-width: 768px) {
          .oversized-brand-wrapper {
            top: 2rem;
          }
          .oversized-brand-text {
            font-size: clamp(3rem, 16vw, 5.5rem);
            -webkit-text-stroke: 1px rgba(245, 237, 225, 0.08);
          }
        }
      `}</style>
    </div>
  );
};
