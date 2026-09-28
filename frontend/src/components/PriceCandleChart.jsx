import React, { useMemo } from 'react';
import StatPlotlyChart from './StatPlotlyChart';
import { DATASETS } from '../data/weeklyData';

export default function PriceCandleChart({
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
  const { dates, price } = currentDataset;

  // Volume verde se la chiusura settimanale è salita, rosso se è scesa (grigio la prima settimana)
  const volumeColors = useMemo(
    () => price.direction.map((d) => (d == null ? '#94a3b8' : d < 0 ? '#dc2626' : '#16a34a')),
    [price.direction]
  );

  const minPrice = Math.max(0, Math.floor(Math.min(...price.lower) * 0.9));
  const maxPrice = Math.ceil(Math.max(...price.upper) * 1.1);  // usato solo se non ci sono dati visibili

  return (
    <StatPlotlyChart
      title="Prezzo"
      dates={dates}
      meanValues={price.mean}
      stdValues={price.std}
      upperValues={price.upper}
      lowerValues={price.lower}
      bottomValues={price.volume}
      bottomColors={volumeColors}
      yTitle="Media settimanale (€)"
      bottomTitle="Volumi"
      yRange={[minPrice, maxPrice]}
      autoY
      meanLabel="Media"
      color="#2a78d6"
      bandColor="rgba(42, 120, 214, 0.18)"
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
