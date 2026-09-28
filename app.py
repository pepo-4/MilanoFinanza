"""
Applicazione Web Streamlit - Supporto Decisionale Finanziario (Hackathon Milano Finanza).

Architettura modulare a strati:
- Layer 1: Data Access (data_access.quotes_service)
- Layer 2: Business Logic / Analytics (analytics.indicators, analytics.fear_greed)
- Layer 3: Visualizzazione Grafica Plotly (visualization.price_charts, visualization.fear_greed_charts)
- Layer 4: Componenti UI Streamlit (ui.streamlit_views)
"""

import os
import streamlit as st
import pandas as pd

# 1. Accesso ai dati
from data_access.quotes_service import query_stock_quotes_bigquery, TICKER_MAP

# 2. Logica di business pura
from analytics.indicators import prepare_stock_data
from analytics.fear_greed import calculate_fear_greed

# 3. Visualizzazione grafica
from visualization.price_charts import create_price_candlestick_figure, CLEAN_MODEBAR_BUTTONS

# 4. Componenti di presentazione UI
from ui.streamlit_views import render_ai_executive_summary, render_fear_and_greed_section

# Configurazione pagina Streamlit
st.set_page_config(
    page_title="Supporto Decisionale Finanziario · Milano Finanza",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Iniezione stili CSS dedicati
st.markdown("""
<style>
    .stApp { background-color: #0b1120; color: #f8fafc; }
    .dashboard-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 16px 24px; border-radius: 12px; border: 1px solid #334155;
        margin-bottom: 20px; display: flex; align-items: center; justify-content: space-between;
    }
    .header-title { font-size: 24px; font-weight: 700; color: #ffffff; margin: 0; }
    .header-subtitle { font-size: 13px; color: #94a3b8; margin: 2px 0 0 0; }
    .ai-box { background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 18px; height: 100%; }
    .ai-badge {
        display: inline-block; padding: 3px 8px; border-radius: 6px;
        font-size: 11px; font-weight: 600; text-transform: uppercase; margin-bottom: 10px;
    }
    .badge-bullish { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-bearish { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .badge-neutral { background: rgba(234, 179, 8, 0.15); color: #facc15; border: 1px solid rgba(234, 179, 8, 0.3); }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_cached_or_remote_quotes(ticker: str, years: int = 5) -> pd.DataFrame:
    """Carica i dati dal Layer di Data Access."""
    cod_target = TICKER_MAP.get(ticker.upper(), ticker.upper())
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(base_dir, "data", f"{cod_target}_quotes_{years}y.csv")

    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        df['DATA_QUOTAZ'] = pd.to_datetime(df['DATA_QUOTAZ'])
        return df

    try:
        from google.cloud import bigquery
        client = bigquery.Client(project="class-hackaton-12")
        return query_stock_quotes_bigquery(client, ticker=ticker, years=years, cache=True)
    except Exception as e:
        st.error(f"Errore connessione BigQuery: {e}")
        return pd.DataFrame()


# ==============================================================================
# SIDEBAR
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Milano_Finanza_logo.svg", width=180)
    st.markdown("### ⚙️ Impostazioni")

    ticker_choices = [
        "UniCredit (UCG)", "Intesa Sanpaolo (ISP)", "ENI (ENI)", "ENEL (ENEL)",
        "Ferrari (RACE)", "Stellantis (STLA)", "Generali (G)", "Telecom Italia (TIT)"
    ]
    ticker_selected = st.selectbox("Titolo Azionario", ticker_choices, index=0)
    ticker_clean = ticker_selected.split("(")[-1].replace(")", "").strip()

    timeframe = st.radio("Timeframe Candele", ["Settimanale (1W - Default)", "Giornaliero (1D)"], index=0)
    timeframe_code = "1W" if "1W" in timeframe else "1D"

    years = st.slider("Orizzonte Temporale (Anni)", 1, 5, 5, 1)

    st.markdown("---")
    st.markdown("#### 🎯 Indicatori Opzionali")
    show_sma50 = st.checkbox("Mostra SMA 50 gg", value=False)
    show_signals = st.checkbox("Mostra Golden/Death Cross", value=False)


# ==============================================================================
# CARICAMENTO DATI & ANALISI
# ==============================================================================
with st.spinner("Elaborazione dati in corso..."):
    df_raw = load_cached_or_remote_quotes(ticker_clean, years=years)

if df_raw.empty:
    st.warning("Quotazioni non disponibili.")
    st.stop()

# Elaborazione tramite i due moduli di Business Logic pura
df_clean_tech = prepare_stock_data(df_raw, ticker=ticker_clean, years=years, timeframe=timeframe_code)
df_fgi = calculate_fear_greed(df_raw)

last_fgi = df_fgi.iloc[-1]
current_price = float(last_fgi['close'] if 'close' in last_fgi else last_fgi['PRZ_LAST'])
sma_200_val = float(df_clean_tech['ma_200'].iloc[-1])
is_above_200 = current_price >= sma_200_val
last_date = pd.to_datetime(last_fgi['date']).strftime('%d/%m/%Y')

# Header
st.markdown(f"""
<div class="dashboard-header">
    <div>
        <h1 class="header-title">📈 Supporto Decisionale: {ticker_selected}</h1>
        <p class="header-subtitle">Dati ufficiali Borsa Italiana · Ultima seduta: <b>{last_date}</b> · Orizzonte: <b>{years} anni</b></p>
    </div>
    <div style="text-align: right;">
        <span style="font-size: 26px; font-weight: 700; color: {'#4ade80' if is_above_200 else '#f87171'};">
            €{current_price:.2f}
        </span>
        <div style="font-size: 12px; color: #94a3b8;">
            {'Sopra SMA 200 (+ Bullish)' if is_above_200 else 'Sotto SMA 200 (- Bearish)'}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# 1. SEZIONE PRINCIPALE: GRAFICO DEI PREZZI + AREA AI
# ==============================================================================
col_chart, col_ai = st.columns([7, 3])

with col_chart:
    st.subheader("📊 Andamento Prezzo e Volumi")
    fig_price = create_price_candlestick_figure(
        df_clean_tech,
        ticker=ticker_selected,
        years=years,
        timeframe=timeframe_code,
    )
    if show_sma50 and len(fig_price.data) > 2:
        fig_price.data[2].visible = True
    if show_signals and len(fig_price.data) > 4:
        fig_price.data[3].visible = True
        fig_price.data[4].visible = True

    clean_cfg = {'modeBarButtonsToRemove': CLEAN_MODEBAR_BUTTONS, 'displaylogo': False, 'responsive': True}
    st.plotly_chart(fig_price, config=clean_cfg)

with col_ai:
    st.subheader("🤖 Area AI Decisionale")
    render_ai_executive_summary(last_fgi, current_price, sma_200_val, is_above_200, ticker_clean)


# ==============================================================================
# 2. SEZIONE ANALISI QUANTITATIVA: INDICE FEAR & GREED DEL TITOLO
# ==============================================================================
render_fear_and_greed_section(df_fgi, ticker=ticker_selected)
