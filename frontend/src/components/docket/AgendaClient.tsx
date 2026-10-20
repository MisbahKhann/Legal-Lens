'use client';

/**
 * AgendaClient – Client Component.
 * Shows a date-range timeline of upcoming events and reminders.
 */

import React, { useEffect, useState } from 'react';
import { CalendarDays, Bell, AlertTriangle } from 'lucide-react';
import { getAgenda } from '@/lib/docketApi';
import type { components } from '@/types/docket';

type AgendaResponse = components['schemas']['AgendaResponse'];

interface AgendaClientProps {
  matterId: string;
}

function formatRelative(dateStr: string): string {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = d.getTime() - now.getTime();
  const diffDays = Math.round(diffMs / 86400000);
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays === -1) return 'Yesterday';
  if (diffDays > 0) return `In ${diffDays} days`;
  return `${Math.abs(diffDays)} days ago`;
}

export default function AgendaClient({ matterId }: AgendaClientProps) {
  const [agenda, setAgenda] = useState<AgendaResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    const now = new Date();
    const fromDate = now.toISOString();
    const toDate = new Date(now.getTime() + 30 * 86400000).toISOString();
    getAgenda(matterId, fromDate, toDate)
      .then(data => {
        if (!cancelled) {
          setAgenda(data);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load agenda');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [matterId]);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem' }}>
        <CalendarDays size={18} color="var(--accent-gold)" aria-hidden />
        <h2 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-cream)' }}>
          Next 30 Days
        </h2>
      </div>

      {/* Missed reminders banner */}
      {agenda && agenda.missed_reminders.length > 0 && (
        <div
          role="alert"
          aria-live="assertive"
          style={{
            background: 'rgba(248,113,113,0.1)',
            border: '1px solid #f8717150',
            borderRadius: '0.6rem',
            padding: '0.85rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            gap: '0.6rem',
            alignItems: 'flex-start',
          }}
        >
          <AlertTriangle size={16} color="#f87171" style={{ flexShrink: 0, marginTop: 2 }} aria-hidden />
          <div>
            <p style={{ color: '#f87171', fontWeight: 700, fontSize: '0.85rem', margin: 0 }}>
              {agenda.missed_reminders.length} Missed Reminder{agenda.missed_reminders.length > 1 ? 's' : ''}
            </p>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.8rem', margin: '0.2rem 0 0' }}>
              These reminders fired while you were away. Please review and acknowledge them.
            </p>
          </div>
        </div>
      )}

      {loading && <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '2rem' }} aria-live="polite" aria-busy>Loading agenda…</p>}
      {error && <p role="alert" style={{ color: '#f87171', padding: '1rem' }}>{error}</p>}

      {!loading && agenda?.items.length === 0 && (
        <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '3rem', fontSize: '0.9rem' }}>
          Nothing scheduled in the next 30 days.
        </p>
      )}

      {/* Timeline */}
      <ol style={{ listStyle: 'none', padding: 0, margin: 0, position: 'relative' }} aria-label="Upcoming events and reminders">
        {agenda?.items.map((item, idx) => {
          const isReminder = item.item_type === 'reminder';
          const displayTitle = isReminder
            ? (item.reminder?.id ? `Reminder for event` : 'Reminder')
            : (item.event?.title ?? 'Event');
          const displayKind = isReminder ? 'Reminder' : (item.event?.kind ?? 'Event');
          return (
            <li
              key={idx}
              style={{
                display: 'flex',
                gap: '0.75rem',
                marginBottom: '0.85rem',
                position: 'relative',
              }}
            >
              {/* Timeline dot */}
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                flexShrink: 0,
                width: 20,
              }}>
                <div style={{
                  width: 12, height: 12,
                  borderRadius: '50%',
                  background: isReminder ? 'var(--accent-burgundy-bright)' : 'var(--accent-gold)',
                  border: '2px solid var(--bg-dark)',
                  marginTop: 4,
                  flexShrink: 0,
                }} aria-hidden />
                {idx < (agenda.items.length - 1) && (
                  <div style={{
                    flex: 1,
                    width: 2,
                    background: 'var(--border-subtle)',
                    marginTop: 2,
                    minHeight: 24,
                  }} aria-hidden />
                )}
              </div>

              {/* Content */}
              <div style={{
                flex: 1,
                background: 'var(--bg-card)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '0.6rem',
                padding: '0.75rem 1rem',
                marginBottom: 0,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                    {isReminder
                      ? <Bell size={13} color="var(--accent-burgundy-bright)" aria-hidden />
                      : <CalendarDays size={13} color="var(--accent-gold)" aria-hidden />
                    }
                    <span style={{
                      fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
                      letterSpacing: '0.07em',
                      color: isReminder ? 'var(--accent-burgundy-bright)' : 'var(--accent-gold)',
                    }}>
                      {displayKind}
                    </span>
                  </div>
                  <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                    {formatRelative(item.timestamp)} · {new Date(item.timestamp).toLocaleString('en-US', {
                      month: 'short', day: 'numeric',
                      hour: '2-digit', minute: '2-digit',
                    })}
                  </span>
                </div>
                <p style={{ fontWeight: 600, color: 'var(--text-cream)', fontSize: '0.9rem', margin: '0.25rem 0 0' }}>
                  {displayTitle}
                </p>
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}
