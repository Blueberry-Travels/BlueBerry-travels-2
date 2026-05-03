import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Navbar() {
  const router = useRouter();
  const [isScrolled, setIsScrolled] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    const handleScroll = () => setIsScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      setIsLoggedIn(true);
      const userData = localStorage.getItem('user');
      if (userData) setUser(JSON.parse(userData));
    }
  }, []);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.trim().toLowerCase();
    if (!query) return;

    if (query.includes('diy') || query.includes('itinerary') || query.includes('build')) {
      router.push('/diy');
    } else if (query.includes('retreat')) {
      router.push('/retreats');
    } else if (query.includes('workation') || query.includes('office')) {
      router.push('/workations');
    } else if (query.includes('event') || query.includes('festival')) {
      router.push('/events');
    } else if (query.includes('quiz') || query.includes('style')) {
      router.push('/quiz');
    } else if (query.includes('dash') || query.includes('trip') || query.includes('book')) {
      router.push('/dashboard');
    } else {
      router.push(`/packages?search=${encodeURIComponent(query)}`);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setIsLoggedIn(false);
    setUser(null);
    router.push('/');
  };

  return (
    <header className={`navbar-root ${isScrolled ? 'scrolled' : ''}`}>
      <div className="top-section">
        <Link href="/" className="logo-container">
          <span className="logo-icon">🫐</span>
          <span className="logo-text">BlueBerry<span>Travels.co</span></span>
        </Link>

        <form className="search-wrap" onSubmit={handleSearch}>
          <input 
            type="text" 
            className="search-input" 
            placeholder="Search treks, retreats, stays..." 
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button type="submit" className="search-btn">Search</button>
        </form>

        <div className="header-actions">
          <div className="status-pill-live">
            <span className="pulse-dot"></span>
            <span>Concierge Live</span>
          </div>
          {isLoggedIn ? (
            <>
              <Link href="/dashboard" className="login-btn">Dashboard</Link>
              <button onClick={handleLogout} className="logout-btn">Log Out</button>
            </>
          ) : (
            <>
              <Link href="/login" className="login-btn">Log In</Link>
              <Link href="/register" className="signup-btn">Sign Up</Link>
            </>
          )}
        </div>
      </div>

      <nav className="main-nav">
        <div className="nav-links">
          <Link href="/diy">DIY Builder</Link>
          <Link href="/packages">Packages</Link>
          <Link href="/events">Events</Link>
          <Link href="/workations">Workations</Link>
          <Link href="/retreats">Retreats</Link>
          <Link href="/quiz">Style Quiz</Link>
        </div>
      </nav>

      <style jsx>{`
        .navbar-root {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          z-index: 1000;
          transition: all 0.4s ease;
          background: transparent;
        }

        .navbar-root.scrolled {
          background: rgba(10, 10, 12, 0.85);
          backdrop-filter: blur(24px);
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
          box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }

        .logo-text { font-size: 24px; font-weight: 900; color: white; letter-spacing: -0.02em; }
        .logo-text span { color: var(--primary); }

        .top-section {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 16px var(--outer-gap);
          max-width: 1440px;
          margin: 0 auto;
        }

        .status-pill-live {
          display: flex;
          align-items: center;
          gap: 8px;
          background: rgba(76, 124, 53, 0.1);
          border: 1px solid rgba(76, 124, 53, 0.2);
          padding: 8px 16px;
          border-radius: 100px;
          color: var(--primary-light);
          font-size: 11px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }
        .pulse-dot {
          width: 6px;
          height: 6px;
          background: #4ade80;
          border-radius: 50%;
          box-shadow: 0 0 0 rgba(74, 222, 128, 0.4);
          animation: pulse 2s infinite;
        }
        @keyframes pulse {
          0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
          70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
          100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
        }

        .header-actions {
          display: flex;
          align-items: center;
          gap: 12px;
        }

        :global(.login-btn), :global(.signup-btn) {
          font-size: 13px;
          font-weight: 800;
          padding: 10px 24px;
          border-radius: 12px;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: inline-block;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        :global(.login-btn) {
          color: white;
          background: rgba(255, 255, 255, 0.05);
          border: 1px solid rgba(255, 255, 255, 0.1);
        }

        :global(.login-btn:hover) {
          background: rgba(255, 255, 255, 0.1);
          border-color: rgba(255, 255, 255, 0.2);
        }

        :global(.signup-btn) {
          color: white;
          background: var(--primary);
          box-shadow: 0 8px 20px rgba(76, 124, 53, 0.3);
        }

        :global(.signup-btn):hover {
          background: var(--primary-light);
          transform: translateY(-2px);
          box-shadow: 0 12px 30px rgba(76, 124, 53, 0.4);
        }

        .logout-btn {
          font-size: 13px;
          font-weight: 800;
          color: #fca5a5;
          background: rgba(239, 68, 68, 0.1);
          border: 1px solid rgba(239, 68, 68, 0.2);
          padding: 10px 24px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.3s ease;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .logout-btn:hover {
          background: rgba(239, 68, 68, 0.2);
          border-color: rgba(239, 68, 68, 0.4);
        }

        .main-nav {
          display: flex;
          justify-content: center;
          padding: 10px 0;
          background: rgba(255, 255, 255, 0.03);
          border-top: 1px solid rgba(255, 255, 255, 0.05);
          backdrop-filter: blur(12px);
        }

        .nav-links {
          display: flex;
          gap: 32px;
        }

        .nav-links a {
          font-size: 12px;
          font-weight: 700;
          color: rgba(255, 255, 255, 0.6);
          text-transform: uppercase;
          letter-spacing: 0.15em;
          transition: all 0.3s ease;
        }

        .nav-links a:hover {
          color: var(--primary-light);
          text-shadow: 0 0 15px rgba(125, 155, 110, 0.4);
        }
      `}</style>
    </header>
  );
}
