import React, { useMemo } from 'react';
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

  // Barre verdi se lo score medio è salito rispetto alla settimana prima, rosse se è sceso
  const newsColors = useMemo(
    () => sentiment.direction.map((d) => (d == null ? '#94a3b8' : d < 0 ? '#dc2626' : '#16a34a')),
    [sentiment.direction]
  );

  return (
    <StatPlotlyChart
      title="Sentiment"
      dates={dates}
      meanValues={sentiment.mean}
      stdValues={sentiment.std}
      upperValues={sentiment.upper}
      lowerValues={sentiment.lower}
      bottomValues={sentiment.newsCount}
      bottomColors={newsColors}
      yTitle="Sentiment medio (−1 / +1)"
      bottomTitle="Notizie"
      yRange={[-1.05, 1.05]}
      meanLabel="Media"
      color="#eb6834"
      bandColor="rgba(235, 104, 52, 0.18)"
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
