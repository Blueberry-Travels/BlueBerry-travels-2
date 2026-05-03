import React from 'react';
import Head from 'next/head';

export default function Legal() {
    return (
        <>
            <Head>
                <title>Legal Terms — Blueberry Travels</title>
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_legal.png')`, height: '30vh', minHeight: '250px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <h1 className="hero-title">Legal Terms</h1>
                    <p className="hero-subtitle">Transparency and trust in every journey.</p>
                </div>
            </div>

            <div className="legal-container glass">
                <div className="legal-content">
                    <p className="legal-placeholder">
                        [Legal terms and conditions will be drafted by counsel and inserted here. 
                        Blueberry Travels committed to fair practices, sustainable tourism, and 
                        mountain safety standards.]
                    </p>
                    <section>
                        <h2>1. Booking & Cancellation</h2>
                        <p>All bookings made through the Blueberry Travels platform are subject to verification by our local partners. Cancellations are handled according to the specific policy of the service provider (Stay, Transport, or Guide).</p>
                    </section>
                    <section>
                        <h2>2. Liability & Safety</h2>
                        <p>Travelling in high-altitude regions involves inherent risks. Users must adhere to safety guidelines provided by local guides and experts.</p>
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
