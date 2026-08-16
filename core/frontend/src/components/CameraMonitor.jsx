import React, { useState, useEffect, useRef } from 'react';
import { Camera, Video, AlertCircle, Play, Square, Activity, Eye, Zap } from 'lucide-react';

export default function CameraMonitor() {
  const [isActive, setIsActive] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [telemetry, setTelemetry] = useState(null);
  const [error, setError] = useState(null);
  const videoRef = useRef(null);
  const timerRef = useRef(null);

  const startSession = async () => {
    setError(null);
    try {
      const newSessionId = `sess_${Date.now()}`;
      const res = await fetch('/api/v1/perception/session/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: newSessionId })
      });
      if (!res.ok) throw new Error('Failed to start perception session');

      setSessionId(newSessionId);
      setIsActive(true);

      // Access camera stream
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 320, height: 240 } });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
      }

      // Start periodic telemetry frame simulation / payload dispatch
      timerRef.current = setInterval(async () => {
        try {
          const frameRes = await fetch(`/api/v1/perception/frame?session_id=${newSessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              head_pose: { pitch: (Math.random() - 0.5) * 10, yaw: (Math.random() - 0.5) * 10, roll: 0 },
              eye_gaze: { x: (Math.random() - 0.5) * 0.2, y: (Math.random() - 0.5) * 0.2 },
              ear_left: 0.28 + (Math.random() * 0.06),
              ear_right: 0.29 + (Math.random() * 0.05),
              mar: 0.12,
              expression_scores: { focused: 0.75 + (Math.random() * 0.2), neutral: 0.15 }
            })
          });
          if (frameRes.ok) {
            const data = await frameRes.json();
            setTelemetry(data);
          }
        } catch (err) {
          console.error('Frame error:', err);
        }
      }, 1500);

    } catch (err) {
      setError(err.message || 'Camera access error');
      setIsActive(false);
    }
  };

  const stopSession = async () => {
    if (timerRef.current) clearInterval(timerRef.current);
    if (videoRef.current && videoRef.current.srcObject) {
      const tracks = videoRef.current.srcObject.getTracks();
      tracks.forEach(track => track.stop());
    }

    if (sessionId) {
      try {
        await fetch(`/api/v1/perception/session/end?session_id=${sessionId}`, { method: 'POST' });
      } catch (err) {
        console.error('End session error:', err);
      }
    }

    setIsActive(false);
    setTelemetry(null);
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  return (
    <div className="card animate-in" style={{ padding: '24px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '28px', height: '28px', borderRadius: 'var(--radius-sm)',
            background: isActive ? 'var(--green-subtle)' : 'var(--surface-3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center'
          }}>
            <Camera size={15} color={isActive ? 'var(--green)' : 'var(--text-3)'} />
          </div>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)' }}>
              Camera Perception & Emotion Monitor (Pillar 1)
            </h3>
            <p style={{ fontSize: '12px', color: 'var(--text-3)' }}>
              Real-time 10-state emotion classification, eye gaze & attention HUD telemetry.
            </p>
          </div>
        </div>

        {!isActive ? (
          <button className="btn-primary" onClick={startSession} style={{ fontSize: '13px', padding: '7px 16px' }}>
            <Play size={13} />
            Start Camera Telemetry
          </button>
        ) : (
          <button className="btn-secondary" onClick={stopSession} style={{ fontSize: '13px', padding: '7px 16px', color: 'var(--red)' }}>
            <Square size={13} />
            Stop Session
          </button>
        )}
      </div>

      {error && (
        <div style={{ fontSize: '12px', color: 'var(--red)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertCircle size={14} />
          <span>{error}</span>
        </div>
      )}

      {/* Video & Telemetry HUD Container */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: isActive ? '240px 1fr' : '1fr',
        gap: '20px',
        alignItems: 'center'
      }}>
        {/* Video Frame */}
        <div style={{
          position: 'relative',
          width: '100%',
          height: isActive ? '180px' : '100px',
          borderRadius: 'var(--radius-md)',
          background: 'var(--surface-2)',
          border: '1px solid var(--border-default)',
          overflow: 'hidden',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            style={{
              width: '100%',
              height: '100%',
              objectFit: 'cover',
              display: isActive ? 'block' : 'none'
            }}
          />

          {!isActive && (
            <div style={{ textAlign: 'center', color: 'var(--text-4)' }}>
              <Video size={24} style={{ marginBottom: '6px' }} />
              <p style={{ fontSize: '12px' }}>Camera offline. Click "Start Camera Telemetry" to launch.</p>
            </div>
          )}

          {isActive && (
            <div style={{
              position: 'absolute',
              top: '8px',
              left: '8px',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              background: 'rgba(0,0,0,0.6)',
              padding: '3px 8px',
              borderRadius: 'var(--radius-full)',
              fontSize: '10px',
              color: 'var(--green)'
            }}>
              <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)', animation: 'pulse-dot 1s infinite' }} />
              <span>REC LIVE</span>
            </div>
          )}
        </div>

        {/* Telemetry HUD Panel */}
        {isActive && telemetry && (
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
            gap: '12px'
          }}>
            <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-3)', display: 'block', marginBottom: '4px' }}>Attention Score</span>
              <span className="font-mono" style={{ fontSize: '20px', fontWeight: 700, color: 'var(--green)' }}>
                {telemetry.attention_score}%
              </span>
            </div>

            <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-3)', display: 'block', marginBottom: '4px' }}>Primary Emotion</span>
              <span style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-0)', textTransform: 'capitalize' }}>
                {telemetry.primary_emotion}
              </span>
            </div>

            <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-3)', display: 'block', marginBottom: '4px' }}>Learning State</span>
              <span className="badge badge-blue" style={{ textTransform: 'capitalize' }}>
                {telemetry.learning_state}
              </span>
            </div>

            <div style={{ padding: '12px', borderRadius: 'var(--radius-sm)', background: 'var(--surface-2)', border: '1px solid var(--border-default)' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-3)', display: 'block', marginBottom: '4px' }}>Fatigue Index</span>
              <span className="font-mono" style={{ fontSize: '15px', fontWeight: 600, color: telemetry.fatigue_index > 0.4 ? 'var(--amber)' : 'var(--text-2)' }}>
                {telemetry.fatigue_index}
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
