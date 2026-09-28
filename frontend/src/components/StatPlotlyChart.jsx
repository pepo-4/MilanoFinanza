import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';
import { baseLayout, xAxisStyle, yAxisStyle, INK, MUTED } from '../theme';

// Finestre temporali disponibili (in mesi); la prima vista è 1 anno
const RANGE_MONTHS = { '6M': 6, '1A': 12, '2A': 24 };
const DEFAULT_MONTHS = 12;

const toDate = (v) => new Date(String(v).replace(' ', 'T'));

export function defaultRange(dates, months = DEFAULT_MONTHS) {
  const end = toDate(dates[dates.length - 1]);
  const start = new Date(end);
  start.setMonth(start.getMonth() - months);
  return [start.toISOString().slice(0, 10), dates[dates.length - 1]];
}

// Fascia ±1σ come poligoni separati per ogni tratto senza buchi (niente riempimenti in diagonale)
function bandPolygon(dates, upper, lower) {
  const x = [];
  const y = [];
  let seg = [];
  const flush = () => {
    if (seg.length) {
      seg.forEach((i) => { x.push(dates[i]); y.push(upper[i]); });
      [...seg].reverse().forEach((i) => { x.push(dates[i]); y.push(lower[i]); });
      x.push(null);
      y.push(null);
    }
    seg = [];
  };
  dates.forEach((_, i) => {
    if (upper[i] == null || lower[i] == null) flush();
    else seg.push(i);
  });
  flush();
  return { x, y };
}

// Range Y adattato ai dati visibili nella finestra [x0, x1]
function visibleRange(dates, series, x0, x1, pad = 0.08) {
  const a = toDate(x0);
  const b = toDate(x1);
  let lo = Infinity;
  let hi = -Infinity;
  dates.forEach((d, i) => {
    const t = toDate(d);
    if (t < a || t > b) return;
    series.forEach((s) => {
      const v = s[i];
      if (v == null) return;
      lo = Math.min(lo, v);
      hi = Math.max(hi, v);
    });
  });
  if (!Number.isFinite(lo)) return null;
  const span = hi - lo || Math.abs(hi) || 1;
  return [lo - span * pad, hi + span * pad];
}

export default function StatPlotlyChart({
  title = 'Sentiment',
  subtitle = '',
  dates = [],
  meanValues = [],
  stdValues = [],
  upperValues = [],
  lowerValues = [],
  bottomValues = [], // Notizie o Volumi
  bottomColors = null, // colore per ogni barra (es. verde/rosso in base al prezzo); null = grigio
  yTitle = 'Sentiment (-1 ... +1)',
  bottomTitle = 'Notizie',
  yRange = [-1.05, 1.05],
  autoY = false, // true: asse Y adattato alla finestra visibile (es. prezzi)
  meanLabel = 'Media settimanale',
  color = '#2563eb', // colore linea media
  bandColor, // colore banda ±1σ
  height = 430,
  theme = 'dark', // 'dark' | 'light'
  selectedDate = null,
  onSelectDate = null,
  syncTargetRef = null,
  syncRange = null,
  onRangeChange = null,
  externalRef = null,
}) {
  const internalRef = useRef(null);
  const containerRef = externalRef || internalRef;
  const isInternalRelayout = useRef(false);
  const fitYRef = useRef(null);
  const isDark = theme === 'dark';

  useEffect(() => {
    if (!containerRef.current || !dates.length) return;

    const actualBandColor = bandColor || 'rgba(42, 120, 214, 0.18)';
    const barColor = '#b5b5b5';

    // Traccia 1: Banda ±1 deviazione standard (poligono chiuso per ogni tratto continuo)
    const band = bandPolygon(dates, upperValues, lowerValues);
    const traceBand = {
      x: band.x,
      y: band.y,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'transparent', width: 0 },
      fill: 'toself',
      fillcolor: actualBandColor,
      name: '± 1σ',
      hoverinfo: 'skip',
      xaxis: 'x',
      yaxis: 'y',
    };

    // Traccia 3: Linea della Media Settimanale
    const traceMean = {
      x: dates,
      y: meanValues,
      type: 'scatter',
      mode: 'lines',
      line: { color: color, width: 2 },
      name: meanLabel,
      customdata: stdValues,
      hovertemplate:
        '<b>settimana al %{x|%d/%m/%Y}</b><br>' +
        'media %{y:+.2f} ± %{customdata:.2f}<extra></extra>',
      xaxis: 'x',
      yaxis: 'y',
    };

    // Traccia 4: Istogramma/Barre inferiori (Notizie o Volumi)
    const traceBottom = {
      x: dates,
      y: bottomValues,
      type: 'bar',
      marker: { color: bottomColors || barColor },
      name: bottomTitle,
      hovertemplate: `${bottomTitle}: %{y}<extra></extra>`,
      xaxis: 'x',
      yaxis: 'y2',
      showlegend: false,
    };

    // L'indice 1 (media) è usato per sincronizzare l'hover tra i due grafici
    const data = [traceBand, traceMean, traceBottom];
    const xRange = syncRange || defaultRange(dates);

    // Cursore/Linea sincronizzata se un periodo è stato premuto
    const cursorShapes = selectedDate
      ? [
          {
            type: 'line',
            xref: 'x',
            yref: 'paper',
            x0: selectedDate,
            x1: selectedDate,
            y0: 0,
            y1: 1,
            line: { color: INK, width: 1, dash: 'dot' },
          },
        ]
      : [];

    const cursorAnnotations = selectedDate
      ? [
          {
            x: selectedDate,
            y: 0.99,
            yref: 'paper',
            text: new Date(selectedDate).toLocaleDateString('it-IT'),
            showarrow: false,
            font: { size: 10, color: '#ffffff' },
            bgcolor: INK,
            borderpad: 3,
            xanchor: 'center',
            yanchor: 'bottom',
          },
        ]
      : [];

    // Layout: stile editoriale condiviso (theme.js), legenda in alto a sinistra, scale a destra
    const layout = {
      ...baseLayout,
      height: height,
      margin: { l: 34, r: 48, t: 34, b: 30 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 0,
        y: 1.1,
        xanchor: 'left',
        font: { size: 11, color: MUTED },
        bgcolor: 'transparent',
        itemclick: false,
        itemdoubleclick: false,
      },
      shapes: cursorShapes,
      // Etichette a sinistra: cosa mostra il grafico sopra (media) e sotto (barre)
      annotations: [
        ...cursorAnnotations,
        { text: yTitle, xref: 'paper', yref: 'paper', x: 0, xshift: -22, y: 0.63, textangle: -90,
          showarrow: false, font: { size: 11, color: MUTED } },
        { text: bottomTitle, xref: 'paper', yref: 'paper', x: 0, xshift: -22, y: 0.1, textangle: -90,
          showarrow: false, font: { size: 11, color: MUTED } },
      ],
      // Asse X condiviso
      xaxis: {
        ...xAxisStyle,
        domain: [0, 1],
        anchor: 'y2',
        range: xRange,
        rangeselector: {
          buttons: Object.entries(RANGE_MONTHS).map(([label, count]) => ({
            count,
            label,
            step: 'month',
            stepmode: 'backward',
          })),
          bgcolor: '#f0f0f0',
          activecolor: '#ffffff',
          bordercolor: '#f0f0f0',
          borderwidth: 2,
          font: { color: INK, size: 11 },
          x: 1,
          xanchor: 'right',
          y: 1.1,
        },
      },
      // Asse Y principale (grafico superiore)
      yaxis: {
        ...yAxisStyle,
        domain: [0.3, 0.96],
        range: autoY ? visibleRange(dates, [upperValues, lowerValues, meanValues], ...xRange) || yRange : yRange,
        zeroline: !autoY,
        zerolinecolor: '#9a9a9a',
        zerolinewidth: 1,
      },
      // Asse Y secondario (grafico inferiore delle notizie/volumi)
      yaxis2: {
        ...yAxisStyle,
        domain: [0, 0.2],
        range: [0, (visibleRange(dates, [bottomValues], ...xRange, 0)?.[1] || 1) * 1.1],
        nticks: 3,
      },
    };

    const config = {
      responsive: true,
      displayModeBar: false,
    };

    // Adatta gli assi Y (prezzo e barre) alla finestra visibile
    const fitY = (range) => {
      const el = containerRef.current;
      if (!el) return;
      const update = {};
      if (autoY) {
        const yr = visibleRange(dates, [upperValues, lowerValues, meanValues], ...range);
        if (yr) update['yaxis.range'] = yr;
      }
      const br = visibleRange(dates, [bottomValues], ...range, 0);
      if (br) update['yaxis2.range'] = [0, br[1] * 1.1];
      if (Object.keys(update).length) Plotly.relayout(el, update).catch(() => {});
    };
    fitYRef.current = fitY;

    Plotly.newPlot(containerRef.current, data, layout, config).then(() => {
      const el = containerRef.current;
      if (!el) return;

      // Evento Hover: sincronizza il cursore dell'altro grafico in tempo reale
      el.on('plotly_hover', (eventData) => {
        if (eventData?.points?.length && syncTargetRef?.current) {
          const pt = eventData.points[0];
          try {
            Plotly.Fx.hover(syncTargetRef.current, [
              { curveNumber: 1, pointNumber: pt.pointNumber },
            ]);
          } catch (e) {
            // Ignora eventuali micro-errori durante il drag
          }
        }
      });

      // Evento Unhover: rimuove il tooltip sull'altro grafico
      el.on('plotly_unhover', () => {
        if (syncTargetRef?.current) {
          try {
            Plotly.Fx.unhover(syncTargetRef.current);
          } catch (e) {}
        }
      });

      // Evento Click: fissa il cursore sul periodo selezionato su entrambi i grafici
      el.on('plotly_click', (eventData) => {
        if (eventData?.points?.length && onSelectDate) {
          const pt = eventData.points[0];
          onSelectDate(pt.x, pt.pointNumber);
        }
      });

      // Evento Relayout: adatta gli assi Y e sincronizza la finestra temporale con l'altro grafico
      el.on('plotly_relayout', (eventData) => {
        let range = null;
        if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
          range = [eventData['xaxis.range[0]'], eventData['xaxis.range[1]']];
        } else if (Array.isArray(eventData['xaxis.range'])) {
          range = eventData['xaxis.range'];
        } else if (eventData['xaxis.autorange']) {
          range = [dates[0], dates[dates.length - 1]]; // doppio clic: tutta la serie
        }
        if (!range) return;
        fitY(range);
        if (onRangeChange && !isInternalRelayout.current) onRangeChange(range);
      });
    });

    const handleResize = () => {
      if (containerRef.current) {
        Plotly.Plots.resize(containerRef.current);
      }
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      if (containerRef.current) {
        Plotly.purge(containerRef.current);
      }
    };
  }, [
    title,
    dates,
    meanValues,
    stdValues,
    upperValues,
    lowerValues,
    bottomValues,
    bottomColors,
    yTitle,
    bottomTitle,
    yRange,
    autoY,
    meanLabel,
    color,
    bandColor,
    height,
    isDark,
    selectedDate,
  ]);

  // Sincronizzazione dinamica dello zoom/range dall'altro grafico
  useEffect(() => {
    if (!containerRef.current) return;
    if (syncRange) {
      isInternalRelayout.current = true;
      Plotly.relayout(containerRef.current, {
        'xaxis.range[0]': syncRange[0],
        'xaxis.range[1]': syncRange[1],
      })
        .then(() => {
          isInternalRelayout.current = false;
          fitYRef.current?.(syncRange);
        })
        .catch(() => {
          isInternalRelayout.current = false;
        });
    }
  }, [syncRange]);

  return (
    <div className="ed-panel w-full">
      <h3 className="ed-title text-lg">{title}</h3>
      {subtitle && <p className="ed-sub">{subtitle}</p>}
      <div ref={containerRef} className="w-full" style={{ minHeight: `${height}px` }} />
    </div>
  );
}
