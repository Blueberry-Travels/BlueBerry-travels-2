import React, { useState, useEffect, useCallback, useRef } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import type { NextPage } from 'next';
import SignatureCanvas from 'react-signature-canvas';

import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import AiBubble from '../components/AiBubble';

const API = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Attendee {
  attendee_id: string;
  name: string;
  mobile: string;
  relationship: string;
  dietary_preference: string;
  kyc_status: 'pending' | 'in_progress' | 'verified' | 'failed';
  noc_signed: boolean;
}

interface Bill {
  base_trip_cost: number;
  assistance_tier_fee: number;
  emergency_cover: number;
  gst: number;
  total: number;
  currency: string;
  assistance_tier: string;
  attendee_count: number;
}

interface DayNode {
  name?: string;
  activity_id?: string;
  day_num?: number;
  node_type?: string;
  start_time?: string;
  earliest_start?: string;
  duration_mins?: number;
  price_from?: number;
  significance_score?: number;
  category?: string;
}

interface Frame {
  frame_id: string;
  status: string;
  frame_type: string;
  region: string | null;
  trip_length_days: number | null;
  origin_city: string;
  assistance_tier: string;
  attendees: Attendee[];
  attendees_count?: number;
  all_partners_confirmed: boolean;
  bill: Bill | null;
  days: DayNode[][] | null;
  days_count?: number;
  price_snapshot_at: string | null;
}

interface Voucher {
  code: string;
  amount: number;
  currency: string;
  expiry: string | null;
  issued_for: string;
  active: boolean;
}

interface Recommendation {
  activity_id: string;
  name: string;
  short_desc: string;
  category: string;
  price_from: string;
  duration_hrs: number;
  significance_score: number;
  tone: string;
  risk_tier: string;
  is_admin_pick: boolean;
  from_other_region?: boolean;
  region_id?: number | null;
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function authHeaders(): Record<string, string> {
  if (typeof window === 'undefined') return {};
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function fmt(n: number): string {
  return `₹${Math.round(n).toLocaleString('en-IN')}`;
}

const TIER_INFO: Record<string, { emoji: string; label: string; price: string; desc: string }> = {
  none: {
    emoji: '🌿',
    label: 'Self',
    price: 'Included',
    desc: 'Full itinerary provided. You manage everything on the ground. Perfect for experienced travellers.',
  },
  basic: {
    emoji: '✨',
    label: 'Guided',
    price: '+₹1,200/person',
    desc: 'Local guide assigned. Language support, cultural context, and route navigation included.',
  },
  concierge: {
    emoji: '👑',
    label: 'Concierge',
    price: '+₹2,800/person',
    desc: 'Dedicated trip concierge. Real-time WhatsApp support, bookings managed, disruptions handled.',
  },
  premium: {
    emoji: '⭐',
    label: 'Premium',
    price: '+₹5,500/person',
    desc: 'Full-service. Private guide, priority recovery, luxury upgrades, 24/7 emergency line.',
  },
};

const TIER_ORDER = ['none', 'basic', 'concierge', 'premium'];

const CATEGORY_ICONS: Record<string, string> = {
  adventure: '🧗',
  chill: '🛋️',
  explore: '🔭',
  experience: '🎭',
  cultural: '🏛️',
  nature: '🌲',
  food: '🍽️',
  spiritual: '🧘',
  rest: '😴',
  transit: '🚗',
  stays: '🏨',
};

const STATUS_COLORS: Record<string, string> = {
  shadow: '#999',
  created: '#1B6B3A',
  planning: '#2563EB',
  payment_pending: '#D97706',
  booked: '#1B6B3A',
  in_progress: '#7C3AED',
  completed: '#6B7280',
  cancelled: '#EF4444',
};

// ─── Sub-components ──────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="card">
      <div style={{ height: 18, background: '#e8e0f0', borderRadius: 6, width: '60%', marginBottom: 12 }} />
      <div style={{ height: 13, background: '#f0ede8', borderRadius: 4, width: '100%', marginBottom: 8 }} />
      <div style={{ height: 13, background: '#f0ede8', borderRadius: 4, width: '80%' }} />
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const color = STATUS_COLORS[status] || '#999';
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      background: `${color}18`, color, border: `1px solid ${color}40`,
      borderRadius: 20, padding: '3px 10px', fontSize: 12, fontWeight: 700,
      textTransform: 'capitalize',
    }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: color, display: 'inline-block' }} />
      {status.replace('_', ' ')}
    </span>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

function Dashboard() {
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [activeFrame, setActiveFrame] = useState<Frame | null>(null);
  const [pastTrips, setPastTrips] = useState<Frame[]>([]);
  const [vouchers, setVouchers] = useState<Voucher[]>([]);
  const [tierUpdating, setTierUpdating] = useState(false);
  const [billFlash, setBillFlash] = useState(false);
  const [itineraryOpen, setItineraryOpen] = useState(false);
  const [toastMsg, setToastMsg] = useState('');

  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [recsLoading, setRecsLoading] = useState(false);
  const [cherryPickLoading, setCherryPickLoading] = useState<string | null>(null);
  const [selectedDayForAdd, setSelectedDayForAdd] = useState(1);

  // ── New attendee form state
  const [addingAttendee, setAddingAttendee] = useState(false);
  const [attendeeForm, setAttendeeForm] = useState({ name: '', mobile: '', relationship: 'self', dietary_preference: 'no_restriction' });
  const [attendeeLoading, setAttendeeLoading] = useState(false);

  // ── Day 9 Payment + NOC state
  const [nocModalActive, setNocModalActive] = useState<Attendee | null>(null);
  const sigCanvasRef = useRef<SignatureCanvas>(null);
  const [paying, setPaying] = useState(false);
  const [polling, setPolling] = useState(false);

  // ── Day 11: PDF download state
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfRemaining, setPdfRemaining] = useState<number | null>(null);

  // ── Day 11: Service bookings sidebar
  interface ServiceBooking {
    booking_id: string;
    service_type: string;
    status: string;
    date: string;
    location: string;
    partner_name: string | null;
  }
  const [serviceBookings, setServiceBookings] = useState<ServiceBooking[]>([]);

  // ── Day 12: Saved Plans state
  interface SavedPlan {
    plan_id: string;
    name: string;
    saved_at: string;
    frame_id: string;
    frame_status: string;
    region: string | null;
    days_count: number;
  }
  const [savedPlans, setSavedPlans] = useState<SavedPlan[]>([]);
  const [savingPlan, setSavingPlan] = useState(false);
  const [savePlanName, setSavePlanName] = useState('');

  const showToast = (msg: string) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(''), 3000);
  };

  // ── Fetch data on mount ──────────────────────────────────────────────────
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      router.push('/login');
      return;
    }
    fetchAll();
    // fetchServiceBookings();
    // fetchSavedPlans();
  }, []);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const headers = { ...authHeaders(), 'Content-Type': 'application/json' };

      const [tripsRes, vouchersRes] = await Promise.all([
        fetch(`${API}/api/v1/bookings/history/`, { headers }),
        fetch(`${API}/api/v1/vouchers/validate/`, { // Check if we should fetch available vouchers instead
            method: 'POST',
            headers,
            body: JSON.stringify({ code: '', booking_total: 0, region_id: '' }) 
        }),
      ]);

      if (tripsRes.ok) {
        const tripsData = await tripsRes.json();
        const all: any[] = tripsData.bookings || [];
        
        const urlParams = new URLSearchParams(window.location.search);
        const preferredId = urlParams.get('booking_id');
        
        if (preferredId) {
            showToast('🎉 Booking Successful! Your journey begins here.');
        }

        const active = (preferredId ? all.find(f => f.id === preferredId) : null) 
                    || all.find((f) => !['completed', 'cancelled'].includes(f.status));
                    
        const past = all.filter((f) => ['completed', 'cancelled'].includes(f.status));
        
        if (active) {
            setActiveFrame(active); // Map booking to Frame interface if possible
            if (preferredId && active.line_items && active.line_items.length > 0) {
                setItineraryOpen(true);
            }
        }
        setPastTrips(past);
      }

      if (vouchersRes.ok) {
        const vData = await vouchersRes.json();
        setVouchers((vData.vouchers || []).filter((v: Voucher) => v.active));
      }
    } catch (e) {
      console.warn('Dashboard fetch error:', e);
    } finally {
      setLoading(false);
    }
  }, []);

  // ── Load service bookings for sidebar (Day 11) ──────────────────────────
  const fetchServiceBookings = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/v1/service-bookings/list/`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setServiceBookings(data.bookings || []);
      }
    } catch {
      // Non-fatal
    }
  }, []);

  // ── Fetch saved plans (Day 12) ──────────────────────────────────────────
  const fetchSavedPlans = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) return;
    try {
      const res = await fetch(`${API}/api/v1/frames/saved/`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setSavedPlans(data.saved_plans || []);
      }
    } catch {
      // Non-fatal
    }
  }, []);

  // ── Save current plan (Day 12) ──────────────────────────────────────────
  const handleSavePlan = async () => {
    if (!activeFrame || !savePlanName.trim() || savingPlan) return;
    setSavingPlan(true);
    try {
      const res = await fetch(`${API}/api/v1/frames/saved/`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({
          frame_id: activeFrame.frame_id,
          name: savePlanName.trim(),
        }),
      });
      if (res.ok) {
        showToast('✓ Plan saved!');
        setSavePlanName('');
        fetchSavedPlans();
      } else {
        const err = await res.json();
        showToast(err.error || 'Could not save plan');
      }
    } catch {
      showToast('Network error');
    } finally {
      setSavingPlan(false);
    }
  };

  // ── PDF download (Day 11) ───────────────────────────────────────────────
  const handleDownloadPdf = async () => {
    if (!activeFrame || pdfLoading) return;
    if (pdfRemaining === 0) {
      showToast('PDF limit reached: 5 downloads per day. Try again tomorrow.');
      return;
    }
    setPdfLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/frames/${activeFrame.frame_id}/pdf/`, {
        headers: authHeaders(),
      });
      if (res.status === 429) {
        const d = await res.json();
        showToast(d.error || 'PDF rate limit exceeded.');
        setPdfRemaining(0);
        return;
      }
      if (!res.ok) {
        showToast('PDF generation failed — try again.');
        return;
      }
      const remaining = res.headers.get('X-PDF-Remaining');
      if (remaining !== null && remaining !== 'unknown') {
        setPdfRemaining(parseInt(remaining));
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `blueberry-trip-${activeFrame.frame_id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('✓ PDF downloaded!');
    } catch {
      showToast('Network error — PDF download failed.');
    } finally {
      setPdfLoading(false);
    }
  };

  // ── Fetch single frame (for poll after PATCH) ────────────────────────────
  const refreshFrame = useCallback(async (frameId: string) => {
    const res = await fetch(`${API}/api/v1/frames/${frameId}/`, { headers: authHeaders() });
    if (res.ok) {
      const data = await res.json();
      setActiveFrame((prev) => prev ? { ...prev, ...data } : data);
    }
  }, []);

  // ── Polling implementation
  useEffect(() => {
    if (!polling || !activeFrame) return;
    const interval = setInterval(async () => {
        const res = await fetch(`${API}/api/v1/frames/${activeFrame.frame_id}/`, { headers: authHeaders() });
        if (res.ok) {
           const data = await res.json();
           if (data.status === 'booked' || data.status === 'in_progress' || data.status === 'completed') {
              setActiveFrame((prev) => prev ? { ...prev, ...data } : data);
              setPolling(false);
              showToast('🎉 Booking Confirmed!');
           }
        }
    }, 4000);
    return () => clearInterval(interval);
  }, [polling, activeFrame]);

  // ── Assitance Tier & Day 9 ────────────────────────────────────────────────

  const selectTier = async (tier: string) => {
    if (!activeFrame || tierUpdating) return;
    if (activeFrame.assistance_tier === tier) return;

    setTierUpdating(true);
    try {
      const res = await fetch(`${API}/api/v1/frames/${activeFrame.frame_id}/patch/`, {
        method: 'PATCH',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ assistance_tier: tier }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveFrame((prev) => prev ? { ...prev, assistance_tier: data.assistance_tier, bill: data.bill } : prev);
        setBillFlash(true);
        setTimeout(() => setBillFlash(false), 800);
        showToast(`✓ Assistance tier updated to ${TIER_INFO[tier]?.label}`);
      } else {
        showToast('Could not update tier — try again');
      }
    } catch {
      showToast('Network error');
    } finally {
      setTierUpdating(false);
    }
  };

  // ── Add Attendee ──────────────────────────────────────────────────────────
  const submitAddAttendee = async () => {
    if (!activeFrame) return;
    if (!attendeeForm.name || !attendeeForm.mobile) {
      showToast('Name and mobile are required');
      return;
    }
    setAttendeeLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/attendees/`, {
        method: 'POST',
        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
        body: JSON.stringify({ frame_id: activeFrame.frame_id, ...attendeeForm }),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveFrame((prev) => prev ? { ...prev, attendees: data.attendees, bill: data.bill } : prev);
        setAddingAttendee(false);
        setAttendeeForm({ name: '', mobile: '', relationship: 'self', dietary_preference: 'no_restriction' });
        showToast('✓ Attendee added successfully');
      } else {
        const err = await res.json();
        showToast(err.error || 'Could not add attendee');
      }
    } catch {
      showToast('Network error');
    } finally {
      setAttendeeLoading(false);
    }
  };

  // ── Remove Attendee ───────────────────────────────────────────────────────
  const removeAttendee = async (attendeeId: string) => {
    if (!activeFrame) return;
    if (!confirm('Remove this attendee? Their KYC data will be purged.')) return;
    try {
      const res = await fetch(`${API}/api/v1/attendees/${attendeeId}/`, {
        method: 'DELETE',
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setActiveFrame((prev) => prev ? { ...prev, attendees: data.attendees, bill: data.bill } : prev);
        showToast('✓ Attendee removed');
      } else {
        showToast('Could not remove attendee');
      }
    } catch {
      showToast('Network error');
    }
  };

  // ── NOC and Checkout Handlers ────────────────────────────────────────────────
  const saveNoc = async () => {
    if (!sigCanvasRef.current || sigCanvasRef.current.isEmpty() || !nocModalActive || !activeFrame) {
      showToast('Please sign before saving');
      return;
    }
    try {
      const res = await fetch(`${API}/api/v1/frames/${activeFrame.frame_id}/sign_noc/`, {
          method: 'POST',
          headers: { ...authHeaders(), 'Content-Type': 'application/json' },
          body: JSON.stringify({ attendee_id: nocModalActive.attendee_id })
      });
      if (res.ok) {
          showToast(`✓ NOC signed for ${nocModalActive.name}`);
          setNocModalActive(null);
          refreshFrame(activeFrame.frame_id);
      } else {
          showToast('NOC save failed');
      }
    } catch {
      showToast('Network Error');
    }
  };

  const handleCheckout = async () => {
    if (!activeFrame) return;
    
    // Check NOC
    const unsigned = (activeFrame.attendees || []).find(a => !a.noc_signed);
    if (unsigned) {
        setNocModalActive(unsigned);
        return;
    }
    
    setPaying(true);
    try {
        const res = await fetch(`${API}/api/v1/booking/confirm/`, {
            method: 'POST',
            headers: { ...authHeaders(), 'Content-Type': 'application/json' },
            body: JSON.stringify({ frame_id: activeFrame.frame_id })
        });
        const data = await res.json();
        if (!res.ok) {
            showToast(data.error || 'Checkout failed');
            setPaying(false);
            return;
        }

        // Razorpay Options
        const options = {
            key: data.key,
            amount: data.amount,
            currency: data.currency,
            name: "BlueBerryTravels.co",
            description: "Trip Booking",
            order_id: data.order_id,
            handler: async function (response: any) {
                setPaying(true);
                setPolling(true); // Enable polling as a robust fallback
                showToast('Verifying payment... Please wait.');
                
                try {
                    const vRes = await fetch(`${API}/api/v1/booking/verify/`, {
                        method: 'POST',
                        headers: { ...authHeaders(), 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            razorpay_payment_id: response.razorpay_payment_id,
                            razorpay_order_id: response.razorpay_order_id,
                            razorpay_signature: response.razorpay_signature,
                            frame_id: data.frame_id
                        })
                    });
                    
                    if (vRes.ok) {
                        const vData = await vRes.json();
                        // Immediate local update
                        setActiveFrame((prev) => prev ? { ...prev, status: vData.status } : prev);
                        setPolling(false);
                        showToast('🎉 Booking Confirmed!');
                        await fetchAll();
                    }
                } catch (e) {
                    console.error('Verification error:', e);
                } finally {
                    setPaying(false);
                }
            },
            modal: {
                ondismiss: function() {
                    setPaying(false);
                }
            },
            prefill: {
                name: typeof window !== 'undefined' ? localStorage.getItem('user_name') : '',
            },
            theme: { color: "#1B6B3A" }
        };
        // @ts-ignore
        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', function () {
            showToast('Payment Failed');
            setPaying(false);
        });
        rzp.open();
    } catch (e) {
        showToast('Network Error - Payment Initialization Failed');
        setPaying(false);
    }
  };

  // -- Fetch recommendations for the active frame --------------------------
  const fetchRecommendations = useCallback(async (frameId: string) => {
    setRecsLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/frames/${frameId}/recommendations/`, {
        headers: authHeaders(),
      });
      if (res.ok) {
        const data = await res.json();
        setRecommendations(data.recommendations || []);
      }
    } catch {
      // Non-fatal -- recommendations are enhancement only
    } finally {
      setRecsLoading(false);
    }
  }, []);

  // Fetch recs whenever itinerary opens with a valid frame
  useEffect(() => {
    if (itineraryOpen && activeFrame?.frame_id) {
      fetchRecommendations(activeFrame.frame_id);
    }
  }, [itineraryOpen, activeFrame?.frame_id, fetchRecommendations]);

  // -- Cherry-pick an activity into the trip --------------------------------
  const handleCherryPick = async (activityId: string, activityName: string) => {
    if (!activeFrame) return;
    setCher      <style jsx global>{`
        .dash-root { 
            max-width: var(--main-width); 
            margin: 0 auto; 
            padding: 40px var(--outer-gap); 
            min-height: 100vh;
            color: white;
        }
        
        .dash-hero {
            background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary) 100%);
            border-radius: 40px;
            padding: 56px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
            box-shadow: 0 30px 60px rgba(0,0,0,0.3);
        }
        .dash-hero::after {
            content: ''; position: absolute; top: -50%; right: -20%;
            width: 80%; height: 150%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            transform: rotate(-15deg); pointer-events: none;
        }
        .dash-hero h1 { font-size: clamp(32px, 5vw, 48px); font-weight: 900; margin-bottom: 12px; letter-spacing: -0.03em; }
        .dash-hero p { color: rgba(255,255,255,0.7); font-size: 17px; max-width: 600px; line-height: 1.6; }
        
        .dash-grid { display: grid; grid-template-columns: 1fr 400px; gap: 32px; align-items: start; }
        @media(max-width: 1100px) { .dash-grid { grid-template-columns: 1fr; } }
        
        .section-title { 
            font-size: 11px; font-weight: 800; letter-spacing: 0.15em; 
            text-transform: uppercase; color: var(--primary-light); 
            margin-bottom: 20px; display: block;
        }
        
        .glass-card {
            background: var(--glass-bg);
            backdrop-filter: blur(var(--glass-blur));
            -webkit-backdrop-filter: blur(var(--glass-blur));
            border: 1px solid var(--glass-border);
            border-radius: 32px; padding: 40px; margin-bottom: 32px;
            transition: var(--transition-smooth);
        }
        .glass-card:hover { border-color: var(--primary-light); background: rgba(255,255,255,0.04); }
        .glass-card h3 { font-size: 20px; font-weight: 800; color: white; margin-bottom: 24px; display: flex; align-items: center; gap: 12px; }
        
        .meta-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 24px; margin-bottom: 32px; }
        .meta-item .label { font-size: 11px; color: var(--text-muted); margin-bottom: 8px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; }
        .meta-item .value { font-size: 16px; font-weight: 700; color: white; }
        
        .day-block { margin-bottom: 32px; }
        .day-label { font-size: 12px; font-weight: 900; text-transform: uppercase; letter-spacing: 0.1em; color: var(--primary-light); margin-bottom: 16px; }
        
        .node-row {
            display: flex; align-items: center; gap: 20px; padding: 18px 24px;
            background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
            border-radius: 20px; margin-bottom: 12px; transition: var(--transition-smooth);
        }
        .node-row:hover { background: rgba(255,255,255,0.06); border-color: var(--primary-light); transform: translateX(6px); }
        .node-icon { font-size: 24px; flex-shrink: 0; }
        .node-info { flex: 1; }
        .node-name { font-size: 16px; font-weight: 700; color: white; margin-bottom: 4px; }
        .node-meta { font-size: 13px; color: var(--text-muted); font-weight: 500; }
        
        .tier-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 12px; }
        .tier-card {
            background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border);
            border-radius: 20px; padding: 24px; cursor: pointer; transition: var(--transition-smooth); position: relative;
        }
        .tier-card:hover { border-color: var(--primary-light); transform: translateY(-4px); background: rgba(255,255,255,0.04); }
        .tier-card.selected { 
            background: rgba(76, 124, 53, 0.1); border-color: var(--primary); 
            box-shadow: 0 10px 30px rgba(76, 124, 53, 0.2); 
        }
        .tier-card.selected::after {
            content: '✓'; position: absolute; top: 16px; right: 16px; 
            font-size: 12px; font-weight: 900; color: white; 
            background: var(--primary); width: 22px; height: 22px;
            border-radius: 50%; display: flex; align-items: center; justify-content: center;
        }
        .tier-emoji { font-size: 32px; margin-bottom: 16px; }
        .tier-name { font-size: 16px; font-weight: 800; color: white; }
        .tier-price { font-size: 13px; color: var(--primary-light); font-weight: 700; margin-top: 4px; }
        .tier-desc { font-size: 12px; color: var(--text-muted); margin-top: 12px; line-height: 1.6; }
        
        .bill-row { display: flex; justify-content: space-between; align-items: center; padding: 14px 0; border-bottom: 1px solid var(--glass-border); font-size: 14px; color: var(--text-secondary); }
        .bill-row:last-child { border-bottom: none; }
        .bill-total { font-size: 24px; font-weight: 900; color: white; }
        
        .attendee-row { 
            display: flex; align-items: center; gap: 20px; padding: 20px; 
            background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); 
            border-radius: 20px; margin-bottom: 16px; 
        }
        .attendee-avatar {
            width: 48px; height: 48px; border-radius: 16px; background: var(--primary);
            color: white; display: flex; align-items: center; justify-content: center; 
            font-size: 18px; font-weight: 900; flex-shrink: 0;
        }
        .attendee-info { flex: 1; }
        .attendee-name { font-size: 16px; font-weight: 700; color: white; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;}
        .attendee-sub { font-size: 13px; color: var(--text-muted); }
        
        .history-card { padding: 24px; margin-bottom: 16px; }
        .trip-row { 
            display: flex; justify-content: space-between; align-items: center; 
            padding: 20px; background: rgba(255,255,255,0.02); border: 1px solid var(--glass-border); 
            border-radius: 20px; margin-bottom: 12px; transition: var(--transition-smooth); 
            cursor: pointer;
        }
        .trip-row:hover { background: rgba(255,255,255,0.05); border-color: var(--primary-light); transform: translateX(6px); }
        
        .voucher-card { 
            background: linear-gradient(135deg, rgba(76, 124, 53, 0.1), rgba(10, 10, 12, 0.4)); 
            border: 1px dashed var(--primary); border-radius: 24px; padding: 32px; margin-bottom: 16px;
            text-align: center;
        }
        .voucher-code { font-family: 'Outfit', monospace; font-size: 18px; font-weight: 900; color: var(--primary-light); letter-spacing: 0.2em; text-transform: uppercase; }
        .voucher-amount { font-size: 32px; font-weight: 900; color: white; margin: 12px 0; }
        
        .noc-modal {
            position: fixed; inset: 0; background: rgba(0,0,0,0.8);
            backdrop-filter: blur(15px); z-index: 3000;
            display: flex; align-items: center; justify-content: center; padding: 24px;
        }
        .noc-card {
            width: 100%; max-width: 600px; background: var(--bg-main);
            border: 1px solid var(--glass-border); border-radius: 40px; padding: 48px;
        }
        .sig-box { background: white; border-radius: 20px; margin: 24px 0; cursor: crosshair; }
        
        .toast {
            position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%);
            background: var(--primary); color: white; padding: 16px 32px;
            border-radius: 100px; font-weight: 700; z-index: 5000;
            box-shadow: 0 20px 40px rgba(0,0,0,0.4);
            animation: slide-up-fade 0.4s ease;
        }
        @keyframes slide-up-fade { from { opacity: 0; transform: translate(-50%, 20px); } to { opacity: 1; transform: translate(-50%, 0); } }
      `}</style>
gba(99, 102, 241, 0.05); border: 1px dashed rgba(99, 102, 241, 0.3); border-radius: 16px; padding: 20px; margin-bottom: 12px; }
        .voucher-code { font-family: monospace; font-size: 16px; font-weight: 700; color: var(--primary-light); letter-spacing: 0.1em; }
        .voucher-amount { font-size: 24px; font-weight: 800; color: white; margin: 8px 0; }
        .voucher-expiry { font-size: 12px; color: var(--text-secondary); }
        
        .btn-green { background: var(--primary); color: white; border: none; border-radius: 12px; padding: 12px 20px; font-size: 14px; font-weight: 700; cursor: pointer; transition: var(--transition-smooth); display: inline-flex; align-items: center; gap: 8px; }
        .btn-green:hover:not(:disabled) { background: var(--primary-dark); transform: translateY(-2px); box-shadow: 0 10px 20px rgba(99, 102, 241, 0.3); }
        .btn-green:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-ghost { background: rgba(255,255,255,0.05); color: white; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px 20px; font-size: 14px; font-weight: 600; cursor: pointer; transition: var(--transition-smooth); }
        .btn-ghost:hover:not(:disabled) { background: rgba(255,255,255,0.1); border-color: rgba(255,255,255,0.2); }
        .btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
        .btn-danger { background: rgba(239, 68, 68, 0.1); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.2); cursor: pointer; font-size: 12px; font-weight: 600; padding: 6px 12px; border-radius: 8px; transition: var(--transition-smooth); }
        .btn-danger:hover { background: rgba(239, 68, 68, 0.2); color: white; }
        .btn-link { background: none; border: none; color: var(--primary-light); font-size: 13px; font-weight: 600; cursor: pointer; transition: color 0.2s; }
        .btn-link:hover { color: white; }
        
        .toast { position: fixed; bottom: 32px; left: 50%; transform: translateX(-50%); background: rgba(20, 20, 24, 0.9); backdrop-filter: blur(12px); border: 1px solid rgba(255,255,255,0.1); color: white; padding: 16px 24px; border-radius: 100px; font-size: 14px; font-weight: 600; z-index: 9999; box-shadow: 0 20px 40px rgba(0,0,0,0.3); pointer-events: none; display: flex; align-items: center; gap: 12px; }
        
        .empty-state { text-align: center; padding: 40px 20px; color: var(--text-secondary); background: rgba(255,255,255,0.02); border: 1px dashed rgba(255,255,255,0.1); border-radius: 16px; }
        .empty-state .e-icon { font-size: 48px; margin-bottom: 16px; opacity: 0.8; }
        .empty-state p { font-size: 14px; line-height: 1.6; }
        
        .rec-section { margin-top: 32px; padding-top: 32px; border-top: 1px solid rgba(255,255,255,0.05); }
        .rec-section-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 20px; }
        .rec-section-title { font-size: 16px; font-weight: 700; color: white; margin-bottom: 4px; }
        .rec-section-sub { font-size: 13px; color: var(--text-secondary); }
        .rec-scroll { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 16px; scrollbar-width: none; }
        .rec-scroll::-webkit-scrollbar { display: none; }
        .rec-card { flex-shrink: 0; width: 240px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 20px; padding: 20px; transition: var(--transition-smooth); position: relative; }
        .rec-card:hover { background: rgba(255,255,255,0.06); border-color: var(--primary); transform: translateY(-4px); box-shadow: 0 15px 30px rgba(0,0,0,0.2); }
        .rec-card.admin-pick { background: rgba(124, 58, 237, 0.05); border-color: rgba(124, 58, 237, 0.2); }
        .rec-pick-badge { position: absolute; top: 12px; right: 12px; background: var(--secondary); color: white; font-size: 10px; font-weight: 800; padding: 4px 8px; border-radius: 10px; text-transform: uppercase; }
        .rec-category { font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; color: var(--primary-light); margin-bottom: 8px; }
        .rec-name { font-size: 15px; font-weight: 700; color: white; margin-bottom: 8px; line-height: 1.4; }
        .rec-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .rec-meta { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
        .rec-pill { background: rgba(255,255,255,0.1); border-radius: 8px; padding: 4px 10px; font-size: 11px; font-weight: 600; color: white; }
        .rec-pill.green { background: rgba(16, 185, 129, 0.2); color: #6EE7B7; }
        .btn-add-trip { width: 100%; background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.05); border-radius: 10px; padding: 10px 0; font-size: 13px; font-weight: 700; cursor: pointer; transition: var(--transition-smooth); }
        .btn-add-trip:hover:not(:disabled) { background: var(--primary); border-color: var(--primary); }
        .btn-add-trip:disabled { opacity: 0.5; cursor: not-allowed; }
        .rec-loading { display: flex; gap: 16px; overflow: hidden; }
        .rec-skeleton { flex-shrink: 0; width: 240px; height: 200px; background: linear-gradient(90deg, rgba(255,255,255,0.03) 25%, rgba(255,255,255,0.08) 50%, rgba(255,255,255,0.03) 75%); background-size: 400% 100%; border-radius: 20px; animation: shimmer-dark 1.5s infinite; }
        @keyframes shimmer-dark { 0% { background-position: 100% 0; } 100% { background-position: -100% 0; } }
        
        .day-select-bar { display: flex; gap: 12px; margin-bottom: 16px; overflow-x: auto; padding-bottom: 4px; align-items: center;}
        .day-select-label { font-size: 12px; font-weight: 700; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.1em; }
        .day-select-pill { padding: 6px 16px; border-radius: 100px; font-size: 13px; font-weight: 600; background: rgba(255,255,255,0.05); color: var(--text-secondary); cursor: pointer; transition: var(--transition-smooth); border: 1px solid transparent; white-space: nowrap; }
        .day-select-pill:hover { background: rgba(255,255,255,0.1); color: white; }
        .day-select-pill.active { background: var(--primary); color: white; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); }
    `}</style>

      <Head>
        <title>My Dashboard — BlueBerryTravels.co</title>
        <meta name="description" content="Manage your trips, itinerary, attendees, and billing on BlueBerryTravels.co." />
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
      </Head>

      <div className="dash-root">
        {/* ── Hero ── */}
        <div className="dash-hero">
          <h1>👤 Your Dashboard</h1>
          <p>Manage your trips, attendees, and billing all in one place.</p>
        </div>

        {loading ? (
          <div className="dash-grid">
            <div><SkeletonCard /><SkeletonCard /><SkeletonCard /></div>
            <div><SkeletonCard /><SkeletonCard /></div>
          </div>
        ) : (
          <div className="dash-grid">
            {/* ──────────── LEFT COLUMN ──────────── */}
            <div>

              {/* ── Active Trip Card ── */}
              {activeFrame ? (
                <div className="glass-card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                    <h3>📅 Active Trip</h3>
                    <StatusBadge status={activeFrame.status} />
                  </div>

                  <div className="meta-grid">
                    <div className="meta-item">
                      <div className="label">Region</div>
                      <div className="value">{activeFrame.region || '—'}</div>
                    </div>
                    <div className="meta-item">
                      <div className="label">Duration</div>
                      <div className="value">{activeFrame.trip_length_days ? `${activeFrame.trip_length_days} Days` : `${activeFrame.days_count || 0} Days planned`}</div>
                    </div>
                    <div className="meta-item">
                      <div className="label">Attendees</div>
                      <div className="value">{attendees.length} person{attendees.length !== 1 ? 's' : ''}</div>
                    </div>
                    <div className="meta-item">
                      <div className="label">Partners</div>
                      <div className="value" style={{ color: activeFrame.all_partners_confirmed ? '#1B6B3A' : '#D97706' }}>
                        {activeFrame.all_partners_confirmed ? '✓ All Confirmed' : 'Awaiting'}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                    <button className="btn-green" onClick={() => setItineraryOpen(!itineraryOpen)}>
                      {itineraryOpen ? '▲' : '▼'} View Itinerary
                    </button>
                    <button
                      className="btn-ghost"
                      id="btn-download-pdf"
                      onClick={handleDownloadPdf}
                      disabled={pdfLoading || pdfRemaining === 0}
                      title={pdfRemaining === 0 ? '5/day limit reached' : `Download PDF itinerary${pdfRemaining !== null ? ` (${pdfRemaining} left today)` : ''}`}
                      style={{ opacity: pdfRemaining === 0 ? 0.5 : 1 }}
                    >
                      {pdfLoading ? '⌛ Generating…' : pdfRemaining === 0 ? '🔒 PDF Limit Reached' : `↓ Download PDF${pdfRemaining !== null ? ` (${pdfRemaining} left)` : ''}`}
                    </button>
                    <button
                      className="btn-ghost"
                      id="btn-share-trip"
                      onClick={() => router.push(`/share?frame_id=${activeFrame.frame_id}`)}
                      title="Invite friends to this trip"
                    >
                      🔗 Invite Friends
                    </button>
                  </div>

                  {/* ── Day-by-day itinerary ── */}
                  {itineraryOpen && (
                    <div style={{ marginTop: 18 }}>
                      <div style={{ height: 1, background: '#f0ede8', marginBottom: 14 }} />
                      {days.length === 0 && (
                        <div className="empty-state">
                          <div className="e-icon">🗺️</div>
                          <p>Itinerary is being planned by the engine…<br />Refresh in a moment.</p>
                        </div>
                      )}
                      {days.map((dayNodes, dayIdx) => (
                        <div className="day-block" key={dayIdx}>
                          <div className="day-label">Day {dayIdx + 1}</div>
                          {(Array.isArray(dayNodes) ? dayNodes : []).map((node, ni) => (
                            <div className="node-row" key={ni}>
                              <div className="node-icon">
                                {CATEGORY_ICONS[node.category || node.node_type || 'activity'] || '📍'}
                              </div>
                              <div>
                                <div className="node-name">{node.name || `Activity ${ni + 1}`}</div>
                                <div className="node-meta">
                                  {(node.start_time || node.earliest_start) && <span>{(node.start_time || node.earliest_start)} · </span>}
                                  {node.duration_mins && <span>{Math.round(node.duration_mins / 60 * 10) / 10}hr</span>}
                                  {node.price_from ? <span> · ₹{node.price_from.toLocaleString('en-IN')}</span> : null}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ))}

                      {/* Day 10: Recommendations */}
                      {days.length > 0 && (
                        <div className="rec-section" id="recommendations-section">
                          <div className="rec-section-header">
                            <div>
                              <div className="rec-section-title">✨ You might also want to add…</div>
                              <div className="rec-section-sub">Personalised picks for your region · Cherry-pick to swap in</div>
                            </div>
                            <button
                              className="btn-ghost"
                              style={{ fontSize: 11, padding: '5px 12px' }}
                              onClick={() => activeFrame && fetchRecommendations(activeFrame.frame_id)}
                            >
                              ↻ Refresh
                            </button>
                          </div>

                          {/* Day Selector for Multi-day trips */}
                          {days.length > 1 && (
                            <div className="day-select-bar">
                              <span className="day-select-label">Add to:</span>
                              {days.map((_, idx) => (
                                <div
                                  key={idx}
                                  className={`day-select-pill${selectedDayForAdd === (idx + 1) ? ' active' : ''}`}
                                  onClick={() => setSelectedDayForAdd(idx + 1)}
                                >
                                  Day {idx + 1}
                                </div>
                              ))}
                            </div>
                          )}

                          {recsLoading ? (
                            <div className="rec-loading">
                              {[1, 2, 3].map(i => <div key={i} className="rec-skeleton" />)}
                            </div>
                          ) : recommendations.length === 0 ? (
                            <div style={{ fontSize: 13, color: '#9B8FAD', padding: '12px 0' }}>
                              No additional recommendations for this region yet.
                            </div>
                          ) : (
                            <div className="rec-scroll">
                              {recommendations.map((rec) => (
                                <div
                                  key={rec.activity_id}
                                  className={'rec-card' + (rec.is_admin_pick ? ' admin-pick' : '')}
                                  id={'rec-card-' + rec.activity_id}
                                >
                                  {rec.is_admin_pick && (
                                    <span className="rec-pick-badge">⭐ Top Pick</span>
                                  )}
                                  {rec.from_other_region && !rec.is_admin_pick && (
                                    <span className="rec-pick-badge" style={{ background: '#6B7280' }}>🌍 Nearby</span>
                                  )}
                                  <div className="rec-category">
                                    {CATEGORY_ICONS[rec.category] || '📍'} {rec.category}
                                  </div>
                                  <div className="rec-name">{rec.name}</div>
                                  <div className="rec-desc">{rec.short_desc}</div>
                                  <div className="rec-meta">
                                    <span className="rec-pill green">₹{parseInt(rec.price_from).toLocaleString('en-IN')}</span>
                                    {rec.duration_hrs > 0 && (
                                      <span className="rec-pill">{rec.duration_hrs}hr</span>
                                    )}
                                    <span className="rec-pill">{rec.risk_tier || 'low'} risk</span>
                                  </div>
                                  <button
                                    id={'btn-cherry-pick-' + rec.activity_id}
                                    className="btn-add-trip"
                                    disabled={!!cherryPickLoading || !!activeFrame?.price_snapshot_at}
                                    onClick={() => handleCherryPick(rec.activity_id, rec.name)}
                                  >
                                    {cherryPickLoading === rec.activity_id
                                      ? '⌛ Adding…'
                                      : activeFrame?.price_snapshot_at
                                      ? '🔒 Locked'
                                      : '+ Add to Trip'}
                                  </button>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                    </div>
                  )}
                </div>
              ) : (
                <div className="glass-card">
                  <div className="empty-state">
                    <div className="e-icon">🗺️</div>
                    <p>No active trip found.<br />
                      <button className="btn-link" onClick={() => router.push('/diy')}>Start planning with DIY Builder →</button>
                    </p>
                  </div>
                </div>
              )}

              {/* ── Assistance Tier Selector ── */}
              {activeFrame && (
                <div className="glass-card">
                  <h3>✨ Choose Assistance Tier</h3>
                  <p style={{ fontSize: 12, color: '#9B8FAD', marginBottom: 14 }}>
                    Select your support level. Bill updates instantly.
                    {activeFrame.price_snapshot_at && <span style={{ color: '#EF4444' }}> (Locked after payment)</span>}
                  </p>
                  <div className="tier-grid">
                    {TIER_ORDER.map((tier) => {
                      const info = TIER_INFO[tier];
                      const isSelected = activeFrame.assistance_tier === tier;
                      const locked = !!activeFrame.price_snapshot_at;
                      return (
                        <div
                          key={tier}
                          className={`tier-card${isSelected ? ' selected' : ''}${tierUpdating ? ' updating' : ''}`}
                          onClick={() => !locked && selectTier(tier)}
                          style={{ cursor: locked ? 'not-allowed' : 'pointer', opacity: locked && !isSelected ? 0.5 : 1 }}
                          role="button"
                          aria-pressed={isSelected}
                          id={`tier-${tier}`}
                        >
                          <div className="tier-emoji">{info.emoji}</div>
                          <div className="tier-name">{info.label}</div>
                          <div className="tier-price">{info.price}</div>
                          <div className="tier-desc">{info.desc}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* ── Attendees ── */}
              {activeFrame && (
                <div className="glass-card">
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                    <h3>👥 Attendees ({attendees.length})</h3>
                    {!activeFrame.price_snapshot_at && (
                      <button className="btn-green" style={{ padding: '7px 14px', fontSize: 12 }} onClick={() => setAddingAttendee(!addingAttendee)}>
                        {addingAttendee ? '✕ Cancel' : '+ Add'}
                      </button>
                    )}
                  </div>

                  {/* Add form */}
                  {addingAttendee && (
                    <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--glass-border)', borderRadius: 20, padding: 24, marginBottom: 24 }}>
                      <div className="form-row">
                        <div>
                          <div style={{ fontSize: 11, color: '#9B8FAD', marginBottom: 5 }}>Full Name *</div>
                          <input id="attendee-name" className="form-input" placeholder="e.g. Raj Sharma" value={attendeeForm.name} onChange={(e) => setAttendeeForm(p => ({...p, name: e.target.value}))} />
                        </div>
                        <div>
                          <div style={{ fontSize: 11, color: '#9B8FAD', marginBottom: 5 }}>Mobile *</div>
                          <input id="attendee-mobile" className="form-input" placeholder="9876543210" value={attendeeForm.mobile} onChange={(e) => setAttendeeForm(p => ({...p, mobile: e.target.value}))} />
                        </div>
                      </div>
                      <div className="form-row">
                        <div>
                          <div style={{ fontSize: 11, color: '#9B8FAD', marginBottom: 5 }}>Relationship</div>
                          <select id="attendee-relationship" className="form-input form-select" value={attendeeForm.relationship} onChange={(e) => setAttendeeForm(p => ({...p, relationship: e.target.value}))}>
                            <option value="self">Self</option>
                            <option value="spouse">Spouse</option>
                            <option value="child">Child</option>
                            <option value="parent">Parent</option>
                            <option value="friend">Friend</option>
                            <option value="colleague">Colleague</option>
                            <option value="other">Other</option>
                          </select>
                        </div>
                        <div>
                          <div style={{ fontSize: 11, color: '#9B8FAD', marginBottom: 5 }}>Dietary Preference</div>
                          <select id="attendee-diet" className="form-input form-select" value={attendeeForm.dietary_preference} onChange={(e) => setAttendeeForm(p => ({...p, dietary_preference: e.target.value}))}>
                            <option value="no_restriction">No Restriction</option>
                            <option value="vegetarian">Vegetarian</option>
                            <option value="non_pungent">Non-Pungent (Jain)</option>
                          </select>
                        </div>
                      </div>
                      <button className="btn-green" onClick={submitAddAttendee} disabled={attendeeLoading} id="btn-add-attendee-submit">
                        {attendeeLoading ? 'Adding…' : '✓ Add Attendee'}
                      </button>
                    </div>
                  )}

                  {attendees.length === 0 && !addingAttendee && (
                    <div className="empty-state" style={{ padding: 16 }}>
                      <p>No attendees added yet. Add travellers to this trip.</p>
                    </div>
                  )}

                  {attendees.map((a) => (
                    <div className="attendee-row" key={a.attendee_id}>
                      <div className="attendee-avatar">{a.name.charAt(0).toUpperCase()}</div>
                      <div className="attendee-info">
                        <div className="attendee-name">
                          {a.name}
                          <span className={`kyc-badge kyc-${a.kyc_status}`}>{a.kyc_status.replace('_', ' ')}</span>
                          {a.noc_signed && <span className="kyc-badge" style={{background: '#D1FAE5', color: '#065F46'}}>✓ NOC Signed</span>}
                        </div>
                        <div className="attendee-sub">
                          {a.relationship} · {a.dietary_preference.replace('_', ' ')} · 📱 {a.mobile}
                        </div>
                      </div>
                      {!activeFrame.price_snapshot_at && a.kyc_status !== 'verified' && (
                        <div style={{display: 'flex', gap: '8px'}}>
                          {!a.noc_signed && (
                            <button className="btn-ghost" style={{padding: '4px 8px', fontSize: '11px'}} onClick={() => setNocModalActive(a)}>Sign NOC</button>
                          )}
                          <button className="btn-danger" onClick={() => removeAttendee(a.attendee_id)} title="Remove attendee" id={`btn-remove-attendee-${a.attendee_id}`}>✕</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* ── Past Trips ── */}
              <div className="glass-card">
                <h3>📁 Past Trips</h3>
                {pastTrips.length === 0 ? (
                  <div className="empty-state" style={{ padding: 16 }}>
                    <p>No past trips yet. Complete your first adventure!</p>
                  </div>
                ) : (
                  pastTrips.slice(0, 5).map((t) => (
                    <div className="trip-row" key={t.frame_id}>
                      <div>
                        <div className="trip-name">{t.region || 'Trip'} {t.frame_type === 'package' ? '(Package)' : ''}</div>
                        <div className="trip-sub">
                          {t.days_count} days · {t.attendees_count} attendee{t.attendees_count !== 1 ? 's' : ''}
                          {t.price_snapshot_at && ` · ${new Date(t.price_snapshot_at).toLocaleDateString('en-IN', { month: 'short', year: 'numeric' })}`}
                        </div>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        <StatusBadge status={t.status} />
                        <button className="btn-ghost" style={{ padding: '5px 12px', fontSize: 12 }} onClick={() => router.push('/diy')}>Rebook</button>
                      </div>
                    </div>
                  ))
                )}
              </div>

            </div>

            {/* ──────────── RIGHT COLUMN ──────────── */}
            <div>

              {/* ── Trip Bill ── */}
              <div className={`glass-card${billFlash ? ' bill-flash' : ''}`}>
                <h3>💰 Trip Bill</h3>
                {bill ? (
                  <>
                    <div className="bill-row">
                      <span style={{ color: '#9B8FAD' }}>Base Trip Cost</span>
                      <span style={{ fontWeight: 600 }}>{fmt(bill.base_trip_cost)}</span>
                    </div>
                    <div className="bill-row">
                      <span style={{ color: '#9B8FAD' }}>
                        {TIER_INFO[bill.assistance_tier]?.label || 'Assistance'} Tier
                        {bill.attendee_count > 0 && ` ×${bill.attendee_count}`}
                      </span>
                      <span style={{ fontWeight: 600 }}>{fmt(bill.assistance_tier_fee)}</span>
                    </div>
                    <div className="bill-row">
                      <span style={{ color: '#9B8FAD' }}>Emergency Cover (2%)</span>
                      <span style={{ fontWeight: 600 }}>{fmt(bill.emergency_cover)}</span>
                    </div>
                    <div className="bill-row">
                      <span style={{ color: '#9B8FAD' }}>GST (5%)</span>
                      <span style={{ fontWeight: 600 }}>{fmt(bill.gst)}</span>
                    </div>
                    <div className="bill-row" style={{ borderTop: '2px solid #f0ede8', marginTop: 4, paddingTop: 12 }}>
                      <span style={{ fontWeight: 700, fontSize: 15 }}>Total</span>
                      <span className="bill-total">{fmt(bill.total)}</span>
                    </div>
                    <div style={{ marginTop: 14 }}>
                      <button className="btn-green" style={{ width: '100%', justifyContent: 'center', padding: 12, fontSize: 14 }} id="btn-confirm-pay" onClick={handleCheckout} disabled={paying || activeFrame?.status === 'booked' || activeFrame?.status === 'completed'}>
                        {activeFrame?.status === 'booked' ? '✓ Booked' : paying ? 'Processing...' : 'Confirm & Pay →'}
                      </button>
                    </div>
                    <div style={{ fontSize: 11, color: '#9B8FAD', marginTop: 8, textAlign: 'center' }}>
                      Secure payment via Razorpay · KYC required before checkout
                    </div>
                    {activeFrame?.price_snapshot_at && (
                      <div style={{ fontSize: 11, color: '#EF4444', marginTop: 6, textAlign: 'center', fontWeight: 600 }}>
                        🔒 Bill locked — payment captured
                      </div>
                    )}
                  </>
                ) : (
                  <div className="empty-state" style={{ padding: 12 }}>
                    <p>Bill will appear once your itinerary is ready.</p>
                  </div>
                )}
              </div>

              {/* ── Vouchers ── */}
              <div className="glass-card">
                <h3>🎟️ Vouchers</h3>
                {vouchers.length === 0 ? (
                  <div style={{ fontSize: 13, color: '#9B8FAD', textAlign: 'center', padding: '12px 0' }}>
                    No active vouchers. Vouchers are issued for disruptions and promotions.
                  </div>
                ) : (
                  vouchers.map((v) => (
                    <div className="voucher-card" key={v.code}>
                      <div className="voucher-code">{v.code}</div>
                      <div className="voucher-amount">{v.currency === 'INR' ? '₹' : ''}{v.amount.toLocaleString('en-IN')} credit</div>
                      <div className="voucher-expiry">
                        {v.expiry ? `Expires ${new Date(v.expiry).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}` : 'No expiry'}
                      </div>
                      <div style={{ fontSize: 11, color: '#9B8FAD', marginTop: 4 }}>{v.issued_for}</div>
                    </div>
                  ))
                )}
              </div>

              {/* ── Profile Quick View ── */}
              <div className="glass-card">
                <h3>👤 Profile</h3>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
                  <div style={{ width: 46, height: 46, borderRadius: '50%', background: 'linear-gradient(135deg,#1A1A2E,#1B6B3A)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontSize: 18, fontWeight: 700 }}>
                    {typeof window !== 'undefined' && localStorage.getItem('user_name')?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <div>
                    <div style={{ fontWeight: 700, fontSize: 14 }}>{typeof window !== 'undefined' && localStorage.getItem('user_name') || 'Traveller'}</div>
                    <div style={{ fontSize: 12, color: '#1B6B3A', marginTop: 2 }}>✓ Registered</div>
                  </div>
                </div>
                <button className="btn-ghost" style={{ width: '100%', justifyContent: 'center' }} onClick={() => showToast('Profile edit coming soon!')}>
                  Edit Profile
                </button>
              </div>

              {/* ── Day 11: Service Bookings Sidebar ── */}
              <div className="glass-card" id="service-bookings-sidebar">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
                  <h3>🛎️ Service Bookings</h3>
                  <button
                    className="btn-green"
                    style={{ padding: '6px 12px', fontSize: 11 }}
                    onClick={() => router.push('/misc')}
                  >
                    + Book
                  </button>
                </div>

                {serviceBookings.length === 0 ? (
                  <div className="empty-state" style={{ padding: 12 }}>
                    <p style={{ fontSize: 12 }}>
                      No service bookings yet.<br />
                      <button className="btn-link" onClick={() => router.push('/misc')}>
                        Book a guide or vehicle →
                      </button>
                    </p>
                  </div>
                ) : (
                  serviceBookings.slice(0, 4).map(b => {
                    const statusColor: Record<string, string> = {
                      pending_approval: '#d4a373',
                      confirmed: '#4c7c35',
                      completed: '#81c784',
                      cancelled: '#EF4444',
                    };
                    const typeEmoji: Record<string, string> = {
                      guide: '🧭', vehicle: '🚗', hotel: '🏨', cab: '🚕',
                    };
                    const color = statusColor[b.status] || '#888';
                    return (
                      <div key={b.booking_id} style={{
                        display: 'flex', alignItems: 'flex-start', gap: 10,
                        padding: '10px 12px', background: '#F9FAFB',
                        borderRadius: 10, marginBottom: 8,
                        borderLeft: `3px solid ${color}`,
                      }}>
                        <span style={{ fontSize: 20 }}>{typeEmoji[b.service_type] || '📋'}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ fontSize: 13, fontWeight: 700, color: '#111827' }}>
                            {b.service_type.charAt(0).toUpperCase() + b.service_type.slice(1)}
                          </div>
                          <div style={{ fontSize: 11, color: '#9B8FAD', marginTop: 2 }}>
                            {b.date} · {b.location}
                          </div>
                        </div>
                        <span style={{
                          fontSize: 10, fontWeight: 700,
                          background: `${color}20`, color,
                          padding: '2px 8px', borderRadius: 10, whiteSpace: 'nowrap',
                        }}>
                          {b.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    );
                  })
                )}

                {serviceBookings.length > 4 && (
                  <button className="btn-link" style={{ width: '100%', textAlign: 'center', marginTop: 4 }} onClick={() => router.push('/misc')}>
                    View all {serviceBookings.length} bookings →
                  </button>
                )}
              </div>

              {/* ── Day 12: Saved Plans ── */}
              <div className="glass-card" id="saved-plans-card">
                <h3>📌 Saved Plans</h3>

                {activeFrame && (
                  <div style={{ marginBottom: 14 }}>
                    <div style={{ fontSize: 11, color: '#9B8FAD', marginBottom: 6 }}>Save current itinerary:</div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <input
                        id="save-plan-name"
                        className="form-input"
                        placeholder="Name this plan…"
                        value={savePlanName}
                        onChange={e => setSavePlanName(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter') handleSavePlan(); }}
                        style={{ flex: 1, fontSize: 12 }}
                      />
                      <button
                        className="btn-green"
                        onClick={handleSavePlan}
                        disabled={savingPlan || !savePlanName.trim()}
                        style={{ padding: '7px 12px', fontSize: 12, whiteSpace: 'nowrap' }}
                        id="btn-save-plan"
                      >
                        {savingPlan ? '…' : '💾 Save'}
                      </button>
                    </div>
                  </div>
                )}

                {savedPlans.length === 0 ? (
                  <div className="empty-state" style={{ padding: 12 }}>
                    <p style={{ fontSize: 12 }}>
                      No saved plans yet. Save your current itinerary to bookmark it.
                    </p>
                  </div>
                ) : (
                  savedPlans.slice(0, 5).map(plan => (
                    <div
                      key={plan.plan_id}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 10,
                        padding: '10px 12px', background: 'rgba(255,255,255,0.03)',
                        borderRadius: 10, marginBottom: 8,
                        borderLeft: '3px solid var(--primary)',
                      }}
                    >
                      <span style={{ fontSize: 18, flexShrink: 0 }}>📍</span>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: 13, fontWeight: 700, color: '#1A1A2E', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {plan.name}
                        </div>
                        <div style={{ fontSize: 11, color: '#9B8FAD', marginTop: 2 }}>
                          {plan.region || 'Custom trip'} · {plan.days_count} days
                        </div>
                      </div>
                      <button
                        className="btn-ghost"
                        style={{ fontSize: 11, padding: '4px 10px', whiteSpace: 'nowrap' }}
                        onClick={() => router.push(`/dashboard?frame_id=${plan.frame_id}`)}
                      >
                        Load →
                      </button>
                    </div>
                  ))
                )}

                {savedPlans.length > 5 && (
                  <div style={{ fontSize: 11, color: '#9B8FAD', textAlign: 'center', marginTop: 4 }}>
                    +{savedPlans.length - 5} more saved plans
                  </div>
                )}
              </div>

            </div>
          </div>
        )}
      </div>

      {/* ── Toast ── */}
      {toastMsg && (
        <div className="toast">{toastMsg}</div>
      )}

      {/* ── NOC Modal ── */}
      {nocModalActive && (
        <div className="noc-modal">
          <div className="noc-card">
            <h3 style={{ marginBottom: 12, color: 'white', fontWeight: 800 }}>Sign NOC Form</h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 16 }}>{nocModalActive.name}, please acknowledge the risks associated with this trip. Draw your signature below.</p>
            <div style={{ border: '2px dashed #ccc', borderRadius: 8, marginBottom: 16, background: '#faf8f5', overflow: 'hidden' }}>
               <SignatureCanvas ref={sigCanvasRef} penColor="#1A1A2E" canvasProps={{ width: 350, height: 160, className: 'sigCanvas' }} />
            </div>
            <div style={{ display: 'flex', gap: 12, justifyContent: 'flex-end' }}>
               <button className="btn-ghost" onClick={() => { sigCanvasRef.current?.clear(); setNocModalActive(null); }}>Cancel</button>
               <button className="btn-ghost" onClick={() => sigCanvasRef.current?.clear()}>Clear</button>
               <button className="btn-green" onClick={saveNoc}>Save Signature</button>
            </div>
          </div>
        </div>
      )}
    </>
    );
}

export default Dashboard;
