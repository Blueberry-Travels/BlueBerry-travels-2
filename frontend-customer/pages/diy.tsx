import React, { useState, useEffect, useCallback, useMemo } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import IndiaMap from '../components/IndiaMap';
import api from '../lib/api';

/* ─────────────────────────────────────────────
   TYPES
   ───────────────────────────────────────────── */

interface RegionData {
  label: string;
  subtitle: string;
  states: string[];
}

interface Activity {
  id: string;
  state: string;
  region: string;
  category: 'adventure' | 'chill' | 'explore' | 'experience';
  name: string;
  desc: string;
  price: string;
}

interface ItineraryNode {
  start_time?: string;
  activity_name?: string;
  name?: string;
  node_type?: string;
  duration_mins: number;
}

interface ItineraryDay {
  day_num: number;
  nodes: ItineraryNode[];
}

/* ─────────────────────────────────────────────
   CONSTANTS
   ───────────────────────────────────────────── */

const REGIONS: Record<string, RegionData> = {
  uttar:    { label: 'Uttar',    subtitle: 'North India',   states: ['Himachal Pradesh', 'Uttarakhand', 'Rajasthan', 'Delhi / NCR'] },
  pashchim: { label: 'Pashchim', subtitle: 'West India',    states: ['Maharashtra', 'Gujarat', 'Goa'] },
  madhyam:  { label: 'Madhyam',  subtitle: 'Central India', states: ['Madhya Pradesh', 'Chhattisgarh'] },
  poorabh:  { label: 'Poorabh',  subtitle: 'East India',    states: ['West Bengal', 'Sikkim', 'Meghalaya', 'Assam'] },
  dakshin:  { label: 'Dakshin',  subtitle: 'South India',   states: ['Kerala', 'Karnataka', 'Tamil Nadu', 'Andaman'] },
};

const STEPS = [
  { id: 'region', label: 'Destination' },
  { id: 'credentials', label: 'Travellers' },
  { id: 'style', label: 'Vibe' },
  { id: 'activities', label: 'Experiences' },
  { id: 'review', label: 'Confirm' }
];

/* ─────────────────────────────────────────────
   MAIN COMPONENT
   ───────────────────────────────────────────── */

export default function Diy() {
  const router = useRouter();
  
  /* -- Wizard State -- */
  const [currentStep, setCurrentStep] = useState(0);
  
  /* -- Data State -- */
  const [selectedRegion, setSelectedRegion] = useState<string | null>(null);
  const [credentials, setCredentials] = useState({
    adults: 2,
    children: 0,
    startDate: '',
    tripDays: 4,
    season: 'spring'
  });
  const [styleValue, setStyleValue] = useState(0.5); // 0 = Pure Chill, 1 = Hardcore Adventure
  const [checklist, setChecklist] = useState<string[]>([]);
  const [activities, setActivities] = useState<Activity[]>([]);
  const [backendRegions, setBackendRegions] = useState<any[]>([]);
  const [loadingMsg, setLoadingMsg] = useState('');
  const [itinerary, setItinerary] = useState<ItineraryDay[] | null>(null);

  /* -- Handlers -- */
  
  const nextStep = () => setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0));

  const selectRegion = (id: string) => {
    setSelectedRegion(id);
    nextStep();
  };

  const handleCreateItinerary = async () => {
    if (!selectedRegion) return;
    setLoadingMsg("Orchestrating your journey...");
    try {
        const regObj = backendRegions.find(r => r.name.toLowerCase() === REGIONS[selectedRegion].label.toLowerCase());
        const payload = {
            region_id: regObj?.id,
            travel_style: styleValue,
            trip_days: credentials.tripDays,
            primary_ids: checklist,
            adults: credentials.adults,
            children: credentials.children,
            start_date: credentials.startDate
        };
        const res = await api.post('/api/v1/itinerary/build/', payload);
        if (res.data.nodes) {
            const grouped: Record<number, any[]> = {};
            res.data.nodes.forEach((node: any) => {
                if (!grouped[node.day]) grouped[node.day] = [];
                grouped[node.day].push({ ...node.activity, day_num: node.day, start_time: node.slot_time });
            });
            const formatted = Object.keys(grouped).map(day => ({
                day_num: parseInt(day),
                nodes: grouped[parseInt(day)]
            }));
            setItinerary(formatted);
            nextStep();
        }
    } catch (err) {
        console.error(err);
        alert("Failed to build itinerary. Please try again.");
    } finally {
        setLoadingMsg("");
    }
  };

  const handleBookTrip = async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
        localStorage.setItem('redirect_after_login', '/diy');
        router.push('/login');
        return;
    }
    setLoadingMsg("Securing your bookings...");
    try {
        const regObj = backendRegions.find(r => r.name.toLowerCase() === REGIONS[selectedRegion!].label.toLowerCase());
        const res = await api.post('/api/v1/bookings/', {
            region_id: regObj?.id,
            trip_start_date: credentials.startDate || new Date().toISOString().split('T')[0],
            travel_style: styleValue,
            total_guests: credentials.adults + credentials.children,
            // Additional booking logic would go here
        });
        if (res.data.booking_id) {
            router.push(`/dashboard?booking_id=${res.data.booking_id}`);
        }
    } catch (err) {
        console.error(err);
    } finally {
        setLoadingMsg("");
    }
  };

  /* -- Effects -- */
  useEffect(() => {
    const init = async () => {
        try {
            const res = await api.get('/api/v1/regions/');
            setBackendRegions(res.data.regions || []);
        } catch (err) { console.error(err); }
    };
    init();
  }, []);

  useEffect(() => {
    if (selectedRegion && backendRegions.length > 0) {
        const regObj = backendRegions.find(r => r.name.toLowerCase() === REGIONS[selectedRegion].label.toLowerCase());
        if (regObj) {
            api.get(`/api/v1/activities/?region_id=${regObj.id}`)
               .then(res => setActivities(res.data.activities || []))
               .catch(err => console.error(err));
        }
    }
  }, [selectedRegion, backendRegions]);

  return (
    <>
      <Head>
        <title>DIY Journey Builder — Blueberry Travels</title>
      </Head>

      <div className="diy-wizard">
        
        {/* PROGRESS BAR */}
        <div className="wizard-progress glass">
            {STEPS.map((s, idx) => (
                <div key={s.id} className={`step-dot ${idx <= currentStep ? 'active' : ''}`}>
                    <div className="dot-circle">{idx + 1}</div>
                    <span className="dot-label">{s.label}</span>
                    {idx < STEPS.length - 1 && <div className="dot-line"></div>}
                </div>
            ))}
        </div>

        <div className="wizard-container">
            
            {/* STEP 1: REGION */}
            {currentStep === 0 && (
                <div className="wizard-step step-region fade-in">
                    <div className="step-head">
                        <h1>Where shall we begin?</h1>
                        <p>Select a region on the map of India to start your premium journey.</p>
                    </div>
                    <div className="map-layout">
                        <div className="map-wrap glass">
                            <IndiaMap selectedRegion={selectedRegion} onRegionClick={setSelectedRegion} />
                        </div>
                        <div className="region-grid">
                            {Object.entries(REGIONS).map(([id, r]) => (
                                <div 
                                    key={id} 
                                    className={`reg-card glass ${selectedRegion === id ? 'active' : ''}`}
                                    onClick={() => setSelectedRegion(id)}
                                >
                                    <h3>{r.label}</h3>
                                    <p>{r.subtitle}</p>
                                    <span className="reg-badge">{r.states.length} States</span>
                                </div>
                            ))}
                        </div>
                    </div>
                    {selectedRegion && (
                        <div className="step-actions">
                            <button className="btn-primary" onClick={nextStep}>Continue to Travellers →</button>
                        </div>
                    )}
                </div>
            )}

            {/* STEP 2: CREDENTIALS */}
            {currentStep === 1 && (
                <div className="wizard-step step-creds fade-in">
                    <div className="step-head">
                        <h1>Define your group</h1>
                        <p>Help us calculate the perfect pace and logistics for your party.</p>
                    </div>
                    <div className="creds-form glass">
                        <div className="form-row">
                            <div className="input-group">
                                <label>Adults</label>
                                <div className="counter">
                                    <button onClick={() => setCredentials(c => ({...c, adults: Math.max(1, c.adults - 1)}))}>−</button>
                                    <span>{credentials.adults}</span>
                                    <button onClick={() => setCredentials(c => ({...c, adults: c.adults + 1}))}>+</button>
                                </div>
                            </div>
                            <div className="input-group">
                                <label>Children</label>
                                <div className="counter">
                                    <button onClick={() => setCredentials(c => ({...c, children: Math.max(0, c.children - 1)}))}>−</button>
                                    <span>{credentials.children}</span>
                                    <button onClick={() => setCredentials(c => ({...c, children: c.children + 1}))}>+</button>
                                </div>
                            </div>
                        </div>
                        <div className="form-row">
                            <div className="input-group">
                                <label>Start Date</label>
                                <input type="date" value={credentials.startDate} onChange={e => setCredentials(c => ({...c, startDate: e.target.value}))} className="glass-input" />
                            </div>
                            <div className="input-group">
                                <label>Trip Duration (Days)</label>
                                <div className="counter">
                                    <button onClick={() => setCredentials(c => ({...c, tripDays: Math.max(1, c.tripDays - 1)}))}>−</button>
                                    <span>{credentials.tripDays}</span>
                                    <button onClick={() => setCredentials(c => ({...c, tripDays: c.tripDays + 1}))}>+</button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="step-actions">
                        <button className="btn-secondary" onClick={prevStep}>Back</button>
                        <button className="btn-primary" onClick={nextStep}>Choose Your Vibe →</button>
                    </div>
                </div>
            )}

            {/* STEP 3: STYLE SLIDER */}
            {currentStep === 2 && (
                <div className="wizard-step step-style fade-in">
                    <div className="step-head">
                        <h1>Set the rhythm</h1>
                        <p>How do you want to experience the mountains?</p>
                    </div>
                    <div className="style-wrap glass">
                        <div className="slider-labels">
                            <div className={`label-vibe ${styleValue < 0.3 ? 'active' : ''}`}>
                                <span>🌿</span>
                                <h3>Pure Chill</h3>
                                <p>Slow mornings, meditation, and luxury leisure.</p>
                            </div>
                            <div className={`label-vibe ${styleValue > 0.7 ? 'active' : ''}`}>
                                <span>🏔️</span>
                                <h3>High Octane</h3>
                                <p>Summit treks, rock climbing, and rapid movement.</p>
                            </div>
                        </div>
                        <input 
                            type="range" min="0" max="1" step="0.1" 
                            value={styleValue} 
                            onChange={e => setStyleValue(parseFloat(e.target.value))} 
                            className="vibe-slider"
                        />
                        <div className="slider-hint">
                            Your style: <strong>{styleValue < 0.3 ? 'Slow & Mindful' : styleValue > 0.7 ? 'Active & Intense' : 'The Perfect Balance'}</strong>
                        </div>
                    </div>
                    <div className="step-actions">
                        <button className="btn-secondary" onClick={prevStep}>Back</button>
                        <button className="btn-primary" onClick={nextStep}>Select Experiences →</button>
                    </div>
                </div>
            )}

            {/* STEP 4: ACTIVITIES */}
            {currentStep === 3 && (
                <div className="wizard-step step-acts fade-in">
                    <div className="step-head">
                        <h1>Must-have experiences</h1>
                        <p>Pick at least 2 activities. Our engine will weave them into a logical route.</p>
                    </div>
                    <div className="acts-grid">
                        {activities.map(act => {
                            const selected = checklist.includes(act.id);
                            return (
                                <div 
                                    key={act.id} 
                                    className={`act-card glass ${selected ? 'selected' : ''}`}
                                    onClick={() => setChecklist(prev => selected ? prev.filter(x => x !== act.id) : [...prev, act.id])}
                                >
                                    <div className="act-cat">{act.category}</div>
                                    <h3>{act.name}</h3>
                                    <p>{act.desc}</p>
                                    <div className="act-price">₹{act.price || '800'}</div>
                                    <div className="act-check">{selected ? '✓' : '+'}</div>
                                </div>
                            );
                        })}
                    </div>
                    <div className="step-actions sticky">
                        <button className="btn-secondary" onClick={prevStep}>Back</button>
                        <button className="btn-primary" onClick={handleCreateItinerary} disabled={checklist.length < 1}>
                            {loadingMsg ? 'Generating Itinerary...' : 'Build My Trip →'}
                        </button>
                    </div>
                </div>
            )}

            {/* STEP 5: REVIEW */}
            {currentStep === 4 && itinerary && (
                <div className="wizard-step step-review fade-in">
                    <div className="step-head">
                        <h1>Your Premium Itinerary</h1>
                        <p>Orchestrated specifically for your group by our Himalayan engine.</p>
                    </div>
                    <div className="itinerary-display">
                        {itinerary.map(day => (
                            <div key={day.day_num} className="iti-day glass">
                                <h2>Day {day.day_num}</h2>
                                <div className="iti-nodes">
                                    {day.nodes.map((node, nIdx) => (
                                        <div key={nIdx} className="iti-node">
                                            <span className="node-time">{node.start_time}</span>
                                            <div className="node-info">
                                                <h4>{node.name || node.activity_name}</h4>
                                                <p>{node.duration_mins} mins</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                    <div className="step-actions">
                        <button className="btn-secondary" onClick={() => setCurrentStep(3)}>Refine</button>
                        <button className="btn-primary" onClick={handleBookTrip}>Confirm & Secure Booking →</button>
                    </div>
                </div>
            )}

        </div>

        {loadingMsg && (
            <div className="wizard-overlay">
                <div className="loading-state">
                    <div className="spinner"></div>
                    <h2>{loadingMsg}</h2>
                </div>
            </div>
        )}

      </div>

      <style jsx>{`
        .diy-wizard {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 40px;
        }
        
        .wizard-progress {
            display: flex;
            justify-content: space-between;
            padding: 32px 60px;
            border-radius: 32px;
            margin-bottom: 60px;
            position: sticky;
            top: 100px;
            z-index: 50;
        }
        
        .step-dot {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            position: relative;
            flex: 1;
        }
        
        .dot-circle {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: rgba(255,255,255,0.05);
            border: 1px solid var(--glass-border);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 800;
            color: var(--text-muted);
            transition: var(--transition-smooth);
            z-index: 2;
        }
        
        .step-dot.active .dot-circle {
            background: var(--primary);
            border-color: var(--primary-light);
            color: white;
            box-shadow: 0 0 20px rgba(76, 124, 53, 0.4);
        }
        
        .dot-label {
            font-size: 11px;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: var(--text-muted);
        }
        
        .step-dot.active .dot-label { color: white; }
        
        .dot-line {
            position: absolute;
            top: 20px;
            left: 50%;
            width: 100%;
            height: 2px;
            background: var(--glass-border);
            z-index: 1;
        }
        
        .step-dot.active .dot-line { background: var(--primary); }
        
        .wizard-container { min-height: 600px; }
        
        .step-head { text-align: center; margin-bottom: 60px; }
        .step-head h1 { font-size: 56px; margin-bottom: 16px; }
        .step-head p { font-size: 18px; color: var(--text-secondary); }
        
        .map-layout { display: grid; grid-template-columns: 1fr 340px; gap: 40px; }
        .map-wrap { border-radius: 40px; padding: 40px; min-height: 500px; }
        
        .region-grid { display: flex; flex-direction: column; gap: 16px; }
        .reg-card { 
            padding: 24px; border-radius: 24px; cursor: pointer; transition: var(--transition-smooth);
        }
        .reg-card:hover { transform: translateX(8px); background: rgba(255,255,255,0.08); }
        .reg-card.active { border-color: var(--primary); background: rgba(76, 124, 53, 0.1); }
        .reg-card h3 { font-size: 20px; margin-bottom: 4px; }
        .reg-card p { font-size: 13px; color: var(--text-secondary); margin-bottom: 12px; }
        .reg-badge { font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--primary-light); background: rgba(76,124,53,0.1); padding: 4px 10px; border-radius: 8px; }
        
        .creds-form { max-width: 600px; margin: 0 auto; padding: 60px; border-radius: 40px; display: flex; flex-direction: column; gap: 40px; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 40px; }
        .input-group { display: flex; flex-direction: column; gap: 12px; }
        .input-group label { font-size: 12px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); }
        
        .counter { 
            display: flex; align-items: center; justify-content: space-between; 
            background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
            border-radius: 16px; padding: 12px 20px;
        }
        .counter button { background: transparent; color: white; font-size: 20px; width: 32px; height: 32px; }
        .counter span { font-weight: 800; font-size: 18px; }
        
        .glass-input {
            background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
            border-radius: 16px; padding: 12px 20px; color: white; outline: none;
        }
        
        .style-wrap { max-width: 800px; margin: 0 auto; padding: 60px; border-radius: 40px; }
        .slider-labels { display: flex; justify-content: space-between; margin-bottom: 60px; gap: 60px; }
        .label-vibe { flex: 1; text-align: center; opacity: 0.3; transition: var(--transition-smooth); }
        .label-vibe.active { opacity: 1; transform: scale(1.1); }
        .label-vibe span { font-size: 48px; display: block; margin-bottom: 16px; }
        .label-vibe h3 { font-size: 24px; margin-bottom: 8px; }
        .label-vibe p { font-size: 14px; color: var(--text-secondary); }
        
        .vibe-slider {
            width: 100%; height: 6px; -webkit-appearance: none; background: var(--glass-border);
            border-radius: 10px; margin-bottom: 32px;
        }
        .vibe-slider::-webkit-slider-thumb {
            -webkit-appearance: none; width: 32px; height: 32px; background: var(--primary);
            border-radius: 50%; cursor: pointer; border: 4px solid white;
            box-shadow: 0 0 20px rgba(76, 124, 53, 0.4);
        }
        
        .slider-hint { text-align: center; color: var(--text-muted); font-size: 14px; }
        .slider-hint strong { color: white; }
        
        .acts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 24px; }
        .act-card { 
            padding: 32px; border-radius: 32px; cursor: pointer; transition: var(--transition-smooth);
            position: relative; border: 1px solid var(--glass-border);
        }
        .act-card:hover { transform: translateY(-8px); border-color: rgba(255,255,255,0.2); }
        .act-card.selected { border-color: var(--primary-light); background: rgba(76, 124, 53, 0.1); }
        .act-cat { font-size: 10px; font-weight: 800; text-transform: uppercase; color: var(--primary-light); margin-bottom: 12px; }
        .act-card h3 { font-size: 20px; margin-bottom: 8px; }
        .act-card p { font-size: 13px; color: var(--text-secondary); margin-bottom: 24px; line-height: 1.6; }
        .act-price { font-weight: 900; font-size: 18px; color: white; }
        .act-check { 
            position: absolute; top: 20px; right: 20px; width: 32px; height: 32px;
            border-radius: 50%; border: 1px solid var(--glass-border);
            display: flex; align-items: center; justify-content: center; font-weight: 900;
        }
        .act-card.selected .act-check { background: var(--primary); border-color: var(--primary-light); color: white; }
        
        .iti-day { margin-bottom: 32px; padding: 40px; border-radius: 32px; }
        .iti-day h2 { font-size: 24px; margin-bottom: 32px; color: var(--primary-light); }
        .iti-nodes { display: flex; flex-direction: column; gap: 24px; border-left: 2px dashed var(--glass-border); padding-left: 32px; }
        .iti-node { position: relative; }
        .iti-node::before { 
            content: ''; position: absolute; left: -37px; top: 8px; 
            width: 10px; height: 10px; background: var(--primary); border-radius: 50%; 
        }
        .node-time { font-size: 12px; font-weight: 800; color: var(--text-muted); margin-bottom: 4px; display: block; }
        .node-info h4 { font-size: 18px; color: white; }
        .node-info p { font-size: 13px; color: var(--text-secondary); }
        
        .step-actions { display: flex; justify-content: center; gap: 20px; margin-top: 60px; }
        .step-actions.sticky { position: sticky; bottom: 40px; background: rgba(12, 17, 9, 0.8); backdrop-filter: blur(20px); padding: 24px; border-radius: 24px; border: 1px solid var(--glass-border); }
        
        .wizard-overlay { position: fixed; inset: 0; background: rgba(12, 17, 9, 0.9); z-index: 1000; display: flex; align-items: center; justify-content: center; }
        .loading-state { text-align: center; }
        .spinner { width: 64px; height: 64px; border: 4px solid rgba(76, 124, 53, 0.1); border-top-color: var(--primary-light); border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 32px; }
        
        @keyframes fade-in { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .fade-in { animation: fade-in 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
      `}</style>
    </>
  );
}
