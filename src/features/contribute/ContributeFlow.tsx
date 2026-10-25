'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { ChangeEvent, DragEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react';
import '../persistence/Persistence.css';
import { summarizeContributionResource } from './contributionPreview';

const INITIAL_FORM = {
  type: 'FILE',
  url: '',
  text: '',
  file_name: '',
  file_mime_type: '',
  file_size: '',
  file_preview: '',
  context: '',
};

const CONTRIBUTION_TYPES = [
  { value: 'FILE', label: 'Dropbox' },
  { value: 'LINK', label: 'Link' },
  { value: 'INSIGHT', label: 'Key insights' },
] as const;

type Contributor = {
  id: string;
  name: string;
  role: string;
};

type Contribution = {
  id: string;
  contributor_id: string;
  contributor_name: string;
  resource_id?: string;
  type: string;
  resource: {
    url?: string;
    text?: string;
    file?: {
      name: string;
      mime_type?: string;
      size?: number;
    };
  };
  context?: string;
  status: string;
  created_at: string;
  updated_at: string;
};

function createClientId() {
  return globalThis.crypto?.randomUUID?.() || `idem_${Date.now().toString(36)}_${Math.random().toString(36).slice(2)}`;
}

function formatTimestamp(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(value));
}

export function ContributeFlow({ contributor }: { contributor: Contributor }) {
  const router = useRouter();
  const [form, setForm] = useState(INITIAL_FORM);
  const [successContribution, setSuccessContribution] = useState<Contribution | null>(null);
  const [error, setError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [recentContributions, setRecentContributions] = useState<Contribution[]>([]);
  const [loadingRecent, setLoadingRecent] = useState(true);
  const [idempotencyKey] = useState(() => createClientId());
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [dragActive, setDragActive] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadRecentContributions() {
      setLoadingRecent(true);
      try {
        const response = await fetch('/api/contributions?limit=10');
        if (!response.ok) {
          throw new Error('Unable to load recent contributions.');
        }
        const payload = (await response.json()) as { contributions: Contribution[] };
        if (!cancelled) {
          setRecentContributions(payload.contributions || []);
        }
      } catch (loadError) {
        if (!cancelled) {
          setRecentContributions([]);
          setError((current) => current || (loadError instanceof Error ? loadError.message : 'Unable to load recent contributions.'));
        }
      } finally {
        if (!cancelled) {
          setLoadingRecent(false);
        }
      }
    }

    loadRecentContributions();

    return () => {
      cancelled = true;
    };
  }, []);

  const contributionType = form.type;

  function populateFile(file: File) {
    setForm((current) => ({
      ...current,
      file_name: file.name,
      file_mime_type: file.type || current.file_mime_type,
      file_size: String(file.size),
      file_preview: file.name,
    }));
  }

  function openFilePicker() {
    fileInputRef.current?.click();
  }

  function handleFileSelect(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      populateFile(file);
    }
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragActive(false);
    const file = event.dataTransfer.files?.[0];
    if (file) {
      populateFile(file);
    }
  }
  const contributionHint = useMemo(() => {
    if (contributionType === 'FILE') {
      return 'Drop a JPG, PNG, PDF, Markdown or similar file. AIL stores file metadata in this MVP, not the binary upload.';
    }
    if (contributionType === 'INSIGHT') {
      return 'Key insights should capture the distilled observation, conclusion or signal.';
    }
    return 'Keep the contribution focused on a single source, excerpt or observation.';
  }, [contributionType]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setError('');
    setSuccessContribution(null);

    const resource =
      form.type === 'LINK'
        ? { url: form.url }
        : form.type === 'FILE'
          ? {
              file: {
                name: form.file_name,
                ...(form.file_mime_type ? { mime_type: form.file_mime_type } : {}),
                size: Number(form.file_size),
              },
            }
          : { text: form.text };

    try {
      const response = await fetch('/api/contributions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Idempotency-Key': idempotencyKey,
        },
        body: JSON.stringify({
          type: form.type,
          resource,
          context: form.context,
        }),
      });

      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.error || 'Unable to save contribution.');
      }

      const contribution = payload as Contribution;
      setSuccessContribution(contribution);
      setRecentContributions((current) => [contribution, ...current.filter((item) => item.id !== contribution.id)]);
      setForm(INITIAL_FORM);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      const refreshed = await fetch('/api/contributions?limit=10');
      if (refreshed.ok) {
        const refreshedPayload = (await refreshed.json()) as { contributions: Contribution[] };
        setRecentContributions(refreshedPayload.contributions || []);
      }
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Unable to save contribution.');
    } finally {
      setIsSubmitting(false);
    }
  }

  async function clearSession() {
    try {
      await fetch('/api/session/logout', { method: 'POST' });
    } catch {
      // Logout is best-effort.
    }
    router.replace('/onboarding');
  }

  return (
    <div className="persistence-shell">
      <section className="persistence-hero" aria-labelledby="contribute-title">
        <p className="persistence-kicker">Contribute</p>
        <h1 id="contribute-title">Share a source, insight or observation.</h1>
        <p className="persistence-intro">
          Contributor records are restored from the server. Contributions are stored as versioned JSON records in the
          private GitHub data repository.
        </p>
      </section>

      <section className="persistence-status" aria-live="polite">
        <h2>Current contributor</h2>
        <div className="persistence-contributor">
          <strong>{contributor.name}</strong>
          <span>{contributor.role}</span>
          <span>{contributor.id}</span>
        </div>
        <div className="persistence-actions">
          <button className="persistence-button persistence-button-secondary" onClick={clearSession}>
            Switch Contributor
          </button>
        </div>
      </section>

      <section className="persistence-panel" aria-labelledby="contribution-form-title">
        <h2 id="contribution-form-title">Contribution form</h2>
        <div className="persistence-type-rail" aria-label="Contribution types">
          {CONTRIBUTION_TYPES.map((type) => (
            <button
              key={type.value}
              type="button"
              className={'persistence-type-option ' + (form.type === type.value ? 'is-active' : '')}
              onClick={() => setForm((current) => ({ ...current, type: type.value }))}
            >
              {type.label}
            </button>
          ))}
        </div>
        <p className="persistence-note">{contributionHint}</p>
        {error ? <p className="persistence-error" role="alert">{error}</p> : null}
        {successContribution ? (
          <div className="persistence-success" role="status">
            <strong>Contribution saved.</strong>
            <span>
              {successContribution.id} · {formatTimestamp(successContribution.created_at)}
            </span>
          </div>
        ) : null}
        <form className="persistence-form" onSubmit={handleSubmit}>
          {form.type === 'LINK' ? (
            <label>
              Resource URL
              <input
                type="url"
                value={form.url}
                onChange={(event) => setForm((current) => ({ ...current, url: event.target.value }))}
                placeholder="https://example.com/research-note"
                autoComplete="url"
              />
            </label>
          ) : null}
          {form.type === 'TEXT' || form.type === 'INSIGHT' ? (
            <label>
              Resource text
              <textarea
                value={form.text}
                onChange={(event) => setForm((current) => ({ ...current, text: event.target.value }))}
                placeholder="Enter the source excerpt or synthesized insight."
                rows={6}
              />
            </label>
          ) : null}
          {form.type === 'FILE' ? (
            <div
              className={'dropbox-dropzone ' + (dragActive ? 'is-active' : '')}
              onDragEnter={(event) => { event.preventDefault(); setDragActive(true); }}
              onDragOver={(event) => { event.preventDefault(); setDragActive(true); }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              role="button"
              tabIndex={0}
              onKeyDown={(event) => { if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); openFilePicker(); } }}
              aria-label="Drop a file to contribute"
            >
              <input
                ref={fileInputRef}
                className="dropbox-file-input"
                type="file"
                accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.md,.markdown,.txt,image/jpeg,image/png,image/gif,image/webp,application/pdf,text/markdown,text/plain"
                onChange={handleFileSelect}
              />
              <div className="dropbox-icon">⬆</div>
              <strong>Drop files here</strong>
              <p>Accepted: JPG, PNG, GIF, WEBP, PDF, MD, TXT</p>
              <button className="persistence-button persistence-button-secondary" type="button" onClick={openFilePicker}>
                Choose file
              </button>
              {form.file_preview ? <span className="dropbox-selected">Selected: {form.file_preview}</span> : null}
            </div>
          ) : null}
          <label>
            Context
            <textarea
              value={form.context}
              onChange={(event) => setForm((current) => ({ ...current, context: event.target.value }))}
              placeholder="Optional context, provenance or notes."
              rows={4}
            />
          </label>
          <div className="persistence-actions">
            <button className="persistence-button persistence-button-primary" type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Saving...' : 'Save Contribution'}
            </button>
            <button className="persistence-button persistence-button-secondary" type="button" onClick={clearSession}>
              Switch Contributor
            </button>
          </div>
        </form>
      </section>

      <section className="persistence-panel" aria-labelledby="recent-contributions-title">
        <h2 id="recent-contributions-title">Recent contributions</h2>
        {loadingRecent ? <p className="persistence-note">Loading recent contributions...</p> : null}
        <div className="persistence-list">
          {recentContributions.map((item) => (
            <article className="persistence-list-item" key={item.id}>
              <div className="persistence-list-item-header">
                <strong>{summarizeContributionResource(item)}</strong>
                <span>{item.type}</span>
              </div>
              <p>{item.context || 'No context provided.'}</p>
              <small>
                {item.contributor_name} · {formatTimestamp(item.created_at)}
              </small>
            </article>
          ))}
          {!loadingRecent && recentContributions.length === 0 ? <p className="persistence-note">No contributions yet.</p> : null}
        </div>
      </section>
    </div>
  );
}
