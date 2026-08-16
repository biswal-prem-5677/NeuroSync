import React from 'react';
import { Check, X, ArrowRight } from 'lucide-react';

export default function StrengthsWeaknesses({ strengths, weaknesses, impliedMatches }) {
  const impliedList = impliedMatches ? Object.entries(impliedMatches) : [];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
      {/* ─── Strengths ─── */}
      <div className="card animate-in" style={{ padding: '24px', animationDelay: '60ms' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
          <div style={{
            width: '22px', height: '22px', borderRadius: '50%',
            background: 'var(--green-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <Check size={12} color="var(--green)" strokeWidth={3} />
          </div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)' }}>
            Matched Skills
          </h3>
          {strengths && (
            <span style={{ fontSize: '11px', color: 'var(--text-4)', marginLeft: 'auto' }}>
              {strengths.length} matched
            </span>
          )}
        </div>

        {strengths && strengths.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {strengths.map((str, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface-2)',
                  fontSize: '13px',
                  color: 'var(--text-1)',
                  transition: 'background var(--duration-fast) var(--ease-out)',
                }}
              >
                <span style={{ color: 'var(--green)', flexShrink: 0 }}>✓</span>
                <span>{str}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '13px', color: 'var(--text-3)' }}>No matched skills detected.</p>
        )}

        {/* Implied matches */}
        {impliedList.length > 0 && (
          <div style={{ marginTop: '16px', paddingTop: '14px', borderTop: '1px solid var(--border-default)' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-4)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Inferred Skills
            </span>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '8px' }}>
              {impliedList.map(([req, skill]) => (
                <span
                  key={req}
                  style={{
                    fontSize: '11px',
                    padding: '3px 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--surface-3)',
                    color: 'var(--text-2)',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  {skill} <ArrowRight size={10} color="var(--text-4)" /> {req}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* ─── Gap Areas ─── */}
      <div className="card animate-in" style={{ padding: '24px', animationDelay: '120ms' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '18px' }}>
          <div style={{
            width: '22px', height: '22px', borderRadius: '50%',
            background: 'var(--red-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
          }}>
            <X size={12} color="var(--red)" strokeWidth={3} />
          </div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)' }}>
            Missing Skills
          </h3>
          {weaknesses && (
            <span style={{ fontSize: '11px', color: 'var(--text-4)', marginLeft: 'auto' }}>
              {weaknesses.length} gaps
            </span>
          )}
        </div>

        {weaknesses && weaknesses.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {weaknesses.map((weak, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  padding: '8px 12px',
                  borderRadius: 'var(--radius-sm)',
                  background: 'var(--surface-2)',
                  fontSize: '13px',
                  color: 'var(--text-2)',
                }}
              >
                <span style={{ color: 'var(--red)', flexShrink: 0, fontSize: '12px' }}>✕</span>
                <span>{weak}</span>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ fontSize: '13px', color: 'var(--green)' }}>No critical gaps detected — great match!</p>
        )}
      </div>
    </div>
  );
}
