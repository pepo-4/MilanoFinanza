import React, { useState } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
} from 'recharts';
import { Calendar, Maximize2, LineChart as ChartIcon } from 'lucide-react';

function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="custom-tooltip">
        <p className="tooltip-date">{label}</p>
        <div className="tooltip-row">
          <span>Chiusura:</span>
          <strong>€{data.close?.toFixed(2)}</strong>
        </div>
        <div className="tooltip-row">
          <span>Max / Min:</span>
          <span>€{data.high?.toFixed(2)} / €{data.low?.toFixed(2)}</span>
        </div>
        <div className="tooltip-row">
          <span>Volume:</span>
          <span>{(data.volume / 1000000).toFixed(2)}M</span>
        </div>
      </div>
    );
  }
  return null;
}

export default function PriceChart({ quotes, ticker, instrumentName }) {
  const [viewMode, setViewMode] = useState('price'); // 'price' | 'volume'

  const minPrice = Math.min(...quotes.map((q) => q.low)) * 0.98;
  const maxPrice = Math.max(...quotes.map((q) => q.high)) * 1.02;

  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">
            {instrumentName} ({ticker})
          </h2>
          <p className="chart-subtitle">
            Serie temporale da <code>financial_instruments.instruments_quotes</code>
          </p>
        </div>

        <div className="chart-controls">
          <div className="btn-group">
            <button
              type="button"
              className={`btn-toggle ${viewMode === 'price' ? 'active' : ''}`}
              onClick={() => setViewMode('price')}
            >
              Prezzo (€)
            </button>
            <button
              type="button"
              className={`btn-toggle ${viewMode === 'volume' ? 'active' : ''}`}
              onClick={() => setViewMode('volume')}
            >
              Volumi
            </button>
          </div>
        </div>
      </div>

      <div className="chart-body">
        <ResponsiveContainer width="100%" height={320}>
          {viewMode === 'price' ? (
            <AreaChart data={quotes} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#38bdf8" stopOpacity={0.35} />
                  <stop offset="95%" stopColor="#38bdf8" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#262b3d" vertical={false} />
              <XAxis
                dataKey="DATA_QUOTAZ"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                domain={[minPrice, maxPrice]}
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                tickFormatter={(val) => `€${val.toFixed(2)}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="close"
                stroke="#38bdf8"
                strokeWidth={2.5}
                fillOpacity={1}
                fill="url(#priceGradient)"
              />
            </AreaChart>
          ) : (
            <BarChart data={quotes} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#262b3d" vertical={false} />
              <XAxis
                dataKey="DATA_QUOTAZ"
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                stroke="#64748b"
                fontSize={12}
                tickLine={false}
                tickFormatter={(val) => `${(val / 1000000).toFixed(0)}M`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar dataKey="volume" fill="#818cf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>

      <div className="chart-footer">
        <div className="chart-legend-item">
          <span className="dot dot-cyan"></span>
          <span>Prezzo di Chiusura</span>
        </div>
        <div className="chart-legend-item">
          <span className="dot dot-indigo"></span>
          <span>Volumi Scambiati</span>
        </div>
        <div className="chart-note">
          <Calendar size={13} />
          <span>Partizione temporale giornaliera</span>
        </div>
      </div>
    </div>
  );
}
