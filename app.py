"""
Applicazione Web Streamlit - Supporto Decisionale Finanziario (Hackathon Milano Finanza)
Include:
1. Sezione Principale: Grafico dei Prezzi (Plotly) + Area AI per Sintesi Operativa.
2. Sezione Analisi Quantitativa: Indice Fear & Greed del Titolo (con metriche e grafico storico Plotly).
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from plot_azione import (
    query_stock_quotes_bigquery,
    plot_stock_plotly,
    TICKER_MAP,
    CLEAN_MODEBAR_BUTTONS_TO_REMOVE,
)
from fear_greed import (
    calculate_fear_greed,
    plot_fear_and_greed_chart,
    render_fear_and_greed_streamlit,
    get_fgi_category,
)

# Configurazione pagina Streamlit a tutta larghezza
st.set_page_config(
    page_title="Supporto Decisionale Finanziario · Milano Finanza",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Stile CSS moderno e rifinito per interfaccia finanziaria premium
st.markdown("""
<style>
    /* Dark Theme Finanziario */
    .stApp {
        background-color: #0b1120;
        color: #f8fafc;
    }
    
    /* Header personalizzato */
    .dashboard-header {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 16px 24px;
        border-radius: 12px;
        border: 1px solid #334155;
        margin-bottom: 20px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    .header-title {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
    }
    .header-subtitle {
        font-size: 13px;
        color: #94a3b8;
        margin: 2px 0 0 0;
    }
    
    /* Card per Area AI */
    .ai-box {
        background: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 18px;
        height: 100%;
    }
    .ai-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 10px;
    }
    .badge-bullish {
        background: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid rgba(34, 197, 94, 0.3);
    }
    .badge-bearish {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .badge-neutral {
        background: rgba(234, 179, 8, 0.15);
        color: #facc15;
        border: 1px solid rgba(234, 179, 8, 0.3);
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_stock_data(ticker: str, years: int = 5) -> pd.DataFrame:
    """Carica i dati storici tramite BigQuery con cache su disco (CLAUDE.md compliant)."""
    cod_target = TICKER_MAP.get(ticker.upper(), ticker.upper())
    cache_path = os.path.join(os.path.dirname(__file__), "data", f"{cod_target}_quotes_{years}y.csv")

    if os.path.exists(cache_path):
        df = pd.read_csv(cache_path)
        df['DATA_QUOTAZ'] = pd.to_datetime(df['DATA_QUOTAZ'])
        return df

    # Fallback connessione BigQuery
    try:
        from google.cloud import bigquery
        client = bigquery.Client(project="class-hackaton-12")
        df = query_stock_quotes_bigquery(client, ticker=ticker, years=years, cache=True)
        return df
    except Exception as e:
        st.error(f"Errore caricamento dati da BigQuery: {e}")
        return pd.DataFrame()


# ==============================================================================
# SIDEBAR DEI CONTROLLI
# ==============================================================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/e/e4/Milano_Finanza_logo.svg", width=180)
    st.markdown("### ⚙️ Impostazioni Analisi")

    ticker_choices = [
        "UniCredit (UCG)",
        "Intesa Sanpaolo (ISP)",
        "ENI (ENI)",
        "ENEL (ENEL)",
        "Ferrari (RACE)",
        "Stellantis (STLA)",
        "Generali (G)",
        "Telecom Italia (TIT)"
    ]
    ticker_selected = st.selectbox("Seleziona Titolo Azionario", ticker_choices, index=0)
    ticker_clean = ticker_selected.split("(")[-1].replace(")", "").strip()

    timeframe = st.radio("Timeframe Candele", ["Settimanale (1W - Consigliato)", "Giornaliero (1D)"], index=0)
    timeframe_code = "1W" if "1W" in timeframe else "1D"

    years = st.slider("Orizzonte Temporale (Anni)", min_value=1, max_value=5, value=5, step=1)

    st.markdown("---")
    st.markdown("#### 🎯 Indicatori Grafico")
    st.info("Di default sono visibili **solo** Prezzo, SMA 200 e Volumi. Gli altri indicatori sono opzionali.")
    show_sma50 = st.checkbox("Mostra SMA 50 gg (Opzionale)", value=False)
    show_signals = st.checkbox("Mostra Segnali Golden/Death Cross (Opzionale)", value=False)


# ==============================================================================
# CARICAMENTO DATI E CALCOLO FEAR & GREED
# ==============================================================================
with st.spinner(f"Caricamento quotazioni per {ticker_selected}..."):
    df_raw = load_stock_data(ticker_clean, years=years)

if df_raw.empty:
    st.warning("Nessun dato disponibile. Assicurati che il file cache in data/ sia presente o di aver autenticato BigQuery.")
    st.stop()

# Calcolo Indice Fear & Greed con la funzione richiesta
df_fgi = calculate_fear_greed(df_raw)

# Informazioni ultimo dato
last_row = df_fgi.iloc[-1]
last_date = pd.to_datetime(last_row['date']).strftime('%d/%m/%Y')
current_price = float(last_row['close'] if 'close' in last_row else last_row['PRZ_LAST'])
sma_200_val = float(df_raw['PRZ_LAST'].rolling(200, min_periods=1).mean().iloc[-1])
is_above_200 = current_price >= sma_200_val

# Header principale
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
# 1. SEZIONE PRINCIPALE (GRAFICO DEI PREZZI + AREA AI)
# ==============================================================================
col_chart, col_ai = st.columns([7, 3])

with col_chart:
    st.subheader("📊 Andamento Prezzo e Volumi")
    fig_price = plot_stock_plotly(
        df_raw,
        ticker=ticker_selected,
        years=years,
        ma_window=200,
        timeframe=timeframe_code,
        theme="plotly_dark",
    )

    # Aggiorna la visibilità in base ai toggle opzionali
    if show_sma50:
        fig_price.data[2].visible = True
    if show_signals:
        fig_price.data[3].visible = True
        fig_price.data[4].visible = True

    clean_cfg = {
        'modeBarButtonsToRemove': CLEAN_MODEBAR_BUTTONS_TO_REMOVE,
        'displaylogo': False,
        'responsive': True,
        'scrollZoom': True
    }
    st.plotly_chart(fig_price, use_container_width=True, config=clean_cfg)

with col_ai:
    st.subheader("🤖 Area AI Decisionale")

    cat_name, cat_emoji, cat_color = get_fgi_category(float(last_row['FGI_Synthetic']))
    badge_class = "badge-bullish" if "Greed" in cat_name else ("badge-bearish" if "Fear" in cat_name else "badge-neutral")

    st.markdown(f"""
    <div class="ai-box">
        <span class="ai-badge {badge_class}">{cat_emoji} Sentiment: {cat_name}</span>
        <h4 style="color:#ffffff; margin: 4px 0 10px 0;">Executive Summary</h4>
        <p style="font-size: 13px; color: #cbd5e1; line-height: 1.5;">
            L'azione <b>{ticker_clean}</b> scambia attualmente a <b>€{current_price:.2f}</b>, 
            posizionandosi <b>{'sopra' if is_above_200 else 'sotto'}</b> la media mobile primaria a 200 giorni (€{sma_200_val:.2f}).
        </p>
        <hr style="border-color: #334155; margin: 12px 0;">
        <h5 style="color:#38bdf8; margin-bottom: 6px;">Key Drivers Quantitativi:</h5>
        <ul style="font-size: 12px; color: #94a3b8; padding-left: 18px; line-height: 1.6;">
            <li><b>Momentum 125g:</b> {last_row['FGI_Momentum']:.1f}/100 ({'Forte spinta rialzista' if last_row['FGI_Momentum'] > 55 else 'Debolezza'})</li>
            <li><b>RSI 20g:</b> {last_row['FGI_RSI']:.1f}/100 ({'Ipercomprato' if last_row['FGI_RSI'] > 70 else ('Ipervenduto' if last_row['FGI_RSI'] < 30 else 'Zona di equilibrio')})</li>
            <li><b>Volatilità ATR:</b> {last_row['FGI_Volatility']:.1f}/100 ({'Fase compressa/Calma' if last_row['FGI_Volatility'] > 55 else 'Volatilità espansa/Allerta'})</li>
            <li><b>Flusso Volumi:</b> {last_row['FGI_Volume_Pressure']:.1f}% volume su sedute rialziste.</li>
        </ul>
        <div style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 8px 12px; border-radius: 4px; margin-top: 14px; font-size: 12px; color: #e2e8f0;">
            💡 <b>Insight AI:</b> La combinazione tra trend a 200 giorni e indice Fear & Greed a <b>{last_row['FGI_Synthetic']:.1f}</b> segnala una configurazione <b>{cat_name.lower()}</b>, idonea a strategie di prosecuzione del trend con stop-loss ancorati alla SMA 200.
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==============================================================================
# 2. SEZIONE ANALISI QUANTITATIVA: INDICE FEAR & GREED DEL TITOLO
# ==============================================================================
render_fear_and_greed_streamlit(df_fgi, ticker=ticker_selected)
