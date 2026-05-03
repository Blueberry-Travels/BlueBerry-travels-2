import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';

export default function Index() {
    const router = useRouter();
    return (
        <>
            <Head>
                <title>BlueBerryTravels.co | Modern Himalayan Journeys</title>
                <meta name="description" content="Discover curated Himalayan adventures, workations, and soulful retreats with BlueBerryTravels.co." />
            </Head>

            {/* Hero Section */}
            <section className="hero-image" style={{ backgroundImage: `url('/hero_himalayas.png')` }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">New Seasonal Departures</span>
                    <h1 className="hero-title">Experience the Himalayas Like Never Before</h1>
                    <p className="hero-subtitle">Curated journeys for the modern traveller. From high-altitude treks to soulful retreats.</p>
                    <div className="hero-actions">
                        <button className="btn-primary">Explore Journeys</button>
                        <button className="btn-secondary">Plan with AI</button>
                    </div>
                </div>
                
                {/* Scroll Indicator */}
                <div className="scroll-indicator">
                    <span className="scroll-text">Scroll to explore</span>
                    <div className="arrows">
                        <svg viewBox="0 0 24 24" className="arrow"><path d="M6 9l6 6 6-6"/></svg>
                        <svg viewBox="0 0 24 24" className="arrow"><path d="M6 9l6 6 6-6"/></svg>
                    </div>
                </div>
            </section>

            {/* Exploration Grid */}
            <section className="forest-tiles-section">
                <div className="section-header">
                    <h2 className="section-title">How would you like to travel?</h2>
                    <p className="section-desc">Choose your style and we'll handle the rest. Every journey is designed for immersion.</p>
                </div>

                <div className="forest-tiles-grid">
                    <Tile 
                        href="/diy" 
                        title="DIY Builder" 
                        subtitle="Build your own route" 
                        bg="/tile_diy.png" 
                    />
                    <Tile 
                        href="/packages" 
                        title="Signature Packages" 
                        subtitle="Browse curated plans" 
                        bg="/tile_packages.png" 
                    />
                    <Tile 
                        href="/workations" 
                        title="Workations" 
                        subtitle="Work away from routine" 
                        bg="/tile_workations.png" 
                    />
                    <Tile 
                        href="/retreats" 
                        title="Soulful Retreats" 
                        subtitle="Slow down and reset" 
                        bg="/tile_retreats.png" 
                    />
                    <Tile 
                        href="/events" 
                        title="Local Events" 
                        subtitle="Join while they're on" 
                        bg="/tile_events.png" 
                    />
                    <Tile 
                        href="/quiz" 
                        title="Travel Quiz" 
                        subtitle="Find your style" 
                        bg="/tile_quiz.png" 
                    />
                </div>
            </section>

            {/* Why Blueberry Section */}
            <section className="features-section">
                <div className="section-header">
                    <span className="section-tag">The Blueberry Edge</span>
                    <h2 className="section-title">Designed for Immersion</h2>
                </div>
                <div className="features-grid">
                    <div className="feature-card">
                        <div className="feature-icon">🌿</div>
                        <h3>Ethical Exploration</h3>
                        <p>We work exclusively with local communities to ensure your journey supports the Himalayan ecosystem.</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">✨</div>
                        <h3>Concierge AI</h3>
                        <p>Our intelligent planner learns your travel style to craft itineraries that feel uniquely yours.</p>
                    </div>
                    <div className="feature-card">
                        <div className="feature-icon">🏔️</div>
                        <h3>Expert Traverses</h3>
                        <p>Led by certified mountaineers, our treks prioritize safety without compromising on the thrill.</p>
                    </div>
                </div>
            </section>

            {/* Showcase Section */}
            <section className="showcase-section">
                <div className="showcase-content">
                    <span className="section-tag">Featured Experience</span>
                    <h2 className="showcase-title">Signature Trekking</h2>
                    <p className="showcase-description">
                        Our high-altitude traverses aren't just walks; they are spiritual transitions. 
                        Join our expert-led expeditions across the most demanding trails of the Zanskar and Spiti valleys.
                    </p>
                    <button className="btn-primary" onClick={() => router.push('/packages')}>View Departures</button>
                </div>
                <div className="showcase-media">
                    <div className="media-mask">
                        <img src="/showcase_trekking.png" alt="Signature Trekking Experience" />
                    </div>
                </div>
            </section>

            {/* Newsletter / CTA */}
            <section className="cta-banner">
                <div className="cta-inner">
                    <h2>Ready for your next adventure?</h2>
                    <p>Let our AI concierge help you find the perfect route.</p>
                    <button className="btn-primary" onClick={() => router.push('/diy')}>Start Planning →</button>
                </div>
            </section>

            <style jsx>{`
                .features-section { padding: 120px var(--outer-gap); max-width: 1440px; margin: 0 auto; }
                .features-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 40px; margin-top: 60px; }
                .feature-card { 
                    padding: 48px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); 
                    border-radius: 32px; transition: var(--transition-smooth); 
                }
                .feature-card:hover { transform: translateY(-10px); background: rgba(255,255,255,0.05); border-color: var(--primary-light); }
                .feature-icon { font-size: 40px; margin-bottom: 24px; }
                .feature-card h3 { font-size: 20px; font-weight: 800; color: white; margin-bottom: 16px; }
                .feature-card p { color: var(--text-muted); font-size: 15px; line-height: 1.6; }

                .showcase-section { 
                    display: grid; grid-template-columns: 1fr 1fr; gap: 80px; align-items: center; 
                    padding: 120px var(--outer-gap); max-width: 1440px; margin: 0 auto;
                }
                .section-tag { 
                    display: inline-block; font-size: 11px; font-weight: 800; text-transform: uppercase; 
                    letter-spacing: 0.2em; color: var(--primary-light); margin-bottom: 16px; 
                }
                .showcase-title { font-size: 48px; font-weight: 900; color: white; margin-bottom: 24px; letter-spacing: -0.02em; }
                .showcase-description { font-size: 18px; color: var(--text-muted); line-height: 1.8; margin-bottom: 40px; }
                .media-mask { border-radius: 40px; overflow: hidden; box-shadow: 0 40px 80px rgba(0,0,0,0.4); }
                .showcase-media img { width: 100%; display: block; transition: transform 0.8s ease; }
                .showcase-media:hover img { transform: scale(1.05); }

                .cta-banner { padding: 0 var(--outer-gap) 120px; }
                .cta-inner { 
                    background: linear-gradient(135deg, var(--primary-dark), var(--primary)); 
                    padding: 80px; border-radius: 48px; text-align: center; color: white;
                    box-shadow: 0 40px 100px rgba(76, 124, 53, 0.2);
                }
                .cta-inner h2 { font-size: 40px; font-weight: 900; margin-bottom: 16px; letter-spacing: -0.02em; }
                .cta-inner p { font-size: 18px; color: rgba(255,255,255,0.8); margin-bottom: 40px; }

                @media (max-width: 900px) {
                    .features-grid { grid-template-columns: 1fr; }
                    .showcase-section { grid-template-columns: 1fr; gap: 40px; }
                    .cta-inner { padding: 40px; }
                }
            `}</style>
        </>
    );
}

function Tile({ href, title, subtitle, bg }: { href: string; title: string; subtitle: string; bg: string }) {
    return (
        <Link href={href} className="forest-tile">
            <div className="forest-tile-bg" style={{ backgroundImage: `url('${bg}')` }}></div>
            <div className="forest-tile-overlay"></div>
            <div className="forest-tile-content">
                <span className="forest-tile-title">{title}</span>
                <span className="forest-tile-btn">
                    {subtitle}
                    <svg className="tile-arrow" viewBox="0 0 24 24" width="16" height="16">
                        <path d="M5 12h14m-7-7l7 7-7 7" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                </span>
            </div>
        </Link>
    );
}
