import React, { useState } from 'react';
import { IndicatorChart, ZoneBadge } from './IndicatorChart';
import { RATING_STYLES, INK, MUTED } from '../theme';

// Settori della scala Fear & Greed (stesse soglie di indicatori/fear_greed.py)
const SECTORS = [
  { from: 0, to: 20, label: ['EXTREME', 'FEAR'], rating: 'Extreme fear' },
  { from: 20, to: 40, label: ['FEAR'], rating: 'Fear' },
  { from: 40, to: 60, label: ['NEUTRAL'], rating: 'Neutral' },
  { from: 60, to: 80, label: ['GREED'], rating: 'Greed' },
  { from: 80, to: 100, label: ['EXTREME', 'GREED'], rating: 'Extreme greed' },
];

const W = 400;
const CX = 200;
const CY = 205;
const R_OUT = 190;
const R_IN = 128;
const R_LABEL = 160;
const R_DOTS = 113;
const R_NUM = 97;
const GAP = 0.9; // gradi di spazio tra i settori

// 0 -> sinistra (180°), 100 -> destra (0°)
const angle = (v) => 180 * (1 - v / 100);
const polar = (deg, r) => [CX + r * Math.cos((deg * Math.PI) / 180), CY - r * Math.sin((deg * Math.PI) / 180)];

function sectorPath(from, to) {
  const a0 = angle(from) - GAP;
  const a1 = angle(to) + GAP;
  const [x0, y0] = polar(a0, R_OUT);
  const [x1, y1] = polar(a1, R_OUT);
  const [x2, y2] = polar(a1, R_IN);
  const [x3, y3] = polar(a0, R_IN);
  return `M${x0},${y0} A${R_OUT},${R_OUT} 0 0 1 ${x1},${y1} L${x2},${y2} A${R_IN},${R_IN} 0 0 0 ${x3},${y3} Z`;
}

export default function FearGreedGauge({
  title, subtitle, value, date, pinned,
  dates = [], series = [], color = '#2a78d6', xRange = null, selectedDate = null, onSelectDate = null,
  chartRef = null, twinRef = null, // Timeline: hover collegato con l'altro tachimetro
}) {
  const [view, setView] = useState('overview'); // 'overview' | 'timeline'
  const shown = value == null ? null : Math.round(value);
  const active = shown == null ? null : SECTORS.find((s) => shown >= s.from && (shown < s.to || s.to === 100));

  // Lancetta: triangolo sottile dal centro verso il valore
  const needle = (() => {
    if (shown == null) return null;
    const a = angle(Math.min(100, Math.max(0, value)));
    const [tx, ty] = polar(a, R_DOTS - 4);
    const [lx, ly] = polar(a + 90, 7);
    const [rx, ry] = polar(a - 90, 7);
    return `M${lx},${ly} L${tx},${ty} L${rx},${ry} Z`;
  })();

  return (
    <div className="ed-panel flex flex-col items-center">
      <div className="w-full flex items-start justify-between mb-2 gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="ed-title text-xl">{title}</h3>
            {view === 'timeline' && <ZoneBadge value={value} inline />}
          </div>
          <p className="ed-sub">
            {subtitle}
            {date ? ` · ${pinned ? 'settimana' : 'ultima settimana'} ${new Date(date).toLocaleDateString('it-IT')}` : ''}
          </p>
        </div>
        {/* Selettore Overview / Timeline */}
        <div className="ed-toggle">
          {[['overview', 'Overview'], ['timeline', 'Timeline']].map(([key, label]) => (
            <button
              key={key}
              type="button"
              onClick={() => setView(key)}
              data-active={view === key}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {view === 'timeline' ? (
        <div className="w-full">
          <IndicatorChart dates={dates} values={series} color={color} xRange={xRange} height={260}
            selectedDate={selectedDate} onSelectDate={onSelectDate} chartRef={chartRef} twinRef={twinRef} />
        </div>
      ) : (
      <svg viewBox={`0 0 ${W} 250`} className="w-full max-w-md" role="img"
        aria-label={`${title}: ${shown ?? 'n/d'}${active ? `, ${active.label.join(' ')}` : ''}`}>
        {/* Settori */}
        {SECTORS.map((s) => {
          const on = s === active;
          const mid = angle((s.from + s.to) / 2);
          const [lx, ly] = polar(mid, R_LABEL);
          return (
            <g key={s.from}>
              <path d={sectorPath(s.from, s.to)} fill={on ? RATING_STYLES[s.rating].bg : '#f2f2f2'}
                stroke={on ? RATING_STYLES[s.rating].border : 'none'} strokeWidth={on ? 1.5 : 0}
                style={{ transition: 'fill 300ms ease, stroke 300ms ease' }} />
              <text x={lx} y={ly} transform={`rotate(${90 - mid} ${lx} ${ly})`} textAnchor="middle"
                fontFamily="Roboto Condensed, Arial Narrow, sans-serif" fontSize="15" fontWeight="800"
                letterSpacing="0.3" fill={on ? INK : '#5f5f5f'}>
                {s.label.map((line, i) => (
                  <tspan key={line} x={lx} dy={i === 0 ? (s.label.length > 1 ? -4 : 5) : 15}>{line}</tspan>
                ))}
              </text>
            </g>
          );
        })}

        {/* Lancetta (sotto i numeri, che hanno un bordo bianco per restare leggibili) */}
        {needle && <path d={needle} fill={INK} />}

        {/* Puntini ogni 5 e numeri ogni 25 */}
        {Array.from({ length: 21 }, (_, i) => i * 5).map((v) => {
          if (v % 25 === 0) {
            const [x, y] = polar(angle(v), R_NUM);
            return (
              <text key={v} x={x} y={y + 4} textAnchor="middle" fontSize="13" fill={MUTED}
                stroke="#ffffff" strokeWidth="4" paintOrder="stroke">{v}</text>
            );
          }
          const [x, y] = polar(angle(v), R_DOTS);
          return <circle key={v} cx={x} cy={y} r="1.5" fill="#9a9a9a" />;
        })}

        {/* Valore */}
        <circle cx={CX} cy={CY} r="44" fill="#ffffff" style={{ filter: 'drop-shadow(0 1px 3px rgba(0,0,0,0.12))' }} />
        <text x={CX} y={CY + 12} textAnchor="middle" fontSize="36" fontWeight="800" fill={INK}>
          {shown ?? 'n/d'}
        </text>
      </svg>
      )}

    </div>
  );
}
