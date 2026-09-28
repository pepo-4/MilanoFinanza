# Milano Finanza · Dashboard Frontend (React + Vite)

Frontend web sviluppato per l'hackathon Milano Finanza (progetto `class-hackaton-12`).
Progettato per visualizzare serie storiche di quotazioni, feed notizie con sentiment analysis e metriche calcolate su dati locali.

## 🚀 Avvio Rapido

```bash
cd frontend
npm run dev
```

L'applicazione sarà visibile su `http://localhost:5173`.

## 📦 Struttura dei Dati Locali

Tutti i dati visualizzati provengono da [src/data/localData.js](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/src/data/localData.js), strutturati in conformità con gli schemi BigQuery descritti in `GEMINI.md`:

- `news.articles`: `data_modifica`, `title`, `summary`, `body`, `sentiment`
- `financial_instruments.instruments_quotes`: `DATA_QUOTAZ`, `ticker`, `open`, `high`, `low`, `close`, `volume`
- `financial_instruments.instruments_info`: `ticker`, `name`, `isin`, `sector`, `market`

### Come aggiornare i dati da Python:
Puoi estrarre dati con BigQuery (rispettando il dry-run < 1 GB e le partizioni) e salvarli in locale come JSON. Basterà importare il file JSON o aggiornare `localData.js`.

## ☁️ Deploy su Vercel

Il progetto include già il file di configurazione [vercel.json](file:///c:/Users/Windows%2010/Documents/Hackathon/MilanoFinanza/frontend/vercel.json):

1. Collega il repository a Vercel.
2. Imposta la **Root Directory** su `frontend` nelle impostazioni del progetto su Vercel (oppure Vercel leggerà direttamente la build di Vite).
3. Build command: `npm run build`
4. Output directory: `dist`

## 🛠️ Tecnologie Utilizzate
- **React 18 + Vite**
- **Recharts** per i grafici interattivi (prezzi e volumi)
- **Lucide React** per l'iconografia
- **Pure CSS / Design Tokens** con tema dark finanziario
