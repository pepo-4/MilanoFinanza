import React from 'react';
import { ArrowUpRight, ArrowDownRight, Activity, BarChart3, Newspaper, MessageSquare } from 'lucide-react';

export default function KPICards({ instrument, newsCount }) {
  const isPositive = instrument.changePercent >= 0;

  // Sentiment label and color
  let sentimentLabel = 'Neutro';
  let sentimentClass = 'neutral';
  if (instrument.sentimentScore > 0.3) {
    sentimentLabel = 'Bullish / Positivo';
    sentimentClass = 'positive';
  } else if (instrument.sentimentScore < -0.3) {
    sentimentLabel = 'Bearish / Negativo';
    sentimentClass = 'negative';
  }

  return (
    <div className="kpi-grid">
      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-label">Ultimo Prezzo</span>
          <span className="kpi-icon-wrapper">
            <Activity size={18} />
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">€{instrument.currentPrice.toFixed(2)}</span>
          <span className={`kpi-badge ${isPositive ? 'positive' : 'negative'}`}>
            {isPositive ? <ArrowUpRight size={15} /> : <ArrowDownRight size={15} />}
            {isPositive ? '+' : ''}{instrument.changePercent}%
          </span>
        </div>
        <div className="kpi-subtext">Settore: {instrument.sector}</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-label">Volume Scambiato (24h)</span>
          <span className="kpi-icon-wrapper">
            <BarChart3 size={18} />
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">
            {(instrument.volume24h / 1_000_000).toFixed(2)}M
          </span>
          <span className="kpi-sub-pill">Azioni</span>
        </div>
        <div className="kpi-subtext">Mercato: {instrument.market}</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-label">Sentiment Rassegna Stampa</span>
          <span className="kpi-icon-wrapper">
            <MessageSquare size={18} />
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">
            {instrument.sentimentScore > 0 ? '+' : ''}{instrument.sentimentScore.toFixed(2)}
          </span>
          <span className={`kpi-badge ${sentimentClass}`}>{sentimentLabel}</span>
        </div>
        <div className="kpi-subtext">Score NLP da embeddings e news</div>
      </div>

      <div className="kpi-card">
        <div className="kpi-top">
          <span className="kpi-label">Notizie Collegate</span>
          <span className="kpi-icon-wrapper">
            <Newspaper size={18} />
          </span>
        </div>
        <div className="kpi-value-row">
          <span className="kpi-main-value">{newsCount}</span>
          <span className="kpi-sub-pill">Articoli</span>
        </div>
        <div className="kpi-subtext">ISIN: {instrument.isin}</div>
      </div>
    </div>
  );
}
