'use client';

/**
 * NotificationsClient – Client Component.
 * Renders in-app notifications for the current user (scoped by the API).
 */

import React, { useEffect, useState } from 'react';
import { Bell, CheckCheck, BellOff } from 'lucide-react';
import {
  listNotifications,
  markNotificationRead,
  markAllNotificationsRead,
} from '@/lib/docketApi';
import type { components } from '@/types/docket';

type NotificationResponse = components['schemas']['NotificationResponse'];

function typeLabel(t: string): string {
  const map: Record<string, string> = {
    reminder_fired: 'Reminder',
    reminder_late: '⚠ Late Reminder',
    event_rescheduled: 'Rescheduled',
    event_postponed: 'Postponed',
    event_cancelled: 'Cancelled',
    document_changed: 'Document Changed',
  };
  return map[t] ?? t;
}

interface NotificationsClientProps {
  matterId?: string;
}

export default function NotificationsClient({ matterId }: NotificationsClientProps) {
  const [items, setItems] = useState<NotificationResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [marking, setMarking] = useState(false);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 20;

  useEffect(() => {
    let cancelled = false;
    listNotifications({
      matter_id: matterId,
      unread_only: unreadOnly,
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
    })
      .then(res => {
        if (!cancelled) {
          setItems(res.items);
          setTotal(res.total);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load notifications');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [matterId, unreadOnly, page]);

  async function handleMarkRead(id: string) {
    await markNotificationRead(id);
    setItems(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  }

  async function handleMarkAll() {
    setMarking(true);
    try {
      await markAllNotificationsRead(matterId);
      setItems(prev => prev.map(n => ({ ...n, is_read: true })));
    } finally { setMarking(false); }
  }

  const unreadCount = items.filter(n => !n.is_read).length;

  return (
    <div>
      {/* Header row */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '1.25rem', flexWrap: 'wrap' }}>
        <Bell size={18} color="var(--accent-gold)" aria-hidden />
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-cream)', margin: 0 }}>
          Notifications
          {unreadCount > 0 && (
            <span
              aria-label={`${unreadCount} unread`}
              style={{
                display: 'inline-block',
                marginLeft: '0.5rem',
                background: 'var(--accent-burgundy)',
                color: 'var(--text-cream)',
                fontSize: '0.7rem',
                fontWeight: 700,
                borderRadius: '999px',
                padding: '0.1rem 0.45rem',
                verticalAlign: 'middle',
              }}
            >
              {unreadCount}
            </span>
          )}
        </h2>

        <label
          style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: 'var(--text-dim)', fontSize: '0.85rem', cursor: 'pointer', marginLeft: 'auto' }}
        >
          <input
            type="checkbox"
            checked={unreadOnly}
            onChange={e => { setUnreadOnly(e.target.checked); setPage(0); }}
            aria-label="Show unread only"
            style={{ accentColor: 'var(--accent-gold)' }}
          />
          Unread only
        </label>

        {unreadCount > 0 && (
          <button
            onClick={handleMarkAll}
            disabled={marking}
            aria-busy={marking}
            aria-label="Mark all notifications as read"
            style={{
              display: 'inline-flex', alignItems: 'center', gap: '0.35rem',
              padding: '0.35rem 0.85rem',
              background: 'transparent',
              color: 'var(--text-dim)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '0.4rem',
              fontSize: '0.8rem', fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            <CheckCheck size={14} aria-hidden /> {marking ? '…' : 'Mark all read'}
          </button>
        )}
      </div>

      {loading && <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '2rem' }} aria-live="polite" aria-busy>Loading…</p>}
      {error && <p role="alert" style={{ color: '#f87171', padding: '1rem' }}>{error}</p>}

      {!loading && items.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-dim)' }}>
          <BellOff size={32} aria-hidden style={{ opacity: 0.4, marginBottom: '0.75rem' }} />
          <p style={{ fontSize: '0.9rem' }}>
            {unreadOnly ? 'No unread notifications.' : 'No notifications yet.'}
          </p>
        </div>
      )}

      <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        {items.map(n => (
          <li
            key={n.id}
            style={{
              background: n.is_read ? 'transparent' : 'rgba(107,31,40,0.08)',
              border: `1px solid ${n.is_read ? 'var(--border-subtle)' : 'var(--border-burgundy)'}`,
              borderRadius: '0.6rem',
              padding: '0.85rem 1rem',
              display: 'flex',
              gap: '0.75rem',
              alignItems: 'flex-start',
            }}
          >
            <div
              style={{
                flexShrink: 0, width: 8, height: 8,
                borderRadius: '50%',
                background: n.is_read ? 'transparent' : 'var(--accent-burgundy-bright)',
                border: n.is_read ? '1px solid var(--border-subtle)' : 'none',
                marginTop: 6,
              }}
              aria-hidden
            />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.5rem', flexWrap: 'wrap' }}>
                <span style={{
                  fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.07em', color: 'var(--accent-gold)',
                }}>
                  {typeLabel(n.notification_type)}
                </span>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  {new Date(n.created_at).toLocaleString()}
                </span>
              </div>
              <p style={{ fontWeight: 600, color: 'var(--text-cream)', fontSize: '0.9rem', margin: '0.2rem 0' }}>
                {n.title}
              </p>
              <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', margin: 0 }}>
                {n.message}
              </p>
            </div>
            {!n.is_read && (
              <button
                onClick={() => handleMarkRead(n.id)}
                aria-label="Mark as read"
                style={{
                  flexShrink: 0,
                  padding: '0.25rem 0.6rem',
                  background: 'transparent',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '0.35rem',
                  color: 'var(--text-dim)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                Read
              </button>
            )}
          </li>
        ))}
      </ul>

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.5rem' }} role="navigation" aria-label="Notifications pagination">
          <button
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
            style={{ padding: '0.4rem 0.85rem', background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '0.4rem', color: 'var(--text-dim)', cursor: 'pointer' }}
            aria-label="Previous page"
          >← Prev</button>
          <span style={{ lineHeight: '2rem', color: 'var(--text-dim)', fontSize: '0.85rem' }}>
            {page + 1} / {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button
            disabled={(page + 1) * PAGE_SIZE >= total}
            onClick={() => setPage(p => p + 1)}
            style={{ padding: '0.4rem 0.85rem', background: 'transparent', border: '1px solid var(--border-subtle)', borderRadius: '0.4rem', color: 'var(--text-dim)', cursor: 'pointer' }}
            aria-label="Next page"
          >Next →</button>
        </div>
      )}
    </div>
  );
}
