"""
Modulo di visualizzazione per l'Indice Fear & Greed.
Costruisce e restituisce esclusivamente oggetti plotly.graph_objects.Figure.
"""

from typing import Optional
import pandas as pd
import plotly.graph_objects as go


def create_fear_greed_figure(
    df_fgi: pd.DataFrame,
    ticker: str = "Azione",
    theme: str = "plotly_dark"
) -> go.Figure:
    """
    Disegna il grafico storico lineare dell'Indice Sintetico FGI_Synthetic nel tempo,
    con linee tratteggiate orizzontali di soglia a 20 (Extreme Fear) e 80 (Extreme Greed)
    e sovrapposizione in semitrasparenza dei 4 indicatori sorgente.
    """
    date_col = 'date' if 'date' in df_fgi.columns else ('data_quotaz' if 'data_quotaz' in df_fgi.columns else None)
    x_vals = df_fgi[date_col] if date_col else df_fgi.index

    fig = go.Figure()

    # Fasce di sfondo orizzontali colorate (Zones)
    fig.add_hrect(y0=80, y1=100, fillcolor="rgba(34, 197, 94, 0.10)", layer="below", line_width=0)
    fig.add_hrect(y0=55, y1=80, fillcolor="rgba(34, 197, 94, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=45, y1=55, fillcolor="rgba(234, 179, 8, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=20, y1=45, fillcolor="rgba(249, 115, 22, 0.04)", layer="below", line_width=0)
    fig.add_hrect(y0=0, y1=20, fillcolor="rgba(239, 68, 68, 0.10)", layer="below", line_width=0)

    # Linee di soglia orizzontali
    fig.add_hline(
        y=80, line=dict(color="#22C55E", width=1.5, dash="dash"),
        annotation_text="<b>Extreme Greed (80)</b>", annotation_position="top left",
        annotation_font=dict(color="#22C55E", size=10)
    )
    fig.add_hline(
        y=55, line=dict(color="rgba(34, 197, 94, 0.4)", width=1, dash="dot"),
        annotation_text="Greed (55)", annotation_position="top left",
        annotation_font=dict(color="#86EFAC", size=9)
    )
    fig.add_hline(
        y=50, line=dict(color="rgba(148, 163, 184, 0.5)", width=1, dash="dashdot"),
        annotation_text="Neutral (50)", annotation_position="bottom left",
        annotation_font=dict(color="#94A3B8", size=9)
    )
    fig.add_hline(
        y=45, line=dict(color="rgba(249, 115, 22, 0.4)", width=1, dash="dot"),
        annotation_text="Fear (45)", annotation_position="bottom left",
        annotation_font=dict(color="#FCA5A5", size=9)
    )
    fig.add_hline(
        y=20, line=dict(color="#EF4444", width=1.5, dash="dash"),
        annotation_text="<b>Extreme Fear (20)</b>", annotation_position="bottom left",
        annotation_font=dict(color="#EF4444", size=10)
    )

    # 4 Indicatori sorgente sovrapposti (sottili e semitrasparenti)
    fig.add_trace(go.Scatter(
        x=x_vals, y=df_fgi['FGI_Momentum'], mode='lines', name='Momentum (SMA 125)',
        line=dict(color='rgba(56, 189, 248, 0.45)', width=1.2, dash='dot'),
        hovertemplate='%{x|%d/%m/%Y}<br>Momentum: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_vals, y=df_fgi['FGI_RSI'], mode='lines', name='Forza Relativa (RSI 20)',
        line=dict(color='rgba(168, 85, 247, 0.45)', width=1.2, dash='dot'),
        hovertemplate='%{x|%d/%m/%Y}<br>RSI 20: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_vals, y=df_fgi['FGI_Volatility'], mode='lines', name='Volatilità Inversa (ATR)',
        line=dict(color='rgba(245, 158, 11, 0.45)', width=1.2, dash='dot'),
        hovertemplate='%{x|%d/%m/%Y}<br>Volatilità Inversa: %{y:.1f}<extra></extra>'
    ))
    fig.add_trace(go.Scatter(
        x=x_vals, y=df_fgi['FGI_Volume_Pressure'], mode='lines', name='Buying Pressure (Volumi)',
        line=dict(color='rgba(236, 72, 153, 0.45)', width=1.2, dash='dot'),
        hovertemplate='%{x|%d/%m/%Y}<br>Pressione Volumi: %{y:.1f}%<extra></extra>'
    ))

    # Traccia principale: FGI Sintetico
    fig.add_trace(go.Scatter(
        x=x_vals, y=df_fgi['FGI_Synthetic'], mode='lines+markers', name='🧭 FGI Sintetico',
        line=dict(color='#38BDF8', width=3.0),
        marker=dict(size=4, color=df_fgi['FGI_Synthetic'], colorscale='RdYlGn', cmin=0, cmax=100, showscale=False),
        hovertemplate='<b>%{x|%d/%m/%Y}</b><br>🧭 <b>Indice FGI Sintetico: %{y:.1f} / 100</b><extra></extra>'
    ))

    fig.update_layout(
        template=theme,
        title=dict(text=f"<b>Storico Indice Fear & Greed (0-100)</b> · {ticker}", x=0.01, y=0.96, font=dict(size=15, color="#F8FAFC")),
        xaxis=dict(title_text="Data", showgrid=True, gridcolor="rgba(51, 65, 85, 0.4)"),
        yaxis=dict(
            title_text="Fear & Greed Index", range=[0, 100],
            tickvals=[0, 20, 45, 50, 55, 80, 100],
            ticktext=["0 (Ext. Fear)", "20", "45", "50", "55", "80", "100 (Ext. Greed)"],
            showgrid=True, gridcolor="rgba(51, 65, 85, 0.4)"
        ),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
        margin=dict(l=60, r=40, t=60, b=40),
        height=420
    )

    return fig


def create_single_indicator_figure(
    df_fgi: pd.DataFrame,
    indicator: str = "momentum",
    ticker: str = "Azione",
    theme: str = "plotly_dark"
) -> go.Figure:
    """
    Costruisce e restituisce un grafico standalone dedicato per UNO solo dei 4 indicatori.
    """
    key = indicator.lower().strip()
    date_col = 'date' if 'date' in df_fgi.columns else ('data_quotaz' if 'data_quotaz' in df_fgi.columns else None)
    x_vals = df_fgi[date_col] if date_col else df_fgi.index

    fig = go.Figure()

    if key in ['momentum', 'slancio', 'sma125']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Momentum'], mode='lines', name='Market Momentum (0-100)',
            line=dict(color='#38BDF8', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>Momentum: %{y:.1f} / 100<extra></extra>'
        ))
        title = f"<b>Market Momentum (Slancio su SMA 125)</b> · {ticker}"
        y_title = "Score Momentum (0-100)"

    elif key in ['strength', 'rsi', 'rsi20', 'forza']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_RSI'], mode='lines', name='RSI 20 giorni',
            line=dict(color='#A855F7', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>RSI (20g): %{y:.1f}<extra></extra>'
        ))
        title = f"<b>Relative Strength (RSI a 20 giorni)</b> · {ticker}"
        y_title = "RSI (0-100)"

    elif key in ['volatility', 'volatilita', 'atr']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Volatility'], mode='lines', name='Volatilità Inversa',
            line=dict(color='#F59E0B', width=2.5),
            hovertemplate='%{x|%d/%m/%Y}<br>Volatilità Inversa: %{y:.1f} / 100<extra></extra>'
        ))
        title = f"<b>Price Volatility (Volatilità Inversa ATR 14 vs 30 MA)</b> · {ticker}"
        y_title = "Score Volatilità (0-100)"

    elif key in ['pressure', 'pressione', 'volume', 'buying_pressure']:
        fig.add_trace(go.Scatter(
            x=x_vals, y=df_fgi['FGI_Volume_Pressure'], mode='lines', name='Buying Pressure %',
            line=dict(color='#EC4899', width=2.5),
            fill='tozeroy', fillcolor='rgba(236, 72, 153, 0.1)',
            hovertemplate='%{x|%d/%m/%Y}<br>Buying Pressure: %{y:.1f}%<extra></extra>'
        ))
        title = f"<b>Buying/Selling Pressure (Flusso Volumi 20g)</b> · {ticker}"
        y_title = "% Volume su Sedute Positive"
    else:
        raise ValueError(f"Indicatore sconosciuto: '{indicator}'. Scegli tra: momentum, strength, volatility, pressure.")

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
