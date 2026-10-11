'use client';

import React, { useState, useRef } from 'react';
import { ScrollCanvasSequence } from './ScrollCanvasSequence';
import { Navbar } from './Navbar';
import { HeroSection } from './HeroSection';
import { FeatureCarousels } from './FeatureCarousels';
import { BentoGridSection } from './BentoGridSection';
import { Footer } from './Footer';
import { DemoModal } from './DemoModal';
import { PolicyModal, PolicyType } from './PolicyModal';

export const LegalLensLanding: React.FC = () => {
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);
  const [activePolicy, setActivePolicy] = useState<PolicyType | null>(null);

  // Store trigger element ref to restore focus upon modal dismissal
  const lastTriggerRef = useRef<HTMLElement | null>(null);

  const handleOpenDemo = () => {
    lastTriggerRef.current = (document.activeElement as HTMLElement) || null;
    setIsDemoModalOpen(true);
  };

  const handleCloseDemo = () => {
    setIsDemoModalOpen(false);
  };

  const handleOpenPolicy = (type: PolicyType) => {
    lastTriggerRef.current = (document.activeElement as HTMLElement) || null;
    setActivePolicy(type);
  };

  const handleClosePolicy = () => {
    setActivePolicy(null);
  };

  return (
    <div className="landing-root">
      {/* 150-Frame Architectural Background Animation preserved underneath */}
      <ScrollCanvasSequence>
        
        {/* Sticky Top Navigation Bar without wordmark */}
        <Navbar onRequestDemo={handleOpenDemo} />

        {/* Clean Editorial Hero Section */}
        <HeroSection onRequestDemo={handleOpenDemo} />

        {/* 10-Feature Interactive Double-Track Carousel */}
        <FeatureCarousels />

        {/* Bento Intelligence Grid, Enterprise Highlights, Pricing & Resources */}
        <BentoGridSection onRequestDemo={handleOpenDemo} />

        {/* Complete 4-Column Editorial Footer */}
        <Footer
          onRequestDemo={handleOpenDemo}
          onOpenPolicy={handleOpenPolicy}
        />

      </ScrollCanvasSequence>

      {/* Accessible, Honest Demo Request Modal */}
      <DemoModal
        isOpen={isDemoModalOpen}
        onClose={handleCloseDemo}
        triggerRef={lastTriggerRef}
      />

      {/* Accessible Policy, Terms, Disclaimer & About Modal */}
      <PolicyModal
        type={activePolicy}
        onClose={handleClosePolicy}
        triggerRef={lastTriggerRef}
      />

      <style jsx>{`
        .landing-root {
          position: relative;
          width: 100%;
          min-height: 100vh;
        }
      `}</style>
    </div>
  );
};
