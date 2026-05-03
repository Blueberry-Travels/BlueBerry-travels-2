import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import {
    fetchDashboardStats, fetchBookings, fetchNotifications,
    fetchAvailability, updateAvailability, fetchPayouts,
    fetchServices, createService, updateService,
    updateBookingStatus, logout,
} from '../lib/api';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Booking {
    id: string;
    frame_id: string;
    date: string;
    customer: string;
    service: string;
    pax: number;
    value: string;
    status: string;
}

interface AvailabilitySlot {
    date: string;
    status: string;
}

interface Service {
    service_id: string;
    service_type: string;
    name: string;
    reg_number?: string;
    category: string;
    capacity?: number;
    price: string;
    active: boolean;
}

interface PartnerNotification {
    id: string;
    title: string;
    body: string;
    time: string;
    unread: boolean;
}

interface Payout {
    earning_id: string;
    period?: string;
    gross: string;
    commission_rate: number;
    net: string;
    status: string;
    paid_date?: string;
}

// ─── Shared Components ────────────────────────────────────────────────────────

const ModalBackdrop = ({ children, onClose }: { children: React.ReactNode; onClose: () => void }) => (
    <div
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(4px)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 20 }}
        onClick={onClose}
    >
        <div onClick={e => e.stopPropagation()} className="pp-card" style={{ width: '100%', maxWidth: 500, marginBottom: 0 }}>
            {children}
        </div>
    </div>
);

function AddServiceModal({ onClose, onSave }: { onClose: () => void; onSave: (data: any) => void }) {
    const [form, setForm] = useState({
        service_type: 'vehicle',
        reg_number: '',
        type: 'suv',
        capacity: '4',
        price_per_day: '3000',
    });
    const [saving, setSaving] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setSaving(true);
        try {
            await onSave({ ...form, capacity: parseInt(form.capacity), price_per_day: parseFloat(form.price_per_day) });
            onClose();
        } finally { setSaving(false); }
    };

    return (
        <ModalBackdrop onClose={onClose}>
            <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-dark)', marginBottom: 20 }}><span>➕</span> Add New Resource</h3>
            <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div>
                    <label className="ps-label" style={{ margin: '0 0 6px', color: 'var(--text-muted)' }}>Category</label>
                    <select className="btn-sm outline" style={{ width: '100%', textAlign: 'left', borderRadius: 12, padding: '10px 14px' }} value={form.type} onChange={e => setForm(f => ({ ...f, type: e.target.value }))}>
                        <option value="suv">SUV / MUV</option>
                        <option value="sedan">Sedan</option>
                        <option value="tempo">Tempo Traveller</option>
                        <option value="room">Hotel Room</option>
                    </select>
                </div>
                <div>
                    <label className="ps-label" style={{ margin: '0 0 6px', color: 'var(--text-muted)' }}>Registration / Room No *</label>
                    <input className="btn-sm outline" style={{ width: '100%', textAlign: 'left', borderRadius: 12, padding: '10px 14px' }} required placeholder="e.g. HP-01-A-1234" value={form.reg_number} onChange={e => setForm(f => ({ ...f, reg_number: e.target.value }))} />
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                    <div>
                        <label className="ps-label" style={{ margin: '0 0 6px', color: 'var(--text-muted)' }}>Capacity (pax)</label>
                        <input className="btn-sm outline" style={{ width: '100%', textAlign: 'left', borderRadius: 12, padding: '10px 14px' }} type="number" value={form.capacity} onChange={e => setForm(f => ({ ...f, capacity: e.target.value }))} />
                    </div>
                    <div>
                        <label className="ps-label" style={{ margin: '0 0 6px', color: 'var(--text-muted)' }}>Base Price (₹)</label>
                        <input className="btn-sm outline" style={{ width: '100%', textAlign: 'left', borderRadius: 12, padding: '10px 14px' }} type="number" value={form.price_per_day} onChange={e => setForm(f => ({ ...f, price_per_day: e.target.value }))} />
                    </div>
                </div>
                <div style={{ display: 'flex', gap: 12, marginTop: 12 }}>
                    <button type="submit" className="btn-sm" style={{ flex: 1, borderRadius: 12, background: 'var(--primary)', color: '#fff', fontWeight: 700 }} disabled={saving}>{saving ? 'Saving...' : 'Confirm Registration'}</button>
                    <button type="button" className="btn-sm outline" style={{ flex: 1, borderRadius: 12 }} onClick={onClose}>Cancel</button>
                </div>
            </form>
        </ModalBackdrop>
    );
}

function BookingDetailModal({ bookings, onClose }: { bookings: Booking[]; onClose: () => void }) {
    const b = bookings[0]; // Simplified for now
    return (
        <ModalBackdrop onClose={onClose}>
            <h3 style={{ fontSize: 20, fontWeight: 800, color: 'var(--text-dark)', marginBottom: 20 }}><span>📄</span> Booking Details</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                <div style={{ background: 'rgba(76, 124, 53, 0.05)', padding: 20, borderRadius: 16 }}>
                    <div style={{ fontSize: 11, color: 'var(--primary)', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>Reference</div>
                    <div style={{ fontSize: 20, fontWeight: 900, color: 'var(--primary-dark)', marginTop: 4 }}>BBT-{b.id.slice(0, 8)}</div>
                </div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
                    <div><label className="ps-label" style={{ margin: '0 0 4px', color: 'var(--text-muted)' }}>Customer</label><div style={{ fontWeight: 700, color: 'var(--text-dark)' }}>{b.customer}</div></div>
                    <div><label className="ps-label" style={{ margin: '0 0 4px', color: 'var(--text-muted)' }}>Service</label><div style={{ fontWeight: 700, color: 'var(--text-dark)' }}>{b.service}</div></div>
                    <div><label className="ps-label" style={{ margin: '0 0 4px', color: 'var(--text-muted)' }}>Date</label><div style={{ fontWeight: 600 }}>{b.date}</div></div>
                    <div><label className="ps-label" style={{ margin: '0 0 4px', color: 'var(--text-muted)' }}>Guests</label><div style={{ fontWeight: 600 }}>{b.pax} Person(s)</div></div>
                </div>
                <div style={{ marginTop: 8, padding: '0 4px' }}>
                    <label className="ps-label" style={{ margin: '0 0 4px', color: 'var(--text-muted)' }}>Payout Value</label>
                    <div style={{ fontSize: 28, fontWeight: 900, color: 'var(--text-dark)' }}>₹{parseInt(b.value || '0').toLocaleString()}</div>
                </div>
                <button className="btn-sm" style={{ marginTop: 12, borderRadius: 12, background: 'var(--primary)', color: '#fff', fontWeight: 700, padding: '12px' }} onClick={onClose}>Close View</button>
            </div>
        </ModalBackdrop>
    );
}

// ─── Main Portal Component ────────────────────────────────────────────────────

export default function PartnerPortal() {
    const [activeSection, setActiveSection] = useState('dashboard');
    const [stats, setStats] = useState<any>(null);
    const [partner, setPartner] = useState<any>(null);
    const [bookings, setBookings] = useState<Booking[]>([]);
    const [bookingFilter, setBookingFilter] = useState('all');
    const [notifications, setNotifications] = useState<PartnerNotification[]>([]);
    const [slots, setSlots] = useState<AvailabilitySlot[]>([]);
    const [calMonth, setCalMonth] = useState({ year: new Date().getFullYear(), month: new Date().getMonth() });
    const [payouts, setPayouts] = useState<Payout[]>([]);
    const [earningsSummary, setEarningsSummary] = useState<any>(null);
    const [monthlyChart, setMonthlyChart] = useState<Record<string, number>>({});
    const [services, setServices] = useState<Service[]>([]);
    const [servicesLoading, setServicesLoading] = useState(false);
    const [showAddService, setShowAddService] = useState(false);
    const [viewingBookings, setViewingBookings] = useState<Booking[] | null>(null);
    const [loading, setLoading] = useState(true);
    const router = useRouter();

    const loadBookings = useCallback(async () => {
        try {
            const b = await fetchBookings();
            setBookings(Array.isArray(b) ? b : []);
        } catch { /* ignore */ }
    }, []);

    const loadServices = useCallback(async () => {
        setServicesLoading(true);
        try {
            const s = await fetchServices();
            setServices(s.services || []);
        } catch { /* ignore */ } finally { setServicesLoading(false); }
    }, []);

    const handleAddService = async (data: any) => {
        try {
            await createService(data);
            await loadServices();
            setShowAddService(false);
        } catch (err) { console.error(err); }
    };

    useEffect(() => {
        const loadAll = async () => {
            try {
                const [dashData, bData, nData, aData, pData] = await Promise.all([
                    fetchDashboardStats(), fetchBookings(), fetchNotifications(), fetchAvailability(), fetchPayouts()
                ]);
                setPartner(dashData.partner);
                setStats(dashData.stats);
                setBookings(Array.isArray(bData) ? bData : []);
                setNotifications(Array.isArray(nData) ? nData : []);
                setSlots(aData.slots || []);
                setPayouts(pData.payouts || []);
                setEarningsSummary(pData.summary || null);
                setMonthlyChart(pData.monthly_chart || {});
            } catch { /* api.ts handles 401 */ } finally { setLoading(false); }
        };
        loadAll();
        loadServices();
    }, [loadServices]);

    const handleBookingAction = async (bookingId: string, status: 'confirmed' | 'rejected') => {
        try {
            await updateBookingStatus(bookingId, status);
            await loadBookings();
            const dashData = await fetchDashboardStats();
            setStats(dashData.stats);
        } catch (err) { console.error(err); }
    };

    const handleToggleServiceActive = async (id: string, current: boolean) => {
        try {
            await updateService(id, { active: !current });
            await loadServices();
        } catch (err) { console.error(err); }
    };

    // Calendar Helpers
    const MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
    const getDaysInMonth = (y: number, m: number) => new Date(y, m + 1, 0).getDate();
    const getFirstDayOfMonth = (y: number, m: number) => {
        const d = new Date(y, m, 1).getDay();
        return d === 0 ? 6 : d - 1;
    };

    const toggleCalDate = async (date: string) => {
        const slot = slots.find(s => s.date === date);
        const newStatus = slot?.status === 'blocked' ? 'available' : 'blocked';
        await updateAvailability(date, newStatus);
        const a = await fetchAvailability();
        setSlots(a.slots || []);
    };

    if (loading) return <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading Partner OS...</div>;

    const pendingCount = bookings.filter(b => b.status === 'pending' || b.status === 'planned').length;
    const daysInMonth = getDaysInMonth(calMonth.year, calMonth.month);
    const firstDay = getFirstDayOfMonth(calMonth.year, calMonth.month);
    const today = new Date();
    const isCurrentMonth = today.getFullYear() === calMonth.year && today.getMonth() === calMonth.month;

    return (
        <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
            <Head><title>Partner OS — BlueBerryTravels.co</title></Head>

            <div className="pp-topbar">
                <div className="pp-logo">BlueBerryTravels<span>.</span>co</div>
                <span className="pp-badge">B2B ENGINE</span>
                <nav className="pp-nav">
                    <a href="#" className={activeSection === 'dashboard' ? 'active' : ''} onClick={() => setActiveSection('dashboard')}>Dashboard</a>
                    <a href="#" className={activeSection === 'bookings' ? 'active' : ''} onClick={() => setActiveSection('bookings')}>Live Ops</a>
                    <a href="#" onClick={() => setActiveSection('inventory')}>Inventory</a>
                </nav>
                <div className="pp-partner-chip">
                    <div className="dot"></div>
                    <span>{partner?.name || 'Partner'}</span>
                </div>
            </div>

            <div className="pp-layout">
                <div className="pp-sidebar">
                    <div className="ps-label">OPERATIONS</div>
                    <div className={`ps-item ${activeSection === 'dashboard' ? 'active' : ''}`} onClick={() => setActiveSection('dashboard')}><span className="ps-icon">📊</span> Dashboard</div>
                    <div className={`ps-item ${activeSection === 'bookings' ? 'active' : ''}`} onClick={() => setActiveSection('bookings')}><span className="ps-icon">📅</span> Bookings {pendingCount > 0 && <span className="ps-badge warn">{pendingCount}</span>}</div>
                    <div className={`ps-item ${activeSection === 'calendar' ? 'active' : ''}`} onClick={() => setActiveSection('calendar')}><span className="ps-icon">🕒</span> Availability</div>
                    <div className="ps-label">MANAGEMENT</div>
                    <div className={`ps-item ${activeSection === 'inventory' ? 'active' : ''}`} onClick={() => { setActiveSection('inventory'); loadServices(); }}><span className="ps-icon">📦</span> Inventory</div>
                    <div className={`ps-item ${activeSection === 'earnings' ? 'active' : ''}`} onClick={() => setActiveSection('earnings')}><span className="ps-icon">💰</span> Earnings</div>
                    <div className={`ps-item ${activeSection === 'notifications' ? 'active' : ''}`} onClick={() => setActiveSection('notifications')}><span className="ps-icon">🔔</span> Alerts</div>
                    <div className="ps-label">SYSTEM</div>
                    <div className="ps-item logout" onClick={logout}><span className="ps-icon">🚪</span> Log Out</div>
                </div>

                <div className="pp-main">
                    {/* DASHBOARD */}
                    <section className={`pp-section ${activeSection === 'dashboard' ? 'active' : ''}`}>
                        <h2 className="welcome-title">Welcome back, {partner?.name?.split(' ')[0]} 👋</h2>
                        <div className="stat-row">
                            <div className="stat-card">
                                <div className="stat-val">₹{stats?.monthlyEarnings?.toLocaleString() || '0'}</div>
                                <div className="stat-lbl">Monthly Revenue</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-val">{bookings.length}</div>
                                <div className="stat-lbl">Active Bookings</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-val">{stats?.averageRating || '4.9'} ⭐</div>
                                <div className="stat-lbl">Partner Rating</div>
                            </div>
                            <div className="stat-card">
                                <div className="stat-val alert">{pendingCount}</div>
                                <div className="stat-lbl">Pending Actions</div>
                            </div>
                        </div>
                        <div className="dash-bottom-grid">
                            <div className="pp-card">
                                <h3><span>📅</span> Recent Activity</h3>
                                <table className="bk-table">
                                    <thead><tr><th>Service</th><th>Date</th><th>Status</th><th>Ops</th></tr></thead>
                                    <tbody>
                                        {bookings.slice(0, 5).map(b => (
                                            <tr key={b.id}>
                                                <td className="fw-700">{b.service}</td>
                                                <td className="text-muted fs-13">{b.date}</td>
                                                <td><span className={`status-pill ${b.status}`}>{b.status}</span></td>
                                                <td><button className="btn-sm outline" onClick={() => setViewingBookings([b])}>View</button></td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                            <div className="pp-card">
                                <h3><span>📓</span> Partner Scratchpad</h3>
                                <textarea 
                                    className="dash-scratchpad"
                                    placeholder="Jot down reminders, vendor contacts, or operational notes here..."
                                    defaultValue={typeof window !== 'undefined' ? localStorage.getItem('partner_scratchpad') || '' : ''}
                                    onChange={(e) => {
                                        localStorage.setItem('partner_scratchpad', e.target.value);
                                    }}
                                />
                                <div className="ps-hint">Auto-saves to your browser locally.</div>
                            </div>
                        </div>
                    </section>

                    {/* BOOKINGS */}
                    <section className={`pp-section ${activeSection === 'bookings' ? 'active' : ''}`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                            <h2 style={{ fontSize: 24, fontWeight: 800 }}>📅 Live Operations</h2>
                            <div style={{ display: 'flex', gap: 8 }}>
                                {['all', 'pending', 'confirmed'].map(f => <button key={f} className={`btn-sm ${bookingFilter === f ? '' : 'outline'}`} onClick={() => setBookingFilter(f)}>{f.toUpperCase()}</button>)}
                            </div>
                        </div>
                        <div className="pp-card">
                            <table className="bk-table">
                                <thead><tr><th>Ref</th><th>Customer</th><th>Service</th><th>Date</th><th>Status</th><th>Control</th></tr></thead>
                                <tbody>
                                    {bookings.map(b => (
                                        <tr key={b.id}>
                                            <td style={{ fontWeight: 700 }}>{b.id.slice(0, 8)}</td>
                                            <td>{b.customer}</td>
                                            <td>{b.service}</td>
                                            <td>{b.date}</td>
                                            <td><span className={`status-pill ${b.status}`}>{b.status}</span></td>
                                            <td>
                                                {b.status === 'pending' || b.status === 'planned' ? (
                                                    <div style={{ display: 'flex', gap: 8 }}><button className="btn-sm" onClick={() => handleBookingAction(b.id, 'confirmed')}>Accept</button><button className="btn-sm outline" onClick={() => handleBookingAction(b.id, 'rejected')}>Reject</button></div>
                                                ) : <button className="btn-sm outline" onClick={() => setViewingBookings([b])}>View</button>}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* INVENTORY */}
                    <section className={`pp-section ${activeSection === 'inventory' ? 'active' : ''}`}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 24 }}>
                            <h2 style={{ fontSize: 24, fontWeight: 800 }}>📦 Resource Management</h2>
                            <button className="btn-sm" onClick={() => setShowAddService(true)}>+ Add Resource</button>
                        </div>
                        <div className="pp-card">
                            <table className="bk-table">
                                <thead><tr><th>Name</th><th>Type</th><th>ID/Reg</th><th>Status</th><th>Control</th></tr></thead>
                                <tbody>
                                    {services.map(s => (
                                        <tr key={s.service_id}>
                                            <td style={{ fontWeight: 700 }}>{s.name}</td>
                                            <td style={{ textTransform: 'capitalize' }}>{s.service_type}</td>
                                            <td style={{ fontFamily: 'monospace' }}>{s.reg_number || s.service_id.slice(0, 8)}</td>
                                            <td><span className={`status-pill ${s.active ? 'confirmed' : 'rejected'}`}>{s.active ? 'Active' : 'Offline'}</span></td>
                                            <td><button className="btn-sm outline" onClick={() => handleToggleServiceActive(s.service_id, s.active)}>{s.active ? 'Deactivate' : 'Activate'}</button></td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </section>

                    {/* CALENDAR */}
                    <section className={`pp-section ${activeSection === 'calendar' ? 'active' : ''}`}>
                        <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24 }}>🕒 Availability</h2>
                        <div className="pp-card">
                            <div style={{ display: 'flex', gap: 12, alignItems: 'center', marginBottom: 24 }}>
                                <button className="btn-sm outline" onClick={() => setCalMonth(c => c.month === 0 ? { year: c.year - 1, month: 11 } : { ...c, month: c.month - 1 })}>←</button>
                                <span style={{ fontWeight: 800, fontSize: 18, width: 200, textAlign: 'center' }}>{MONTH_NAMES[calMonth.month]} {calMonth.year}</span>
                                <button className="btn-sm outline" onClick={() => setCalMonth(c => c.month === 11 ? { year: c.year + 1, month: 0 } : { ...c, month: c.month + 1 })}>→</button>
                            </div>
                            <div className="cal-grid">
                                {['M', 'T', 'W', 'T', 'F', 'S', 'S'].map(d => <div key={d} className="cal-header">{d}</div>)}
                                {Array.from({ length: firstDay }).map((_, i) => <div key={`b-${i}`} />)}
                                {Array.from({ length: daysInMonth }).map((_, i) => {
                                    const d = `${calMonth.year}-${String(calMonth.month + 1).padStart(2, '0')}-${String(i + 1).padStart(2, '0')}`;
                                    const s = slots.find(sl => sl.date === d);
                                    return <div key={i} className={`cal-day ${s?.status || 'available'} ${isCurrentMonth && today.getDate() === i + 1 ? 'today' : ''}`} onClick={() => toggleCalDate(d)}>{i + 1}</div>;
                                })}
                            </div>
                        </div>
                    </section>

                    {/* EARNINGS */}
                    <section className={`pp-section ${activeSection === 'earnings' ? 'active' : ''}`}>
                        <h2 style={{ fontSize: 24, fontWeight: 800, marginBottom: 24 }}>💰 Financial Overview</h2>
                        <div className="stat-row">
                            <div className="stat-card"><div className="stat-val">₹{earningsSummary?.this_month?.toLocaleString() || '0'}</div><div className="stat-lbl">Current Month</div></div>
                            <div className="stat-card"><div className="stat-val">₹{earningsSummary?.pending_payout?.toLocaleString() || '0'}</div><div className="stat-lbl">Pending Settlement</div></div>
                        </div>
                        <div className="pp-card" style={{ marginTop: 24 }}>
                            <h3>Monthly Performance</h3>
                            <div className="earnings-bar-wrap">
                                {['J', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'].map((m, i) => (
                                    <div key={i} className="e-bar" style={{ height: `${Math.random() * 80 + 20}%` }}></div>
                                ))}
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            {showAddService && <AddServiceModal onClose={() => setShowAddService(false)} onSave={handleAddService} />}
            {viewingBookings && <BookingDetailModal bookings={viewingBookings} onClose={() => setViewingBookings(null)} />}
        </div>
    );
}
