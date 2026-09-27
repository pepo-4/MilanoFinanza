# CLAUDE.md

Progetto hackathon su dati Milano Finanza in BigQuery.

## Contesto

- Progetto Google Cloud: `class-hackaton-12`
- Dataset in sola lettura:
  - `news`: `articles` (partizionata per giorno su `data_modifica`, DATETIME), `articles_embeddings`
  - `financial_instruments`: `instruments_quotes` (partizionata per giorno su `DATA_QUOTAZ`, DATETIME), `instruments_embeddings` (non partizionata), `instruments_info`
- Credenziali: `gcloud auth application-default login`. Se mancano o sono scadute, fermati e chiedi all'utente di rifare il login dal browser.
- Ambiente: `.venv` nella radice (`.venv/bin/python`), dipendenze in `requirements.txt`.
- La quota è limitata e BigQuery fa pagare i **byte letti**, non le righe restituite: `LIMIT` non riduce il costo.

## Regole

1. **Non indovinare i nomi delle colonne**: leggi prima lo schema (`bq show --schema` oppure `client.get_table`), che è gratuito.
2. **Mai `SELECT *`**: seleziona solo le colonne che servono.
3. **Sulle tabelle partizionate filtra sempre sulla colonna di partizione** (`data_modifica` per `news.articles`, `DATA_QUOTAZ` per `financial_instruments.instruments_quotes`).
4. **Prima di ogni query fai un dry run e mostra i byte stimati.** Se la stima supera 1 GB, chiedi conferma all'utente prima di eseguirla.
5. **Non committare mai credenziali, file `.env` o dati estratti dalle tabelle**: sono contenuti protetti di Milano Finanza. I dati locali vanno in `data/` (ignorata da git); gli output dei notebook sono rimossi da `nbstripout` al commit.

## Note pratiche

- `INFORMATION_SCHEMA.PARTITIONS` è accessibile, ma ogni query su `INFORMATION_SCHEMA` fattura il minimo di 10 MB.
- Anche una query piccola fattura almeno 10 MB.
- Le colonne `embedding` (FLOAT REPEATED) e `body` sono le più pesanti: includile solo se servono davvero.
