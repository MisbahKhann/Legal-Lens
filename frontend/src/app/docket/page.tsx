import type { Metadata } from "next";
import Link from "next/link";
import { Scale } from "lucide-react";

export const metadata: Metadata = {
  title: "Matters | LegalLens Docket",
};

/**
 * Server Component page: /docket
 * Lists matters — dev stub shows a single seeded matter card.
 * Replace with a real Server Component fetch once auth is wired up.
 */
export default function DocketIndexPage() {
  return (
    <div
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: "2.5rem 1.5rem",
      }}
    >
      <h1
        style={{
          fontFamily: "var(--font-serif)",
          fontSize: "1.75rem",
          fontWeight: 700,
          color: "var(--accent-gold)",
          marginBottom: "0.5rem",
        }}
      >
        Your Matters
      </h1>
      <p
        style={{
          color: "var(--text-dim)",
          marginBottom: "2rem",
          fontSize: "0.9rem",
        }}
      >
        Select a matter to view its docket calendar, events, and reminders.
      </p>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        {/* Sample Matter 1 */}
        <Link
          href="/docket/matter-acme-2026"
          style={{ textDecoration: "none" }}
          aria-label="Open Acme Corp litigation matter"
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-gold)",
              borderRadius: "0.75rem",
              padding: "1.25rem 1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              cursor: "pointer",
            }}
          >
            <Scale
              size={24}
              color="var(--accent-burgundy-bright)"
              aria-hidden
            />
            <div>
              <div
                style={{
                  fontWeight: 600,
                  color: "var(--text-cream)",
                  fontSize: "1rem",
                }}
              >
                Acme Corp v. Global Logistics
              </div>
              <div
                style={{
                  color: "var(--text-dim)",
                  fontSize: "0.8rem",
                  marginTop: "0.15rem",
                }}
              >
                CV-2026-0842 &nbsp;·&nbsp; Client: Acme Corp &nbsp;·&nbsp; Active
              </div>
            </div>
          </div>
        </Link>

        {/* Sample Matter 2 */}
        <Link
          href="/docket/matter-henderson-2026"
          style={{ textDecoration: "none" }}
          aria-label="Open Henderson criminal litigation matter"
        >
          <div
            style={{
              background: "var(--bg-card)",
              border: "1px solid var(--border-subtle)",
              borderRadius: "0.75rem",
              padding: "1.25rem 1.5rem",
              display: "flex",
              alignItems: "center",
              gap: "1rem",
              cursor: "pointer",
            }}
          >
            <Scale
              size={24}
              color="var(--accent-gold)"
              aria-hidden
            />
            <div>
              <div
                style={{
                  fontWeight: 600,
                  color: "var(--text-cream)",
                  fontSize: "1rem",
                }}
              >
                State of California v. Henderson
              </div>
              <div
                style={{
                  color: "var(--text-dim)",
                  fontSize: "0.8rem",
                  marginTop: "0.15rem",
                }}
              >
                CR-2026-0199 &nbsp;·&nbsp; Client: David Henderson &nbsp;·&nbsp; Active
              </div>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
