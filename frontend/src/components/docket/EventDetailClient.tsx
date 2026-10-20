'use client';

/**
 * EventDetailClient – Detailed view for a single docket event.
 * Includes:
 *  - Event details (hearing / deadline fields)
 *  - Attached Documents manager (upload, review status toggling, download)
 *  - Reminders manager (per event or per doc, create, snooze, acknowledge, done)
 *  - Event date change history & audit trail
 */

import React, { useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import {
  ArrowLeft,
  CheckCircle2,
  XCircle,
  PauseCircle,
  RefreshCw,
  AlertTriangle,
  Download,
  Plus,
  FileCheck,
  FileText,
  Bell,
  History,
  Trash2,
  ExternalLink,
} from 'lucide-react';

import {
  getEvent,
  rescheduleEvent,
  postponeEvent,
  cancelEvent,
  verifyDeadline,
  exportIcs,
  uploadDocument,
  updateDocumentReview,
  deleteDocument,
  getDocumentDownloadUrl,
  createReminder,
  updateReminderAction,
  getEventHistory,
} from '@/lib/docketApi';

import type { components } from '@/types/docket';

type EventDetailResponse = components['schemas']['EventDetailResponse'];
type AttachedDocumentResponse = components['schemas']['AttachedDocumentResponse'];
type ReminderResponse = components['schemas']['ReminderResponse'];
type EventHistoryResponse = components['schemas']['EventHistoryResponse'];
type ConflictDecision = components['schemas']['ConflictDecision'];
type RescheduleResponse = components['schemas']['RescheduleResponse'];

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

function reviewStatusBadge(status: string) {
  switch (status) {
    case 'reviewed':
      return <span style={{ color: '#34d399', background: 'rgba(52,211,153,0.1)', border: '1px solid #34d39950', borderRadius: '0.25rem', padding: '0.15rem 0.5rem', fontSize: '0.75rem', fontWeight: 600 }}>Reviewed</span>;
    case 'changed_since_review':
      return <span style={{ color: '#f59e0b', background: 'rgba(245,158,11,0.1)', border: '1px solid #f59e0b50', borderRadius: '0.25rem', padding: '0.15rem 0.5rem', fontSize: '0.75rem', fontWeight: 600 }}>Changed Since Review</span>;
    default:
      return <span style={{ color: '#fbbf24', background: 'rgba(251,191,36,0.1)', border: '1px solid #fbbf2450', borderRadius: '0.25rem', padding: '0.15rem 0.5rem', fontSize: '0.75rem', fontWeight: 600 }}>To Review</span>;
  }
}

interface EventDetailClientProps {
  matterId: string;
  eventId: string;
}

export default function EventDetailClient({ matterId, eventId }: EventDetailClientProps) {
  const [event, setEvent] = useState<EventDetailResponse | null>(null);
  const [history, setHistory] = useState<EventHistoryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Modals & sub-state
  const [showReschedule, setShowReschedule] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [showAddReminder, setShowAddReminder] = useState(false);
  const [actionReasonModal, setActionReasonModal] = useState<'postpone' | 'cancel' | null>(null);
  const [verifying, setVerifying] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([
      getEvent(matterId, eventId),
      getEventHistory(matterId, eventId).catch(() => null),
    ])
      .then(([evData, histData]) => {
        if (!cancelled) {
          setEvent(evData);
          if (histData) setHistory(histData);
          setLoading(false);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load event details');
          setLoading(false);
        }
      });
    return () => { cancelled = true; };
  }, [matterId, eventId]);

  async function handleVerify() {
    setVerifying(true);
    try {
      const updated = await verifyDeadline(matterId, eventId);
      setEvent(prev => prev ? { ...prev, ...updated } : null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Verification failed');
    } finally {
      setVerifying(false);
    }
  }

  async function handleExportIcs() {
    try {
      const text = await exportIcs(matterId, eventId);
      const blob = new Blob([text], { type: 'text/calendar' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `event-${eventId}.ics`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Export failed');
    }
  }

  if (loading) {
    return (
      <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: 'var(--text-dim)' }} aria-live="polite">
        Loading event details…
      </div>
    );
  }

  if (error || !event) {
    return (
      <div style={{ padding: '3rem 1.5rem', textAlign: 'center', color: '#f87171' }} role="alert">
        {error || 'Event not found'}
      </div>
    );
  }

  const isActive = !['cancelled', 'completed'].includes(event.status);
  const isDeadline = event.kind === 'deadline';

  return (
    <div style={{ maxWidth: 1100, margin: '0 auto', padding: '2rem 1.5rem' }}>
      {/* Back button */}
      <Link
        href={`/docket/${matterId}`}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          color: 'var(--text-dim)',
          textDecoration: 'none',
          fontSize: '0.85rem',
          marginBottom: '1.5rem',
        }}
      >
        <ArrowLeft size={15} /> Back to Events & Agenda
      </Link>

      {/* Main Event Header Card */}
      <div
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-gold)',
          borderRadius: '0.875rem',
          padding: '1.75rem',
          marginBottom: '2rem',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '1rem' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem', marginBottom: '0.5rem' }}>
              <span
                style={{
                  fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase',
                  letterSpacing: '0.08em',
                  color: statusColor(event.status),
                  background: `${statusColor(event.status)}20`,
                  border: `1px solid ${statusColor(event.status)}50`,
                  borderRadius: '0.25rem', padding: '0.2rem 0.5rem',
                }}
              >
                {event.status}
              </span>
              <span
                style={{
                  fontSize: '0.75rem', fontWeight: 600, textTransform: 'uppercase',
                  color: event.kind === 'hearing' ? 'var(--accent-burgundy-bright)' : '#818cf8',
                }}
              >
                {event.kind}
              </span>
              <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>
                Priority: {event.priority}
              </span>
            </div>

            <h1 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.75rem', color: 'var(--text-cream)', margin: '0 0 0.5rem 0' }}>
              {event.title}
            </h1>

            {event.notes && (
              <p style={{ color: 'var(--text-dim)', fontSize: '0.9rem', marginBottom: '0.75rem', maxWidth: 650 }}>
                {event.notes}
              </p>
            )}
          </div>

          <div style={{ textAlign: 'right' }}>
            <p style={{ color: 'var(--accent-gold)', fontSize: '1.15rem', fontWeight: 700, margin: 0 }}>
              {new Date(event.starts_at).toLocaleDateString('en-US', {
                weekday: 'long', month: 'short', day: 'numeric', year: 'numeric',
              })}
            </p>
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', margin: '0.25rem 0 0' }}>
              {new Date(event.starts_at).toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })}
              {' '}(Court Timezone: {event.timezone})
            </p>
          </div>
        </div>

        {/* Specific Hearing / Deadline details grid */}
        <div
          style={{
            marginTop: '1.25rem',
            paddingTop: '1.25rem',
            borderTop: '1px solid var(--border-subtle)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            fontSize: '0.85rem',
          }}
        >
          {event.kind === 'hearing' && (
            <>
              <div>
                <span style={fieldLabelStyle}>Court</span>
                <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0' }}>{event.court_name || '—'}</p>
              </div>
              <div>
                <span style={fieldLabelStyle}>Courtroom & Judge</span>
                <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0' }}>
                  {event.courtroom ? `Rm ${event.courtroom} · ` : ''}{event.judge || '—'}
                </p>
              </div>
              <div>
                <span style={fieldLabelStyle}>Mode</span>
                <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0', textTransform: 'capitalize' }}>
                  {event.mode || 'In Person'}
                  {event.virtual_link && (
                    <a
                      href={event.virtual_link}
                      target="_blank"
                      rel="noreferrer"
                      style={{ marginLeft: '0.5rem', color: 'var(--accent-gold)', display: 'inline-flex', alignItems: 'center' }}
                    >
                      <ExternalLink size={12} />
                    </a>
                  )}
                </p>
              </div>
            </>
          )}

          {isDeadline && (
            <>
              <div>
                <span style={fieldLabelStyle}>Deadline Type</span>
                <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0' }}>{event.deadline_type || 'General'}</p>
              </div>
              <div>
                <span style={fieldLabelStyle}>Verification Status</span>
                <p style={{ color: event.verified_by ? '#34d399' : 'var(--text-dim)', margin: '0.2rem 0 0', display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
                  {event.verified_by ? (
                    <>
                      <CheckCircle2 size={13} /> Verified by {event.verified_by}
                    </>
                  ) : (
                    'Unverified'
                  )}
                </p>
              </div>
              <div>
                <span style={fieldLabelStyle}>Source Rule/Order</span>
                <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0' }}>{event.source_description || '—'}</p>
              </div>
            </>
          )}
        </div>

        {/* Action bar */}
        <div style={{ display: 'flex', gap: '0.6rem', flexWrap: 'wrap', marginTop: '1.5rem', paddingTop: '1rem', borderTop: '1px solid var(--border-subtle)' }}>
          {isActive && (
            <>
              <button onClick={() => setShowReschedule(true)} style={primaryActionBtnStyle}>
                <RefreshCw size={13} aria-hidden /> Reschedule
              </button>
              <button onClick={() => setActionReasonModal('postpone')} style={secondaryActionBtnStyle}>
                <PauseCircle size={13} aria-hidden /> Postpone
              </button>
              <button onClick={() => setActionReasonModal('cancel')} style={{ ...secondaryActionBtnStyle, color: '#f87171', borderColor: '#f8717140' }}>
                <XCircle size={13} aria-hidden /> Cancel
              </button>
              {isDeadline && !event.verified_by && (
                <button onClick={handleVerify} disabled={verifying} style={{ ...secondaryActionBtnStyle, color: '#34d399', borderColor: '#34d39940' }}>
                  <FileCheck size={13} aria-hidden /> {verifying ? 'Verifying…' : 'Verify Deadline'}
                </button>
              )}
            </>
          )}
          <button onClick={handleExportIcs} style={secondaryActionBtnStyle}>
            <Download size={13} aria-hidden /> Export .ics
          </button>
        </div>
      </div>

      {/* Grid: Attached Documents & Reminders */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(450px, 1fr))', gap: '2rem', alignItems: 'start', marginBottom: '2rem' }}>
        {/* ── Section: Attached Documents ── */}
        <section
          aria-label="Attached Documents"
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '0.875rem',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <FileText size={17} color="var(--accent-gold)" aria-hidden />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-cream)', margin: 0 }}>
                Attached Documents ({event.documents?.length ?? 0})
              </h2>
            </div>
            {isActive && (
              <button onClick={() => setShowUpload(true)} style={chipActionBtnStyle}>
                <Plus size={13} /> Attach File
              </button>
            )}
          </div>

          {(!event.documents || event.documents.length === 0) ? (
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', textAlign: 'center', padding: '1.5rem 0' }}>
              No documents attached to this event.
            </p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {event.documents.map(doc => (
                <DocumentRow
                  key={doc.id}
                  doc={doc}
                  matterId={matterId}
                  eventId={eventId}
                  isActive={isActive}
                  onStatusUpdate={updated => {
                    setEvent(prev => prev ? {
                      ...prev,
                      documents: prev.documents.map(d => d.id === updated.id ? updated : d),
                    } : null);
                  }}
                  onDelete={deletedId => {
                    setEvent(prev => prev ? {
                      ...prev,
                      documents: prev.documents.filter(d => d.id !== deletedId),
                    } : null);
                  }}
                />
              ))}
            </ul>
          )}
        </section>

        {/* ── Section: Reminders ── */}
        <section
          aria-label="Reminders"
          style={{
            background: 'var(--bg-card)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '0.875rem',
            padding: '1.5rem',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Bell size={17} color="var(--accent-gold)" aria-hidden />
              <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-cream)', margin: 0 }}>
                Reminders ({event.reminders?.length ?? 0})
              </h2>
            </div>
            {isActive && (
              <button onClick={() => setShowAddReminder(true)} style={chipActionBtnStyle}>
                <Plus size={13} /> Add Reminder
              </button>
            )}
          </div>

          {(!event.reminders || event.reminders.length === 0) ? (
            <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem', textAlign: 'center', padding: '1.5rem 0' }}>
              No reminders scheduled.
            </p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {event.reminders.map(rem => (
                <ReminderRow
                  key={rem.id}
                  rem={rem}
                  matterId={matterId}
                  eventId={eventId}
                  isActive={isActive}
                  onUpdate={updated => {
                    setEvent(prev => prev ? {
                      ...prev,
                      reminders: prev.reminders.map(r => r.id === updated.id ? updated : r),
                    } : null);
                  }}
                />
              ))}
            </ul>
          )}
        </section>
      </div>

      {/* ── Section: History & Audit Trail ── */}
      <section
        aria-label="Audit and History Trail"
        style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-subtle)',
          borderRadius: '0.875rem',
          padding: '1.5rem',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.25rem' }}>
          <History size={17} color="var(--accent-gold)" aria-hidden />
          <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--text-cream)', margin: 0 }}>
            History & Audit Trail
          </h2>
        </div>

        {(!history || (history.changes.length === 0 && history.audit_trail.length === 0)) ? (
          <p style={{ color: 'var(--text-dim)', fontSize: '0.85rem' }}>No history records yet.</p>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {history.changes.length > 0 && (
              <div>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  Date / Schedule Changes
                </h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {history.changes.map(ch => (
                    <li key={ch.id} style={{ fontSize: '0.82rem', padding: '0.6rem 0.8rem', background: 'var(--bg-dark)', borderRadius: '0.4rem', border: '1px solid var(--border-subtle)' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-dim)' }}>
                        <span>By {ch.actor}</span>
                        <span>{new Date(ch.created_at).toLocaleString()}</span>
                      </div>
                      <p style={{ color: 'var(--text-cream)', margin: '0.3rem 0 0' }}>
                        Changed from {ch.old_starts_at ? new Date(ch.old_starts_at).toLocaleString() : 'initial'} → {ch.new_starts_at ? new Date(ch.new_starts_at).toLocaleString() : 'none'}
                      </p>
                      <p style={{ color: 'var(--accent-gold)', margin: '0.15rem 0 0', fontStyle: 'italic' }}>
                        Reason: {ch.reason}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {history.audit_trail.length > 0 && (
              <div style={{ marginTop: '0.5rem' }}>
                <h3 style={{ fontSize: '0.85rem', color: 'var(--text-dim)', textTransform: 'uppercase', marginBottom: '0.5rem' }}>
                  Audit Trail Events
                </h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: 0, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {history.audit_trail.map((log, idx) => {
                    const action = String(log.action ?? 'Action');
                    const createdAt = log.created_at ? new Date(String(log.created_at)).toLocaleString() : '';
                    const actor = String(log.actor ?? 'system');
                    const reason = log.reason ? String(log.reason) : null;
                    return (
                      <li key={idx} style={{ fontSize: '0.82rem', padding: '0.6rem 0.8rem', background: 'var(--bg-dark)', borderRadius: '0.4rem', border: '1px solid var(--border-subtle)' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', color: 'var(--text-dim)' }}>
                          <span style={{ fontWeight: 600, color: 'var(--accent-gold)' }}>{action}</span>
                          <span>{createdAt}</span>
                        </div>
                        <p style={{ color: 'var(--text-cream)', margin: '0.2rem 0 0' }}>Actor: {actor}</p>
                        {reason && <p style={{ color: 'var(--text-dim)', margin: '0.1rem 0 0' }}>Reason: {reason}</p>}
                      </li>
                    );
                  })}
                </ul>
              </div>
            )}
          </div>
        )}
      </section>

      {/* Reschedule Modal */}
      {showReschedule && (
        <RescheduleModal
          event={event}
          matterId={matterId}
          onClose={() => setShowReschedule(false)}
          onSuccess={res => {
            setShowReschedule(false);
            setEvent(prev => prev ? { ...prev, ...res.event } : null);
          }}
        />
      )}

      {/* Postpone/Cancel Reason Modal */}
      {actionReasonModal && (
        <ReasonModal
          action={actionReasonModal}
          event={event}
          matterId={matterId}
          onClose={() => setActionReasonModal(null)}
          onSuccess={updated => {
            setActionReasonModal(null);
            setEvent(prev => prev ? { ...prev, ...updated } : null);
          }}
        />
      )}

      {/* Upload Document Modal */}
      {showUpload && (
        <UploadDocumentModal
          matterId={matterId}
          eventId={eventId}
          onClose={() => setShowUpload(false)}
          onSuccess={newDoc => {
            setShowUpload(false);
            setEvent(prev => prev ? { ...prev, documents: [...prev.documents, newDoc] } : null);
          }}
        />
      )}

      {/* Add Reminder Modal */}
      {showAddReminder && (
        <AddReminderModal
          matterId={matterId}
          eventId={eventId}
          documents={event.documents ?? []}
          onClose={() => setShowAddReminder(false)}
          onSuccess={newRem => {
            setShowAddReminder(false);
            setEvent(prev => prev ? { ...prev, reminders: [...prev.reminders, newRem] } : null);
          }}
        />
      )}
    </div>
  );
}

// ─── DocumentRow ──────────────────────────────────────────────────────────────

interface DocumentRowProps {
  doc: AttachedDocumentResponse;
  matterId: string;
  eventId: string;
  isActive: boolean;
  onStatusUpdate: (d: AttachedDocumentResponse) => void;
  onDelete: (id: string) => void;
}

function DocumentRow({ doc, matterId, eventId, isActive, onStatusUpdate, onDelete }: DocumentRowProps) {
  const [updating, setUpdating] = useState(false);

  async function handleToggleReview() {
    setUpdating(true);
    const nextStatus = doc.review_status === 'reviewed' ? 'to_review' : 'reviewed';
    try {
      const res = await updateDocumentReview(matterId, eventId, doc.id, nextStatus);
      onStatusUpdate(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Update failed');
    } finally {
      setUpdating(false);
    }
  }

  async function handleDelete() {
    if (!confirm(`Delete attached document "${doc.display_name}"?`)) return;
    try {
      await deleteDocument(matterId, eventId, doc.id);
      onDelete(doc.id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Delete failed');
    }
  }

  const downloadUrl = getDocumentDownloadUrl(matterId, eventId, doc.id);

  return (
    <li
      style={{
        background: 'var(--bg-dark)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '0.5rem',
        padding: '0.75rem 1rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '0.75rem',
        flexWrap: 'wrap',
      }}
    >
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <span style={{ fontWeight: 600, color: 'var(--text-cream)', fontSize: '0.9rem' }}>
            {doc.display_name}
          </span>
          {reviewStatusBadge(doc.review_status)}
        </div>
        <p style={{ color: 'var(--text-dim)', fontSize: '0.75rem', margin: 0 }}>
          Attached {new Date(doc.created_at).toLocaleDateString()}
          {doc.reviewed_by ? ` · Reviewed by ${doc.reviewed_by}` : ''}
        </p>
      </div>

      <div style={{ display: 'flex', gap: '0.4rem', alignItems: 'center' }}>
        <a
          href={downloadUrl}
          target="_blank"
          rel="noreferrer"
          style={{
            padding: '0.3rem 0.6rem',
            borderRadius: '0.3rem',
            background: 'transparent',
            border: '1px solid var(--border-subtle)',
            color: 'var(--text-dim)',
            fontSize: '0.78rem',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.3rem',
          }}
        >
          <Download size={12} /> Download
        </a>

        {isActive && (
          <>
            <button
              onClick={handleToggleReview}
              disabled={updating}
              style={{
                padding: '0.3rem 0.6rem',
                borderRadius: '0.3rem',
                background: 'transparent',
                border: '1px solid var(--border-subtle)',
                color: doc.review_status === 'reviewed' ? '#fbbf24' : '#34d399',
                fontSize: '0.78rem',
                cursor: 'pointer',
                fontWeight: 600,
              }}
            >
              {updating ? '…' : doc.review_status === 'reviewed' ? 'Mark To Review' : 'Mark Reviewed'}
            </button>

            <button
              onClick={handleDelete}
              style={{
                padding: '0.3rem',
                borderRadius: '0.3rem',
                background: 'transparent',
                border: 'none',
                color: '#f87171',
                cursor: 'pointer',
              }}
              title="Delete document"
            >
              <Trash2 size={14} />
            </button>
          </>
        )}
      </div>
    </li>
  );
}

// ─── ReminderRow ──────────────────────────────────────────────────────────────

interface ReminderRowProps {
  rem: ReminderResponse;
  matterId: string;
  eventId: string;
  isActive: boolean;
  onUpdate: (r: ReminderResponse) => void;
}

function ReminderRow({ rem, matterId, eventId, isActive, onUpdate }: ReminderRowProps) {
  const [acting, setActing] = useState(false);

  async function handleAction(actionName: 'acknowledge' | 'done' | 'cancel' | 'snooze', snoozeMinutes?: number) {
    setActing(true);
    try {
      const snoozeUntil = (actionName === 'snooze' && snoozeMinutes)
        ? new Date(Date.now() + snoozeMinutes * 60 * 1000).toISOString()
        : undefined;
      const res = await updateReminderAction(matterId, eventId, rem.id, {
        action: actionName,
        snooze_until: snoozeUntil,
      });
      onUpdate(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Action failed');
    } finally {
      setActing(false);
    }
  }

  const isMissed = rem.state === 'missed';

  return (
    <li
      style={{
        background: isMissed ? 'rgba(248,113,113,0.08)' : 'var(--bg-dark)',
        border: `1px solid ${isMissed ? '#f8717150' : 'var(--border-subtle)'}`,
        borderRadius: '0.5rem',
        padding: '0.75rem 1rem',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '0.5rem', flexWrap: 'wrap' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <span
              style={{
                fontSize: '0.72rem', fontWeight: 700, textTransform: 'uppercase',
                color: isMissed ? '#f87171' : rem.state === 'done' ? '#34d399' : 'var(--accent-gold)',
              }}
            >
              {rem.state}
            </span>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
              {rem.anchor === 'offset_before_event'
                ? `${rem.days_before ?? 0}d before at ${rem.time_of_day ?? '09:00'}`
                : `Fixed: ${rem.fire_at ? new Date(rem.fire_at).toLocaleString() : 'not set'}`}
            </span>
          </div>

          <p style={{ color: 'var(--text-cream)', fontSize: '0.82rem', margin: 0 }}>
            {rem.document_id ? 'Document Review Reminder' : 'Event Reminder'}
            {rem.repeat_rule !== 'none' && ` · Repeats ${rem.repeat_rule}`}
          </p>
        </div>

        {isActive && rem.state !== 'done' && rem.state !== 'cancelled' && (
          <div style={{ display: 'flex', gap: '0.35rem', flexWrap: 'wrap' }}>
            <button
              onClick={() => handleAction('acknowledge')}
              disabled={acting}
              style={chipBtnStyle}
            >
              Ack
            </button>
            <button
              onClick={() => handleAction('snooze', 60)}
              disabled={acting}
              style={chipBtnStyle}
            >
              +1h
            </button>
            <button
              onClick={() => handleAction('done')}
              disabled={acting}
              style={{ ...chipBtnStyle, color: '#34d399' }}
            >
              Done
            </button>
            <button
              onClick={() => handleAction('cancel')}
              disabled={acting}
              style={{ ...chipBtnStyle, color: '#f87171' }}
            >
              Cancel
            </button>
          </div>
        )}
      </div>
    </li>
  );
}

// ─── UploadDocumentModal ──────────────────────────────────────────────────────

interface UploadDocumentModalProps {
  matterId: string;
  eventId: string;
  onClose: () => void;
  onSuccess: (d: AttachedDocumentResponse) => void;
}

function UploadDocumentModal({ matterId, eventId, onClose, onSuccess }: UploadDocumentModalProps) {
  const [displayName, setDisplayName] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!displayName.trim()) { setError('Display name is required'); return; }
    setLoading(true);
    try {
      const fd = new FormData();
      fd.append('display_name', displayName.trim());
      if (file) fd.append('file', file);
      const res = await uploadDocument(matterId, eventId, fd);
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
      setLoading(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" style={modalOverlayStyle}>
      <div style={modalCardStyle}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', color: 'var(--accent-gold)', marginBottom: '1rem' }}>
          Attach Document
        </h2>
        <form onSubmit={handleSubmit}>
          <label style={labelStyle} htmlFor="doc-display-name">Display Name *</label>
          <input
            id="doc-display-name"
            value={displayName}
            onChange={e => setDisplayName(e.target.value)}
            placeholder="e.g. Motion for Summary Judgment"
            style={inputStyle}
            required
          />

          <label style={labelStyle} htmlFor="doc-file">Select File</label>
          <input
            id="doc-file"
            type="file"
            onChange={e => {
              if (e.target.files?.[0]) {
                setFile(e.target.files[0]);
                if (!displayName) setDisplayName(e.target.files[0].name);
              }
            }}
            style={{ ...inputStyle, padding: '0.4rem' }}
          />

          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button type="submit" disabled={loading} style={primaryBtnStyle}>
              {loading ? 'Uploading…' : 'Attach Document'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── AddReminderModal ─────────────────────────────────────────────────────────

interface AddReminderModalProps {
  matterId: string;
  eventId: string;
  documents: AttachedDocumentResponse[];
  onClose: () => void;
  onSuccess: (r: ReminderResponse) => void;
}

function AddReminderModal({ matterId, eventId, documents, onClose, onSuccess }: AddReminderModalProps) {
  const [anchor, setAnchor] = useState<'offset_before_event' | 'fixed_datetime'>('offset_before_event');
  const [daysBefore, setDaysBefore] = useState(1);
  const [timeOfDay, setTimeOfDay] = useState('09:00');
  const [fireAt, setFireAt] = useState('');
  const [repeatRule, setRepeatRule] = useState('none');
  const [documentId, setDocumentId] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const data: any = {
        anchor,
        repeat_rule: repeatRule,
        document_id: documentId || null,
        ...(anchor === 'offset_before_event'
          ? { days_before: Number(daysBefore), time_of_day: timeOfDay }
          : { fire_at: new Date(fireAt).toISOString() }),
      };
      const res = await createReminder(matterId, eventId, data);
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to create reminder');
      setLoading(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" style={modalOverlayStyle}>
      <div style={modalCardStyle}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', color: 'var(--accent-gold)', marginBottom: '1rem' }}>
          Schedule Reminder
        </h2>
        <form onSubmit={handleSubmit}>
          <label style={labelStyle}>Target</label>
          <select value={documentId} onChange={e => setDocumentId(e.target.value)} style={inputStyle}>
            <option value="">Event itself</option>
            {documents.map(d => (
              <option key={d.id} value={d.id}>Document: {d.display_name}</option>
            ))}
          </select>

          <label style={labelStyle}>Anchor Type</label>
          <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1rem' }}>
            {(['offset_before_event', 'fixed_datetime'] as const).map(a => (
              <button
                key={a}
                type="button"
                onClick={() => setAnchor(a)}
                style={{
                  flex: 1, padding: '0.45rem',
                  borderRadius: '0.4rem',
                  border: anchor === a ? '2px solid var(--accent-gold)' : '1px solid var(--border-subtle)',
                  background: anchor === a ? 'rgba(201,162,75,0.1)' : 'transparent',
                  color: anchor === a ? 'var(--accent-gold)' : 'var(--text-dim)',
                  cursor: 'pointer',
                  fontSize: '0.82rem',
                }}
              >
                {a === 'offset_before_event' ? 'Days Before Event' : 'Fixed Date/Time'}
              </button>
            ))}
          </div>

          {anchor === 'offset_before_event' ? (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
              <div>
                <label style={labelStyle} htmlFor="rem-days">Days Before</label>
                <input
                  id="rem-days"
                  type="number"
                  min={0}
                  max={365}
                  value={daysBefore}
                  onChange={e => setDaysBefore(Number(e.target.value))}
                  style={inputStyle}
                  required
                />
              </div>
              <div>
                <label style={labelStyle} htmlFor="rem-time">Time of Day (Court TZ)</label>
                <input
                  id="rem-time"
                  type="time"
                  value={timeOfDay}
                  onChange={e => setTimeOfDay(e.target.value)}
                  style={inputStyle}
                  required
                />
              </div>
            </div>
          ) : (
            <div>
              <label style={labelStyle} htmlFor="rem-fire-at">Fire At (Date & Time) *</label>
              <input
                id="rem-fire-at"
                type="datetime-local"
                value={fireAt}
                onChange={e => setFireAt(e.target.value)}
                style={inputStyle}
                required
              />
            </div>
          )}

          <label style={labelStyle}>Repeat Rule</label>
          <select value={repeatRule} onChange={e => setRepeatRule(e.target.value)} style={inputStyle}>
            <option value="none">None (fire once)</option>
            <option value="daily_until_event">Daily until event date</option>
            {documentId && <option value="daily_until_reviewed">Daily until document reviewed</option>}
          </select>

          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button type="submit" disabled={loading} style={primaryBtnStyle}>
              {loading ? 'Creating…' : 'Add Reminder'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Reschedule Modal ─────────────────────────────────────────────────────────

interface RescheduleModalProps {
  event: EventDetailResponse;
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

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!newDate || !reason.trim()) { setError('New date and reason are required'); return; }
    setLoading(true);
    try {
      const conflictResMap: Record<string, ConflictDecision> = {};
      Object.entries(resolutions).forEach(([rId, action]) => {
        conflictResMap[rId] = { action };
      });
      const payload = {
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
      setError(err instanceof Error ? err.message : 'Reschedule failed');
      setLoading(false);
    }
  }

  return (
    <div role="dialog" aria-modal="true" style={modalOverlayStyle}>
      <div style={modalCardStyle}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.25rem', color: 'var(--accent-gold)', marginBottom: '1rem' }}>
          Reschedule Event
        </h2>
        <form onSubmit={handleSubmit}>
          <label style={labelStyle} htmlFor="reschedule-date">New Date & Time *</label>
          <input
            id="reschedule-date"
            ref={firstInputRef}
            type="datetime-local"
            value={newDate}
            onChange={e => setNewDate(e.target.value)}
            style={inputStyle}
            required
          />

          <label style={labelStyle} htmlFor="reschedule-reason-input">Reason *</label>
          <textarea
            id="reschedule-reason-input"
            rows={3}
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder="e.g. Court ordered continuance"
            style={{ ...inputStyle, resize: 'vertical' }}
            required
          />

          {conflicts.length > 0 && (
            <div style={{ marginBottom: '1rem' }}>
              <p style={{ color: '#f59e0b', fontSize: '0.85rem', marginBottom: '0.5rem' }}>
                <AlertTriangle size={14} style={{ display: 'inline', marginRight: 4 }} />
                {conflicts.length} fixed reminder(s) conflict. Choose action:
              </p>
              {conflicts.map(c => (
                <div key={c.reminder_id} style={{ marginBottom: '0.75rem', padding: '0.6rem', background: 'var(--bg-dark)', borderRadius: '0.4rem' }}>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-cream)', marginBottom: '0.4rem' }}>
                    Fires at: {c.current_fire_at ? new Date(c.current_fire_at).toLocaleString() : 'unknown'} · {c.issue}
                  </p>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {(['shift', 'keep', 'cancel'] as const).map(opt => (
                      <button
                        key={opt}
                        type="button"
                        onClick={() => setResolutions(r => ({ ...r, [c.reminder_id]: opt }))}
                        style={{
                          padding: '0.25rem 0.6rem',
                          borderRadius: '0.3rem',
                          fontSize: '0.78rem',
                          border: resolutions[c.reminder_id] === opt ? '2px solid var(--accent-gold)' : '1px solid var(--border-subtle)',
                          background: resolutions[c.reminder_id] === opt ? 'var(--accent-gold)' : 'transparent',
                          color: resolutions[c.reminder_id] === opt ? '#140d0e' : 'var(--text-cream)',
                          cursor: 'pointer',
                          fontWeight: 600,
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

          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button type="submit" disabled={loading} style={primaryBtnStyle}>
              {loading ? 'Saving…' : conflicts.length > 0 ? 'Confirm Resolution' : 'Reschedule'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── ReasonModal ─────────────────────────────────────────────────────────────

interface ReasonModalProps {
  action: 'postpone' | 'cancel';
  event: EventDetailResponse;
  matterId: string;
  onClose: () => void;
  onSuccess: (e: components['schemas']['EventResponse']) => void;
}

function ReasonModal({ action, event, matterId, onClose, onSuccess }: ReasonModalProps) {
  const [reason, setReason] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!reason.trim()) { setError('Reason is required'); return; }
    setLoading(true);
    try {
      const fn = action === 'postpone' ? postponeEvent : cancelEvent;
      const res = await fn(matterId, event.id, reason.trim());
      onSuccess(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Action failed');
      setLoading(false);
    }
  }

  const title = action === 'postpone' ? 'Postpone Event' : 'Cancel Event';
  return (
    <div role="dialog" aria-modal="true" style={modalOverlayStyle}>
      <div style={modalCardStyle}>
        <h2 style={{ fontFamily: 'var(--font-serif)', fontSize: '1.2rem', color: action === 'cancel' ? '#f87171' : '#f59e0b', marginBottom: '0.75rem' }}>
          {title}
        </h2>
        <form onSubmit={handleSubmit}>
          <label style={labelStyle} htmlFor="reason-box">Reason *</label>
          <textarea
            id="reason-box"
            rows={3}
            value={reason}
            onChange={e => setReason(e.target.value)}
            placeholder={`Why is this event being ${action}d?`}
            style={{ ...inputStyle, resize: 'vertical' }}
            required
          />
          {error && <p role="alert" style={{ color: '#f87171', fontSize: '0.85rem', marginBottom: '0.75rem' }}>{error}</p>}
          <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'flex-end', marginTop: '1rem' }}>
            <button type="button" onClick={onClose} style={secondaryBtnStyle}>Cancel</button>
            <button
              type="submit"
              disabled={loading}
              style={{ ...primaryBtnStyle, background: action === 'cancel' ? '#991b1b' : 'var(--accent-burgundy)' }}
            >
              {loading ? 'Processing…' : title}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Style Tokens ─────────────────────────────────────────────────────────────

const fieldLabelStyle: React.CSSProperties = {
  display: 'block',
  fontSize: '0.72rem',
  fontWeight: 600,
  color: 'var(--text-dim)',
  textTransform: 'uppercase',
  letterSpacing: '0.07em',
};

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
  padding: '0.55rem 0.75rem',
  color: 'var(--text-cream)',
  fontSize: '0.88rem',
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
  fontSize: '0.85rem',
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
  fontSize: '0.85rem',
  cursor: 'pointer',
};

const primaryActionBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.45rem 0.85rem',
  background: 'var(--accent-burgundy)',
  color: 'var(--text-cream)',
  border: '1px solid var(--accent-burgundy-bright)',
  borderRadius: '0.35rem',
  fontWeight: 600,
  fontSize: '0.82rem',
  cursor: 'pointer',
};

const secondaryActionBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.35rem',
  padding: '0.45rem 0.85rem',
  background: 'transparent',
  color: 'var(--text-dim)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '0.35rem',
  fontWeight: 600,
  fontSize: '0.82rem',
  cursor: 'pointer',
};

const chipActionBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.3rem',
  padding: '0.35rem 0.7rem',
  background: 'rgba(201,162,75,0.1)',
  border: '1px solid var(--border-gold)',
  borderRadius: '0.35rem',
  color: 'var(--accent-gold)',
  fontSize: '0.8rem',
  fontWeight: 600,
  cursor: 'pointer',
};

const chipBtnStyle: React.CSSProperties = {
  display: 'inline-flex',
  alignItems: 'center',
  gap: '0.3rem',
  padding: '0.25rem 0.55rem',
  background: 'transparent',
  color: 'var(--text-dim)',
  border: '1px solid var(--border-subtle)',
  borderRadius: '0.3rem',
  fontSize: '0.75rem',
  fontWeight: 600,
  cursor: 'pointer',
};

const modalOverlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  zIndex: 50,
  background: 'rgba(0,0,0,0.65)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
  padding: '1rem',
};

const modalCardStyle: React.CSSProperties = {
  background: 'var(--bg-card)',
  border: '1px solid var(--border-gold)',
  borderRadius: '0.875rem',
  padding: '1.75rem',
  width: '100%',
  maxWidth: 500,
  maxHeight: '90vh',
  overflowY: 'auto',
};
