import React from 'react';
import { BookOpen, Clock, ArrowRight } from 'lucide-react';

export default function GapAnalysis({ gaps }) {
  if (!gaps || gaps.length === 0) return null;

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'critical': return 'badge-red';
      case 'high': return 'badge-amber';
      case 'medium': return 'badge-blue';
      default: return 'badge-neutral';
    }
  };

  return (
    <div className="card animate-in" style={{ padding: '28px', marginBottom: '24px', animationDelay: '240ms' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
            background: 'var(--surface-3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <BookOpen size={15} color="var(--text-2)" />
          </div>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>
            Prioritized Gap Intelligence ({gaps.length})
          </h3>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-4)' }}>Impact-Ranked</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
        {gaps.map((gap, idx) => (
          <div key={idx} style={{
            padding: '14px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--surface-2)',
            border: '1px solid var(--border-default)',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)' }}>{gap.skill}</h4>
                <span className={`badge ${getPriorityBadge(gap.priority)}`}>
                  {gap.priority}
                </span>
                {gap.optional && (
                  <span style={{ fontSize: '11px', color: 'var(--text-4)', fontStyle: 'italic' }}>
                    nice-to-have
                  </span>
                )}
              </div>

              {gap.learning_time && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '12px', color: 'var(--text-3)' }}>
                  <Clock size={12} />
                  <span>Est. {gap.learning_time}</span>
                </div>
              )}
            </div>

            <p style={{ fontSize: '13px', color: 'var(--text-2)', lineHeight: 1.5 }}>
              {gap.reasoning}
            </p>

            {gap.alternatives && gap.alternatives.length > 0 && (
              <div style={{ fontSize: '11px', color: 'var(--text-3)', display: 'flex', gap: '6px', alignItems: 'center', marginTop: '2px' }}>
                <ArrowRight size={10} color="var(--accent)" />
                <span>Accepted alternatives:</span>
                <strong style={{ color: 'var(--text-1)' }}>{gap.alternatives.join(', ')}</strong>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
