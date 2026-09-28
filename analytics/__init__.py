"""
Package Analytics: Logica di business pura per il calcolo di indicatori tecnici e finanziari.
Nessuna dipendenza da librerie UI (zero Streamlit, zero HTML).
"""

from .indicators import prepare_stock_data
from .fear_greed import calculate_fear_greed, get_fgi_category

__all__ = [
    "prepare_stock_data",
    "calculate_fear_greed",
    "get_fgi_category",
]
