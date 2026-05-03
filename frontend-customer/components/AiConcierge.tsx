import React, { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/router';

export default function AiConcierge() {
  const [isOpen, setIsOpen] = useState(false);
  const [showWheel, setShowWheel] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'ai', text: "Namaste! I am your BlueBerry Concierge. How can I help you design your Himalayan escape today?" }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;
    const userText = input.trim();
    setMessages(prev => [...prev, { role: 'user', text: userText }]);
    setInput('');
    setIsTyping(true);

    // Enhanced "Live" Simulation Logic
    setTimeout(() => {
      let response = "I'm sorry, I'm still learning about that. Would you like to explore our Curated Packages or start building a custom DIY Itinerary?";
      const low = userText.toLowerCase();

      if (low.includes('hi') || low.includes('hello') || low.includes('hey')) {
        response = "Namaste! I am your BlueBerry Concierge. I can help you find the perfect trek, build a custom itinerary, or manage your bookings. What's on your mind?";
      } else if (low.includes('diy') || low.includes('build') || low.includes('itinerary')) {
        response = "Our DIY Builder is a state-of-the-art tool! You select a region (like Harsil or Spiti), pick your 'Passion' (Trek, Yoga, or Leisure), and I'll generate a day-by-day plan with transport and stays. Want me to open it for you?";
      } else if (low.includes('package') || low.includes('trek') || low.includes('retreat')) {
        response = "We have signature journeys for every pace. From the high-altitude 'Harsil Discovery' to 'Soulful Yoga Retreats'. You can browse them all in our Packages section. Any specific region you love?";
      } else if (low.includes('contact') || low.includes('support') || low.includes('help') || low.includes('phone') || low.includes('email')) {
        response = "You can reach our human experts at concierge@blueberrytravels.co. For urgent trip assistance, your Dashboard has a 'Live Support' link once you have an active booking.";
      } else if (low.includes('dashboard') || low.includes('account') || low.includes('my trip') || low.includes('status')) {
        response = "Your Dashboard is your personal travel command center. You can track KYC status, sign NOC documents, and check your trip itinerary 24/7. Shall I take you there?";
      } else if (low.includes('pay') || low.includes('price') || low.includes('cost') || low.includes('razorpay')) {
        response = "We use secure Razorpay integration. You'll see a 'Trip Bill' in your Dashboard once you confirm an itinerary. You can choose different assistance tiers (Essential vs Premium) to fit your budget.";
      } else if (low.includes('weather') || low.includes('best time')) {
        response = "Great question! Most Himalayan regions are best from May-June and Sept-Oct. However, Spiti is a summer paradise while Harsil is stunning during the apple harvest in September.";
      } else if (low.includes('who are you') || low.includes('about')) {
        response = "I am the BlueBerry AI Concierge, built to make Himalayan travel as smooth as the mountain air. I know every corner of our platform—from the DIY engine to the partner portal.";
      }

      setMessages(prev => [...prev, { role: 'ai', text: response }]);
      setIsTyping(false);
    }, 1500);
  };

  const navWheel = [
    { label: 'Build DIY', path: '/diy', icon: '🛠️' },
    { label: 'Explore', path: '/packages', icon: '🏔️' },
    { label: 'Events', path: '/events', icon: '🎪' },
    { label: 'Dashboard', path: '/dashboard', icon: '📊' },
  ];

  return (
    <>
      {/* ── Chatbot Toggle ── */}
      <div className="concierge-trigger" onClick={() => setIsOpen(!isOpen)}>
        <div className="trigger-inner">
          {isOpen ? <span style={{fontSize: 24}}>✕</span> : <span style={{fontSize: 32}}>🫐</span>}
        </div>
      </div>

      {/* ── Quick Nav Wheel ── */}
      <div className="nav-wheel-trigger" onClick={() => setShowWheel(!showWheel)}>
        <span>🧭</span>
      </div>

      {showWheel && (
        <div className="nav-wheel-overlay" onClick={() => setShowWheel(false)}>
           <div className="wheel-container" onClick={e => e.stopPropagation()}>
              {navWheel.map((item, i) => (
                <div 
                  key={i} 
                  className="wheel-item" 
                  style={{ transform: `rotate(${i * 90}deg) translateY(-80px) rotate(-${i * 90}deg)` }}
                  onClick={() => { router.push(item.path); setShowWheel(false); }}
                >
                  <div className="wheel-icon">{item.icon}</div>
                  <div className="wheel-label">{item.label}</div>
                </div>
              ))}
              <div className="wheel-center">BlueBerry</div>
           </div>
        </div>
      )}

      {/* ── Chat Window ── */}
      {isOpen && (
        <div className="concierge-window glass">
          <div className="concierge-header">
            <div className="header-info">
              <div className="ai-avatar">🫐</div>
              <div>
                <h4>BlueBerry Concierge</h4>
                <div className="online-status">Online</div>
              </div>
            </div>
          </div>

          <div className="concierge-body" ref={scrollRef}>
            {messages.map((m, i) => (
              <div key={i} className={`msg-row ${m.role}`}>
                <div className="msg-bubble">{m.text}</div>
              </div>
            ))}
            {isTyping && (
              <div className="msg-row ai">
                <div className="msg-bubble typing">...</div>
              </div>
            )}
          </div>

          <div className="concierge-input">
            <input 
              type="text" 
              placeholder="Ask anything..." 
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyPress={e => e.key === 'Enter' && handleSend()}
            />
            <button onClick={handleSend}>➔</button>
          </div>
        </div>
      )}

      <style jsx>{`
        .concierge-trigger {
          position: fixed;
          bottom: 32px;
          right: 32px;
          width: 64px;
          height: 64px;
          background: var(--primary);
          border-radius: 50%;
          cursor: pointer;
          z-index: 9999;
          box-shadow: 0 12px 30px rgba(76, 124, 53, 0.4);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .concierge-trigger:hover {
          transform: scale(1.1) rotate(5deg);
        }
        .trigger-inner { color: white; display: flex; align-items: center; justify-content: center; }

        .nav-wheel-trigger {
          position: fixed;
          bottom: 32px;
          right: 110px;
          width: 50px;
          height: 50px;
          background: rgba(255,255,255,0.05);
          backdrop-filter: blur(10px);
          border: 1px solid var(--glass-border);
          border-radius: 50%;
          cursor: pointer;
          z-index: 9998;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
          transition: all 0.3s ease;
        }
        .nav-wheel-trigger:hover { background: rgba(255,255,255,0.1); }

        .nav-wheel-overlay {
          position: fixed;
          inset: 0;
          background: rgba(0,0,0,0.4);
          backdrop-filter: blur(8px);
          z-index: 10000;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .wheel-container {
          position: relative;
          width: 300px;
          height: 300px;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .wheel-center {
          width: 100px;
          height: 100px;
          background: var(--primary);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-weight: 900;
          font-size: 14px;
          box-shadow: 0 0 40px rgba(76, 124, 53, 0.5);
        }
        .wheel-item {
          position: absolute;
          width: 70px;
          height: 70px;
          background: rgba(255,255,255,0.05);
          border: 1px solid rgba(255,255,255,0.1);
          backdrop-filter: blur(20px);
          border-radius: 20px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .wheel-item:hover {
          background: var(--primary);
          border-color: var(--primary-light);
          transform: scale(1.1) !important;
        }
        .wheel-icon { font-size: 24px; margin-bottom: 4px; }
        .wheel-label { font-size: 9px; font-weight: 800; text-transform: uppercase; color: white; opacity: 0.8; }

        .concierge-window {
          position: fixed;
          bottom: 112px;
          right: 32px;
          width: 380px;
          height: 600px;
          max-height: 80vh;
          border-radius: 32px;
          z-index: 10000;
          display: flex;
          flex-direction: column;
          overflow: hidden;
          box-shadow: 0 40px 100px rgba(0,0,0,0.5);
          border: 1px solid var(--glass-border);
          animation: slideUp 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }
        @keyframes slideUp {
          from { transform: translateY(40px); opacity: 0; }
          to { transform: translateY(0); opacity: 1; }
        }

        .concierge-header {
          padding: 24px;
          background: rgba(255,255,255,0.03);
          border-bottom: 1px solid var(--glass-border);
        }
        .header-info { display: flex; align-items: center; gap: 16px; }
        .ai-avatar {
          width: 48px;
          height: 48px;
          background: var(--primary);
          border-radius: 16px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 24px;
        }
        .concierge-header h4 { color: white; margin-bottom: 4px; font-weight: 800; }
        .online-status {
          font-size: 11px;
          color: #4ade80;
          font-weight: 700;
          display: flex;
          align-items: center;
          gap: 6px;
        }
        .online-status::before {
          content: '';
          width: 6px;
          height: 6px;
          background: currentColor;
          border-radius: 50%;
        }

        .concierge-body {
          flex: 1;
          padding: 24px;
          overflow-y: auto;
          display: flex;
          flex-direction: column;
          gap: 16px;
        }
        .msg-row { display: flex; width: 100%; }
        .msg-row.user { justify-content: flex-end; }
        .msg-bubble {
          max-width: 80%;
          padding: 14px 20px;
          border-radius: 20px;
          font-size: 14px;
          line-height: 1.6;
        }
        .ai .msg-bubble { background: rgba(255,255,255,0.05); color: white; border-bottom-left-radius: 4px; }
        .user .msg-bubble { background: var(--primary); color: white; border-bottom-right-radius: 4px; }
        .typing { font-style: italic; opacity: 0.6; }

        .concierge-input {
          padding: 24px;
          display: flex;
          gap: 12px;
          background: rgba(255,255,255,0.02);
        }
        .concierge-input input {
          flex: 1;
          background: rgba(255,255,255,0.05);
          border: 1px solid var(--glass-border);
          border-radius: 100px;
          padding: 12px 24px;
          color: white;
          font-size: 14px;
        }
        .concierge-input button {
          width: 44px;
          height: 44px;
          background: var(--primary);
          color: white;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-weight: 900;
        }
      `}</style>
    </>
  );
}
