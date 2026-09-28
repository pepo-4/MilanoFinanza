"""
Modulo di calcolo degli indicatori tecnici tradizionali.
Logica di business pura: nessun import di Plotly, Streamlit o HTML.
"""

from typing import Optional
import pandas as pd
import numpy as np


def detect_column(df: pd.DataFrame, candidates: list) -> Optional[str]:
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
    ticker_map: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Pulisce, calcola gli indicatori tecnici (SMA 200, SMA 50, segnali Golden/Death Cross)
    e aggrega le quotazioni a livello settimanale (1W) o giornaliero (1D).

    Ritorna un DataFrame Pandas con colonne standardizzate:
    ['date', 'open', 'high', 'low', 'close', 'volume', 'ma_50', 'ma_200',
     'is_golden_cross', 'is_death_cross']
    """
    data = df.copy()

    # Rilevamento automatico colonne
    date_col = date_col or detect_column(data, ['data_quotaz', 'data', 'date', 'datetime', 'timestamp'])
    open_col = open_col or detect_column(data, ['prz_apertura', 'apertura', 'prezzo_apertura', 'open', 'p_apertura'])
    close_col = close_col or detect_column(data, ['prz_last', 'prz_rif', 'prz_uff', 'chiusura', 'prezzo_chiusura', 'close', 'ultimo'])
    volume_col = volume_col or detect_column(data, ['quantitativo', 'volumi', 'volume', 'vol', 'vol_scambi', 'quantita'])
    high_col = high_col or detect_column(data, ['prz_max', 'massimo', 'prezzo_max', 'high', 'max'])
    low_col = low_col or detect_column(data, ['prz_min', 'minimo', 'prezzo_min', 'low', 'min'])
    ticker_col = ticker_col or detect_column(data, ['cod_azione', 'des_azione', 'ticker', 'symbol', 'cod_isin', 'isin', 'titolo'])

    if not date_col:
        raise ValueError("Colonna della data non trovata. Specificare `date_col` esplicitamente.")
    if not close_col:
        raise ValueError("Colonna del prezzo di chiusura non trovata. Specificare `close_col` esplicitamente.")

    # Filtro su ticker se presente
    if ticker and ticker_col and ticker_col in data.columns:
        cod_target = ticker_map.get(str(ticker).upper(), str(ticker).upper()) if ticker_map else str(ticker).upper()
        matches = (
            (data[ticker_col].astype(str).str.upper() == str(ticker).upper()) |
            (data[ticker_col].astype(str).str.upper() == cod_target)
        )
        if matches.any():
            data = data[matches]

    # Conversione data e ordinamento cronologico
    data[date_col] = pd.to_datetime(data[date_col])
    data = data.sort_values(by=date_col).reset_index(drop=True)

    # Conversione numerica
    numeric_cols = [c for c in [open_col, close_col, high_col, low_col, volume_col] if c and c in data.columns]
    for c in numeric_cols:
        data[c] = pd.to_numeric(data[c], errors='coerce')

    if not high_col and open_col:
        data['__high__'] = data[[open_col, close_col]].max(axis=1)
        high_col = '__high__'
    if not low_col and open_col:
        data['__low__'] = data[[open_col, close_col]].min(axis=1)
        low_col = '__low__'

    # Calcolo SMA 200 e SMA 50 sui dati GIORNALIERI per evitare warmup/NaN all'inizio
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

        # Resample W-FRI (settimane di trading chiuse al venerdì)
        resampled = data.set_index(date_col).resample('W-FRI').agg(agg_rules)
        resampled = resampled.dropna(subset=[close_col]).reset_index()
        data = resampled

    # Filtro temporale sugli ultimi N anni
    max_date = data[date_col].max()
    cutoff_date = max_date - pd.DateOffset(years=years)
    filtered = data[data[date_col] >= cutoff_date].copy().reset_index(drop=True)

    # Rilevamento segnali tecnici Golden Cross e Death Cross
    diff = filtered['ma_50'] - filtered['ma_200']
    prev_diff = diff.shift(1)
    filtered['is_golden_cross'] = (diff > 0) & (prev_diff <= 0)
    filtered['is_death_cross'] = (diff < 0) & (prev_diff >= 0)

    # Mappatura nomi standardizzati
    rename_map = {date_col: 'date', close_col: 'close'}
    if open_col:
        rename_map[open_col] = 'open'
    if volume_col:
        rename_map[volume_col] = 'volume'
    if high_col:
        rename_map[high_col] = 'high'
    if low_col:
        rename_map[low_col] = 'low'

    return filtered.rename(columns=rename_map)
