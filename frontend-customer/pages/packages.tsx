import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../lib/api';

interface Package {
    package_id: string;
    name: string;
    short_desc: string;
    description: string;
    category: string;
    days_count: number;
    base_pricing: {
        per_person_estimate?: number;
        node_total?: number;
        currency?: string;
    };
}

const CATEGORY_EMOJI: Record<string, string> = {
    adventure: '🧗', chill: '🛋️', explore: '🔭', experience: '🎭',
    workation: '💻', retreat: '🌿', cultural: '🏛️', spiritual: '🧘',
};

const CATEGORIES = ['all', 'adventure', 'chill', 'cultural', 'spiritual', 'workation', 'retreat'];

export default function Packages() {
    const router = useRouter();
    const [packages, setPackages] = useState<Package[]>([]);
    const [loading, setLoading] = useState(true);
    const [arrivingSoon, setArrivingSoon] = useState(false);
    const [activeCategory, setActiveCategory] = useState('all');

    const fetchPackages = useCallback(async (category?: string) => {
        setLoading(true);
        try {
            const url = category && category !== 'all'
                ? `/api/v1/packages/?category=${encodeURIComponent(category)}`
                : `/api/v1/packages/`;
            const res = await api.get(url);
            setPackages(res.data.packages || []);
            setArrivingSoon(res.data.arriving_soon || false);
        } catch {
            setArrivingSoon(true);
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchPackages(activeCategory);
    }, [fetchPackages, activeCategory]);

    return (
        <>
            <Head>
                <title>Curated Packages — Blueberry Travels</title>
            </Head>

            <div className="hero-image" style={{ backgroundImage: `url('/hero_packages.png')`, height: '40vh', minHeight: '350px' }}>
                <div className="hero-overlay"></div>
                <div className="hero-content">
                    <span className="hero-badge">Curated Journeys</span>
                    <h1 className="hero-title">Expert Packages</h1>
                    <p className="hero-subtitle">Meticulously planned itineraries from the archives of seasoned mountain explorers.</p>
                </div>
            </div>

            <div className="packages-container">
                <div className="filter-bar glass">
                    {CATEGORIES.map(cat => (
                        <button 
                            key={cat} 
                            className={`filter-chip ${activeCategory === cat ? 'active' : ''}`}
                            onClick={() => setActiveCategory(cat)}
                        >
                            {cat === 'all' ? 'All Journeys' : `${CATEGORY_EMOJI[cat] || '🎯'} ${cat}`}
                        </button>
                    ))}
                </div>

                {loading ? (
                    <div className="loading-grid">
                        {[1, 2, 3, 4].map(i => <div key={i} className="skeleton-card glass" />)}
                    </div>
                ) : arrivingSoon && packages.length === 0 ? (
                    <div className="empty-state glass">
                        <div className="e-icon">🌿</div>
                        <h2>Coming Soon</h2>
                        <p>Our team is currently hand-crafting premium curated journeys for this category.</p>
                        <button className="btn-primary" onClick={() => router.push('/diy')}>Build Your Own Instead →</button>
                    </div>
                ) : (
                    <div className="packages-grid">
                        {packages.map(pkg => (
                            <div key={pkg.package_id} className="package-card glass" onClick={() => router.push(`/packages/${pkg.package_id}`)}>
                                <div className="p-thumb" style={{ background: `linear-gradient(135deg, var(--primary-dark), rgba(10,10,12,0.8))` }}>
                                    <span className="p-emoji">{CATEGORY_EMOJI[pkg.category] || '🗺️'}</span>
                                </div>
                                <div className="p-body">
                                    <div className="p-meta">
                                        <span className="p-cat">#{pkg.category}</span>
                                        <span className="p-dur">⏱ {pkg.days_count} Days</span>
                                    </div>
                                    <h2 className="p-title">{pkg.name}</h2>
                                    <p className="p-desc">{pkg.short_desc}</p>
                                    <div className="p-footer">
                                        <div className="p-price">
                                            <small>From</small>
                                            <span>₹{Math.round(pkg.base_pricing?.per_person_estimate || 0).toLocaleString('en-IN')}</span>
                                        </div>
                                        <button className="btn-primary" onClick={(e) => { e.stopPropagation(); router.push(`/diy?package_id=${pkg.package_id}`); }}>
                                            Customise
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            <style jsx>{`
                .packages-container {
                    max-width: var(--main-width);
                    margin: -60px auto 100px;
                    padding: 0 var(--outer-gap);
                    position: relative;
                    z-index: 10;
                }
                
                .filter-bar {
                    display: flex; gap: 12px; padding: 20px 32px; border-radius: 24px;
                    margin-bottom: 48px; overflow-x: auto; scrollbar-width: none;
                }
                .filter-chip {
                    padding: 8px 20px; border-radius: 100px; background: rgba(255,255,255,0.05);
                    color: var(--text-muted); font-size: 13px; font-weight: 700; white-space: nowrap;
                    transition: 0.2s; text-transform: capitalize;
                }
                .filter-chip:hover { background: rgba(255,255,255,0.1); color: white; }
                .filter-chip.active { background: var(--primary); color: white; box-shadow: 0 4px 15px rgba(76,124,53,0.3); }
                
                .packages-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 32px;
                }
                
                .package-card {
                    border-radius: 32px; overflow: hidden; cursor: pointer;
                    transition: var(--transition-smooth);
                }
                .package-card:hover { transform: translateY(-8px); border-color: var(--primary-light); }
                
                .p-thumb { height: 180px; display: flex; align-items: center; justify-content: center; }
                .p-emoji { font-size: 56px; filter: drop-shadow(0 0 20px rgba(76,124,53,0.3)); }
                
                .p-body { padding: 32px; }
                .p-meta { display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--primary-light); margin-bottom: 16px; letter-spacing: 0.05em; }
                
                .p-title { font-size: 24px; color: white; margin-bottom: 12px; letter-spacing: -0.02em; }
                .p-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 24px; height: 3.2em; overflow: hidden; }
                
                .p-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 24px; border-top: 1px solid var(--glass-border); }
                .p-price { display: flex; flex-direction: column; }
                .p-price small { font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }
                .p-price span { font-size: 20px; font-weight: 900; color: white; }
                
                .loading-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 32px; }
                .skeleton-card { height: 400px; border-radius: 32px; }
                
                .empty-state { padding: 80px; text-align: center; border-radius: 40px; }
                .e-icon { font-size: 64px; margin-bottom: 24px; }
            `}</style>
        </>
    );
}
