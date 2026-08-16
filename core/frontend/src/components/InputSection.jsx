import React, { useState, useRef } from 'react';
import { FileText, Upload, Sparkles, ToggleLeft, ToggleRight, ArrowRight } from 'lucide-react';

const SAMPLE_RESUME = `Priyabrata Biswal
Senior Software Engineer | Full Stack Developer

EXPERIENCE
Senior Software Engineer, TechCorp (2024-2026)
- Built production-grade REST APIs using Python and FastAPI, serving 10M+ requests/month
- Designed and implemented microservices architecture with Docker and Kubernetes on AWS
- Led migration of monolithic application to event-driven architecture using Apache Kafka
- Implemented CI/CD pipelines using GitHub Actions and ArgoCD

Software Developer, StartupXYZ (2022-2024)
- Developed full-stack web applications using React, TypeScript, and Node.js
- Built real-time data processing pipeline using Python, Pandas, and Apache Spark
- Designed PostgreSQL database schemas optimized for high-throughput analytics
- Integrated machine learning models for recommendation engine using scikit-learn

SKILLS
Python, JavaScript, TypeScript, React, FastAPI, Django, Node.js, Docker, PostgreSQL,
MongoDB, Redis, AWS, Git, Linux, Machine Learning, Deep Learning, NLP, TensorFlow,
PyTorch, scikit-learn, Pandas, NumPy, Kafka, System Design, Agile`;

const SAMPLE_JD = `Senior Backend Engineer - Cloud Infrastructure

Requirements:
- 3+ years of experience with Python, Go, or Java
- Strong experience with Kubernetes and container orchestration
- Experience with cloud platforms (AWS, GCP, or Azure)
- Experience with Terraform or similar infrastructure-as-code tools
- Strong understanding of microservices architecture and distributed systems
- Experience with CI/CD pipelines and DevOps practices
- Knowledge of monitoring tools like Prometheus and Grafana
- Experience with message queues (Kafka, RabbitMQ)
- Strong SQL and database design skills
- Experience with Redis or similar caching solutions

Nice to have:
- Experience with GraphQL
- Knowledge of service mesh (Istio, Linkerd)`;

export default function InputSection({ onAnalyze, loading }) {
  const [inputMode, setInputMode] = useState('text');
  const [resumeText, setResumeText] = useState('');
  const [jdText, setJdText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [includeSimulations, setIncludeSimulations] = useState(true);
  const [includeEvidence, setIncludeEvidence] = useState(true);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleLoadSample = () => {
    setInputMode('text');
    setResumeText(SAMPLE_RESUME.trim());
    setJdText(SAMPLE_JD.trim());
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMode === 'file' && resumeFile) {
      onAnalyze({ mode: 'file', resumeFile, jdText, includeSimulations, includeEvidence });
    } else {
      if (!resumeText.trim() || !jdText.trim()) return;
      onAnalyze({ mode: 'text', resumeText, jdText, includeSimulations, includeEvidence });
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) setResumeFile(file);
  };

  const canSubmit = inputMode === 'text'
    ? resumeText.trim().length > 0 && jdText.trim().length > 0
    : resumeFile && jdText.trim().length > 0;

  return (
    <div className="card animate-in" style={{ padding: '28px 28px 24px' }}>
      {/* ─── Header ─── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <h2 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-0)' }}>
          Analyze Resume Against Job Role
        </h2>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {/* Mode toggle */}
          <div
            style={{
              display: 'inline-flex',
              background: 'var(--surface-2)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-default)',
              padding: '2px',
            }}
          >
            {['text', 'file'].map((mode) => (
              <button
                key={mode}
                type="button"
                onClick={() => setInputMode(mode)}
                style={{
                  background: inputMode === mode ? 'var(--surface-4)' : 'transparent',
                  color: inputMode === mode ? 'var(--text-0)' : 'var(--text-3)',
                  border: 'none',
                  padding: '5px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 500,
                  cursor: 'pointer',
                  transition: 'all var(--duration-fast) var(--ease-out)',
                  fontFamily: 'var(--font-sans)',
                }}
              >
                {mode === 'text' ? 'Paste Text' : 'Upload File'}
              </button>
            ))}
          </div>

          <button type="button" className="btn-ghost" onClick={handleLoadSample} style={{ fontSize: '12px', color: 'var(--accent)' }}>
            Load sample
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* ─── Input columns ─── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          {/* Resume */}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Resume
            </label>

            {inputMode === 'text' ? (
              <textarea
                className="input"
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste resume text here..."
                rows={14}
                style={{ minHeight: '320px' }}
              />
            ) : (
              <div
                onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
                onDragLeave={() => setIsDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                style={{
                  minHeight: '320px',
                  border: `1.5px dashed ${isDragOver ? 'var(--accent)' : 'var(--border-default)'}`,
                  borderRadius: 'var(--radius-md)',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '12px',
                  background: isDragOver ? 'var(--accent-glow)' : 'var(--surface-2)',
                  cursor: 'pointer',
                  transition: 'all var(--duration-normal) var(--ease-out)',
                }}
              >
                <div
                  style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: 'var(--radius-md)',
                    background: 'var(--surface-3)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}
                >
                  <Upload size={20} color="var(--text-3)" />
                </div>
                <div style={{ textAlign: 'center' }}>
                  <p style={{ fontSize: '14px', fontWeight: 500, color: 'var(--text-1)', marginBottom: '4px' }}>
                    {resumeFile ? resumeFile.name : 'Drop your resume here'}
                  </p>
                  <p style={{ fontSize: '12px', color: 'var(--text-4)' }}>
                    PDF, DOCX, or TXT · Max 10 MB
                  </p>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setResumeFile(e.target.files[0])}
                  style={{ display: 'none' }}
                />
              </div>
            )}
          </div>

          {/* Job Description */}
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '11px', fontWeight: 600, color: 'var(--text-3)', letterSpacing: '0.06em', textTransform: 'uppercase' }}>
              Target Job Description
            </label>
            <textarea
              className="input"
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the job description here..."
              rows={14}
              style={{ minHeight: '320px' }}
            />
          </div>
        </div>

        {/* ─── Footer: options + action ─── */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            paddingTop: '16px',
            borderTop: '1px solid var(--border-default)',
            flexWrap: 'wrap',
            gap: '12px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            {[
              { label: 'What-If Simulations', value: includeSimulations, set: setIncludeSimulations },
              { label: 'Evidence Trace', value: includeEvidence, set: setIncludeEvidence },
            ].map(({ label, value, set }) => (
              <button
                key={label}
                type="button"
                onClick={() => set(!value)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '13px',
                  color: value ? 'var(--text-1)' : 'var(--text-4)',
                  fontFamily: 'var(--font-sans)',
                  transition: 'color var(--duration-fast) var(--ease-out)',
                }}
              >
                <div
                  style={{
                    width: '32px',
                    height: '18px',
                    borderRadius: 'var(--radius-full)',
                    background: value ? 'var(--accent-stronger)' : 'var(--surface-4)',
                    position: 'relative',
                    transition: 'background var(--duration-fast) var(--ease-out)',
                  }}
                >
                  <div
                    style={{
                      width: '14px',
                      height: '14px',
                      borderRadius: '50%',
                      background: '#fff',
                      position: 'absolute',
                      top: '2px',
                      left: value ? '16px' : '2px',
                      transition: 'left var(--duration-fast) var(--ease-out)',
                      boxShadow: '0 1px 3px rgba(0,0,0,0.3)',
                    }}
                  />
                </div>
                {label}
              </button>
            ))}
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !canSubmit}
            style={{ fontSize: '14px', padding: '10px 24px' }}
          >
            {loading ? (
              <>
                <span className="skeleton" style={{ width: '14px', height: '14px', borderRadius: '50%' }} />
                Analyzing...
              </>
            ) : (
              <>
                Run Analysis
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
