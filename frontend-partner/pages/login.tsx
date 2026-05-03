import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [rememberMe, setRememberMe] = useState(false);

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('partner_access_token') || localStorage.getItem('access_token');
    if (token) {
      router.push('/');
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    // Basic validation
    if (!email.trim() || !password.trim()) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/api/v1/partner/auth/login/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, login_context: 'partner' }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || data.message || 'Invalid email or password');
      }

      // Store JWT tokens in localStorage
      localStorage.setItem('partner_access_token', data.access || data.access_token);
      localStorage.setItem('access_token', data.access || data.access_token); // fallback if anything uses it
      if (data.refresh || data.refresh_token) {
        localStorage.setItem('partner_refresh_token', data.refresh || data.refresh_token);
        localStorage.setItem('refresh_token', data.refresh || data.refresh_token);
      }
      if (data.user || data.partner) {
        localStorage.setItem('user', JSON.stringify(data.user || data.partner));
      }

      // Dispatch event to notify other components
      window.dispatchEvent(new Event('auth-change'));

      // Redirect to dashboard or the page they came from
      const redirect = (router.query.redirect as string) || '/';
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
        <title>Partner Login — Blueberry Travel</title>
        <meta name="description" content="Sign in to your Blueberry Partner account to manage your business." />
      </Head>

      <div className="login-page">
        {/* Background image + overlay */}
        <div className="login-bg">
          <div className="login-bg-overlay"></div>
        </div>

        {/* Floating particles for depth */}
        <div className="login-particles">
          <span className="particle p1"></span>
          <span className="particle p2"></span>
          <span className="particle p3"></span>
          <span className="particle p4"></span>
          <span className="particle p5"></span>
        </div>

        {/* Main login card */}
        <div className="login-container">
          {/* Left side — branding */}
          <div className="login-brand-side">
            <div className="login-brand-content">
              <Link href="/" className="login-logo-mark" style={{ textDecoration: 'none' }}>
                <span className="login-logo-icon">🫐</span>
              </Link>
              <h1 className="login-brand-title">Blueberry</h1>
              <p className="login-brand-sub">Partner Portal</p>
              <div className="login-brand-divider"></div>
              <p className="login-brand-tagline">
                Grow your travel business with India's fastest growing platform
              </p>
              <div className="login-brand-features">
                <div className="login-feature">
                  <span className="login-feature-icon">📈</span>
                  <span>Manage bookings & earnings</span>
                </div>
                <div className="login-feature">
                  <span className="login-feature-icon">📅</span>
                  <span>Real-time availability sync</span>
                </div>
                <div className="login-feature">
                  <span className="login-feature-icon">🤝</span>
                  <span>Direct customer access</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right side — login form */}
          <div className="login-form-side">
            <div className="login-form-wrapper">
              <div className="login-form-header">
                <h2 className="login-form-title">Welcome back</h2>
                <p className="login-form-subtitle">Sign in to manage your business</p>
              </div>

              {router.query.registered === 'true' && (
                <div className="login-error" style={{ background: 'linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%)', borderColor: '#bbf7d0', color: '#166534' }}>
                  <span className="login-error-icon">✅</span>
                  <span>Account created successfully! Please sign in.</span>
                </div>
              )}

              {error && (
                <div className="login-error" id="login-error">
                  <span className="login-error-icon">⚠</span>
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="login-form" id="login-form">
                <div className="login-field">
                  <label htmlFor="login-email" className="login-label">Email address</label>
                  <div className="login-input-wrap">
                    <span className="login-input-icon">✉</span>
                    <input
                      id="login-email"
                      type="email"
                      className="login-input"
                      placeholder="partner@example.com"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      autoComplete="email"
                      required
                    />
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="login-password" className="login-label">Password</label>
                  <div className="login-input-wrap">
                    <span className="login-input-icon">🔒</span>
                    <input
                      id="login-password"
                      type={showPassword ? 'text' : 'password'}
                      className="login-input"
                      placeholder="Enter your password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      autoComplete="current-password"
                      required
                    />
                    <button
                      type="button"
                      className="login-toggle-pw"
                      onClick={() => setShowPassword(!showPassword)}
                      aria-label={showPassword ? 'Hide password' : 'Show password'}
                      id="toggle-password"
                    >
                      {showPassword ? '🙈' : '👁'}
                    </button>
                  </div>
                </div>

                <div className="login-options">
                  <label className="login-remember" htmlFor="remember-me">
                    <input
                      type="checkbox"
                      id="remember-me"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                    />
                    <span className="login-checkbox-custom"></span>
                    <span>Remember me</span>
                  </label>
                  <Link href="/forgot-password" className="login-forgot" id="forgot-password-link">
                    Forgot password?
                  </Link>
                </div>

                <button
                  type="submit"
                  className="login-submit-btn"
                  disabled={isLoading}
                  id="login-submit"
                >
                  {isLoading ? (
                    <span className="login-spinner-wrap">
                      <span className="login-spinner"></span>
                      <span>Signing in…</span>
                    </span>
                  ) : (
                    <span>Sign In</span>
                  )}
                </button>
              </form>

              <div className="login-divider-row">
                <span className="login-divider-line"></span>
                <span className="login-divider-text">or</span>
                <span className="login-divider-line"></span>
              </div>

              <p className="login-signup-text">
                Want to become a partner?{' '}
                <Link href={router.query.redirect ? `/register?redirect=${encodeURIComponent(router.query.redirect as string)}` : "/register"} className="login-signup-link" id="register-link">
                  Apply here
                </Link>
              </p>
            </div>
          </div>
        </div>

        {/* Bottom attribution */}
        <div className="login-footer">
          <span>© 2026 Blueberry Travel Solutions Pvt Ltd</span>
          <span className="login-footer-dot">·</span>
          <Link href="#">Partner Terms</Link>
          <span className="login-footer-dot">·</span>
          <Link href="#">Help Center</Link>
        </div>
      </div>
    </>
  );
}

// Override _app layout — login page should NOT have the standard Navbar/Footer
LoginPage.getLayout = function getLayout(page: React.ReactNode) {
  return page;
};
