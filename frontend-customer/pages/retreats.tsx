import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../lib/api';

interface Retreat {
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
}

export default function Retreats() {
    const router = useRouter();
    const [retreats, setRetreats] = useState<Retreat[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchRetreats = async () => {
            try {
                // Fetch packages with type 'retreat'
                const res = await api.get('/api/v1/packages/?category=retreat');
                if (res.data && res.data.packages) {
                    setRetreats(res.data.packages);
                }
            } catch (err) {
                console.error("Failed to fetch retreats:", err);
                // Fallback static data if API fails or is empty
                setRetreats([
                    {
                        package_id: 'isha-yoga',
                        name: 'Isha Yoga Retreat',
                        short_desc: 'Silence, sadhana, and nature at the Isha Foundation.',
                        description: 'A transformative experience in the foothills of Velliangiri mountains.',
                        category: 'retreat',
                        days_count: 7,
                        base_pricing: { per_person_estimate: 4800 }
                    },
                    {
                        package_id: 'vipassana',
                        name: 'Himalayan Vipassana',
                        short_desc: 'Traditional 10-day silent meditation in the mountains.',
                        description: 'A deep dive into silence and self-discovery in Dharamshala.',
                        category: 'retreat',
                        days_count: 10,
                        base_pricing: { per_person_estimate: 0 }
                    },
                    {
                        package_id: 'panchakarma',
                        name: 'Ayurveda Panchakarma',
                        short_desc: 'Doctor-prescribed detox and rejuvenation by the sea.',
                        description: 'Traditional healing practices in the coastal beauty of Varkala.',
                        category: 'retreat',
                        days_count: 14,
                        base_pricing: { per_person_estimate: 8200 }
                    }
                ]);
            } finally {
                setLoading(false);
            }
        };
        fetchRetreats();
    }, []);

    return (
        <>
            <Head>
                <title>Soulful Retreats — BlueBerryTravels.co</title>
                <meta name="description" content="Slow down. Reset. Return to yourself in the heart of nature with our curated soulful retreats on BlueBerryTravels.co." />
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_retreats.png')`, height: '60vh', minHeight: '500px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">Curated Stillness</span>
                    <h1 className="hero-title" style={{ fontSize: 'clamp(40px, 7vw, 80px)' }}>Soulful Retreats</h1>
                    <p className="hero-subtitle">Slow down. Reset. Return to yourself in the heart of nature.</p>
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
                    <div className="retreats-grid">
                        {retreats.map(rt => (
                            <div key={rt.package_id} className="retreat-card glass" onClick={() => router.push(`/packages/${rt.package_id}`)}>
                                <div className="rt-visual">
                                    <div className="rt-icon">{rt.package_id.includes('yoga') ? '🧘' : rt.package_id.includes('vipassana') ? '🏔️' : '🌿'}</div>
                                    <div className="rt-days">{rt.days_count} Days</div>
                                </div>
                                <div className="rt-body">
                                    <h3 className="rt-name">{rt.name}</h3>
                                    <p className="rt-desc">{rt.short_desc}</p>
                                    <div className="rt-footer">
                                        <div className="rt-price">
                                            {rt.base_pricing.per_person_estimate ? (
                                                <>From <span>₹{rt.base_pricing.per_person_estimate.toLocaleString()}</span></>
                                            ) : (
                                                <span>Donation Based</span>
                                            )}
                                        </div>
                                        <button className="rt-btn">View Journey →</button>
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
                
                .retreats-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 32px;
                }
                
                .retreat-card {
                    border-radius: 32px;
                    overflow: hidden;
                    transition: var(--transition-smooth);
                    cursor: pointer;
                    display: flex;
                    flex-direction: column;
                }
                
                .retreat-card:hover {
                    transform: translateY(-12px);
                    background: rgba(255, 255, 255, 0.06);
                    border-color: var(--primary-light);
                }
                
                .rt-visual {
                    height: 200px;
                    background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    position: relative;
                }
                
                .rt-icon {
                    font-size: 64px;
                    filter: drop-shadow(0 10px 20px rgba(0,0,0,0.2));
                }
                
                .rt-days {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background: rgba(0,0,0,0.3);
                    backdrop-filter: blur(8px);
                    padding: 6px 14px;
                    border-radius: 100px;
                    font-size: 11px;
                    font-weight: 800;
                    text-transform: uppercase;
                    letter-spacing: 0.1em;
                }
                
                .rt-body {
                    padding: 32px;
                    flex: 1;
                    display: flex;
                    flex-direction: column;
                }
                
                .rt-name {
                    font-size: 24px;
                    margin-bottom: 12px;
                    color: white;
                }
                
                .rt-desc {
                    color: var(--text-secondary);
                    font-size: 15px;
                    line-height: 1.7;
                    margin-bottom: 24px;
                    flex: 1;
                }
                
                .rt-footer {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    padding-top: 24px;
                    border-top: 1px solid var(--glass-border);
                }
                
                .rt-price {
                    font-size: 13px;
                    color: var(--text-muted);
                    font-weight: 600;
                }
                
                .rt-price span {
                    display: block;
                    font-size: 20px;
                    color: var(--primary-light);
                    font-weight: 800;
                }
                
                .rt-btn {
                    background: transparent;
                    color: white;
                    font-weight: 700;
                    font-size: 14px;
                    transition: var(--transition-smooth);
                }
                
                .retreat-card:hover .rt-btn {
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
