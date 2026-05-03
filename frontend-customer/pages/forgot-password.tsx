import React from 'react';
import Link from 'next/link';
import Head from 'next/head';

export default function ForgotPasswordPage() {
  return (
    <>
      <Head>
        <title>Forgot Password — Blueberry Travel Solutions</title>
        <meta name="description" content="Reset your password for Blueberry Travel Solutions." />
      </Head>

      <div className="login-page">
        <div className="login-bg">
          <div className="login-bg-overlay"></div>
        </div>

        <div className="login-particles">
          <span className="particle p1"></span>
          <span className="particle p2"></span>
          <span className="particle p3"></span>
        </div>

        <div className="login-container" style={{ maxWidth: 480 }}>
          <div className="login-form-side" style={{ borderRadius: 24 }}>
            <div className="login-form-wrapper">
              <div className="login-form-header">
                <div className="login-logo-mark" style={{ margin: '0 auto 16px' }}>
                  <span className="login-logo-icon">🫐</span>
                </div>
                <h2 className="login-form-title" style={{ textAlign: 'center' }}>Reset Password</h2>
                <p className="login-form-subtitle" style={{ textAlign: 'center' }}>
                  This feature will be available soon. Please contact support for help.
                </p>
              </div>

              <div style={{
                background: 'linear-gradient(135deg, #ebf6e7 0%, #f0f5ed 100%)',
                borderRadius: 14,
                padding: '24px 20px',
                textAlign: 'center',
                marginBottom: 24,
              }}>
                <p style={{ fontSize: 14, color: '#376121', margin: 0, lineHeight: 1.6 }}>
                  📧 Contact us at <strong>support@blueberrytravels.co</strong> to reset your password.
                </p>
              </div>

              <Link href="/login" className="login-submit-btn" id="back-to-login" style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                textDecoration: 'none',
                textAlign: 'center',
              }}>
                ← Back to Login
              </Link>
            </div>
          </div>
        </div>

        <div className="login-footer">
          <span>© 2026 Blueberry Travel Solutions Pvt Ltd</span>
        </div>
      </div>
    </>
  );
}

ForgotPasswordPage.getLayout = function getLayout(page: React.ReactNode) {
  return page;
};
