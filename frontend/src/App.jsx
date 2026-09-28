import React, { useState } from 'react';
// Componenti conservati (disattivati temporaneamente come richiesto, pronti per essere riattivati)
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
import { TrendingUp, Database, ShieldCheck } from 'lucide-react';

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState('UCG.MI');

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

  return (
    <div className="min-h-screen bg-[#070a12] text-slate-100 flex flex-col p-4 sm:p-6 selection:bg-trade-accent selection:text-black">
      {/* ==========================================================================
          HEADER DISATTIVATO TEMPORANEAMENTE (Imposta SHOW_HEADER = true per riattivarlo)
         ========================================================================== */}
      {SHOW_HEADER && (
        <header className="mb-6 bg-dark-900/95 border border-dark-700/80 rounded-xl backdrop-blur-md px-4 sm:px-6 py-3">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <TrendingUp size={20} className="text-white" />
              </div>
              <div>
                <h1 className="text-base font-bold tracking-tight text-white">
                  MilanoFinanza · Alpha Terminal
                </h1>
                <p className="text-[11px] text-slate-400">
                  Dashboard Dati, Momentum, Forza e Sentiment Analysis
                </p>
              </div>
            </div>

            <div className="flex items-center gap-1.5 bg-dark-850 p-1 rounded-xl border border-dark-700 overflow-x-auto max-w-full">
              {tickersList.map((t) => (
                <button
                  key={t.code}
                  type="button"
                  onClick={() => setSelectedTicker(t.code)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all ${
                    selectedTicker === t.code
                      ? 'bg-dark-700 text-white border border-dark-600 shadow-md shadow-black/40'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-dark-800'
                  }`}
                >
                  <span>{t.code.replace('.MI', '')}</span>
                  <span
                    className={`text-[10px] font-bold ${
                      t.isUp ? 'text-trade-up' : 'text-trade-down'
                    }`}
                  >
                    {t.delta}
                  </span>
                </button>
              ))}
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
          I DUE GRAFICI AFFIANCATI (PriceCandleChart a sinistra, SentimentCandleChart a destra)
         ========================================================================== */}
      <main className="flex-1 w-full max-w-[1780px] mx-auto flex flex-col justify-center">
        {/* Barra compatta per il cambio rapido del titolo */}
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 px-1">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold uppercase tracking-wider text-slate-300">
              Chart Comparison · Milano Finanza
            </span>
            <span className="text-xs font-mono text-slate-500">
              ({activeInstrument.name})
            </span>
          </div>

          <div className="flex items-center gap-1 bg-dark-850 p-1 rounded-lg border border-dark-700">
            {tickersList.map((t) => (
              <button
                key={t.code}
                type="button"
                onClick={() => setSelectedTicker(t.code)}
                className={`px-2.5 py-1 rounded text-xs font-mono font-medium transition-all ${
                  selectedTicker === t.code
                    ? 'bg-dark-700 text-trade-accent shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.code.replace('.MI', '')}
              </button>
            ))}
          </div>
        </div>

        {/* Griglia 2 Colonne Simmetriche Affiancate */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full">
          {/* Grafico 1: Prezzi (Media e Banda ±1σ Deviazione Standard) */}
          <div>
            <PriceCandleChart
              ticker={selectedTicker}
              instrumentName={activeInstrument.name}
              height={440}
            />
          </div>

          {/* Grafico 2: Sentiment (Media e Banda ±1σ Deviazione Standard) */}
          <div>
            <SentimentCandleChart
              ticker={selectedTicker}
              instrumentName={activeInstrument.name}
              height={440}
            />
          </div>
        </div>
      </main>
    </div>
  );
}
