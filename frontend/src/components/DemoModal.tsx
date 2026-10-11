'use client';

import React, { useState, useEffect, useRef } from 'react';
import { X, Sparkles, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';

interface DemoModalProps {
  isOpen: boolean;
  onClose: () => void;
  triggerRef?: React.RefObject<HTMLElement | null>;
}

export const DemoModal: React.FC<DemoModalProps> = ({ isOpen, onClose, triggerRef }) => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [organization, setOrganization] = useState('');
  const [practiceArea, setPracticeArea] = useState('Litigation');
  const [notes, setNotes] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitted, setSubmitted] = useState(false);

  const modalRef = useRef<HTMLDivElement>(null);
  const firstInputRef = useRef<HTMLInputElement>(null);

  const handleClose = React.useCallback(() => {
    setSubmitted(false);
    setErrors({});
    onClose();
  }, [onClose]);

  // Focus management
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => {
        firstInputRef.current?.focus();
      }, 50);

      document.body.style.overflow = 'hidden';
      return () => {
        clearTimeout(timer);
        document.body.style.overflow = '';
      };
    } else {
      document.body.style.overflow = '';
      if (triggerRef?.current) {
        triggerRef.current.focus();
      }
    }
  }, [isOpen, triggerRef]);

  // Keyboard trap & Escape listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        e.preventDefault();
        handleClose();
        return;
      }

      // Tab trap
      if (e.key === 'Tab' && modalRef.current) {
        const focusables = modalRef.current.querySelectorAll<HTMLElement>(
          'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;

        const firstElement = focusables[0];
        const lastElement = focusables[focusables.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            e.preventDefault();
            lastElement.focus();
          }
        } else {
          if (document.activeElement === lastElement) {
            e.preventDefault();
            firstElement.focus();
          }
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleClose]);

  if (!isOpen) return null;

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!fullName.trim()) {
      errs.fullName = 'Full name is required.';
    }
    if (!email.trim()) {
      errs.email = 'Work email is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      errs.email = 'Please enter a valid email address.';
    }
    if (!organization.trim()) {
      errs.organization = 'Law firm or legal organization name is required.';
    }
    return errs;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }

    setErrors({});
    // Honest submission state: clear prototype notice without fabricating backend transmission
    setSubmitted(true);
  };

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onClick={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
    >
      <div
        ref={modalRef}
        className="modal-card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="demo-modal-title"
        aria-describedby="demo-modal-description"
      >
        <button
          type="button"
          onClick={handleClose}
          className="modal-close-btn"
          aria-label="Close demo request dialog"
        >
          <X size={20} />
        </button>

        {submitted ? (
          <div className="submission-success-view">
            <div className="success-icon-box">
              <CheckCircle2 size={36} className="text-gold" />
            </div>
            <h2 id="demo-modal-title" className="modal-title">
              Interface Validated
            </h2>
            <div className="honest-notice-callout">
              <ShieldAlert size={18} className="callout-icon" />
              <div>
                <strong>Frontend Prototype Mode</strong>
                <p>
                  No live demo dispatch endpoint is configured on this environment.
                  Your form inputs have passed local client-side validation, but no personal or firm data has been stored or transmitted to external servers.
                </p>
              </div>
            </div>
            <p className="success-details">
              Once connected to the LegalLens backend email or CRM service, this request will automatically schedule a product walkthrough for <strong>{organization}</strong>.
            </p>
            <button
              type="button"
              onClick={handleClose}
              className="btn-done"
            >
              Close Window
            </button>
          </div>
        ) : (
          <>
            <div className="modal-header">
              <div className="header-badge">
                <Sparkles size={13} className="text-gold" />
                <span>ENTERPRISE WALKTHROUGH</span>
              </div>
              <h2 id="demo-modal-title" className="modal-title">
                Request a Demo
              </h2>
              <p id="demo-modal-description" className="modal-subtitle">
                Explore LegalLens case intelligence, contract analysis, and discovery organization with our platform team.
              </p>
            </div>

            {/* Prototype Transparency Banner */}
            <div className="prototype-status-banner">
              <AlertCircle size={15} className="banner-icon" />
              <span>
                <strong>Prototype Notice:</strong> Submissions in this preview test client validation only. No external data is collected or logged.
              </span>
            </div>

            <form onSubmit={handleSubmit} className="demo-form" noValidate>
              <div className="form-group">
                <label htmlFor="full-name" className="form-label">
                  Full Name <span className="req">*</span>
                </label>
                <input
                  ref={firstInputRef}
                  id="full-name"
                  type="text"
                  value={fullName}
                  onChange={(e) => {
                    setFullName(e.target.value);
                    if (errors.fullName) setErrors((prev) => ({ ...prev, fullName: '' }));
                  }}
                  placeholder="e.g. Eleanor Vance, Esq."
                  className={`form-input ${errors.fullName ? 'has-error' : ''}`}
                  aria-invalid={!!errors.fullName}
                  aria-describedby={errors.fullName ? 'full-name-error' : undefined}
                />
                {errors.fullName && (
                  <span id="full-name-error" className="error-message">
                    {errors.fullName}
                  </span>
                )}
              </div>

              <div className="form-group">
                <label htmlFor="work-email" className="form-label">
                  Work Email <span className="req">*</span>
                </label>
                <input
                  id="work-email"
                  type="email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (errors.email) setErrors((prev) => ({ ...prev, email: '' }));
                  }}
                  placeholder="name@lawfirm.com"
                  className={`form-input ${errors.email ? 'has-error' : ''}`}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? 'work-email-error' : undefined}
                />
                {errors.email && (
                  <span id="work-email-error" className="error-message">
                    {errors.email}
                  </span>
                )}
              </div>

              <div className="form-row">
                <div className="form-group flex-1">
                  <label htmlFor="org-name" className="form-label">
                    Firm or Organization <span className="req">*</span>
                  </label>
                  <input
                    id="org-name"
                    type="text"
                    value={organization}
                    onChange={(e) => {
                      setOrganization(e.target.value);
                      if (errors.organization) setErrors((prev) => ({ ...prev, organization: '' }));
                    }}
                    placeholder="e.g. Vance & Sterling LLP"
                    className={`form-input ${errors.organization ? 'has-error' : ''}`}
                    aria-invalid={!!errors.organization}
                    aria-describedby={errors.organization ? 'org-name-error' : undefined}
                  />
                  {errors.organization && (
                    <span id="org-name-error" className="error-message">
                      {errors.organization}
                    </span>
                  )}
                </div>

                <div className="form-group flex-1">
                  <label htmlFor="practice-area" className="form-label">
                    Primary Practice Area
                  </label>
                  <select
                    id="practice-area"
                    value={practiceArea}
                    onChange={(e) => setPracticeArea(e.target.value)}
                    className="form-select"
                  >
                    <option value="Litigation">Commercial Litigation</option>
                    <option value="Contracts">Corporate & Transactional</option>
                    <option value="Regulatory">Regulatory & Compliance</option>
                    <option value="In-House">In-House General Counsel</option>
                    <option value="Other">Other Legal Practice</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="demo-notes" className="form-label">
                  Workflow Focus or Questions <span className="opt">(Optional)</span>
                </label>
                <textarea
                  id="demo-notes"
                  rows={2}
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Tell us about your team's legal research or contract review priorities..."
                  className="form-textarea"
                />
              </div>

              <div className="form-actions">
                <button
                  type="submit"
                  className="btn-submit-demo"
                >
                  <Sparkles size={16} className="text-gold" />
                  <span>Submit Demo Request</span>
                </button>
              </div>
            </form>
          </>
        )}
      </div>

      <style jsx>{`
        .modal-backdrop {
          position: fixed;
          inset: 0;
          background: rgba(10, 6, 7, 0.82);
          backdrop-filter: blur(12px);
          -webkit-backdrop-filter: blur(12px);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 200;
          padding: 1.5rem;
          animation: fadeIn 0.2s ease-out;
        }

        .modal-card {
          position: relative;
          width: 100%;
          max-width: 540px;
          background: #180f11;
          border: 1px solid rgba(201, 162, 75, 0.35);
          border-radius: 20px;
          box-shadow: 0 24px 60px rgba(0, 0, 0, 0.8), 0 0 30px rgba(107, 31, 40, 0.3);
          padding: 2.25rem;
          color: var(--text-cream);
          animation: scaleUp 0.25s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .modal-close-btn {
          position: absolute;
          top: 1.25rem;
          right: 1.25rem;
          background: transparent;
          border: 1px solid rgba(201, 162, 75, 0.2);
          border-radius: 50%;
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          color: var(--text-cream-muted);
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .modal-close-btn:hover {
          color: #ffffff;
          border-color: var(--accent-gold);
          background: rgba(107, 31, 40, 0.4);
        }

        .modal-header {
          margin-bottom: 1.25rem;
        }

        .header-badge {
          display: inline-flex;
          align-items: center;
          gap: 0.45rem;
          font-size: 0.68rem;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: var(--accent-gold);
          margin-bottom: 0.5rem;
        }

        .modal-title {
          font-family: var(--font-sans);
          font-size: 1.75rem;
          font-weight: 800;
          letter-spacing: -0.02em;
          color: var(--text-cream);
          margin-bottom: 0.4rem;
        }

        .modal-subtitle {
          font-size: 0.9rem;
          color: var(--text-cream-muted);
          line-height: 1.5;
        }

        .prototype-status-banner {
          display: flex;
          align-items: flex-start;
          gap: 0.55rem;
          background: rgba(201, 162, 75, 0.1);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 8px;
          padding: 0.65rem 0.85rem;
          font-size: 0.76rem;
          color: var(--text-cream-muted);
          line-height: 1.4;
          margin-bottom: 1.5rem;
        }

        .banner-icon {
          color: var(--accent-gold);
          flex-shrink: 0;
          margin-top: 0.1rem;
        }

        .demo-form {
          display: flex;
          flex-direction: column;
          gap: 1.1rem;
        }

        .form-row {
          display: flex;
          gap: 1rem;
        }

        .flex-1 {
          flex: 1;
        }

        .form-group {
          display: flex;
          flex-direction: column;
          gap: 0.4rem;
        }

        .form-label {
          font-size: 0.82rem;
          font-weight: 600;
          color: var(--text-cream);
        }

        .req {
          color: var(--accent-gold);
        }

        .opt {
          font-size: 0.74rem;
          color: var(--text-dim);
          font-weight: 400;
        }

        .form-input,
        .form-select,
        .form-textarea {
          width: 100%;
          background: rgba(20, 13, 14, 0.9);
          border: 1px solid rgba(201, 162, 75, 0.25);
          border-radius: 8px;
          padding: 0.65rem 0.85rem;
          color: var(--text-cream);
          font-size: 0.88rem;
          font-family: var(--font-sans);
          transition: border-color 0.2s ease, box-shadow 0.2s ease;
          outline: none;
        }

        .form-input:focus,
        .form-select:focus,
        .form-textarea:focus {
          border-color: var(--accent-gold);
          box-shadow: 0 0 0 2px rgba(201, 162, 75, 0.2);
        }

        .form-input.has-error {
          border-color: #e57373;
        }

        .error-message {
          font-size: 0.74rem;
          color: #ff8a80;
          font-weight: 500;
        }

        .form-actions {
          margin-top: 0.5rem;
        }

        .btn-submit-demo {
          width: 100%;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.6rem;
          padding: 0.85rem;
          background: var(--accent-burgundy);
          color: var(--text-cream);
          border: 1px solid var(--accent-gold);
          border-radius: 999px;
          font-size: 0.95rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
          box-shadow: 0 4px 16px rgba(107, 31, 40, 0.4);
        }

        .btn-submit-demo:hover {
          background: var(--accent-burgundy-bright);
          border-color: var(--accent-gold-bright);
          transform: translateY(-1px);
        }

        .btn-submit-demo:focus-visible {
          outline: 2px solid var(--accent-gold);
          outline-offset: 3px;
        }

        /* Success View */
        .submission-success-view {
          display: flex;
          flex-direction: column;
          align-items: center;
          text-align: center;
          padding: 1.5rem 0.5rem;
          gap: 1rem;
        }

        .success-icon-box {
          width: 60px;
          height: 60px;
          border-radius: 50%;
          background: rgba(201, 162, 75, 0.15);
          border: 1px solid var(--accent-gold);
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .honest-notice-callout {
          display: flex;
          align-items: flex-start;
          gap: 0.75rem;
          text-align: left;
          background: rgba(107, 31, 40, 0.25);
          border: 1px solid rgba(201, 162, 75, 0.3);
          border-radius: 10px;
          padding: 0.85rem 1rem;
          font-size: 0.8rem;
          line-height: 1.5;
          color: var(--text-cream);
        }

        .callout-icon {
          color: var(--accent-gold);
          flex-shrink: 0;
          margin-top: 0.2rem;
        }

        .success-details {
          font-size: 0.86rem;
          color: var(--text-cream-muted);
          line-height: 1.5;
        }

        .btn-done {
          margin-top: 0.5rem;
          padding: 0.75rem 2rem;
          background: rgba(20, 13, 14, 0.85);
          border: 1px solid var(--accent-gold);
          color: var(--text-cream);
          border-radius: 999px;
          font-size: 0.9rem;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s ease;
        }

        .btn-done:hover {
          background: var(--accent-burgundy);
        }

        .text-gold {
          color: var(--accent-gold);
        }

        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes scaleUp {
          from { opacity: 0; transform: scale(0.96); }
          to { opacity: 1; transform: scale(1); }
        }

        @media (max-width: 640px) {
          .modal-card {
            padding: 1.5rem;
          }
          .form-row {
            flex-direction: column;
            gap: 1.1rem;
          }
        }
      `}</style>
    </div>
  );
};
