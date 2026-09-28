import React from 'react';
import { ExternalLink } from 'lucide-react';
import { NEWS_BY_WEEK } from '../data/newsByWeek';
import { RATING_STYLES, INK } from '../theme';

// Colore dello score, come i riquadri Fear & Greed: positivo / negativo / neutro (|score| <= 0.2)
function scoreStyle(score) {
  const r = RATING_STYLES[score > 0.2 ? 'Greed' : score < -0.2 ? 'Fear' : 'Neutral'];
  return { background: r.bg, borderColor: r.border, color: INK };
}

// Minicard con le notizie (con score) della settimana selezionata
export default function WeekNewsCards({ week }) {
  const entry = NEWS_BY_WEEK[week];
  const news = entry?.news || [];

  return (
    <div className="mb-4">
      <div className="flex items-baseline gap-2 mb-2">
        <h3 className="ed-title text-sm">Notizie della settimana</h3>
        <span className="ed-sub">{news.length}</span>
      </div>

      {news.length === 0 ? (
        <p className="ed-sub">Nessuna notizia in questa settimana.</p>
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {news.map((n) => (
            <a
              key={n.url || n.title}
              href={n.url}
              target="_blank"
              rel="noopener noreferrer"
              title={n.title}
              className="group shrink-0 w-64 flex flex-col justify-between gap-2 p-3 border-t-2 border-[#111111] bg-white hover:bg-[#f7f7f7] transition-colors duration-200"
            >
              <p className="text-[13px] font-semibold text-[#111111] leading-snug line-clamp-2 group-hover:underline">{n.title}</p>
              <div className="flex items-center justify-between">
                <span className="ed-rating" style={scoreStyle(n.score)}>
                  {n.score > 0 ? '+' : ''}
                  {n.score.toFixed(2)}
                </span>
                <span className="flex items-center gap-1 text-[11px] text-[#8a8a8a]">
                  {n.time}
                  <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </span>
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
