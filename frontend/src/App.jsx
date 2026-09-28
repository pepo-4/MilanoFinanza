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
  // Settimana evidenziata all'apertura (venerdì di fine settimana); null = nessuna
  const DEFAULT_WEEK = '2026-03-20';
  const [selectedDate, setSelectedDate] = useState(DEFAULT_WEEK); // Data/periodo sincronizzato
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
        {/* Barra superiore: titolo a sinistra, selettore del titolo a destra */}
        <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4 mb-6 px-1">
          <div>
            <p className="ed-title text-xs text-[#6b6b6b] mb-1">Milano Finanza</p>
            <h1 className="ed-title text-3xl sm:text-4xl">Fear &amp; Greed · Unicredit</h1>
          </div>

          {/* Menu a tendina per la selezione del titolo */}
          <div className="relative inline-flex items-center">
            <label htmlFor="ticker-select" className="sr-only">Titolo</label>
            <select
              id="ticker-select"
              value={selectedTicker}
              onChange={(e) => {
                const t = tickersList.find((x) => x.code === e.target.value);
                if (!t || t.disabled) return; // titoli non ancora disponibili: nessuna azione
                setSelectedTicker(t.code);
                setSelectedDate(null);
              }}
              className="ed-title appearance-none text-xl pl-6 pr-14 py-3 min-w-[320px] rounded-full border border-transparent bg-[#f0f0f0] text-[#111111] hover:bg-[#e6e6e6] transition-colors cursor-pointer outline-none focus:border-[#111111]"
            >
              {tickersList.map((t) => (
                <option key={t.code} value={t.code} disabled={t.disabled} className="bg-white text-slate-900">
                  {t.name} ({t.code}){t.disabled ? ' · presto' : ''}
                </option>
              ))}
            </select>
            <ChevronDown size={22} className="absolute right-5 pointer-events-none text-[#111111]" />
          </div>
        </div>

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

        {/* Settimana selezionata: riepilogo e notizie, sotto i grafici, su fondo chiaro */}
        {selectedPointInfo && (
          <div className="mt-6 px-5 py-4 bg-[#f5f5f2] rounded-lg">
            <div className="pb-3 mb-4 border-b border-[#d9d9d4] flex flex-wrap items-center justify-between gap-3 text-xs text-[#111111]">
              <div className="flex flex-wrap items-center gap-3">
                <span className="ed-title text-sm flex items-center gap-1.5">
                  <Crosshair size={13} />
                  <span>Settimana al {new Date(selectedPointInfo.date).toLocaleDateString('it-IT')}</span>
                </span>
                <span className="text-[#cfcfcf] hidden sm:inline">|</span>
                <span>
                  <strong className="font-normal text-[#6b6b6b]">Prezzo:</strong> €{selectedPointInfo.priceMean.toFixed(2)}
                </span>
                <span className="text-[#cfcfcf] hidden sm:inline">|</span>
                <span>
                  <strong className="font-normal text-[#6b6b6b]">Sentiment:</strong>{' '}
                  {selectedPointInfo.sentimentMean == null
                    ? 'n/d'
                    : `${selectedPointInfo.sentimentMean > 0 ? '+' : ''}${selectedPointInfo.sentimentMean.toFixed(2)}`}
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
                className="flex items-center gap-1 px-3 py-1 rounded-full text-[11px] font-semibold bg-white text-[#111111] hover:bg-[#e6e6e6] transition-colors"
              >
                <X size={12} />
                <span>Chiudi</span>
              </button>
            </div>

            {/* Minicard con le notizie della settimana selezionata */}
            <WeekNewsCards week={selectedPointInfo.date} />
          </div>
        )}

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
