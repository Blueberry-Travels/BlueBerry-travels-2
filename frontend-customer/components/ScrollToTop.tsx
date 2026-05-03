import React, { useState, useEffect } from 'react';

export default function ScrollToTop() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const toggleVisible = () => {
      if (window.pageYOffset > 300) {
        setVisible(true);
      } else {
        setVisible(false);
      }
    };
    window.addEventListener('scroll', toggleVisible);
    return () => window.removeEventListener('scroll', toggleVisible);
  }, []);

  const scrollToTop = () => {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  };

  return (
    <div 
      className={`scroll-to-top ${visible ? 'visible' : ''}`} 
      onClick={scrollToTop}
    >
      <span>↑</span>
      <style jsx>{`
        .scroll-to-top {
          position: fixed;
          bottom: 32px;
          right: 175px;
          width: 50px;
          height: 50px;
          background: rgba(255,255,255,0.05);
          backdrop-filter: blur(10px);
          border: 1px solid var(--glass-border);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          font-size: 20px;
          font-weight: 900;
          cursor: pointer;
          z-index: 9997;
          opacity: 0;
          transform: translateY(20px);
          transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .scroll-to-top.visible {
          opacity: 1;
          transform: translateY(0);
        }
        .scroll-to-top:hover {
          background: var(--primary);
          border-color: var(--primary-light);
          transform: scale(1.1);
        }
      `}</style>
    </div>
  );
}
