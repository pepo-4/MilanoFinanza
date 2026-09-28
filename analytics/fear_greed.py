"""
Modulo di calcolo per l'Indice Fear & Greed.
Logica di business pura: nessun import di Plotly, Streamlit o codice HTML.
"""

from typing import Tuple, Optional
import numpy as np
import pandas as pd


def get_fgi_category(val: float) -> Tuple[str, str, str]:
    """
    Ritorna la classificazione qualitativa, emoji e colore associati al valore (0-100):
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
    Calcola le colonne storiche dell'Indice Fear & Greed normalizzate su scala 0-100:
    1. Market Momentum: Scostamento dalla SMA a 125 giorni normalizzato su ±20%.
    2. Relative Strength: RSI a 20 giorni (Wilder smoothing).
    3. Price Volatility: Rapporto invertito ATR 14 vs Media ATR 30.
    4. Buying/Selling Pressure: Flusso volumi rialzisti su finestra 20 sedute.
    5. FGI_Synthetic: Media dei 4 indicatori compositi.

    Ritorna una copia del DataFrame arricchito con tutte le colonne analitiche.
    """
    data = df.copy()

    # Rilevamento colonne
    cols_lower = {c.lower(): c for c in data.columns}
    def _find(cands):
        for c in cands:
            if c.lower() in cols_lower:
                return cols_lower[c.lower()]
        return None

    date_col = _find(['date', 'data_quotaz', 'data', 'datetime', 'timestamp'])
    close_col = _find(['close', 'prz_last', 'prz_rif', 'prz_uff', 'chiusura', 'prezzo_chiusura', 'ultimo'])
    open_col = _find(['open', 'prz_apertura', 'apertura', 'prezzo_apertura', 'p_apertura'])
    high_col = _find(['high', 'prz_max', 'massimo', 'prezzo_max', 'max'])
    low_col = _find(['low', 'prz_min', 'minimo', 'prezzo_min', 'min'])
    volume_col = _find(['volume', 'quantitativo', 'volumi', 'vol', 'vol_scambi', 'quantita'])

    if not close_col:
        raise ValueError("Colonna del prezzo di chiusura non trovata nel DataFrame.")

    if date_col:
        data[date_col] = pd.to_datetime(data[date_col])
        data = data.sort_values(by=date_col).reset_index(drop=True)

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

    # 1. Market Momentum (SMA 125)
    sma_125 = close.rolling(window=125, min_periods=1).mean()
    mom_pct = (close - sma_125) / sma_125
    fgi_momentum = np.clip(50.0 + mom_pct * 250.0, 0.0, 100.0)

    data['SMA_125'] = sma_125
    data['Momentum_Pct'] = mom_pct * 100.0
    data['FGI_Momentum'] = fgi_momentum.round(1)

    # 2. Relative Strength (RSI a 20 giorni)
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

    # 3. Price Volatility (Inversa: ATR 14 vs ATR 30 MA)
    prev_close = close.shift(1)
    tr1 = high - low
    tr2 = (high - prev_close).abs()
    tr3 = (low - prev_close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    atr_14 = true_range.rolling(window=14, min_periods=1).mean()
    atr_30_ma = atr_14.rolling(window=30, min_periods=1).mean()

    vol_ratio = (atr_14 / atr_30_ma.replace(0.0, np.nan)).fillna(1.0)
    fgi_volatility = np.clip(50.0 - (vol_ratio - 1.0) * 100.0, 0.0, 100.0)

    data['True_Range'] = true_range
    data['ATR_14'] = atr_14
    data['ATR_30_MA'] = atr_30_ma
    data['ATR_Ratio'] = vol_ratio.round(2)
    data['FGI_Volatility'] = fgi_volatility.round(1)

    # 4. Buying/Selling Pressure
    pos_vol = np.where(close > prev_close, vol, 0.0)
    rolling_pos_vol = pd.Series(pos_vol, index=data.index).rolling(window=20, min_periods=1).sum()
    rolling_tot_vol = vol.rolling(window=20, min_periods=1).sum()

    pressure_pct = (rolling_pos_vol / rolling_tot_vol.replace(0.0, np.nan)) * 100.0
    pressure_pct = pressure_pct.fillna(50.0)
    fgi_volume_pressure = np.clip(pressure_pct, 0.0, 100.0)

    data['Volume_Positivo'] = pos_vol
    data['FGI_Volume_Pressure'] = fgi_volume_pressure.round(1)

    # 5. Fear & Greed Sintetico
    fgi_synthetic = (fgi_momentum + fgi_rsi + fgi_volatility + fgi_volume_pressure) / 4.0
    data['FGI_Synthetic'] = fgi_synthetic.round(1)
    data['FGI_Label'] = [get_fgi_category(v)[0] for v in data['FGI_Synthetic']]

    if date_col and date_col != 'date':
        data['date'] = data[date_col]

    return data
