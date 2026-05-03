import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import Head from 'next/head';

export default function RegisterPage() {
  const router = useRouter();
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    mobile: '',
    password: '',
    confirm_password: '',
    nationality: 'IN',
    terms_accepted: false,
  });
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      router.push('/dashboard');
    }
  }, [router]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const val = type === 'checkbox' ? (e.target as HTMLInputElement).checked : value;
    setFormData(prev => ({ ...prev, [name]: val }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    if (!formData.name.trim() || !formData.email.trim() || !formData.mobile.trim() || !formData.password.trim() || !formData.confirm_password.trim() || !formData.nationality) {
      setError('Please fill in all fields');
      setIsLoading(false);
      return;
    }

    if (formData.password !== formData.confirm_password) {
        setError('Passwords do not match');
        setIsLoading(false);
        return;
    }

    if (!formData.terms_accepted) {
        setError('Please accept the Terms & Conditions');
        setIsLoading(false);
        return;
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const res = await fetch(`${API_BASE}/api/v1/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await res.json();

      if (!res.ok) {
        const errorMsg = data.detail || data.message || (typeof data === 'object' ? Object.values(data)[0] : 'Registration failed');
        throw new Error(errorMsg as string);
      }

      router.push('/login?registered=true');
    } catch (err: any) {
      setError(err.message || 'Registration failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <Head>
        <title>Join Us | Blueberry Travels</title>
      </Head>

      <div className="auth-container">
        <div className="auth-left">
            <div className="auth-overlay"></div>
            <div className="auth-brand-content">
                <Link href="/" className="auth-logo">🫐 Blueberry</Link>
                <h1 className="auth-hero-title">Start Your Adventure</h1>
                <p className="auth-hero-subtitle">Join an exclusive community of modern explorers and unlock the full potential of the Himalayas.</p>
                <div className="auth-perks">
                    <div className="auth-perk">🏔️ Curated Hidden Gems</div>
                    <div className="auth-perk">🤝 Collaboration First Tools</div>
                    <div className="auth-perk">🍃 Sustainable Exploration</div>
                </div>
            </div>
        </div>

        <div className="auth-right">
            <div className="auth-form-wrapper glass-dark">
                <div className="auth-header">
                    <h2>Create Account</h2>
                    <p>Begin your journey with a few simple details.</p>
                </div>

                {error && (
                    <div className="auth-error">
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="auth-form">
                    <div className="form-group">
                        <label>Full Name</label>
                        <input 
                            name="name" type="text" placeholder="John Doe" 
                            className="glass-input"
                            value={formData.name} onChange={handleChange} required
                        />
                    </div>

                    <div className="form-group">
                        <label>Email Address</label>
                        <input 
                            name="email" type="email" placeholder="john@example.com" 
                            className="glass-input"
                            value={formData.email} onChange={handleChange} required
                        />
                    </div>

                    <div className="form-row">
                        <div className="form-group" style={{ flex: 1 }}>
                            <label>Mobile</label>
                            <input 
                                name="mobile" type="tel" placeholder="Mobile Number" 
                                className="glass-input"
                                value={formData.mobile} onChange={handleChange} required
                            />
                        </div>
                        <div className="form-group" style={{ width: '120px' }}>
                            <label>Nationality</label>
                            <select name="nationality" value={formData.nationality} onChange={handleChange} className="glass-input auth-select">
                                <option value="IN">Indian</option>
                                <option value="US">US</option>
                                <option value="GB">UK</option>
                                <option value="OTHER">Other</option>
                            </select>
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input 
                            name="password" type="password" placeholder="••••••••" 
                            className="glass-input"
                            value={formData.password} onChange={handleChange} required
                        />
                    </div>

                    <div className="form-group">
                        <label>Confirm Password</label>
                        <input 
                            name="confirm_password" type="password" placeholder="••••••••" 
                            className="glass-input"
                            value={formData.confirm_password} onChange={handleChange} required
                        />
                    </div>

                    <div className="checkbox-group">
                        <input 
                            name="terms_accepted" type="checkbox" id="terms"
                            checked={formData.terms_accepted} onChange={handleChange}
                        />
                        <label htmlFor="terms">I agree to the <Link href="/terms">Terms</Link> & <Link href="/privacy">Privacy Policy</Link></label>
                    </div>

                    <button type="submit" className="btn-primary" style={{ width: '100%', marginBottom: '24px', marginTop: '12px' }} disabled={isLoading}>
                        {isLoading ? 'Creating...' : 'Create Account →'}
                    </button>
                </form>

                <div className="auth-footer">
                    <p>Already a member? <Link href="/login" style={{ color: 'white', fontWeight: '800' }}>Sign In</Link></p>
                </div>
            </div>
        </div>
      </div>

      <style jsx global>{`
        /* Shared with Login.tsx styles in a real project, but duplicated here for standalone correctness */
        .auth-container { display: flex; height: 100vh; width: 100vw; background: var(--bg-main); overflow: hidden; }
        .auth-left { flex: 1; position: relative; background-image: url('/auth_nature_bg.png'); background-size: cover; background-position: center; display: flex; align-items: center; padding: 80px; }
        .auth-overlay { position: absolute; inset: 0; background: linear-gradient(135deg, rgba(10, 10, 12, 0.8) 0%, rgba(10, 10, 12, 0.3) 100%); }
        .auth-brand-content { position: relative; z-index: 2; max-width: 600px; }
        .auth-logo { font-size: 24px; font-weight: 900; color: white; text-decoration: none; display: inline-block; margin-bottom: 40px; letter-spacing: -0.02em; }
        .auth-hero-title { font-size: clamp(40px, 6vw, 72px); color: white; line-height: 1.1; margin-bottom: 24px; letter-spacing: -0.03em; }
        .auth-hero-subtitle { font-size: 18px; color: var(--text-secondary); margin-bottom: 40px; line-height: 1.6; }
        .auth-perks { display: flex; flex-direction: column; gap: 16px; }
        .auth-perk { font-size: 14px; font-weight: 700; color: white; display: flex; align-items: center; gap: 12px; }
        
        .auth-right { flex: 0 0 600px; display: flex; align-items: center; justify-content: center; padding: 40px; background: var(--bg-main); border-left: 1px solid var(--glass-border); overflow-y: auto; }
        .auth-form-wrapper { width: 100%; max-width: 480px; padding: 48px; border-radius: 40px; border: 1px solid var(--glass-border); margin: auto 0; }
        
        .auth-header { margin-bottom: 32px; }
        .auth-header h2 { font-size: 32px; color: white; margin-bottom: 12px; }
        .auth-header p { color: var(--text-secondary); font-size: 14px; }
        
        .auth-error { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #fca5a5; padding: 14px 18px; border-radius: 16px; margin-bottom: 24px; font-size: 13px; font-weight: 600; }
        
        .form-group { margin-bottom: 20px; }
        .form-row { display: flex; gap: 16px; }
        .form-group label { display: block; margin-bottom: 8px; color: var(--text-muted); font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em; }
        
        .glass-input { width: 100%; padding: 14px 18px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--glass-border); border-radius: 16px; color: white; font-size: 14px; outline: none; transition: var(--transition-smooth); }
        .glass-input:focus { border-color: var(--primary-light); background: rgba(255, 255, 255, 0.06); }
        .auth-select option { background: #111; color: white; }
        
        .checkbox-group { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
        .checkbox-group input { width: 18px; height: 18px; cursor: pointer; }
        .checkbox-group label { font-size: 13px; color: var(--text-secondary); cursor: pointer; }
        .checkbox-group a { color: var(--primary-light); text-decoration: none; font-weight: 600; }
        
        .auth-footer { text-align: center; color: var(--text-muted); font-size: 14px; }

        @media (max-width: 1100px) { .auth-right { flex: 0 0 500px; } }
        @media (max-width: 980px) { .auth-left { display: none; } .auth-right { flex: 1; } .auth-form-wrapper { border: none; background: transparent; padding: 0; } }
      `}</style>
    </>
  );
}

RegisterPage.getLayout = function getLayout(page: React.ReactNode) {
  return page;
};
