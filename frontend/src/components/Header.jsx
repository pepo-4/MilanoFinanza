import React from 'react';
import { TrendingUp, Database, Sparkles } from 'lucide-react';

export default function Header({ selectedTicker, onSelectTicker, instruments }) {
  return (
    <header className="app-header">
      <div className="header-brand">
        <div className="brand-logo">
          <TrendingUp className="icon-logo" size={24} />
        </div>
        <div>
          <h1 className="brand-title">MilanoFinanza · Hub Dati</h1>
          <p className="brand-subtitle">Analytics & Sentiment Engine (Dati Locali)</p>
        </div>
      </div>

      <div className="header-actions">
        <div className="mode-badge">
          <Database size={14} />
          <span>BigQuery Local Cache</span>
        </div>

        <div className="ticker-tabs">
          {instruments.map((inst) => (
            <button
              key={inst.ticker}
              type="button"
              className={`ticker-tab-btn ${selectedTicker === inst.ticker ? 'active' : ''}`}
              onClick={() => onSelectTicker(inst.ticker)}
            >
              <span className="ticker-tab-code">{inst.ticker.replace('.MI', '')}</span>
              <span className={`ticker-tab-delta ${inst.changePercent >= 0 ? 'pos' : 'neg'}`}>
                {inst.changePercent >= 0 ? '+' : ''}{inst.changePercent}%
              </span>
            </button>
          ))}
        </div>
      </div>
    </header>
  );
}
