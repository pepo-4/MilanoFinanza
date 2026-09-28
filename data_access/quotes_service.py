"""
Servizio di estrazione e caching delle quotazioni storiche.
Rispetta le linee guida di costo, sicurezza e partizionamento (CLAUDE.md).
"""

import os
from typing import Optional
import pandas as pd

# Mappatura dei ticker di Borsa Italiana al COD_AZIONE del database Milano Finanza
TICKER_MAP = {
    'UCG': 'CRIT',
    'UNICREDIT': 'CRIT',
    'ISP': 'ISP',
    'INTESA': 'ISP',
    'INTESA SANPAOLO': 'ISP',
    'ENI': 'ENI',
    'ENEL': 'ENEL',
    'RACE': 'RACE',
    'FERRARI': 'RACE',
    'STM': 'STM',
    'STLA': 'STLA',
    'STELLANTIS': 'STLA',
    'G': 'GAS',
    'GENERALI': 'GAS',
    'TIT': 'TIT',
    'TELECOM': 'TIT',
}


def query_stock_quotes_bigquery(
    client,
    ticker: str,
    project_id: str = "class-hackaton-12",
    years: int = 5,
    confermato: bool = False,
    cache: bool = True,
    data_dir: Optional[str] = None,
) -> pd.DataFrame:
    """
    Estrae le quotazioni reali dell'azione da BigQuery rispettando CLAUDE.md:
    1. Risolve il ticker al COD_AZIONE (es. UCG -> CRIT).
    2. Usa la cache locale in `data/` per non rieseguire la query se i dati esistono già.
    3. Nessuna SELECT *: richiede solo le colonne necessarie.
    4. Filtra sempre sulla colonna di partizione `DATA_QUOTAZ`.
    5. Aggiunge un buffer di 300 giorni prima dei 5 anni per il calcolo delle SMA storiche.
    6. Esegue dry run preventivo obbligatorio prima dell'esecuzione (soglia 1 GB).
    """
    from google.cloud import bigquery

    if data_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        data_dir = os.path.join(base_dir, "data")

    cod_azione = TICKER_MAP.get(ticker.upper(), ticker.upper())
    os.makedirs(data_dir, exist_ok=True)
    cache_file = os.path.join(data_dir, f"{cod_azione}_quotes_{years}y.csv")

    # Verifica cache locale (Regola 5 CLAUDE.md)
    if cache and os.path.exists(cache_file):
        df_cached = pd.read_csv(cache_file)
        df_cached['DATA_QUOTAZ'] = pd.to_datetime(df_cached['DATA_QUOTAZ'])
        return df_cached

    # Buffer: 5 anni + 300 giorni di margine per le medie mobili
    giorni_totali = (years * 365) + 300
    table_id = f"`{project_id}.financial_instruments.instruments_quotes`"

    sql = f"""
    SELECT
        DATA_QUOTAZ,
        COD_AZIONE,
        DES_AZIONE,
        PRZ_APERTURA,
        PRZ_LAST,
        PRZ_RIF,
        PRZ_MAX,
        PRZ_MIN,
        QUANTITATIVO
    FROM {table_id}
    WHERE DATA_QUOTAZ >= DATETIME_SUB(CURRENT_DATETIME(), INTERVAL {giorni_totali} DAY)
      AND COD_AZIONE = @cod_azione
    ORDER BY DATA_QUOTAZ ASC
    """

    params = [bigquery.ScalarQueryParameter("cod_azione", "STRING", cod_azione)]

    # 1. Dry run preventivo
    cfg_dry = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, query_parameters=params)
    job_dry = client.query(sql, job_config=cfg_dry)
    bytes_stimati = job_dry.total_bytes_processed

    max_bytes = 1024**3  # 1 GB
    if bytes_stimati > max_bytes and not confermato:
        raise RuntimeError(
            f"Stima di {bytes_stimati / (1024**2):.2f} MB supera 1 GB. Passare `confermato=True` per eseguire."
        )

    # 2. Esecuzione effettiva protetta
    cfg_exec = bigquery.QueryJobConfig(
        query_parameters=params,
        maximum_bytes_billed=max(bytes_stimati * 2, 10 * 1024**2),
    )
    job_exec = client.query(sql, job_config=cfg_exec)
    df = job_exec.to_dataframe(create_bqstorage_client=False)

    if cache and not df.empty:
        df.to_csv(cache_file, index=False)

    return df
