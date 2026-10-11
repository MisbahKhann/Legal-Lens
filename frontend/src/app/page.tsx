import { Metadata } from 'next';
import { LegalLensLanding } from '@/components/LegalLensLanding';

export const metadata: Metadata = {
  title: 'LegalLens — AI-Powered Legal Intelligence Platform',
  description: 'Research cases, understand contracts, and organize legal evidence in one intelligent workspace built for legal professionals.',
  keywords: ['legal tech', 'AI contract analysis', 'case law research', 'legal evidence timeline', 'law firm AI', 'LegalLens'],
  openGraph: {
    title: 'LegalLens — AI-Powered Legal Intelligence',
    description: 'Legal intelligence, clearly connected. Built for lawyers, law firms, and corporate legal teams.',
    type: 'website',
  },
};

export default function Home() {
  return (
    <main className="min-h-screen bg-[#140d0e] text-[#f5ede1] antialiased overflow-x-hidden">
      <LegalLensLanding />
    </main>
  );
}
