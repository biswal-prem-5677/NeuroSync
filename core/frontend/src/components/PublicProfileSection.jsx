import React, { useState, useEffect } from 'react';
import { User, Globe, Share2, Heart, Award, ExternalLink, MessageSquare } from 'lucide-react';


export default function PublicProfileSection() {
  const [profile, setProfile] = useState(null);
  const [feed, setFeed] = useState([]);

  useEffect(() => {
    fetch('/api/v1/social/profile?user_id=usr_biswal')
      .then(res => res.json())
      .then(data => setProfile(data))
      .catch(console.error);

    fetch('/api/v1/social/feed')
      .then(res => res.json())
      .then(data => setFeed(data))
      .catch(console.error);
  }, []);

  if (!profile) return null;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
      {/* Profile Card & Projects */}
      <div className="card animate-in" style={{ padding: '28px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
          <div style={{
            width: '56px', height: '56px', borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--accent-stronger), #a78bfa)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '22px', fontWeight: 700, color: '#fff'
          }}>
            PB
          </div>
          <div>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--text-0)' }}>{profile.full_name}</h3>
            <p style={{ fontSize: '13px', color: 'var(--text-2)' }}>{profile.headline}</p>
            <span style={{ fontSize: '11px', color: 'var(--text-4)' }}>{profile.location}</span>
          </div>
        </div>

        <p style={{ fontSize: '13px', color: 'var(--text-3)', marginBottom: '20px', lineHeight: 1.5 }}>
          {profile.bio}
        </p>

        {/* Skills Pills */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '24px' }}>
          {profile.top_skills.map(s => (
            <span key={s} style={{ fontSize: '11px', padding: '4px 10px', borderRadius: 'var(--radius-full)', background: 'var(--surface-3)', color: 'var(--text-1)' }}>
              {s}
            </span>
          ))}
        </div>

        {/* Portfolio Showcase Projects */}
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)', marginBottom: '12px' }}>Featured Portfolio Projects</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {profile.projects.map(p => (
            <div key={p.id} style={{ padding: '16px', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <h5 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>{p.title}</h5>
                <a href={p.github_url} target="_blank" rel="noreferrer" style={{ color: 'var(--text-3)' }}><Globe size={16} /></a>
              </div>

              <p style={{ fontSize: '12px', color: 'var(--text-3)', marginBottom: '10px' }}>{p.description}</p>
              <div style={{ display: 'flex', gap: '6px' }}>
                {p.tech_stack.map(t => (
                  <span key={t} style={{ fontSize: '10px', padding: '2px 6px', borderRadius: '4px', background: 'var(--surface-3)', color: 'var(--text-4)' }}>{t}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Community Achievement Feed */}
      <div className="card animate-in" style={{ padding: '24px' }}>
        <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-0)', marginBottom: '16px' }}>Community Achievement Feed</h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {feed.map(post => (
            <div key={post.id} style={{ padding: '14px', borderRadius: 'var(--radius-md)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <strong style={{ fontSize: '12px', color: 'var(--text-1)' }}>{post.user_name}</strong>
                <span className="badge badge-blue" style={{ fontSize: '9px' }}>{post.category}</span>
              </div>
              <h5 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-0)', marginBottom: '4px' }}>{post.title}</h5>
              <p style={{ fontSize: '11px', color: 'var(--text-3)', lineHeight: 1.4, marginBottom: '8px' }}>{post.description}</p>
              <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', color: 'var(--text-4)' }}>
                <Heart size={12} color="var(--red)" />
                <span>{post.likes_count} kudos</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
