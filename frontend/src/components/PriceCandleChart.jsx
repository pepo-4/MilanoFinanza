import React from 'react';
import StatPlotlyChart from './StatPlotlyChart';
import { DATASETS } from '../data/weeklyData';

export default function PriceCandleChart({
  ticker = 'UCG.MI',
  instrumentName = 'Unicredit',
  height = 420,
}) {
  const currentDataset = DATASETS[ticker] || DATASETS['UCG.MI'];
  const { dates, price } = currentDataset;

  const minPrice = Math.max(0, Math.floor(Math.min(...price.lower) * 0.9));
  const maxPrice = Math.ceil(Math.max(...price.upper) * 1.1);

  return (
    <StatPlotlyChart
      title={`${instrumentName} · quotazioni settimanali`}
      dates={dates}
      meanValues={price.mean}
      stdValues={price.std}
      upperValues={price.upper}
      lowerValues={price.lower}
      bottomValues={price.volume}
      yTitle="Prezzo (€)"
      bottomTitle="Volumi"
      yRange={[minPrice, maxPrice]}
      meanLabel="Media settimanale"
      color="#38bdf8"
      bandColor="rgba(56, 189, 248, 0.18)"
      height={height}
    />
  );
}
