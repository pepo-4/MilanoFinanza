import React, { useState } from 'react';
import { Newspaper, ExternalLink, Filter, Sparkles, Clock, Tag } from 'lucide-react';

export default function NewsPanel({ news }) {
  const [filter, setFilter] = useState('ALL');

  const filteredNews = news.filter((item) => {
    if (filter === 'ALL') return true;
    if (filter === 'POS') return item.sentiment === 'positivo';
    if (filter === 'NEU') return item.sentiment === 'neutro';
    if (filter === 'NEG') return item.sentiment === 'negativo';
    return true;
  });

  return (
    <div className="bg-dark-800/90 border border-dark-700/80 rounded-xl p-4 flex flex-col h-full shadow-lg backdrop-blur-sm">
      {/* Header News Panel */}
      <div className="flex items-center justify-between pb-3 border-b border-dark-700/60 mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-dark-900/80 border border-dark-700/50">
            <Newspaper size={16} className="text-trade-accent" />
          </div>
          <div>
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
              News Stream & Rassegna
            </h3>
            <p className="text-[10px] text-slate-400 font-mono">Milano Finanza Live Feed</p>
          </div>
        </div>

        {/* Filtri veloci */}
        <div className="flex items-center gap-1 bg-dark-900 p-1 rounded-lg border border-dark-700/60">
          {['ALL', 'POS', 'NEU'].map((f) => (
            <button
              key={f}
              type="button"
              onClick={() => setFilter(f)}
              className={`px-2 py-0.5 text-[10px] font-mono font-semibold rounded ${
                filter === f
                  ? 'bg-dark-700 text-trade-accent shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Lista Notizie con Scroll Elegante */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1 max-h-[360px] custom-scrollbar">
        {filteredNews.map((article) => {
          const isPos = article.sentiment === 'positivo';
          const isNeg = article.sentiment === 'negativo';

          return (
            <article
              key={article.id}
              className="p-3 rounded-lg bg-dark-900/60 border border-dark-750 hover:border-dark-600 transition-all group"
            >
              <div className="flex items-center justify-between text-[11px] mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-slate-400 flex items-center gap-1">
                    <Clock size={11} className="text-slate-500" />
                    {article.time}
                  </span>
                  <span className="px-1.5 py-0.5 rounded bg-dark-800 text-[10px] font-mono font-bold text-trade-accent border border-dark-700">
                    {article.ticker}
                  </span>
                </div>

                {/* Badge Sentiment */}
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                    isPos
                      ? 'bg-trade-up-bg text-trade-up border-emerald-500/30'
                      : isNeg
                      ? 'bg-trade-down-bg text-trade-down border-rose-500/30'
                      : 'bg-dark-800 text-slate-300 border-slate-700'
                  }`}
                >
                  {article.score}
                </span>
              </div>

              <h4 className="text-xs font-semibold text-slate-100 group-hover:text-trade-accent transition-colors leading-snug mb-1">
                {article.title}
              </h4>

              <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">
                {article.summary}
              </p>

              <div className="flex items-center justify-between mt-2 pt-2 border-t border-dark-800/80 text-[10px] text-slate-500">
                <span className="flex items-center gap-1">
                  <Tag size={10} />
                  {article.source}
                </span>
                <span className="font-mono">Impatto: {article.impact}</span>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
