/**
 * ExternalRedirectOverlay.tsx
 * ────────────────────────────
 * Full-screen overlay that embeds an external ticketing/booking site in an
 * iframe. After the user closes it, a ResumeCard is shown to offer BBT
 * secondary services.
 *
 * Field Guide §4 — Redirect Mechanism (Gmail-style overlay)
 */

import { useState, useCallback, useEffect } from 'react';
import ResumeCard from './ResumeCard';

interface OverlayProps {
  /** External URL to embed */
  url: string;
  /** Event name shown in the top bar */
  title: string;
  /** Location string passed to ResumeCard */
  location?: string;
  /** If true the site refuses to be iframed — open new tab instead */
  blockedIframe?: boolean;
  /** Called when the overlay + resume card are fully dismissed */
  onClose: () => void;
  /** Called when user picks a secondary BBT service from ResumeCard */
  onReturn: (serviceType: 'stays' | 'guide' | 'vehicle' | 'diy') => void;
}

export default function ExternalRedirectOverlay({
  url,
  title,
  location,
  blockedIframe = false,
  onClose,
  onReturn,
}: OverlayProps) {
  const [showResume, setShowResume] = useState(false);

  // If site blocks iframes — open in new tab and immediately show resume card
  useEffect(() => {
    if (blockedIframe) {
      if (typeof window !== 'undefined') {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
    }
  }, [blockedIframe, url]);

  const handleClose = useCallback(() => {
    // Closing the overlay → show the "want to complete your trip?" resume card
    setShowResume(true);
  }, []);

  const handleResumeDismiss = useCallback(() => {
    setShowResume(false);
    onClose();
  }, [onClose]);

  const handleResumeReturn = useCallback(
    (serviceType: 'stays' | 'guide' | 'vehicle' | 'diy') => {
      setShowResume(false);
      onClose();
      onReturn(serviceType);
    },
    [onClose, onReturn],
  );

  if (blockedIframe || showResume) {
    return (
      <ResumeCard
        eventName={title}
        eventLocation={location}
        onDismiss={handleResumeDismiss}
        onReturn={handleResumeReturn}
        externalUrl={url}
      />
    );
  }

  return (
    <div style={styles.backdrop}>
      <div style={styles.modal}>
        {/* ── Top bar ───────────────────────────────────── */}
        <div style={styles.topBar}>
          {/* BBT logo text mark instead of img (works without a real logo file) */}
          <span style={styles.logo}>🫐 BBT</span>
          <span style={styles.title}>{title}</span>
          <button
            style={styles.closeBtn}
            onClick={handleClose}
            aria-label="Close overlay"
            id="overlay-close-btn"
          >
            ×
          </button>
        </div>

        {/* ── Iframe ─────────────────────────────────────── */}
        <iframe
          src={url}
          style={styles.iframe}
          title={title}
          sandbox="allow-scripts allow-forms allow-same-origin allow-popups"
        />

        {/* ── Bottom bar ─────────────────────────────────── */}
        <div style={styles.bottomBar}>
          <span>Booking on external site — your BBT session is saved</span>
          <button
            style={styles.doneBtn}
            onClick={handleClose}
            id="overlay-done-btn"
          >
            Done — return to BBT
          </button>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  backdrop: {
    position: 'fixed',
    inset: 0,
    background: 'rgba(0,0,0,0.80)',
    zIndex: 9999,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backdropFilter: 'blur(2px)',
    animation: 'overlayFadeIn 0.2s ease',
  },
  modal: {
    width: '92vw',
    height: '90vh',
    background: '#fff',
    borderRadius: 14,
    display: 'flex',
    flexDirection: 'column',
    overflow: 'hidden',
    boxShadow: '0 24px 80px rgba(0,0,0,0.50)',
  },
  topBar: {
    display: 'flex',
    alignItems: 'center',
    gap: 12,
    padding: '10px 16px',
    borderBottom: '1px solid #e0e0e0',
    background: '#fff',
    flexShrink: 0,
    minHeight: 50,
  },
  logo: {
    fontWeight: 700,
    fontSize: 15,
    color: '#1B6B3A',
    letterSpacing: '-0.5px',
    flexShrink: 0,
  },
  title: {
    flex: 1,
    fontWeight: 600,
    fontSize: 15,
    color: '#1A1A2E',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  closeBtn: {
    background: 'none',
    border: 'none',
    fontSize: 26,
    lineHeight: 1,
    cursor: 'pointer',
    color: '#555',
    padding: '0 4px',
    flexShrink: 0,
  },
  iframe: {
    flex: 1,
    border: 'none',
    width: '100%',
    background: '#f5f5f5',
  },
  bottomBar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '9px 16px',
    background: '#f8f9fa',
    borderTop: '1px solid #e0e0e0',
    fontSize: 13,
    color: '#6C7A89',
    flexShrink: 0,
    gap: 12,
  },
  doneBtn: {
    background: '#1B6B3A',
    color: '#fff',
    border: 'none',
    borderRadius: 7,
    padding: '7px 18px',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: 13,
    whiteSpace: 'nowrap',
    flexShrink: 0,
  },
};
