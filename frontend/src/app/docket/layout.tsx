import type { Metadata } from "next";
import { Calendar, ArrowLeft } from "lucide-react";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Docket | LegalLens",
  description:
    "Manage hearings, deadlines, and reminders for your legal matter.",
};

/** Server Component layout for all docket sub-routes. */
export default function DocketLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--bg-dark)",
        color: "var(--text-cream)",
        fontFamily: "var(--font-sans)",
      }}
    >
      {/* Docket top-bar */}
      <header
        style={{
          borderBottom: "1px solid var(--border-subtle)",
          background: "var(--bg-card)",
          padding: "0 1.5rem",
          height: "56px",
          display: "flex",
          alignItems: "center",
          gap: "1rem",
          position: "sticky",
          top: 0,
          zIndex: 20,
        }}
      >
        <Link
          href="/"
          aria-label="Back to LegalLens"
          style={{
            color: "var(--text-dim)",
            display: "flex",
            alignItems: "center",
            gap: "0.375rem",
            textDecoration: "none",
            fontSize: "0.85rem",
          }}
        >
          <ArrowLeft size={15} />
          Home
        </Link>
        <div
          style={{
            width: 1,
            height: 20,
            background: "var(--border-subtle)",
          }}
        />
        <Calendar size={16} color="var(--accent-gold)" aria-hidden />
        <span
          style={{
            fontWeight: 600,
            fontSize: "0.95rem",
            color: "var(--text-cream)",
          }}
        >
          Docket
        </span>
      </header>

      <main>{children}</main>
    </div>
  );
}
