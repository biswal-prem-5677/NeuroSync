import React, { useState } from 'react';
import { X, Mail, ShieldCheck, ArrowRight, Lock } from 'lucide-react';

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
        setMessage('Verification token generated (Dev Mode). Click verify below to authenticate.');
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
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(12px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 2000,
      padding: '20px'
    }}>
      <div className="card animate-in-scale" style={{
        width: '100%',
        maxWidth: '400px',
        padding: '28px',
        position: 'relative',
        background: 'var(--surface-1)'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: 'none',
            border: 'none',
            color: 'var(--text-4)',
            cursor: 'pointer'
          }}
        >
          <X size={18} />
        </button>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '6px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Lock size={15} color="var(--accent)" />
          </div>
          <h3 style={{ fontSize: '17px', fontWeight: 600, color: 'var(--text-0)' }}>Sign in to NeuroSync</h3>
        </div>
        <p style={{ fontSize: '13px', color: 'var(--text-3)', marginBottom: '20px' }}>
          Passwordless magic link authentication for secure candidate analysis.
        </p>

        {!magicToken ? (
          <form onSubmit={handleRequestMagicLink}>
            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.05em', textTransform: 'uppercase', marginBottom: '6px' }}>
                Email Address
              </label>
              <div style={{ position: 'relative' }}>
                <Mail size={15} color="var(--text-4)" style={{ position: 'absolute', left: '12px', top: '11px' }} />
                <input
                  type="email"
                  className="input"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@company.com"
                  required
                  style={{ paddingLeft: '36px' }}
                />
              </div>
            </div>

            {message && <p style={{ fontSize: '12px', color: 'var(--amber)', marginBottom: '12px' }}>{message}</p>}

            <button type="submit" className="btn-primary" disabled={loading} style={{ width: '100%', padding: '10px' }}>
              {loading ? 'Generating...' : 'Send Magic Link'}
            </button>
          </form>
        ) : (
          <div style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '13px', color: 'var(--green)', marginBottom: '16px', lineHeight: 1.4 }}>
              {message}
            </p>
            <button onClick={handleVerifyMagicToken} className="btn-primary" disabled={loading} style={{ width: '100%', padding: '10px' }}>
              {loading ? 'Verifying...' : 'Authenticate & Continue'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
