import React from 'react';
import { AlertCircle, Clock, ArrowRight, BookOpen } from 'lucide-react';

export default function GapAnalysis({ gaps }) {
  if (!gaps || gaps.length === 0) {
    return (
      <div className="glass-panel" style={{ padding: '24px', marginBottom: '32px', textAlign: 'center' }}>
        <p style={{ color: 'var(--signal-strong)' }}>Zero missing requirement gaps! Perfect match.</p>
      </div>
    );
  }

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'critical': return 'badge-weak';
      case 'high': return 'badge-potential';
      case 'medium': return 'badge-good';
      case 'low': return 'badge';
      default: return 'badge';
    }
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '28px', marginBottom: '32px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <BookOpen size={22} color="var(--accent-glow)" />
          <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Skill Gap Intelligence ({gaps.length})</h3>
        </div>
        <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>Prioritized by Impact</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {gaps.map((gap, idx) => (
          <div key={idx} style={{
            padding: '18px',
            borderRadius: '12px',
            background: 'var(--bg-elevated)',
            border: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            gap: '10px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h4 style={{ fontSize: '16px', fontWeight: 700 }}>{gap.skill}</h4>
                <span className={`badge ${getPriorityBadgeClass(gap.priority)}`}>
                  {gap.priority}
                </span>
                {gap.optional && (
                  <span style={{ fontSize: '11px', color: 'var(--text-dim)', fontStyle: 'italic' }}>
                    [Nice to Have]
                  </span>
                )}
              </div>

              {gap.learning_time && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-muted)' }}>
                  <Clock size={14} />
                  <span>Est. {gap.learning_time}</span>
                </div>
              )}
            </div>

            {/* Dynamic Non-Template Reasoning */}
            <p style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: 1.5 }}>
              {gap.reasoning}
            </p>

            {/* Alternatives if "A or B" JD line */}
            {gap.alternatives && gap.alternatives.length > 0 && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', gap: '6px', alignItems: 'center' }}>
                <ArrowRight size={12} color="var(--accent-glow)" />
                <span>Alternatives that satisfy requirement:</span>
                <strong style={{ color: 'var(--text-main)' }}>{gap.alternatives.join(', ')}</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
