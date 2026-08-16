import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InputSection from './components/InputSection';
import ScoreRing from './components/ScoreRing';
import StrengthsWeaknesses from './components/StrengthsWeaknesses';
import GapAnalysis from './components/GapAnalysis';
import SimulationPlayground from './components/SimulationPlayground';
import AuthModal from './components/AuthModal';
import { AlertCircle } from 'lucide-react';

export default function App() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverHealthy, setServerHealthy] = useState(true);
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

  // Check health endpoint on load
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

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Navbar
        user={user}
        onOpenAuth={() => setShowAuthModal(true)}
        serverHealthy={serverHealthy}
      />

      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '32px 24px' }}>
        {/* Hero Banner */}
        <div style={{ textAlign: 'center', marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '36px',
            fontWeight: 800,
            letterSpacing: '-0.03em',
            background: 'linear-gradient(135deg, #FFF 30%, #9CA3AF 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '8px'
          }}>
            Career Decision Engine
          </h1>
          <p style={{ fontSize: '16px', color: 'var(--text-muted)', maxWidth: '640px', margin: '0 auto' }}>
            Multi-factor resume & job alignment analysis with skill graph reasoning, requirement group resolution, and what-if score simulations.
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <div style={{
            padding: '14px 18px',
            borderRadius: '12px',
            background: 'rgba(239, 68, 68, 0.12)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: 'var(--signal-weak)',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            marginBottom: '24px'
          }}>
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Input & Upload Panel */}
        <InputSection onAnalyze={handleAnalyze} loading={loading} />

        {/* Results Section */}
        {analysisResult && (
          <div className="animate-fade-in">
            {/* Score Ring & Verdict Header */}
            <ScoreRing
              decision={analysisResult.decision}
              scoring={analysisResult.scoring}
              meta={analysisResult.meta}
            />

            {/* Strengths & Weaknesses */}
            <StrengthsWeaknesses
              strengths={analysisResult.strengths}
              weaknesses={analysisResult.weaknesses}
              impliedMatches={analysisResult.skills?.implied_matches}
            />

            {/* Simulation Playground */}
            {analysisResult.simulations && (
              <SimulationPlayground
                simulations={analysisResult.simulations}
                improvementPath={analysisResult.improvement_path}
                currentScore={analysisResult.decision.overall_score}
              />
            )}

            {/* Prioritized Skill Gaps */}
            <GapAnalysis gaps={analysisResult.gaps} />
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
