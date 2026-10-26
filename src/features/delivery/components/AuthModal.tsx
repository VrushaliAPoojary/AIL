import React, { FormEvent, useEffect, useState } from 'react';
import { IconLock, IconClose, IconAlertTriangle, IconShieldCheck } from './Icons';

interface AuthModalProps {
  username: string;
  password: string;
  setUsername: (value: string) => void;
  setPassword: (value: string) => void;
  onSubmit: (e: FormEvent) => void;
  onClose: () => void;
  busy: boolean;
  error: string;
  configured: boolean;
}

export function AuthModal({
  username,
  password,
  setUsername,
  setPassword,
  onSubmit,
  onClose,
  busy,
  error,
  configured,
}: AuthModalProps) {
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  return (
    <div
      className="auth-modal-backdrop"
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className="auth-modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
      >
        <button
          type="button"
          className="auth-modal-close-btn"
          onClick={onClose}
          aria-label="Close authentication dialog"
        >
          <IconClose size={20} />
        </button>

        <div className="auth-modal-icon-badge">
          <IconLock size={28} />
        </div>

        <h2 id="auth-modal-title" className="auth-modal-title">
          Administrator Access
        </h2>
        <p className="auth-modal-subtitle">
          Sign in to execute live monitoring runs and manage delivery configuration settings.
        </p>

        {!configured ? (
          <div className="auth-unconfigured-card">
            <IconAlertTriangle size={20} className="warning-icon" />
            <div>
              <strong>Credentials Not Configured</strong>
              <p>
                To enable administrator privileges, specify <code>P02_ADMIN_USERNAME</code>,{' '}
                <code>P02_ADMIN_PASSWORD</code>, and <code>P02_SESSION_SECRET</code> in the server environment.
              </p>
            </div>
          </div>
        ) : (
          <form onSubmit={onSubmit} className="auth-modal-form">
            <div className="auth-form-group">
              <label htmlFor="auth-username-field" className="auth-label">
                Administrator Username
              </label>
              <input
                id="auth-username-field"
                type="text"
                autoComplete="username"
                className="auth-input"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter admin username"
                required
                maxLength={120}
              />
            </div>

            <div className="auth-form-group">
              <label htmlFor="auth-password-field" className="auth-label">
                Password
              </label>
              <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
                <input
                  id="auth-password-field"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  className="auth-input"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter admin password"
                  required
                  maxLength={256}
                  style={{ paddingRight: '48px', width: '100%' }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={{
                    position: 'absolute',
                    right: '10px',
                    background: 'none',
                    border: 'none',
                    color: '#64748b',
                    fontSize: '12px',
                    cursor: 'pointer',
                    fontWeight: 600,
                  }}
                  tabIndex={-1}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </div>

            {error && (
              <div className="auth-error-banner">
                <IconAlertTriangle size={16} />
                <span>{error}</span>
              </div>
            )}

            <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
              <button
                type="submit"
                className="auth-submit-btn"
                disabled={busy}
                style={{ flex: 1 }}
              >
                {busy ? 'Authenticating…' : 'Sign In Securely'}
              </button>
              <button
                type="button"
                className="admin-login-btn"
                onClick={onClose}
                style={{ padding: '12px 16px', fontSize: '13px' }}
              >
                Explore Demo
              </button>
            </div>
          </form>
        )}

        <div className="auth-modal-guard-footer">
          <IconShieldCheck size={14} />
          <span>Session tokens are cryptographically signed and stored in HTTP-only cookies.</span>
        </div>
      </div>
    </div>
  );
}
