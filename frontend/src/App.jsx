import React, { useState, useRef } from 'react';
// Componenti modulari (disattivati temporaneamente via flag, pronti per essere riattivati)
import TopMetrics from './components/TopMetrics';
import NewsPanel from './components/NewsPanel';
import PriceCandleChart from './components/PriceCandleChart';
import SentimentCandleChart from './components/SentimentCandleChart';
import IndicatorGrid from './components/IndicatorGrid';
import WeekNewsCards from './components/WeekNewsCards';
import CorrelationCharts from './components/CorrelationCharts';
import {
  PRICE_CANDLES_DATA,
  SENTIMENT_CANDLES_DATA,
  METRICS_DATA,
  RECENT_NEWS,
} from './data/mockData';
import { DATASETS } from './data/weeklyData';
import { TrendingUp, Database, ShieldCheck, ChevronDown, Crosshair, X } from 'lucide-react';

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState('UCG.MI');
  const theme = 'light'; // solo tema chiaro
  const [selectedDate, setSelectedDate] = useState(null); // Data/periodo sincronizzato
  const [syncRange, setSyncRange] = useState(null); // Finestra temporale condivisa

  const priceChartContainerRef = useRef(null);
  const sentimentChartContainerRef = useRef(null);

  // Flag per disattivare temporaneamente Header e Sezione Dati senza eliminarli
  const SHOW_HEADER = false;
  const SHOW_TOP_METRICS = false;

  const tickersList = [
    // Per ora si lavora solo su Unicredit: gli altri titoli sono visibili ma non selezionabili
    { code: 'UCG.MI', name: 'Unicredit' },
    { code: 'ENI.MI', name: 'Eni S.p.A.', disabled: true },
    { code: 'ISP.MI', name: 'Intesa Sanpaolo', disabled: true },
    { code: 'RACE.MI', name: 'Ferrari N.V.', disabled: true },
    { code: 'ENEL.MI', name: 'Enel S.p.A.', disabled: true },
    { code: 'STLAM.MI', name: 'Stellantis N.V.', disabled: true },
  ];

  const activeInstrument =
    tickersList.find((t) => t.code === selectedTicker) || tickersList[0];

  const isDark = theme === 'dark';

  // Dettagli del punto correlato quando un periodo viene premuto
  const currentDataset = DATASETS[selectedTicker] || DATASETS['UCG.MI'];
  const dateIdx = selectedDate ? currentDataset.dates.indexOf(selectedDate) : -1;
  const selectedPointInfo =
    dateIdx !== -1
      ? {
          date: selectedDate,
          priceMean: currentDataset.price.mean[dateIdx],
          priceStd: currentDataset.price.std[dateIdx],
          volume: currentDataset.price.volume[dateIdx],
          sentimentMean: currentDataset.sentiment.mean[dateIdx],
          sentimentStd: currentDataset.sentiment.std[dateIdx],
          newsCount: currentDataset.sentiment.newsCount[dateIdx],
        }
      : null;

  return (
    <div
      className={`min-h-screen flex flex-col p-4 sm:p-6 transition-colors duration-200 ${
        isDark ? 'bg-[#070a12] text-slate-100' : 'bg-white text-[#111111]'
      }`}
    >
      {/* ==========================================================================
          HEADER DISATTIVATO TEMPORANEAMENTE (Imposta SHOW_HEADER = true per riattivarlo)
         ========================================================================== */}
      {SHOW_HEADER && (
        <header
          className={`mb-6 border rounded-xl backdrop-blur-md px-4 sm:px-6 py-3 ${
            isDark ? 'bg-dark-900/95 border-dark-700/80' : 'bg-white/95 border-slate-200 shadow-sm'
          }`}
        >
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight">
                  MilanoFinanza · Alpha Terminal
                </h1>
                <p className="text-[11px] text-slate-400">
                  Dashboard Dati, Momentum, Forza e Sentiment Analysis
                </p>
              </div>
            </div>
          </div>
        </header>
      )}

      {/* ==========================================================================
          SEZIONE METRICHE & NEWS DISATTIVATA TEMPORANEAMENTE (Imposta SHOW_TOP_METRICS = true per riattivarla)
         ========================================================================== */}
      {SHOW_TOP_METRICS && (
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
          <div className="lg:col-span-2">
            <TopMetrics metrics={METRICS_DATA} />
          </div>
          <div className="lg:col-span-1">
            <NewsPanel news={RECENT_NEWS} />
          </div>
        </section>
      )}

      {/* ==========================================================================
          I DUE GRAFICI AFFIANCATI CON CONTROLLI SULLA DESTRA E SINCRONIZZAZIONE
         ========================================================================== */}
      <main className="flex-1 w-full max-w-[1600px] mx-auto flex flex-col justify-start">
        {/* Barra superiore: Titolo e Menu Ticker a sinistra, Switch Tema a destra */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4 px-1">
          {/* Sinistra: Titolo in alto e Menu a Tendina Ticker posizionato direttamente al di sotto */}
          <div className="flex flex-col gap-2">
            <div className="flex flex-wrap items-center gap-3">
              <div>
                <p className="ed-title text-xs text-[#6b6b6b] mb-1">Milano Finanza</p>
                <h1 className="ed-title text-3xl sm:text-4xl">Fear &amp; Greed · Unicredit</h1>
                <p className="ed-sub mt-1">Cosa muove il titolo: prezzi e notizie, settimana per settimana.</p>
              </div>
            </div>

            {/* Menu a tendina Ticker posizionato sotto al titolo + Badge Ticker Attivo ben visibile */}
            <div className="flex flex-wrap items-center gap-3">
              {/* Menu a tendina per la selezione del Ticker */}
              <div className="relative inline-flex items-center">
                <select
                  value={selectedTicker}
                  onChange={(e) => {
                    const t = tickersList.find((x) => x.code === e.target.value);
                    if (!t || t.disabled) return; // titoli non ancora disponibili: nessuna azione
                    setSelectedTicker(t.code);
                    setSelectedDate(null);
                  }}
                  className={`appearance-none text-xs font-semibold pl-3 pr-8 py-1.5 rounded-full border transition-colors cursor-pointer outline-none ${
                    isDark
                      ? 'bg-dark-850 text-slate-100 border-dark-700 hover:border-slate-500 focus:border-trade-accent'
                      : 'bg-[#f0f0f0] text-[#111111] border-transparent hover:bg-[#e6e6e6]'
                  }`}
                >
                  {tickersList.map((t) => (
                    <option
                      key={t.code}
                      value={t.code}
                      disabled={t.disabled}
                      className={isDark ? 'bg-[#0b0f19] text-slate-100' : 'bg-white text-slate-900'}
                    >
                      {t.name} ({t.code}){t.disabled ? ' · presto' : ''}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  size={15}
                  className={`absolute right-2.5 pointer-events-none ${
                    isDark ? 'text-slate-400' : 'text-slate-500'
                  }`}
                />
              </div>
            </div>
          </div>

        </div>

        {/* Banner di Correlazione quando un periodo è cliccato/selezionato */}
        {selectedPointInfo && (
          <div
            className="mb-3 py-2.5 border-y border-[#111111] flex flex-wrap items-center justify-between gap-3 text-xs text-[#111111]"
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className="ed-title text-sm flex items-center gap-1.5">
                <Crosshair size={13} />
                <span>Settimana al {new Date(selectedPointInfo.date).toLocaleDateString('it-IT')}</span>
              </span>
              <span className="text-[#cfcfcf] hidden sm:inline">|</span>
              <span>
                <strong className="font-normal text-[#6b6b6b]">Prezzo:</strong> €{selectedPointInfo.priceMean.toFixed(2)} (±{selectedPointInfo.priceStd.toFixed(2)})
              </span>
              <span className="text-[#cfcfcf] hidden sm:inline">|</span>
              <span>
                <strong className="font-normal text-[#6b6b6b]">Sentiment:</strong>{' '}
                {selectedPointInfo.sentimentMean == null
                  ? 'n/d'
                  : `${selectedPointInfo.sentimentMean > 0 ? '+' : ''}${selectedPointInfo.sentimentMean.toFixed(2)} (±${selectedPointInfo.sentimentStd.toFixed(2)})`}
              </span>
              <span className="text-[#cfcfcf] hidden sm:inline">|</span>
              <span>
                <strong className="font-normal text-[#6b6b6b]">Notizie:</strong> {selectedPointInfo.newsCount}
              </span>
              <span className="text-[#cfcfcf] hidden sm:inline">|</span>
              <span>
                <strong className="font-normal text-[#6b6b6b]">Volumi:</strong> {(selectedPointInfo.volume / 1_000_000).toFixed(1)}M
              </span>
            </div>

            <button
              type="button"
              onClick={() => setSelectedDate(null)}
              className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-semibold bg-[#f0f0f0] text-[#111111] hover:bg-[#e6e6e6] transition-colors"
            >
              <X size={12} />
              <span>Chiudi</span>
            </button>
          </div>
        )}

        {/* Minicard con le notizie della settimana selezionata */}
        {selectedPointInfo && <WeekNewsCards week={selectedPointInfo.date} />}

        {/* Griglia 2 Colonne Simmetriche Affiancate con Sincronizzazione Attiva */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
          {/* Grafico 1: Prezzi (Media e Banda ±1σ Deviazione Standard) */}
          <div>
            <PriceCandleChart
              ticker={selectedTicker}
              instrumentName={activeInstrument.name}
              height={440}
              theme={theme}
              selectedDate={selectedDate}
              onSelectDate={(date) => setSelectedDate(date)}
              syncTargetRef={sentimentChartContainerRef}
              syncRange={syncRange}
              onRangeChange={(range) => setSyncRange(range)}
              chartContainerRef={priceChartContainerRef}
            />
          </div>

          {/* Grafico 2: Sentiment (Media e Banda ±1σ Deviazione Standard) */}
          <div>
            <SentimentCandleChart
              ticker={selectedTicker}
              instrumentName={activeInstrument.name}
              height={440}
              theme={theme}
              selectedDate={selectedDate}
              onSelectDate={(date) => setSelectedDate(date)}
              syncTargetRef={priceChartContainerRef}
              syncRange={syncRange}
              onRangeChange={(range) => setSyncRange(range)}
              chartContainerRef={sentimentChartContainerRef}
            />
          </div>
        </div>

        {/* Separatore tra i grafici principali e gli indicatori */}
        <hr className="ed-rule" />

        {/* Griglia 4 x 2: stessi indicatori per prezzi (sinistra) e notizie (destra) */}
        <IndicatorGrid
          ticker={selectedTicker}
          syncRange={syncRange}
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
        />

        {/* Separatore tra gli indicatori e le correlazioni */}
        <hr className="ed-rule" />

        {/* Correlazioni mobili a tutta larghezza */}
        <CorrelationCharts
          ticker={selectedTicker}
          syncRange={syncRange}
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
        />
      </main>
    </div>
  );
}
