import React, { useState } from 'react';
import { X, Mail, ShieldCheck, ArrowRight, Key } from 'lucide-react';

export default function AuthModal({ isOpen, onClose, onLoginSuccess }) {
  if (!isOpen) return null;

  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [magicToken, setMagicToken] = useState(null);
  const [message, setMessage] = useState('');

  const handleRequestMagicLink = async (e) => {
    e.preventDefault();
    if (!email) return;
    setLoading(true);
    setMessage('');
    try {
      const res = await fetch('/api/v1/auth/magic-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });
      const data = await res.json();
      if (res.ok) {
        setMagicToken(data.token);
        setMessage('Magic link generated! (Dev Mode: Click verify below)');
      } else {
        setMessage(data.detail || 'Failed to request magic link');
      }
    } catch (err) {
      setMessage('Server error requesting magic link');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyMagicToken = async () => {
    if (!magicToken) return;
    setLoading(true);
    try {
      const res = await fetch('/api/v1/auth/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: magicToken })
      });
      const data = await res.json();
      if (res.ok) {
        onLoginSuccess(data.user, data.access_token);
        onClose();
      } else {
        setMessage(data.detail || 'Verification failed');
      }
    } catch (err) {
      setMessage('Server error verifying token');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px'
    }}>
      <div className="glass-panel animate-fade-in" style={{
        width: '100%',
        maxWidth: '420px',
        padding: '28px',
        position: 'relative'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer'
          }}
        >
          <X size={20} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '8px' }}>
          <ShieldCheck size={24} color="var(--accent-primary)" />
          <h3 style={{ fontSize: '20px', fontWeight: 700 }}>Magic Link Auth</h3>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '20px' }}>
          Passwordless login to save analysis reports & track your growth
        </p>

        {!magicToken ? (
          <form onSubmit={handleRequestMagicLink}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '6px' }}>
                EMAIL ADDRESS
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={16} color="var(--text-dim)" style={{ position: 'absolute', left: '12px', top: '12px' }} />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  required
                  style={{
                    width: '100%',
                    background: 'var(--bg-elevated)',
                    border: '1px solid var(--border-subtle)',
                    borderRadius: '8px',
                    padding: '10px 12px 10px 38px',
                    color: 'var(--text-main)',
                    fontSize: '14px',
                    outline: 'none'
                  }}
                />
              </div>
            </div>

            {message && <p style={{ fontSize: '13px', color: 'var(--signal-potential)', marginBottom: '12px' }}>{message}</p>}

            <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? 'Generating...' : 'Send Magic Link'}
            </button>
          </form>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '14px', color: 'var(--signal-strong)', marginBottom: '16px' }}>
              {message}
            </p>
            <button onClick={handleVerifyMagicToken} className="btn-primary" disabled={loading} style={{ width: '100%', justifyContent: 'center' }}>
              {loading ? 'Verifying...' : 'Verify Magic Link & Log In'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
