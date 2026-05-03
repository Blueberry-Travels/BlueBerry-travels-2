import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

const ShareTripPage = () => {
  const router = useRouter();
  const { frame_id } = router.query;
  const [copied, setCopied] = useState(false);
  const [shareUrl, setShareUrl] = useState('');

  useEffect(() => {
    if (frame_id) {
      // Create the join URL
      const origin = typeof window !== 'undefined' ? window.location.origin : '';
      setShareUrl(`${origin}/join?frame_id=${frame_id}`);
    }
  }, [frame_id]);

  const handleCopy = () => {
    navigator.clipboard.writeText(shareUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="share-container">
      <Head>
        <title>Invite Friends | Blueberry Travels</title>
      </Head>

      <div className="share-card">
        <div className="share-icon">✨</div>
        <h1>Invite Your Squad</h1>
        <p>Send this link to your friends. Once they click and join, they'll be added to your itinerary auto-magically.</p>
        
        <div className="url-box">
          <input type="text" readOnly value={shareUrl} />
          <button onClick={handleCopy} className={copied ? 'btn-copied' : ''}>
            {copied ? '✓ Copied!' : 'Copy Link'}
          </button>
        </div>

        <div className="share-actions">
          <button className="btn-secondary" onClick={() => router.back()}>← Back to Dashboard</button>
        </div>
      </div>

      <style jsx>{`
        .share-container {
          min-height: 100vh;
          background: #0F172A;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 20px;
          font-family: 'Inter', sans-serif;
        }

        .share-card {
          background: rgba(30, 41, 59, 0.7);
          backdrop-filter: blur(12px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          padding: 40px;
          border-radius: 24px;
          max-width: 500px;
          width: 100%;
          text-align: center;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
        }

        .share-icon {
          font-size: 48px;
          margin-bottom: 20px;
        }

        h1 {
          color: #F8FAFC;
          font-size: 28px;
          margin-bottom: 12px;
          font-weight: 700;
          letter-spacing: -0.02em;
        }

        p {
          color: #94A3B8;
          line-height: 1.6;
          margin-bottom: 32px;
          font-size: 16px;
        }

        .url-box {
          display: flex;
          gap: 10px;
          background: #020617;
          padding: 8px;
          border-radius: 12px;
          border: 1px solid #334155;
          margin-bottom: 24px;
        }

        input {
          flex: 1;
          background: transparent;
          border: none;
          color: #E2E8F0;
          padding: 10px;
          font-family: inherit;
          font-size: 14px;
          outline: none;
        }

        button {
          background: #2563EB;
          color: white;
          border: none;
          padding: 10px 20px;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: all 0.2s;
        }

        button:hover {
          background: #3B82F6;
          transform: translateY(-1px);
        }

        .btn-copied {
          background: #10B981 !important;
        }

        .btn-secondary {
          background: transparent;
          color: #94A3B8;
          border: 1px solid #334155;
        }

        .btn-secondary:hover {
          background: rgba(255, 255, 255, 0.05);
          color: #F8FAFC;
        }

        .share-actions {
          display: flex;
          justify-content: center;
          margin-top: 10px;
        }
      `}</style>
    </div>
  );
};

export default ShareTripPage;
