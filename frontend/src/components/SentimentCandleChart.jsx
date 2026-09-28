import React from 'react';
import StatPlotlyChart from './StatPlotlyChart';
import { DATASETS } from '../data/weeklyData';

export default function SentimentCandleChart({
  ticker = 'UCG.MI',
  instrumentName = 'Unicredit',
  height = 420,
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
      color="#2563eb"
      bandColor="rgba(56, 189, 248, 0.20)"
      height={height}
    />
  );
}
