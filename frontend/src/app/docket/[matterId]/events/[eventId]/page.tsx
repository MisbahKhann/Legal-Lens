import { Suspense } from "react";
import type { Metadata } from "next";
import EventDetailClient from "@/components/docket/EventDetailClient";

export const instant = false;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ matterId: string; eventId: string }>;
}): Promise<Metadata> {
  const { eventId } = await params;
  return {
    title: `Event ${eventId} | LegalLens Docket`,
  };
}

export default function EventDetailPage({
  params,
}: {
  params: Promise<{ matterId: string; eventId: string }>;
}) {
  return (
    <Suspense fallback={<div style={{ padding: "3rem", textAlign: "center", color: "var(--text-dim)" }}>Loading event…</div>}>
      <EventDetailContent params={params} />
    </Suspense>
  );
}

async function EventDetailContent({
  params,
}: {
  params: Promise<{ matterId: string; eventId: string }>;
}) {
  const { matterId, eventId } = await params;

  return <EventDetailClient matterId={matterId} eventId={eventId} />;
}

