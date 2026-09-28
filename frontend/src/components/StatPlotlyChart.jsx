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
  bandColor = 'rgba(56, 189, 248, 0.22)', // colore banda ±1σ
  height = 420,
}) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current || !dates.length) return;

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
      fillcolor: bandColor,
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
      marker: { color: '#64748b' },
      name: bottomTitle,
      hovertemplate: `${bottomTitle}: %{y}<extra></extra>`,
      xaxis: 'x',
      yaxis: 'y2',
      showlegend: false,
    };

    const data = [traceUpper, traceLower, traceMean, traceBottom];

    // Layout con sfondo nero e assi puliti
    const layout = {
      title: {
        text: title,
        font: { color: '#e2e8f0', size: 13, family: 'Plus Jakarta Sans, sans-serif' },
        x: 0.01,
        y: 0.98,
        xanchor: 'left',
      },
      paper_bgcolor: '#070a12',
      plot_bgcolor: '#070a12',
      font: { color: '#94a3b8', family: 'Plus Jakarta Sans, monospace', size: 11 },
      height: height,
      margin: { l: 55, r: 25, t: 45, b: 35 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 1,
        y: 1.08,
        xanchor: 'right',
        font: { size: 11, color: '#94a3b8' },
        bgcolor: 'transparent',
      },
      hovermode: 'x unified',
      hoverlabel: {
        bgcolor: '#0f172a',
        bordercolor: '#334155',
        font: { color: '#f8fafc', size: 11, family: 'JetBrains Mono, monospace' },
      },
      // Asse X condiviso
      xaxis: {
        domain: [0, 1],
        anchor: 'y2',
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        linecolor: '#1e293b',
        zerolinecolor: 'rgba(255, 255, 255, 0.08)',
        showspikes: true,
        spikemode: 'across',
        spikedash: 'dot',
        spikethickness: 1,
        spikecolor: '#94a3b8',
        rangeselector: {
          buttons: [
            { count: 6, label: '6M', step: 'month', stepmode: 'backward' },
            { count: 1, label: '1A', step: 'year', stepmode: 'backward' },
            { count: 2, label: '2A', step: 'year', stepmode: 'backward' },
            { step: 'all', label: 'Tutto' },
          ],
          bgcolor: '#111827',
          activecolor: '#1f293d',
          bordercolor: '#1f2937',
          borderwidth: 1,
          font: { color: '#cbd5e1', size: 10 },
          x: 0.01,
          y: 0.92,
        },
      },
      // Asse Y principale (grafico superiore)
      yaxis: {
        domain: [0.30, 0.88],
        title: { text: yTitle, font: { size: 11, color: '#94a3b8' } },
        range: yRange,
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        linecolor: '#1e293b',
        zeroline: true,
        zerolinecolor: 'rgba(255, 255, 255, 0.20)',
        zerolinedash: 'dash',
        zerolinewidth: 1,
      },
      // Asse Y secondario (grafico inferiore delle notizie/volumi)
      yaxis2: {
        domain: [0, 0.22],
        title: { text: bottomTitle, font: { size: 11, color: '#94a3b8' } },
        gridcolor: 'rgba(255, 255, 255, 0.05)',
        linecolor: '#1e293b',
        zerolinecolor: 'rgba(255, 255, 255, 0.08)',
      },
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['select2d', 'lasso2d'],
    };

    Plotly.newPlot(containerRef.current, data, layout, config);

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
  ]);

  return (
    <div className="bg-[#070a12] border border-dark-750/80 rounded-xl p-2.5 shadow-xl w-full">
      <div ref={containerRef} className="w-full" style={{ minHeight: `${height}px` }} />
    </div>
  );
}
