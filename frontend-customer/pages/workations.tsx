import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../lib/api';

interface Workation {
    package_id: string;
    name: string;
    short_desc: string;
    description: string;
    category: string;
    days_count: number;
    base_pricing: {
        per_person_estimate?: number;
        currency?: string;
    };
    location_name?: string;
}

export default function Workations() {
    const router = useRouter();
    const [workations, setWorkations] = useState<Workation[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchWorkations = async () => {
            try {
                const res = await api.get('/api/v1/packages/?category=workation');
                if (res.data && res.data.packages) {
                    setWorkations(res.data.packages);
                }
            } catch (err) {
                console.error("Failed to fetch workations:", err);
                setWorkations([
                    {
                        package_id: 'harsil-workation',
                        name: 'Harsil Workation',
                        short_desc: 'Riverside cottages with fibre-optic internet and forest trails.',
                        description: 'Work from the valley of gods with high-speed connectivity.',
                        category: 'workation',
                        days_count: 30,
                        location_name: 'Uttarakhand',
                        base_pricing: { per_person_estimate: 3200 }
                    },
                    {
                        package_id: 'goa-work-hub',
                        name: 'Goa Beach Work Hub',
                        short_desc: 'Beachside co-working with community events and sundowners.',
                        description: 'A vibrant community of digital nomads by the Arabian Sea.',
                        category: 'workation',
                        days_count: 14,
                        location_name: 'Goa',
                        base_pricing: { per_person_estimate: 2800 }
                    },
                    {
                        package_id: 'coorg-estate',
                        name: 'Coorg Estate Stay',
                        short_desc: 'Boutique estate bungalows. Morning mist and mountain co-working.',
                        description: 'Find productivity in the lush coffee estates of Coorg.',
                        category: 'workation',
                        days_count: 21,
                        location_name: 'Karnataka',
                        base_pricing: { per_person_estimate: 4100 }
                    }
                ]);
            } finally {
                setLoading(false);
            }
        };
        fetchWorkations();
    }, []);

    return (
        <>
            <Head>
                <title>Workations — BlueBerryTravels.co</title>
                <meta name="description" content="Work well, live better. India's finest remote work stays in the heart of nature on BlueBerryTravels.co." />
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_workations.png')`, height: '60vh', minHeight: '500px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">Office in Nature</span>
                    <h1 className="hero-title" style={{ fontSize: 'clamp(40px, 7vw, 80px)' }}>Workations</h1>
                    <p className="hero-subtitle">Work well, live better — India&apos;s finest remote work stays.</p>
                </div>
            </div>

            <div className="discovery-container">
                {loading ? (
                    <div className="loading-grid">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="skeleton-card glass"></div>
                        ))}
                    </div>
                ) : (
                    <div className="workations-grid">
                        {workations.map(wk => (
                            <div key={wk.package_id} className="workation-card glass" onClick={() => router.push(`/packages/${wk.package_id}`)}>
                                <div className="wk-visual">
                                    <div className="wk-icon">{wk.package_id.includes('harsil') ? '🏔️' : wk.package_id.includes('goa') ? '🏖️' : '☕'}</div>
                                    <div className="wk-loc">📍 {wk.location_name || 'India'}</div>
                                </div>
                                <div className="wk-body">
                                    <h3 className="wk-name">{wk.name}</h3>
                                    <p className="wk-desc">{wk.short_desc}</p>
                                    <div className="wk-tags">
                                        <span className="mini-tag">High Speed WiFi</span>
                                        <span className="mini-tag">Power Backup</span>
                                    </div>
                                    <div className="wk-footer">
                                        <div className="wk-price">
                                            From <span>₹{wk.base_pricing.per_person_estimate?.toLocaleString()}</span>
                                            <small>/ night</small>
                                        </div>
                                        <button className="wk-btn">Explore Hub →</button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <style jsx>{`
                .discovery-container {
                    max-width: var(--main-width);
                    margin: -100px auto 100px;
                    padding: 0 var(--outer-gap);
                    position: relative;
                    z-index: 10;
                }
                
                .workations-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 32px;
                }
                
                .workation-card {
                    border-radius: 32px;
                    overflow: hidden;
                    transition: var(--transition-smooth);
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                }
                
                .workation-card:hover {
                    transform: translateY(-12px);
                    background: rgba(255, 255, 255, 0.06);
                    border-color: var(--primary-light);
                }
                
                .wk-visual {
                    height: 200px;
                    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                }
                
                .wk-icon {
                    font-size: 64px;
                    filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));
                }
                
                .wk-loc {
                    position: absolute;
                    top: 20px;
                    left: 20px;
                    background: rgba(0,0,0,0.3);
                    backdrop-filter: blur(8px);
                    padding: 6px 14px;
                    border-radius: 100px;
                    font-size: 11px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                    color: white;
                }
                
                .wk-body {
                    padding: 32px;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                
                .wk-name {
                    font-size: 24px;
                    margin-bottom: 12px;
                    color: white;
                }
                
                .wk-desc {
                    color: var(--text-secondary);
                    font-size: 15px;
                    line-height: 1.7;
                    margin-bottom: 20px;
                }
                
                .wk-tags {
                    display: flex;
                    gap: 8px;
                    margin-bottom: 24px;
                    flex: 1;
                }
                
                .mini-tag {
                    font-size: 10px;
                    font-weight: 700;
                    background: rgba(255, 255, 255, 0.05);
                    padding: 4px 10px;
                    border-radius: 100px;
                    text-transform: uppercase;
                    color: var(--text-muted);
                    border: 1px solid rgba(255,255,255,0.05);
                }
                
                .wk-footer {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding-top: 24px;
                    border-top: 1px solid var(--glass-border);
                }
                
                .wk-price {
                    font-size: 12px;
                    color: var(--text-muted);
                    font-weight: 600;
                }
                
                .wk-price span {
                    display: block;
                    font-size: 20px;
                    color: var(--primary-light);
                    font-weight: 800;
                }
                
                .wk-btn {
                    background: transparent;
                    color: white;
                    font-weight: 700;
                    font-size: 14px;
                    transition: var(--transition-smooth);
                }
                
                .workation-card:hover .wk-btn {
                    color: var(--primary-light);
                    transform: translateX(4px);
                }
                
                .loading-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 32px;
                }
                
                .skeleton-card {
                    height: 450px;
                    border-radius: 32px;
                    animation: shimmer 2s infinite linear;
                    background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%);
                    background-size: 200% 100%;
                }
                
                @keyframes shimmer {
                    0% { background-position: 200% 0; }
                    100% { background-position: -200% 0; }
                }
            `}</style>
        </>
    );
}
