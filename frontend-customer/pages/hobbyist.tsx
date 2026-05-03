import React from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';

export default function Hobbyist() {
    const router = useRouter();
    
    const HOBBIES = [
        { id: 'photography', icon: '📷', title: 'Photography', sub: "Capture India's landscapes and culture", color: '#7d9b6e' },
        { id: 'trekking', icon: '🏔️', title: 'Trekking', sub: "High altitude trails and forest paths", color: '#5c7d50' },
        { id: 'yoga', icon: '🧘', title: 'Yoga & Meditation', sub: "Find stillness in sacred spaces", color: '#2d4c1e' },
        { id: 'culinary', icon: '🍲', title: 'Culinary Arts', sub: "Cook, eat, and travel with flavour", color: '#c9a076' },
        { id: 'wildlife', icon: '🦅', title: 'Wildlife & Birding', sub: "India's extraordinary biodiversity", color: '#3e5c2e' },
        { id: 'climbing', icon: '🧗', title: 'Rock Climbing', sub: "Vertical adventures across terrain", color: '#1B6B3A' }
    ];

    return (
        <>
            <Head>
                <title>Find Your Tribe — Blueberry Travels</title>
                <meta name="description" content="Travel shaped around what you love. Discover journeys tailored to your passions and hobbies." />
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_hobbyist.png')`, height: '50vh', minHeight: '400px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">Passion Driven</span>
                    <h1 className="hero-title" style={{ fontSize: 'clamp(40px, 7vw, 70px)' }}>Find Your Tribe</h1>
                    <p className="hero-subtitle">Travel shaped around what you love — every journey is a world of its own.</p>
                </div>
            </div>

            <div className="hobby-container">
                <div className="hobby-intro">
                    <p>Choose a passion below to start building your custom Himalayan itinerary.</p>
                </div>

                <div className="hobby-grid">
                    {HOBBIES.map(hobby => (
                        <div 
                            key={hobby.id} 
                            className="hobby-tile glass" 
                            onClick={() => router.push(`/diy?passion=${hobby.id}`)}
                        >
                            <div className="hobby-visual" style={{ background: `linear-gradient(135deg, ${hobby.color}88, ${hobby.color})` }}>
                                <span className="hobby-icon">{hobby.icon}</span>
                            </div>
                            <div className="hobby-info">
                                <h3 className="hobby-name">{hobby.title}</h3>
                                <p className="hobby-sub">{hobby.sub}</p>
                                <div className="hobby-action">
                                    <span>Explore Journey</span>
                                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <style jsx>{`
                .hobby-container {
                    max-width: var(--main-width);
                    margin: -60px auto 100px;
                    padding: 0 var(--outer-gap);
                    position: relative;
                    z-index: 10;
                }
                
                .hobby-intro {
                    text-align: center;
                    margin-bottom: 48px;
                    color: var(--text-secondary);
                    font-weight: 500;
                }
                
                .hobby-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                    gap: 32px;
                }
                
                .hobby-tile {
                    border-radius: 40px;
                    padding: 40px;
                    cursor: pointer;
                    transition: var(--transition-smooth);
                    border: 1px solid var(--glass-border);
                    display: flex;
                    flex-direction: column;
                    gap: 32px;
                }
                
                .hobby-tile:hover {
                    transform: translateY(-12px);
                    background: rgba(255, 255, 255, 0.06);
                    border-color: var(--primary-light);
                    box-shadow: 0 30px 60px rgba(0,0,0,0.2);
                }
                
                .hobby-visual {
                    width: 80px;
                    height: 80px;
                    border-radius: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    box-shadow: 0 10px 20px rgba(0,0,0,0.1);
                }
                
                .hobby-icon {
                    font-size: 32px;
                    filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
                }
                
                .hobby-info {
                    display: flex;
                    flex-direction: column;
                }
                
                .hobby-name {
                    font-size: 28px;
                    font-weight: 900;
                    margin-bottom: 8px;
                    color: white;
                }
                
                .hobby-sub {
                    font-size: 15px;
                    color: var(--text-secondary);
                    line-height: 1.6;
                    margin-bottom: 24px;
                }
                
                .hobby-action {
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    font-size: 14px;
                    font-weight: 800;
                    color: var(--primary-light);
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    transition: var(--transition-smooth);
                }
                
                .hobby-tile:hover .hobby-action {
                    gap: 20px;
                    color: white;
                }
            `}</style>
        </>
    );
}
