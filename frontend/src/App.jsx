import React, { useState } from 'react';
import Header from './components/Header';
import KPICards from './components/KPICards';
import PriceChart from './components/PriceChart';
import NewsFeed from './components/NewsFeed';
import MarketStats from './components/MarketStats';
import {
  INSTRUMENTS,
  QUOTES_SERIES,
  LOCAL_NEWS,
  MARKET_SUMMARY,
} from './data/localData';
import './App.css';

export default function App() {
  const [selectedTicker, setSelectedTicker] = useState('ENI.MI');

  // Find the selected instrument
  const activeInstrument =
    INSTRUMENTS.find((inst) => inst.ticker === selectedTicker) || INSTRUMENTS[0];

  // Quotes for the selected instrument
  const currentQuotes = QUOTES_SERIES[selectedTicker] || [];

  // Filtered news count for the active instrument
  const relatedNewsCount = LOCAL_NEWS.filter(
    (n) => n.ticker === selectedTicker
  ).length;

  return (
    <div className="app-container">
      <Header
        selectedTicker={selectedTicker}
        onSelectTicker={setSelectedTicker}
        instruments={INSTRUMENTS}
      />

      <main className="app-main">
        {/* KPI Cards Row */}
        <section className="section-kpis">
          <KPICards
            instrument={activeInstrument}
            newsCount={relatedNewsCount}
          />
        </section>

        {/* Dashboard Center Grid: Chart on Left, Market Stats on Right */}
        <div className="dashboard-grid">
          <div className="dashboard-left">
            <PriceChart
              quotes={currentQuotes}
              ticker={activeInstrument.ticker}
              instrumentName={activeInstrument.name}
            />

            <NewsFeed
              news={LOCAL_NEWS}
              selectedTicker={selectedTicker}
            />
          </div>

          <aside className="dashboard-right">
            <MarketStats
              marketSummary={MARKET_SUMMARY}
              instruments={INSTRUMENTS}
              selectedTicker={selectedTicker}
              onSelectTicker={setSelectedTicker}
            />
          </aside>
        </div>
      </main>

      <footer className="app-footer">
        <div>
          <span>Milano Finanza Hackathon 2024 • Progetto <code>class-hackaton-12</code></span>
        </div>
        <div className="footer-links">
          <span>React 18 + Vite</span>
          <span>•</span>
          <span>Pronto per Vercel</span>
          <span>•</span>
          <span>Architettura Dati Locali</span>
        </div>
      </footer>
    </div>
  );
}
