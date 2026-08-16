import React, { useState } from 'react';
import { Sliders, Plus, Check, TrendingUp } from 'lucide-react';

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

  const cumulativeDelta = activeSims.reduce((acc, skillName) => {
    const sim = simulations.find(s => s.skill_added === skillName);
    return acc + (sim ? sim.delta : 0);
  }, 0);

  const projectedTotalScore = Math.min(100, (currentScore || 0) + cumulativeDelta);

  return (
    <div className="card animate-in" style={{ padding: '28px', marginBottom: '24px', animationDelay: '180ms' }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
            background: 'var(--accent-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Sliders size={15} color="var(--accent)" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>What-If Score Simulator</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-3)' }}>
              Toggle missing skills to project real-time score impact and return on investment.
            </p>
          </div>
        </div>

        {/* Live Score Counter Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          padding: '6px 14px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--surface-2)',
          border: '1px solid var(--border-default)'
        }}>
          <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Score:</span>
          <span className="font-mono" style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-2)' }}>
            {currentScore?.toFixed(0)}
          </span>
          <span style={{ fontSize: '12px', color: 'var(--text-4)' }}>→</span>
          <span className="font-mono" style={{ fontSize: '15px', fontWeight: 700, color: cumulativeDelta > 0 ? 'var(--green)' : 'var(--text-0)' }}>
            {projectedTotalScore.toFixed(0)}
            {cumulativeDelta > 0 && <span style={{ fontSize: '11px', marginLeft: '4px' }}>(+{cumulativeDelta.toFixed(1)})</span>}
          </span>
        </div>
      </div>

      {/* Grid of Simulation Skill Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
        gap: '12px'
      }}>
        {simulations.map((sim, idx) => {
          const isSelected = activeSims.includes(sim.skill_added);
          const roiAction = improvementPath ? improvementPath.find(p => p.skill === sim.skill_added) : null;

          return (
            <div
              key={idx}
              onClick={() => toggleSim(sim.skill_added)}
              style={{
                padding: '16px',
                borderRadius: 'var(--radius-md)',
                background: isSelected ? 'var(--accent-subtle)' : 'var(--surface-2)',
                border: `1px solid ${isSelected ? 'var(--accent)' : 'var(--border-default)'}`,
                cursor: 'pointer',
                transition: 'all var(--duration-fast) var(--ease-out)',
                userSelect: 'none'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <div style={{
                    width: '18px', height: '18px', borderRadius: '50%',
                    background: isSelected ? 'var(--accent-stronger)' : 'var(--surface-3)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff'
                  }}>
                    {isSelected ? <Check size={11} strokeWidth={3} /> : <Plus size={11} />}
                  </div>
                  <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)' }}>{sim.skill_added}</h4>
                </div>

                <span className="badge badge-green font-mono" style={{ fontSize: '10px' }}>
                  +{sim.delta.toFixed(1)} pts
                </span>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-3)' }}>
                <span>Fit level:</span>
                <span style={{ color: 'var(--text-1)', textTransform: 'capitalize' }}>
                  {sim.new_fit_level.replace('_', ' ')}
                </span>
              </div>

              {roiAction && (
                <p style={{ fontSize: '11px', color: 'var(--text-3)', marginTop: '8px', paddingTop: '8px', borderTop: '1px solid var(--border-default)', lineHeight: 1.4 }}>
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
