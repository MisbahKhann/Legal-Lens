import { Suspense } from "react";
import type { Metadata } from "next";
import EventsClient from "@/components/docket/EventsClient";
import AgendaClient from "@/components/docket/AgendaClient";
import NotificationsClient from "@/components/docket/NotificationsClient";

export const instant = false;

/** Route: /docket/[matterId] — Matter Docket Dashboard (Server Component page). */
export async function generateMetadata({
  params,
}: {
  params: Promise<{ matterId: string }>;
}): Promise<Metadata> {
  const { matterId } = await params;
  return {
    title: `Docket — Matter ${matterId} | LegalLens`,
  };
}

export default function MatterDocketPage({
  params,
}: {
  params: Promise<{ matterId: string }>;
}) {
  return (
    <Suspense fallback={<div style={{ padding: "3rem", textAlign: "center", color: "var(--text-dim)" }}>Loading matter docket…</div>}>
      <MatterDocketContent params={params} />
    </Suspense>
  );
}

async function MatterDocketContent({
  params,
}: {
  params: Promise<{ matterId: string }>;
}) {
  const { matterId } = await params;

  return (
    <div
      style={{
        maxWidth: 1200,
        margin: "0 auto",
        padding: "2rem 1.5rem",
        display: "grid",
        gridTemplateColumns: "1fr 360px",
        gap: "2rem",
        alignItems: "start",
      }}
    >
      {/* ── Left column: Events ───────────────────────────────── */}
      <section aria-label="Docket events">
        <h2
          style={{
            fontFamily: "var(--font-serif)",
            fontSize: "1.5rem",
            fontWeight: 700,
            color: "var(--accent-gold)",
            marginBottom: "1.25rem",
          }}
        >
          Events
        </h2>
        <EventsClient matterId={matterId} />
      </section>

      {/* ── Right column: Agenda + Notifications ──────────────── */}
      <aside style={{ display: "flex", flexDirection: "column", gap: "2rem" }}>
        <section
          aria-label="Agenda"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.875rem",
            padding: "1.25rem",
          }}
        >
          <AgendaClient matterId={matterId} />
        </section>

        <section
          aria-label="Notifications"
          style={{
            background: "var(--bg-card)",
            border: "1px solid var(--border-subtle)",
            borderRadius: "0.875rem",
            padding: "1.25rem",
          }}
        >
          <NotificationsClient matterId={matterId} />
        </section>
      </aside>
    </div>
  );
}
