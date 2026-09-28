import React, { useEffect } from 'react';
import Plotly from 'plotly.js-dist-min';
import { baseLayout, xAxisStyle, INK, MUTED, RULE, RATING_STYLES } from '../theme';

// Grafico 0-100 con le fasce Fear & Greed a sinistra, usato dagli indicatori e dalla Timeline dei tachimetri

// Scala Fear & Greed (0-100): stesse soglie di indicatori/fear_greed.py
const ZONES = [
  { from: 80, label: 'Extreme greed' },
  { from: 60, label: 'Greed' },
  { from: 40, label: 'Neutral' },
  { from: 20, label: 'Fear' },
  { from: 0, label: 'Extreme fear' },
];
const zoneOf = (v) => ZONES.find((z) => v >= z.from);

// Valore mostrato nel riquadro: settimana selezionata (pin) oppure ultima settimana disponibile
export function currentValue(dates, values, selectedDate) {
  if (selectedDate) {
    const i = dates.indexOf(selectedDate);
    return { value: i === -1 ? null : values[i], date: selectedDate };
  }
  for (let i = values.length - 1; i >= 0; i -= 1) {
    if (values[i] != null) return { value: values[i], date: dates[i] };
  }
  return { value: null, date: null };
}

export function ZoneBadge({ value, date, pinned, inline = false }) {
  const shown = value == null ? null : Math.round(value); // categoria e numero mostrato coincidono
  const zone = shown == null ? null : zoneOf(shown);
  return (
    <div className={inline ? 'flex items-center' : 'flex flex-col items-end gap-1'}>
      <span
        className="ed-rating"
        style={zone
          ? { background: RATING_STYLES[zone.label].bg, borderColor: RATING_STYLES[zone.label].border, color: INK }
          : { background: '#f5f5f5', borderColor: '#cfcfcf', color: MUTED }}
      >
        {zone ? `${zone.label} · ${shown}` : 'n/d'}
      </span>
      {date && !inline && (
        <span className="text-[10px] text-[#8a8a8a]">
          {pinned ? 'Settimana' : 'Ultima settimana'} · {new Date(date).toLocaleDateString('it-IT')}
        </span>
      )}
    </div>
  );
}

export function IndicatorChart({
  dates, values, color, title = '', xRange, selectedDate, onSelectDate, chartRef, twinRef = null, height = 210,
}) {
  const ref = chartRef;

  useEffect(() => {
    if (!ref.current || !dates.length) return;
    const hasData = values.some((v) => v != null);

    const data = [
      {
        x: dates,
        y: values,
        type: 'scatter',
        mode: 'lines',
        line: { color, width: 1.8 },
        hovertemplate: '%{x|%d/%m/%Y}<br><b>%{y:.0f}</b><extra></extra>',
      },
    ];

    // Confini delle fasce Fear & Greed
    const shapes = [20, 40, 60, 80].map((y) => ({
      type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: y, y1: y,
      line: { color: RULE, width: 1, dash: 'dash' },
    }));
    if (selectedDate) {
      shapes.push({ type: 'line', xref: 'x', yref: 'paper', x0: selectedDate, x1: selectedDate, y0: 0, y1: 1,
        line: { color: INK, width: 1, dash: 'dot' } });
    }

    const layout = {
      ...baseLayout,
      height,
      margin: { l: 84, r: 12, t: 8, b: 26 },
      xaxis: { ...xAxisStyle, range: xRange },
      // A sinistra le fasce della scala, al centro di ciascuna
      yaxis: { range: [0, 100], tickvals: [10, 30, 50, 70, 90],
        ticktext: ['EXTREME FEAR', 'FEAR', 'NEUTRAL', 'GREED', 'EXTREME GREED'],
        tickfont: { size: 9, color: MUTED, family: 'Roboto Condensed, Arial Narrow, sans-serif' },
        ticks: '', showgrid: false, showline: false, zeroline: false, fixedrange: true },
      shapes,
      annotations: hasData
        ? []
        : [{ text: 'Sentiment non disponibile per questo titolo', xref: 'paper', yref: 'paper', x: 0.5, y: 0.5,
            showarrow: false, font: { size: 11, color: MUTED } }],
    };

    Plotly.newPlot(ref.current, data, layout, { responsive: true, displayModeBar: false }).then(() => {
      const el = ref.current;
      if (!el) return;
      el.on('plotly_click', (e) => {
        if (e?.points?.length && onSelectDate) onSelectDate(e.points[0].x);
      });
      // Hover sincronizzato con il grafico gemello (stesso indicatore, altra serie)
      el.on('plotly_hover', (e) => {
        // Solo hover reali del mouse: quelli generati da Fx.hover (dal gemello) non vengono rimandati indietro
        if (!(e?.event instanceof Event) || !e.points?.length || !twinRef?.current) return;
        try {
          Plotly.Fx.hover(twinRef.current, [{ curveNumber: 0, pointNumber: e.points[0].pointNumber }]);
        } catch (err) {
          // gemello non ancora disegnato
        }
      });
      el.on('plotly_unhover', () => {
        try {
          if (twinRef?.current) Plotly.Fx.unhover(twinRef.current);
        } catch (err) {}
      });
    });

    const el = ref.current;
    const onResize = () => el && Plotly.Plots.resize(el);
    window.addEventListener('resize', onResize);
    return () => {
      window.removeEventListener('resize', onResize);
      Plotly.purge(el);
    };
  }, [dates, values, color, title, xRange, selectedDate, onSelectDate, height]);

  return <div ref={ref} className="w-full" style={{ minHeight: `${height}px` }} />;
}
