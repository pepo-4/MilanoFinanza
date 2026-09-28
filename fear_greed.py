"""
Modulo Facade per l'Indice Fear & Greed.
Mantiene la piena retrocompatibilità per qualsiasi script esistente,
delegando le responsabilità ai layer dedicati:
- Business Logic: analytics.fear_greed
- Visualizzazione: visualization.fear_greed_charts
- Presentazione UI: ui.streamlit_views
"""

# 1. Logica di business pura (calcolo matematico)
from analytics.fear_greed import (
    calculate_fear_greed,
    get_fgi_category,
)

# 2. Visualizzazione grafica Plotly
from visualization.fear_greed_charts import (
    create_fear_greed_figure as plot_fear_and_greed_chart,
    create_single_indicator_figure as plot_single_indicator,
)

from visualization.price_charts import CLEAN_MODEBAR_BUTTONS

# 3. Presentazione UI (Streamlit)
from ui.streamlit_views import (
    render_fear_and_greed_section as render_fear_and_greed_streamlit,
)

__all__ = [
    "calculate_fear_greed",
    "get_fgi_category",
    "plot_fear_and_greed_chart",
    "plot_single_indicator",
    "render_fear_and_greed_streamlit",
    "CLEAN_MODEBAR_BUTTONS",
]
