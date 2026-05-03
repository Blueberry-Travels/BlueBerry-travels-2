import React, { useState } from 'react';
import REGION_PATHS from '../data/india_paths.json';

/*
 * IndiaMap – Geographically accurate SVG map of India.
 * State boundary paths sourced from @svg-maps/india (CC BY 4.0).
 * Complete paths loaded from india_paths.json.
 * States are grouped into 5 clickable <g> regions.
 *
 * Props:
 *   selectedRegion – currently active region id (or null)
 *   onRegionClick  – callback when a region group is clicked
 */

interface IndiaMapProps {
  selectedRegion: string | null;
  onRegionClick: (regionId: string) => void;
}

/* ── Region colour palette with gradient pairs ── */
const REGION_COLORS: Record<string, { base: string; hover: string; active: string; gradient: [string, string] }> = {
  uttar:    { base: '#7d9b6e', hover: '#8faf7e', active: '#6b8a5c', gradient: ['#8faf7e', '#6b8a5c'] },
  dakshin:  { base: '#3e5c2e', hover: '#4e6e3e', active: '#2d4c1e', gradient: ['#4e6e3e', '#2d4c1e'] },
  poorabh:  { base: '#c9a076', hover: '#dab38b', active: '#b78d61', gradient: ['#dab38b', '#b78d61'] },
  pashchim: { base: '#5c7d50', hover: '#6c8d60', active: '#4b6a3f', gradient: ['#6c8d60', '#4b6a3f'] },
  madhyam:  { base: '#2d4c1e', hover: '#3e5c2e', active: '#1b3310', gradient: ['#3e5c2e', '#1b3310'] },
};

/* ── Region label positions (tuned for viewBox 0 0 612 696) ── */
const REGION_LABELS: Record<string, { x: number; y: number; label: string; sub: string }> = {
  uttar:    { x: 195, y: 175, label: 'Uttar',    sub: 'North India'   },
  dakshin:  { x: 230, y: 560, label: 'Dakshin',  sub: 'South India'   },
  poorabh:  { x: 505, y: 270, label: 'Poorabh',  sub: 'East India'    },
  pashchim: { x: 85,  y: 355, label: 'Pashchim', sub: 'West India'    },
  madhyam:  { x: 280, y: 340, label: 'Madhyam',  sub: 'Central India' },
};

/* ── Render order (back → front) ── */
const RENDER_ORDER = ['pashchim', 'madhyam', 'uttar', 'dakshin', 'poorabh'] as const;

export default function IndiaMap({ selectedRegion, onRegionClick }: IndiaMapProps) {
  const [hoveredRegion, setHoveredRegion] = useState<string | null>(null);

  return (
    <>
      <style jsx>{`
        .india-map-container {
          position: relative;
          width: 100%;
          max-width: 520px;
          margin: 0 auto;
        }
        .region-group {
          cursor: pointer;
          transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .region-group:hover {
          filter: brightness(1.15) drop-shadow(0 0 8px rgba(0,0,0,0.25));
        }
        .region-group:hover path {
          stroke-width: 1.4;
        }
        .region-group.active {
          filter: brightness(1.22) drop-shadow(0 0 14px rgba(55,97,33,0.5));
        }
        .region-group.active path {
          stroke-width: 1.8;
        }
        .region-group:focus-visible {
          outline: 2px solid #1B6B3A;
          outline-offset: 2px;
          border-radius: 4px;
        }
        .state-path {
          transition: fill 0.3s ease, stroke-width 0.25s ease;
        }
        .region-label-text {
          pointer-events: none;
          user-select: none;
          font-family: 'Inter', 'Segoe UI', Arial, Helvetica, sans-serif;
          text-shadow: 0 1px 4px rgba(0,0,0,0.45), 0 0 8px rgba(0,0,0,0.15);
          transition: opacity 0.3s ease;
        }
        .region-label-sub {
          pointer-events: none;
          user-select: none;
          font-family: 'Inter', 'Segoe UI', Arial, Helvetica, sans-serif;
          text-shadow: 0 1px 3px rgba(0,0,0,0.4);
          letter-spacing: 0.03em;
          transition: opacity 0.3s ease;
        }
        /* Pulse animation for active region */
        @keyframes regionPulse {
          0%, 100% { filter: brightness(1.22) drop-shadow(0 0 14px rgba(55,97,33,0.5)); }
          50% { filter: brightness(1.28) drop-shadow(0 0 20px rgba(55,97,33,0.65)); }
        }
        .region-group.active {
          animation: regionPulse 2.5s ease-in-out infinite;
        }
        .region-group.active:hover {
          animation: none;
          filter: brightness(1.25) drop-shadow(0 0 16px rgba(55,97,33,0.55));
        }
      `}</style>

      <div className="india-map-container">
        <svg
          viewBox="0 0 612 696"
          xmlns="http://www.w3.org/2000/svg"
          style={{ display: 'block', width: '100%', height: 'auto' }}
          aria-label="Interactive map of India with 5 clickable regions"
          role="img"
        >
          <defs>
            {/* Gradient fills for each region */}
            {Object.entries(REGION_COLORS).map(([id, c]) => (
              <linearGradient key={id} id={`india-grad-${id}`} x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor={c.gradient[0]} />
                <stop offset="100%" stopColor={c.gradient[1]} />
              </linearGradient>
            ))}

            {/* Subtle inner glow filter */}
            <filter id="india-glow" x="-10%" y="-10%" width="120%" height="120%">
              <feGaussianBlur stdDeviation="2" result="blur" />
              <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
          </defs>

          {/* Ocean/background hint */}
          <rect x="0" y="0" width="612" height="696" fill="transparent" />

          {/* Render each region group */}
          {RENDER_ORDER.map((regionId) => {
            const paths = (REGION_PATHS as Record<string, string[]>)[regionId];
            if (!paths) return null;

            const isActive = selectedRegion === regionId;
            const isHovered = hoveredRegion === regionId;
            const color = REGION_COLORS[regionId];

            // Determine fill
            let fill: string;
            if (isActive) {
              fill = `url(#india-grad-${regionId})`;
            } else if (isHovered) {
              fill = color.hover;
            } else {
              fill = color.base;
            }

            return (
              <g
                key={regionId}
                className={`region-group${isActive ? ' active' : ''}`}
                onClick={() => onRegionClick(regionId)}
                onMouseEnter={() => setHoveredRegion(regionId)}
                onMouseLeave={() => setHoveredRegion(null)}
                role="button"
                aria-label={`${REGION_LABELS[regionId].label} region – ${REGION_LABELS[regionId].sub}`}
                aria-pressed={isActive}
                tabIndex={0}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onRegionClick(regionId); } }}
              >
                {paths.map((d, i) => (
                  <path
                    key={`${regionId}-${i}`}
                    className="state-path"
                    d={d}
                    fill={fill}
                    stroke="#fff"
                    strokeWidth={isActive ? '1.2' : '0.6'}
                    strokeLinejoin="round"
                    strokeLinecap="round"
                  />
                ))}
              </g>
            );
          })}

          {/* Region labels rendered on top of all paths */}
          {Object.entries(REGION_LABELS).map(([regionId, info]) => {
            const isActive = selectedRegion === regionId;
            const labelColor = '#fff';
            const subColor = 'rgba(255,255,255,0.85)';

            return (
              <g key={`label-${regionId}`} style={{ opacity: isActive ? 1 : 0.92 }}>
                <text
                  className="region-label-text"
                  x={info.x}
                  y={info.y}
                  textAnchor="middle"
                  fontSize={isActive ? '16' : '14'}
                  fontWeight="700"
                  fill={labelColor}
                >
                  {info.label}
                </text>
                <text
                  className="region-label-sub"
                  x={info.x}
                  y={info.y + 17}
                  textAnchor="middle"
                  fontSize="10"
                  fontWeight="500"
                  fill={subColor}
                >
                  {info.sub}
                </text>
              </g>
            );
          })}

          {/* Map footer */}
          <text x="306" y="690" textAnchor="middle" fontSize="10" fill="#aaa" fontFamily="'Inter', Arial, sans-serif">
            Click a region to explore
          </text>
        </svg>
      </div>
    </>
  );
}
