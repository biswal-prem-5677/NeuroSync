import React, { useState, useEffect } from 'react';
import { Briefcase, Search, ExternalLink, CheckCircle2, Clock } from 'lucide-react';

export default function JobTracker() {
  const [jobs, setJobs] = useState([]);
  const [applications, setApplications] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState('match'); // 'match' | 'kanban'

  useEffect(() => {
    fetch(`/api/v1/jobs/search${searchQuery ? `?query=${encodeURIComponent(searchQuery)}` : ''}`)
      .then(res => res.json())
      .then(data => setJobs(data))
      .catch(console.error);

    fetch('/api/v1/jobs/applications')
      .then(res => res.json())
      .then(data => setApplications(data))
      .catch(console.error);
  }, [searchQuery]);

  const handleStatusChange = async (appId, newStatus) => {
    try {
      const res = await fetch(`/api/v1/jobs/applications/status?user_id=usr_biswal&app_id=${appId}&new_status=${newStatus}`, {
        method: 'POST'
      });
      if (res.ok) {
        const updated = await res.json();
        setApplications(applications.map(a => a.id === appId ? updated : a));
      }
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="card animate-in" style={{ padding: '28px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px', flexWrap: 'wrap', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
            background: 'var(--blue-subtle)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Briefcase size={15} color="var(--blue)" />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>
              Job Discovery & Application Kanban (Pillar 3)
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-3)' }}>
              Personalized job matching engine and application pipeline tracker.
            </p>
          </div>
        </div>

        {/* View Switch */}
        <div style={{ display: 'inline-flex', background: 'var(--surface-2)', padding: '2px', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-default)' }}>
          <button
            onClick={() => setActiveTab('match')}
            style={{
              background: activeTab === 'match' ? 'var(--surface-4)' : 'transparent',
              color: activeTab === 'match' ? 'var(--text-0)' : 'var(--text-3)',
              border: 'none', padding: '5px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer'
            }}
          >
            Job Matches ({jobs.length})
          </button>
          <button
            onClick={() => setActiveTab('kanban')}
            style={{
              background: activeTab === 'kanban' ? 'var(--surface-4)' : 'transparent',
              color: activeTab === 'kanban' ? 'var(--text-0)' : 'var(--text-3)',
              border: 'none', padding: '5px 12px', borderRadius: '4px', fontSize: '12px', cursor: 'pointer'
            }}
          >
            Kanban Board ({applications.length})
          </button>
        </div>
      </div>

      {activeTab === 'match' ? (
        <div>
          <div style={{ position: 'relative', marginBottom: '16px' }}>
            <Search size={15} color="var(--text-4)" style={{ position: 'absolute', left: '12px', top: '11px' }} />
            <input
              type="text"
              className="input"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search jobs by skill (e.g. Kubernetes, React, Python)..."
              style={{ paddingLeft: '36px' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
            {jobs.map(job => (
              <div key={job.id} style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)' }}>{job.role_title}</h4>
                    <span style={{ fontSize: '12px', color: 'var(--text-3)' }}>{job.company_name} · {job.location}</span>
                  </div>
                  <span className="badge badge-green font-mono">{job.match_score}% Match</span>
                </div>

                <div style={{ fontSize: '12px', color: 'var(--text-2)', marginBottom: '12px' }}>
                  Salary: <strong style={{ color: 'var(--text-0)' }}>{job.salary_range}</strong>
                </div>

                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginBottom: '14px' }}>
                  {job.required_skills.map(s => (
                    <span key={s} style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'var(--surface-3)', color: 'var(--text-3)' }}>
                      {s}
                    </span>
                  ))}
                </div>

                <a href={job.apply_url} target="_blank" rel="noreferrer" className="btn-secondary" style={{ width: '100%', fontSize: '12px', justifyContent: 'center' }}>
                  <span>Apply Now</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '14px' }}>
          {['Applied', 'Interview', 'Offer'].map(column => {
            const columnApps = applications.filter(a => a.status === column);
            return (
              <div key={column} style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
                  <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-2)' }}>{column}</h4>
                  <span style={{ fontSize: '11px', color: 'var(--text-4)' }}>{columnApps.length}</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {columnApps.map(app => (
                    <div key={app.id} style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-3)', border: '1px solid var(--border-default)' }}>
                      <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-0)' }}>{app.role_title}</h5>
                      <span style={{ fontSize: '11px', color: 'var(--text-3)' }}>{app.company_name}</span>
                      <p style={{ fontSize: '11px', color: 'var(--text-4)', marginTop: '6px', lineHeight: 1.4 }}>{app.notes}</p>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
