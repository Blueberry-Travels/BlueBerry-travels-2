import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

const JoinTripPage = () => {
  const router = useRouter();
  const { frame_id } = router.query;
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'unauthorized'>('loading');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (!router.isReady || !frame_id) return;

    const performJoin = async () => {
      const token = localStorage.getItem('access_token');
      
      if (!token) {
        // Not logged in -> redirect to register with return path
        router.push(`/register?redirect=/join?frame_id=${frame_id}`);
        return;
      }

      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'}/api/v1/frames/join/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ frame_id })
        });

        const data = await response.json();
        
        if (response.ok || data.status === 'already_member') {
          setStatus('success');
          // Redirect to dashboard after 2 seconds
          setTimeout(() => {
            router.push('/dashboard');
          }, 2000);
        } else {
          setStatus('error');
          setErrorMsg(data.error || 'Failed to join trip');
        }
      } catch (err) {
        console.error('Join error:', err);
        setStatus('error');
        setErrorMsg('Connection error. Please try again later.');
      }
    };

    performJoin();
  }, [router.isReady, frame_id]);

  return (
    <div className="join-container">
      <Head>
        <title>Joining Trip... | Blueberry Travels</title>
      </Head>

      <div className="join-card">
        {status === 'loading' && (
          <>
            <div className="spinner"></div>
            <h1>Joining Trip...</h1>
            <p>We're adding you to the itinerary. One moment!</p>
          </>
        )}

        {status === 'success' && (
          <div className="success-state">
            <div className="icon">🎉</div>
            <h1>You're in!</h1>
            <p>Welcome to the squad. Redirecting you to the dashboard...</p>
          </div>
        )}

        {status === 'error' && (
          <div className="error-state">
            <div className="icon">⚠️</div>
            <h1>Oops!</h1>
            <p>{errorMsg}</p>
            <button onClick={() => router.push('/dashboard')}>Back to Home</button>
          </div>
        )}
      </div>

      <style jsx>{`
        .join-container {
          min-height: 100vh;
          background: #0F172A;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          font-family: 'Inter', sans-serif;
        }

        .join-card {
          background: rgba(30, 41, 59, 0.7);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          padding: 60px 40px;
          border-radius: 24px;
          max-width: 450px;
          width: 100%;
          text-align: center;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .spinner {
          width: 50px;
          height: 50px;
          border: 4px solid rgba(255, 255, 255, 0.1);
          border-left-color: #2563EB;
          border-radius: 50%;
          margin: 0 auto 30px;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        h1 {
          color: #F8FAFC;
          font-size: 24px;
          margin-bottom: 12px;
          font-weight: 700;
        }

        p {
          color: #94A3B8;
          line-height: 1.6;
          font-size: 16px;
        }

        .icon {
          font-size: 64px;
          margin-bottom: 24px;
        }

        button {
          margin-top: 30px;
          background: #2563EB;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 10px;
          font-weight: 600;
          cursor: pointer;
        }

        button:hover {
          background: #3B82F6;
        }
      `}</style>
    </div>
  );
};

export default JoinTripPage;
