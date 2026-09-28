import React from 'react';
import StatPlotlyChart from './StatPlotlyChart';
import { DATASETS } from '../data/weeklyData';

export default function SentimentCandleChart({
  ticker = 'UCG.MI',
  instrumentName = 'Unicredit',
  height = 420,
  theme = 'dark',
  selectedDate = null,
  onSelectDate = null,
  syncTargetRef = null,
  syncRange = null,
  onRangeChange = null,
  chartContainerRef = null,
}) {
  const currentDataset = DATASETS[ticker] || DATASETS['UCG.MI'];
  const { dates, sentiment } = currentDataset;

  return (
    <StatPlotlyChart
      title={`${instrumentName} · sentiment settimanale delle notizie (gemini-3-flash-preview)`}
      dates={dates}
      meanValues={sentiment.mean}
      stdValues={sentiment.std}
      upperValues={sentiment.upper}
      lowerValues={sentiment.lower}
      bottomValues={sentiment.newsCount}
      yTitle="Sentiment (-1 ... +1)"
      bottomTitle="Notizie"
      yRange={[-1.05, 1.05]}
      meanLabel="Media settimanale"
      color={theme === 'dark' ? '#2563eb' : '#1d4ed8'}
      bandColor={theme === 'dark' ? 'rgba(56, 189, 248, 0.20)' : 'rgba(59, 130, 246, 0.16)'}
      height={height}
      theme={theme}
      selectedDate={selectedDate}
      onSelectDate={onSelectDate}
      syncTargetRef={syncTargetRef}
      syncRange={syncRange}
      onRangeChange={onRangeChange}
      externalRef={chartContainerRef}
    />
  );
}
