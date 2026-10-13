'use client';

import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Loader2, X } from 'lucide-react';

interface DocumentUploadPanelProps {
  currentCaseId: string;
  onUploadSuccess: (caseId: string) => void;
  onClose?: () => void;
}

const SUPPORTED_EXTENSIONS = ['.pdf', '.docx', '.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp'];
const MAX_BYTES = 150 * 1024 * 1024; // 150 MB

export const DocumentUploadPanel: React.FC<DocumentUploadPanelProps> = ({
  currentCaseId,
  onUploadSuccess,
  onClose,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [targetCaseId, setTargetCaseId] = useState<string>(currentCaseId || 'case_investigation');
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processingStage, setProcessingStage] = useState<string>('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    status?: string;
    message?: string;
    neo4j_synced?: boolean;
    metrics?: { entities_extracted?: number; relationships_extracted?: number };
  } | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    setSuccessInfo(null);

    const ext = '.' + file.name.split('.').pop()?.toLowerCase();
    if (!SUPPORTED_EXTENSIONS.includes(ext)) {
      setErrorMessage(`Unsupported file format '${ext}'. Supported formats: ${SUPPORTED_EXTENSIONS.join(', ')}`);
      return;
    }

    if (file.size > MAX_BYTES) {
      setErrorMessage(`File exceeds 150MB maximum size limit (${(file.size / (1024 * 1024)).toFixed(1)} MB).`);
      return;
    }

    if (file.size === 0) {
      setErrorMessage('Selected file is empty (0 bytes).');
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const handleUploadSubmit = async () => {
    if (!selectedFile) return;
    const cid = targetCaseId.trim();
    if (!cid) {
      setErrorMessage('Case identifier is required.');
      return;
    }

    setIsProcessing(true);
    setErrorMessage(null);
    setProcessingStage('Uploading document…');

    try {
      // 1. Submit upload — returns immediately with a job_id
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('case_id', cid);

      const uploadRes = await fetch(`${API_BASE}/api/v1/graph/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!uploadRes.ok) {
        let errText = `Upload failed (${uploadRes.status})`;
        try {
          const errJson = await uploadRes.json();
          if (errJson.detail) errText = errJson.detail;
        } catch { /* ignore */ }
        throw new Error(errText);
      }

      const { job_id } = await uploadRes.json();
      setProcessingStage('Document received — starting extraction (this takes several minutes for large documents)…');

      // 2. Poll job status until terminal
      const POLL_INTERVAL_MS = 4000;
      const MAX_POLLS = 300; // 20 min ceiling

      for (let i = 0; i < MAX_POLLS; i++) {
        await new Promise((r) => setTimeout(r, POLL_INTERVAL_MS));

        let jobStatus: { status: string; stage: string; metrics?: Record<string, number | boolean>; error?: string | null };
        try {
          const pollRes = await fetch(`${API_BASE}/api/v1/graph/jobs/${encodeURIComponent(job_id)}`, {
            headers: { 'Accept': 'application/json' },
          });
          if (!pollRes.ok) continue; // transient — keep polling
          jobStatus = await pollRes.json();
        } catch {
          continue; // network blip — keep polling
        }

        // Update stage message
        if (jobStatus.stage) {
          setProcessingStage(jobStatus.stage);
        }

        if (jobStatus.status === 'SUCCESS' || jobStatus.status === 'PARTIAL') {
          const metrics = jobStatus.metrics || {};
          setSuccessInfo({
            status: jobStatus.status,
            message: jobStatus.stage,
            neo4j_synced: Boolean(metrics.neo4j_synced),
            metrics: {
              entities_extracted: Number(metrics.entities_extracted ?? 0),
              relationships_extracted: Number(metrics.relationships_extracted ?? 0),
            },
          });
          setSelectedFile(null);
          setTimeout(() => {
            onUploadSuccess(cid);
            if (onClose) onClose();
          }, 1200);
          return;
        }

        if (jobStatus.status === 'FAILED') {
          throw new Error(jobStatus.error || jobStatus.stage || 'Extraction pipeline failed.');
        }

        // PENDING / PROCESSING — keep polling
      }

      // Timed out on the frontend — the job may still be running
      throw new Error(
        'Processing is taking longer than expected. The job is still running in the background. ' +
        'Reload the page in a few minutes — your graph may already be available.'
      );

    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'An unexpected error occurred during processing.';
      setErrorMessage(msg);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="kg-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="upload-modal-title">
      <div className="kg-modal-card">
        <div className="kg-modal-header">
          <div className="kg-modal-title" id="upload-modal-title">
            Upload Legal Document
          </div>
          {onClose && (
            <button type="button" className="kg-tool-btn" onClick={onClose} aria-label="Close modal">
              <X size={18} />
            </button>
          )}
        </div>

        <div className="kg-modal-body">
          {/* Target Case ID */}
          <div className="kg-meta-row">
            <label className="kg-meta-label" htmlFor="upload-case-id">
              Target Case Identifier
            </label>
            <input
              id="upload-case-id"
              type="text"
              className="kg-search-input"
              value={targetCaseId}
              onChange={(e) => setTargetCaseId(e.target.value)}
              placeholder="e.g., case_v_acme_corp"
              disabled={isProcessing}
            />
          </div>

          {/* Drag & Drop Zone */}
          <div
            className={`kg-upload-dropzone ${isDragging ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              style={{ display: 'none' }}
              accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff,.tif,.bmp"
              onChange={handleFileInputChange}
            />
            <Upload size={32} className="kg-upload-icon" />
            <div className="kg-upload-text">
              Drag & drop document here, or <span style={{ color: 'var(--accent-gold, #c9a24b)', textDecoration: 'underline' }}>Browse files</span>
            </div>
            <div className="kg-upload-hint">
              Supported: PDF, DOCX, PNG, JPG, TIFF, BMP (up to 150MB)
            </div>
          </div>

          {/* Selected File Card */}
          {selectedFile && (
            <div className="kg-provenance-box" style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                <FileText size={18} color="var(--accent-gold, #c9a24b)" />
                <div>
                  <div style={{ fontSize: '0.86rem', fontWeight: 600 }}>{selectedFile.name}</div>
                  <div style={{ fontSize: '0.72rem', color: 'var(--text-dim, #9e8a78)' }}>
                    {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </div>
                </div>
              </div>
              {!isProcessing && (
                <button
                  type="button"
                  className="kg-tool-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                  }}
                  title="Remove file"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          )}

          {/* Processing Status Banner */}
          {isProcessing && (
            <div className="kg-status-badge saving" style={{ width: '100%', padding: '0.6rem 0.8rem', justifyContent: 'center' }}>
              <Loader2 size={16} className="animate-spin" />
              <span>{processingStage}</span>
            </div>
          )}

          {/* Success Banner */}
          {successInfo && (
            <div
              className={`kg-upload-result ${successInfo.status === 'PARTIAL' ? 'kg-upload-result--warn' : ''}`}
            >
              <CheckCircle2 size={18} />
              <div>
                <div className="kg-upload-result-title">
                  {successInfo.metrics?.entities_extracted ?? 0} entities,{' '}
                  {successInfo.metrics?.relationships_extracted ?? 0} relationships
                </div>
                {successInfo.message && (
                  <p className="kg-upload-result-detail">{successInfo.message}</p>
                )}
                {successInfo.neo4j_synced === false && successInfo.status !== 'PARTIAL' && (
                  <p className="kg-upload-result-detail">
                    Saved to case files; Neo4j sync skipped (database offline).
                  </p>
                )}
              </div>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#f87171', fontSize: '0.8rem', background: 'rgba(239, 68, 68, 0.1)', padding: '0.6rem', borderRadius: '6px' }}>
              <AlertCircle size={16} />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        <div className="kg-modal-footer">
          {onClose && (
            <button type="button" className="kg-btn-secondary" onClick={onClose} disabled={isProcessing}>
              Cancel
            </button>
          )}
          <button
            type="button"
            className="kg-btn-primary"
            onClick={handleUploadSubmit}
            disabled={!selectedFile || isProcessing || !targetCaseId.trim()}
          >
            {isProcessing ? 'Processing Graph...' : 'Generate Knowledge Graph'}
          </button>
        </div>
      </div>
    </div>
  );
};
