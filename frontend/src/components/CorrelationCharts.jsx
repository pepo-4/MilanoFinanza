import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { DATASETS } from '../data/weeklyData';
import { defaultRange } from './StatPlotlyChart';
import { baseLayout, xAxisStyle, yAxisStyle, INK, MUTED, RATING_STYLES } from '../theme';
import { currentValue } from './IndicatorChart';

// Stessi verde e rosso del resto della pagina (barre dei volumi, riquadri Fear & Greed)
const LINE = '#111111';
const CONCORDI = '#16a34a'; // verde
const OPPOSTI = '#dc2626'; // rosso
const CONCORDI_FILL = 'rgba(22, 163, 74, 0.16)';
const OPPOSTI_FILL = 'rgba(220, 38, 38, 0.14)';

// Stato della correlazione: soglie ±0.2
function corrState(v) {
  if (v == null) return { label: 'n/d', style: { background: '#f5f5f5', borderColor: '#cfcfcf', color: MUTED } };
  const box = (r) => ({ background: r.bg, borderColor: r.border, color: r.text });
  if (v > 0.2) return { label: 'Concordi', style: box(RATING_STYLES.Greed) };
  if (v < -0.2) return { label: 'Opposti', style: box(RATING_STYLES.Fear) };
  return { label: 'Slegati', style: box(RATING_STYLES.Neutral) };
}

const LABEL_FONT = { size: 10, family: 'Roboto Condensed, Arial Narrow, sans-serif' };

// Riquadro con lo stato della settimana selezionata (o dell'ultima)
function CorrBadge({ value }) {
  const st = corrState(value);
  return (
    <span className="ed-rating" style={st.style}>
      {value == null ? st.label : `${st.label} · ${value > 0 ? '+' : ''}${value.toFixed(2)}`}
    </span>
  );
}

// Correlazione mobile (-1..+1) a tutta larghezza, con lo 0 tratteggiato
function CorrelationChart({ title, subtitle, dates, values, xRange, selectedDate, onSelectDate }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const shapes = [
      { type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: 0, y1: 0,
        line: { color: '#9a9a9a', width: 1, dash: 'dash' } },
    ];
    if (selectedDate) {
      shapes.push({ type: 'line', xref: 'x', yref: 'paper', x0: selectedDate, x1: selectedDate, y0: 0, y1: 1,
        line: { color: INK, width: 1, dash: 'dot' } });
    }
    // A sinistra il significato della scala, a destra i numeri
    const sideLabel = (y, text, color) => ({ text: `<b>${text}</b>`, xref: 'paper', x: 0, xanchor: 'right', xshift: -8,
      yref: 'y', y, showarrow: false, font: { ...LABEL_FONT, color } });
    const layout = {
      ...baseLayout,
      height: 240,
      margin: { l: 70, r: 40, t: 6, b: 28 },
      xaxis: { ...xAxisStyle, range: xRange },
      yaxis: { ...yAxisStyle, range: [-1.05, 1.05], tickvals: [-1, -0.5, 0, 0.5, 1], fixedrange: true },
      shapes,
      annotations: [sideLabel(0.9, 'CONCORDI', CONCORDI), sideLabel(0, 'SLEGATI', MUTED), sideLabel(-0.9, 'OPPOSTI', OPPOSTI)],
    };
    const area = (clip, fillcolor) => ({
      x: dates, y: values.map((v) => (v == null ? null : clip(v))), type: 'scatter', mode: 'lines',
      line: { width: 0 }, fill: 'tozeroy', fillcolor, hoverinfo: 'skip', connectgaps: false,
    });
    const data = [
      // Aree colorate tra lo 0 e la linea: verde quando concordi, rosso quando opposti
      area((v) => Math.max(v, 0), CONCORDI_FILL),
      area((v) => Math.min(v, 0), OPPOSTI_FILL),
      {
        x: dates, y: values, type: 'scatter', mode: 'lines', line: { color: LINE, width: 2.2 },
        customdata: values.map((v) => corrState(v).label),
        hovertemplate: '%{x|%d/%m/%Y}<br><b>%{y:+.2f}</b> · %{customdata}<extra></extra>',
      },
    ];

    const el = ref.current;
    Plotly.newPlot(el, data, layout, { responsive: true, displayModeBar: false }).then(() => {
      el.on('plotly_click', (e) => {
        if (e?.points?.length && onSelectDate) onSelectDate(e.points[0].x);
      });
    });
    const onResize = () => Plotly.Plots.resize(el);
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      Plotly.purge(el);
    };
  }, [dates, values, xRange, selectedDate, onSelectDate]);

  return (
    <div className="ed-panel w-full">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="ed-title text-lg">{title}</h3>
          <p className="ed-sub">{subtitle}</p>
        </div>
        <CorrBadge {...currentValue(dates, values, selectedDate)} />
      </div>
      <div ref={ref} className="w-full" style={{ minHeight: '240px' }} />
    </div>
  );
}

export default function CorrelationCharts({ ticker = 'UCG.MI', syncRange = null, selectedDate = null, onSelectDate = null }) {
  const { dates, correlation } = DATASETS[ticker] || DATASETS['UCG.MI'];
  const xRange = syncRange || defaultRange(dates);
  const w = correlation.window;

  return (
    <section className="w-full flex flex-col gap-5">
      <div>
        <h2 className="ed-title text-2xl">Correlazione</h2>
        <p className="ed-sub">Correlazione mobile a {w} settimane, da −1 a +1</p>
      </div>
      <CorrelationChart
        title="Rendimento e sentiment"
        subtitle="Rendimento settimanale del titolo contro sentiment medio delle notizie"
        dates={dates}
        values={correlation.rendimento_sentiment}
        xRange={xRange}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
      />
      <CorrelationChart
        title="Fear & Greed: prezzo e sentiment"
        subtitle="Indice sintetico del prezzo contro indice sintetico del sentiment"
        dates={dates}
        values={correlation.fgi}
        xRange={xRange}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
      />
    </section>
  );
}
