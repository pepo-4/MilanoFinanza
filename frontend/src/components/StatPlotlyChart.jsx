import React, { useEffect, useRef } from 'react';
import Plotly from 'plotly.js-dist-min';

export default function StatPlotlyChart({
  title = 'Unicredit · sentiment settimanale delle notizie (gemini-3-flash-preview)',
  dates = [],
  meanValues = [],
  stdValues = [],
  upperValues = [],
  lowerValues = [],
  bottomValues = [], // Notizie o Volumi
  yTitle = 'Sentiment (-1 ... +1)',
  bottomTitle = 'Notizie',
  yRange = [-1.05, 1.05],
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
  const isDark = theme === 'dark';

  useEffect(() => {
    if (!containerRef.current || !dates.length) return;

    // Palette dinamica in base al tema Dark / Light
    const paperBg = isDark ? '#070a12' : '#ffffff';
    const plotBg = isDark ? '#070a12' : '#ffffff';
    const textColor = isDark ? '#94a3b8' : '#475569';
    const titleColor = isDark ? '#e2e8f0' : '#0f172a';
    const gridColor = isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.06)';
    const axisLineColor = isDark ? '#1e293b' : '#cbd5e1';
    const zeroLineColor = isDark ? 'rgba(255, 255, 255, 0.20)' : 'rgba(0, 0, 0, 0.25)';
    const rangeBtnBg = isDark ? '#111827' : '#f1f5f9';
    const rangeBtnActive = isDark ? '#1f293d' : '#e2e8f0';
    const rangeBtnBorder = isDark ? '#1f2937' : '#cbd5e1';
    const rangeBtnText = isDark ? '#cbd5e1' : '#334155';
    const hoverBg = isDark ? '#0f172a' : '#ffffff';
    const hoverBorder = isDark ? '#334155' : '#cbd5e1';
    const hoverText = isDark ? '#f8fafc' : '#0f172a';
    const actualBandColor = bandColor || (isDark ? 'rgba(56, 189, 248, 0.20)' : 'rgba(59, 130, 246, 0.16)');
    const barColor = isDark ? '#64748b' : '#71717a';

    // Traccia 1: Bordo Superiore Banda (+1 deviazione standard) - invisibile
    const traceUpper = {
      x: dates,
      y: upperValues,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'transparent', width: 0 },
      showlegend: false,
      hoverinfo: 'skip',
      xaxis: 'x',
      yaxis: 'y',
    };

    // Traccia 2: Bordo Inferiore Banda (-1 deviazione standard) con riempimento verso la precedente
    const traceLower = {
      x: dates,
      y: lowerValues,
      type: 'scatter',
      mode: 'lines',
      line: { color: 'transparent', width: 0 },
      fill: 'tonexty',
      fillcolor: actualBandColor,
      name: '± 1 deviazione standard',
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
      marker: { color: barColor },
      name: bottomTitle,
      hovertemplate: `${bottomTitle}: %{y}<extra></extra>`,
      xaxis: 'x',
      yaxis: 'y2',
      showlegend: false,
    };

    const data = [traceUpper, traceLower, traceMean, traceBottom];

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
            line: {
              color: isDark ? '#38bdf8' : '#2563eb',
              width: 2,
              dash: 'dot',
            },
          },
        ]
      : [];

    const cursorAnnotations = selectedDate
      ? [
          {
            x: selectedDate,
            y: 0.99,
            yref: 'paper',
            text: `📍 ${selectedDate}`,
            showarrow: false,
            font: {
              size: 10,
              color: isDark ? '#38bdf8' : '#2563eb',
              family: 'JetBrains Mono, monospace',
            },
            bgcolor: isDark ? '#0f172a' : '#ffffff',
            bordercolor: isDark ? '#334155' : '#cbd5e1',
            borderwidth: 1,
            borderpad: 2,
            xanchor: 'center',
            yanchor: 'bottom',
          },
        ]
      : [];

    // Layout Plotly con supporto Light / Dark mode e Cursore Sincronizzato
    const layout = {
      title: {
        text: title,
        font: { color: titleColor, size: 13, family: 'Plus Jakarta Sans, sans-serif' },
        x: 0.01,
        y: 0.98,
        xanchor: 'left',
      },
      paper_bgcolor: paperBg,
      plot_bgcolor: plotBg,
      font: { color: textColor, family: 'Plus Jakarta Sans, monospace', size: 11 },
      height: height,
      margin: { l: 55, r: 25, t: 45, b: 35 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 1,
        y: 1.08,
        xanchor: 'right',
        font: { size: 11, color: textColor },
        bgcolor: 'transparent',
      },
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: hoverBg,
        bordercolor: hoverBorder,
        font: { color: hoverText, size: 11, family: 'JetBrains Mono, monospace' },
      },
      shapes: cursorShapes,
      annotations: cursorAnnotations,
      // Asse X condiviso
      xaxis: {
        domain: [0, 1],
        anchor: 'y2',
        gridcolor: gridColor,
        linecolor: axisLineColor,
        zerolinecolor: gridColor,
        showspikes: true,
        spikemode: 'across',
        spikedash: 'dot',
        spikethickness: 1,
        spikecolor: textColor,
        rangeselector: {
          buttons: [
            { count: 6, label: '6M', step: 'month', stepmode: 'backward' },
            { count: 1, label: '1A', step: 'year', stepmode: 'backward' },
            { count: 2, label: '2A', step: 'year', stepmode: 'backward' },
            { step: 'all', label: 'Tutto' },
          ],
          bgcolor: rangeBtnBg,
          activecolor: rangeBtnActive,
          bordercolor: rangeBtnBorder,
          borderwidth: 1,
          font: { color: rangeBtnText, size: 10 },
          x: 0.01,
          y: 0.92,
        },
      },
      // Asse Y principale (grafico superiore)
      yaxis: {
        domain: [0.30, 0.88],
        title: { text: yTitle, font: { size: 11, color: textColor } },
        range: yRange,
        gridcolor: gridColor,
        linecolor: axisLineColor,
        zeroline: true,
        zerolinecolor: zeroLineColor,
        zerolinedash: 'dash',
        zerolinewidth: 1,
      },
      // Asse Y secondario (grafico inferiore delle notizie/volumi)
      yaxis2: {
        domain: [0, 0.22],
        title: { text: bottomTitle, font: { size: 11, color: textColor } },
        gridcolor: gridColor,
        linecolor: axisLineColor,
        zerolinecolor: gridColor,
      },
    };

    const config = {
      responsive: true,
      displayModeBar: false,
    };

    Plotly.newPlot(containerRef.current, data, layout, config).then(() => {
      const el = containerRef.current;
      if (!el) return;

      // Evento Hover: sincronizza il cursore dell'altro grafico in tempo reale
      el.on('plotly_hover', (eventData) => {
        if (eventData?.points?.length && syncTargetRef?.current) {
          const pt = eventData.points[0];
          try {
            Plotly.Fx.hover(syncTargetRef.current, [
              { curveNumber: 2, pointNumber: pt.pointNumber },
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

      // Evento Relayout: sincronizza la finestra temporale (6M, 1A, Zoom) con l'altro grafico
      el.on('plotly_relayout', (eventData) => {
        if (onRangeChange && !isInternalRelayout.current) {
          if (eventData['xaxis.range[0]'] && eventData['xaxis.range[1]']) {
            onRangeChange([eventData['xaxis.range[0]'], eventData['xaxis.range[1]']]);
          } else if (eventData['xaxis.autorange']) {
            onRangeChange(null);
          }
        }
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
    yTitle,
    bottomTitle,
    yRange,
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
        })
        .catch(() => {
          isInternalRelayout.current = false;
        });
    }
  }, [syncRange]);

  return (
    <div
      className={`border rounded-xl p-2.5 shadow-xl w-full transition-colors duration-200 ${
        isDark
          ? 'bg-[#070a12] border-dark-750/80 shadow-black/40'
          : 'bg-white border-slate-200 shadow-slate-200/60'
      }`}
    >
      <div ref={containerRef} className="w-full" style={{ minHeight: `${height}px` }} />
    </div>
  );
}
