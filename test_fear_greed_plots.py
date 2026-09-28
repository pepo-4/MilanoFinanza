"""
Script di Test: Calcolo e Visualizzazione dei 4 Indicatori Fear & Greed Separati.

Questo script:
1. Carica i dati storici a 5 anni di UniCredit (dalla cache locale `data/CRIT_quotes_5y.csv`).
2. Calcola i 4 indicatori quantitativi tramite `calculate_fear_greed(df)`.
3. Genera 4 grafici Plotly completamente DISTINTI e INDIPENDENTI:
   - Grafico 1: Market Momentum (Slancio SMA 125)
   - Grafico 2: Relative Strength (RSI a 20 giorni)
   - Grafico 3: Price Volatility (Volatilità Inversa ATR 14 vs 30 MA)
   - Grafico 4: Buying/Selling Pressure (Flusso Volumi su 20 sedute)
   + Grafico 5: Indice Sintetico Finale (FGI_Synthetic)
4. Crea una pagina web di test interattiva (`test_fear_greed_plots.html`) con:
   - Vista a Griglia (tutti e 4 i grafici visibili contemporaneamente)
   - Vista a Schede (Tab dedicate per ciascun singolo indicatore)
5. Apre automaticamente la pagina nel browser predefinito.
"""

import os
import sys
import webbrowser
import pandas as pd
import plotly.graph_objects as go

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from fear_greed import (
    calculate_fear_greed,
    plot_single_indicator,
    plot_fear_and_greed_chart,
    get_fgi_category,
    CLEAN_MODEBAR_BUTTONS,
)


def run_fear_greed_test(ticker: str = "UniCredit (UCG)", auto_open: bool = True):
    print("=" * 70)
    print(f"🚀 TEST INDICATORI FEAR & GREED SEPARATI: {ticker}")
    print("=" * 70)

    # 1. Ricerca del file di cache dati
    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, "data", "CRIT_quotes_5y.csv"),
        os.path.join(base_dir, "MilanoFinanza", "data", "CRIT_quotes_5y.csv"),
        os.path.join(os.path.dirname(base_dir), "data", "CRIT_quotes_5y.csv"),
    ]

    cache_file = None
    for p in possible_paths:
        if os.path.exists(p):
            cache_file = p
            break

    if not cache_file:
        raise FileNotFoundError(
            "File 'CRIT_quotes_5y.csv' non trovato. Assicurati che i dati siano presenti in data/."
        )

    print(f"📁 Caricamento dati da: {cache_file}")
    df_raw = pd.read_csv(cache_file)
    print(f"✅ Righe caricate: {len(df_raw):,} quotazioni giornaliere.")

    # 2. Calcolo dei 4 indicatori
    print("\n⚙️ Calcolo dei 4 indicatori quantitativi...")
    df_fgi = calculate_fear_greed(df_raw)

    last_row = df_fgi.iloc[-1]
    prev_row = df_fgi.iloc[-2] if len(df_fgi) > 1 else last_row
    last_date = pd.to_datetime(last_row['date']).strftime('%d/%m/%Y')

    cat_name, cat_emoji, _ = get_fgi_category(float(last_row['FGI_Synthetic']))

    print(f"\n📊 VALORI ODVERNI ({last_date}) - SCALA 0-100 (<45 Fear, >55 Greed):")
    print("-" * 70)
    print(f"1. 🎯 Market Momentum:       {last_row['FGI_Momentum']:5.1f} / 100  (Δ {last_row['FGI_Momentum'] - prev_row['FGI_Momentum']:+.1f} vs ieri)")
    print(f"2. 💪 Relative Strength:     {last_row['FGI_RSI']:5.1f} / 100  (Δ {last_row['FGI_RSI'] - prev_row['FGI_RSI']:+.1f} vs ieri)")
    print(f"3. 🛡️ Volatilità Inversa:    {last_row['FGI_Volatility']:5.1f} / 100  (Δ {last_row['FGI_Volatility'] - prev_row['FGI_Volatility']:+.1f} vs ieri)")
    print(f"4. ⚖️ Buying Pressure:       {last_row['FGI_Volume_Pressure']:5.1f} %    (Δ {last_row['FGI_Volume_Pressure'] - prev_row['FGI_Volume_Pressure']:+.1f}% vs ieri)")
    print("-" * 70)
    print(f"🧭 INDICE FGI SINTETICO:     {last_row['FGI_Synthetic']:5.1f} / 100  -> {cat_name} {cat_emoji}")
    print("=" * 70)

    # 3. Generazione dei 4 grafici DISTINTI + Indice Sintetico
    print("\n🎨 Generazione di 4 grafici Plotly individuali e separati...")

    fig_momentum = plot_single_indicator(df_fgi, indicator="momentum", ticker=ticker)
    fig_strength = plot_single_indicator(df_fgi, indicator="strength", ticker=ticker)
    fig_volatility = plot_single_indicator(df_fgi, indicator="volatility", ticker=ticker)
    fig_pressure = plot_single_indicator(df_fgi, indicator="pressure", ticker=ticker)
    fig_synthetic = plot_fear_and_greed_chart(df_fgi, ticker=ticker)

    # Personalizzazioni delle altezze per visualizzazione pulita
    for f in [fig_momentum, fig_strength, fig_volatility, fig_pressure]:
        f.update_layout(height=360, margin=dict(l=50, r=30, t=50, b=35))
    fig_synthetic.update_layout(height=420, margin=dict(l=50, r=30, t=50, b=35))

    # Configurazione Plotly senza bottoni inutili
    clean_config = {
        'modeBarButtonsToRemove': CLEAN_MODEBAR_BUTTONS,
        'displaylogo': False,
        'responsive': True
    }

    # 4. Creazione dell'HTML interattivo di test
    html_output_path = os.path.join(base_dir, "test_fear_greed_plots.html")
    print(f"📝 Creazione visualizzatore interattivo in: {html_output_path}")

    html_content = f"""<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Test 4 Grafici Fear & Greed Separati - {ticker}</title>
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', sans-serif;
            background-color: #0b1120;
            color: #f8fafc;
            padding: 24px;
        }}
        .header {{
            background: linear-gradient(135deg, #0f172a, #1e293b);
            border: 1px solid #334155;
            border-radius: 12px;
            padding: 20px 24px;
            margin-bottom: 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .title {{ font-size: 22px; font-weight: 700; color: #fff; }}
        .subtitle {{ font-size: 13px; color: #94a3b8; margin-top: 4px; }}
        .score-pill {{
            background: #1e293b;
            border: 1px solid #475569;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: #1e293b;
            border: 1px solid #334155;
            border-radius: 10px;
            padding: 16px;
        }}
        .metric-label {{ font-size: 12px; color: #94a3b8; font-weight: 600; text-transform: uppercase; }}
        .metric-value {{ font-size: 24px; font-weight: 700; color: #ffffff; margin: 4px 0; }}
        .metric-sub {{ font-size: 11px; color: #64748b; }}

        /* Tabs di navigazione */
        .tabs {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 1px solid #334155;
            padding-bottom: 10px;
        }}
        .tab-btn {{
            background: #1e293b;
            color: #94a3b8;
            border: 1px solid #334155;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s;
        }}
        .tab-btn:hover {{ background: #334155; color: #fff; }}
        .tab-btn.active {{
            background: #0284c7;
            color: #fff;
            border-color: #38bdf8;
        }}

        /* Sezioni grafici */
        .charts-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 1024px) {{
            .charts-container {{ grid-template-columns: 1fr; }}
        }}
        .chart-card {{
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 10px;
            padding: 12px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
    </style>
</head>
<body>

    <div class="header">
        <div>
            <h1 class="title">📈 Test 4 Indicatori Fear & Greed Separati</h1>
            <p class="subtitle">Titolo: <b>{ticker}</b> · Ultima seduta: <b>{last_date}</b> · Verifica disaccoppiamento grafico</p>
        </div>
        <div class="score-pill">
            🧭 FGI Sintetico: <span style="color: #38bdf8; font-size: 16px;">{last_row['FGI_Synthetic']:.1f}/100</span> ({cat_name} {cat_emoji})
        </div>
    </div>

    <!-- 4 Metriche chiave -->
    <div class="metrics-grid">
        <div class="metric-card" style="border-top: 3px solid #38bdf8;">
            <div class="metric-label">1. Market Momentum</div>
            <div class="metric-value">{last_row['FGI_Momentum']:.1f} <span style="font-size:14px; color:#94a3b8;">/ 100</span></div>
            <div class="metric-sub">SMA 125g · Slancio rialzista</div>
        </div>

        <div class="metric-card" style="border-top: 3px solid #a855f7;">
            <div class="metric-label">2. Relative Strength</div>
            <div class="metric-value">{last_row['FGI_RSI']:.1f} <span style="font-size:14px; color:#94a3b8;">/ 100</span></div>
            <div class="metric-sub">RSI standard a 20 giorni</div>
        </div>

        <div class="metric-card" style="border-top: 3px solid #f59e0b;">
            <div class="metric-label">3. Volatilità Inversa</div>
            <div class="metric-value">{last_row['FGI_Volatility']:.1f} <span style="font-size:14px; color:#94a3b8;">/ 100</span></div>
            <div class="metric-sub">ATR 14 vs 30 MA (Invertito)</div>
        </div>

        <div class="metric-card" style="border-top: 3px solid #ec4899;">
            <div class="metric-label">4. Buying Pressure</div>
            <div class="metric-value">{last_row['FGI_Volume_Pressure']:.1f}%</div>
            <div class="metric-sub">Volume sedute positive (20g)</div>
        </div>
    </div>

    <!-- Selettore modalità di vista -->
    <div class="tabs">
        <button class="tab-btn active" onclick="switchView('grid')">🔲 Vista Griglia (Tutti e 4 insieme)</button>
        <button class="tab-btn" onclick="switchView('tab-mom')">🎯 Solo Momentum</button>
        <button class="tab-btn" onclick="switchView('tab-rsi')">💪 Solo RSI</button>
        <button class="tab-btn" onclick="switchView('tab-vol')">🛡️ Solo Volatilità</button>
        <button class="tab-btn" onclick="switchView('tab-pres')">⚖️ Solo Buying Pressure</button>
        <button class="tab-btn" onclick="switchView('tab-synth')">🧭 Indice Sintetico Finale</button>
    </div>

    <!-- VISTA 1: GRIGLIA CON 4 GRAFICI DISTINTI -->
    <div id="view-grid" class="tab-content active">
        <div class="charts-container">
            <div class="chart-card">
                <div id="plot-momentum"></div>
            </div>
            <div class="chart-card">
                <div id="plot-strength"></div>
            </div>
            <div class="chart-card">
                <div id="plot-volatility"></div>
            </div>
            <div class="chart-card">
                <div id="plot-pressure"></div>
            </div>
            <div class="chart-card full-width">
                <div id="plot-synthetic-grid"></div>
            </div>
        </div>
    </div>

    <!-- VISTE SINGOLE TAB -->
    <div id="view-tab-mom" class="tab-content">
        <div class="chart-card"><div id="plot-mom-single"></div></div>
    </div>
    <div id="view-tab-rsi" class="tab-content">
        <div class="chart-card"><div id="plot-rsi-single"></div></div>
    </div>
    <div id="view-tab-vol" class="tab-content">
        <div class="chart-card"><div id="plot-vol-single"></div></div>
    </div>
    <div id="view-tab-pres" class="tab-content">
        <div class="chart-card"><div id="plot-pres-single"></div></div>
    </div>
    <div id="view-tab-synth" class="tab-content">
        <div class="chart-card"><div id="plot-synth-single"></div></div>
    </div>

    <script>
        var figMom = {fig_momentum.to_json()};
        var figRsi = {fig_strength.to_json()};
        var figVol = {fig_volatility.to_json()};
        var figPres = {fig_pressure.to_json()};
        var figSynth = {fig_synthetic.to_json()};

        var cfg = {{ displaylogo: false, responsive: true }};

        // Render dei 4 grafici nella griglia
        Plotly.newPlot('plot-momentum', figMom.data, figMom.layout, cfg);
        Plotly.newPlot('plot-strength', figRsi.data, figRsi.layout, cfg);
        Plotly.newPlot('plot-volatility', figVol.data, figVol.layout, cfg);
        Plotly.newPlot('plot-pressure', figPres.data, figPres.layout, cfg);
        Plotly.newPlot('plot-synthetic-grid', figSynth.data, figSynth.layout, cfg);

        // Render per le viste a scheda singola
        Plotly.newPlot('plot-mom-single', figMom.data, figMom.layout, cfg);
        Plotly.newPlot('plot-rsi-single', figRsi.data, figRsi.layout, cfg);
        Plotly.newPlot('plot-vol-single', figVol.data, figVol.layout, cfg);
        Plotly.newPlot('plot-pres-single', figPres.data, figPres.layout, cfg);
        Plotly.newPlot('plot-synth-single', figSynth.data, figSynth.layout, cfg);

        function switchView(viewName) {{
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');

            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            var target = document.getElementById('view-' + viewName);
            if (target) {{
                target.classList.add('active');
                // Trigger relayout per ridisegnare correttamente le dimensioni Plotly
                window.dispatchEvent(new Event('resize'));
            }}
        }}
    </script>
</body>
</html>
"""

    with open(html_output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"🎉 Pagina di test generata con successo: {html_output_path}")

    if auto_open:
        try:
            webbrowser.open(f"file://{os.path.abspath(html_output_path)}")
            print("🌐 Aperta automaticamente nel browser predefinito.")
        except Exception as e:
            print(f"Nota: impossibile aprire il browser automaticamente: {e}")

    return html_output_path


if __name__ == "__main__":
    run_fear_greed_test(ticker="UniCredit (UCG)", auto_open=True)
