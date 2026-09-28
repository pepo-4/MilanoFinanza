"""
Modulo Facade per l'Analisi e Visualizzazione Grafica delle Azioni.
Mantiene la piena retrocompatibilità per qualsiasi script o import esistente,
delegando ogni responsabilità ai layer architetturali dedicati:

- Data Access: `data_access.quotes_service`
- Business Logic: `analytics.indicators` e `analytics.fear_greed`
- Visualizzazione: `visualization.price_charts` e `visualization.fear_greed_charts`
- Presentazione UI: `ui.standalone_html` e `ui.streamlit_views`
"""

import os

# 1. Data Access Layer
from data_access.quotes_service import (
    query_stock_quotes_bigquery,
    TICKER_MAP,
)

# 2. Business Logic Layer
from analytics.indicators import (
    prepare_stock_data,
    detect_column as _detect_column,
)
from analytics.fear_greed import (
    calculate_fear_greed,
    get_fgi_category,
)

# 3. Visualization Layer
from visualization.price_charts import (
    create_price_candlestick_figure as plot_stock_plotly,
    CLEAN_MODEBAR_BUTTONS as CLEAN_MODEBAR_BUTTONS_TO_REMOVE,
)
from visualization.fear_greed_charts import (
    create_fear_greed_figure as plot_fear_and_greed_chart,
    create_single_indicator_figure as plot_single_indicator,
)

# 4. Presentation UI Layer
from ui.standalone_html import (
    generate_decision_support_html as generate_decision_support_app,
)
from ui.streamlit_views import (
    render_fear_and_greed_section as render_fear_and_greed_streamlit,
    render_ai_executive_summary,
)

__all__ = [
    "query_stock_quotes_bigquery",
    "TICKER_MAP",
    "prepare_stock_data",
    "_detect_column",
    "calculate_fear_greed",
    "get_fgi_category",
    "plot_stock_plotly",
    "CLEAN_MODEBAR_BUTTONS_TO_REMOVE",
    "plot_fear_and_greed_chart",
    "plot_single_indicator",
    "generate_decision_support_app",
    "render_fear_and_greed_streamlit",
    "render_ai_executive_summary",
]

# Esecuzione diretta per generazione rapida dell'applicazione di test HTML
if __name__ == "__main__":
    from google.cloud import bigquery

    ticker_test = "UCG"
    project_id = "class-hackaton-12"

    print(f"--- Supporto Decisionale Finanziario per {ticker_test} ---")
    try:
        client = bigquery.Client(project=project_id)
        df_real = query_stock_quotes_bigquery(client, ticker=ticker_test, years=5, cache=True)
    except Exception as e:
        print(f"Errore connessione BigQuery ({e}).")
        raise

    print(f"Dati caricati: {len(df_real):,} quotazioni.")

    # 1. Calcolo indicatori tramite Business Logic
    df_clean = prepare_stock_data(df_real, ticker=ticker_test, years=5, timeframe="1W")

    # 2. Generazione figura tramite Visualization Layer
    fig = plot_stock_plotly(
        df_clean,
        ticker="UniCredit (UCG)",
        years=5,
        ma_window=200,
        timeframe="1W",
    )

    # 3. Presentazione tramite UI Layer
    generate_decision_support_app(fig, ticker="UniCredit (UCG)", output_html="stock_analysis.html", auto_open=True)
