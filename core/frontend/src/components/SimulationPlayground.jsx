import React, { useState } from 'react';
import { Sliders, TrendingUp, Sparkles, Plus, Check } from 'lucide-react';

export default function SimulationPlayground({ simulations, improvementPath, currentScore }) {
  if (!simulations || simulations.length === 0) return null;

  const [activeSims, setActiveSims] = useState([]);

  const toggleSim = (skill) => {
    if (activeSims.includes(skill)) {
      setActiveSims(activeSims.filter(s => s !== skill));
    } else {
      setActiveSims([...activeSims, skill]);
    }
  };

  // Calculate cumulative score delta from selected simulations
  const cumulativeDelta = activeSims.reduce((acc, skillName) => {
    const sim = simulations.find(s => s.skill_added === skillName);
    return acc + (sim ? sim.delta : 0);
  }, 0);

  const projectedTotalScore = Math.min(100, (currentScore || 0) + cumulativeDelta);

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '28px', marginBottom: '32px' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <Sliders size={22} color="var(--accent-primary)" />
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 600 }}>What-If Simulation Playground</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Select missing skills below to project real-time score improvements & ROI
            </p>
          </div>
        </div>

        {/* Live Score Counter */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          padding: '10px 20px',
          borderRadius: '12px',
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-active)'
        }}>
          <div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Baseline</span>
            <div className="font-mono" style={{ fontSize: '16px', fontWeight: 700 }}>{currentScore?.toFixed(1)}</div>
          </div>

          <div style={{ fontSize: '18px', color: 'var(--text-dim)' }}>→</div>

          <div>
            <span style={{ fontSize: '11px', color: 'var(--accent-glow)', textTransform: 'uppercase' }}>Projected</span>
            <div className="font-mono" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--signal-strong)' }}>
              {projectedTotalScore.toFixed(1)}
              {cumulativeDelta > 0 && (
                <span style={{ fontSize: '12px', marginLeft: '6px' }}>(+{cumulativeDelta.toFixed(1)})</span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Simulation Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '16px'
      }}>
        {simulations.map((sim, idx) => {
          const isSelected = activeSims.includes(sim.skill_added);
          const roiAction = improvementPath ? improvementPath.find(p => p.skill === sim.skill_added) : null;

          return (
            <div
              key={idx}
              onClick={() => toggleSim(sim.skill_added)}
              style={{
                padding: '20px',
                borderRadius: '12px',
                background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'var(--bg-elevated)',
                border: isSelected ? '1px solid var(--accent-primary)' : '1px solid var(--border-subtle)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                boxShadow: isSelected ? '0 0 20px rgba(99, 102, 241, 0.2)' : 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{
                    width: '24px',
                    height: '24px',
                    borderRadius: '50%',
                    background: isSelected ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white'
                  }}>
                    {isSelected ? <Check size={14} /> : <Plus size={14} />}
                  </span>
                  <h4 style={{ fontSize: '16px', fontWeight: 700 }}>{sim.skill_added}</h4>
                </div>

                <span className="badge badge-strong" style={{ fontFamily: 'var(--font-mono)' }}>
                  +{sim.delta.toFixed(1)} pts
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                <span>Score Improvement:</span>
                <strong style={{ color: 'var(--text-main)' }}>
                  {sim.current_score.toFixed(1)} → {sim.projected_score.toFixed(1)}
                </strong>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--text-muted)' }}>
                <span>Projected Fit:</span>
                <strong style={{ color: 'var(--signal-strong)', textTransform: 'capitalize' }}>
                  {sim.new_fit_level.replace('_', ' ')}
                </strong>
              </div>

              {roiAction && (
                <p style={{ fontSize: '12px', color: 'var(--text-dim)', marginTop: '10px', lineHeight: 1.4, borderTop: '1px solid var(--border-subtle)', paddingTop: '8px' }}>
                  {roiAction.reasoning}
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
