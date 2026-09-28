"""
Package Data Access: Estrazione dati e gestione cache locale.
Conforme alle linee guida di CLAUDE.md per BigQuery.
"""

from .quotes_service import query_stock_quotes_bigquery, TICKER_MAP

__all__ = [
    "query_stock_quotes_bigquery",
    "TICKER_MAP",
]
