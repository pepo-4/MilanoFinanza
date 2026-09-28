import React from 'react';
import { ArrowUpRight, ArrowDownRight, Layers, ShieldCheck, Terminal } from 'lucide-react';

export default function MarketStats({ marketSummary, instruments, onSelectTicker, selectedTicker }) {
  return (
    <div className="market-stats-card">
      <div className="stats-box">
        <h3 className="stats-box-title">Panoramica Mercato MF</h3>
        <div className="stats-list">
          <div className="stat-row">
            <span>Miglior Titolo</span>
            <button
              type="button"
              className="stat-link-btn text-positive"
              onClick={() => onSelectTicker(marketSummary.topGainer.ticker)}
            >
              {marketSummary.topGainer.name} (+{marketSummary.topGainer.changePercent}%)
            </button>
          </div>
          <div className="stat-row">
            <span>Maggior Ribasso</span>
            <button
              type="button"
              className="stat-link-btn text-negative"
              onClick={() => onSelectTicker(marketSummary.topLoser.ticker)}
            >
              {marketSummary.topLoser.name} ({marketSummary.topLoser.changePercent}%)
            </button>
          </div>
          <div className="stat-row">
            <span>Sentiment Medio</span>
            <span className="stat-val font-semibold">
              {marketSummary.averageSentiment > 0 ? '+' : ''}
              {marketSummary.averageSentiment}
            </span>
          </div>
          <div className="stat-row">
            <span>Ultimo Aggiornamento</span>
            <span className="stat-val text-muted">{marketSummary.lastUpdated}</span>
          </div>
        </div>
      </div>

      <div className="stats-box">
        <h3 className="stats-box-title">Strumenti Monitorati</h3>
        <div className="instruments-quick-list">
          {instruments.map((inst) => {
            const isSelected = inst.ticker === selectedTicker;
            const isPos = inst.changePercent >= 0;
            return (
              <div
                key={inst.ticker}
                className={`inst-item ${isSelected ? 'active' : ''}`}
                onClick={() => onSelectTicker(inst.ticker)}
              >
                <div className="inst-info">
                  <span className="inst-ticker">{inst.ticker}</span>
                  <span className="inst-name">{inst.name}</span>
                </div>
                <div className="inst-values">
                  <span className="inst-price">€{inst.currentPrice.toFixed(2)}</span>
                  <span className={`inst-delta ${isPos ? 'pos' : 'neg'}`}>
                    {isPos ? '+' : ''}{inst.changePercent}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="stats-box compliance-box">
        <div className="compliance-header">
          <ShieldCheck size={16} className="text-emerald" />
          <span>Regole GEMINI.md attive</span>
        </div>
        <p className="compliance-text">
          Dry Run &lt; 1 GB • Nessuna query diretta da browser • Dataset <code>class-hackaton-12</code>
        </p>
      </div>
    </div>
  );
}
