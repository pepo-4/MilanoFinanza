import React, { useRef } from 'react';
import { DATASETS } from '../data/weeklyData';
import { defaultRange } from './StatPlotlyChart';
import FearGreedGauge from './FearGreedGauge';
import { IndicatorChart, ZoneBadge, currentValue } from './IndicatorChart';

// Righe della griglia: stesso indicatore, prezzi a sinistra e notizie a destra
const INDICATORS = [
  { key: 'momentum', label: 'Momentum', help: 'Distanza dalla media delle ultime 26 settimane' },
  { key: 'forza', label: 'Forza', help: 'RSI: rialzi contro ribassi, ultime 14 settimane' },
  { key: 'pressione', label: 'Pressione', help: 'Quota di volume nelle settimane in salita' },
  { key: 'incertezza', label: 'Incertezza', help: 'Escursione rispetto alla norma annuale (alta = fear)' },
];

const SERIES = [
  { key: 'prezzi', label: 'Prezzi', color: '#2a78d6' },
  { key: 'notizie', label: 'Notizie', color: '#eb6834' },
];

// Una riga: stesso indicatore per prezzi (sinistra) e notizie (destra), con hover collegato
function IndicatorRow({ ind, dates, indicators, xRange, selectedDate, onSelectDate }) {
  const refs = { prezzi: useRef(null), notizie: useRef(null) };
  return SERIES.map((s) => (
    <div key={`${ind.key}-${s.key}`} className="ed-panel">
      <div className="flex items-start justify-between gap-3 mb-1">
        <div>
          <h3 className="ed-title text-base">
            {ind.label} <span className="text-[#8a8a8a]">· {s.label}</span>
          </h3>
          <p className="ed-sub">{ind.help}</p>
        </div>
        <ZoneBadge {...currentValue(dates, indicators[s.key][ind.key], selectedDate)} pinned={!!selectedDate} />
      </div>
      <IndicatorChart
        dates={dates}
        values={indicators[s.key][ind.key]}
        color={s.color}
        xRange={xRange}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
        chartRef={refs[s.key]}
        twinRef={refs[s.key === 'prezzi' ? 'notizie' : 'prezzi']}
      />
    </div>
  ));
}

export default function IndicatorGrid({ ticker = 'UCG.MI', syncRange = null, selectedDate = null, onSelectDate = null }) {
  const dataset = DATASETS[ticker] || DATASETS['UCG.MI'];
  const { dates, indicators } = dataset;
  const xRange = syncRange || defaultRange(dates);
  const gaugeRefs = { prezzi: useRef(null), notizie: useRef(null) };

  return (
    <section className="w-full">
      <div className="mb-4">
        <h2 className="ed-title text-2xl">Fear &amp; Greed Index</h2>
        <p className="ed-sub">Stessi 4 indicatori su prezzi e notizie · scala 0–100</p>
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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-8 gap-y-6 w-full">
        {INDICATORS.map((ind) => (
          <IndicatorRow
            key={ind.key}
            ind={ind}
            dates={dates}
            indicators={indicators}
            xRange={xRange}
            selectedDate={selectedDate}
            onSelectDate={onSelectDate}
          />
        ))}
      </div>
    </section>
  );
}
