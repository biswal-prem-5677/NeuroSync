import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import InputSection from './components/InputSection';
import CameraMonitor from './components/CameraMonitor';
import ScoreRing from './components/ScoreRing';
import StrengthsWeaknesses from './components/StrengthsWeaknesses';
import GapAnalysis from './components/GapAnalysis';
import SimulationPlayground from './components/SimulationPlayground';
import AuthModal from './components/AuthModal';
import { AlertTriangle, ArrowUpRight } from 'lucide-react';


export default function App() {
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [error, setError] = useState(null);
  const [serverHealthy, setServerHealthy] = useState(true);
  const [user, setUser] = useState(null);
  const [showAuthModal, setShowAuthModal] = useState(false);

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

      <main style={{ flex: 1, maxWidth: '1200px', width: '100%', margin: '0 auto', padding: '40px 24px 64px' }}>
        {/* Hero Section (Vercel style clean minimal header) */}
        <div style={{ marginBottom: '40px', textAlign: 'center' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
            fontWeight: 500,
            color: 'var(--accent)',
            background: 'var(--accent-subtle)',
            border: '1px solid rgba(129, 140, 248, 0.2)',
            padding: '4px 12px',
            borderRadius: 'var(--radius-full)',
            marginBottom: '16px'
          }}>
            <span>Multi-factor Skill Graph & Decision Engine</span>
          </div>

          <h1 style={{
            fontSize: '38px',
            fontWeight: 800,
            letterSpacing: '-0.03em',
            color: 'var(--text-0)',
            marginBottom: '12px',
            lineHeight: 1.15
          }}>
            Precision Career Intelligence
          </h1>

          <p style={{ fontSize: '15px', color: 'var(--text-2)', maxWidth: '600px', margin: '0 auto', lineHeight: 1.6 }}>
            Evaluate resume alignment, resolve requirement groups, and run real-time what-if score simulations using on-device ML embeddings.
          </p>
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

        {/* Input & Upload Panel */}
        <InputSection onAnalyze={handleAnalyze} loading={loading} />

        {/* Camera Perception & Emotion Telemetry Monitor (Pillar 1) */}
        <CameraMonitor />

        {/* Results Container */}

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
      </main>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
        onLoginSuccess={handleLoginSuccess}
      />
    </div>
  );
}
