import React, { useState } from 'react';
import { FileText, Upload, Sparkles, Sliders, CheckCircle2 } from 'lucide-react';

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
  const [inputMode, setInputMode] = useState('text'); // 'text' | 'file'
  const [resumeText, setResumeText] = useState('');
  const [jdText, setJdText] = useState('');
  const [resumeFile, setResumeFile] = useState(null);
  const [includeSimulations, setIncludeSimulations] = useState(true);
  const [includeEvidence, setIncludeEvidence] = useState(true);

  const handleLoadSample = () => {
    setInputMode('text');
    setResumeText(SAMPLE_RESUME.trim());
    setJdText(SAMPLE_JD.trim());
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputMode === 'file' && resumeFile) {
      onAnalyze({
        mode: 'file',
        resumeFile,
        jdText,
        includeSimulations,
        includeEvidence,
      });
    } else {
      if (!resumeText.trim() || !jdText.trim()) return;
      onAnalyze({
        mode: 'text',
        resumeText,
        jdText,
        includeSimulations,
        includeEvidence,
      });
    }
  };

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '28px', marginBottom: '32px' }}>
      {/* Header controls */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: '20px',
        flexWrap: 'wrap',
        gap: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={20} color="var(--accent-glow)" />
          <h2 style={{ fontSize: '18px', fontWeight: 600 }}>Analyze Resume Against Job Role</h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* Mode Switch */}
          <div style={{
            display: 'flex',
            background: 'var(--bg-elevated)',
            padding: '3px',
            borderRadius: '8px',
            border: '1px solid var(--border-subtle)'
          }}>
            <button
              onClick={() => setInputMode('text')}
              style={{
                background: inputMode === 'text' ? 'var(--accent-primary)' : 'transparent',
                color: inputMode === 'text' ? '#FFF' : 'var(--text-muted)',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              Text Paste
            </button>
            <button
              onClick={() => setInputMode('file')}
              style={{
                background: inputMode === 'file' ? 'var(--accent-primary)' : 'transparent',
                color: inputMode === 'file' ? '#FFF' : 'var(--text-muted)',
                border: 'none',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '13px',
                fontWeight: 500,
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              File Upload (PDF/DOCX)
            </button>
          </div>

          <button className="btn-secondary" onClick={handleLoadSample}>
            Load Sample Data
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Grid Inputs */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: '20px',
          marginBottom: '20px'
        }}>
          {/* Resume Column */}
          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-muted)'
            }}>
              YOUR RESUME
            </label>

            {inputMode === 'text' ? (
              <textarea
                value={resumeText}
                onChange={(e) => setResumeText(e.target.value)}
                placeholder="Paste raw resume text here (min 50 characters)..."
                rows={12}
                style={{
                  width: '100%',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: '12px',
                  padding: '14px',
                  color: 'var(--text-main)',
                  fontFamily: 'var(--font-sans)',
                  fontSize: '14px',
                  resize: 'vertical',
                  outline: 'none'
                }}
              />
            ) : (
              <div style={{
                border: '2px dashed var(--border-subtle)',
                borderRadius: '12px',
                padding: '40px 20px',
                textAlign: 'center',
                background: 'var(--bg-elevated)',
                cursor: 'pointer'
              }}>
                <Upload size={32} color="var(--accent-primary)" style={{ marginBottom: '12px' }} />
                <p style={{ fontSize: '14px', fontWeight: 500, marginBottom: '6px' }}>
                  {resumeFile ? resumeFile.name : 'Upload PDF, DOCX, or TXT file'}
                </p>
                <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                  Max size 10MB • Automatic text extraction
                </span>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => setResumeFile(e.target.files[0])}
                  style={{ display: 'block', margin: '12px auto 0' }}
                />
              </div>
            )}
          </div>

          {/* JD Column */}
          <div>
            <label style={{
              display: 'block',
              marginBottom: '8px',
              fontSize: '13px',
              fontWeight: 600,
              color: 'var(--text-muted)'
            }}>
              TARGET JOB DESCRIPTION
            </label>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste Target Job Description (min 20 characters)..."
              rows={12}
              style={{
                width: '100%',
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '12px',
                padding: '14px',
                color: 'var(--text-main)',
                fontFamily: 'var(--font-sans)',
                fontSize: '14px',
                resize: 'vertical',
                outline: 'none'
              }}
            />
          </div>
        </div>

        {/* Options & Action Footer */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '16px',
          paddingTop: '16px',
          borderTop: '1px solid var(--border-subtle)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeSimulations}
                onChange={(e) => setIncludeSimulations(e.target.checked)}
              />
              <span>What-If Simulations</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeEvidence}
                onChange={(e) => setIncludeEvidence(e.target.checked)}
              />
              <span>Evidence Trace</span>
            </label>
          </div>

          <button
            type="submit"
            className="btn-primary"
            disabled={loading || (inputMode === 'text' ? !resumeText || !jdText : !resumeFile || !jdText)}
            style={{ opacity: loading ? 0.7 : 1 }}
          >
            {loading ? (
              <>Running Intelligence Pipeline...</>
            ) : (
              <>
                <Sparkles size={18} />
                Run Intelligence Analysis
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
