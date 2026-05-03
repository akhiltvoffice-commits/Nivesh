"""Compare — side-by-side fundamentals for 2-4 stocks."""
import streamlit as st
from utils.style import inject_css, theme_toggle
import pandas as pd
from utils.data import get_fundamentals

st.set_page_config(page_title="Compare — NIVESH", page_icon="🔗", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("🔗 Compare Stocks")
st.caption("Side-by-side fundamental comparison · 19 metrics · Star marks best in class")

PRESETS = {
    "Banks":     ["HDFCBANK","ICICIBANK","AXISBANK","KOTAKBANK"],
    "IT":        ["TCS","INFOSYS","HCLTECH","WIPRO"],
    "FMCG":      ["HINDUNILVR","ITC","NESTLEIND","DABUR"],
    "Auto":      ["MARUTI","TATAMOTORS","BAJAJ-AUTO","EICHERMOT"],
    "Pharma":    ["SUNPHARMA","DRREDDY","CIPLA","DIVISLAB"],
}

col1, col2 = st.columns([3,1])
with col1:
    symbols_raw = st.text_input("Enter 2–4 NSE symbols (comma separated)",
                                 placeholder="e.g. TCS, INFOSYS, WIPRO, HCLTECH")
with col2:
    preset = st.selectbox("Or use preset", ["—"] + list(PRESETS.keys()))

if preset != "—":
    symbols = PRESETS[preset]
elif symbols_raw:
    symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()][:4]
else:
    symbols = []

if len(symbols) < 2:
    st.info("Enter at least 2 stock symbols or pick a preset")
    st.stop()

# Fetch fundamentals
with st.spinner(f"Fetching data for {', '.join(symbols)}..."):
    infos = {s: get_fundamentals(s) for s in symbols}

METRICS = [
    ("Price ₹",          lambda i: f"₹{i.get('regularMarketPrice',0):,.2f}",            None),
    ("Day Change",        lambda i: f"{i.get('regularMarketChangePercent',0)*100:+.2f}%", "max"),
    ("Market Cap",        lambda i: f"₹{i.get('marketCap',0)/1e7:.0f}Cr",               "max"),
    ("P/E (TTM)",         lambda i: f"{i.get('trailingPE','—')}",                        "min"),
    ("P/E (Forward)",     lambda i: f"{i.get('forwardPE','—')}",                         "min"),
    ("P/B Ratio",         lambda i: f"{i.get('priceToBook','—')}",                       "min"),
    ("EV/EBITDA",         lambda i: f"{i.get('enterpriseToEbitda','—')}",                "min"),
    ("EPS ₹",             lambda i: f"₹{i.get('trailingEps','—')}",                     "max"),
    ("ROE",               lambda i: f"{i.get('returnOnEquity',0)*100:.1f}%" if i.get('returnOnEquity') else "—", "max"),
    ("ROA",               lambda i: f"{i.get('returnOnAssets',0)*100:.1f}%" if i.get('returnOnAssets') else "—", "max"),
    ("Net Margin",        lambda i: f"{i.get('profitMargins',0)*100:.1f}%" if i.get('profitMargins') else "—", "max"),
    ("Operating Margin",  lambda i: f"{i.get('operatingMargins',0)*100:.1f}%" if i.get('operatingMargins') else "—", "max"),
    ("Revenue Growth",    lambda i: f"{i.get('revenueGrowth',0)*100:.1f}%" if i.get('revenueGrowth') else "—", "max"),
    ("Earnings Growth",   lambda i: f"{i.get('earningsGrowth',0)*100:.1f}%" if i.get('earningsGrowth') else "—", "max"),
    ("Debt/Equity",       lambda i: f"{i.get('debtToEquity','—')}",                      "min"),
    ("Current Ratio",     lambda i: f"{i.get('currentRatio','—')}",                      "max"),
    ("FCF",               lambda i: f"₹{i.get('freeCashflow',0)/1e7:.0f}Cr" if i.get('freeCashflow') else "—", "max"),
    ("Div Yield",         lambda i: f"{i.get('dividendYield',0)*100:.2f}%" if i.get('dividendYield') else "—", "max"),
    ("Beta",              lambda i: f"{i.get('beta','—')}",                               None),
    ("Analyst Target",    lambda i: f"₹{i.get('targetMeanPrice','—')}",                  None),
    ("Recommendation",    lambda i: str(i.get('recommendationKey','—')).upper(),          None),
]

def get_raw(info, metric_name):
    raw_map = {
        "P/E (TTM)": "trailingPE", "P/E (Forward)": "forwardPE", "P/B Ratio": "priceToBook",
        "EV/EBITDA": "enterpriseToEbitda", "EPS ₹": "trailingEps",
        "ROE": "returnOnEquity", "ROA": "returnOnAssets", "Net Margin": "profitMargins",
        "Operating Margin": "operatingMargins", "Revenue Growth": "revenueGrowth",
        "Earnings Growth": "earningsGrowth", "Debt/Equity": "debtToEquity",
        "Current Ratio": "currentRatio", "FCF": "freeCashflow", "Div Yield": "dividendYield",
        "Day Change": "regularMarketChangePercent", "Market Cap": "marketCap",
    }
    key = raw_map.get(metric_name)
    return info.get(key) if key else None

# Build comparison table
rows = []
for label, fmt_fn, best in METRICS:
    row = {"Metric": label}
    raw_vals = {s: get_raw(infos[s], label) for s in symbols}
    valid_raws = {s: v for s, v in raw_vals.items() if v is not None and isinstance(v, (int,float))}

    best_sym = None
    if best and valid_raws:
        if best == "max": best_sym = max(valid_raws, key=valid_raws.get)
        else:             best_sym = min(valid_raws, key=valid_raws.get)

    for s in symbols:
        val = fmt_fn(infos[s])
        if best_sym == s: val = f"⭐ {val}"
        row[s] = val
    rows.append(row)

df = pd.DataFrame(rows)
st.dataframe(df, use_container_width=True, hide_index=True,
             column_config={s: st.column_config.TextColumn(s, width="medium") for s in symbols})

st.caption("⭐ = Best value in comparison for that metric")

# Analyst consensus comparison
st.divider()
st.subheader("Analyst Consensus")
cols = st.columns(len(symbols))
for i, s in enumerate(symbols):
    info = infos[s]
    with cols[i]:
        rec = str(info.get("recommendationKey","—")).upper()
        target = info.get("targetMeanPrice","—")
        price  = info.get("regularMarketPrice",0)
        upside = ((target/price - 1)*100) if isinstance(target,(int,float)) and price else None
        color  = "#10D98D" if "BUY" in rec else "#FF4757" if "SELL" in rec else "#F59E0B"
        st.markdown(f"""<div style="background:{color}18;border:1px solid {color}44;border-radius:8px;padding:12px;text-align:center">
            <div style="font-family:monospace;font-weight:700;font-size:15px;color:#F1F5F9">{s}</div>
            <div style="color:{color};font-weight:700;margin:4px 0">{rec}</div>
            <div style="font-size:12px;color:#8DA4BF">Target: ₹{target}</div>
            {f'<div style="font-size:12px;color:{color}">Upside: {upside:+.1f}%</div>' if upside else ''}
        </div>""", unsafe_allow_html=True)
