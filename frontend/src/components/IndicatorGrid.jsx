import React, { useEffect, useRef, useState } from 'react';
import { Maximize2, X } from 'lucide-react';
import { DATASETS } from '../data/weeklyData';
import { defaultRange } from './StatPlotlyChart';
import FearGreedGauge from './FearGreedGauge';
import { IndicatorChart, ZoneBadge, currentValue } from './IndicatorChart';

// Righe della tabella: stesso indicatore per prezzo e sentiment (definizioni come in indicatori/fear_greed.py,
// finestre in WINDOWS). Sempre: valore alto = greed
const INDICATORS = [
  { key: 'momentum', label: 'Momentum', help: 'Scostamento dalla media mobile a 26 settimane, in deviazioni standard' },
  { key: 'forza', label: 'Forza', help: 'RSI a 14 settimane: rialzi medi rispetto ai ribassi medi' },
  { key: 'pressione', label: 'Pressione', help: 'Quota del volume nelle settimane in rialzo, su 13 settimane' },
  { key: 'incertezza', label: 'Incertezza', help: 'ATR a 8 settimane rispetto alla media annuale' },
];

const SERIES = [
  { key: 'prezzi', label: 'Prezzo', color: '#2a78d6' },
  { key: 'notizie', label: 'Sentiment', color: '#eb6834' },
];

// Mini-grafico dell'indicatore nella finestra visibile (6M/1A/2A), con la settimana selezionata
function Sparkline({ dates, values, color, xRange, selectedDate }) {
  const from = String(xRange[0]).slice(0, 10);
  const to = String(xRange[1]).slice(0, 10);
  const idx = dates.map((d, i) => i).filter((i) => dates[i] >= from && dates[i] <= to);
  const W = 240;
  const H = 48;
  const x = (k) => (idx.length > 1 ? (k / (idx.length - 1)) * W : 0);
  const y = (v) => 3 + (1 - v / 100) * (H - 6);
  let d = '';
  idx.forEach((i, k) => {
    const v = values[i];
    if (v == null) return;
    d += `${d && values[idx[k - 1]] != null ? 'L' : 'M'}${x(k).toFixed(1)},${y(v).toFixed(1)} `;
  });
  const pin = selectedDate ? idx.indexOf(dates.indexOf(selectedDate)) : -1;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" className="w-full h-12" aria-hidden="true">
      <line x1="0" x2={W} y1={y(50)} y2={y(50)} stroke="#e5e5e5" strokeDasharray="3 3" vectorEffect="non-scaling-stroke" />
      {pin !== -1 && (
        <line x1={x(pin)} x2={x(pin)} y1="0" y2={H} stroke="#111111" strokeDasharray="2 2" vectorEffect="non-scaling-stroke" />
      )}
      <path d={d} fill="none" stroke={color} strokeWidth="1.8" strokeLinejoin="round" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

// Tabella unica: una riga per indicatore, prezzi e notizie affiancati
function IndicatorTable({ dates, indicators, xRange, selectedDate, onZoom }) {
  const cols = 'grid grid-cols-[minmax(200px,1.1fr)_minmax(0,1fr)_minmax(0,1fr)_44px] gap-8 items-center';
  return (
    <div className="ed-panel">
      <div className={`${cols} pb-3 border-b border-[#e5e5e5]`}>
        <div>
          <h3 className="ed-title text-xl">I 4 indicatori</h3>
          <p className="ed-sub">
            {selectedDate ? 'Settimana' : 'Ultima settimana'} ·{' '}
            {new Date(currentValue(dates, indicators.prezzi.momentum, selectedDate).date).toLocaleDateString('it-IT')}
          </p>
        </div>
        {SERIES.map((s) => (
          <div key={s.key} className="ed-title text-sm flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
            {s.label}
          </div>
        ))}
        <span />
      </div>
      {INDICATORS.map((ind) => (
        <div key={ind.key} className={`${cols} py-4 border-b border-[#efefef] transition-colors duration-200 hover:bg-[#fafafa]`}>
          <div>
            <div className="ed-title text-lg">{ind.label}</div>
            <p className="ed-sub">{ind.help}</p>
          </div>
          {SERIES.map((s) => {
            const cur = currentValue(dates, indicators[s.key][ind.key], selectedDate);
            return (
              <div key={s.key} className="flex items-center gap-4 min-w-0">
                <span className="ed-title text-3xl w-12 text-right tabular-nums">
                  {cur.value == null ? '–' : Math.round(cur.value)}
                </span>
                <div className="w-32 shrink-0">
                  <ZoneBadge value={cur.value} inline showValue={false} />
                </div>
                <div className="flex-1 min-w-0">
                  <Sparkline dates={dates} values={indicators[s.key][ind.key]} color={s.color}
                    xRange={xRange} selectedDate={selectedDate} />
                </div>
              </div>
            );
          })}
          <button
            type="button"
            onClick={() => onZoom(ind.key)}
            aria-label={`Ingrandisci ${ind.label}`}
            title="Ingrandisci"
            className="w-11 h-11 flex items-center justify-center rounded-full bg-[#f0f0f0] text-[#111111] hover:bg-[#111111] hover:text-white transition-colors duration-200"
          >
            <Maximize2 size={16} />
          </button>
        </div>
      ))}
    </div>
  );
}

// Finestra con i due grafici dell'indicatore ingranditi, prezzo e sentiment affiancati
function IndicatorZoom({ ind, dates, indicators, xRange, selectedDate, onSelectDate, onClose }) {
  const refs = { prezzi: useRef(null), notizie: useRef(null) };
  useEffect(() => {
    const onKey = (e) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    const prev = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      window.removeEventListener('keydown', onKey);
      document.body.style.overflow = prev;
    };
  }, [onClose]);

  return (
    <div className="ed-modal fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/40" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={ind.label}
        className="w-full max-w-[1500px] max-h-full overflow-auto bg-white rounded-lg p-8 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 mb-6">
          <div>
            <h2 className="ed-title text-3xl">{ind.label}</h2>
            <p className="ed-sub text-sm">{ind.help}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Chiudi"
            className="w-11 h-11 flex items-center justify-center rounded-full bg-[#f0f0f0] text-[#111111] hover:bg-[#111111] hover:text-white transition-colors duration-200"
          >
            <X size={18} />
          </button>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {SERIES.map((s) => {
            const cur = currentValue(dates, indicators[s.key][ind.key], selectedDate);
            return (
              <div key={s.key} className="ed-panel">
                <div className="flex items-center justify-between gap-3 mb-2">
                  <h3 className="ed-title text-xl flex items-center gap-2">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
                    {s.label}
                  </h3>
                  <ZoneBadge value={cur.value} inline />
                </div>
                <IndicatorChart
                  dates={dates}
                  values={indicators[s.key][ind.key]}
                  color={s.color}
                  xRange={xRange}
                  height={420}
                  selectedDate={selectedDate}
                  onSelectDate={onSelectDate}
                  chartRef={refs[s.key]}
                  twinRef={refs[s.key === 'prezzi' ? 'notizie' : 'prezzi']}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

export default function IndicatorGrid({ ticker = 'UCG.MI', syncRange = null, selectedDate = null, onSelectDate = null }) {
  const dataset = DATASETS[ticker] || DATASETS['UCG.MI'];
  const { dates, indicators } = dataset;
  const xRange = syncRange || defaultRange(dates);
  const gaugeRefs = { prezzi: useRef(null), notizie: useRef(null) };
  const [zoomKey, setZoomKey] = useState(null); // indicatore aperto nella finestra ingrandita
  const zoomInd = INDICATORS.find((i) => i.key === zoomKey);

  return (
    <section className="w-full">
      <div className="mb-4">
        <h2 className="ed-title text-2xl">Fear &amp; Greed Index</h2>
      </div>

      {/* Riassunto: indice sintetico (media dei 4 indicatori) per prezzi e notizie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 w-full mb-8">
        {SERIES.map((s) => (
          <FearGreedGauge
            key={s.key}
            title={s.label}
            subtitle="Media dei 4 indicatori"
            {...currentValue(dates, indicators[s.key].sintesi, selectedDate)}
            pinned={!!selectedDate}
            dates={dates}
            series={indicators[s.key].sintesi}
            color={s.color}
            xRange={xRange}
            selectedDate={selectedDate}
            onSelectDate={onSelectDate}
            chartRef={gaugeRefs[s.key]}
            twinRef={gaugeRefs[s.key === 'prezzi' ? 'notizie' : 'prezzi']}
          />
        ))}
      </div>

      <IndicatorTable dates={dates} indicators={indicators} xRange={xRange} selectedDate={selectedDate} onZoom={setZoomKey} />

      {zoomInd && (
        <IndicatorZoom
          ind={zoomInd}
          dates={dates}
          indicators={indicators}
          xRange={xRange}
          selectedDate={selectedDate}
          onSelectDate={onSelectDate}
          onClose={() => setZoomKey(null)}
        />
      )}
    </section>
  );
}
