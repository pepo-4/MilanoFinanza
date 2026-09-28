"""
Package Visualization: Generazione grafici Plotly finanziari.
Riceve DataFrame puliti e restituisce oggetti plotly.graph_objects.Figure.
Nessun codice HTML incorporato, nessuna chiamata a Streamlit.
"""

from .price_charts import create_price_candlestick_figure, CLEAN_MODEBAR_BUTTONS
from .fear_greed_charts import create_fear_greed_figure, create_single_indicator_figure

__all__ = [
    "create_price_candlestick_figure",
    "create_fear_greed_figure",
    "create_single_indicator_figure",
    "CLEAN_MODEBAR_BUTTONS",
]
