import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import api from '../lib/api';

/* ─────────────────────────────────────────────
   TYPES
   ───────────────────────────────────────────── */
interface ServiceBooking {
  booking_id: string;
  service_type: string;
  status: string;
  date: string;
  location: string;
  notes: string;
  partner_name: string | null;
  frame_id: string | null;
  price: string | null;
}

interface BookingForm {
  service_type: string;
  date: string;
  location: string;
  notes: string;
  frame_id: string;
}

/* ─────────────────────────────────────────────
   COMPONENTS
   ───────────────────────────────────────────── */

function BookingModal({
  serviceType,
  serviceLabel,
  icon,
  partnerId,
  partnerName,
  onClose,
  onSuccess,
}: {
  serviceType: string;
  serviceLabel: string;
  icon: string;
  partnerId?: string;
  partnerName?: string;
  onClose: () => void;
  onSuccess: (booking: ServiceBooking) => void;
}) {
  const [form, setForm] = useState<BookingForm>({
    service_type: serviceType,
    date: '',
    location: '',
    notes: '',
    frame_id: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const payload: Record<string, string> = {
        service_type: form.service_type,
        date: form.date,
        location: form.location,
        notes: form.notes,
      };
      if (form.frame_id) payload.frame_id = form.frame_id;
      if (partnerId) payload.partner_id = partnerId;
      const res = await api.post('/api/v1/service-bookings/', payload);
      onSuccess(res.data);
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to request booking.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-backdrop" onClick={onClose}>
        <div className="modal-card glass-dark" onClick={e => e.stopPropagation()}>
            <div className="modal-head">
                <span className="modal-icon">{icon}</span>
                <div className="modal-titles">
                    <h2>Book {partnerName || serviceLabel}</h2>
                    <p>Request service from local experts</p>
                </div>
                <button className="close-btn" onClick={onClose}>✕</button>
            </div>
            <form onSubmit={handleSubmit} className="modal-form">
                <div className="form-group">
                    <label>Preferred Date *</label>
                    <input 
                        type="date" required 
                        className="glass-input"
                        value={form.date}
                        onChange={e => setForm({...form, date: e.target.value})}
                    />
                </div>
                <div className="form-group">
                    <label>Pickup / Location *</label>
                    <input 
                        type="text" required 
                        placeholder="e.g. Manali Market, Base Camp"
                        className="glass-input"
                        value={form.location}
                        onChange={e => setForm({...form, location: e.target.value})}
                    />
                </div>
                <div className="form-group">
                    <label>Specific Notes</label>
                    <textarea 
                        placeholder="Any special requirements..."
                        className="glass-input"
                        style={{ height: 80 }}
                        value={form.notes}
                        onChange={e => setForm({...form, notes: e.target.value})}
                    ></textarea>
                </div>
                {error && <div className="form-error">{error}</div>}
                <div className="modal-actions">
                    <button type="button" className="btn-secondary" onClick={onClose}>Cancel</button>
                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? 'Processing...' : 'Confirm Request'}
                    </button>
                </div>
            </form>
        </div>
        <style jsx>{`
            .modal-backdrop {
                position: fixed; inset: 0; background: rgba(0,0,0,0.6);
                backdrop-filter: blur(8px); z-index: 1000;
                display: flex; align-items: center; justify-content: center;
                padding: 24px;
            }
            .modal-card {
                width: 100%; max-width: 500px; border-radius: 32px;
                overflow: hidden; animation: slide-up 0.4s ease;
            }
            @keyframes slide-up { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
            .modal-head {
                padding: 32px; display: flex; align-items: center; gap: 20px;
                border-bottom: 1px solid var(--glass-border);
            }
            .modal-icon { font-size: 32px; }
            .modal-titles h2 { font-size: 20px; color: white; margin-bottom: 4px; }
            .modal-titles p { font-size: 13px; color: var(--text-muted); }
            .close-btn { background: transparent; color: var(--text-muted); font-size: 20px; margin-left: auto; }
            .modal-form { padding: 32px; display: flex; flex-direction: column; gap: 24px; }
            .form-group { display: flex; flex-direction: column; gap: 8px; }
            .form-group label { font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--text-muted); letter-spacing: 0.1em; }
            .glass-input {
                background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border);
                border-radius: 14px; padding: 12px 16px; color: white; outline: none; transition: 0.2s;
            }
            .glass-input:focus { border-color: var(--primary-light); background: rgba(255,255,255,0.06); }
            .form-error { color: #fca5a5; font-size: 13px; font-weight: 600; }
            .modal-actions { display: flex; gap: 12px; margin-top: 8px; }
            .modal-actions button { flex: 1; }
        `}</style>
    </div>
  );
}

/* ─────────────────────────────────────────────
   PAGE COMPONENT
   ───────────────────────────────────────────── */

export default function Misc() {
  const router = useRouter();
  const { type } = router.query;

  const [modal, setModal] = useState<any>(null);
  const [confirmed, setConfirmed] = useState<ServiceBooking | null>(null);
  const [myBookings, setMyBookings] = useState<ServiceBooking[]>([]);
  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState<any[]>([]);

  useEffect(() => {
    const fetchServices = async () => {
        try {
            const res = await api.get('/api/v1/misc-services/');
            const partners = res.data.partners || [];
            
            const grouped = [
                {
                    id: 'guide', icon: '🧭', label: 'Local Guides',
                    items: partners.filter((p: any) => p.partner_type === 'guide')
                },
                {
                    id: 'vehicle', icon: '🚗', label: 'Vehicle Rentals',
                    items: partners.filter((p: any) => p.partner_type === 'vehicle')
                }
            ];
            setServices(grouped);
        } catch (err) {
            console.error(err);
        } finally {
            setLoading(false);
        }
    };
    fetchServices();
  }, []);

  useEffect(() => {
    const fetchMyBookings = async () => {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        try {
            const res = await api.get('/api/v1/service-bookings/list/');
            setMyBookings(res.data.bookings || []);
        } catch (err) { console.error(err); }
    };
    fetchMyBookings();
  }, [confirmed]);

  const handleBookingSuccess = (booking: ServiceBooking) => {
    setModal(null);
    setConfirmed(booking);
  };

  return (
    <>
      <Head>
        <title>Local Services — Blueberry Travels</title>
      </Head>

      <div className="hero-image" style={{ backgroundImage: `url('/hero_misc.png')`, height: '40vh', minHeight: '350px' }}>
          <div className="hero-overlay"></div>
          <div className="hero-content">
              <span className="hero-badge">Expert Support</span>
              <h1 className="hero-title" style={{ fontSize: ' clamp(40px, 7vw, 60px)' }}>Local Services</h1>
              <p className="hero-subtitle">Verified guides, vehicles, and mountain logistics at your fingertips.</p>
          </div>
      </div>

      <div className="misc-container">
          
          {loading ? (
              <div className="loading-grid">
                  {[1,2].map(i => <div key={i} className="skeleton-card glass"></div>)}
              </div>
          ) : (
              <div className="services-layout">
                  {services.map(svc => (
                      <section key={svc.id} className="svc-section">
                          <div className="svc-header">
                              <h2>{svc.icon} {svc.label}</h2>
                              <button className="btn-ghost" onClick={() => setModal({ serviceType: svc.id, label: svc.label, icon: svc.icon })}>
                                  General Request +
                              </button>
                          </div>
                          <div className="partner-grid">
                              {svc.items.map((item: any) => (
                                  <div key={item.partner_id} className="partner-card glass">
                                      <div className="p-header">
                                          <div className="p-avatar">{item.business_name.charAt(0)}</div>
                                          <div className="p-titles">
                                              <h3>{item.business_name}</h3>
                                              <p>⭐ {item.rating || '4.8'} · {item.trips || '120'}+ trips</p>
                                          </div>
                                      </div>
                                      <div className="p-body">
                                          <p className="p-desc">{item.desc || `Verified ${svc.label.toLowerCase()} partner for Himalayan regions.`}</p>
                                          <div className="p-meta">
                                              <span>📍 {(item.region_ids || []).join(', ') || 'Various'}</span>
                                          </div>
                                      </div>
                                      <button className="btn-primary" style={{ width: '100%' }} onClick={() => setModal({
                                          serviceType: svc.id,
                                          label: svc.label,
                                          icon: svc.icon,
                                          partnerId: item.partner_id,
                                          partnerName: item.business_name
                                      })}>
                                          Request Booking
                                      </button>
                                  </div>
                              ))}
                          </div>
                      </section>
                  ))}
              </div>
          )}

          {myBookings.length > 0 && (
              <section className="my-bookings-section glass">
                  <h2 className="section-header">📋 Your Service History</h2>
                  <div className="bookings-list">
                      {myBookings.map(b => (
                          <div key={b.booking_id} className="booking-row">
                              <div className="b-info">
                                  <h3>{b.service_type.toUpperCase()} · {b.location}</h3>
                                  <p>{b.date} · {b.partner_name || 'Assigning Partner...'}</p>
                              </div>
                              <div className={`b-status status-${b.status}`}>
                                  {b.status.replace('_', ' ')}
                              </div>
                          </div>
                      ))}
                  </div>
              </section>
          )}

      </div>

      {modal && (
          <BookingModal 
              {...modal} 
              onClose={() => setModal(null)} 
              onSuccess={handleBookingSuccess} 
          />
      )}

      {confirmed && (
          <div className="modal-backdrop" onClick={() => setConfirmed(null)}>
              <div className="confirm-card glass-dark" onClick={e => e.stopPropagation()}>
                  <div className="confirm-icon">✅</div>
                  <h2>Request Sent!</h2>
                  <p>Your booking request has been dispatched to the local partner. They will respond shortly.</p>
                  <div className="confirm-details">
                      <div className="c-row"><span>Service</span> <span>{confirmed.service_type}</span></div>
                      <div className="c-row"><span>Date</span> <span>{confirmed.date}</span></div>
                      <div className="c-row"><span>Ref</span> <span style={{fontFamily:'monospace'}}>{confirmed.booking_id.slice(0,8)}</span></div>
                  </div>
                  <button className="btn-primary" style={{ width: '100%' }} onClick={() => setConfirmed(null)}>Got it</button>
              </div>
          </div>
      )}

      <style jsx>{`
        .misc-container {
            max-width: var(--main-width);
            margin: -60px auto 100px;
            padding: 0 var(--outer-gap);
            position: relative;
            z-index: 10;
        }
        
        .svc-section { margin-bottom: 64px; }
        .svc-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 32px; }
        .svc-header h2 { font-size: 24px; color: white; }
        
        .partner-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 24px;
        }
        
        .partner-card {
            padding: 32px; border-radius: 32px;
            transition: var(--transition-smooth);
        }
        .partner-card:hover { transform: translateY(-8px); border-color: var(--primary-light); }
        
        .p-header { display: flex; gap: 16px; align-items: center; margin-bottom: 24px; }
        .p-avatar {
            width: 50px; height: 50px; border-radius: 16px;
            background: var(--primary); display: flex; align-items: center;
            justify-content: center; font-size: 20px; font-weight: 900; color: white;
        }
        .p-titles h3 { font-size: 18px; color: white; margin-bottom: 2px; }
        .p-titles p { font-size: 12px; color: var(--primary-light); font-weight: 700; }
        
        .p-body { margin-bottom: 24px; }
        .p-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 16px; }
        .p-meta { font-size: 12px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; }
        
        .my-bookings-section { padding: 48px; border-radius: 40px; margin-top: 80px; }
        .bookings-list { display: flex; flex-direction: column; gap: 16px; margin-top: 32px; }
        .booking-row {
            display: flex; justify-content: space-between; align-items: center;
            padding: 24px; background: rgba(255,255,255,0.03); border-radius: 20px;
            border: 1px solid var(--glass-border);
        }
        .b-info h3 { font-size: 16px; color: white; margin-bottom: 4px; }
        .b-info p { font-size: 13px; color: var(--text-muted); }
        .b-status { font-size: 11px; font-weight: 800; text-transform: uppercase; padding: 6px 14px; border-radius: 100px; }
        .status-pending_approval { background: rgba(212, 163, 115, 0.1); color: var(--accent); }
        .status-confirmed { background: rgba(76, 124, 53, 0.1); color: var(--primary-light); }
        
        .confirm-card {
            width: 100%; max-width: 400px; border-radius: 32px;
            padding: 48px; text-align: center;
        }
        .confirm-icon { font-size: 64px; margin-bottom: 24px; }
        .confirm-card h2 { font-size: 28px; color: white; margin-bottom: 12px; }
        .confirm-card p { font-size: 15px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 32px; }
        .confirm-details { background: rgba(255,255,255,0.03); border-radius: 20px; padding: 20px; margin-bottom: 32px; }
        .c-row { display: flex; justify-content: space-between; font-size: 13px; padding: 8px 0; border-bottom: 1px solid var(--glass-border); }
        .c-row:last-child { border-bottom: none; }
        .c-row span:first-child { color: var(--text-muted); font-weight: 700; text-transform: uppercase; font-size: 11px; }
        .c-row span:last-child { color: white; font-weight: 700; }
        
        .loading-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
        .skeleton-card { height: 300px; border-radius: 32px; }
      `}</style>
    </>
  );
}
