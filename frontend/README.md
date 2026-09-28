# Milano Finanza · Alpha Terminal (React + Vite + Tailwind CSS)

Dashboard finanziaria modulare sviluppata per l'hackathon Milano Finanza (progetto BigQuery `class-hackaton-12`).

## 🧱 Architettura e Componenti (`src/components/`)

L'applicazione è strutturata in modo modulare con layout responsive a 2 sezioni (Tailwind CSS Grid & Flexbox):

1. **Sezione Superiore (Split 2/3 - 1/3)**:
   - [TopMetrics.jsx](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/components/TopMetrics.jsx): widget e tabelle per **Dati Chiave**, **Momentum** (RSI, MACD, ROC), **Forza** (Forza Relativa vs FTSE MIB, ADX, OBV) e **Incertezza** (Volatilità Storica, News Dispersion, VaR).
   - [NewsPanel.jsx](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/components/NewsPanel.jsx): rassegna stampa con filtri rapidi, timestamp, ticker associato, badge di sentiment score e livello di impatto.

2. **Sezione Inferiore (Simmetrica 1 col mobile / 2 col desktop)**:
   - [PriceCandleChart.jsx](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/components/PriceCandleChart.jsx): grafico a candele OHLC per i prezzi con istogramma dei volumi in overlay, basato su **TradingView Lightweight Charts v5**.
   - [SentimentCandleChart.jsx](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/components/SentimentCandleChart.jsx): grafico a candele e barre per l'analisi temporale dell'escursione del sentiment derivato dai testi e dagli embeddings delle notizie.

## 📦 Dati Mock e Schemi BigQuery (`src/data/mockData.js`)

Tutti i dati mock sono archiviati in locale in [mockData.js](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/data/mockData.js) e riflettono fedelmente le tabelle BigQuery:
- `financial_instruments.instruments_quotes`: partizionata su `DATA_QUOTAZ` (open, high, low, close, volume).
- `news.articles`: partizionata su `data_modifica` (titolo, sommario, sentiment NLP).

## 🚀 Avvio Locale

```bash
cd frontend
npm run dev
```

L'applicazione sarà disponibile su `http://localhost:5173`.

## ☁️ Deploy su Vercel

Configurato tramite [vercel.json](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/vercel.json):
- Build command: `npm run build`
- Output directory: `dist`
