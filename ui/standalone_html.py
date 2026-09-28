"""
Modulo di presentazione HTML Standalone.
Genera la pagina Web interattiva 'Decision Support' con Righello magnetico
strettamente ancorato ai prezzi reali di borsa (TradingView style).
"""

import os
import json
import webbrowser
import plotly.graph_objects as go
from visualization.price_charts import CLEAN_MODEBAR_BUTTONS


def generate_decision_support_html(
    fig: go.Figure,
    ticker: str = "Azione",
    output_html: str = "stock_analysis.html",
    auto_open: bool = True
) -> str:
    """
    Genera un file HTML standalone completo per il Decision Support:
    - ModeBar pulita da bottoni superflui.
    - Checkbox interattive per SMA 200, SMA 50, Volumi, Segnali Cross.
    - Righello di misurazione con aggancio magnetico ai prezzi reali.
    """
    plot_json = fig.to_json()

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
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: 'Inter', -apple-system, sans-serif;
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
            position: sticky;
            top: 0;
            z-index: 100;
        }}
        .brand {{ display: flex; align-items: center; gap: 10px; }}
        .brand-icon {{
            background: linear-gradient(135deg, #2563eb, #3b82f6);
            width: 32px; height: 32px; border-radius: 8px;
            display: flex; align-items: center; justify-content: center;
        }}
        .brand-title {{ font-size: 16px; font-weight: 700; color: #fff; }}
        .brand-subtitle {{ font-size: 11px; color: #94a3b8; }}
        .control-panel {{
            display: flex; align-items: center; flex-wrap: wrap; gap: 10px;
            background: #1e293b; padding: 5px 12px; border-radius: 10px; border: 1px solid #334155;
        }}
        .control-label {{
            font-size: 12px; font-weight: 600; color: #cbd5e1;
            display: flex; align-items: center; gap: 6px; cursor: pointer;
            padding: 4px 6px; border-radius: 6px;
        }}
        .control-label:hover {{ background: #334155; color: #fff; }}
        .divider {{ width: 1px; height: 20px; background: #475569; }}
        .btn-clean, .btn-ruler {{
            background: #334155; color: #f1f5f9; border: 1px solid #475569;
            padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; cursor: pointer;
            display: flex; align-items: center; gap: 6px;
        }}
        .btn-clean.active {{ background: #0ea5e9; border-color: #38bdf8; color: white; }}
        .btn-ruler {{ color: #38bdf8; border-color: #0284c7; background: #1e293b; }}
        .btn-ruler.active {{ background: #0284c7; color: white; }}
        .info-bar {{
            background: #172554; border-bottom: 1px solid #1e3a8a; padding: 6px 20px;
            font-size: 12px; color: #93c5fd; display: flex; justify-content: space-between;
        }}
        .ruler-key {{ background: #1e40af; color: #fff; padding: 1px 6px; border-radius: 4px; font-family: monospace; }}
        #chart-wrapper {{ flex: 1; position: relative; width: 100%; height: calc(100vh - 90px); }}
        #stock-chart {{ width: 100%; height: 100%; }}
        .ruler-svg-layer {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 40; }}
        .ruler-rect.pos-box {{ fill: rgba(38, 166, 154, 0.16); stroke: #26a69a; stroke-width: 1.5; stroke-dasharray: 4,3; }}
        .ruler-rect.neg-box {{ fill: rgba(239, 83, 80, 0.16); stroke: #ef5350; stroke-width: 1.5; stroke-dasharray: 4,3; }}
        .ruler-line.pos-line {{ stroke: #26a69a; stroke-width: 2.2; }}
        .ruler-line.neg-line {{ stroke: #ef5350; stroke-width: 2.2; }}
        .ruler-dot.pos-dot {{ fill: #26a69a; stroke: #fff; stroke-width: 2; }}
        .ruler-dot.neg-dot {{ fill: #ef5350; stroke: #fff; stroke-width: 2; }}
        .ruler-hover-dot {{ fill: #38bdf8; stroke: #fff; stroke-width: 2; filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.8)); }}
        .hover-price-tag {{
            position: absolute; background: rgba(15, 23, 42, 0.95); color: #38bdf8; font-size: 11px;
            font-weight: 600; padding: 3px 8px; border-radius: 4px; border: 1px solid #38bdf8;
            pointer-events: none; z-index: 55; display: none; transform: translate(-50%, -130%);
        }}
        .measure-badge {{
            position: absolute; background: rgba(15, 23, 42, 0.96); border: 1px solid #334155;
            border-radius: 8px; padding: 10px 14px; pointer-events: none; z-index: 60; display: none;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6); min-width: 230px;
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

            <label class="control-label" style="opacity: 0.9;">
                <input type="checkbox" id="chk-sma50" onchange="toggleTrace(2, this.checked)">
                🔵 SMA 50 gg (Opz.)
            </label>

            <label class="control-label" style="opacity: 0.9;">
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
            🎯 <b>Ancoraggio Automatico ai Prezzi:</b> Tieni premuto <span class="ruler-key">Ctrl</span> (o attiva <b>Misura Prezzo</b>) e <b>trascina il mouse</b> per agganciarti ai prezzi reali.
        </div>
        <div>Premi <span class="ruler-key">ESC</span> per cancellare.</div>
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

        var cleanConfig = {{
            modeBarButtonsToRemove: {json.dumps(CLEAN_MODEBAR_BUTTONS)},
            displaylogo: false,
            responsive: true,
            scrollZoom: true
        }};

        Plotly.newPlot(plotDiv, figData.data, figData.layout, cleanConfig);

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

            if (relX < xOffset || relX > xOffset + xLen || relY < yOffset || relY > yOffset + yLen) return null;

            var xNorm = (relX - xOffset) / xLen;
            var d0 = new Date(xa.range[0]).getTime();
            var d1 = new Date(xa.range[1]).getTime();
            var targetMs = d0 + xNorm * (d1 - d0);

            var bestIdx = 0, bestDiff = Infinity;
            for (var i = 0; i < candleData.length; i++) {{
                var diff = Math.abs(new Date(candleData[i].date).getTime() - targetMs);
                if (diff < bestDiff) {{ bestDiff = diff; bestIdx = i; }}
            }}

            var candle = candleData[bestIdx];
            var cDateMs = new Date(candle.date).getTime();

            var yNorm = 1.0 - ((relY - yOffset) / yLen);
            var y0 = parseFloat(ya.range[0]), y1 = parseFloat(ya.range[1]);
            var cursorPrice = y0 + yNorm * (y1 - y0);

            var priceCandidates = [
                {{ label: 'Chiusura', price: candle.close }},
                {{ label: 'Massimo',  price: candle.high }},
                {{ label: 'Minimo',   price: candle.low }},
                {{ label: 'Apertura', price: candle.open }}
            ];

            var bestItem = priceCandidates[0];
            var bestPDiff = Math.abs(cursorPrice - priceCandidates[0].price);
            for (var j = 1; j < priceCandidates.length; j++) {{
                var pDiff = Math.abs(cursorPrice - priceCandidates[j].price);
                if (pDiff < bestPDiff) {{ bestPDiff = pDiff; bestItem = priceCandidates[j]; }}
            }}

            var pixelX = xOffset + ((cDateMs - d0) / (d1 - d0)) * xLen;
            var pixelY = yOffset + (1.0 - ((bestItem.price - y0) / (y1 - y0))) * yLen;

            return {{
                index: bestIdx,
                candle: candle,
                date: new Date(candle.date),
                price: bestItem.price,
                priceType: bestItem.label,
                pixelX: pixelX,
                pixelY: pixelY
            }};
        }}

        window.addEventListener('keydown', function(e) {{
            if (e.key === 'Control' || e.key === 'Meta') plotDiv.style.cursor = 'crosshair';
            if (e.key === 'Escape') clearRuler();
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
                if (hasActiveMeasurement && !e.target.closest('#measure-badge')) clearRuler();
            }}
        }});

        window.addEventListener('mouseup', function(e) {{
            if (isMeasuring) {{
                isMeasuring = false;
                plotDiv.style.cursor = 'default';
            }}
        }});

        function renderAnchoredRuler(pt1, pt2) {{
            if (!pt1 || !pt2) return;
            var x1 = pt1.pixelX, y1 = pt1.pixelY, x2 = pt2.pixelX, y2 = pt2.pixelY;
            var minX = Math.min(x1, x2), minY = Math.min(y1, y2);
            var width = Math.abs(x2 - x1), height = Math.abs(y2 - y1);
            var pStart = pt1.price, pEnd = pt2.price;
            var deltaPrice = pEnd - pStart;
            var pct = ((pEnd - pStart) / pStart) * 100;
            var isPos = deltaPrice >= 0;
            var styleClass = isPos ? 'pos' : 'neg';

            rulerRect.style.display = 'block';
            rulerRect.setAttribute('x', minX);
            rulerRect.setAttribute('y', minY);
            rulerRect.setAttribute('width', Math.max(width, 2));
            rulerRect.setAttribute('height', Math.max(height, 2));
            rulerRect.setAttribute('class', 'ruler-rect ' + styleClass + '-box');

            rulerLine.style.display = 'block';
            rulerLine.setAttribute('x1', x1);
            rulerLine.setAttribute('y1', y1);
            rulerLine.setAttribute('x2', x2);
            rulerLine.setAttribute('y2', y2);
            rulerLine.setAttribute('class', 'ruler-line ' + styleClass + '-line');

            startDot.style.display = 'block';
            startDot.setAttribute('cx', x1);
            startDot.setAttribute('cy', y1);
            startDot.setAttribute('class', 'ruler-dot ' + styleClass + '-dot');

            endDot.style.display = 'block';
            endDot.setAttribute('cx', x2);
            endDot.setAttribute('cy', y2);
            endDot.setAttribute('class', 'ruler-dot ' + styleClass + '-dot');

            var bars = Math.abs(pt2.index - pt1.index) + 1;
            var msDiff = Math.abs(pt2.date.getTime() - pt1.date.getTime());
            var days = Math.round(msDiff / (1000 * 60 * 60 * 24));
            var weeks = Math.round(days / 7);

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
    </script>
</body>
</html>
"""
    output_path = os.path.abspath(output_html)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_template)

    if auto_open:
        try:
            webbrowser.open(f"file://{output_path}")
        except Exception:
            pass

    return output_path
