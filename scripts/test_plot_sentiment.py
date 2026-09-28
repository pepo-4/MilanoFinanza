"""Serie temporale settimanale del sentiment Unicredit, con il volume di notizie sotto.

Le notizie solo descrittive (analisi tecnica ecc.) sono escluse del tutto: non entrano né nel
sentiment né nel volume. Per ogni settimana, sulle notizie con score:
  media     = score medio (linea)
  ±1 std    = fascia chiara media ± deviazione standard: quanto sono discordi le notizie
              (larghezza 0 nelle settimane con una sola notizia; tagliata a [-1, 1])
  volume    = numero di notizie con score
Le settimane senza notizie con score restano vuote (buco nella linea, volume 0).

Uso:
  .venv/bin/python scripts/weekly_sentiment.py        # prima, per aggiornare news_by_week
  .venv/bin/python scripts/test_plot_sentiment.py     # -> data/unicredit/sentiment_weekly_<modello>.html
  .venv/bin/python scripts/test_plot_sentiment.py --show
"""

import argparse
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "unicredit"
# Palette: una sola tinta (blu) a più intensità, volume e assi neutri
MEAN = "#1c5cab"
BAND = "rgba(42, 120, 214, 0.12)"
VOLUME = "#8a8984"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"


def weekly_series(news):
    s = news[(news["solo_descrittiva"] == False) & news["score"].notna()]  # noqa: E712
    g = s.groupby("settimana")["score"]
    w = pd.DataFrame({"media": g.mean(), "std": g.std().fillna(0), "volume": g.size()})
    w["sopra"] = (w["media"] + w["std"]).clip(upper=1)
    w["sotto"] = (w["media"] - w["std"]).clip(lower=-1)
    # Serie continua: le settimane senza notizie con score restano vuote
    w = w.reindex(pd.date_range(w.index.min(), w.index.max(), freq="W-FRI"))
    w["volume"] = w["volume"].fillna(0).astype(int)
    return w


def plot(w, title):
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.72, 0.28])

    # Fascia ±1 std: un poligono per ogni tratto di settimane consecutive con score,
    # così i buchi non vengono riempiti in diagonale
    bx, by = [], []
    ok = w["media"].notna()
    for _, seg in w[ok].groupby((~ok).cumsum()[ok]):
        bx += list(seg.index) + list(seg.index[::-1]) + [None]
        by += list(seg["sopra"]) + list(seg["sotto"][::-1]) + [None]
    fig.add_trace(go.Scatter(
        x=bx, y=by, mode="lines", line=dict(width=0), fill="toself", fillcolor=BAND,
        name="± 1 deviazione standard", hoverinfo="skip",
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=w.index, y=w["media"], mode="lines", line=dict(color=MEAN, width=2), connectgaps=False,
        name="Media settimanale", customdata=w[["std"]],
        hovertemplate="media %{y:+.2f} ± %{customdata[0]:.2f}<extra></extra>",
    ), row=1, col=1)
    fig.add_hline(y=0, line=dict(color=INK_2, width=1, dash="dot"), row=1, col=1)

    fig.add_trace(go.Bar(
        x=w.index, y=w["volume"], name="Notizie con score", marker=dict(color=VOLUME, line=dict(width=0)),
        showlegend=False, hovertemplate="%{y} notizie<extra></extra>",
    ), row=2, col=1)

    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=INK), x=0.01, y=0.975),
        template="simple_white",
        paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        font=dict(family="Inter, system-ui, sans-serif", size=12, color=INK_2),
        legend=dict(orientation="h", x=1, xanchor="right", y=1.02, yanchor="bottom", font=dict(color=INK_2)),
        hovermode="x unified",
        margin=dict(l=60, r=24, t=96, b=40),
        height=720,
        bargap=0.15,
    )
    axis = dict(showgrid=True, gridcolor=GRID, zeroline=False, linecolor=GRID, tickcolor=GRID)
    fig.update_xaxes(**axis, hoverformat="settimana al %d/%m/%Y")
    fig.update_yaxes(**axis)
    fig.update_yaxes(title_text="Sentiment (-1 … +1)", range=[-1.05, 1.05], tickvals=[-1, -0.5, 0, 0.5, 1], row=1, col=1)
    fig.update_yaxes(title_text="Notizie", rangemode="tozero", row=2, col=1)
    fig.update_xaxes(
        rangeselector=dict(buttons=[
            dict(count=6, label="6M", step="month", stepmode="backward"),
            dict(count=1, label="1A", step="year", stepmode="backward"),
            dict(count=2, label="2A", step="year", stepmode="backward"),
            dict(step="all", label="Tutto"),
        ], bgcolor=SURFACE, activecolor=GRID, font=dict(color=INK_2)),
        row=1, col=1,
    )
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="gemini-3-flash-preview")
    ap.add_argument("--show", action="store_true", help="apri il grafico nel browser")
    args = ap.parse_args()

    news = pd.read_parquet(OUT_DIR / f"news_by_week_{args.model}.parquet")
    w = weekly_series(news)
    n_descr = int((news["solo_descrittiva"] == True).sum())  # noqa: E712
    print(f"Notizie con score: {w['volume'].sum()} (escluse {n_descr} descrittive) | "
          f"settimane: {len(w)}, con score: {w['media'].notna().sum()}")

    fig = plot(w, f"Unicredit · sentiment settimanale delle notizie ({args.model})")
    out = OUT_DIR / f"sentiment_weekly_{args.model}.html"
    fig.write_html(out, include_plotlyjs="cdn")
    print(f"-> {out}")
    if args.show:
        fig.show()


if __name__ == "__main__":
    main()
