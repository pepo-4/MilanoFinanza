"""
Componenti visuali e viste per l'applicazione Streamlit.
Isola tutti i comandi st.* (metriche, card, header, layout) dal resto dell'applicazione.
"""

import pandas as pd
import streamlit as st

from analytics.fear_greed import get_fgi_category
from visualization.fear_greed_charts import create_fear_greed_figure
from visualization.price_charts import CLEAN_MODEBAR_BUTTONS


def render_ai_executive_summary(
    last_row: pd.Series,
    current_price: float,
    sma_200_val: float,
    is_above_200: bool,
    ticker_clean: str
):
    """Renderizza la card informativa dell'Area AI Decisionale."""
    cat_name, cat_emoji, _ = get_fgi_category(float(last_row['FGI_Synthetic']))
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
            <li><b>Momentum 125g:</b> {last_row['FGI_Momentum']:.1f}/100 ({'Spinta rialzista' if last_row['FGI_Momentum'] > 55 else 'Debolezza'})</li>
            <li><b>RSI 20g:</b> {last_row['FGI_RSI']:.1f}/100 ({'Ipercomprato' if last_row['FGI_RSI'] > 70 else ('Ipervenduto' if last_row['FGI_RSI'] < 30 else 'Zona di equilibrio')})</li>
            <li><b>Volatilità ATR:</b> {last_row['FGI_Volatility']:.1f}/100 ({'Fase compressa/Calma' if last_row['FGI_Volatility'] > 55 else 'Volatilità espansa/Allerta'})</li>
            <li><b>Flusso Volumi:</b> {last_row['FGI_Volume_Pressure']:.1f}% volume su sedute rialziste.</li>
        </ul>
        <div style="background: rgba(56, 189, 248, 0.08); border-left: 3px solid #38bdf8; padding: 8px 12px; border-radius: 4px; margin-top: 14px; font-size: 12px; color: #e2e8f0;">
            💡 <b>Insight AI:</b> La combinazione tra trend a 200 giorni e indice Fear & Greed a <b>{last_row['FGI_Synthetic']:.1f}</b> segnala una configurazione <b>{cat_name.lower()}</b>, idonea a strategie di prosecuzione del trend con stop-loss ancorati alla SMA 200.
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_fear_and_greed_section(df_fgi: pd.DataFrame, ticker: str = "Azione"):
    """
    Renderizza la sezione completa Fear & Greed in Streamlit:
    - st.markdown("---")
    - st.header("Analisi Quantitativa: Indice Fear & Greed del Titolo")
    - st.columns(5) con st.metric()
    - Grafico storico Plotly a tutta larghezza
    """
    st.markdown("---")
    st.header("Analisi Quantitativa: Indice Fear & Greed del Titolo")

    if df_fgi.empty:
        st.warning("Dati insufficienti per il calcolo dell'Indice Fear & Greed.")
        return

    last_row = df_fgi.iloc[-1]
    prev_row = df_fgi.iloc[-2] if len(df_fgi) > 1 else last_row

    fgi_now = float(last_row['FGI_Synthetic'])
    fgi_prev = float(prev_row['FGI_Synthetic'])
    cat_now, emoji_now, _ = get_fgi_category(fgi_now)

    mom_now = float(last_row['FGI_Momentum'])
    mom_prev = float(prev_row['FGI_Momentum'])

    rsi_now = float(last_row['FGI_RSI'])
    rsi_prev = float(prev_row['FGI_RSI'])

    vol_now = float(last_row['FGI_Volatility'])
    vol_prev = float(prev_row['FGI_Volatility'])

    pres_now = float(last_row['FGI_Volume_Pressure'])
    pres_prev = float(prev_row['FGI_Volume_Pressure'])

    cols = st.columns(5)
    cols[0].metric(
        label="🎯 Market Momentum",
        value=f"{mom_now:.1f}",
        delta=f"{mom_now - mom_prev:+.1f} vs ieri",
        help="Slancio sul prezzo rispetto alla SMA 125 giorni normalizzato 0-100."
    )
    cols[1].metric(
        label="💪 Relative Strength (RSI)",
        value=f"{rsi_now:.1f}",
        delta=f"{rsi_now - rsi_prev:+.1f} vs ieri",
        help="RSI standard a 20 giorni su guadagni e perdite medie (0-100)."
    )
    cols[2].metric(
        label="🛡️ Volatilità Inversa",
        value=f"{vol_now:.1f}",
        delta=f"{vol_now - vol_prev:+.1f} vs ieri",
        help="Rapporto ATR 14 / Media ATR 30 invertito (volatilità esplosiva < 45, piatta > 55)."
    )
    cols[3].metric(
        label="⚖️ Buying Pressure",
        value=f"{pres_now:.1f}%",
        delta=f"{pres_now - pres_prev:+.1f}% vs ieri",
        help="Quota di volume scambiato su candele positive negli ultimi 20 giorni."
    )
    cols[4].metric(
        label="🧭 FGI Sintetico",
        value=f"{fgi_now:.1f} / 100",
        delta=f"{cat_now} {emoji_now}",
        help="Media quantitativa dei 4 indicatori compositi di mercato."
    )

    fig_fgi = create_fear_greed_figure(df_fgi, ticker=ticker)
    clean_config = {
        'modeBarButtonsToRemove': CLEAN_MODEBAR_BUTTONS,
        'displaylogo': False,
        'responsive': True,
        'scrollZoom': True
    }
    st.plotly_chart(fig_fgi, config=clean_config)
