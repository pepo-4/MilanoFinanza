import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { DATASETS } from '../data/weeklyData';
import { defaultRange } from './StatPlotlyChart';
import { baseLayout, xAxisStyle, yAxisStyle, INK } from '../theme';

const LINE = '#4a3aa7'; // viola: combina prezzi (blu) e notizie (arancione)

// Correlazione mobile (-1..+1) a tutta larghezza, con lo 0 tratteggiato
function CorrelationChart({ title, subtitle, dates, values, xRange, selectedDate, onSelectDate }) {
  const ref = useRef(null);

  useEffect(() => {
    if (!ref.current) return;
    const shapes = [
      { type: 'line', xref: 'paper', x0: 0, x1: 1, yref: 'y', y0: 0, y1: 0,
        line: { color: INK, width: 1, dash: 'dash' } },
    ];
    if (selectedDate) {
      shapes.push({ type: 'line', xref: 'x', yref: 'paper', x0: selectedDate, x1: selectedDate, y0: 0, y1: 1,
        line: { color: INK, width: 1, dash: 'dot' } });
    }
    const layout = {
      ...baseLayout,
      height: 260,
      margin: { l: 10, r: 40, t: 8, b: 28 },
      xaxis: { ...xAxisStyle, range: xRange },
      yaxis: { ...yAxisStyle, range: [-1.05, 1.05], tickvals: [-1, -0.5, 0, 0.5, 1], fixedrange: true },
      shapes,
    };
    const data = [{
      x: dates, y: values, type: 'scatter', mode: 'lines', line: { color: LINE, width: 1.8 },
      hovertemplate: '%{x|%d/%m/%Y}<br><b>%{y:+.2f}</b><extra></extra>',
    }];

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
      <h3 className="ed-title text-lg">{title}</h3>
      <p className="ed-sub mb-1">{subtitle}</p>
      <div ref={ref} className="w-full" style={{ minHeight: '260px' }} />
    </div>
  );
}

export default function CorrelationCharts({ ticker = 'UCG.MI', syncRange = null, selectedDate = null, onSelectDate = null }) {
  const { dates, correlation } = DATASETS[ticker] || DATASETS['UCG.MI'];
  const xRange = syncRange || defaultRange(dates);
  const w = correlation.window;

  return (
    <section className="w-full flex flex-col gap-6">
      <div>
        <h2 className="ed-title text-2xl">Correlazione</h2>
        <p className="ed-sub">Ultime {w} settimane · sotto lo 0 si muovono in direzioni opposte</p>
      </div>
      <CorrelationChart
        title="Rendimento vs sentiment"
        subtitle="Variazione % della chiusura settimanale contro score medio delle notizie"
        dates={dates}
        values={correlation.rendimento_sentiment}
        xRange={xRange}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
      />
      <CorrelationChart
        title="Fear & Greed: prezzi vs notizie"
        subtitle="Indice sintetico dei prezzi contro quello delle notizie"
        dates={dates}
        values={correlation.fgi}
        xRange={xRange}
        selectedDate={selectedDate}
        onSelectDate={onSelectDate}
      />
    </section>
  );
}
