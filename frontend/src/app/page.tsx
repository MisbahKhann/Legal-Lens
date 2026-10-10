import { Metadata } from 'next';
import { ScrollCanvasSequence } from '@/components/ScrollCanvasSequence';
import { HeroSection } from '@/components/HeroSection';
import { FeatureCarousels } from '@/components/FeatureCarousels';
import { BentoGridSection } from '@/components/BentoGridSection';

export const metadata: Metadata = {
  title: 'LegalLens — AI-Powered Legal Intelligence Platform',
  description: 'Research case law, analyze contracts, trace legal timelines, and organize case evidence in one intelligent workspace built for legal professionals.',
  keywords: ['legal tech', 'AI contract analysis', 'case law research', 'legal timeline extraction', 'law firm AI', 'LegalLens'],
  openGraph: {
    title: 'LegalLens — AI-Powered Legal Intelligence',
    description: 'Legal Research. Reimagined. Built for lawyers, law firms, and legal professionals.',
    type: 'website',
  },
};

export default function Home() {
  return (
    <main className="min-h-screen bg-[#140d0e] text-[#f5ede1] antialiased overflow-x-hidden">
      <ScrollCanvasSequence>
        <HeroSection />
        <FeatureCarousels />
        <BentoGridSection />
      </ScrollCanvasSequence>
    </main>
  );
}
