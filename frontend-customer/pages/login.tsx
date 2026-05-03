import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/api/v1/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Invalid email or password');
      }

      localStorage.setItem('access_token', data.access || data.access_token);
      if (data.refresh || data.refresh_token) {
        localStorage.setItem('refresh_token', data.refresh || data.refresh_token);
      }
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }

      window.dispatchEvent(new Event('auth-change'));
      const redirect = (router.query.redirect as string) || '/dashboard';
      router.push(redirect);
    } catch (err: any) {
      setError(err.message || 'Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Sign In | Blueberry Travels</title>
      </Head>

      <div className="auth-container">
        <div className="auth-left">
            <div className="auth-overlay"></div>
            <div className="auth-brand-content">
                <Link href="/" className="auth-logo">🫐 Blueberry</Link>
                <h1 className="auth-hero-title">Your Next Journey Awaits</h1>
                <p className="auth-hero-subtitle">Sign in to access personalized itineraries, manage bookings, and explore the Himalayas like never before.</p>
                <div className="auth-perks">
                    <div className="auth-perk">✨ Personalized AI Itineraries</div>
                    <div className="auth-perk">🛡️ Secure Payment & KYC</div>
                    <div className="auth-perk">🧭 Local Mountain Support</div>
                </div>
            </div>
        </div>

        <div className="auth-right">
            <div className="auth-form-wrapper glass-dark">
                <div className="auth-header">
                    <h2>Welcome Back</h2>
                    <p>Enter your credentials to continue your adventure.</p>
                </div>

                {error && (
                    <div className="auth-error">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label>Email Address</label>
                        <input 
                            type="email" 
                            placeholder="you@example.com" 
                            className="glass-input"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input 
                            type="password" 
                            placeholder="••••••••" 
                            className="glass-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <div className="form-options">
                        <label className="remember-me">
                            <input type="checkbox" />
                            <span>Keep me signed in</span>
                        </label>
                        <Link href="/forgot-password" style={{ color: 'var(--primary-light)', fontSize: '13px', fontWeight: '600' }}>Forgot?</Link>
                    </div>

                    <button type="submit" className="btn-primary" style={{ width: '100%', marginBottom: '24px' }} disabled={isLoading}>
                        {isLoading ? 'Verifying...' : 'Sign In →'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>New to Blueberry? <Link href="/register" style={{ color: 'white', fontWeight: '800' }}>Create account</Link></p>
                </div>
            </div>
        </div>
      </div>

      <style jsx global>{`
        .auth-container {
            display: flex;
            height: 100vh;
            width: 100vw;
            background: var(--bg-main);
            overflow: hidden;
        }

        .auth-left {
            flex: 1;
            position: relative;
            background-image: url('/auth_nature_bg.png');
            background-size: cover;
            background-position: center;
            display: flex;
            align-items: center;
            padding: 80px;
        }

        .auth-overlay {
            position: absolute;
            inset: 0;
            background: linear-gradient(135deg, rgba(10, 10, 12, 0.8) 0%, rgba(10, 10, 12, 0.3) 100%);
        }

        .auth-brand-content {
            position: relative;
            z-index: 2;
            max-width: 600px;
        }

        .auth-logo {
            font-size: 24px;
            font-weight: 900;
            color: white;
            text-decoration: none;
            display: inline-block;
            margin-bottom: 40px;
            letter-spacing: -0.02em;
        }

        .auth-hero-title {
            font-size: clamp(40px, 6vw, 72px);
            color: white;
            line-height: 1.1;
            margin-bottom: 24px;
            letter-spacing: -0.03em;
        }

        .auth-hero-subtitle {
            font-size: 18px;
            color: var(--text-secondary);
            margin-bottom: 40px;
            line-height: 1.6;
        }
        
        .auth-perks {
            display: flex;
            flex-direction: column;
            gap: 16px;
        }
        
        .auth-perk {
            font-size: 14px;
            font-weight: 700;
            color: white;
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .auth-right {
            flex: 0 0 600px;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
            background: var(--bg-main);
            border-left: 1px solid var(--glass-border);
        }

        .auth-form-wrapper {
            width: 100%;
            max-width: 440px;
            padding: 56px;
            border-radius: 40px;
            border: 1px solid var(--glass-border);
        }

        .auth-header {
            margin-bottom: 40px;
        }

        .auth-header h2 {
            font-size: 32px;
            color: white;
            margin-bottom: 12px;
        }

        .auth-header p {
            color: var(--text-secondary);
            font-size: 14px;
            line-height: 1.5;
        }

        .auth-error {
            background: rgba(239, 68, 68, 0.1);
            border: 1px solid rgba(239, 68, 68, 0.2);
            color: #fca5a5;
            padding: 14px 18px;
            border-radius: 16px;
            margin-bottom: 32px;
            font-size: 13px;
            font-weight: 600;
        }

        .form-group {
            margin-bottom: 24px;
        }

        .form-group label {
            display: block;
            margin-bottom: 10px;
            color: var(--text-muted);
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }

        .glass-input {
            width: 100%;
            padding: 16px 20px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--glass-border);
            border-radius: 18px;
            color: white;
            font-size: 15px;
            outline: none;
            transition: var(--transition-smooth);
        }

        .glass-input:focus {
            border-color: var(--primary-light);
            background: rgba(255, 255, 255, 0.06);
            box-shadow: 0 0 20px rgba(76, 124, 53, 0.1);
        }

        .form-options {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 32px;
            font-size: 13px;
        }

        .remember-me {
            display: flex;
            align-items: center;
            gap: 10px;
            color: var(--text-secondary);
            cursor: pointer;
            font-weight: 600;
        }

        .auth-footer {
            text-align: center;
            color: var(--text-muted);
            font-size: 14px;
        }

        @media (max-width: 1100px) {
            .auth-right {
                flex: 0 0 500px;
            }
        }

        @media (max-width: 980px) {
            .auth-left {
                display: none;
            }
            .auth-right {
                flex: 1;
            }
            .auth-form-wrapper {
                border: none;
                background: transparent;
                padding: 0;
            }
        }
      `}</style>
    </>
  );
}

LoginPage.getLayout = function getLayout(page: React.ReactNode) {
  return page;
};
