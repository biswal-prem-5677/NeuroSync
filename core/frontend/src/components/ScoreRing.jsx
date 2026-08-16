import React from 'react';
import { Target, TrendingUp, AlertTriangle, CheckCircle, Lightbulb } from 'lucide-react';

export default function ScoreRing({ decision, scoring, meta }) {
  if (!decision || !scoring) return null;

  const score = decision.overall_score || 0;
  const shortlistProb = Math.round((decision.shortlist_probability || 0) * 100);

  const getFitBadgeClass = (level) => {
    switch (level) {
      case 'strong_fit': return 'badge-strong';
      case 'good_fit': return 'badge-good';
      case 'potential_fit': return 'badge-potential';
      case 'weak_fit':
      case 'no_fit': return 'badge-weak';
      default: return 'badge-good';
    }
  };

  const formatRecommendation = (rec) => {
    switch (rec) {
      case 'strong_apply': return 'Strong Apply — Priority Match';
      case 'apply': return 'Apply — Good Overall Match';
      case 'apply_with_preparation': return 'Apply with Preparation — Address Gaps';
      case 'upskill_then_apply': return 'Upskill Then Apply — Key Gaps Exist';
      case 'do_not_apply': return 'Do Not Apply — Poor Role Alignment';
      default: return rec;
    }
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '28px', marginBottom: '32px' }}>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '28px',
        alignItems: 'center'
      }}>
        {/* Left Ring & Score Display */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <div style={{
            position: 'relative',
            width: '180px',
            height: '180px',
            borderRadius: '50%',
            background: `conic-gradient(#6366F1 ${score * 3.6}deg, rgba(255,255,255,0.06) 0deg)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 30px rgba(99, 102, 241, 0.25)',
            marginBottom: '16px'
          }}>
            {/* Inner Ring Circle */}
            <div style={{
              width: '150px',
              height: '150px',
              borderRadius: '50%',
              background: 'var(--bg-secondary)',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <span className="font-mono" style={{ fontSize: '42px', fontWeight: 700, lineHeight: 1 }}>
                {score.toFixed(1)}
              </span>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginTop: '4px' }}>
                Overall Score
              </span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', justifyContent: 'center' }}>
            <span className={`badge ${getFitBadgeClass(decision.fit_level)}`}>
              {decision.fit_level.replace('_', ' ')}
            </span>
          </div>
        </div>

        {/* Center: Verdict & Decision Reasoning */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'var(--bg-elevated)',
            borderLeft: '4px solid var(--accent-primary)'
          }}>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>
              AI Recommendation
            </span>
            <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--text-main)', marginTop: '2px' }}>
              {formatRecommendation(decision.recommendation)}
            </h3>
          </div>

          <p style={{ fontSize: '14px', color: 'var(--text-main)', lineHeight: 1.6 }}>
            {decision.reasoning}
          </p>

          {meta && (
            <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
              Processed in {meta.processing_time_ms}ms • Engine v1.0.0
            </span>
          )}
        </div>

        {/* Right Metrics & Signals */}
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          padding: '20px',
          borderRadius: '12px',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)'
        }}>
          {/* Shortlist Probability */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Shortlist Probability</span>
              <span className="font-mono" style={{ fontWeight: 700, color: 'var(--accent-glow)' }}>
                {shortlistProb}%
              </span>
            </div>
            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${shortlistProb}%`, height: '100%', background: 'linear-gradient(90deg, #6366F1, #8B5CF6)', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Skill Overlap */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Skill Coverage</span>
              <span className="font-mono" style={{ fontWeight: 700 }}>
                {Math.round((scoring.skill_overlap_score || 0) * 100)}%
              </span>
            </div>
            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${(scoring.skill_overlap_score || 0) * 100}%`, height: '100%', background: 'var(--signal-strong)', borderRadius: '3px' }} />
            </div>
          </div>

          {/* Semantic Score */}
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
              <span style={{ color: 'var(--text-muted)' }}>Semantic Vocabulary Alignment</span>
              <span className="font-mono" style={{ fontWeight: 700 }}>
                {scoring.semantic_score ? `${Math.round(scoring.semantic_score * 100)}%` : 'N/A'}
              </span>
            </div>
            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.08)', borderRadius: '3px', overflow: 'hidden' }}>
              <div style={{ width: `${(scoring.semantic_score || 0) * 100}%`, height: '100%', background: 'var(--signal-good)', borderRadius: '3px' }} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
