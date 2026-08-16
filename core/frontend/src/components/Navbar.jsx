import React from 'react';
import { Cpu, ShieldCheck, User, Zap, Terminal } from 'lucide-react';

export default function Navbar({ user, onOpenAuth, serverHealthy }) {
  return (
    <nav style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 32px',
      borderBottom: '1px solid var(--border-subtle)',
      background: 'rgba(10, 14, 26, 0.8)',
      backdropFilter: 'blur(12px)',
      position: 'sticky',
      top: 0,
      zIndex: 100
    }}>
      {/* Brand Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '38px',
          height: '38px',
          borderRadius: '10px',
          background: 'linear-gradient(135deg, #6366F1, #8B5CF6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 16px rgba(99, 102, 241, 0.4)'
        }}>
          <Cpu size={22} color="#FFFFFF" />
        </div>
        <div>
          <h1 style={{ fontSize: '18px', fontWeight: 700, letterSpacing: '-0.02em', lineHeight: 1.2 }}>
            NeuroSync
          </h1>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 500 }}>
            Career Decision System v1.0
          </span>
        </div>
      </div>

      {/* Right Controls & Status */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* API Health Indicator */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          fontSize: '12px',
          padding: '4px 10px',
          borderRadius: '20px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid var(--border-subtle)'
        }}>
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: serverHealthy ? 'var(--signal-strong)' : 'var(--signal-weak)',
            boxShadow: serverHealthy ? '0 0 8px var(--signal-strong)' : 'none'
          }} />
          <span style={{ color: 'var(--text-muted)' }}>
            {serverHealthy ? 'Engine Ready' : 'Connecting...'}
          </span>
        </div>

        {/* User Auth Button */}
        {user ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '6px 12px',
            borderRadius: '8px',
            background: 'var(--bg-elevated)',
            fontSize: '13px',
            fontWeight: 500
          }}>
            <ShieldCheck size={16} color="var(--signal-strong)" />
            <span>{user.email}</span>
          </div>
        ) : (
          <button className="btn-secondary" onClick={onOpenAuth}>
            <User size={15} />
            <span>Sign In</span>
          </button>
        )}
      </div>
    </nav>
  );
}
