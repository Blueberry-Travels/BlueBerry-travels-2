import React, { useState, useEffect, useCallback } from 'react';
import Head from 'next/head';
import { useRouter } from 'next/router';
import ExternalRedirectOverlay from '../components/ExternalRedirectOverlay';
import api from '../lib/api';

/* ── Types ──────────────────────────────────────────────────────── */

interface EventRecord {
  event_id: string;
  name: string;
  short_desc: string;
  location: string;
  start_date: string;
  end_date: string;
  redirect_url: string;
  price_display: string;
  tags: string[];
  image_url?: string;
  blocked_iframe?: boolean;
  region_id?: number | null;
  emoji?: string;
}

interface OverlayState {
  url: string;
  title: string;
  eventId: string;
  location: string;
  blockedIframe: boolean;
}

const STATIC_EVENTS: EventRecord[] = [
  {
    event_id: 'static-1',
    name: 'Rann Utsav 2026',
    short_desc: 'The great white salt desert festival. Music, craft, camel rides under the full moon.',
    location: 'Kutch, Gujarat',
    start_date: '2026-03-15',
    end_date: '2026-03-28',
    redirect_url: 'https://www.rannutsav.com',
    price_display: '₹3,500 / night',
    tags: ['Festival', 'Culture', 'Desert'],
    emoji: '🎉',
    blocked_iframe: false,
  },
  {
    event_id: 'static-2',
    name: 'Hornbill Festival',
    short_desc: 'Largest tribal cultural showcase in India. Dance, music, food of 16 tribes.',
    location: 'Kohima, Nagaland',
    start_date: '2026-12-01',
    end_date: '2026-12-10',
    redirect_url: 'https://nagalandtourism.com/hornbill-festival',
    price_display: '₹800 entry',
    tags: ['Tribal', 'Culture', 'Northeast'],
    emoji: '🎉',
    blocked_iframe: false,
  },
  {
    event_id: 'static-4',
    name: 'Ziro Music Festival',
    short_desc: 'Indie music in one of India\'s most scenic valleys. Camping, community, culture.',
    location: 'Ziro Valley, Arunachal',
    start_date: '2026-09-24',
    end_date: '2026-09-27',
    redirect_url: 'https://ziromusicfestival.com',
    price_display: '₹2,200',
    tags: ['Music', 'Adventure', 'Northeast'],
    emoji: '🎸',
    blocked_iframe: false,
  }
];

export default function Events() {
  const router = useRouter();
  const [events, setEvents] = useState<EventRecord[]>(STATIC_EVENTS);
  const [overlay, setOverlay] = useState<OverlayState | null>(null);
  const [activeTag, setActiveTag] = useState<string>('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEvents = async () => {
        try {
            const res = await api.get('/api/v1/events/');
            if (res.data?.results?.length) {
                setEvents(res.data.results);
            }
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    };
    fetchEvents();
  }, []);

  const allTags = Array.from(new Set(events.flatMap(e => e.tags)));
  const visibleEvents = activeTag
    ? events.filter(e => e.tags.includes(activeTag))
    : events;

  const handleBookTicket = useCallback((ev: EventRecord) => {
    setOverlay({
      url: ev.redirect_url,
      title: ev.name,
      eventId: ev.event_id,
      location: ev.location,
      blockedIframe: ev.blocked_iframe ?? false,
    });
  }, []);

  const handleReturn = useCallback(
    (serviceType: 'stays' | 'guide' | 'vehicle' | 'diy') => {
      const loc = overlay?.location || '';
      setOverlay(null);
      if (serviceType === 'stays')   router.push(`/diy?focus=stays&region=${encodeURIComponent(loc)}`);
      if (serviceType === 'guide')   router.push(`/misc?type=guide&region=${encodeURIComponent(loc)}`);
      if (serviceType === 'vehicle') router.push(`/misc?type=vehicle&region=${encodeURIComponent(loc)}`);
      if (serviceType === 'diy')     router.push(`/diy?region=${encodeURIComponent(loc)}`);
    },
    [overlay, router],
  );

  const fmtDate = (d: string) => {
    try {
      return new Date(d).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' });
    } catch { return d; }
  };

  return (
    <>
      <Head>
        <title>Events & Festivals — Blueberry Travels</title>
      </Head>

      {overlay && (
        <ExternalRedirectOverlay
          url={overlay.url}
          title={overlay.title}
          location={overlay.location}
          blockedIframe={overlay.blockedIframe}
          onClose={() => setOverlay(null)}
          onReturn={handleReturn}
        />
      )}

      <div className="hero-image" style={{ backgroundImage: `url('/hero_events.png')`, height: '40vh', minHeight: '350px' }}>
          <div className="hero-overlay"></div>
          <div className="hero-content">
              <span className="hero-badge">Local Vibes</span>
              <h1 className="hero-title">Events & Festivals</h1>
              <p className="hero-subtitle">Be there when the culture comes alive. Festivals, concerts, and tribal fairs.</p>
          </div>
      </div>

      <div className="events-container">
          <div className="filter-bar glass">
              <button className={`filter-chip ${!activeTag ? 'active' : ''}`} onClick={() => setActiveTag('')}>All Experiences</button>
              {allTags.map(tag => (
                  <button key={tag} className={`filter-chip ${activeTag === tag ? 'active' : ''}`} onClick={() => setActiveTag(tag)}>
                      {tag}
                  </button>
              ))}
          </div>

          <div className="events-grid">
              {visibleEvents.map(ev => (
                  <div key={ev.event_id} className="event-card glass">
                      <div className="ev-thumb" style={{ background: `linear-gradient(135deg, var(--primary-dark), rgba(10,10,12,0.8))` }}>
                          <span className="ev-emoji">{ev.emoji || '🎉'}</span>
                      </div>
                      <div className="ev-body">
                          <div className="ev-meta">
                              <span className="ev-loc">📍 {ev.location}</span>
                              <span className="ev-date">📅 {fmtDate(ev.start_date)} — {fmtDate(ev.end_date)}</span>
                          </div>
                          <h2 className="ev-title">{ev.name}</h2>
                          <p className="ev-desc">{ev.short_desc}</p>
                          <div className="ev-footer">
                              <span className="ev-price">{ev.price_display}</span>
                              <button className="btn-primary" onClick={() => handleBookTicket(ev)}>Book Tickets</button>
                          </div>
                      </div>
                  </div>
              ))}
          </div>
      </div>

      <style jsx>{`
        .events-container {
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
            transition: 0.2s;
        }
        .filter-chip:hover { background: rgba(255,255,255,0.1); color: white; }
        .filter-chip.active { background: var(--primary); color: white; box-shadow: 0 4px 15px rgba(76,124,53,0.3); }
        
        .events-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 32px;
        }
        
        .event-card {
            border-radius: 32px; overflow: hidden;
            transition: var(--transition-smooth);
        }
        .event-card:hover { transform: translateY(-8px); border-color: var(--primary-light); }
        
        .ev-thumb { height: 180px; display: flex; align-items: center; justify-content: center; position: relative; }
        .ev-emoji { font-size: 56px; filter: drop-shadow(0 0 20px rgba(76,124,53,0.3)); }
        
        .ev-body { padding: 32px; }
        .ev-meta { display: flex; justify-content: space-between; font-size: 11px; font-weight: 800; text-transform: uppercase; color: var(--primary-light); margin-bottom: 16px; letter-spacing: 0.05em; }
        
        .ev-title { font-size: 24px; color: white; margin-bottom: 12px; letter-spacing: -0.02em; }
        .ev-desc { font-size: 14px; color: var(--text-secondary); line-height: 1.6; margin-bottom: 24px; }
        
        .ev-footer { display: flex; justify-content: space-between; align-items: center; padding-top: 24px; border-top: 1px solid var(--glass-border); }
        .ev-price { font-size: 15px; font-weight: 900; color: white; }
      `}</style>
    </>
  );
}
