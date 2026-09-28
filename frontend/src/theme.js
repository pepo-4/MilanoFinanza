// Stile condiviso dei grafici (ispirato a CNN Fear & Greed): bianco, griglia tratteggiata leggera,
// scala a destra, linea verticale che segue il mouse e tooltip sobrio.
export const FONT = 'Inter, system-ui, sans-serif';
export const INK = '#111111';
export const MUTED = '#6b6b6b';
export const RULE = '#e5e5e5';
export const PRICE = '#2a78d6';
export const NEWS = '#eb6834';

export const baseLayout = {
  paper_bgcolor: '#ffffff',
  plot_bgcolor: '#ffffff',
  font: { family: FONT, size: 11, color: MUTED },
  showlegend: false,
  hovermode: 'x',
  spikedistance: -1, // la linea verticale segue il mouse ovunque nel grafico
  hoverdistance: -1,
  hoverlabel: {
    bgcolor: '#ffffff',
    bordercolor: INK,
    font: { family: FONT, size: 12, color: INK },
    align: 'left',
  },
};

export const xAxisStyle = {
  showgrid: false,
  linecolor: '#cfcfcf',
  ticks: '',
  tickfont: { size: 11, color: MUTED },
  showspikes: true,
  spikemode: 'across',
  spikesnap: 'hovered data',
  spikecolor: INK,
  spikethickness: 1,
  spikedash: 'solid',
};

export const yAxisStyle = {
  side: 'right',
  gridcolor: RULE,
  griddash: 'dash',
  zeroline: false,
  showline: false,
  ticks: '',
  tickfont: { size: 11, color: MUTED },
};

// Riquadro della categoria Fear & Greed (colori come i settori del tachimetro)
export const RATING_STYLES = {
  'Extreme fear': { bg: '#fbd5c8', border: '#c2410c', text: '#111111' },
  Fear: { bg: '#fde6dc', border: '#ea580c', text: '#111111' },
  Neutral: { bg: '#ececec', border: '#3f3f3f', text: '#111111' },
  Greed: { bg: '#dcf2e2', border: '#16803c', text: '#111111' },
  'Extreme greed': { bg: '#c3ebce', border: '#166534', text: '#111111' },
};
