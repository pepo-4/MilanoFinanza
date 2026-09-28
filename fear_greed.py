"""
Modulo per il calcolo e la visualizzazione dell'Indice Fear & Greed (Hackathon Milano Finanza).
Strumento di Analisi Quantitativa per Supporto Decisionale Finanziario.

Indicatori compositi:
1. Market Momentum (Slancio): Scostamento percentuale dalla SMA a 125 giorni normalizzato 0-100.
2. Relative Strength (Forza Relativa): RSI standard a 20 giorni su Avg_Gain e Avg_Loss (0-100).
3. Price Volatility (Volatilità Inversa): ATR 14 giorni rapportato alla media a 30 giorni, invertito su scala 0-100.
4. Buying/Selling Pressure: Volume positivo su 20 giorni rispetto al volume totale (0-100%).
5. Fear & Greed Sintetico (FGI_Synthetic): Media dei 4 indicatori compositi.
"""

from typing import Optional, Tuple
import numpy as np
import pandas as pd
import plotly.graph_objects as go

# Lista dei bottoni inutili di Plotly da rimuovere per un layout pulito
CLEAN_MODEBAR_BUTTONS = [
    'toImage',
    'sendDataToCloud',
    'zoom2d',
    'pan2d',
    'select2d',
    'lasso2d',
    'zoomIn2d',
    'zoomOut2d',
    'autoScale2d',
    'resetScale2d',
    'hoverClosestCartesian',
    'hoverCompareCartesian',
    'toggleSpikelines',
]


def _detect_col(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Cerca una colonna nel DataFrame tra una lista di nomi candidati (case-insensitive)."""
    cols_lower = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def get_fgi_category(val: float) -> Tuple[str, str, str]:
    """
    Ritorna la categoria testuale, emoji e colore CSS/HEX per il valore (0-100):
    - < 20: Extreme Fear (Rosso intenso)
    - 20 - 45: Fear (Arancione)
    - 45 - 55: Neutral (Giallo ambra)
    - 55 - 80: Greed (Verde chiaro)
    - > 80: Extreme Greed (Verde smeraldo)
    """
    if pd.isna(val):
        return "N/D", "❓", "#94A3B8"
    if val < 20:
        return "Extreme Fear", "😱", "#EF4444"
    elif val < 45:
        return "Fear", "😨", "#F97316"
    elif val <= 55:
        return "Neutral", "⚖️", "#EAB308"
    elif val <= 80:
        return "Greed", "🤑", "#22C55E"
    else:
        return "Extreme Greed", "🚀", "#10B981"


def calculate_fear_greed(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prende il DataFrame giornaliero pulito (con open, high, low, close, volume)
    e calcola le colonne storiche dell'Indice Fear & Greed normalizzate tra 0 e 100
    (dove < 45 è Fear, 45-55 è Neutral, > 55 è Greed).

    Parametri
    ---------
    df : pd.DataFrame
        Dati giornalieri contenenti le colonne di prezzo e volume (riconosciute sia
        in formato standard che con i nomi BigQuery es. PRZ_LAST, QUANTITATIVO, DATA_QUOTAZ).

    Ritorna
    -------
    pd.DataFrame
        Copia del DataFrame arricchita con tutti i valori calcolati e la colonna `FGI_Synthetic`.
    """
    data = df.copy()

    # Rilevamento colonne flessibile (standard o BigQuery)
    date_col = _detect_col(data, ['date', 'data_quotaz', 'data', 'datetime', 'timestamp'])
    close_col = _detect_col(data, ['close', 'prz_last', 'prz_rif', 'prz_uff', 'chiusura', 'prezzo_chiusura', 'ultimo'])
    open_col = _detect_col(data, ['open', 'prz_apertura', 'apertura', 'prezzo_apertura', 'p_apertura'])
    high_col = _detect_col(data, ['high', 'prz_max', 'massimo', 'prezzo_max', 'max'])
    low_col = _detect_col(data, ['low', 'prz_min', 'minimo', 'prezzo_min', 'min'])
    volume_col = _detect_col(data, ['volume', 'quantitativo', 'volumi', 'vol', 'vol_scambi', 'quantita'])

    if not close_col:
        raise ValueError("Colonna del prezzo di chiusura non trovata nel DataFrame.")

    # Ordinamento temporale
    if date_col:
        data[date_col] = pd.to_datetime(data[date_col])
        data = data.sort_values(by=date_col).reset_index(drop=True)

    # Conversione numerica
    data[close_col] = pd.to_numeric(data[close_col], errors='coerce')
    if open_col:
        data[open_col] = pd.to_numeric(data[open_col], errors='coerce')
    if high_col:
        data[high_col] = pd.to_numeric(data[high_col], errors='coerce')
    if low_col:
        data[low_col] = pd.to_numeric(data[low_col], errors='coerce')
    if volume_col:
        data[volume_col] = pd.to_numeric(data[volume_col], errors='coerce').fillna(0.0)
    else:
        volume_col = '__synthetic_volume__'
        data[volume_col] = 1.0

    # Ricostruzione high/low se mancanti
    if not high_col and open_col:
        high_col = '__high__'
        data[high_col] = data[[open_col, close_col]].max(axis=1)
    elif not high_col:
        high_col = '__high__'
        data[high_col] = data[close_col]

    if not low_col and open_col:
        low_col = '__low__'
        data[low_col] = data[[open_col, close_col]].min(axis=1)
    elif not low_col:
        low_col = '__low__'
        data[low_col] = data[close_col]

    close = data[close_col]
    high = data[high_col]
    low = data[low_col]
    vol = data[volume_col]

    # --------------------------------------------------------------------------
    # 1. MARKET MOMENTUM (SLANCIO)
    # --------------------------------------------------------------------------
    # SMA a 125 giorni della chiusura e scostamento percentuale: (Close - SMA_125) / SMA_125
    # Normalizzazione: se -20% -> 0, se 0% -> 50, se +20% -> 100
    sma_125 = close.rolling(window=125, min_periods=1).mean()
    mom_pct = (close - sma_125) / sma_125
    # Scaling lineare centrato a 50 con escursione ±20%
    fgi_momentum = np.clip(50.0 + mom_pct * 250.0, 0.0, 100.0)

    data['SMA_125'] = sma_125
    data['Momentum_Pct'] = mom_pct * 100.0
    data['FGI_Momentum'] = fgi_momentum.round(1)

    # --------------------------------------------------------------------------
    # 2. RELATIVE STRENGTH (FORZA RELATIVA - RSI 20)
    # --------------------------------------------------------------------------
    # RSI standard a 20 giorni su Avg_Gain e Avg_Loss (Wilder Smoothing)
    delta = close.diff()
    gain = delta.clip(lower=0.0)
    loss = (-delta).clip(lower=0.0)

    avg_gain = gain.ewm(alpha=1.0 / 20.0, min_periods=20, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / 20.0, min_periods=20, adjust=False).mean()

    rs = avg_gain / avg_loss.replace(0.0, np.nan)
    rsi_20 = 100.0 - (100.0 / (1.0 + rs))
    rsi_20 = rsi_20.fillna(50.0)
    fgi_rsi = np.clip(rsi_20, 0.0, 100.0)

    data['RSI_20'] = rsi_20.round(1)
    data['FGI_RSI'] = fgi_rsi.round(1)

    # --------------------------------------------------------------------------
    # 3. PRICE VOLATILITY (VOLATILITÀ INVERSA)
    # --------------------------------------------------------------------------
    # True Range e ATR a 14 giorni; media dell'ATR a 30 giorni
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr_14 = true_range.rolling(window=14, min_periods=1).mean()
    atr_30_ma = atr_14.rolling(window=30, min_periods=1).mean()

    vol_ratio = (atr_14 / atr_30_ma.replace(0.0, np.nan)).fillna(1.0)
    # Se ATR_14 > ATR_30_MA (rapporto > 1), la volatilità sale -> Paura (verso 0)
    # Se ATR_14 < ATR_30_MA (rapporto < 1), volatilità piatta -> Avidità/Calma (verso 100)
    # Scaling: ratio 0.5 -> 100, ratio 1.0 -> 50, ratio 1.5 -> 0
    fgi_volatility = np.clip(50.0 - (vol_ratio - 1.0) * 100.0, 0.0, 100.0)

    data['True_Range'] = true_range
    data['ATR_14'] = atr_14
    data['ATR_30_MA'] = atr_30_ma
    data['ATR_Ratio'] = vol_ratio.round(2)
    data['FGI_Volatility'] = fgi_volatility.round(1)

    # --------------------------------------------------------------------------
    # 4. BUYING/SELLING PRESSURE
    # --------------------------------------------------------------------------
    # Finestra rolling 20 giorni: Volume Positivo (Close > Close Ieri) / Volume Totale 20g
    pos_vol = np.where(close > prev_close, vol, 0.0)
    rolling_pos_vol = pd.Series(pos_vol, index=data.index).rolling(window=20, min_periods=1).sum()
    rolling_tot_vol = vol.rolling(window=20, min_periods=1).sum()

    pressure_pct = (rolling_pos_vol / rolling_tot_vol.replace(0.0, np.nan)) * 100.0
    pressure_pct = pressure_pct.fillna(50.0)
    fgi_volume_pressure = np.clip(pressure_pct, 0.0, 100.0)

    data['Volume_Positivo'] = pos_vol
    data['FGI_Volume_Pressure'] = fgi_volume_pressure.round(1)

    # --------------------------------------------------------------------------
    # 5. FEAR & GREED SINTETICO
    # --------------------------------------------------------------------------
    # Media dei 4 valori normalizzati sopra calcolati
    fgi_synthetic = (fgi_momentum + fgi_rsi + fgi_volatility + fgi_volume_pressure) / 4.0
    data['FGI_Synthetic'] = fgi_synthetic.round(1)
    data['FGI_Label'] = [get_fgi_category(v)[0] for v in data['FGI_Synthetic']]

    # Standardizzazione colonna data per coerenza
    if date_col and date_col != 'date':
        data['date'] = data[date_col]

    return data


def plot_fear_and_greed_chart(
    df_fgi: pd.DataFrame,
    ticker: str = "Azione",
    theme: str = "plotly_dark"
) -> go.Figure:
    """
    Disegna il grafico storico lineare dell'Indice Sintetico FGI_Synthetic nel tempo,
    con linee tratteggiate orizzontali di soglia a 20 (Extreme Fear) e 80 (Extreme Greed)
    e sovrapposizione in semitrasparenza dei 4 indicatori sorgente.
    """
    date_col = 'date' if 'date' in df_fgi.columns else _detect_col(df_fgi, ['data_quotaz', 'data'])
    x_vals = df_fgi[date_col] if date_col else df_fgi.index

    fig = go.Figure()

    # 1. Fasce di sfondo orizzontali colorate (Zones)
    fig.add_hrect(y0=80, y1=100, fillcolor="rgba(34, 197, 94, 0.10)", layer="below", line_width=0)
    fig.add_hrect(y0=55, y1=80, fillcolor="rgba(34, 197, 94, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=45, y1=55, fillcolor="rgba(234, 179, 8, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=20, y1=45, fillcolor="rgba(249, 115, 22, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=0, y1=20, fillcolor="rgba(239, 68, 68, 0.10)", layer="below", line_width=0)

    # 2. Linee di soglia orizzontali
    fig.add_hline(
        y=80,
        line=dict(color="#22C55E", width=1.5, dash="dash"),
        annotation_text="<b>Extreme Greed (80)</b>",
        annotation_position="top left",
        annotation_font=dict(color="#22C55E", size=10)
    )
    fig.add_hline(
        y=55,
        line=dict(color="rgba(34, 197, 94, 0.4)", width=1, dash="dot"),
        annotation_text="Greed (55)",
        annotation_position="top left",
        annotation_font=dict(color="#86EFAC", size=9)
    )
    fig.add_hline(
        y=50,
        line=dict(color="rgba(148, 163, 184, 0.5)", width=1, dash="dashdot"),
        annotation_text="Neutral (50)",
        annotation_position="bottom left",
        annotation_font=dict(color="#94A3B8", size=9)
    )
    fig.add_hline(
        y=45,
        line=dict(color="rgba(249, 115, 22, 0.4)", width=1, dash="dot"),
        annotation_text="Fear (45)",
        annotation_position="bottom left",
        annotation_font=dict(color="#FCA5A5", size=9)
    )
    fig.add_hline(
        y=20,
        line=dict(color="#EF4444", width=1.5, dash="dash"),
        annotation_text="<b>Extreme Fear (20)</b>",
        annotation_position="bottom left",
        annotation_font=dict(color="#EF4444", size=10)
    )

    # 3. Indicatori sorgente sovrapposti (sottili e semitrasparenti)
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_fgi['FGI_Momentum'],
            mode='lines',
            name='Momentum (SMA 125)',
            line=dict(color='rgba(56, 189, 248, 0.45)', width=1.2, dash='dot'),
            hovertemplate='%{x|%d/%m/%Y}<br>Momentum: %{y:.1f}<extra></extra>'
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_fgi['FGI_RSI'],
            mode='lines',
            name='Forza Relativa (RSI 20)',
            line=dict(color='rgba(168, 85, 247, 0.45)', width=1.2, dash='dot'),
            hovertemplate='%{x|%d/%m/%Y}<br>RSI 20: %{y:.1f}<extra></extra>'
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_fgi['FGI_Volatility'],
            mode='lines',
            name='Volatilità Inversa (ATR)',
            line=dict(color='rgba(245, 158, 11, 0.45)', width=1.2, dash='dot'),
            hovertemplate='%{x|%d/%m/%Y}<br>Volatilità Inversa: %{y:.1f}<extra></extra>'
        )
    )
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_fgi['FGI_Volume_Pressure'],
            mode='lines',
            name='Buying Pressure (Volumi)',
            line=dict(color='rgba(236, 72, 153, 0.45)', width=1.2, dash='dot'),
            hovertemplate='%{x|%d/%m/%Y}<br>Pressione Volumi: %{y:.1f}%<extra></extra>'
        )
    )

    # 4. Traccia principale: Fear & Greed Sintetico (Linea solida con marker cromatico)
    fig.add_trace(
        go.Scatter(
            x=x_vals,
            y=df_fgi['FGI_Synthetic'],
            mode='lines+markers',
            name='🧭 FGI Sintetico',
            line=dict(color='#38BDF8', width=3.0),
            marker=dict(
                size=4,
                color=df_fgi['FGI_Synthetic'],
                colorscale='RdYlGn',
                cmin=0,
                cmax=100,
                showscale=False
            ),
            hovertemplate=(
                '<b>%{x|%d/%m/%Y}</b><br>'
                '🧭 <b>Indice FGI Sintetico: %{y:.1f} / 100</b><br>'
                '<extra></extra>'
            )
        )
    )

    fig.update_layout(
        template=theme,
        title=dict(
            text=f"<b>Storico Indice Fear & Greed (0-100)</b> · {ticker}",
            x=0.01,
            y=0.96,
            font=dict(size=15, color="#F8FAFC")
        ),
        xaxis=dict(
            title_text="Data",
            showgrid=True,
            gridcolor="rgba(51, 65, 85, 0.4)"
        ),
        yaxis=dict(
            title_text="Fear & Greed Index",
            range=[0, 100],
            tickvals=[0, 20, 45, 50, 55, 80, 100],
            ticktext=["0 (Ext. Fear)", "20", "45", "50", "55", "80", "100 (Ext. Greed)"],
            showgrid=True,
            gridcolor="rgba(51, 65, 85, 0.4)"
        ),
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11)
        ),
        margin=dict(l=60, r=40, t=60, b=40),
        height=420
    )

    return fig


def plot_single_indicator(
    df_fgi: pd.DataFrame,
    indicator: str = "momentum",
    ticker: str = "Azione",
    theme: str = "plotly_dark"
) -> go.Figure:
    """
    Estrae e disegna un grafico standalone dedicato per UNO solo dei 4 indicatori.

    Parametri
    ---------
    df_fgi : pd.DataFrame
        DataFrame restituito da calculate_fear_greed(df).
    indicator : str
        Uno tra: 'momentum' (Slancio), 'strength' o 'rsi' (Forza Relativa),
        'volatility' (Volatilità Inversa), 'pressure' o 'volume' (Pressione Acquisti).
    ticker : str
        Nome o ticker dell'azione per il titolo.
    """
    key = indicator.lower().strip()
    date_col = 'date' if 'date' in df_fgi.columns else _detect_col(df_fgi, ['data_quotaz', 'data'])
    x_vals = df_fgi[date_col] if date_col else df_fgi.index

    fig = go.Figure()

    if key in ['momentum', 'slancio', 'sma125']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Momentum'],
            mode='lines', name='Market Momentum (0-100)',
            line=dict(color='#38BDF8', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>Momentum: %{y:.1f} / 100<extra></extra>'
        ))
        title = f"<b>Market Momentum (Slancio su SMA 125)</b> · {ticker}"
        y_title = "Score Momentum (0-100)"

    elif key in ['strength', 'rsi', 'rsi20', 'forza']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_RSI'],
            mode='lines', name='RSI 20 giorni',
            line=dict(color='#A855F7', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>RSI (20g): %{y:.1f}<extra></extra>'
        ))
        title = f"<b>Relative Strength (RSI a 20 giorni)</b> · {ticker}"
        y_title = "RSI (0-100)"

    elif key in ['volatility', 'volatilita', 'atr']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Volatility'],
            mode='lines', name='Volatilità Inversa',
            line=dict(color='#F59E0B', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>Volatilità Inversa: %{y:.1f} / 100<extra></extra>'
        ))
        title = f"<b>Price Volatility (Volatilità Inversa ATR 14 vs 30 MA)</b> · {ticker}"
        y_title = "Score Volatilità (0-100)"

    elif key in ['pressure', 'pressione', 'volume', 'buying_pressure']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Volume_Pressure'],
            mode='lines', name='Buying Pressure %',
            line=dict(color='#EC4899', width=2.5),
            fill='tozeroy',
            fillcolor='rgba(236, 72, 153, 0.1)',
            hovertemplate='%{x|%d/%m/%Y}<br>Buying Pressure: %{y:.1f}%<extra></extra>'
        ))
        title = f"<b>Buying/Selling Pressure (Flusso Volumi 20g)</b> · {ticker}"
        y_title = "% Volume su Sedute Positive"
    else:
        raise ValueError(f"Indicatore sconosciuto: '{indicator}'. Scegli tra: momentum, strength, volatility, pressure.")

    # Soglie orizzontali standard 20, 50, 80
    fig.add_hline(y=80, line=dict(color="#22C55E", width=1, dash="dash"), annotation_text="Greed (80)", annotation_position="top left")
    fig.add_hline(y=50, line=dict(color="#94A3B8", width=1, dash="dot"), annotation_text="Neutral (50)", annotation_position="bottom left")
    fig.add_hline(y=20, line=dict(color="#EF4444", width=1, dash="dash"), annotation_text="Fear (20)", annotation_position="bottom left")

    fig.update_layout(
        template=theme,
        title=dict(text=title, x=0.01, y=0.96, font=dict(size=14, color="#F8FAFC")),
        xaxis=dict(title_text="Data", showgrid=True, gridcolor="rgba(51, 65, 85, 0.4)"),
        yaxis=dict(title_text=y_title, range=[0, 100], showgrid=True, gridcolor="rgba(51, 65, 85, 0.4)"),
        margin=dict(l=60, r=40, t=50, b=40),
        height=320
    )
    return fig


def render_fear_and_greed_streamlit(df_fgi: pd.DataFrame, ticker: str = "Azione"):
    """
    Renderizza la sezione completa Fear & Greed in un'applicazione Streamlit:
    - st.markdown("---")
    - st.header("Analisi Quantitativa: Indice Fear & Greed del Titolo")
    - st.columns(5) con st.metric() per i 4 indicatori e l'Indice Sintetico
    - Grafico storico lineare Plotly dell'indice e delle 4 componenti
    """
    import streamlit as st

    st.markdown("---")
    st.header("Analisi Quantitativa: Indice Fear & Greed del Titolo")

    if df_fgi.empty:
        st.warning("Dati insufficienti per il calcolo dell'Indice Fear & Greed.")
        return

    # Estrazione valori odierni e confronto con giorno precedente
    last_row = df_fgi.iloc[-1]
    prev_row = df_fgi.iloc[-2] if len(df_fgi) > 1 else last_row

    fgi_now = float(last_row['FGI_Synthetic'])
    fgi_prev = float(prev_row['FGI_Synthetic'])
    delta_fgi = fgi_now - fgi_prev
    cat_now, emoji_now, color_now = get_fgi_category(fgi_now)

    mom_now = float(last_row['FGI_Momentum'])
    mom_prev = float(prev_row['FGI_Momentum'])

    rsi_now = float(last_row['FGI_RSI'])
    rsi_prev = float(prev_row['FGI_RSI'])

    vol_now = float(last_row['FGI_Volatility'])
    vol_prev = float(prev_row['FGI_Volatility'])

    pres_now = float(last_row['FGI_Volume_Pressure'])
    pres_prev = float(prev_row['FGI_Volume_Pressure'])

    # 5 Colonne con st.metric()
    cols = st.columns(5)

    with cols[0]:
        st.metric(
            label="🎯 Market Momentum",
            value=f"{mom_now:.1f}",
            delta=f"{mom_now - mom_prev:+.1f} vs ieri",
            help="Slancio sul prezzo rispetto alla SMA 125 giorni normalizzato 0-100."
        )

    with cols[1]:
        st.metric(
            label="💪 Relative Strength (RSI)",
            value=f"{rsi_now:.1f}",
            delta=f"{rsi_now - rsi_prev:+.1f} vs ieri",
            help="RSI standard a 20 giorni su guadagni e perdite medie (0-100)."
        )

    with cols[2]:
        st.metric(
            label="🛡️ Volatilità Inversa",
            value=f"{vol_now:.1f}",
            delta=f"{vol_now - vol_prev:+.1f} vs ieri",
            help="Rapporto ATR 14 / Media ATR 30 invertito (volatilità esplosiva < 45, piatta > 55)."
        )

    with cols[3]:
        st.metric(
            label="⚖️ Buying Pressure",
            value=f"{pres_now:.1f}%",
            delta=f"{pres_now - pres_prev:+.1f}% vs ieri",
            help="Quota di volume scambiato su candele positive negli ultimi 20 giorni."
        )

    with cols[4]:
        st.metric(
            label="🧭 FGI Sintetico",
            value=f"{fgi_now:.1f} / 100",
            delta=f"{cat_now} {emoji_now}",
            help="Media quantitativa dei 4 indicatori compositi di mercato."
        )

    # Grafico storico Plotly
    fig_fgi = plot_fear_and_greed_chart(df_fgi, ticker=ticker)
    clean_config = {
        'modeBarButtonsToRemove': CLEAN_MODEBAR_BUTTONS,
        'displaylogo': False,
        'responsive': True,
        'scrollZoom': True
    }
    st.plotly_chart(fig_fgi, use_container_width=True, config=clean_config)
