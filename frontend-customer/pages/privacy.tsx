import React from 'react';
import Head from 'next/head';

export default function Privacy() {
    return (
        <>
            <Head>
                <title>Privacy Policy — Blueberry Travels</title>
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_privacy.png')`, height: '30vh', minHeight: '250px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <h1 className="hero-title">Privacy Policy</h1>
                    <p className="hero-subtitle">Your data privacy is our mountain promise.</p>
                </div>
            </div>

            <div className="legal-container glass">
                <div className="legal-content">
                    <p className="legal-placeholder">
                        [Privacy policy will be drafted per DPDP Act 2023 requirements and inserted here. 
                        Blueberry Travels values your privacy and ensures end-to-end encryption for your data.]
                    </p>
                    <section>
                        <h2>1. Data Collection</h2>
                        <p>We collect only the essential information needed to process your bookings and provide personalised AI recommendations. This includes your contact details, nationality, and travel preferences.</p>
                    </section>
                    <section>
                        <h2>2. Data Usage</h2>
                        <p>Your data is used to coordinate with local partners (Guides, Hotels, Transport) to ensure a seamless travel experience.</p>
                    </section>
                </div>
            </div>

            <style jsx>{`
                .legal-container {
                    max-width: 800px;
                    margin: -40px auto 100px;
                    padding: 64px;
                    border-radius: 40px;
                    position: relative;
                    z-index: 10;
                }
                .legal-content h2 { color: white; font-size: 20px; margin-bottom: 16px; margin-top: 32px; }
                .legal-content p { color: var(--text-secondary); line-height: 1.8; font-size: 15px; margin-bottom: 24px; }
                .legal-placeholder { font-style: italic; color: var(--text-muted) !important; margin-bottom: 48px; }
            `}</style>
        </>
    );
}
