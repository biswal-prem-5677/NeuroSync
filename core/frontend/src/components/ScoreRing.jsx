import React, { useEffect, useRef } from 'react';

export default function ScoreRing({ decision, scoring, meta }) {
  if (!decision || !scoring) return null;

  const score = decision.overall_score || 0;
  const shortlistProb = Math.round((decision.shortlist_probability || 0) * 100);

  const getFitColor = (level) => {
    switch (level) {
      case 'strong_fit': return 'var(--green)';
      case 'good_fit': return 'var(--blue)';
      case 'potential_fit': return 'var(--amber)';
      case 'weak_fit':
      case 'no_fit': return 'var(--red)';
      default: return 'var(--accent)';
    }
  };

  const getFitBadge = (level) => {
    switch (level) {
      case 'strong_fit': return 'badge-green';
      case 'good_fit': return 'badge-blue';
      case 'potential_fit': return 'badge-amber';
      case 'weak_fit':
      case 'no_fit': return 'badge-red';
      default: return 'badge-neutral';
    }
  };

  const formatRecommendation = (rec) => {
    switch (rec) {
      case 'strong_apply': return 'Strong Apply';
      case 'apply': return 'Apply — Good Match';
      case 'apply_with_preparation': return 'Apply with Prep';
      case 'upskill_then_apply': return 'Upskill First';
      case 'do_not_apply': return 'Not Recommended';
      default: return rec;
    }
  };

  const fitColor = getFitColor(decision.fit_level);

  // SVG ring calculations
  const radius = 72;
  const stroke = 5;
  const circumference = 2 * Math.PI * radius;
  const dashOffset = circumference - (score / 100) * circumference;

  const metrics = [
    { label: 'Shortlist Probability', value: `${shortlistProb}%`, pct: shortlistProb, color: 'var(--accent)' },
    { label: 'Skill Coverage', value: `${Math.round((scoring.skill_overlap_score || 0) * 100)}%`, pct: (scoring.skill_overlap_score || 0) * 100, color: 'var(--green)' },
    { label: 'Semantic Match', value: scoring.semantic_score ? `${Math.round(scoring.semantic_score * 100)}%` : 'N/A', pct: (scoring.semantic_score || 0) * 100, color: 'var(--blue)' },
  ];

  return (
    <div className="card animate-in-scale" style={{ padding: '32px', marginBottom: '24px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '200px 1fr 260px', gap: '32px', alignItems: 'center' }}>

        {/* ─── SVG Score Ring ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '14px' }}>
          <div style={{ position: 'relative', width: '164px', height: '164px' }}>
            <svg width="164" height="164" viewBox="0 0 164 164" style={{ transform: 'rotate(-90deg)' }}>
              {/* Track */}
              <circle
                cx="82" cy="82" r={radius}
                fill="none"
                stroke="var(--surface-3)"
                strokeWidth={stroke}
              />
              {/* Fill */}
              <circle
                cx="82" cy="82" r={radius}
                fill="none"
                stroke={fitColor}
                strokeWidth={stroke}
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={dashOffset}
                style={{
                  transition: 'stroke-dashoffset 1s var(--ease-out)',
                  filter: `drop-shadow(0 0 6px ${fitColor})`,
                }}
              />
            </svg>
            {/* Center label */}
            <div
              style={{
                position: 'absolute',
                inset: 0,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <span className="font-mono" style={{ fontSize: '36px', fontWeight: 700, color: 'var(--text-0)', lineHeight: 1 }}>
                {score.toFixed(0)}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-3)', marginTop: '2px', letterSpacing: '0.04em' }}>
                / 100
              </span>
            </div>
          </div>

          <span className={getFitBadge(decision.fit_level)}>
            {decision.fit_level?.replace('_', ' ')}
          </span>
        </div>

        {/* ─── Verdict & Reasoning ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>
              Recommendation
            </span>
            <h3 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-0)', marginTop: '4px', letterSpacing: '-0.02em' }}>
              {formatRecommendation(decision.recommendation)}
            </h3>
          </div>

          <p style={{ fontSize: '14px', color: 'var(--text-2)', lineHeight: 1.65, maxWidth: '480px' }}>
            {decision.reasoning}
          </p>

          {meta && (
            <span className="font-mono" style={{ fontSize: '11px', color: 'var(--text-4)' }}>
              {meta.processing_time_ms}ms · engine v1.0.0
            </span>
          )}
        </div>

        {/* ─── Metric bars ─── */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
          {metrics.map((m) => (
            <div key={m.label}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>{m.label}</span>
                <span className="font-mono" style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-1)' }}>
                  {m.value}
                </span>
              </div>
              <div className="progress-track">
                <div
                  className="progress-fill"
                  style={{ width: `${m.pct}%`, background: m.color }}
                />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
