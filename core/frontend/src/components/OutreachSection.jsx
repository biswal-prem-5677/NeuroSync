import React, { useState } from 'react';
import { Mail, Sparkles, Send, Check, Copy } from 'lucide-react';

export default function OutreachSection() {
  const [recipientName, setRecipientName] = useState('Sarah Jenkins');
  const [recipientRole, setRecipientRole] = useState('Senior Technical Recruiter');
  const [companyName, setCompanyName] = useState('Vercel');
  const [targetRole, setTargetRole] = useState('Senior Full Stack AI Developer');
  const [emailResponse, setEmailResponse] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const res = await fetch('/api/v1/outreach/cold-email', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          recipient_name: recipientName,
          recipient_role: recipientRole,
          company_name: companyName,
          target_role: targetRole,
          user_name: 'Priyabrata Biswal',
          key_achievements: [
            'Built production-grade REST APIs in FastAPI serving 10M+ requests/month',
            'Designed microservices architecture with Docker & Kubernetes on AWS'
          ]
        })
      });
      if (res.ok) {
        const data = await res.json();
        setEmailResponse(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card animate-in" style={{ padding: '28px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '20px' }}>
        <div style={{
          width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
          background: 'var(--accent-subtle)',
          display: 'flex', alignItems: 'center', justifyContent: 'center'
        }}>
          <Mail size={15} color="var(--accent)" />
        </div>
        <div>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>
            AI Recruiter Cold Email & Outreach Generator (Pillar 3)
          </h3>
          <p style={{ fontSize: '12px', color: 'var(--text-3)' }}>
            Generates high-conversion recruiter outreach emails & automated follow-up sequences.
          </p>
        </div>
      </div>

      <form onSubmit={handleGenerate} style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '14px', marginBottom: '20px' }}>
        <div>
          <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-3)', marginBottom: '4px' }}>RECIPIENT NAME</label>
          <input className="input" value={recipientName} onChange={e => setRecipientName(e.target.value)} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-3)', marginBottom: '4px' }}>RECIPIENT ROLE</label>
          <input className="input" value={recipientRole} onChange={e => setRecipientRole(e.target.value)} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-3)', marginBottom: '4px' }}>TARGET COMPANY</label>
          <input className="input" value={companyName} onChange={e => setCompanyName(e.target.value)} required />
        </div>
        <div>
          <label style={{ display: 'block', fontSize: '11px', color: 'var(--text-3)', marginBottom: '4px' }}>JOB ROLE</label>
          <input className="input" value={targetRole} onChange={e => setTargetRole(e.target.value)} required />
        </div>
      </form>

      <button className="btn-primary" onClick={handleGenerate} disabled={loading} style={{ marginBottom: '20px' }}>
        <Sparkles size={14} />
        {loading ? 'Generating Outreach...' : 'Generate Cold Email Sequence'}
      </button>

      {emailResponse && (
        <div style={{ padding: '20px', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>Subject: <strong style={{ color: 'var(--text-0)' }}>{emailResponse.subject_line}</strong></span>
            <button className="btn-ghost" onClick={() => copyToClipboard(emailResponse.email_body)} style={{ fontSize: '12px' }}>
              {copied ? <Check size={13} color="var(--green)" /> : <Copy size={13} />}
              {copied ? 'Copied!' : 'Copy Body'}
            </button>
          </div>

          <textarea
            className="input"
            rows={10}
            value={emailResponse.email_body}
            readOnly
            style={{ marginBottom: '16px', background: 'var(--surface-3)' }}
          />

          <div style={{ borderTop: '1px solid var(--border-default)', paddingTop: '12px' }}>
            <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-4)', textTransform: 'uppercase' }}>Automated Follow-up Sequence</span>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '10px', marginTop: '8px' }}>
              {emailResponse.followup_sequence.map((seq, i) => (
                <div key={i} style={{ padding: '10px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-3)', fontSize: '11px' }}>
                  <span style={{ color: 'var(--accent)', fontWeight: 600 }}>{seq.day}: </span>
                  <span style={{ color: 'var(--text-2)' }}>{seq.subject}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
