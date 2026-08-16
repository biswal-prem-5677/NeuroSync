import React from 'react';
import { Activity, User, ChevronDown } from 'lucide-react';

export default function Navbar({ user, onOpenAuth, serverHealthy }) {
  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        borderBottom: '1px solid var(--border-default)',
        background: 'rgba(9, 9, 11, 0.82)',
        backdropFilter: 'blur(16px) saturate(1.8)',
        WebkitBackdropFilter: 'blur(16px) saturate(1.8)',
      }}
    >
      <div
        style={{
          maxWidth: '1280px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '0 24px',
          height: '56px',
        }}
      >
        {/* ─── Brand ─── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {/* Logo mark */}
          <div
            style={{
              width: '28px',
              height: '28px',
              borderRadius: '7px',
              background: 'linear-gradient(135deg, var(--accent-stronger), #a78bfa)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2" />
            </svg>
          </div>
          <span
            style={{
              fontSize: '15px',
              fontWeight: 700,
              color: 'var(--text-0)',
              letterSpacing: '-0.03em',
            }}
          >
            NeuroSync
          </span>
          <span
            style={{
              fontSize: '11px',
              fontWeight: 500,
              color: 'var(--text-4)',
              background: 'var(--surface-3)',
              padding: '2px 7px',
              borderRadius: 'var(--radius-full)',
              letterSpacing: '0.02em',
            }}
          >
            v1.0
          </span>
        </div>

        {/* ─── Right section ─── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Health indicator */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              fontSize: '12px',
              color: 'var(--text-3)',
            }}
          >
            <span
              style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                background: serverHealthy ? 'var(--green)' : 'var(--red)',
                animation: serverHealthy ? 'none' : 'pulse-dot 1.5s infinite',
                boxShadow: serverHealthy ? '0 0 6px rgba(52, 211, 153, 0.4)' : 'none',
                flexShrink: 0,
              }}
            />
            <span>{serverHealthy ? 'Online' : 'Connecting'}</span>
          </div>

          {/* Divider */}
          <div
            style={{
              width: '1px',
              height: '20px',
              background: 'var(--border-default)',
            }}
          />

          {/* Auth */}
          {user ? (
            <button
              className="btn-ghost"
              style={{
                gap: '6px',
                fontSize: '13px',
                padding: '6px 10px',
                borderRadius: 'var(--radius-sm)',
              }}
            >
              <div
                style={{
                  width: '22px',
                  height: '22px',
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--accent-stronger), #a78bfa)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '11px',
                  fontWeight: 700,
                  color: '#fff',
                  flexShrink: 0,
                }}
              >
                {user.email?.[0]?.toUpperCase() || 'U'}
              </div>
              <span style={{ color: 'var(--text-2)', maxWidth: '140px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {user.email}
              </span>
            </button>
          ) : (
            <button className="btn-secondary" onClick={onOpenAuth} style={{ fontSize: '13px', padding: '7px 14px' }}>
              <User size={14} />
              Sign in
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
