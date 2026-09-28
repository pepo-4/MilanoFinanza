import React, { useState, useRef } from 'react';
// Componenti modulari (disattivati temporaneamente via flag, pronti per essere riattivati)
import TopMetrics from './components/TopMetrics';
import NewsPanel from './components/NewsPanel';
import PriceCandleChart from './components/PriceCandleChart';
import SentimentCandleChart from './components/SentimentCandleChart';
import {
  PRICE_CANDLES_DATA,
  SENTIMENT_CANDLES_DATA,
  METRICS_DATA,
  RECENT_NEWS,
} from './data/mockData';
import { DATASETS } from './data/weeklyData';
import { TrendingUp, Database, ShieldCheck, Sun, Moon, ChevronDown, Crosshair, X } from 'lucide-react';

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState('UCG.MI');
  const [theme, setTheme] = useState('dark'); // 'dark' | 'light'
  const [selectedDate, setSelectedDate] = useState(null); // Data/periodo sincronizzato
  const [syncRange, setSyncRange] = useState(null); // Finestra temporale condivisa

  const priceChartContainerRef = useRef(null);
  const sentimentChartContainerRef = useRef(null);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'));
  };

  // Flag per disattivare temporaneamente Header e Sezione Dati senza eliminarli
  const SHOW_HEADER = false;
  const SHOW_TOP_METRICS = false;

  const tickersList = [
    { code: 'UCG.MI', name: 'Unicredit', delta: '+1.85%', isUp: true },
    { code: 'ENI.MI', name: 'Eni S.p.A.', delta: '+1.65%', isUp: true },
    { code: 'ISP.MI', name: 'Intesa Sanpaolo', delta: '+0.48%', isUp: true },
    { code: 'RACE.MI', name: 'Ferrari N.V.', delta: '-0.84%', isUp: false },
    { code: 'ENEL.MI', name: 'Enel S.p.A.', delta: '+2.12%', isUp: true },
    { code: 'STLAM.MI', name: 'Stellantis N.V.', delta: '-1.95%', isUp: false },
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
        isDark ? 'bg-[#070a12] text-slate-100' : 'bg-[#f8fafc] text-slate-800'
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
      <main className="flex-1 w-full max-w-[1780px] mx-auto flex flex-col justify-center">
        {/* Barra superiore: Titolo a sinistra, Menu a tendina e Switch Tema a destra */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 px-1">
          {/* Sinistra: Titolo del confronto e nome strumento attivo */}
          <div className="flex items-center gap-2">
            <span
              className={`font-mono text-xs font-bold uppercase tracking-wider ${
                isDark ? 'text-slate-300' : 'text-slate-800'
              }`}
            >
              Chart Comparison · Milano Finanza
            </span>
            <span className="text-xs font-mono text-slate-500">
              ({activeInstrument.name})
            </span>
            {selectedDate && (
              <span className="hidden md:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono rounded bg-trade-accent/10 text-trade-accent border border-trade-accent/30">
                <Crosshair size={11} /> Cursore sincronizzato
              </span>
            )}
          </div>

          {/* Destra: Menu a tendina del ticker + Switch Light/Dark Mode */}
          <div className="flex items-center gap-2.5">
            {/* Menu a tendina per la selezione del Ticker */}
            <div className="relative inline-flex items-center">
              <select
                value={selectedTicker}
                onChange={(e) => {
                  setSelectedTicker(e.target.value);
                  setSelectedDate(null);
                }}
                className={`appearance-none text-xs font-mono font-medium pl-3 pr-8 py-1.5 rounded-lg border transition-all cursor-pointer outline-none ${
                  isDark
                    ? 'bg-dark-850 text-slate-200 border-dark-700 hover:border-dark-600 focus:border-trade-accent'
                    : 'bg-white text-slate-800 border-slate-300 hover:border-slate-400 focus:border-blue-500 shadow-sm'
                }`}
              >
                {tickersList.map((t) => (
                  <option
                    key={t.code}
                    value={t.code}
                    className={isDark ? 'bg-[#0b0f19] text-slate-200' : 'bg-white text-slate-800'}
                  >
                    {t.name} ({t.code}) {t.delta}
                  </option>
                ))}
              </select>
              <ChevronDown
                size={14}
                className={`absolute right-2.5 pointer-events-none ${
                  isDark ? 'text-slate-400' : 'text-slate-500'
                }`}
              />
            </div>

            {/* Toggle Switch Light / Dark Mode */}
            <button
              type="button"
              onClick={toggleTheme}
              title={isDark ? 'Attiva Tema Chiaro' : 'Attiva Tema Scuro'}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium border transition-all ${
                isDark
                  ? 'bg-dark-850 text-amber-400 border-dark-700 hover:bg-dark-750 hover:border-dark-600'
                  : 'bg-white text-indigo-600 border-slate-300 hover:bg-slate-50 hover:border-slate-400 shadow-sm'
              }`}
            >
              {isDark ? (
                <>
                  <Sun size={14} className="text-amber-400" />
                  <span className="text-slate-300 text-[11px]">Light</span>
                </>
              ) : (
                <>
                  <Moon size={14} className="text-indigo-600" />
                  <span className="text-slate-700 text-[11px]">Dark</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Banner di Correlazione quando un periodo è cliccato/selezionato */}
        {selectedPointInfo && (
          <div
            className={`mb-3.5 px-3.5 py-2 rounded-xl border flex flex-wrap items-center justify-between gap-3 text-xs font-mono transition-all animate-fadeIn ${
              isDark
                ? 'bg-dark-850/95 border-trade-accent/40 text-slate-200 shadow-lg shadow-black/40'
                : 'bg-blue-50/90 border-blue-200 text-blue-950 shadow-sm'
            }`}
          >
            <div className="flex flex-wrap items-center gap-3">
              <span className="font-bold flex items-center gap-1.5 text-trade-accent">
                <Crosshair size={13} />
                <span>Periodo: Settimana al {new Date(selectedPointInfo.date).toLocaleDateString('it-IT')}</span>
              </span>
              <span className="text-slate-400 hidden sm:inline">|</span>
              <span>
                <strong className={isDark ? 'text-slate-300' : 'text-slate-700'}>Prezzo:</strong> €{selectedPointInfo.priceMean.toFixed(2)} (±{selectedPointInfo.priceStd.toFixed(2)})
              </span>
              <span className="text-slate-400 hidden sm:inline">|</span>
              <span>
                <strong className={isDark ? 'text-slate-300' : 'text-slate-700'}>Sentiment:</strong> {selectedPointInfo.sentimentMean > 0 ? '+' : ''}{selectedPointInfo.sentimentMean.toFixed(2)} (±{selectedPointInfo.sentimentStd.toFixed(2)})
              </span>
              <span className="text-slate-400 hidden sm:inline">|</span>
              <span>
                <strong className={isDark ? 'text-slate-300' : 'text-slate-700'}>Notizie:</strong> {selectedPointInfo.newsCount}
              </span>
              <span className="text-slate-400 hidden sm:inline">|</span>
              <span>
                <strong className={isDark ? 'text-slate-300' : 'text-slate-700'}>Volumi:</strong> {(selectedPointInfo.volume / 1_000_000).toFixed(1)}M
              </span>
            </div>

            <button
              type="button"
              onClick={() => setSelectedDate(null)}
              className={`flex items-center gap-1 px-2.5 py-1 rounded-md text-[11px] font-semibold border transition-all ${
                isDark
                  ? 'bg-dark-750 text-slate-300 border-dark-600 hover:text-white hover:border-trade-accent'
                  : 'bg-white text-slate-600 border-slate-300 hover:text-slate-900 shadow-sm'
              }`}
            >
              <X size={12} />
              <span>Rimuovi cursore</span>
            </button>
          </div>
        )}

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
      </main>
    </div>
  );
}
