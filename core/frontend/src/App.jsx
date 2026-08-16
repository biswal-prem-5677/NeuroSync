import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InputSection from './components/InputSection';
import CameraMonitor from './components/CameraMonitor';
import ScoreRing from './components/ScoreRing';
import StrengthsWeaknesses from './components/StrengthsWeaknesses';
import GapAnalysis from './components/GapAnalysis';
import SimulationPlayground from './components/SimulationPlayground';
import JobTracker from './components/JobTracker';
import OutreachSection from './components/OutreachSection';
import PublicProfileSection from './components/PublicProfileSection';
import AuthModal from './components/AuthModal';
import { AlertTriangle, Sparkles, Camera, Briefcase, Mail, User } from 'lucide-react';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverHealthy, setServerHealthy] = useState(true);
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [activeTab, setActiveTab] = useState('career'); // 'career' | 'perception' | 'jobs' | 'outreach' | 'profile'

  useEffect(() => {
    fetch('/api/v1/health')
      .then(res => res.json())
      .then(data => {
        setServerHealthy(data.status === 'healthy' || data.status === 'degraded');
      })
      .catch(() => setServerHealthy(false));
  }, []);

  const handleAnalyze = async (options) => {
    setLoading(true);
    setError(null);
    try {
      let res;
      if (options.mode === 'file') {
        const formData = new FormData();
        formData.append('resume_file', options.resumeFile);
        formData.append('jd_text', options.jdText);
        formData.append('include_simulations', options.includeSimulations);
        formData.append('include_evidence', options.includeEvidence);

        res = await fetch('/api/v1/analyze-file', {
          method: 'POST',
          body: formData,
        });
      } else {
        res = await fetch('/api/v1/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            resume_text: options.resumeText,
            jd_text: options.jdText,
            include_simulations: options.includeSimulations,
            include_evidence: options.includeEvidence,
          }),
        });
      }

      const data = await res.json();
      if (res.ok) {
        setAnalysisResult(data);
      } else {
        setError(data.detail || data.message || 'Analysis failed');
      }
    } catch (err) {
      setError('Failed to connect to backend server');
    } finally {
      setLoading(false);
    }
  };

  const handleLoginSuccess = (userData, token) => {
    setUser(userData);
    localStorage.setItem('neurosync_token', token);
  };

  const navTabs = [
    { id: 'career', label: 'Career Engine', icon: Sparkles },
    { id: 'perception', label: 'Perception Monitor', icon: Camera },
    { id: 'jobs', label: 'Job Tracker', icon: Briefcase },
    { id: 'outreach', label: 'Cold Outreach', icon: Mail },
    { id: 'profile', label: 'Public Profile', icon: User },
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        user={user}
        onOpenAuth={() => setShowAuthModal(true)}
        serverHealthy={serverHealthy}
      />

      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '32px 16px 64px' }}>
        {/* Responsive Ecosystem Navigation Tab Bar */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          overflowX: 'auto',
          padding: '4px',
          background: 'var(--surface-2)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-default)',
          marginBottom: '32px'
        }}>
          {navTabs.map(tab => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: 'var(--radius-sm)',
                  background: isActive ? 'var(--surface-4)' : 'transparent',
                  color: isActive ? 'var(--text-0)' : 'var(--text-3)',
                  border: 'none',
                  fontSize: '13px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                  transition: 'all var(--duration-fast) var(--ease-out)'
                }}
              >
                <Icon size={14} color={isActive ? 'var(--accent)' : 'currentColor'} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Error Alert Banner */}
        {error && (
          <div style={{
            padding: '12px 16px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--red-subtle)',
            border: '1px solid rgba(248, 113, 113, 0.3)',
            color: 'var(--red)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '24px',
            fontSize: '14px'
          }}>
            <AlertTriangle size={16} />
            <span>{error}</span>
          </div>
        )}

        {/* Tab 1: Career Engine */}
        {activeTab === 'career' && (
          <div>
            <InputSection onAnalyze={handleAnalyze} loading={loading} />

            {analysisResult && (
              <div>
                <ScoreRing
                  decision={analysisResult.decision}
                  scoring={analysisResult.scoring}
                  meta={analysisResult.meta}
                />

                <StrengthsWeaknesses
                  strengths={analysisResult.strengths}
                  weaknesses={analysisResult.weaknesses}
                  impliedMatches={analysisResult.skills?.implied_matches}
                />

                {analysisResult.simulations && (
                  <SimulationPlayground
                    simulations={analysisResult.simulations}
                    improvementPath={analysisResult.improvement_path}
                    currentScore={analysisResult.decision.overall_score}
                  />
                )}

                <GapAnalysis gaps={analysisResult.gaps} />
              </div>
            )}
          </div>
        )}

        {/* Tab 2: Perception Monitor (Pillar 1) */}
        {activeTab === 'perception' && (
          <div>
            <CameraMonitor />
          </div>
        )}

        {/* Tab 3: Job Tracker & Kanban (Pillar 3) */}
        {activeTab === 'jobs' && (
          <div>
            <JobTracker />
          </div>
        )}

        {/* Tab 4: Cold Outreach (Pillar 3) */}
        {activeTab === 'outreach' && (
          <div>
            <OutreachSection />
          </div>
        )}

        {/* Tab 5: Public Profile & Showcase (Pillar 3) */}
        {activeTab === 'profile' && (
          <div>
            <PublicProfileSection />
          </div>
        )}
      </main>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
}
