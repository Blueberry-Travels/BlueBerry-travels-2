import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../../lib/api';

export default function JoinPage() {
  const router = useRouter();
  const { id } = router.query;
  const [loading, setLoading] = useState(true);
  const [frame, setFrame] = useState<any>(null);
  const [error, setError] = useState('');
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    if (id) {
      fetchFramePreview();
    }
  }, [id]);

  const fetchFramePreview = async () => {
    try {
      const res = await api.get(`/api/v1/frames/${id}/`);
      setFrame(res.data);
    } catch (e) {
      setError('Trip not found or link expired.');
    } finally {
      setLoading(false);
    }
  };

  const handleJoin = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      localStorage.setItem('redirect_after_login', `/join/${id}`);
      router.push('/login');
      return;
    }

    setJoining(true);
    try {
      const res = await api.post(`/api/v1/frames/join/`, { frame_id: id });
      if (res.status === 200 || res.status === 201) {
        router.push('/dashboard');
      } else {
        setError(res.data?.error || 'Failed to join trip.');
      }
    } catch (e) {
      setError('Network error. Please try again.');
    } finally {
      setJoining(false);
    }
  };

  return (
    <>
      <Head>
        <title>Join Journey — Blueberry Travels</title>
      </Head>

      <div className="join-page-wrapper">
        <div className="join-card glass">
          {loading ? (
            <div className="join-loading">
              <div className="loading-spinner"></div>
              <p>Fetching trip details...</p>
            </div>
          ) : error ? (
            <div className="join-error">
              <div className="error-icon">⚠️</div>
              <h2>Oops!</h2>
              <p>{error}</p>
              <button onClick={() => router.push('/')} className="btn-secondary">Go Home</button>
            </div>
          ) : (
            <div className="join-content">
              <div className="join-header">
                <span className="join-badge">Invitation</span>
                <h1>You&apos;re Invited!</h1>
                <p>Join this {frame.frame_type || 'Custom'} trip in {frame.region?.name || 'Loading...'}</p>
              </div>
              
              <div className="join-stats">
                <div className="stat-item">
                  <span className="stat-label">Duration</span>
                  <span className="stat-value">{frame.days?.length || 0} Days</span>
                </div>
                <div className="stat-divider"></div>
                <div className="stat-item">
                  <span className="stat-label">Travellers</span>
                  <span className="stat-value">{frame.attendees?.length || 0}</span>
                </div>
              </div>

              <div className="join-perks">
                <div className="perk-item">
                  <div className="perk-icon">🗺️</div>
                  <div className="perk-info">
                    <h3>See Itinerary</h3>
                    <p>View all planned activities and recommendations for this trip.</p>
                  </div>
                </div>
                <div className="perk-item">
                  <div className="perk-icon">💳</div>
                  <div className="perk-info">
                    <h3>Individual Payments</h3>
                    <p>Pay for your own assistance tier and booking share securely.</p>
                  </div>
                </div>
              </div>

              <div className="join-actions">
                <button 
                  onClick={handleJoin}
                  disabled={joining}
                  className="btn-primary"
                  style={{ width: '100%' }}
                >
                  {joining ? 'Joining Trip...' : 'Join Trip Now →'}
                </button>
                <p className="join-terms">
                  By joining, you agree to Blueberry Travels Terms & Privacy.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      <style jsx>{`
        .join-page-wrapper {
          min-height: 80vh;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 60px 24px;
        }
        
        .join-card {
          width: 100%;
          max-width: 500px;
          border-radius: 40px;
          overflow: hidden;
          box-shadow: 0 40px 100px rgba(0,0,0,0.3);
        }
        
        .join-loading, .join-error {
          padding: 80px 40px;
          text-align: center;
        }
        
        .loading-spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(76, 124, 53, 0.1);
          border-top-color: var(--primary-light);
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 24px;
        }
        
        @keyframes spin { to { transform: rotate(360deg); } }
        
        .error-icon {
          font-size: 64px;
          margin-bottom: 24px;
        }
        
        .join-header {
          background: rgba(10, 10, 12, 0.4);
          padding: 60px 40px 40px;
          text-align: center;
          border-bottom: 1px solid var(--glass-border);
        }
        
        .join-badge {
          display: inline-block;
          padding: 6px 16px;
          background: var(--primary);
          color: white;
          border-radius: 100px;
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.15em;
          margin-bottom: 20px;
        }
        
        .join-header h1 {
          font-size: 36px;
          font-weight: 900;
          margin-bottom: 12px;
          color: white;
        }
        
        .join-header p {
          color: var(--text-secondary);
          font-size: 15px;
          opacity: 0.8;
        }
        
        .join-stats {
          display: flex;
          align-items: center;
          padding: 40px;
          border-bottom: 1px solid var(--glass-border);
        }
        
        .stat-item {
          flex: 1;
          text-align: center;
        }
        
        .stat-label {
          display: block;
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          color: var(--text-muted);
          margin-bottom: 8px;
        }
        
        .stat-value {
          font-size: 24px;
          font-weight: 900;
          color: white;
        }
        
        .stat-divider {
          width: 1px;
          height: 40px;
          background: var(--glass-border);
        }
        
        .join-perks {
          padding: 40px;
          display: flex;
          flex-direction: column;
          gap: 32px;
        }
        
        .perk-item {
          display: flex;
          gap: 20px;
          align-items: flex-start;
        }
        
        .perk-icon {
          width: 48px;
          height: 48px;
          background: rgba(255,255,255,0.03);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          flex-shrink: 0;
          border: 1px solid var(--glass-border);
        }
        
        .perk-info h3 {
          font-size: 17px;
          font-weight: 800;
          color: white;
          margin-bottom: 4px;
        }
        
        .perk-info p {
          font-size: 14px;
          color: var(--text-secondary);
          line-height: 1.6;
        }
        
        .join-actions {
          padding: 0 40px 40px;
        }
        
        .join-terms {
          text-align: center;
          font-size: 11px;
          color: var(--text-muted);
          margin-top: 20px;
          font-weight: 500;
        }
      `}</style>
    </>
  );
}
