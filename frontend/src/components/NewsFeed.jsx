import React, { useState } from 'react';
import { Newspaper, Calendar, Tag, ChevronDown, ChevronUp, Search, ThumbsUp, ThumbsDown, Minus } from 'lucide-react';

export default function NewsFeed({ news, selectedTicker }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedId, setExpandedId] = useState(null);

  const filteredNews = news.filter((item) => {
    const matchesTicker = !selectedTicker || item.ticker === selectedTicker;
    const matchesSearch =
      item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.category.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesTicker && matchesSearch;
  });

  const toggleExpand = (id) => {
    setExpandedId((prev) => (prev === id ? null : id));
  };

  const renderSentimentBadge = (sentiment, score) => {
    if (sentiment === 'positivo') {
      return (
        <span className="news-badge badge-pos">
          <ThumbsUp size={12} />
          <span>Positivo (+{score.toFixed(2)})</span>
        </span>
      );
    }
    if (sentiment === 'negativo') {
      return (
        <span className="news-badge badge-neg">
          <ThumbsDown size={12} />
          <span>Negativo ({score.toFixed(2)})</span>
        </span>
      );
    }
    return (
      <span className="news-badge badge-neutral">
        <Minus size={12} />
        <span>Neutro ({score.toFixed(2)})</span>
      </span>
    );
  };

  return (
    <div className="news-section-card">
      <div className="news-header">
        <div className="news-title-group">
          <div className="news-title-row">
            <Newspaper size={20} className="news-icon-primary" />
            <h2 className="news-section-title">Rassegna Notizie & Sentiment</h2>
          </div>
          <p className="news-section-subtitle">
            Notizie estratte da <code>news.articles</code> (filtro partizione: <code>data_modifica</code>)
          </p>
        </div>

        <div className="news-search-box">
          <Search size={15} className="search-icon" />
          <input
            type="text"
            placeholder="Cerca nelle notizie o categorie..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
        </div>
      </div>

      <div className="news-list">
        {filteredNews.length === 0 ? (
          <div className="empty-news">
            <p>Nessun articolo trovato con i filtri correnti.</p>
          </div>
        ) : (
          filteredNews.map((article) => {
            const isExpanded = expandedId === article.id;
            const formattedDate = new Date(article.data_modifica).toLocaleString('it-IT', {
              day: '2-digit',
              month: 'short',
              hour: '2-digit',
              minute: '2-digit',
            });

            return (
              <div key={article.id} className="news-item">
                <div className="news-meta">
                  <div className="news-meta-left">
                    <span className="news-category">
                      <Tag size={12} />
                      {article.category}
                    </span>
                    <span className="news-ticker-tag">{article.ticker}</span>
                    <span className="news-date">
                      <Calendar size={12} />
                      {formattedDate}
                    </span>
                  </div>
                  <div>{renderSentimentBadge(article.sentiment, article.sentimentScore)}</div>
                </div>

                <h3 className="news-item-title">{article.title}</h3>
                <p className="news-item-summary">{article.summary}</p>

                {isExpanded && (
                  <div className="news-item-body">
                    <p>{article.body}</p>
                    <span className="news-author">Fonte: {article.author}</span>
                  </div>
                )}

                <button
                  type="button"
                  className="news-expand-btn"
                  onClick={() => toggleExpand(article.id)}
                >
                  <span>{isExpanded ? 'Comprimi articolo' : 'Leggi corpo completo'}</span>
                  {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
