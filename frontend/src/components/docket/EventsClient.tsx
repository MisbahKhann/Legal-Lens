'use client';

/**
 * EventsClient – Client Component.
 * Renders the events list for a matter with create, filter, reschedule
 * (keyboard-accessible), postpone, cancel, verify deadline, and .ics export.
 */

import React, { useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  Calendar,
  Clock,
  CheckCircle2,
  XCircle,
  PauseCircle,
  RefreshCw,
  AlertTriangle,
  Download,
  Plus,
  FileCheck,
  GripVertical,
  ExternalLink,
} from 'lucide-react';

import {
  listEvents,
  cancelEvent,
  postponeEvent,
  rescheduleEvent,
  verifyDeadline,
  createEvent,
  exportIcs,
} from '@/lib/docketApi';

import type { components } from '@/types/docket';

type EventResponse = components['schemas']['EventResponse'];
type RescheduleResponse = components['schemas']['RescheduleResponse'];
type ConflictDecision = components['schemas']['ConflictDecision'];

function statusColor(s: string): string {
  switch (s) {
    case 'scheduled': return 'var(--accent-gold)';
    case 'rescheduled': return '#60a5fa';
    case 'postponed': return '#f59e0b';
    case 'cancelled': return '#f87171';
    case 'completed': return '#34d399';
    default: return 'var(--text-dim)';
  }
}

function statusIcon(s: string) {
  switch (s) {
    case 'scheduled': return <Calendar size={14} />;
    case 'rescheduled': return <RefreshCw size={14} />;
    case 'postponed': return <PauseCircle size={14} />;
    case 'cancelled': return <XCircle size={14} />;
    case 'completed': return <CheckCircle2 size={14} />;
    default: return <Clock size={14} />;
  }
}

// ─── Reschedule Modal ─────────────────────────────────────────────────────────

interface RescheduleModalProps {
  event: EventResponse;
  matterId: string;
  onClose: () => void;
  onSuccess: (res: RescheduleResponse) => void;
}

function RescheduleModal({ event, matterId, onClose, onSuccess }: RescheduleModalProps) {
  const [newDate, setNewDate] = useState('');
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [conflicts, setConflicts] = useState<RescheduleResponse['conflicts']>([]);
  const [resolutions, setResolutions] = useState<Record<string, 'shift' | 'keep' | 'cancel'>>({});
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    firstInputRef.current?.focus();
  }, []);

  // keyboard trap
  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    if (!newDate || !reason.trim()) {
      setError('New date and reason are required.');
      return;
    }
    setLoading(true);
    try {
      const conflictResMap: { [key: string]: ConflictDecision } = {};
      Object.entries(resolutions).forEach(([reminder_id, action]) => {
        conflictResMap[reminder_id] = { action };
      });
      const payload: components['schemas']['RescheduleRequest'] = {
        new_starts_at: new Date(newDate).toISOString(),
        reason: reason.trim(),
        conflict_resolutions: Object.keys(conflictResMap).length > 0 ? conflictResMap : undefined,
      };
      const res = await rescheduleEvent(matterId, event.id, payload);
      if (res.conflicts && res.conflicts.length > 0 && conflicts.length === 0) {
        setConflicts(res.conflicts);
        setLoading(false);
        return;
      }
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to reschedule');
      setLoading(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="reschedule-title"
      onKeyDown={handleKeyDown}
      style={{
        position: 'fixed', inset: 0, zIndex: 50,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-gold)',
          borderRadius: '0.875rem',
          padding: '1.75rem',
          width: '100%',
          maxWidth: 520,
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        <h2 id="reschedule-title" style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', color: 'var(--accent-gold)', marginBottom: '1rem' }}>
          Reschedule Event
        </h2>
        <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
          <strong style={{ color: 'var(--text-cream)' }}>{event.title}</strong><br />
          Currently: {new Date(event.starts_at).toLocaleString()}
        </p>

        <form onSubmit={handleSubmit}>
          <label style={labelStyle} htmlFor="new-date">New Date & Time *</label>
          <input
            id="new-date"
            ref={firstInputRef}
            type="datetime-local"
            value={newDate}
            onChange={e => setNewDate(e.target.value)}
            style={inputStyle}
            required
            aria-required="true"
          />

          <label style={labelStyle} htmlFor="reschedule-reason">Reason *</label>
          <textarea
            id="reschedule-reason"
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="e.g. Judge unavailable, case settled, etc."
            rows={3}
            style={{ ...inputStyle, resize: 'vertical' }}
            required
            aria-required="true"
          />

          {/* Conflict resolution section */}
          {conflicts.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <p style={{ color: '#f59e0b', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                <AlertTriangle size={14} style={{ display: 'inline', marginRight: 4 }} />
                {conflicts.length} fixed reminder(s) would conflict. Choose resolution:
              </p>
              {conflicts.map(c => (
                <div key={c.reminder_id} style={{ marginBottom: '0.75rem', padding: '0.75rem', background: 'var(--bg-dark)', borderRadius: '0.5rem', border: '1px solid var(--border-subtle)' }}>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-cream)', marginBottom: '0.5rem' }}>
                    Reminder fires at: {c.current_fire_at ? new Date(c.current_fire_at).toLocaleString() : 'unknown'} &nbsp;·&nbsp; {c.issue}
                  </p>
                  <div role="group" aria-label={`Resolution for reminder ${c.reminder_id}`} style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                    {(['shift', 'keep', 'cancel'] as const).map(opt => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => setResolutions(r => ({ ...r, [c.reminder_id]: opt }))}
                        aria-pressed={resolutions[c.reminder_id] === opt}
                        style={{
                          padding: '0.3rem 0.75rem',
                          borderRadius: '0.35rem',
                          fontSize: '0.8rem',
                          border: resolutions[c.reminder_id] === opt ? '2px solid var(--accent-gold)' : '1px solid var(--border-subtle)',
                          background: resolutions[c.reminder_id] === opt ? 'var(--accent-gold)' : 'transparent',
                          color: resolutions[c.reminder_id] === opt ? '#140d0e' : 'var(--text-cream)',
                          cursor: 'pointer',
                          fontWeight: 600,
                          textTransform: 'capitalize',
                        }}
                      >
                        {opt}
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle} aria-label="Cancel reschedule">
              Cancel
            </button>
            <button type="submit" disabled={loading} style={primaryBtnStyle} aria-busy={loading}>
              {loading ? 'Saving…' : conflicts.length > 0 ? 'Confirm with Resolutions' : 'Reschedule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Create Event Modal ───────────────────────────────────────────────────────

interface CreateEventModalProps {
  matterId: string;
  onClose: () => void;
  onSuccess: (ev: EventResponse) => void;
}

function CreateEventModal({ matterId, onClose, onSuccess }: CreateEventModalProps) {
  const [kind, setKind] = useState<'hearing' | 'deadline'>('hearing');
  const [title, setTitle] = useState('');
  const [startsAt, setStartsAt] = useState('');
  const [timezone, setTz] = useState('America/New_York');
  const [priority, setPriority] = useState('normal');
  const [courtName, setCourtName] = useState('');
  const [judge, setJudge] = useState('');
  const [deadlineType, setDeadlineType] = useState('');
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [loading, setLoading] = useState(false);
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { firstInputRef.current?.focus(); }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(''); setWarning('');
    if (!title.trim() || !startsAt) {
      setError('Title and start date are required.');
      return;
    }
    setLoading(true);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data: any = {
        kind,
        title: title.trim(),
        starts_at: new Date(startsAt).toISOString(),
        timezone,
        priority,
        ...(kind === 'hearing' ? { court_name: courtName, judge } : { deadline_type: deadlineType }),
      };
      const res = await createEvent(matterId, data);
      if (res.warning) setWarning(res.warning);
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create event');
      setLoading(false);
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-event-title"
      onKeyDown={handleKeyDown}
      style={{
        position: 'fixed', inset: 0, zIndex: 50,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-gold)',
          borderRadius: '0.875rem',
          padding: '1.75rem',
          width: '100%',
          maxWidth: 540,
          maxHeight: '90vh',
          overflowY: 'auto',
        }}
      >
        <h2 id="create-event-title" style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', color: 'var(--accent-gold)', marginBottom: '1.25rem' }}>
          New Event
        </h2>

        <form onSubmit={handleSubmit}>
          <fieldset style={{ border: 'none', marginBottom: '1rem' }}>
            <legend style={{ ...labelStyle, marginBottom: '0.5rem' }}>Event Type</legend>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              {(['hearing', 'deadline'] as const).map(k => (
                <button
                  key={k}
                  type="button"
                  onClick={() => setKind(k)}
                  aria-pressed={kind === k}
                  style={{
                    flex: 1, padding: '0.5rem',
                    border: kind === k ? '2px solid var(--accent-gold)' : '1px solid var(--border-subtle)',
                    borderRadius: '0.5rem',
                    background: kind === k ? 'rgba(201,162,75,0.1)' : 'transparent',
                    color: kind === k ? 'var(--accent-gold)' : 'var(--text-dim)',
                    cursor: 'pointer', fontWeight: 600, textTransform: 'capitalize',
                    fontSize: '0.9rem',
                  }}
                >
                  {k}
                </button>
              ))}
            </div>
          </fieldset>

          <label style={labelStyle} htmlFor="event-title">Title *</label>
          <input
            id="event-title"
            ref={firstInputRef}
            value={title}
            onChange={e => setTitle(e.target.value)}
            placeholder="e.g. Preliminary Hearing, Motion Filing Deadline"
            style={inputStyle}
            required
            aria-required="true"
          />

          <label style={labelStyle} htmlFor="event-starts">Date & Time *</label>
          <input
            id="event-starts"
            type="datetime-local"
            value={startsAt}
            onChange={e => setStartsAt(e.target.value)}
            style={inputStyle}
            required
            aria-required="true"
          />

          <label style={labelStyle} htmlFor="event-tz">Court Timezone</label>
          <select id="event-tz" value={timezone} onChange={e => setTz(e.target.value)} style={inputStyle} aria-label="Court timezone">
            <option value="America/New_York">America/New_York (ET)</option>
            <option value="America/Chicago">America/Chicago (CT)</option>
            <option value="America/Denver">America/Denver (MT)</option>
            <option value="America/Los_Angeles">America/Los_Angeles (PT)</option>
            <option value="Europe/London">Europe/London (GMT)</option>
            <option value="UTC">UTC</option>
          </select>

          <label style={labelStyle} htmlFor="event-priority">Priority</label>
          <select id="event-priority" value={priority} onChange={e => setPriority(e.target.value)} style={inputStyle}>
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>

          {kind === 'hearing' && (
            <>
              <label style={labelStyle} htmlFor="court-name">Court Name</label>
              <input id="court-name" value={courtName} onChange={e => setCourtName(e.target.value)} placeholder="e.g. U.S. District Court, SDNY" style={inputStyle} />

              <label style={labelStyle} htmlFor="judge">Judge</label>
              <input id="judge" value={judge} onChange={e => setJudge(e.target.value)} placeholder="e.g. Hon. Sarah Vance" style={inputStyle} />
            </>
          )}

          {kind === 'deadline' && (
            <>
              <label style={labelStyle} htmlFor="deadline-type">Deadline Type</label>
              <input id="deadline-type" value={deadlineType} onChange={e => setDeadlineType(e.target.value)} placeholder="e.g. Statutory, Filing, Discovery" style={inputStyle} />
            </>
          )}

          {warning && <p role="status" aria-live="polite" style={{ color: '#f59e0b', fontSize: '0.85rem', marginBottom: '0.75rem' }}>⚠ {warning}</p>}
          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button type="submit" disabled={loading} style={primaryBtnStyle} aria-busy={loading}>
              {loading ? 'Creating…' : 'Create Event'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Reason Modal (Postpone / Cancel) ────────────────────────────────────────

interface ReasonModalProps {
  action: 'postpone' | 'cancel';
  event: EventResponse;
  matterId: string;
  onClose: () => void;
  onSuccess: (ev: EventResponse) => void;
}

function ReasonModal({ action, event, matterId, onClose, onSuccess }: ReasonModalProps) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRef = useRef<HTMLTextAreaElement>(null);
  useEffect(() => { inputRef.current?.focus(); }, []);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Escape') onClose();
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reason.trim()) { setError('Reason is required.'); return; }
    setLoading(true);
    try {
      const fn = action === 'postpone' ? postponeEvent : cancelEvent;
      const res = await fn(matterId, event.id, reason.trim());
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed');
      setLoading(false);
    }
  }

  const label = action === 'postpone' ? 'Postpone Event' : 'Cancel Event';
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="reason-modal-title"
      onKeyDown={handleKeyDown}
      style={{
        position: 'fixed', inset: 0, zIndex: 50,
        background: 'rgba(0,0,0,0.65)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '1rem',
      }}
    >
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-burgundy)',
        borderRadius: '0.875rem',
        padding: '1.75rem',
        width: '100%',
        maxWidth: 460,
      }}>
        <h2 id="reason-modal-title" style={{ fontFamily: 'var(--font-serif)', fontSize: '1.15rem', color: action === 'cancel' ? '#f87171' : '#f59e0b', marginBottom: '0.75rem' }}>
          {label}
        </h2>
        <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', marginBottom: '1rem' }}>
          Event: <strong style={{ color: 'var(--text-cream)' }}>{event.title}</strong>
        </p>
        <form onSubmit={handleSubmit}>
          <label style={labelStyle} htmlFor="reason-input">Reason *</label>
          <textarea
            id="reason-input"
            ref={inputRef}
            rows={3}
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder={`Why is this event being ${action}d?`}
            style={{ ...inputStyle, resize: 'vertical' }}
            required
            aria-required="true"
          />
          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button
              type="submit"
              disabled={loading}
              style={{ ...primaryBtnStyle, background: action === 'cancel' ? '#991b1b' : 'var(--accent-burgundy)' }}
              aria-busy={loading}
            >
              {loading ? 'Processing…' : label}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── EventCard ────────────────────────────────────────────────────────────────

interface EventCardProps {
  event: EventResponse;
  matterId: string;
  onUpdate: (ev: EventResponse) => void;
}

function EventCard({ event, matterId, onUpdate }: EventCardProps) {
  const [showReschedule, setShowReschedule] = useState(false);
  const [showReason, setShowReason] = useState<'postpone' | 'cancel' | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [exporting, setExporting] = useState(false);

  const isActive = !['cancelled', 'completed'].includes(event.status);
  const isDeadline = event.kind === 'deadline';

  async function handleVerify() {
    setVerifying(true);
    try {
      const res = await verifyDeadline(matterId, event.id);
      onUpdate(res);
    } finally { setVerifying(false); }
  }

  async function handleExportIcs() {
    setExporting(true);
    try {
      const text = await exportIcs(matterId, event.id);
      const blob = new Blob([text], { type: 'text/calendar' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `event-${event.id}.ics`;
      a.click();
      URL.revokeObjectURL(url);
    } finally { setExporting(false); }
  }

  return (
    <>
      <div
        draggable={isActive}
        onDragStart={e => {
          e.dataTransfer.setData('text/plain', event.id);
          e.dataTransfer.effectAllowed = 'move';
        }}
        style={{
          background: 'var(--bg-card)',
          border: `1px solid ${isActive ? 'var(--border-subtle)' : 'var(--border-burgundy)'}`,
          borderRadius: '0.75rem',
          padding: '1rem 1.25rem',
          opacity: event.status === 'cancelled' ? 0.6 : 1,
          cursor: isActive ? 'grab' : 'default',
        }}
      >
        {/* Header row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginBottom: '0.4rem' }}>
              {isActive && (
                <span title="Drag event onto quick slot to reschedule" style={{ color: 'var(--text-dim)', cursor: 'grab', display: 'inline-flex' }}>
                  <GripVertical size={14} />
                </span>
              )}
              <span
                style={{
                  display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                  fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: statusColor(event.status),
                  background: `${statusColor(event.status)}20`,
                  border: `1px solid ${statusColor(event.status)}50`,
                  borderRadius: '0.25rem', padding: '0.15rem 0.45rem',
                }}
              >
                {statusIcon(event.status)} {event.status}
              </span>
              <span
                style={{
                  fontSize: '0.7rem', fontWeight: 600, textTransform: 'uppercase',
                  letterSpacing: '0.06em',
                  color: event.kind === 'hearing' ? 'var(--accent-burgundy-bright)' : '#818cf8',
                  marginRight: '0.25rem',
                }}
              >
                {event.kind}
              </span>
              {isDeadline && event.verified_by && (
                <span title={`Verified by ${event.verified_by}`} style={{ color: '#34d399', display: 'inline-flex', alignItems: 'center' }}>
                  <CheckCircle2 size={12} />
                </span>
              )}
            </div>
            <h3 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-cream)', margin: 0 }}>
              <Link
                href={`/docket/${matterId}/events/${event.id}`}
                style={{ color: 'inherit', textDecoration: 'none' }}
                aria-label={`View details for ${event.title}`}
              >
                {event.title}
              </Link>
            </h3>
            {event.court_name && (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.8rem', margin: '0.15rem 0 0' }}>
                {event.court_name}{event.judge ? ` · ${event.judge}` : ''}
              </p>
            )}
          </div>
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <p style={{ color: 'var(--accent-gold)', fontSize: '0.85rem', fontWeight: 600, margin: 0 }}>
              {new Date(event.starts_at).toLocaleDateString('en-US', {
                weekday: 'short', month: 'short', day: 'numeric', year: 'numeric',
              })}
            </p>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.78rem', margin: '0.15rem 0 0' }}>
              {new Date(event.starts_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              {' '}({event.timezone})
            </p>
          </div>
        </div>

        {event.warning && (
          <p role="status" style={{ color: '#f59e0b', fontSize: '0.8rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <AlertTriangle size={13} aria-hidden /> {event.warning}
          </p>
        )}

        {/* Action row */}
        {isActive && (
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
            {/* Reschedule – keyboard accessible button */}
            <button
              onClick={() => setShowReschedule(true)}
              style={chipBtnStyle}
              aria-label={`Reschedule ${event.title}`}
            >
              <RefreshCw size={12} aria-hidden /> Reschedule
            </button>

            <button
              onClick={() => setShowReason('postpone')}
              style={chipBtnStyle}
              aria-label={`Postpone ${event.title}`}
            >
              <PauseCircle size={12} aria-hidden /> Postpone
            </button>

            <button
              onClick={() => setShowReason('cancel')}
              style={{ ...chipBtnStyle, color: '#f87171', borderColor: '#f8717140' }}
              aria-label={`Cancel ${event.title}`}
            >
              <XCircle size={12} aria-hidden /> Cancel
            </button>

            {isDeadline && !event.verified_by && (
              <button
                onClick={handleVerify}
                disabled={verifying}
                style={{ ...chipBtnStyle, color: '#34d399', borderColor: '#34d39940' }}
                aria-label={`Verify deadline for ${event.title}`}
                aria-busy={verifying}
              >
                <FileCheck size={12} aria-hidden /> {verifying ? 'Verifying…' : 'Verify'}
              </button>
            )}

            <Link
              href={`/docket/${matterId}/events/${event.id}`}
              style={{ ...chipBtnStyle, textDecoration: 'none' }}
              aria-label={`View details and documents for ${event.title}`}
            >
              <ExternalLink size={12} aria-hidden /> Details & Docs
            </Link>

            <button
              onClick={handleExportIcs}
              disabled={exporting}
              style={chipBtnStyle}
              aria-label={`Export ${event.title} as .ics`}
              aria-busy={exporting}
            >
              <Download size={12} aria-hidden /> {exporting ? '…' : '.ics'}
            </button>
          </div>
        )}
      </div>

      {showReschedule && (
        <RescheduleModal
          event={event}
          matterId={matterId}
          onClose={() => setShowReschedule(false)}
          onSuccess={res => { setShowReschedule(false); onUpdate(res.event); }}
        />
      )}

      {showReason && (
        <ReasonModal
          action={showReason}
          event={event}
          matterId={matterId}
          onClose={() => setShowReason(null)}
          onSuccess={res => { setShowReason(null); onUpdate(res); }}
        />
      )}
    </>
  );
}

// ─── Main Events Client ───────────────────────────────────────────────────────

interface EventsClientProps {
  matterId: string;
}

export default function EventsClient({ matterId }: EventsClientProps) {
  const [events, setEvents] = useState<EventResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [kindFilter, setKindFilter] = useState<'' | 'hearing' | 'deadline'>('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [page, setPage] = useState(0);
  const PAGE_SIZE = 20;

  useEffect(() => {
    let cancelled = false;
    listEvents(matterId, {
      limit: PAGE_SIZE,
      offset: page * PAGE_SIZE,
      kind: kindFilter || undefined,
      status: statusFilter || undefined,
    })
      .then(res => {
        if (!cancelled) {
          setEvents(res.items);
          setTotal(res.total);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load events');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [matterId, kindFilter, statusFilter, page]);

  function handleUpdate(updated: EventResponse) {
    setEvents(prev => prev.map(e => e.id === updated.id ? updated : e));
  }

  function handleCreate(ev: EventResponse) {
    setShowCreate(false);
    setEvents(prev => [ev, ...prev]);
    setTotal(t => t + 1);
  }

  async function handleDropReschedule(eventId: string, daysToAdd: number) {
    const target = events.find(e => e.id === eventId);
    if (!target) return;
    const curDate = new Date(target.starts_at);
    const newStartsAt = new Date(curDate.getTime() + daysToAdd * 86400000).toISOString();
    try {
      const res = await rescheduleEvent(matterId, eventId, {
        new_starts_at: newStartsAt,
        reason: `Quick drag-and-drop reschedule (+${daysToAdd} days)`,
      });
      if (res.conflicts && res.conflicts.length > 0) {
        alert(`Event has ${res.conflicts.length} reminder conflict(s). Please use the keyboard Reschedule button to resolve them.`);
      } else {
        handleUpdate(res.event);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Reschedule failed');
    }
  }

  return (
    <div>
      {/* Toolbar */}
      <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        <select
          value={kindFilter}
          onChange={e => { setKindFilter(e.target.value as '' | 'hearing' | 'deadline'); setPage(0); }}
          style={{ ...inputStyle, width: 'auto', padding: '0.4rem 0.75rem' }}
          aria-label="Filter by event type"
        >
          <option value="">All Types</option>
          <option value="hearing">Hearings</option>
          <option value="deadline">Deadlines</option>
        </select>

        <select
          value={statusFilter}
          onChange={e => { setStatusFilter(e.target.value); setPage(0); }}
          style={{ ...inputStyle, width: 'auto', padding: '0.4rem 0.75rem' }}
          aria-label="Filter by status"
        >
          <option value="">All Statuses</option>
          <option value="scheduled">Scheduled</option>
          <option value="rescheduled">Rescheduled</option>
          <option value="postponed">Postponed</option>
          <option value="cancelled">Cancelled</option>
          <option value="completed">Completed</option>
        </select>

        <div style={{ marginLeft: 'auto' }}>
          <button
            onClick={() => setShowCreate(true)}
            style={primaryBtnStyle}
            aria-label="Create a new event"
          >
            <Plus size={15} aria-hidden /> New Event
          </button>
        </div>
      </div>

      {/* Quick Reschedule Drag-and-Drop Bar */}
      <div
        style={{
          background: 'rgba(201,162,75,0.05)',
          border: '1px dashed var(--border-gold)',
          borderRadius: '0.6rem',
          padding: '0.65rem 1rem',
          marginBottom: '1.25rem',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          flexWrap: 'wrap',
        }}
      >
        <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
          <GripVertical size={14} color="var(--accent-gold)" /> Drag event card onto a quick slot to reschedule:
        </span>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {[
            { label: '+1 Day', days: 1 },
            { label: '+7 Days', days: 7 },
            { label: '+14 Days', days: 14 },
          ].map(slot => (
            <div
              key={slot.days}
              onDragOver={e => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }}
              onDrop={e => {
                e.preventDefault();
                const evId = e.dataTransfer.getData('text/plain');
                if (evId) handleDropReschedule(evId, slot.days);
              }}
              style={{
                padding: '0.3rem 0.7rem',
                borderRadius: '0.35rem',
                border: '1px solid var(--border-gold)',
                background: 'rgba(201,162,75,0.1)',
                color: 'var(--accent-gold)',
                fontSize: '0.75rem',
                fontWeight: 600,
                cursor: 'copy',
              }}
            >
              {slot.label}
            </div>
          ))}
        </div>
      </div>

      {/* Event count */}
      {!loading && (
        <p style={{ color: 'var(--text-dim)', fontSize: '0.82rem', marginBottom: '1rem' }}>
          {total} event{total !== 1 ? 's' : ''}
        </p>
      )}

      {/* States */}
      {loading && <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '2rem' }} aria-live="polite" aria-busy>Loading events…</p>}
      {error && <p role="alert" style={{ color: '#f87171', textAlign: 'center', padding: '1rem' }}>{error}</p>}

      {/* List */}
      {!loading && !error && events.length === 0 && (
        <p style={{ color: 'var(--text-dim)', textAlign: 'center', padding: '3rem', fontSize: '0.9rem' }}>
          No events found. Click <strong>New Event</strong> to add one.
        </p>
      )}

      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {events.map(ev => (
          <EventCard key={ev.id} event={ev} matterId={matterId} onUpdate={handleUpdate} />
        ))}
      </div>

      {/* Pagination */}
      {total > PAGE_SIZE && (
        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center', marginTop: '1.5rem' }} role="navigation" aria-label="Events pagination">
          <button
            disabled={page === 0}
            onClick={() => setPage(p => Math.max(0, p - 1))}
            style={secondaryBtnStyle}
            aria-label="Previous page"
          >
            ← Prev
          </button>
          <span style={{ color: 'var(--text-dim)', lineHeight: '2rem', fontSize: '0.85rem' }}>
            Page {page + 1} of {Math.ceil(total / PAGE_SIZE)}
          </span>
          <button
            disabled={(page + 1) * PAGE_SIZE >= total}
            onClick={() => setPage(p => p + 1)}
            style={secondaryBtnStyle}
            aria-label="Next page"
          >
            Next →
          </button>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <CreateEventModal matterId={matterId} onClose={() => setShowCreate(false)} onSuccess={handleCreate} />
      )}
    </div>
  );
}

// ─── Shared style tokens ──────────────────────────────────────────────────────

const labelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.8rem',
  fontWeight: 600,
  color: 'var(--text-dim)',
  textTransform: 'uppercase',
  letterSpacing: '0.06em',
  marginBottom: '0.35rem',
};

const inputStyle: React.CSSProperties = {
  display: 'block',
  width: '100%',
  background: 'var(--bg-dark)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '0.45rem',
  padding: '0.6rem 0.75rem',
  color: 'var(--text-cream)',
  fontSize: '0.9rem',
  marginBottom: '1rem',
  outline: 'none',
};

const primaryBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.55rem 1.1rem',
  background: 'var(--accent-burgundy)',
  color: 'var(--text-cream)',
  border: '1px solid var(--accent-burgundy-bright)',
  borderRadius: '0.45rem',
  fontWeight: 600,
  fontSize: '0.875rem',
  cursor: 'pointer',
};

const secondaryBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.55rem 1rem',
  background: 'transparent',
  color: 'var(--text-dim)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '0.45rem',
  fontWeight: 500,
  fontSize: '0.875rem',
  cursor: 'pointer',
};

const chipBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.3rem',
  padding: '0.3rem 0.65rem',
  background: 'transparent',
  color: 'var(--text-dim)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '0.3rem',
  fontSize: '0.78rem',
  fontWeight: 600,
  cursor: 'pointer',
};
