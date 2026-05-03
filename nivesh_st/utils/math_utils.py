"""
Finance math utilities: indicators, Black-Scholes, Monte Carlo, scoring.
"""
import numpy as np
import pandas as pd
from scipy.stats import norm

# ── Technical Indicators ───────────────────────────────────────────────────

def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_g = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_l = loss.ewm(com=period - 1, min_periods=period).mean()
    rs    = avg_g / avg_l.replace(0, np.nan)
    return 100 - 100 / (1 + rs)

def compute_macd(series: pd.Series, fast=12, slow=26, signal=9):
    ema_fast   = series.ewm(span=fast, adjust=False).mean()
    ema_slow   = series.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line= macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram

def compute_bollinger(series: pd.Series, period: int = 20, std: float = 2.0):
    mid   = series.rolling(period).mean()
    sd    = series.rolling(period).std()
    upper = mid + std * sd
    lower = mid - std * sd
    return upper, mid, lower

def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    hi, lo, cl = df["High"], df["Low"], df["Close"]
    tr = pd.concat([hi - lo, (hi - cl.shift()).abs(), (lo - cl.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(span=period, adjust=False).mean()

def compute_all_signals(df: pd.DataFrame) -> dict:
    """Compute all technical signals and return summary."""
    if df is None or len(df) < 30:
        return {}
    c = df["Close"]
    rsi    = compute_rsi(c)
    macd_l, macd_s, macd_h = compute_macd(c)
    sma20  = c.rolling(20).mean()
    sma50  = c.rolling(50).mean()
    sma200 = c.rolling(200).mean()
    bb_u, bb_m, bb_l = compute_bollinger(c)
    atr_v  = compute_atr(df)

    last    = c.iloc[-1]
    rsi_v   = rsi.iloc[-1]
    atr_last= atr_v.iloc[-1]

    signals = []; bull = 0; bear = 0

    if not np.isnan(rsi_v):
        if rsi_v < 30:      signals.append(("RSI", f"{rsi_v:.1f}", "Oversold — Bullish", "🟢")); bull += 2
        elif rsi_v > 70:    signals.append(("RSI", f"{rsi_v:.1f}", "Overbought — Bearish", "🔴")); bear += 2
        elif rsi_v >= 50:   signals.append(("RSI", f"{rsi_v:.1f}", "Neutral Bullish", "🟡")); bull += 1
        else:               signals.append(("RSI", f"{rsi_v:.1f}", "Neutral Bearish", "🟡")); bear += 1

    if not macd_l.isna().iloc[-1]:
        if macd_l.iloc[-1] > macd_s.iloc[-1]:
            signals.append(("MACD", f"{macd_l.iloc[-1]:.2f}", "Bullish crossover", "🟢")); bull += 2
        else:
            signals.append(("MACD", f"{macd_l.iloc[-1]:.2f}", "Bearish crossover", "🔴")); bear += 2

    for label, sma_s in [("20 DMA", sma20), ("50 DMA", sma50), ("200 DMA", sma200)]:
        v = sma_s.iloc[-1]
        if not np.isnan(v):
            if last > v: signals.append((label, f"₹{v:.0f}", "Price above — Bullish", "🟢")); bull += 1
            else:        signals.append((label, f"₹{v:.0f}", "Price below — Bearish", "🔴")); bear += 1

    if not bb_u.isna().iloc[-1]:
        bu, bl = bb_u.iloc[-1], bb_l.iloc[-1]
        if last > bu:   signals.append(("Bollinger", f"₹{bl:.0f}–₹{bu:.0f}", "Above upper band — Extended", "🔴")); bear += 1
        elif last < bl: signals.append(("Bollinger", f"₹{bl:.0f}–₹{bu:.0f}", "Below lower band — Oversold", "🟢")); bull += 1
        else:           signals.append(("Bollinger", f"₹{bl:.0f}–₹{bu:.0f}", "Inside bands — Neutral", "⚪"))

    score = bull - bear
    if score >= 5:     overall = "Strong Buy"
    elif score >= 2:   overall = "Buy"
    elif score <= -5:  overall = "Strong Sell"
    elif score <= -2:  overall = "Sell"
    else:              overall = "Neutral"

    return {
        "signals": signals, "overall": overall, "score": score,
        "rsi": rsi_v, "atr": atr_last,
        "sma20": sma20.iloc[-1], "sma50": sma50.iloc[-1],
        "sma200": sma200.iloc[-1] if len(df) >= 200 else None,
        "bb_upper": bb_u.iloc[-1], "bb_lower": bb_l.iloc[-1],
        "macd": macd_l.iloc[-1], "macd_signal": macd_s.iloc[-1],
        "stop_1x": last - 1.5 * atr_last,
        "stop_2x": last - 2.5 * atr_last,
        "sma_series": {"20": sma20, "50": sma50, "200": sma200},
        "bb_series": {"upper": bb_u, "lower": bb_l, "mid": bb_m},
    }

# ── Black-Scholes ──────────────────────────────────────────────────────────

def black_scholes(S, K, T, r, sigma, opt_type="call"):
    """Black-Scholes option pricing."""
    if T <= 0:
        if opt_type == "call": return max(0, S - K)
        return max(0, K - S)
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    if opt_type == "call":
        return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    return K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)

def compute_greeks(S, K, T, r, sigma, opt_type="call"):
    """Compute all Greeks."""
    if T <= 0:
        return {"price": black_scholes(S, K, T, r, sigma, opt_type),
                "delta": 0, "gamma": 0, "theta": 0, "vega": 0, "rho": 0}
    d1  = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2  = d1 - sigma * np.sqrt(T)
    phi = np.exp(-0.5 * d1**2) / np.sqrt(2 * np.pi)
    price = black_scholes(S, K, T, r, sigma, opt_type)
    if opt_type == "call":
        delta = norm.cdf(d1)
        rho   = K * T * np.exp(-r * T) * norm.cdf(d2) / 100
    else:
        delta = norm.cdf(d1) - 1
        rho   = -K * T * np.exp(-r * T) * norm.cdf(-d2) / 100
    gamma = phi / (S * sigma * np.sqrt(T))
    theta = ((-S * phi * sigma / (2 * np.sqrt(T)) -
              (r * K * np.exp(-r * T) * norm.cdf(d2 if opt_type=="call" else -d2)
               * (1 if opt_type=="call" else -1))) / 365)
    vega  = S * phi * np.sqrt(T) / 100
    return {"price": price, "delta": delta, "gamma": gamma,
            "theta": theta, "vega": vega, "rho": rho, "iv": sigma}

def implied_vol(mkt_price, S, K, T, r, opt_type="call", tol=1e-4):
    """Implied volatility via bisection."""
    lo, hi = 1e-4, 5.0
    for _ in range(100):
        mid = (lo + hi) / 2
        p   = black_scholes(S, K, T, r, mid, opt_type)
        if abs(p - mkt_price) < tol:
            return mid
        if p < mkt_price: lo = mid
        else:             hi = mid
    return (lo + hi) / 2

# ── Probability Engine ────────────────────────────────────────────────────

def return_probabilities(mu, sigma, horizon, target=0.12):
    """Log-normal return distribution probabilities."""
    muT   = mu * horizon
    sigT  = sigma * np.sqrt(horizon)
    z_loss   = -muT / sigT if sigT else 0
    z_target = (target * horizon - muT) / sigT if sigT else 0
    return {
        "prob_loss":   norm.cdf(z_loss) * 100,
        "prob_pos":    (1 - norm.cdf(z_loss)) * 100,
        "prob_beat":   (1 - norm.cdf(z_target)) * 100,
        "expected":    (np.exp(muT) - 1) * 100,
        "best":        (np.exp(muT + 1.645 * sigT) - 1) * 100,
        "worst":       (np.exp(muT - 1.645 * sigT) - 1) * 100,
    }

# ── Monte Carlo ───────────────────────────────────────────────────────────

def monte_carlo(mu, sigma, horizon, n=1000, initial=100):
    """GBM Monte Carlo simulation. Returns percentile outcomes."""
    dt    = 1 / 252
    steps = int(horizon * 252)
    rng   = np.random.default_rng(42)
    Z     = rng.standard_normal((n, steps))
    ret   = (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z
    paths = initial * np.exp(np.cumsum(ret, axis=1))
    final = paths[:, -1]
    max_dd= np.array([
        ((np.maximum.accumulate(p) - p) / np.maximum.accumulate(p)).max()
        for p in paths
    ]) * 100
    return {
        "p5":  np.percentile(final, 5),
        "p25": np.percentile(final, 25),
        "p50": np.percentile(final, 50),
        "p75": np.percentile(final, 75),
        "p95": np.percentile(final, 95),
        "prob_loss": (final < initial).mean() * 100,
        "avg_dd":    max_dd.mean(),
        "p90_dd":    np.percentile(max_dd, 90),
        "paths":     paths[:50],  # sample 50 for plotting
    }

def risk_parity_weights(sigmas):
    """Inverse-volatility risk-parity weights."""
    inv = np.array([1/s if s > 0 else 0 for s in sigmas])
    total = inv.sum()
    return (inv / total * 100) if total > 0 else np.ones(len(sigmas)) * 100 / len(sigmas)

# ══════════════════════════════════════════════════════════════════════════
# ADDITIONAL INDICATORS — added for best-in-class analysis
# ══════════════════════════════════════════════════════════════════════════

# ── Stochastic Oscillator ─────────────────────────────────────────────────
def compute_stochastic(df: pd.DataFrame, k_period=14, d_period=3) -> tuple:
    """Stochastic %K and %D. %K<20 oversold, %K>80 overbought."""
    lo  = df["Low"].rolling(k_period).min()
    hi  = df["High"].rolling(k_period).max()
    k   = 100 * (df["Close"] - lo) / (hi - lo + 1e-10)
    d   = k.rolling(d_period).mean()
    return k, d

# ── Stochastic RSI ────────────────────────────────────────────────────────
def compute_stoch_rsi(series: pd.Series, period=14) -> pd.Series:
    """Stochastic RSI — more sensitive than RSI. 0–1 scale."""
    rsi = compute_rsi(series, period)
    lo  = rsi.rolling(period).min()
    hi  = rsi.rolling(period).max()
    return (rsi - lo) / (hi - lo + 1e-10)

# ── OBV (On Balance Volume) ───────────────────────────────────────────────
def compute_obv(df: pd.DataFrame) -> pd.Series:
    """On Balance Volume — rising OBV + rising price = confirmed uptrend."""
    direction = np.where(df["Close"] > df["Close"].shift(1), 1,
                         np.where(df["Close"] < df["Close"].shift(1), -1, 0))
    return (direction * df["Volume"]).cumsum()

# ── Williams %R ───────────────────────────────────────────────────────────
def compute_williams_r(df: pd.DataFrame, period=14) -> pd.Series:
    """Williams %R. 0 to -100. Below -80 = oversold, above -20 = overbought."""
    hi  = df["High"].rolling(period).max()
    lo  = df["Low"].rolling(period).min()
    return -100 * (hi - df["Close"]) / (hi - lo + 1e-10)

# ── Ichimoku Cloud ────────────────────────────────────────────────────────
def compute_ichimoku(df: pd.DataFrame) -> dict:
    """Ichimoku Cloud components."""
    tenkan  = (df["High"].rolling(9).max()  + df["Low"].rolling(9).min())  / 2
    kijun   = (df["High"].rolling(26).max() + df["Low"].rolling(26).min()) / 2
    span_a  = ((tenkan + kijun) / 2).shift(26)
    span_b  = ((df["High"].rolling(52).max() + df["Low"].rolling(52).min()) / 2).shift(26)
    chikou  = df["Close"].shift(-26)
    c       = df["Close"].iloc[-1]
    sa      = span_a.iloc[-1] if not span_a.isna().iloc[-1] else None
    sb      = span_b.iloc[-1] if not span_b.isna().iloc[-1] else None
    signal  = ("Above Cloud" if sa and sb and c > max(sa,sb)
               else "Below Cloud" if sa and sb and c < min(sa,sb)
               else "In Cloud")
    return {"tenkan": tenkan, "kijun": kijun, "span_a": span_a,
            "span_b": span_b, "signal": signal, "sa_last": sa, "sb_last": sb}

# ── Pivot Points ──────────────────────────────────────────────────────────
def compute_pivot_points(df: pd.DataFrame) -> dict:
    """Daily pivot points (S1/S2/S3, R1/R2/R3) from previous session."""
    if len(df) < 2:
        return {}
    h = float(df["High"].iloc[-2])
    l = float(df["Low"].iloc[-2])
    c = float(df["Close"].iloc[-2])
    p = (h + l + c) / 3
    return {
        "Pivot": round(p, 2),
        "R1": round(2*p - l, 2),
        "R2": round(p + (h - l), 2),
        "R3": round(h + 2*(p - l), 2),
        "S1": round(2*p - h, 2),
        "S2": round(p - (h - l), 2),
        "S3": round(l - 2*(h - p), 2),
    }

# ── Sharpe & Sortino Ratios ───────────────────────────────────────────────
def compute_sharpe(df: pd.DataFrame, rf_rate: float = 0.065, period: int = 252) -> float:
    """Annualised Sharpe Ratio. >1 good, >2 excellent, >3 exceptional."""
    rets = df["Close"].pct_change().dropna()
    if len(rets) < 30:
        return None
    ann_ret = rets.mean() * period
    ann_vol = rets.std() * np.sqrt(period)
    return round((ann_ret - rf_rate) / ann_vol, 3) if ann_vol > 0 else None

def compute_sortino(df: pd.DataFrame, rf_rate: float = 0.065, period: int = 252) -> float:
    """Sortino Ratio — like Sharpe but only penalises downside vol."""
    rets = df["Close"].pct_change().dropna()
    if len(rets) < 30:
        return None
    ann_ret = rets.mean() * period
    neg     = rets[rets < 0]
    dd_vol  = neg.std() * np.sqrt(period)
    return round((ann_ret - rf_rate) / dd_vol, 3) if dd_vol > 0 else None

# ── Value at Risk (VaR / CVaR) ────────────────────────────────────────────
def compute_var(df: pd.DataFrame, confidence: float = 0.95) -> dict:
    """
    Parametric VaR and CVaR (Expected Shortfall) at given confidence.
    Returns daily worst-case loss percentages.
    """
    rets = df["Close"].pct_change().dropna()
    if len(rets) < 30:
        return {}
    var95  = float(np.percentile(rets, (1 - confidence) * 100))
    cvar95 = float(rets[rets <= var95].mean())
    var99  = float(np.percentile(rets, 1))
    return {
        "VaR_95%":  round(var95 * 100, 2),   # daily, negative = loss
        "CVaR_95%": round(cvar95 * 100, 2),
        "VaR_99%":  round(var99 * 100, 2),
        "Ann_Vol":  round(rets.std() * np.sqrt(252) * 100, 2),
        "Skewness": round(float(rets.skew()), 3),
        "Kurtosis": round(float(rets.kurt()), 3),
    }

# ── Kelly Criterion ───────────────────────────────────────────────────────
def kelly_position_size(win_prob: float, win_return: float, loss_return: float,
                         capital: float, max_kelly_fraction: float = 0.25) -> dict:
    """
    Kelly Criterion optimal position size.
    win_prob: probability of winning (0-1)
    win_return: gain if win (e.g. 0.20 = 20%)
    loss_return: loss if lose (e.g. 0.10 = 10%, positive number)
    max_kelly_fraction: cap at this fraction (safety — full Kelly is too aggressive)
    """
    q = 1 - win_prob
    if loss_return <= 0 or win_prob <= 0:
        return {"kelly_pct": 0, "half_kelly_pct": 0, "quarter_kelly_pct": 0, "amount": 0}
    b   = win_return / loss_return
    k   = (b * win_prob - q) / b
    k   = max(0, min(k, max_kelly_fraction))  # cap at max
    half_k    = k / 2
    quarter_k = k / 4
    return {
        "kelly_pct":         round(k * 100, 1),
        "half_kelly_pct":    round(half_k * 100, 1),
        "quarter_kelly_pct": round(quarter_k * 100, 1),
        "kelly_amount":      round(capital * k, 0),
        "half_kelly_amount": round(capital * half_k, 0),
        "interpretation":    ("Aggressive" if k > 0.20 else
                              "Moderate" if k > 0.10 else
                              "Conservative" if k > 0 else "Skip trade"),
    }

# ── RS Rating (IBD Relative Strength) ────────────────────────────────────
def compute_rs_rating(stock_returns: dict, nifty_returns: dict) -> int:
    """
    IBD-style Relative Strength Rating (1-99).
    Measures stock performance vs Nifty 50 across 4 time periods.
    Weighted: 40% recent quarter + 20% each prior quarter.
    """
    # stock_returns and nifty_returns: dicts with keys '3M','6M','9M','12M'
    def rel(period):
        sr = stock_returns.get(period, 0) or 0
        nr = nifty_returns.get(period, 0) or 0
        return sr - nr  # alpha vs Nifty

    rs_raw = (0.40 * rel('3M') + 0.20 * rel('6M') +
              0.20 * rel('9M') + 0.20 * rel('12M'))
    return rs_raw  # raw score — will be percentile-ranked vs universe

def percentile_rank(value: float, universe: list) -> int:
    """Convert raw RS score to 1-99 percentile rank."""
    clean = [v for v in universe if v is not None and not np.isnan(v)]
    if not clean:
        return 50
    rank = sum(1 for v in clean if v <= value) / len(clean) * 99
    return max(1, min(99, int(rank)))

# ── Enhanced all-signals ──────────────────────────────────────────────────
def compute_all_signals_enhanced(df: pd.DataFrame) -> dict:
    """Full technical signal suite including all new indicators."""
    base = compute_all_signals(df)
    if df is None or len(df) < 14:
        return base

    c = df["Close"]
    enhanced = dict(base)

    # Stochastic
    try:
        k, d = compute_stochastic(df)
        k_v  = k.iloc[-1]; d_v = d.iloc[-1]
        if not np.isnan(k_v):
            enhanced["stoch_k"]   = round(k_v, 1)
            enhanced["stoch_d"]   = round(d_v, 1) if not np.isnan(d_v) else None
            enhanced["stoch_sig"] = ("Oversold" if k_v < 20 else "Overbought" if k_v > 80 else "Neutral")
    except Exception: pass

    # OBV
    try:
        obv = compute_obv(df)
        obv_ma = obv.rolling(20).mean()
        obv_trend = "Rising" if obv.iloc[-1] > obv_ma.iloc[-1] else "Falling"
        enhanced["obv_trend"] = obv_trend
        enhanced["obv_confirm"] = (obv_trend == "Rising" and base.get("score",0) > 0)
    except Exception: pass

    # Williams %R
    try:
        wr = compute_williams_r(df)
        wr_v = wr.iloc[-1]
        if not np.isnan(wr_v):
            enhanced["williams_r"] = round(wr_v, 1)
            enhanced["wr_signal"]  = ("Oversold" if wr_v < -80 else "Overbought" if wr_v > -20 else "Neutral")
    except Exception: pass

    # Pivot Points
    try:
        enhanced["pivots"] = compute_pivot_points(df)
    except Exception: pass

    # Ichimoku
    try:
        if len(df) >= 52:
            ichi = compute_ichimoku(df)
            enhanced["ichimoku"] = ichi["signal"]
    except Exception: pass

    # Sharpe & Sortino
    try:
        enhanced["sharpe"]  = compute_sharpe(df)
        enhanced["sortino"] = compute_sortino(df)
    except Exception: pass

    # VaR
    try:
        if len(df) >= 60:
            enhanced["var"] = compute_var(df)
    except Exception: pass

    # Relative Volume
    try:
        if "Volume" in df.columns:
            avg_vol  = df["Volume"].rolling(20).mean().iloc[-1]
            cur_vol  = df["Volume"].iloc[-1]
            enhanced["rel_volume"] = round(cur_vol / avg_vol, 2) if avg_vol > 0 else None
    except Exception: pass

    return enhanced
