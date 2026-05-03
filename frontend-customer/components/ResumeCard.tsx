import React from 'react';

/**
 * ResumeCard.tsx
 * ──────────────
 * Shown after the user closes the ExternalRedirectOverlay.
 * Offers 4 secondary BBT service options so the user can convert the event
 * visit into a fuller trip.
 *
 * Field Guide §4.2 — Component: ResumeCard
 */

interface ResumeCardProps {
  onDismiss: () => void;
  onReturn: (serviceType: 'stays' | 'guide' | 'vehicle' | 'diy') => void;
  eventName?: string;
  eventLocation?: string;
  externalUrl?: string;
}

interface OptionBtnProps {
  icon: string;
  label: string;
  id: string;
  onClick: () => void;
}

function OptionBtn({ icon, label, id, onClick }: OptionBtnProps) {
  return (
    <button id={id} onClick={onClick} style={optStyles.optBtn}>
      <span style={optStyles.optIcon}>{icon}</span>
      <span style={optStyles.optLabel}>{label}</span>
    </button>
  );
}

export default function ResumeCard({
  onDismiss,
  onReturn,
  eventName,
  eventLocation,
  externalUrl,
}: ResumeCardProps) {
  const where = eventLocation || 'the event venue';
  const what = eventName ? `You attended ${eventName}` : 'You just attended an event';

  return (
    <div style={cardStyles.backdrop}>
      <div style={cardStyles.card}>
        {/* Decorative top stripe */}
        <div style={cardStyles.stripe} />

        <div style={cardStyles.body}>
          <div style={cardStyles.emoji}>🌿</div>
          <h3 style={cardStyles.heading}>Great! Make it a full trip</h3>
          <p style={cardStyles.sub}>
            {what} in {where}. Want us to sort the rest?
          </p>

          {externalUrl && (
            <div style={{ marginBottom: 20 }}>
              <a
                href={externalUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  fontSize: 13,
                  color: '#1B6B3A',
                  fontWeight: 600,
                  textDecoration: 'underline',
                }}
                id="resume-external-link"
              >
                Couldn&apos;t see the site? Open manually ↗
              </a>
            </div>
          )}

          <div style={cardStyles.options}>
            <OptionBtn
              id="resume-stays-btn"
              icon="🏨"
              label="Find a stay nearby"
              onClick={() => onReturn('stays')}
            />
            <OptionBtn
              id="resume-guide-btn"
              icon="🧭"
              label="Book a local guide"
              onClick={() => onReturn('guide')}
            />
            <OptionBtn
              id="resume-vehicle-btn"
              icon="🚗"
              label="Get a vehicle"
              onClick={() => onReturn('vehicle')}
            />
            <OptionBtn
              id="resume-diy-btn"
              icon="🗓️"
              label="Build full itinerary"
              onClick={() => onReturn('diy')}
            />
          </div>

          <button id="resume-dismiss-btn" onClick={onDismiss} style={cardStyles.skip}>
            No thanks, I&apos;m done
          </button>
        </div>
      </div>
    </div>
  );
}

const cardStyles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.65)',
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(4px)',
  },
  card: {
    width: 'min(440px, 92vw)',
    background: '#fff',
    borderRadius: 16,
    boxShadow: '0 24px 80px rgba(0,0,0,0.35)',
    overflow: 'hidden',
    animation: 'slideUpCard 0.25s cubic-bezier(0.34,1.3,0.64,1)',
  },
  stripe: {
    height: 5,
    background: 'linear-gradient(90deg, #1B6B3A 0%, #4CAF50 60%, #8BC34A 100%)',
  },
  body: {
    padding: '28px 28px 24px',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    textAlign: 'center',
  },
  emoji: {
    fontSize: 40,
    marginBottom: 8,
    lineHeight: 1,
  },
  heading: {
    color: '#1B6B3A',
    margin: '0 0 8px',
    fontSize: 20,
    fontWeight: 700,
  },
  sub: {
    color: '#555',
    fontSize: 14,
    lineHeight: 1.55,
    margin: '0 0 20px',
    maxWidth: 340,
  },
  options: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: 10,
    width: '100%',
    marginBottom: 18,
  },
  skip: {
    background: 'none',
    border: 'none',
    color: '#999',
    fontSize: 13,
    cursor: 'pointer',
    textDecoration: 'underline',
    padding: 0,
  },
};

const optStyles: Record<string, React.CSSProperties> = {
  optBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: 10,
    padding: '12px 14px',
    border: '1.5px solid #e0e0e0',
    borderRadius: 10,
    background: '#fafafa',
    cursor: 'pointer',
    fontSize: 13,
    fontWeight: 600,
    color: '#1A1A2E',
    transition: 'all 0.15s ease',
    textAlign: 'left',
  },
  optIcon: {
    fontSize: 20,
    flexShrink: 0,
  },
  optLabel: {
    flex: 1,
    lineHeight: 1.3,
  },
};
