import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function RegisterPage() {
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    business_name: '',
    email: '',
    mobile: '',
    partner_type: 'hotel',
    password: '',
  });
  
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  // Check if already logged in
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      router.push('/');
    }
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!formData.business_name.trim() || !formData.email.trim() || !formData.mobile.trim() || !formData.password.trim() || !formData.partner_type) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/api/v1/partner/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMsg = data.detail || data.message || (typeof data === 'object' ? Object.values(data)[0] : 'Registration failed');
        throw new Error(errorMsg as string);
      }

      const redirect = router.query.redirect;
      const loginUrl = redirect ? `/login?registered=true&redirect=${encodeURIComponent(redirect as string)}` : '/login?registered=true';
      router.push(loginUrl);
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Apply as Partner — Blueberry Travel</title>
        <meta name="description" content="Apply to become a Blueberry Partner and grow your travel business." />
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

          {/* Right side — register form */}
          <div className="login-form-side">
            <div className="login-form-wrapper" style={{ maxWidth: '380px' }}>
              <div className="login-form-header" style={{ marginBottom: '20px' }}>
                <h2 className="login-form-title">Apply as Partner</h2>
                <p className="login-form-subtitle">Join us to start getting more bookings</p>
              </div>

              {error && (
                <div className="login-error" id="register-error" style={{ marginBottom: '16px' }}>
                  <span className="login-error-icon">⚠</span>
                  <span>{error}</span>
                </div>
              )}

              <form onSubmit={handleSubmit} className="login-form" id="register-form" style={{ gap: '14px' }}>
                
                <div className="login-field">
                  <label htmlFor="reg-name" className="login-label">Business / Partner Name</label>
                  <div className="login-input-wrap" style={{ height: '44px' }}>
                    <span className="login-input-icon">💼</span>
                    <input
                      id="reg-name"
                      name="business_name"
                      type="text"
                      className="login-input"
                      placeholder="e.g. Himalayan Stays"
                      value={formData.business_name}
                      onChange={handleChange}
                      required
                    />
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="reg-email" className="login-label">Business Email address</label>
                  <div className="login-input-wrap" style={{ height: '44px' }}>
                    <span className="login-input-icon">✉</span>
                    <input
                      id="reg-email"
                      name="email"
                      type="email"
                      className="login-input"
                      placeholder="contact@yourbusiness.com"
                      value={formData.email}
                      onChange={handleChange}
                      autoComplete="email"
                      required
                    />
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="reg-mobile" className="login-label">Mobile Number</label>
                  <div className="login-input-wrap" style={{ height: '44px' }}>
                    <span className="login-input-icon">📱</span>
                    <input
                      id="reg-mobile"
                      name="mobile"
                      type="tel"
                      className="login-input"
                      placeholder="+91 98765 43210"
                      value={formData.mobile}
                      onChange={handleChange}
                      autoComplete="tel"
                      required
                    />
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="reg-type" className="login-label">Partner Type</label>
                  <div className="login-input-wrap" style={{ height: '44px' }}>
                    <span className="login-input-icon">🏢</span>
                    <select
                      id="reg-type"
                      name="partner_type"
                      className="login-input"
                      value={formData.partner_type}
                      onChange={handleChange}
                      required
                      style={{ cursor: 'pointer' }}
                    >
                      <option value="hotel">Hotel / Accommodation</option>
                      <option value="vehicle">Vehicle / Transport Provider</option>
                      <option value="guide">Local Guide</option>
                      <option value="activity_provider">Activity Provider</option>
                    </select>
                  </div>
                </div>

                <div className="login-field">
                  <label htmlFor="reg-password" className="login-label">Password</label>
                  <div className="login-input-wrap" style={{ height: '44px' }}>
                    <span className="login-input-icon">🔒</span>
                    <input
                      id="reg-password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      className="login-input"
                      placeholder="Create a secure password"
                      value={formData.password}
                      onChange={handleChange}
                      autoComplete="new-password"
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

                <button
                  type="submit"
                  className="login-submit-btn"
                  disabled={isLoading}
                  id="register-submit"
                  style={{ marginTop: '8px', height: '48px' }}
                >
                  {isLoading ? (
                    <span className="login-spinner-wrap">
                      <span className="login-spinner"></span>
                      <span>Submitting Application…</span>
                    </span>
                  ) : (
                    <span>Apply as Partner</span>
                  )}
                </button>
              </form>

              <div className="login-divider-row" style={{ margin: '16px 0' }}>
                <span className="login-divider-line"></span>
                <span className="login-divider-text">or</span>
                <span className="login-divider-line"></span>
              </div>

              <p className="login-signup-text" style={{ marginTop: '10px' }}>
                Already an approved partner?{' '}
                <Link href={router.query.redirect ? `/login?redirect=${encodeURIComponent(router.query.redirect as string)}` : "/login"} className="login-signup-link" id="login-link">
                  Sign in
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

// Override _app layout — register page should NOT have the standard Navbar/Footer
RegisterPage.getLayout = function getLayout(page: React.ReactNode) {
  return page;
};
