"""Sentiment delle notizie su Unicredit con Gemini (una valutazione per notizia).

Passi:
  1. download   notizie con "Unicredit" nel titolo o nel sommario -> data/unicredit/articles.parquet
  2. score      Gemini assegna a ogni notizia uno score in [-1, 1], oppure la marca come solo
                descrittiva del prezzo (analisi tecnica ecc.) e la esclude
                -> data/unicredit/sentiment_<modello>_<versione prompt>.jsonl
  3. per la serie settimanale usa scripts/weekly_sentiment.py

Il download e lo scoring riprendono da dove si erano interrotti: le notizie già
scaricate/valutate non vengono rifatte (usa --refresh per riscaricare).

Uso:
  .venv/bin/python scripts/unicredit_sentiment.py --limit 20          # prova su 20 notizie
  .venv/bin/python scripts/unicredit_sentiment.py                     # tutte
  .venv/bin/python scripts/unicredit_sentiment.py --model gemini-2.5-flash

I file in data/ contengono testo protetto di Milano Finanza: data/ è in .gitignore, non committarli.
"""

import argparse
import json
import sys
import threading
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from google.cloud import bigquery
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

warnings.filterwarnings("ignore", message=".*quota project.*")

PROJECT = "class-hackaton-12"
PATTERN = r"(?i)\bunicredit\b"
MAX_BYTES_SENZA_CONFERMA = 1024**3  # 1 GB
CHIUSURA_BORSA = "17:30"
MAX_CHARS = 12000  # il body più lungo è ~24k caratteri; la mediana ~1.3k

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "unicredit"


# ---------------------------------------------------------------- BigQuery

def human_bytes(n):
    n = float(n or 0)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if n < 1024:
            return f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def run_query(bq, sql, params=None, confermato=False):
    """Dry run + esecuzione. Oltre 1 GB si ferma se non c'è --conferma."""
    params = params or []
    dry = bq.query(sql, job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, query_parameters=params))
    stima = dry.total_bytes_processed
    print(f"  dry run: {stima:,} byte stimati ({human_bytes(stima)})")
    if stima > MAX_BYTES_SENZA_CONFERMA and not confermato:
        sys.exit(f"  STOP: stima {human_bytes(stima)} > 1 GB. Rilancia con --conferma se sei sicuro.")
    cfg = bigquery.QueryJobConfig(query_parameters=params, maximum_bytes_billed=max(stima * 2, 20 * 1024**2))
    job = bq.query(sql, job_config=cfg)
    df = job.to_dataframe(create_bqstorage_client=False)
    print(f"  eseguita: {job.total_bytes_billed or 0:,} byte fatturati ({human_bytes(job.total_bytes_billed)})")
    return df


def download_articles(bq, refresh, confermato):
    path = OUT_DIR / "articles.parquet"
    if path.exists() and not refresh:
        df = pd.read_parquet(path)
        print(f"[download] uso {path.relative_to(OUT_DIR.parents[1])} ({len(df)} notizie). --refresh per riscaricare.")
        return df
    print("[download] notizie Unicredit da news.articles")
    # Le notizie 2021-2024 hanno data_modifica NULL (partizione __NULL__): vanno incluse esplicitamente.
    sql = f"""
    SELECT content_id, data_pubblicazione, data_modifica, titolo, sommario, body
    FROM `{PROJECT}.news.articles`
    WHERE (data_modifica IS NULL OR data_modifica >= '2021-01-01')
      AND REGEXP_CONTAINS(CONCAT(IFNULL(titolo, ''), ' ', IFNULL(sommario, '')), @pattern)
    """
    df = run_query(bq, sql, [bigquery.ScalarQueryParameter("pattern", "STRING", PATTERN)], confermato)
    df = df.drop_duplicates("content_id")
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)
    print(f"  salvate {len(df)} notizie in {path.relative_to(OUT_DIR.parents[1])}")
    return df


# ---------------------------------------------------------------- Gemini

PROMPT_VERSION = "v2"  # cambiala quando modifichi ISTRUZIONI: i risultati finiscono in un file nuovo


class Sentiment(BaseModel):
    solo_descrittiva: bool = Field(
        description="true se l'articolo descrive solo l'andamento del prezzo già avvenuto (analisi tecnica, livelli, rialzi/ribassi di seduta) senza informazioni nuove"
    )
    score: float | None = Field(
        default=None, ge=-1, le=1,
        description="null se solo_descrittiva; altrimenti -1 = molto negativa, 0 = neutra, 1 = molto positiva per UniCredit",
    )
    motivazione: str = Field(description="Una frase in italiano")


ISTRUZIONI = """Sei un analista finanziario. Valuta l'impatto della notizia su UniCredit
(la banca e il suo titolo in Borsa).

1. Decidi prima se l'articolo è SOLO DESCRITTIVO del prezzo: si limita a raccontare come si è
   già mosso il titolo (analisi tecnica, supporti e resistenze, "il titolo sale/scende del 2%",
   cronaca di seduta) senza aggiungere informazioni nuove su UniCredit.
   In quel caso metti solo_descrittiva = true e score = null.
   NON è solo descrittivo se contiene anche informazioni nuove: conti, dividendi, operazioni
   (acquisizioni, fusioni, cessioni), management, regolatori, giudizi o target price di analisti.

2. Altrimenti metti solo_descrittiva = false e assegna uno score da -1 a 1:
   -1 = molto negativa, 0 = neutra o non rilevante per UniCredit, 1 = molto positiva.
   Usa valori intermedi (es. -0.3, 0.6) per impatti moderati.
   Se UniCredit è solo citata di passaggio, lo score deve essere vicino a 0.

Basati solo sul contenuto dell'articolo."""


def build_prompt(row):
    testo = (row.body or row.sommario or "")[:MAX_CHARS]
    return f"Titolo: {row.titolo}\n\nSommario: {row.sommario or ''}\n\nTesto:\n{testo}"


def score_one(client, model, row, max_retry=6):
    cfg = types.GenerateContentConfig(
        system_instruction=ISTRUZIONI,
        temperature=0,
        response_mime_type="application/json",
        response_schema=Sentiment,
        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
    )
    for tentativo in range(max_retry):
        try:
            r = client.models.generate_content(model=model, contents=build_prompt(row), config=cfg)
            s = r.parsed
            if s is None:
                s = Sentiment.model_validate_json(r.text)
            if not s.solo_descrittiva and s.score is None:
                raise ValueError("score mancante per notizia non descrittiva")
            return {
                "content_id": row.content_id,
                "solo_descrittiva": s.solo_descrittiva,
                "score": None if s.solo_descrittiva else s.score,
                "motivazione": s.motivazione,
                "model": model,
                "tok_in": r.usage_metadata.prompt_token_count,
                "tok_out": r.usage_metadata.candidates_token_count,
            }
        except Exception as e:  # 429 / 5xx / JSON malformato: backoff esponenziale
            if tentativo == max_retry - 1:
                return {"content_id": row.content_id, "errore": f"{type(e).__name__}: {e}"[:300], "model": model}
            time.sleep(min(2**tentativo * 2, 60))


def score_articles(df, model, workers, limit):
    path = OUT_DIR / f"sentiment_{model}_{PROMPT_VERSION}.jsonl"
    fatti = set()
    if path.exists():
        with path.open() as f:
            fatti = {r["content_id"] for r in map(json.loads, f) if "errore" not in r}
    todo = df[~df["content_id"].isin(fatti)].sort_values("data_pubblicazione")
    if limit:
        todo = todo.head(limit)
    print(f"[score] modello {model}: {len(fatti)} già valutate, {len(todo)} da valutare ({workers} in parallelo)")
    if todo.empty:
        return path

    client = genai.Client(vertexai=True, project=PROJECT, location="global")
    lock = threading.Lock()
    ok = err = descr = tok_in = tok_out = 0
    t0 = time.time()
    with path.open("a") as out, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(score_one, client, model, row) for row in todo.itertuples()]
        for i, fut in enumerate(as_completed(futures), 1):
            res = fut.result()
            with lock:
                out.write(json.dumps(res, ensure_ascii=False) + "\n")
                out.flush()
            if "errore" not in res:
                ok += 1
                descr += res["solo_descrittiva"]
                tok_in += res["tok_in"] or 0
                tok_out += res["tok_out"] or 0
            else:
                err += 1
            if i % 50 == 0 or i == len(futures):
                print(f"  {i}/{len(futures)}  ok={ok} (descrittive={descr}) errori={err}  token in/out={tok_in:,}/{tok_out:,}  {time.time() - t0:.0f}s")
    if err:
        print(f"  {err} notizie in errore: rilancia lo script per riprovarle.")
    return path


# ---------------------------------------------------------------- Date

def to_seduta(ts):
    """Notizie dopo la chiusura o nel weekend contano per la seduta successiva."""
    ts = pd.Timestamp(ts)
    giorno = ts.normalize()
    if ts.dayofweek >= 5 or ts.strftime("%H:%M") >= CHIUSURA_BORSA:
        giorno = giorno + pd.offsets.BDay(1)
    return giorno


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--limit", type=int, default=0, help="valuta al massimo N notizie nuove (0 = tutte)")
    ap.add_argument("--workers", type=int, default=8, help="chiamate Gemini in parallelo")
    ap.add_argument("--refresh", action="store_true", help="riscarica le notizie da BigQuery")
    ap.add_argument("--conferma", action="store_true", help="consenti query oltre 1 GB")
    args = ap.parse_args()

    bq = bigquery.Client(project=PROJECT)
    df = download_articles(bq, args.refresh, args.conferma)
    df["data_pubblicazione"] = pd.to_datetime(df["data_pubblicazione"])

    score_articles(df, args.model, args.workers, args.limit)
    print("Per la serie settimanale: .venv/bin/python scripts/weekly_sentiment.py")


if __name__ == "__main__":
    main()
