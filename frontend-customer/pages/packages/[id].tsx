import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../../lib/api';

interface PackageDetail {
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
    itinerary?: {
        day: number;
        title: string;
        desc: string;
        location: string;
    }[];
}

export default function PackageDetails() {
    const router = useRouter();
    const { id } = router.query;
    const [pkg, setPkg] = useState<PackageDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (!id) return;
        const fetchPackage = async () => {
            setLoading(true);
            try {
                const res = await api.get(`/api/v1/packages/${id}/`);
                setPkg(res.data);
            } catch (err) {
                console.error("Failed to fetch package:", err);
                setError(true);
            } finally {
                setLoading(false);
            }
        };
        fetchPackage();
    }, [id]);

    if (loading) {
        return (
            <div className="loading-state">
                <div className="spinner"></div>
                <p>Curating your journey details...</p>
            </div>
        );
    }

    if (error || !pkg) {
        return (
            <div className="error-state">
                <div className="error-icon">🍃</div>
                <h2>Path Not Found</h2>
                <p>The journey you seek is currently unavailable in our archives.</p>
                <button className="btn-primary" onClick={() => router.push('/packages')}>Back to Packages</button>
            </div>
        );
    }

    return (
        <>
            <Head>
                <title>{pkg.name} — Blueberry Travels</title>
                <meta name="description" content={pkg.short_desc} />
            </Head>

            <div className="detail-hero" style={{ backgroundImage: `url('/hero_package_detail.png')` }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">{pkg.category}</span>
                    <h1 className="hero-title">{pkg.name}</h1>
                    <p className="hero-subtitle">{pkg.short_desc}</p>
                    <div className="hero-meta-row">
                        <div className="meta-pill">⏱ {pkg.days_count} Days</div>
                        <div className="meta-pill">🏔️ Himalayas</div>
                        <div className="meta-pill">👥 Small Group</div>
                    </div>
                </div>
            </div>

            <div className="detail-layout">
                <div className="detail-main">
                    <section className="detail-section glass">
                        <h2 className="section-header">The Experience</h2>
                        <div className="rich-text" dangerouslySetInnerHTML={{ __html: pkg.description.replace(/\n/g, '<br/>') }} />
                    </section>

                    <section className="detail-section glass">
                        <h2 className="section-header">Route & Itinerary</h2>
                        <div className="itinerary-timeline">
                            {(pkg.itinerary || [
                                { day: 1, title: 'Arrival & Forest Immersive', desc: 'Arrive at the base camp. Forest bathing and evening tea by the stream.', location: 'Base Camp' },
                                { day: 2, title: 'The High Pass Trek', desc: 'Ascend to the ridge for 360° views of the snow-capped range.', location: 'Silver Ridge' },
                                { day: 3, title: 'Heritage & Homeward', desc: 'Visit a 400-year old temple and local village before departure.', location: 'Old Village' }
                            ]).map((day, idx) => (
                                <div key={idx} className="timeline-item">
                                    <div className="timeline-marker">
                                        <div className="day-circle">Day {day.day}</div>
                                        <div className="line"></div>
                                    </div>
                                    <div className="timeline-content">
                                        <h3>{day.title}</h3>
                                        <span className="loc-tag">📍 {day.location}</span>
                                        <p>{day.desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </section>
                </div>

                <aside className="detail-sidebar">
                    <div className="booking-card glass-dark">
                        <div className="price-box">
                            <span className="price-label">Starting from</span>
                            <div className="price-value">
                                <span>₹{Math.round(pkg.base_pricing?.per_person_estimate || 14500).toLocaleString('en-IN')}</span>
                                <small>/ person</small>
                            </div>
                        </div>
                        <p className="booking-note">Inclusive of premium stay, expert guides, and mountain permits.</p>
                        
                        <button className="btn-primary" style={{ width: '100%' }} onClick={() => router.push(`/diy?package_id=${pkg.package_id}`)}>
                            Customise & Book →
                        </button>

                        <div className="perk-list">
                            <div className="perk">🛡️ 100% Safety Track Record</div>
                            <div className="perk">🍃 Sustainable & Low Impact</div>
                            <div className="perk">🧭 Certified Mountain Experts</div>
                        </div>
                    </div>
                </aside>
            </div>

            <style jsx>{`
                .loading-state, .error-state {
                    min-height: 80vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    text-align: center;
                    padding: 40px;
                }
                
                .spinner {
                    width: 48px;
                    height: 48px;
                    border: 3px solid rgba(76, 124, 53, 0.1);
                    border-top-color: var(--primary-light);
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    margin-bottom: 24px;
                }
                
                @keyframes spin { to { transform: rotate(360deg); } }
                
                .detail-hero {
                    height: 60vh;
                    min-height: 500px;
                    background-size: cover;
                    background-position: center;
                    position: relative;
                    display: flex;
                    align-items: center;
                    padding: 0 var(--outer-gap);
                }
                
                .hero-content {
                    position: relative;
                    z-index: 5;
                    max-width: 900px;
                }
                
                .hero-title {
                    font-size: clamp(40px, 8vw, 80px);
                    line-height: 1;
                    margin-bottom: 24px;
                }
                
                .hero-meta-row {
                    display: flex;
                    gap: 16px;
                    margin-top: 32px;
                }
                
                .meta-pill {
                    padding: 8px 20px;
                    background: rgba(255,255,255,0.05);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 100px;
                    font-size: 13px;
                    font-weight: 700;
                }
                
                .detail-layout {
                    max-width: var(--main-width);
                    margin: -100px auto 100px;
                    padding: 0 var(--outer-gap);
                    display: grid;
                    grid-template-columns: 1fr 380px;
                    gap: 48px;
                    position: relative;
                    z-index: 10;
                }
                
                .detail-section {
                    padding: 48px;
                    border-radius: 40px;
                    margin-bottom: 40px;
                }
                
                .section-header {
                    font-size: 32px;
                    margin-bottom: 32px;
                    color: white;
                }
                
                .rich-text {
                    font-size: 17px;
                    line-height: 1.8;
                    color: var(--text-secondary);
                }
                
                .itinerary-timeline {
                    display: flex;
                    flex-direction: column;
                }
                
                .timeline-item {
                    display: flex;
                    gap: 32px;
                }
                
                .timeline-marker {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    width: 80px;
                    flex-shrink: 0;
                }
                
                .day-circle {
                    width: 80px;
                    height: 80px;
                    background: var(--primary);
                    border-radius: 24px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-weight: 900;
                    color: white;
                    font-size: 14px;
                    box-shadow: 0 10px 20px rgba(76, 124, 53, 0.3);
                }
                
                .line {
                    width: 2px;
                    flex: 1;
                    background: var(--glass-border);
                    margin: 10px 0;
                }
                
                .timeline-item:last-child .line { display: none; }
                
                .timeline-content {
                    padding-bottom: 48px;
                }
                
                .timeline-content h3 {
                    font-size: 22px;
                    margin-bottom: 8px;
                    color: white;
                }
                
                .loc-tag {
                    display: inline-block;
                    font-size: 11px;
                    font-weight: 800;
                    text-transform: uppercase;
                    color: var(--primary-light);
                    margin-bottom: 16px;
                }
                
                .timeline-content p {
                    font-size: 15px;
                    color: var(--text-secondary);
                    line-height: 1.7;
                }
                
                .booking-card {
                    padding: 48px;
                    border-radius: 40px;
                    position: sticky;
                    top: 120px;
                    border: 1px solid var(--glass-border);
                }
                
                .price-box {
                    margin-bottom: 24px;
                }
                
                .price-label {
                    font-size: 12px;
                    font-weight: 800;
                    text-transform: uppercase;
                    color: var(--text-muted);
                    display: block;
                    margin-bottom: 8px;
                }
                
                .price-value {
                    display: flex;
                    align-items: baseline;
                    gap: 8px;
                }
                
                .price-value span {
                    font-size: 40px;
                    font-weight: 900;
                    color: white;
                }
                
                .price-value small {
                    font-size: 16px;
                    color: var(--text-muted);
                }
                
                .booking-note {
                    font-size: 13px;
                    color: var(--text-muted);
                    line-height: 1.6;
                    margin-bottom: 40px;
                }
                
                .perk-list {
                    margin-top: 40px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                
                .perk {
                    font-size: 13px;
                    font-weight: 600;
                    color: var(--text-secondary);
                }
                
                @media (max-width: 1000px) {
                    .detail-layout { grid-template-columns: 1fr; }
                    .detail-sidebar { order: -1; }
                    .booking-card { position: static; }
                }
            `}</style>
        </>
    );
}
