import React from 'react';
import { CheckCircle, AlertTriangle, Zap } from 'lucide-react';

export default function StrengthsWeaknesses({ strengths, weaknesses, impliedMatches }) {
  const impliedList = impliedMatches ? Object.entries(impliedMatches) : [];

  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
      gap: '24px',
      marginBottom: '32px'
    }}>
      {/* Strengths Card */}
      <div className="glass-panel animate-fade-in" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <CheckCircle size={20} color="var(--signal-strong)" />
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Key Strengths</h3>
        </div>

        {strengths && strengths.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {strengths.map((str, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(16, 185, 129, 0.08)',
                border: '1px solid rgba(16, 185, 129, 0.2)',
                fontSize: '14px'
              }}>
                <Zap size={14} color="var(--signal-strong)" />
                <span>{str}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>No major strengths detected.</p>
        )}

        {/* Implied Matches callout */}
        {impliedList.length > 0 && (
          <div style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--border-subtle)' }}>
            <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
              Implied Skills Resolution ({impliedList.length})
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
              {impliedList.map(([req, skill]) => (
                <span key={req} style={{
                  fontSize: '12px',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  color: 'var(--text-main)'
                }}>
                  <strong>{req}</strong> via <em>{skill}</em>
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Weaknesses / Gaps Card */}
      <div className="glass-panel animate-fade-in" style={{ padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
          <AlertTriangle size={20} color="var(--signal-potential)" />
          <h3 style={{ fontSize: '16px', fontWeight: 600 }}>Key Gap Areas</h3>
        </div>

        {weaknesses && weaknesses.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {weaknesses.map((weak, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '10px',
                padding: '10px 14px',
                borderRadius: '8px',
                background: 'rgba(239, 68, 68, 0.08)',
                border: '1px solid rgba(239, 68, 68, 0.2)',
                fontSize: '14px'
              }}>
                <AlertTriangle size={14} color="var(--signal-weak)" />
                <span>{weak}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>No critical weaknesses detected.</p>
        )}
      </div>
    </div>
  );
}
