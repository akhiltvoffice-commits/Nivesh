"""
ETF Tracker — Live NAV · Expense ratio · Exit load · AUM · Best ETF picks.
"""
import streamlit as st
import pandas as pd
from utils.style import inject_css, theme_toggle
from utils.data import get_fundamentals, get_history, get_live_etf_list
from utils.math_utils import compute_all_signals_enhanced
from utils import ai_utils

st.set_page_config(page_title="ETF Tracker — NIVESH", page_icon="💹", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)

st.title("💹 Indian ETF Tracker")
st.caption("Live NAV · Expense ratio · Exit load · AUM · Best ETF recommendations")

# ── ETF UNIVERSE with full details ────────────────────────────────────────
ETFS = [
    # Symbol, Name, Category, Benchmark, TER%, Exit Load, AUM Est (₹Cr), Min Invest
    ("NIFTYBEES.NS",  "Nippon Nifty BeES",         "Large Cap Index", "Nifty 50",          0.04, "Nil",   18000, "1 unit"),
    ("JUNIORBEES.NS", "Nippon Jr BeES",             "Mid Cap Index",   "Nifty Next 50",     0.19, "Nil",   4500,  "1 unit"),
    ("BANKBEES.NS",   "Nippon Bank BeES",           "Sectoral",        "Nifty Bank",        0.17, "Nil",   7200,  "1 unit"),
    ("ITBEES.NS",     "Nippon IT BeES",             "Sectoral",        "Nifty IT",          0.18, "Nil",   900,   "1 unit"),
    ("MOM100.NS",     "Mirae Nifty 100 ETF",        "Large Cap Index", "Nifty 100",         0.07, "Nil",   1200,  "1 unit"),
    ("LIQUIDBEES.NS", "Nippon Liquid BeES",         "Liquid/Cash",     "Overnight Rate",    0.05, "Nil",   35000, "1 unit"),
    ("GOLDBEES.NS",   "Nippon Gold BeES",           "Gold",            "Domestic Gold",     0.54, "Nil",   9800,  "1 unit"),
    ("SETFNN50.NS",   "SBI Nifty Next 50 ETF",      "Mid Cap Index",   "Nifty Next 50",     0.18, "Nil",   2100,  "1 unit"),
    ("ICICIB22.NS",   "ICICI Pru Bharat 22 ETF",    "PSU/Govt",        "Bharat 22 Index",   0.07, "Nil",   19000, "1 unit"),
    ("CPSE.NS",       "Nippon CPSE ETF",            "PSU",             "CPSE Index",        0.01, "Nil",   32000, "1 unit"),
    ("SETFNIF50.NS",  "SBI Nifty 50 ETF",           "Large Cap Index", "Nifty 50",          0.07, "Nil",   3500,  "1 unit"),
    ("MAFSETF.NS",    "Mirae Nifty Financial Svcs", "Sectoral",        "Nifty Fin Services",0.12, "Nil",   350,   "1 unit"),
    ("PHARMABEES.NS", "Nippon Pharma BeES",         "Sectoral",        "Nifty Pharma",      0.35, "Nil",   1100,  "1 unit"),
    ("AUTOBEES.NS",   "Nippon Auto BeES",           "Sectoral",        "Nifty Auto",        0.35, "Nil",   400,   "1 unit"),
    ("INFRABEES.NS",  "Nippon Infra BeES",          "Sectoral",        "Nifty Infra",       0.35, "Nil",   550,   "1 unit"),
    ("SILVERBEES.NS", "Nippon Silver BeES",         "Silver",          "Domestic Silver",   0.40, "Nil",   1200,  "1 unit"),
    ("MAFANG.NS",     "Mirae FANG+ ETF",            "Global Tech",     "NYSE FANG+",        0.53, "Nil",   1800,  "1 unit"),
    ("N100.NS",       "Nippon US ETF / Nasdaq 100", "International",   "NASDAQ 100",        0.50, "Nil",   2200,  "1 unit"),
]

# ── BEST ETF PICKS ────────────────────────────────────────────────────────
st.subheader("⭐ Best ETFs by Category")
st.caption("Lowest expense ratio in each category = highest long-term wealth retention")

best_picks = {
    "📈 Large Cap (Core holding)": {
        "ETF": "NIFTYBEES / SETFNIF50",
        "TER": "0.04–0.07% (lowest in India)",
        "Why": "Track Nifty 50. Lowest cost. Most liquid. Best for SIP core allocation (50–60% of equity portfolio).",
        "Avoid": "Actively managed large cap funds with TER > 1.5% — they rarely beat the index after costs",
        "color": "#22C55E"
    },
    "📊 Mid Cap (Growth)": {
        "ETF": "JUNIORBEES / SETFNN50",
        "TER": "0.18–0.19%",
        "Why": "Nifty Next 50 captures quality large-mid caps. Better risk-adjusted returns vs pure smallcap.",
        "Avoid": "Mid cap ETFs with TER > 0.5%",
        "color": "#F59E0B"
    },
    "🥇 Gold (Hedge / 10–15%)": {
        "ETF": "GOLDBEES",
        "TER": "0.54%",
        "Why": "Most liquid gold ETF. Better than Sovereign Gold Bonds for short-term. No making charges like physical.",
        "Avoid": "Gold funds (fund of funds) — add another 0.3–0.5% cost layer",
        "color": "#F59E0B"
    },
    "🏛 PSU/Govt (Value)": {
        "ETF": "CPSE ETF / BHARAT 22",
        "TER": "0.01–0.07% (near-zero cost!)",
        "Why": "Government divests via CPSE/Bharat 22. Extremely low cost. High dividend yield. Good for value investors.",
        "Avoid": "Only when global FII selling India hard",
        "color": "#3B82F6"
    },
    "💵 Cash Parking": {
        "ETF": "LIQUIDBEES",
        "TER": "0.05%",
        "Why": "Earn overnight rate (~6.5%) on idle money in trading account. No exit load. Settles T+0.",
        "Avoid": "Keeping cash idle in savings account (loses to inflation)",
        "color": "#22C55E"
    },
    "🌍 International / Tech": {
        "ETF": "N100 (NASDAQ 100) or MAFANG",
        "TER": "0.50–0.53%",
        "Why": "Diversification into US tech. Hedge if INR weakens. 10–15% of portfolio max.",
        "Avoid": "Over-allocating (more than 15%) — currency risk + US valuation risk",
        "color": "#A78BFA"
    },
}

cols = st.columns(3)
for i, (category, info) in enumerate(best_picks.items()):
    with cols[i%3]:
        st.markdown(f"""<div style="background:#111113;border-left:3px solid {info['color']};border-radius:0 8px 8px 0;padding:14px;margin:6px 0">
          <div style="font-size:13px;font-weight:700;color:#FAFAFA;margin-bottom:6px">{category}</div>
          <div style="font-size:14px;font-weight:700;color:{info['color']}">{info['ETF']}</div>
          <div style="font-size:11px;color:#F59E0B;margin:3px 0">TER: {info['TER']}</div>
          <div style="font-size:12px;color:#A1A1AA;margin-top:6px">{info['Why']}</div>
          <div style="font-size:11px;color:#EF4444;margin-top:4px">⚠️ {info['Avoid']}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── FULL ETF TABLE ────────────────────────────────────────────────────────
st.subheader("📊 Full ETF Universe — Live Data")

# Try to get live ETF list from NSE (auto-updates when new ETFs launch)
with st.spinner("Fetching live ETF list from NSE..."):
    live_etfs = get_live_etf_list()

if live_etfs:
    st.caption(f"✅ Live NSE ETF list: **{len(live_etfs)} ETFs** fetched (auto-updates daily). New ETFs appear within 24 hours of NSE listing.")
    # Show a searchable live list
    with st.expander(f"📋 All {len(live_etfs)} NSE-listed ETFs (live)", expanded=False):
        search_etf = st.text_input("Search ETF", placeholder="e.g. Nifty, Gold, Bank, Pharma...", key="etf_search")
        etf_df = __import__('pandas').DataFrame(live_etfs)
        if search_etf:
            etf_df = etf_df[
                etf_df["name"].str.contains(search_etf, case=False, na=False) |
                etf_df["symbol"].str.contains(search_etf.upper(), na=False) |
                etf_df["underlying"].str.contains(search_etf, case=False, na=False)
            ]
        st.dataframe(etf_df[["symbol","name","underlying"]].rename(columns={
            "symbol":"NSE Symbol","name":"ETF Name","underlying":"Tracks (Underlying Index)"
        }), use_container_width=True, hide_index=True)
        st.caption("Add .NS to symbol for yfinance. E.g. NIFTYBEES → NIFTYBEES.NS")
else:
    st.caption("⚠️ Could not fetch live ETF list from NSE. Showing curated list of 18 major ETFs below.")
st.caption("TER = Total Expense Ratio (annual cost). Lower = more wealth for you. All Indian ETFs have Nil exit load.")

rows = []
progress = st.progress(0, "Fetching live ETF prices...")
for i, (sym, name, cat, bench, ter, exit_load, aum, min_inv) in enumerate(ETFS):
    try:
        hist = get_history(sym.replace(".NS",""), "6mo", "1d")
        if hist.empty:
            import yfinance as yf
            hist = yf.Ticker(sym).history(period="6mo")
        price = float(hist["Close"].dropna().iloc[-1]) if not hist.empty else 0
        prev  = float(hist["Close"].dropna().iloc[-2]) if len(hist) > 1 else price
        chg   = (price/prev - 1)*100 if prev else 0
        ret1m = (price/hist["Close"].dropna().iloc[-21] - 1)*100 if len(hist) >= 21 else 0
        ret3m = (price/hist["Close"].dropna().iloc[-63] - 1)*100 if len(hist) >= 63 else 0
    except Exception:
        price = chg = ret1m = ret3m = 0

    rows.append({
        "ETF":          name,
        "Category":     cat,
        "Benchmark":    bench,
        "Price (₹)":    round(price, 2),
        "Day %":        round(chg, 2),
        "1M Return %":  round(ret1m, 2),
        "3M Return %":  round(ret3m, 2),
        "TER %":        ter,
        "Exit Load":    exit_load,
        "AUM (₹Cr)":   f"~{aum:,}",
        "Min Invest":   min_inv,
    })
    progress.progress((i+1)/len(ETFS))

progress.empty()
df = pd.DataFrame(rows)

# Format
for col in ["Price (₹)"]:
    df[col] = df[col].map(lambda x: f"₹{x:,.2f}" if x else "—")
for col in ["Day %","1M Return %","3M Return %"]:
    df[col] = df[col].map(lambda x: f"{x:+.2f}%")

st.dataframe(df, use_container_width=True, hide_index=True,
    column_config={
        "TER %": st.column_config.NumberColumn("TER % 💰",format="%.2f%%",
            help="Total Expense Ratio — annual cost. 0.04% on ₹1L = ₹40/year. Over 20 years, 1% TER = ₹3L+ lost to fees!"),
        "Exit Load": st.column_config.TextColumn("Exit Load",
            help="All Indian ETFs have NIL exit load. Buy/sell any time at market price."),
        "Day %": st.column_config.TextColumn("Day %",
            help="Today's price change"),
    })

st.info("💡 **TER impact over time:** On ₹10L for 20 years at 12% return: TER 0.04% → ₹93.5L vs TER 1.5% → ₹80.2L. **Difference = ₹13.3L** just from lower costs.")

st.divider()

# ── EXPENSE RATIO EXPLAINER ────────────────────────────────────────────────
st.subheader("💡 How to Choose an ETF")
st.markdown("""
**Rule 1 — Lowest TER wins** for same benchmark
TCS earns similar returns whether you pay 0.04% or 1.5% TER. Lower TER = more money stays with you.

**Rule 2 — Check liquidity** (daily volume × price)
NIFTYBEES trades ₹100Cr+ daily. Some sectoral ETFs trade only ₹1–2Cr. Low volume = large bid-ask spread = hidden cost.

**Rule 3 — Tracking Error matters**
How closely does the ETF track its benchmark? NIFTYBEES tracks Nifty 50 within 0.02%. High tracking error = performance drag.

**Rule 4 — ETF vs Index Fund**
Both are passive. ETF = stock exchange traded (no exit load, real-time price). Index fund = mutual fund (NAV once/day, may have exit load).

**Rule 5 — Gold/Silver ETFs vs Physical**
ETF gold = 99.9% purity, no storage cost, no making charges. Sell anytime. Better than physical for ₹50K+ amounts.
""")

st.divider()

# ── AI BEST ETF RECOMMENDATION ────────────────────────────────────────────
st.subheader("🤖 AI ETF Recommendation")
risk_profile = st.select_slider("Your Risk Profile",
    ["Conservative","Moderate-Conservative","Moderate","Moderate-Aggressive","Aggressive"])
amount = st.number_input("Monthly SIP or Lump Sum ₹", value=10000, step=5000, format="%d")
horizon = st.slider("Investment Horizon (years)", 1, 20, 7)

if st.button("🤖 Get AI ETF Portfolio", type="primary"):
    prompt = (
        f"Indian ETF portfolio recommendation:\n"
        f"Investor: {risk_profile} risk | ₹{amount:,} to invest | {horizon}-year horizon\n\n"
        f"Available ETFs with costs:\n"
        + "\n".join(f"- {name} ({cat}) TER={ter}% Benchmark={bench}"
                    for _, name, cat, bench, ter, _, _, _ in ETFS[:12])
        + f"\n\nProvide:\n"
        f"1. **Portfolio Allocation** — specific ETFs with % allocation and ₹ amount\n"
        f"2. **Rationale** — why this mix for {risk_profile} {horizon}-year investor\n"
        f"3. **SIP Strategy** — which to SIP, which to lump sum, and when\n"
        f"4. **TER Impact** — total annual cost of recommended portfolio\n"
        f"5. **Expected Range** — 10-year P25, P50, P75 wealth estimate\n"
        f"6. **What to avoid** — ETFs/categories not suitable for this profile"
    )
    with st.spinner("AI building ETF portfolio..."):
        result = ai_utils.generate(prompt, temperature=0.3, max_tokens=1200)
    st.markdown(result)
