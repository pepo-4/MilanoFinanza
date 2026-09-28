"""
Modulo di visualizzazione per l'andamento del prezzo e dei volumi.
Costruisce e restituisce esclusivamente oggetti plotly.graph_objects.Figure.
"""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Bottoni inutili da rimuovere dalla barra degli strumenti di Plotly
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


def create_price_candlestick_figure(
    df: pd.DataFrame,
    ticker: str = "Azione",
    years: int = 5,
    timeframe: str = "1W",
    theme: str = "plotly_dark",
    remove_weekends: Optional[bool] = None,
    use_candlesticks: bool = True,
) -> go.Figure:
    """
    Costruisce la figura Plotly con 2 subplot:
    - Row 1: Candele Prezzo, SMA 200 (attiva), SMA 50 (opzionale), segnali Cross (opzionali).
    - Row 2: Volumi di scambio con colorazione direzionale.

    Parametri
    ---------
    df : pd.DataFrame
        DataFrame pre-elaborato da analytics.indicators.prepare_stock_data.
    """
    is_weekly = str(timeframe).upper() in ['1W', 'W', 'WEEKLY', 'SETTIMANALE']
    freq_label = "Settimanale" if is_weekly else "Giornaliero"

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.72, 0.28],
        subplot_titles=(
            f"<b>{ticker}</b> - Andamento {freq_label} ({len(df)} candele, {years} anni)",
            f"<b>Volumi di Scambio ({freq_label})</b>"
        )
    )

    has_open = 'open' in df.columns
    has_high = 'high' in df.columns
    has_low = 'low' in df.columns

    # 1. TRACCIA 0: Candele Prezzo
    if use_candlesticks and has_open:
        high_vals = df['high'] if has_high else df[['open', 'close']].max(axis=1)
        low_vals = df['low'] if has_low else df[['open', 'close']].min(axis=1)

        fig.add_trace(
            go.Candlestick(
                x=df['date'],
                open=df['open'],
                high=high_vals,
                low=low_vals,
                close=df['close'],
                name="Candele Prezzo",
                increasing_line_color='#26a69a',
                decreasing_line_color='#ef5350',
                increasing_fillcolor='#26a69a',
                decreasing_fillcolor='#ef5350',
                text=[f"Settimana: {d.strftime('%d/%m/%Y')}" for d in df['date']] if is_weekly else None,
            ),
            row=1, col=1
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['close'],
                mode='lines',
                name='Prezzo Chiusura',
                line=dict(color='#2962FF', width=2.0),
                hovertemplate='%{x|%d/%m/%Y}<br>Chiusura: €%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

    # 2. TRACCIA 1: Media Mobile 200 gg (Attiva di default)
    if 'ma_200' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['ma_200'],
                mode='lines',
                name="SMA 200 gg",
                line=dict(color='#FFA500', width=2.2),
                hovertemplate='SMA 200 gg: €%{y:.2f}<extra></extra>',
                visible=True
            ),
            row=1, col=1
        )

    # 3. TRACCIA 2: Media Mobile 50 gg (Opzionale: legendonly)
    if 'ma_50' in df.columns:
        fig.add_trace(
            go.Scatter(
                x=df['date'],
                y=df['ma_50'],
                mode='lines',
                name="SMA 50 gg",
                line=dict(color='#00E5FF', width=1.8, dash='dot'),
                hovertemplate='SMA 50 gg: €%{y:.2f}<extra></extra>',
                visible='legendonly'
            ),
            row=1, col=1
        )

    # 4. TRACCIA 3: Golden Cross Marker (Opzionale: legendonly)
    if 'is_golden_cross' in df.columns:
        golden_df = df[df['is_golden_cross']]
        if not golden_df.empty:
            golden_y = golden_df['low'] * 0.96 if has_low else golden_df['close'] * 0.96
            golden_hover = [
                f"<b>🌟 GOLDEN CROSS RIALZISTA</b><br>"
                f"Data: {d.strftime('%d/%m/%Y')}<br>"
                f"Prezzo: €{c:.2f}<br>"
                f"SMA 50 gg (€{m50:.2f}) ha superato al rialzo la SMA 200 gg (€{m200:.2f})."
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
                    visible='legendonly'
                ),
                row=1, col=1
            )
        else:
            fig.add_trace(go.Scatter(x=[], y=[], mode='markers', name="🌟 Golden Cross", visible='legendonly'), row=1, col=1)

    # 5. TRACCIA 4: Death Cross Marker (Opzionale: legendonly)
    if 'is_death_cross' in df.columns:
        death_df = df[df['is_death_cross']]
        if not death_df.empty:
            death_y = death_df['high'] * 1.04 if has_high else death_df['close'] * 1.04
            death_hover = [
                f"<b>⚠️ DEATH CROSS RIBASSISTA</b><br>"
                f"Data: {d.strftime('%d/%m/%Y')}<br>"
                f"Prezzo: €{c:.2f}<br>"
                f"SMA 50 gg (€{m50:.2f}) ha tagliato al ribasso la SMA 200 gg (€{m200:.2f})."
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
                    visible='legendonly'
                ),
                row=1, col=1
            )
        else:
            fig.add_trace(go.Scatter(x=[], y=[], mode='markers', name="⚠️ Death Cross", visible='legendonly'), row=1, col=1)

    # 6. TRACCIA 5: Volumi di Scambio
    if 'volume' in df.columns:
        if has_open:
            vol_colors = ['#26a69a' if c >= o else '#ef5350' for c, o in zip(df['close'], df['open'])]
        else:
            vol_colors = ['#26a69a' if df['close'].iloc[i] >= df['close'].iloc[max(0, i - 1)] else '#ef5350'
                          for i in range(len(df))]

        fig.add_trace(
            go.Bar(
                x=df['date'],
                y=df['volume'],
                marker_color=vol_colors,
                name="Volumi",
                hovertemplate='%{x|%d/%m/%Y}<br>Volume: %{y:,.0f}<extra></extra>',
                visible=True
            ),
            row=2, col=1
        )

    # Pulsanti di controllo nativi
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
