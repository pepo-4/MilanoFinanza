"""Serie temporale settimanale del sentiment delle notizie su Unicredit.

Legge le valutazioni prodotte da unicredit_sentiment.py (funziona anche a valutazione in corso:
usa quelle disponibili) e produce in data/unicredit/:

  weekly_<modello>.parquet / .csv   una riga per settimana, senza buchi (chiave: settimana = venerdì)
      score        sentiment medio delle notizie con score (null se nessuna)
      volume       numero di notizie della settimana
      n_con_score, n_descrittive, n_da_valutare
      content_ids  (solo parquet) id delle notizie della settimana

  news_by_week_<modello>.parquet    una riga per notizia, con la stessa colonna `settimana`
      content_id, settimana, data_pubblicazione, titolo, URL, solo_descrittiva, score, motivazione

Il collegamento settimana -> notizie è la colonna `settimana` (oppure `content_ids`).
Per un grafico interattivo: al clic su un punto usa notizie_settimana(news, settimana).

Uso:
  .venv/bin/python scripts/weekly_sentiment.py
  .venv/bin/python scripts/weekly_sentiment.py --refresh        # riscarica gli URL

I file in data/ contengono testo protetto di Milano Finanza: non committarli.
"""

import argparse
import warnings

import pandas as pd
from google.cloud import bigquery

from unicredit_sentiment import OUT_DIR, PROJECT, PROMPT_VERSION, run_query, to_seduta

warnings.filterwarnings("ignore", message=".*quota project.*")


# ---------------------------------------------------------------- dati

def load_urls(bq, content_ids, refresh, confermato):
    """URL delle notizie (non presenti in articles.parquet), cache locale."""
    path = OUT_DIR / "urls.parquet"
    if path.exists() and not refresh:
        cached = pd.read_parquet(path)
        if set(content_ids) <= set(cached["content_id"]):
            print(f"[url] uso {path.name}")
            return cached
    print("[url] link delle notizie")
    sql = f"""
    SELECT content_id, URL
    FROM `{PROJECT}.news.articles`
    WHERE (data_modifica IS NULL OR data_modifica >= '2021-01-01')
      AND content_id IN UNNEST(@ids)
    """
    df = run_query(bq, sql, [bigquery.ArrayQueryParameter("ids", "STRING", list(content_ids))], confermato)
    df = df.drop_duplicates("content_id")
    df.to_parquet(path, index=False)
    return df


def load_scores(model):
    path = OUT_DIR / f"sentiment_{model}_{PROMPT_VERSION}.jsonl"
    s = pd.read_json(path, lines=True, dtype={"content_id": str})
    if "errore" in s:
        s = s[s["errore"].isna()]
    return s.drop_duplicates("content_id", keep="last")[["content_id", "solo_descrittiva", "score", "motivazione"]]


# ---------------------------------------------------------------- aggregazione

def settimana_di(seduta):
    """Chiave della settimana: il venerdì con cui si chiude (settimane sabato -> venerdì)."""
    return seduta.dt.to_period("W-FRI").dt.end_time.dt.normalize()


def build_news_by_week(articles, scores, urls):
    news = articles[["content_id", "data_pubblicazione", "titolo"]].merge(urls, on="content_id", how="left")
    news = news.merge(scores, on="content_id", how="left")  # notizie non ancora valutate: score/flag null
    # Notizie dopo la chiusura o nel weekend contano per la seduta (e quindi la settimana) successiva
    news["settimana"] = settimana_di(news["data_pubblicazione"].map(to_seduta))
    news["valutata"] = news["solo_descrittiva"].notna()
    cols = ["content_id", "settimana", "data_pubblicazione", "titolo", "URL",
            "valutata", "solo_descrittiva", "score", "motivazione"]
    return news[cols].sort_values("data_pubblicazione").reset_index(drop=True)


def build_weekly(news):
    g = news.groupby("settimana")
    w = pd.DataFrame({
        "score": g["score"].mean(),
        "volume": g.size(),
        "n_con_score": g["score"].count(),
        "n_descrittive": g["solo_descrittiva"].apply(lambda s: (s == True).sum()),  # noqa: E712 (può essere null)
        "n_da_valutare": g["valutata"].apply(lambda s: (~s).sum()),
        "content_ids": g["content_id"].agg(list),
    })
    # Serie continua: anche le settimane senza notizie (volume 0, score null)
    w = w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="W-FRI"))
    for c in ["volume", "n_con_score", "n_descrittive", "n_da_valutare"]:
        w[c] = w[c].fillna(0).astype(int)
    w["content_ids"] = w["content_ids"].apply(lambda x: x if isinstance(x, list) else [])
    w.index.name = "settimana"
    return w


def notizie_settimana(news, settimana, anche_descrittive=True):
    """Notizie di una settimana: `settimana` è il venerdì di chiusura (o una data qualsiasi della settimana)."""
    key = settimana_di(pd.Series([to_seduta(pd.Timestamp(settimana))])).iloc[0]
    out = news[news["settimana"] == key]
    if not anche_descrittive:
        out = out[out["solo_descrittiva"] == False]  # noqa: E712
    return out[["data_pubblicazione", "titolo", "score", "solo_descrittiva", "motivazione", "URL", "content_id"]]


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--refresh", action="store_true", help="riscarica gli URL da BigQuery")
    ap.add_argument("--conferma", action="store_true", help="consenti query oltre 1 GB")
    args = ap.parse_args()

    articles = pd.read_parquet(OUT_DIR / "articles.parquet")
    articles["data_pubblicazione"] = pd.to_datetime(articles["data_pubblicazione"])
    scores = load_scores(args.model)
    urls = load_urls(bigquery.Client(project=PROJECT), articles["content_id"], args.refresh, args.conferma)

    news = build_news_by_week(articles, scores, urls)
    weekly = build_weekly(news)

    news_path = OUT_DIR / f"news_by_week_{args.model}.parquet"
    weekly_path = OUT_DIR / f"weekly_{args.model}.parquet"
    news.to_parquet(news_path, index=False)
    weekly.to_parquet(weekly_path)
    weekly.drop(columns="content_ids").to_csv(weekly_path.with_suffix(".csv"), float_format="%.4f")

    n_val = int(news["valutata"].sum())
    print(f"Notizie valutate: {n_val}/{len(news)}"
          + ("" if n_val == len(news) else "  (valutazione incompleta: rilancia quando unicredit_sentiment.py ha finito)"))
    print(f"Settimane: {len(weekly)} ({weekly.index.min().date()} -> {weekly.index.max().date()}), "
          f"con score: {(weekly['n_con_score'] > 0).sum()}")
    print(f"-> {weekly_path.name} (+ .csv), {news_path.name}\n")
    print(weekly[weekly["n_con_score"] > 0].drop(columns="content_ids").tail(5).to_string())


if __name__ == "__main__":
    main()
