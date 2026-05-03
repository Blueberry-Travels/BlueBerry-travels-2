import React from 'react';
import Link from 'next/link';

export default function Footer() {
    return (
        <footer className="site-footer">
            <div className="footer-content">
                <div className="footer-brand">
                    <h2 className="footer-logo">BlueBerry<span>Travels.co</span></h2>
                    <p className="footer-tagline">Crafting extraordinary Himalayan experiences since 2024.</p>
                </div>

                <div className="footer-links-grid">
                    <div className="footer-col">
                        <h4>Exploration</h4>
                        <Link href="/diy">Itinerary Builder</Link>
                        <Link href="/packages">Signature Journeys</Link>
                        <Link href="/retreats">Yoga & Wellness</Link>
                        <Link href="/workations">Remote Work Hubs</Link>
                    </div>
                    <div className="footer-col">
                        <h4>Trust & Safety</h4>
                        <Link href="/legal">Terms of Service</Link>
                        <Link href="/privacy">Privacy Shield</Link>
                        <Link href="/legal#refunds">Refund Policy</Link>
                        <Link href="/legal#safety">Safety Protocols</Link>
                    </div>
                    <div className="footer-col">
                        <h4>Concierge</h4>
                        <a href="mailto:concierge@blueberrytravels.co">concierge@blueberrytravels.co</a>
                        <a href="mailto:ops@blueberrytravels.co">ops@blueberrytravels.co</a>
                        <Link href="/contact">Help Center</Link>
                        <Link href="/join">Become a Partner</Link>
                    </div>
                </div>
            </div>

            <div className="footer-bottom">
                <p>&copy; 2026 BlueBerryTravels.co | Registered Office: Himachal Pradesh, India</p>
                <div className="footer-meta">
                    BlueBerryTravels.co — Crafting the Future of Travel.
                </div>
            </div>

            <style jsx>{`
                .site-footer {
                    background: #08080A;
                    padding: 100px var(--outer-gap) 40px;
                    border-top: 1px solid rgba(76, 124, 53, 0.1);
                }
                .footer-content {
                    display: grid;
                    grid-template-columns: 1fr 2fr;
                    gap: 80px;
                    margin-bottom: 80px;
                    max-width: 1440px;
                    margin-left: auto;
                    margin-right: auto;
                }
                .footer-logo {
                    font-size: 32px;
                    font-weight: 900;
                    margin-bottom: 16px;
                    letter-spacing: -0.03em;
                    color: white;
                }
                .footer-logo span {
                    color: var(--primary);
                }
                .footer-tagline {
                    color: var(--text-muted);
                    max-width: 320px;
                    line-height: 1.6;
                    font-size: 15px;
                }
                .footer-links-grid {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 60px;
                }
                .footer-col h4 {
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.15em;
                    color: white;
                    margin-bottom: 32px;
                    font-weight: 800;
                }
                .footer-col :global(a) {
                    display: block;
                    color: var(--text-muted);
                    margin-bottom: 16px;
                    font-size: 14px;
                    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
                    font-weight: 500;
                }
                .footer-col :global(a:hover) {
                    color: var(--primary-light);
                    transform: translateX(6px);
                }
                .footer-bottom {
                    display: flex;
                    justify-content: space-between;
                    padding-top: 40px;
                    border-top: 1px solid rgba(255, 255, 255, 0.03);
                    color: var(--text-muted);
                    font-size: 13px;
                    max-width: 1440px;
                    margin: 0 auto;
                }
                .footer-meta {
                    color: var(--primary-light);
                    font-weight: 700;
                    letter-spacing: 0.05em;
                    text-transform: uppercase;
                    font-size: 11px;
                }
                @media (max-width: 800px) {
                    .footer-content { grid-template-columns: 1fr; gap: 40px; }
                    .footer-links-grid { gap: 30px; }
                }
            `}</style>
        </footer>
    );
}
