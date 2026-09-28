"""
Modulo per la visualizzazione e analisi grafica delle azioni (Hackathon Milano Finanza).
Strumento di Supporto Decisionale per Analisi Finanziaria.

Funzionalità principali:
- Riconoscimento automatico colonne di BigQuery (DATA_QUOTAZ, PRZ_APERTURA, PRZ_LAST, PRZ_MAX, PRZ_MIN, QUANTITATIVO).
- Mappatura ticker comuni (es. 'UCG' / 'UNICREDIT' -> COD_AZIONE 'CRIT').
- Estrazione sicura da BigQuery conforme a CLAUDE.md con Caching locale in `data/`.
- Aggregazione settimanale (timeframe='1W', ~260 candele per 5 anni) o giornaliera (timeframe='1D').
- Calcolo SMA 200 gg continua e SMA 50 gg.
- Indicatori Golden Cross (stellina dorata sotto la candela) e Death Cross (X rossa sopra la candela) con tooltip esplicativi.
- Toggle 'Grafico Pulito' (isola solo il prezzo spegnendo volumi e indicatori).
- Checkbox per attivare/disattivare ogni singolo elemento tecnico (SMA 200, SMA 50, Volumi, Segnali Cross).
- Rimozione di tutti i bottoni inutili dalla modeBar (download png, zoom, pan, select, autoscale, home, ecc.).
- Righello di Misurazione 'Ctrl + Drag & Drop' STRETTAMENTE ANCORATO AI PREZZI REALI DELLE CANDELE:
  aggancia magneticamente i prezzi (Chiusura, Minimo, Massimo) e calcola variazione %, delta prezzo e durata.
"""

from datetime import datetime
import os
import json
import webbrowser
from typing import Optional, Tuple
import pandas as pd

try:
    from fear_greed import (
        calculate_fear_greed,
        plot_fear_and_greed_chart,
        plot_single_indicator,
        render_fear_and_greed_streamlit,
        get_fgi_category,
    )
except ImportError:
    pass

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False

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

# Bottoni inutili da rimuovere dalla barra degli strumenti di Plotly
CLEAN_MODEBAR_BUTTONS_TO_REMOVE = [
    'toImage',           # Download plot as png
    'sendDataToCloud',   # Share chart
    'zoom2d',            # Zoom
    'pan2d',             # Pan
    'select2d',          # Box select
    'lasso2d',           # Lasso select
    'zoomIn2d',          # Zoom in
    'zoomOut2d',         # Zoom out
    'autoScale2d',       # Autoscale
    'resetScale2d',      # Tasto home / reset scale
    'hoverClosestCartesian',
    'hoverCompareCartesian',
    'toggleSpikelines',
]


# ==============================================================================
# 1. MAPPATURA E PREPARAZIONE DATI CON SEGNALI CROSS
# ==============================================================================

def _detect_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
    """Cerca una colonna nel DataFrame tra una lista di nomi candidati (case-insensitive)."""
    cols_lower = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        if candidate.lower() in cols_lower:
            return cols_lower[candidate.lower()]
    return None


def prepare_stock_data(
    df: pd.DataFrame,
    ticker: Optional[str] = None,
    years: int = 5,
    ma_window: int = 200,
    timeframe: str = "1W",
    date_col: Optional[str] = None,
    open_col: Optional[str] = None,
    close_col: Optional[str] = None,
    volume_col: Optional[str] = None,
    high_col: Optional[str] = None,
    low_col: Optional[str] = None,
    ticker_col: Optional[str] = None,
) -> pd.DataFrame:
    """
    Pulisce, calcola indicatori tecnici (SMA 200, SMA 50, Golden/Death Cross)
    e aggrega i dati dell'azione a livello settimanale (1W) o giornaliero (1D).
    """
    data = df.copy()

    # Rilevamento automatico colonne
    date_col = date_col or _detect_column(data, ['data_quotaz', 'data', 'date', 'datetime', 'timestamp'])
    open_col = open_col or _detect_column(data, ['prz_apertura', 'apertura', 'prezzo_apertura', 'open', 'p_apertura'])
    close_col = close_col or _detect_column(data, ['prz_last', 'prz_rif', 'prz_uff', 'chiusura', 'prezzo_chiusura', 'close', 'ultimo'])
    volume_col = volume_col or _detect_column(data, ['quantitativo', 'volumi', 'volume', 'vol', 'vol_scambi', 'quantita'])
    high_col = high_col or _detect_column(data, ['prz_max', 'massimo', 'prezzo_max', 'high', 'max'])
    low_col = low_col or _detect_column(data, ['prz_min', 'minimo', 'prezzo_min', 'low', 'min'])
    ticker_col = ticker_col or _detect_column(data, ['cod_azione', 'des_azione', 'ticker', 'symbol', 'cod_isin', 'isin', 'titolo'])

    if not date_col:
        raise ValueError("Colonna della data non trovata. Specificare `date_col` esplicitamente.")
    if not close_col:
        raise ValueError("Colonna del prezzo di chiusura non trovata. Specificare `close_col` esplicitamente.")

    # Filtro eventuale su ticker / cod_azione
    if ticker and ticker_col and ticker_col in data.columns:
        cod_target = TICKER_MAP.get(str(ticker).upper(), str(ticker).upper())
        matches = (
            (data[ticker_col].astype(str).str.upper() == str(ticker).upper()) |
            (data[ticker_col].astype(str).str.upper() == cod_target)
        )
        if matches.any():
            data = data[matches]

    # Conversione data e ordinamento
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(by=date_col).reset_index(drop=True)

    # Conversione colonne numeriche
    numeric_cols = [c for c in [open_col, close_col, high_col, low_col, volume_col] if c and c in data.columns]
    for c in numeric_cols:
        data[c] = pd.to_numeric(data[c], errors='coerce')

    if not high_col and open_col:
        data['__high__'] = data[[open_col, close_col]].max(axis=1)
        high_col = '__high__'
    if not low_col and open_col:
        data['__low__'] = data[[open_col, close_col]].min(axis=1)
        low_col = '__low__'

    # Calcolo SMA 200 e SMA 50 giorni sui dati giornalieri PRIMA di qualsiasi aggregazione
    data['ma_50'] = data[close_col].rolling(window=50, min_periods=1).mean()
    data['ma_200'] = data[close_col].rolling(window=ma_window, min_periods=1).mean()

    # Aggregazione temporale (Settimanale vs Giornaliero)
    is_weekly = str(timeframe).upper() in ['1W', 'W', 'WEEKLY', 'SETTIMANALE']

    if is_weekly:
        agg_rules = {close_col: 'last', 'ma_50': 'last', 'ma_200': 'last'}
        if open_col:
            agg_rules[open_col] = 'first'
        if high_col:
            agg_rules[high_col] = 'max'
        if low_col:
            agg_rules[low_col] = 'min'
        if volume_col:
            agg_rules[volume_col] = 'sum'

        # Resample W-FRI (settimane di trading con chiusura venerdì)
        resampled = data.set_index(date_col).resample('W-FRI').agg(agg_rules)
        resampled = resampled.dropna(subset=[close_col]).reset_index()
        data = resampled

    # Filtro sugli ultimi N anni
    max_date = data[date_col].max()
    cutoff_date = max_date - pd.DateOffset(years=years)
    filtered_data = data[data[date_col] >= cutoff_date].copy().reset_index(drop=True)

    # Rilevamento segnali Golden Cross e Death Cross
    diff = filtered_data['ma_50'] - filtered_data['ma_200']
    prev_diff = diff.shift(1)
    filtered_data['is_golden_cross'] = (diff > 0) & (prev_diff <= 0)
    filtered_data['is_death_cross'] = (diff < 0) & (prev_diff >= 0)

    # Standardizzazione finale nomi colonne
    rename_dict = {
        date_col: 'date',
        close_col: 'close',
    }
    if open_col:
        rename_dict[open_col] = 'open'
    if volume_col:
        rename_dict[volume_col] = 'volume'
    if high_col:
        rename_dict[high_col] = 'high'
    if low_col:
        rename_dict[low_col] = 'low'

    return filtered_data.rename(columns=rename_dict)


# ==============================================================================
# 2. GRAFICO INTERATTIVO PLOTLY CON SEGNALI E CONTROLLI INTEGRATI
# ==============================================================================

def plot_stock_plotly(
    df: pd.DataFrame,
    ticker: str = "Azione",
    years: int = 5,
    ma_window: int = 200,
    timeframe: str = "1W",
    theme: str = "plotly_dark",
    remove_weekends: Optional[bool] = None,
    use_candlesticks: bool = True,
    **prep_kwargs,
):
    """
    Crea un grafico finanziario interattivo pulito e conforme ai requisiti:
    - Bottoni inutili rimossi dalla modeBar.
    - Candele (OHLC) settimanali o giornaliere.
    - SMA 200 gg (visibile) e SMA 50 gg (calcolata ma disattivata di default).
    - Marcatori Golden Cross (stellina dorata sotto la candela) e Death Cross (X rossa sopra).
    - Subplot volumi di scambio.
    - Pulsanti integrati per 'Grafico Pulito' e 'Vista Completa'.
    """
    if not HAS_PLOTLY:
        raise ImportError("Plotly non è installato. Installa con `pip install plotly`.")

    is_weekly = str(timeframe).upper() in ['1W', 'W', 'WEEKLY', 'SETTIMANALE']
    freq_label = "Settimanale" if is_weekly else "Giornaliero"

    clean_df = prepare_stock_data(
        df,
        ticker=ticker,
        years=years,
        ma_window=ma_window,
        timeframe=timeframe,
        **prep_kwargs
    )

    # Creazione subplot: 2 righe (Prezzo 72%, Volumi 28%)
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.72, 0.28],
        subplot_titles=(
            f"<b>{ticker}</b> - Andamento {freq_label} ({len(clean_df)} candele, {years} anni)",
            f"<b>Volumi di Scambio ({freq_label})</b>"
        )
    )

    has_open = 'open' in clean_df.columns
    has_high = 'high' in clean_df.columns
    has_low = 'low' in clean_df.columns

    # --------------------------------------------------------------------------
    # TRACCIA 0: Candele del Prezzo
    # --------------------------------------------------------------------------
    if use_candlesticks and has_open:
        high_vals = clean_df['high'] if has_high else clean_df[['open', 'close']].max(axis=1)
        low_vals = clean_df['low'] if has_low else clean_df[['open', 'close']].min(axis=1)

        fig.add_trace(
            go.Candlestick(
                x=clean_df['date'],
                open=clean_df['open'],
                high=high_vals,
                low=low_vals,
                close=clean_df['close'],
                name="Candele Prezzo",
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a',
                decreasing_fillcolor='#ef5350',
                text=[f"Settimana conclusa: {d.strftime('%d/%m/%Y')}" for d in clean_df['date']] if is_weekly else None,
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=clean_df['date'],
                y=clean_df['close'],
                mode='lines',
                name='Prezzo Chiusura',
                line=dict(color='#2962FF', width=2.0),
                hovertemplate='%{x|%d/%m/%Y}<br>Chiusura: €%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # --------------------------------------------------------------------------
    # TRACCIA 1: Media Mobile 200 giorni (Attiva di default)
    # --------------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=clean_df['date'],
            y=clean_df['ma_200'],
            mode='lines',
            name="SMA 200 gg",
            line=dict(color='#FFA500', width=2.2),
            hovertemplate='SMA 200 gg: €%{y:.2f}<extra></extra>',
            visible=True
        ),
        row=1, col=1
    )

    # --------------------------------------------------------------------------
    # TRACCIA 2: Media Mobile 50 giorni (Disattivata di default per non sporcare)
    # --------------------------------------------------------------------------
    fig.add_trace(
        go.Scatter(
            x=clean_df['date'],
            y=clean_df['ma_50'],
            mode='lines',
            name="SMA 50 gg",
            line=dict(color='#00E5FF', width=1.8, dash='dot'),
            hovertemplate='SMA 50 gg: €%{y:.2f}<extra></extra>',
            visible='legendonly'  # <-- Non disegnata di default, attivabile con un click
        ),
        row=1, col=1
    )

    # --------------------------------------------------------------------------
    # TRACCIA 3: Golden Cross Marker (Stellina Dorata SOTTO la candela)
    # --------------------------------------------------------------------------
    golden_df = clean_df[clean_df['is_golden_cross']]
    if not golden_df.empty:
        golden_y = golden_df['low'] * 0.96 if has_low else golden_df['close'] * 0.96
        golden_hover = [
            f"<b>🌟 GOLDEN CROSS RIALZISTA</b><br>"
            f"Data: {d.strftime('%d/%m/%Y')}<br>"
            f"Prezzo: €{c:.2f}<br>"
            f"SMA 50 gg (€{m50:.2f}) ha superato al rialzo la SMA 200 gg (€{m200:.2f}).<br>"
            f"<i>Segnale tecnico di potenziale inversione o rafforzamento rialzista.</i>"
            for d, c, m50, m200 in zip(golden_df['date'], golden_df['close'], golden_df['ma_50'], golden_df['ma_200'])
        ]
        fig.add_trace(
            go.Scatter(
                x=golden_df['date'],
                y=golden_y,
                mode='markers',
                marker=dict(symbol='star', size=16, color='#FFD700', line=dict(color='#000000', width=1)),
                name="🌟 Golden Cross",
                hovertext=golden_hover,
                hoverinfo='text',
                visible='legendonly'  # Opzionale: nascosto di default
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], mode='markers', name="🌟 Golden Cross", visible='legendonly'), row=1, col=1)

    # --------------------------------------------------------------------------
    # TRACCIA 4: Death Cross Marker (X Rossa SOPRA la candela)
    # --------------------------------------------------------------------------
    death_df = clean_df[clean_df['is_death_cross']]
    if not death_df.empty:
        death_y = death_df['high'] * 1.04 if has_high else death_df['close'] * 1.04
        death_hover = [
            f"<b>⚠️ DEATH CROSS RIBASSISTA</b><br>"
            f"Data: {d.strftime('%d/%m/%Y')}<br>"
            f"Prezzo: €{c:.2f}<br>"
            f"SMA 50 gg (€{m50:.2f}) ha tagliato al ribasso la SMA 200 gg (€{m200:.2f}).<br>"
            f"<i>Segnale di allerta: possibile avvio di una fase correttiva o trend ribassista.</i>"
            for d, c, m50, m200 in zip(death_df['date'], death_df['close'], death_df['ma_50'], death_df['ma_200'])
        ]
        fig.add_trace(
            go.Scatter(
                x=death_df['date'],
                y=death_y,
                mode='markers',
                marker=dict(symbol='x', size=14, color='#FF1744', line=dict(width=3, color='#FF1744')),
                name="⚠️ Death Cross",
                hovertext=death_hover,
                hoverinfo='text',
                visible='legendonly'  # Opzionale: nascosto di default
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(go.Scatter(x=[], y=[], mode='markers', name="⚠️ Death Cross", visible='legendonly'), row=1, col=1)

    # --------------------------------------------------------------------------
    # TRACCIA 5: Volumi di Scambio
    # --------------------------------------------------------------------------
    if 'volume' in clean_df.columns:
        if has_open:
            vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(clean_df['close'], clean_df['open'])]
        else:
            vol_colors = ['#26a69a' if clean_df['close'].iloc[i] >= clean_df['close'].iloc[max(0, i - 1)] else '#ef5350'
                          for i in range(len(clean_df))]

        fig.add_trace(
            go.Bar(
                x=clean_df['date'],
                y=clean_df['volume'],
                marker_color=vol_colors,
                name="Volumi",
                hovertemplate='%{x|%d/%m/%Y}<br>Volume: %{y:,.0f}<extra></extra>',
                visible=True
            ),
            row=2, col=1
        )

    # --------------------------------------------------------------------------
    # PULSANTI TOGGLE NATIVI 'GRAFICO PULITO' & 'VISTA COMPLETA'
    # --------------------------------------------------------------------------
    updatemenus = [
        dict(
            type="buttons",
            direction="left",
            active=0,
            x=0.0,
            y=1.12,
            xanchor="left",
            yanchor="top",
            bgcolor="rgba(30, 41, 59, 0.9)",
            bordercolor="#475569",
            borderwidth=1,
            font=dict(color="#F1F5F9", size=11),
            buttons=[
                dict(
                    label="📊 Vista Default (Prezzo, SMA 200, Volumi)",
                    method="update",
                    args=[{"visible": [True, True, 'legendonly', 'legendonly', 'legendonly', True]}],
                ),
                dict(
                    label="🌟 Tutti gli Indicatori",
                    method="update",
                    args=[{"visible": [True, True, True, True, True, True]}],
                ),
                dict(
                    label="🧹 Grafico Pulito (Solo Prezzo)",
                    method="update",
                    args=[{"visible": [True, False, False, False, False, False]}],
                ),
            ]
        )
    ]

    # Layout finale
    fig.update_layout(
        template=theme,
        hovermode='x unified',
        updatemenus=updatemenus,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1,
            itemclick="toggle",
            itemdoubleclick="toggleothers"
        ),
        margin=dict(l=60, r=40, t=80, b=40),
        xaxis_rangeslider_visible=False,
    )

    fig.update_yaxes(title_text="Prezzo (€)", row=1, col=1)
    fig.update_yaxes(title_text="Volume", row=2, col=1)
    fig.update_xaxes(title_text="Data", row=2, col=1)

    if remove_weekends is None:
        remove_weekends = not is_weekly
    if remove_weekends:
        fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])

    return fig


# ==============================================================================
# 3. GENERATORE APPLICAZIONE DECISIONALE CON ANCORAGGIO REALE AI PREZZI
# ==============================================================================

def generate_decision_support_app(
    fig,
    ticker: str = "Azione",
    output_html: str = "stock_analysis.html",
    auto_open: bool = True
) -> str:
    """
    Genera un'interfaccia web completa da 'Supporto Decisionale':
    1. Rimuove tutti i bottoni inutili della modeBar.
    2. Checkbox per attivare/disattivare SMA 200, SMA 50, Volumi, Segnali Cross.
    3. Interruttore 'Grafico Pulito' a 1 click per isolare il prezzo.
    4. RIGHELLO ANCORATO AI PREZZI DI BORSA (TradingView Style):
       - Aggancio magnetico istantaneo ai prezzi reali della candela (Chiusura, Minimo, Massimo).
       - Zero coordinate arbitrarie: le quote iniziali e finali riflettono fedelmente i dati di mercato.
       - Calcolo automatico di variazione percentuale, guadagno/perdita in euro e numero di candele.
    """
    plot_json = fig.to_json()

    # Estrazione delle candele reali direttamente dalla prima traccia del grafico
    trace0 = fig.data[0]
    dates = [str(x)[:10] for x in trace0.x]
    closes = [round(float(c), 3) for c in trace0.close]
    opens = [round(float(o), 3) for o in (trace0.open if hasattr(trace0, 'open') and trace0.open is not None else trace0.close)]
    highs = [round(float(h), 3) for h in (trace0.high if hasattr(trace0, 'high') and trace0.high is not None else trace0.close)]
    lows = [round(float(l), 3) for l in (trace0.low if hasattr(trace0, 'low') and trace0.low is not None else trace0.close)]

    candles_list = [
        {'date': d, 'open': o, 'high': h, 'low': l, 'close': c}
        for d, o, h, l, c in zip(dates, opens, highs, lows, closes)
    ]
    candles_json = json.dumps(candles_list)

    html_template = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Supporto Decisionale Finanziario - {ticker}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: #0b1120;
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
        }}
        header {{
            background: rgba(15, 23, 42, 0.95);
            border-bottom: 1px solid #1e293b;
            padding: 10px 20px;
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            backdrop-filter: blur(8px);
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .brand-icon {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            width: 32px;
            height: 32px;
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 16px;
        }}
        .brand-title {{
            font-size: 16px;
            font-weight: 700;
            color: #ffffff;
        }}
        .brand-subtitle {{
            font-size: 11px;
            color: #94a3b8;
            font-weight: 500;
        }}
        .control-panel {{
            display: flex;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
            background: #1e293b;
            padding: 5px 12px;
            border-radius: 10px;
            border: 1px solid #334155;
        }}
        .control-label {{
            font-size: 12px;
            font-weight: 600;
            color: #cbd5e1;
            display: flex;
            align-items: center;
            gap: 6px;
            cursor: pointer;
            user-select: none;
            padding: 4px 6px;
            border-radius: 6px;
            transition: all 0.15s ease;
        }}
        .control-label:hover {{
            background: #334155;
            color: #ffffff;
        }}
        .control-label input[type="checkbox"] {{
            accent-color: #3b82f6;
            cursor: pointer;
            width: 15px;
            height: 15px;
        }}
        .divider {{
            width: 1px;
            height: 20px;
            background: #475569;
        }}
        .btn-clean {{
            background: #334155;
            color: #f1f5f9;
            border: 1px solid #475569;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}
        .btn-clean:hover {{
            background: #475569;
        }}
        .btn-clean.active {{
            background: #0ea5e9;
            border-color: #38bdf8;
            color: white;
            box-shadow: 0 0 10px rgba(14, 165, 233, 0.4);
        }}
        .btn-ruler {{
            background: #1e293b;
            color: #38bdf8;
            border: 1px solid #0284c7;
            padding: 5px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            transition: all 0.2s;
        }}
        .btn-ruler:hover {{
            background: #0369a1;
            color: white;
        }}
        .btn-ruler.active {{
            background: #0284c7;
            color: white;
            box-shadow: 0 0 10px rgba(2, 132, 199, 0.5);
        }}
        .info-bar {{
            background: #172554;
            border-bottom: 1px solid #1e3a8a;
            padding: 6px 20px;
            font-size: 12px;
            color: #93c5fd;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .ruler-key {{
            background: #1e40af;
            color: #ffffff;
            padding: 1px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-weight: 600;
        }}
        #chart-wrapper {{
            flex: 1;
            position: relative;
            width: 100%;
            height: calc(100vh - 90px);
        }}
        #stock-chart {{
            width: 100%;
            height: 100%;
        }}
        /* Livello SVG del Righello ancorato */
        .ruler-svg-layer {{
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 40;
        }}
        .ruler-rect.pos-box {{
            fill: rgba(38, 166, 154, 0.16);
            stroke: #26a69a;
            stroke-width: 1.5;
            stroke-dasharray: 4,3;
        }}
        .ruler-rect.neg-box {{
            fill: rgba(239, 83, 80, 0.16);
            stroke: #ef5350;
            stroke-width: 1.5;
            stroke-dasharray: 4,3;
        }}
        .ruler-line.pos-line {{
            stroke: #26a69a;
            stroke-width: 2.2;
        }}
        .ruler-line.neg-line {{
            stroke: #ef5350;
            stroke-width: 2.2;
        }}
        .ruler-dot.pos-dot {{
            fill: #26a69a;
            stroke: #ffffff;
            stroke-width: 2;
        }}
        .ruler-dot.neg-dot {{
            fill: #ef5350;
            stroke: #ffffff;
            stroke-width: 2;
        }}
        .ruler-hover-dot {{
            fill: #38bdf8;
            stroke: #ffffff;
            stroke-width: 2;
            filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.8));
            transition: all 0.04s ease-out;
        }}
        .hover-price-tag {{
            position: absolute;
            background: rgba(15, 23, 42, 0.95);
            color: #38bdf8;
            font-size: 11px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 4px;
            border: 1px solid #38bdf8;
            pointer-events: none;
            z-index: 55;
            display: none;
            white-space: nowrap;
            box-shadow: 0 4px 10px rgba(0,0,0,0.5);
            transform: translate(-50%, -130%);
        }}
        .measure-badge {{
            position: absolute;
            background: rgba(15, 23, 42, 0.96);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 10px 14px;
            pointer-events: none;
            z-index: 60;
            display: none;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
            backdrop-filter: blur(8px);
            min-width: 230px;
            line-height: 1.45;
        }}
    </style>
</head>
<body>

    <header>
        <div class="brand">
            <div class="brand-icon">📈</div>
            <div>
                <div class="brand-title">{ticker}</div>
                <div class="brand-subtitle">Supporto Decisionale Finanziario · Ultimi 5 Anni</div>
            </div>
        </div>

        <div class="control-panel">
            <label class="control-label">
                <input type="checkbox" id="chk-sma200" checked onchange="toggleTrace(1, this.checked)">
                🟡 SMA 200 gg
            </label>

            <label class="control-label">
                <input type="checkbox" id="chk-volume" checked onchange="toggleTrace(5, this.checked)">
                📊 Volumi
            </label>

            <div class="divider"></div>

            <label class="control-label">
                <input type="checkbox" id="chk-sma50" onchange="toggleTrace(2, this.checked)">
                🔵 SMA 50 gg (Opz.)
            </label>

            <label class="control-label">
                <input type="checkbox" id="chk-signals" onchange="toggleSignals(this.checked)">
                🌟 Segnali Cross (Opz.)
            </label>

            <div class="divider"></div>

            <button class="btn-clean" id="btn-clean-mode" onclick="toggleCleanMode()">
                <span>🧹</span> Grafico Pulito
            </button>

            <button class="btn-ruler" id="btn-toggle-ruler" onclick="toggleRulerMode()">
                <span>📏</span> Misura Prezzo
            </button>
        </div>
    </header>

    <div class="info-bar">
        <div>
            🎯 <b>Ancoraggio Automatico ai Prezzi:</b> Tieni premuto <span class="ruler-key">Ctrl</span> (o attiva <b>Misura Prezzo</b>) e <b>trascina il mouse</b>. Il punto di inizio e fine si aggancia <b>esattamente ai prezzi reali</b> della candela (Chiusura / Minimo / Massimo).
        </div>
        <div>
            Premi <span class="ruler-key">ESC</span> o clicca altrove per cancellare la misura.
        </div>
    </div>

    <div id="chart-wrapper">
        <svg id="ruler-svg" class="ruler-svg-layer">
            <rect id="ruler-rect" class="ruler-rect" style="display:none;"></rect>
            <line id="ruler-line" class="ruler-line" style="display:none;"></line>
            <circle id="ruler-start-dot" class="ruler-dot" r="5" style="display:none;"></circle>
            <circle id="ruler-end-dot" class="ruler-dot" r="5" style="display:none;"></circle>
            <circle id="ruler-hover-dot" class="ruler-hover-dot" r="6" style="display:none;"></circle>
        </svg>

        <div id="hover-price-tag" class="hover-price-tag"></div>
        <div id="measure-badge" class="measure-badge"></div>
        <div id="stock-chart"></div>
    </div>

    <script>
        var figData = {plot_json};
        var candleData = {candles_json};
        var plotDiv = document.getElementById('stock-chart');

        // Configurazione pulita: rimossi tutti i bottoni inutili richiesti
        var cleanConfig = {{
            modeBarButtonsToRemove: {json.dumps(CLEAN_MODEBAR_BUTTONS_TO_REMOVE)},
            displaylogo: false,
            responsive: true,
            scrollZoom: true
        }};

        // Render Plotly
        Plotly.newPlot(plotDiv, figData.data, figData.layout, cleanConfig);

        // ---------------------------------------------------------------------
        // GESTIONE CHECKBOX & TOGGLE
        // ---------------------------------------------------------------------
        function toggleTrace(traceIndex, isVisible) {{
            Plotly.restyle(plotDiv, {{ visible: isVisible ? true : 'legendonly' }}, [traceIndex]);
            syncCleanButtonState();
        }}

        function toggleSignals(isVisible) {{
            Plotly.restyle(plotDiv, {{ visible: isVisible ? true : 'legendonly' }}, [3, 4]);
            syncCleanButtonState();
        }}

        var isCleanModeActive = false;
        function toggleCleanMode() {{
            isCleanModeActive = !isCleanModeActive;
            var btn = document.getElementById('btn-clean-mode');

            if (isCleanModeActive) {{
                btn.classList.add('active');
                btn.innerHTML = '<span>✨</span> Mostra Default';

                document.getElementById('chk-sma200').checked = false;
                document.getElementById('chk-sma50').checked = false;
                document.getElementById('chk-signals').checked = false;
                document.getElementById('chk-volume').checked = false;

                Plotly.restyle(plotDiv, {{ visible: [true, 'legendonly', 'legendonly', 'legendonly', 'legendonly', 'legendonly'] }});
            }} else {{
                btn.classList.remove('active');
                btn.innerHTML = '<span>🧹</span> Grafico Pulito';

                document.getElementById('chk-sma200').checked = true;
                document.getElementById('chk-volume').checked = true;
                document.getElementById('chk-sma50').checked = false;
                document.getElementById('chk-signals').checked = false;

                Plotly.restyle(plotDiv, {{ visible: [true, true, 'legendonly', 'legendonly', 'legendonly', true] }});
            }}
        }}

        function syncCleanButtonState() {{
            var hasExtras = document.getElementById('chk-sma200').checked ||
                            document.getElementById('chk-sma50').checked ||
                            document.getElementById('chk-signals').checked ||
                            document.getElementById('chk-volume').checked;
            var btn = document.getElementById('btn-clean-mode');
            if (hasExtras && isCleanModeActive) {{
                isCleanModeActive = false;
                btn.classList.remove('active');
                btn.innerHTML = '<span>🧹</span> Grafico Pulito';
            }}
        }}

        var isRulerModeBtnActive = false;
        function toggleRulerMode() {{
            isRulerModeBtnActive = !isRulerModeBtnActive;
            var btn = document.getElementById('btn-toggle-ruler');
            if (isRulerModeBtnActive) {{
                btn.classList.add('active');
            }} else {{
                btn.classList.remove('active');
                clearRuler();
            }}
        }}

        // ---------------------------------------------------------------------
        // RIGHELLO STRETTAMENTE ANCORATO AI PREZZI REALI DELLE CANDELE
        // ---------------------------------------------------------------------
        var isMeasuring = false;
        var startAnchor = null;
        var currentAnchor = null;
        var hasActiveMeasurement = false;

        var rulerRect = document.getElementById('ruler-rect');
        var rulerLine = document.getElementById('ruler-line');
        var startDot = document.getElementById('ruler-start-dot');
        var endDot = document.getElementById('ruler-end-dot');
        var hoverDot = document.getElementById('ruler-hover-dot');
        var hoverTag = document.getElementById('hover-price-tag');
        var badge = document.getElementById('measure-badge');

        function isRulerActive(e) {{
            return isRulerModeBtnActive || (e && (e.ctrlKey || e.metaKey));
        }}

        // Calcola il punto ancorato ai prezzi reali per le coordinate del mouse
        function getAnchoredPoint(e) {{
            var rect = plotDiv.getBoundingClientRect();
            var relX = e.clientX - rect.left;
            var relY = e.clientY - rect.top;

            var fullLayout = plotDiv._fullLayout;
            if (!fullLayout) return null;

            var xa = fullLayout.xaxis;
            var ya = fullLayout.yaxis;
            if (!xa || !ya) return null;

            var xOffset = xa._offset || 0;
            var xLen = xa._length || 1;
            var yOffset = ya._offset || 0;
            var yLen = ya._length || 1;

            // Limita l'ancoraggio all'area del prezzo (Row 1)
            if (relX < xOffset || relX > xOffset + xLen || relY < yOffset || relY > yOffset + yLen) {{
                return null;
            }}

            var xNorm = (relX - xOffset) / xLen;
            var d0 = new Date(xa.range[0]).getTime();
            var d1 = new Date(xa.range[1]).getTime();
            var targetMs = d0 + xNorm * (d1 - d0);

            // 1. Trova orizzontalmente la candela più vicina nel dataset
            var bestIdx = 0;
            var bestDiff = Infinity;
            for (var i = 0; i < candleData.length; i++) {{
                var cMs = new Date(candleData[i].date).getTime();
                var diff = Math.abs(cMs - targetMs);
                if (diff < bestDiff) {{
                    bestDiff = diff;
                    bestIdx = i;
                }}
            }}

            var candle = candleData[bestIdx];
            var cDateMs = new Date(candle.date).getTime();

            // 2. Determina verticalmente a quale prezzo REALE della candela agganciarsi
            var yNorm = 1.0 - ((relY - yOffset) / yLen);
            var y0 = parseFloat(ya.range[0]);
            var y1 = parseFloat(ya.range[1]);
            var cursorPrice = y0 + yNorm * (y1 - y0);

            // Opzioni di prezzo reali della candela
            var priceCandidates = [
                {{ label: 'Chiusura', price: candle.close }},
                {{ label: 'Massimo',  price: candle.high }},
                {{ label: 'Minimo',   price: candle.low }},
                {{ label: 'Apertura', price: candle.open }}
            ];

            // Seleziona il prezzo della candela più vicino alla posizione Y del cursore
            var bestPriceItem = priceCandidates[0];
            var bestPriceDiff = Math.abs(cursorPrice - priceCandidates[0].price);
            for (var j = 1; j < priceCandidates.length; j++) {{
                var pDiff = Math.abs(cursorPrice - priceCandidates[j].price);
                if (pDiff < bestPriceDiff) {{
                    bestPriceDiff = pDiff;
                    bestPriceItem = priceCandidates[j];
                }}
            }}

            var targetPrice = bestPriceItem.price;

            // 3. Calcola le coordinate pixel rigorosamente derivate dal prezzo e dalla data della candela
            var pixelX = xOffset + ((cDateMs - d0) / (d1 - d0)) * xLen;
            var pixelY = yOffset + (1.0 - ((targetPrice - y0) / (y1 - y0))) * yLen;

            return {{
                index: bestIdx,
                candle: candle,
                date: new Date(candle.date),
                dateStr: candle.date,
                price: targetPrice,
                priceType: bestPriceItem.label,
                pixelX: pixelX,
                pixelY: pixelY
            }};
        }}

        // Gestione tastiera
        window.addEventListener('keydown', function(e) {{
            if (e.key === 'Control' || e.key === 'Meta') {{
                plotDiv.style.cursor = 'crosshair';
            }}
            if (e.key === 'Escape') {{
                clearRuler();
            }}
        }});

        window.addEventListener('keyup', function(e) {{
            if (e.key === 'Control' || e.key === 'Meta') {{
                if (!isMeasuring && !isRulerModeBtnActive) {{
                    plotDiv.style.cursor = 'default';
                    hoverDot.style.display = 'none';
                    hoverTag.style.display = 'none';
                }}
            }}
        }});

        // Hover continuo: mostra il punto magnetico di aggancio al prezzo
        plotDiv.addEventListener('mousemove', function(e) {{
            if (!isMeasuring) {{
                if (isRulerActive(e)) {{
                    var pt = getAnchoredPoint(e);
                    if (pt) {{
                        plotDiv.style.cursor = 'crosshair';
                        hoverDot.style.display = 'block';
                        hoverDot.setAttribute('cx', pt.pixelX);
                        hoverDot.setAttribute('cy', pt.pixelY);

                        hoverTag.style.display = 'block';
                        hoverTag.style.left = pt.pixelX + 'px';
                        hoverTag.style.top = pt.pixelY + 'px';
                        hoverTag.innerHTML = `€${{pt.price.toFixed(2)}} (${{pt.priceType}})`;
                    }} else {{
                        hoverDot.style.display = 'none';
                        hoverTag.style.display = 'none';
                    }}
                }} else {{
                    hoverDot.style.display = 'none';
                    hoverTag.style.display = 'none';
                }}
                return;
            }}

            // Durante il trascinamento: aggiorna il punto di fine ancorato
            var ptEnd = getAnchoredPoint(e);
            if (!ptEnd) return;
            currentAnchor = ptEnd;
            renderAnchoredRuler(startAnchor, currentAnchor);
        }});

        plotDiv.addEventListener('mousedown', function(e) {{
            if (isRulerActive(e)) {{
                var pt = getAnchoredPoint(e);
                if (!pt) return;

                e.preventDefault();
                isMeasuring = true;
                startAnchor = pt;
                currentAnchor = pt;
                hasActiveMeasurement = true;

                hoverDot.style.display = 'none';
                hoverTag.style.display = 'none';

                renderAnchoredRuler(startAnchor, currentAnchor);
            }} else {{
                if (hasActiveMeasurement && !e.target.closest('#measure-badge')) {{
                    clearRuler();
                }}
            }}
        }});

        window.addEventListener('mouseup', function(e) {{
            if (isMeasuring) {{
                isMeasuring = false;
                plotDiv.style.cursor = 'default';
            }}
        }});

        // Ridisegna il righello ancorato
        function renderAnchoredRuler(pt1, pt2) {{
            if (!pt1 || !pt2) return;

            var x1 = pt1.pixelX;
            var y1 = pt1.pixelY;
            var x2 = pt2.pixelX;
            var y2 = pt2.pixelY;

            var minX = Math.min(x1, x2);
            var minY = Math.min(y1, y2);
            var width = Math.abs(x2 - x1);
            var height = Math.abs(y2 - y1);

            var pStart = pt1.price;
            var pEnd = pt2.price;
            var deltaPrice = pEnd - pStart;
            var pct = ((pEnd - pStart) / pStart) * 100;
            var isPos = deltaPrice >= 0;

            var styleClass = isPos ? 'pos' : 'neg';

            // Rettangolo ombreggiato ancorato
            rulerRect.style.display = 'block';
            rulerRect.setAttribute('x', minX);
            rulerRect.setAttribute('y', minY);
            rulerRect.setAttribute('width', Math.max(width, 2));
            rulerRect.setAttribute('height', Math.max(height, 2));
            rulerRect.setAttribute('class', 'ruler-rect ' + styleClass + '-box');

            // Linea diagonale tra i due prezzi reali
            rulerLine.style.display = 'block';
            rulerLine.setAttribute('x1', x1);
            rulerLine.setAttribute('y1', y1);
            rulerLine.setAttribute('x2', x2);
            rulerLine.setAttribute('y2', y2);
            rulerLine.setAttribute('class', 'ruler-line ' + styleClass + '-line');

            // Punto iniziale ancorato sul prezzo
            startDot.style.display = 'block';
            startDot.setAttribute('cx', x1);
            startDot.setAttribute('cy', y1);
            startDot.setAttribute('class', 'ruler-dot ' + styleClass + '-dot');

            // Punto finale ancorato sul prezzo
            endDot.style.display = 'block';
            endDot.setAttribute('cx', x2);
            endDot.setAttribute('cy', y2);
            endDot.setAttribute('class', 'ruler-dot ' + styleClass + '-dot');

            // Calcolo candele e date
            var bars = Math.abs(pt2.index - pt1.index) + 1;
            var msDiff = Math.abs(pt2.date.getTime() - pt1.date.getTime());
            var days = Math.round(msDiff / (1000 * 60 * 60 * 24));
            var weeks = Math.round(days / 7);

            var dStart = pt1.date < pt2.date ? pt1.date : pt2.date;
            var dEnd = pt1.date < pt2.date ? pt2.date : pt1.date;

            var fmtD = function(d) {{
                return ('0' + d.getDate()).slice(-2) + '/' + ('0' + (d.getMonth() + 1)).slice(-2) + '/' + d.getFullYear();
            }};

            var sign = isPos ? '+' : '';
            var color = isPos ? '#26a69a' : '#ef5350';

            badge.style.display = 'block';
            badge.innerHTML = `
                <div style="font-size: 17px; font-weight: 700; color: ${{color}}; margin-bottom: 4px;">
                    ${{sign}}${{pct.toFixed(2)}}% (${{sign}}€${{deltaPrice.toFixed(2)}})
                </div>
                <div style="font-size: 12px; color: #f1f5f9; margin-bottom: 2px;">
                    <b>Inizio:</b> €${{pStart.toFixed(2)}} (${{pt1.priceType}}) · ${{fmtD(pt1.date)}}
                </div>
                <div style="font-size: 12px; color: #f1f5f9; margin-bottom: 4px;">
                    <b>Fine:</b> €${{pEnd.toFixed(2)}} (${{pt2.priceType}}) · ${{fmtD(pt2.date)}}
                </div>
                <div style="font-size: 11px; color: #94a3b8; border-top: 1px solid #334155; padding-top: 4px; margin-top: 4px;">
                    ⏱️ <b>${{bars}} candele</b> (~${{weeks}} sett. · ${{days}} giorni)
                </div>
            `;

            // Posiziona il badge accanto al punto finale
            badge.style.left = (x2 + 16) + 'px';
            badge.style.top = (y2 - 10) + 'px';
        }}

        function clearRuler() {{
            rulerRect.style.display = 'none';
            rulerLine.style.display = 'none';
            startDot.style.display = 'none';
            endDot.style.display = 'none';
            hoverDot.style.display = 'none';
            hoverTag.style.display = 'none';
            badge.style.display = 'none';
            isMeasuring = false;
            startAnchor = null;
            currentAnchor = null;
            hasActiveMeasurement = false;
        }}

        // Quando l'utente effettua zoom o scroll sul grafico, riposiziona gli ancoraggi sui prezzi corretti
        plotDiv.on('plotly_relayout', function() {{
            if (hasActiveMeasurement && startAnchor && currentAnchor) {{
                var xa = plotDiv._fullLayout.xaxis;
                var ya = plotDiv._fullLayout.yaxis;
                if (!xa || !ya) return;

                var xOffset = xa._offset || 0;
                var xLen = xa._length || 1;
                var yOffset = ya._offset || 0;
                var yLen = ya._length || 1;

                var d0 = new Date(xa.range[0]).getTime();
                var d1 = new Date(xa.range[1]).getTime();
                var y0 = parseFloat(ya.range[0]);
                var y1 = parseFloat(ya.range[1]);

                var updatePt = function(pt) {{
                    var cDateMs = new Date(pt.candle.date).getTime();
                    pt.pixelX = xOffset + ((cDateMs - d0) / (d1 - d0)) * xLen;
                    pt.pixelY = yOffset + (1.0 - ((pt.price - y0) / (y1 - y0))) * yLen;
                }};

                updatePt(startAnchor);
                updatePt(currentAnchor);
                renderAnchoredRuler(startAnchor, currentAnchor);
            }}
        }});
    </script>
</body>
</html>
"""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    full_output_path = os.path.join(base_dir, output_html)

    with open(full_output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    print(f"Applicazione interattiva salvata in: {full_output_path}")

    if auto_open:
        try:
            webbrowser.open(f"file://{os.path.abspath(full_output_path)}")
            print("Dashboard aperta nel browser predefinito.")
        except Exception as e:
            print(f"Impossibile aprire automaticamente il browser: {e}")

    return full_output_path


# ==============================================================================
# 4. ESTRAZIONE SICURA DA BIGQUERY (Conforme a CLAUDE.md) CON CACHE LOCALE
# ==============================================================================

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
    1. Risolve il ticker al COD_AZIONE del database Milano Finanza (es. UCG -> CRIT).
    2. Usa la cache locale in `data/` per non rieseguire la query se i dati sono già presenti.
    3. Nessuna SELECT *: richiede solo le colonne necessarie.
    4. Filtra sempre sulla colonna di partizione `DATA_QUOTAZ`.
    5. Aggiunge un margine di 300 giorni prima dei 5 anni per calcolare la SMA a 200 gg continua.
    6. Esegue dry run obbligatorio prima dell'esecuzione (soglia di sicurezza 1 GB).
    """
    from google.cloud import bigquery

    if data_dir is None:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(base_dir, "data")

    cod_azione = TICKER_MAP.get(ticker.upper(), ticker.upper())
    os.makedirs(data_dir, exist_ok=True)
    cache_file = os.path.join(data_dir, f"{cod_azione}_quotes_{years}y.csv")

    # Verifica cache locale (Regola 5 CLAUDE.md: i dati estratti vanno in data/)
    if cache and os.path.exists(cache_file):
        print(f"Caricamento dati di {ticker} ({cod_azione}) dalla cache locale ({cache_file})...")
        df_cached = pd.read_csv(cache_file)
        df_cached['DATA_QUOTAZ'] = pd.to_datetime(df_cached['DATA_QUOTAZ'])
        return df_cached

    # Buffer: 5 anni + 300 giorni di margine per la SMA a 200 giorni
    giorni_totali = (years * 365) + 300
    table_id = f"`{project_id}.financial_instruments.instruments_quotes`"

    # Query selettiva
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

    # 1. Dry run preventivo (gratuito)
    cfg_dry = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False, query_parameters=params)
    job_dry = client.query(sql, job_config=cfg_dry)
    bytes_stimati = job_dry.total_bytes_processed
    print(f"Dry run BigQuery per {ticker} ({cod_azione}): {bytes_stimati / (1024**2):.2f} MB stimati")

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
    print(f"Query completata: {len(df):,} quotazioni caricate per {ticker} ({cod_azione}).")

    if cache and not df.empty:
        df.to_csv(cache_file, index=False)
        print(f"Dati salvati in cache locale: {cache_file}")

    return df


# ==============================================================================
# 5. ESECUZIONE DIRETTA (Supporto Decisionale UniCredit)
# ==============================================================================

if __name__ == "__main__":
    from google.cloud import bigquery

    TICKER_TEST = "UCG"  # UniCredit (COD_AZIONE: 'CRIT')
    PROJECT = "class-hackaton-12"

    print(f"--- Supporto Decisionale Finanziario per {TICKER_TEST} ---")
    try:
        client = bigquery.Client(project=PROJECT)
        df_real = query_stock_quotes_bigquery(client, ticker=TICKER_TEST, years=5, cache=True)
    except Exception as e:
        print(f"Errore connessione BigQuery ({e}). Assicurati di aver fatto login.")
        raise

    print(f"Dati giornalieri: {len(df_real):,} righe dal {df_real['DATA_QUOTAZ'].min().date()} al {df_real['DATA_QUOTAZ'].max().date()}")

    # Generazione figura Plotly con candele settimanali e indicatori
    fig = plot_stock_plotly(
        df_real,
        ticker="UniCredit (UCG)",
        years=5,
        ma_window=200,
        timeframe="1W",
        theme="plotly_dark",
    )

    # Generazione e apertura della Web App completa con Righello Ancorato ai Prezzi Reali
    generate_decision_support_app(fig, ticker="UniCredit (UCG)", output_html="stock_analysis.html", auto_open=True)
