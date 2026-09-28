/**
 * Calcola media mobile e banda di deviazione standard (+1 e -1 sigma)
 * @param {Array} data - Array di oggetti con { time, [valueKey] }
 * @param {number} windowSize - Finestra temporale di calcolo (es. 5 periodi)
 * @param {string} valueKey - Chiave del valore su cui calcolare la statistica ('close', 'score', ecc.)
 */
export function calculateMeanAndStdDev(data, windowSize = 5, valueKey = 'close') {
  return data.map((item, idx, arr) => {
    const start = Math.max(0, idx - windowSize + 1);
    const windowSlice = arr.slice(start, idx + 1);
    const values = windowSlice.map((d) => (d[valueKey] !== undefined ? d[valueKey] : d.close ?? 0));
    const n = values.length;

    // Calcolo Media (mu)
    const mean = values.reduce((sum, v) => sum + v, 0) / n;

    // Calcolo Varianza e Deviazione Standard (sigma)
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / (n > 1 ? n : 1);
    const stdDev = Math.sqrt(variance);

    const rawValue = item[valueKey] !== undefined ? item[valueKey] : (item.close ?? 0);

    return {
      time: item.time,
      value: Number(rawValue.toFixed(2)),
      mean: Number(mean.toFixed(2)),
      upperStd: Number((mean + stdDev).toFixed(2)), // +1 Deviazione Standard
      lowerStd: Number((mean - stdDev).toFixed(2)), // -1 Deviazione Standard
      stdDev: Number(stdDev.toFixed(2)),
      volume: item.volume,
    };
  });
}
