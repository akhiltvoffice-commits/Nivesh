"""Watchlist — track stocks with live prices, P&L, AI analysis on click."""
import streamlit as st
from utils.style import inject_css, theme_toggle, research_card
import pandas as pd
from utils.data import get_multiple_quotes
from utils.ai_utils import auto_research_stock
from utils.data import get_nse_live_multiple, get_nse_live_quote, get_fundamentals, get_history, is_market_open
from utils.math_utils import compute_all_signals
from utils import ai_utils

st.set_page_config(page_title="Watchlist — NIVESH", page_icon="⭐", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("⭐ Watchlist")
st.caption("Track stocks live · P&L tracking · Click any stock for AI analysis")

# ── Session state init ─────────────────────────────────────────────────────
if "watchlist" not in st.session_state:
    st.session_state.watchlist = ["RELIANCE","TCS","HDFCBANK","ZOMATO","TATAMOTORS"]
if "buy_prices" not in st.session_state:
    st.session_state.buy_prices = {}

# ── Add stock ──────────────────────────────────────────────────────────────
with st.expander("➕ Add Stock to Watchlist"):
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_sym = st.text_input("Symbol", placeholder="e.g. INFY", key="new_sym").upper().strip()
    with col2:
        buy_px  = st.number_input("Buy Price ₹ (optional)", min_value=0.0, key="buy_px")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Add", type="primary"):
            if new_sym and new_sym not in st.session_state.watchlist:
                st.session_state.watchlist.append(new_sym)
                if buy_px > 0:
                    st.session_state.buy_prices[new_sym] = buy_px
                st.success(f"Added {new_sym}")
                st.rerun()

    # Quick add popular
    st.markdown("**Quick add:**")
    quick = ["INFY","WIPRO","BAJFINANCE","ICICIBANK","NTPC","APOLLOHOSP","TITAN","DMART"]
    qcols = st.columns(8)
    for i, s in enumerate(quick):
        if s not in st.session_state.watchlist:
            if qcols[i].button(f"+ {s}"):
                st.session_state.watchlist.append(s)
                st.rerun()

# ── Remove ─────────────────────────────────────────────────────────────────
if st.session_state.watchlist:
    remove = st.multiselect("Remove stocks", st.session_state.watchlist)
    if remove and st.button("Remove selected"):
        st.session_state.watchlist = [s for s in st.session_state.watchlist if s not in remove]
        st.rerun()

st.divider()

# ── Live quotes ────────────────────────────────────────────────────────────
if not st.session_state.watchlist:
    st.info("Watchlist empty. Add stocks above.")
    st.stop()

with st.spinner("Fetching live prices from NSE..."):
    df = get_nse_live_multiple(st.session_state.watchlist)
    if df.empty:  # fallback
        df = get_multiple_quotes(st.session_state.watchlist)
    mkt_open = is_market_open()

if df.empty:
    st.warning("Could not fetch prices. Check connection.")
    st.stop()

# Summary metrics
adv = (df["Change%"] > 0).sum()
dec = (df["Change%"] < 0).sum()
c1,c2,c3,c4 = st.columns(4)
source_str = "NSE Live" if ("Source" in df.columns and not df.empty and "NSE" in str(df["Source"].iloc[0])) else "yfinance"
delay_str  = "~15 sec delay" if "NSE" in source_str else "15-20 min delay"
st.markdown(f'''<span style="background:#10D98D22;border:1px solid #10D98D44;color:#10D98D;padding:2px 8px;border-radius:8px;font-size:10px;font-weight:700">📡 {source_str}</span>&nbsp;
<span style="color:#64748B;font-size:10px">{delay_str}</span>''', unsafe_allow_html=True)
c1.metric("Watching", len(df))
c2.metric("Advancing", adv)
c3.metric("Declining", dec)
avg_chg = df["Change%"].mean()
c4.metric("Avg Move", f"{avg_chg:+.2f}%")

# Stock cards
cols = st.columns(min(4, len(df)))
for i, row in df.iterrows():
    sym   = row["Symbol"]
    price = row["Price"]
    chg   = row["Change"]
    pct   = row["Change%"]
    up    = chg >= 0
    color = "#10D98D" if up else "#FF4757"
    bp    = st.session_state.buy_prices.get(sym)
    unr   = ((price - bp) / bp * 100) if bp else None

    vwap_v     = row.get('VWAP') or row.get('vwap')
    upper_ckt  = row.get('Upper Ckt') or row.get('upperCircuit')
    lower_ckt  = row.get('Lower Ckt') or row.get('lowerCircuit')
    high_v     = row.get('High') or 0
    low_v      = row.get('Low') or 0
    high_str   = f"{high_v:,.0f}" if high_v else "—"
    low_str    = f"{low_v:,.0f}"  if low_v  else "—"
    vwap_str   = f'<span>|</span><span>VWAP:₹{vwap_v:,.0f}</span>' if vwap_v else ""
    circuit_str= f'<div style="font-size:9px;color:#64748B">Circuit: ₹{lower_ckt}–₹{upper_ckt}</div>' if upper_ckt else ""
    with cols[i % 4]:
        st.markdown(f"""  <div style="background:#111827;border:1px solid {'#10D98D44' if up else '#FF475744'};border-radius:10px;padding:14px;margin-bottom:8px">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                <span style="font-family:monospace;font-weight:700;color:#F1F5F9;font-size:15px">{sym}</span>
                <span style="font-size:11px">{'🟢' if up else '🔴'}</span>
            </div>
            <div style="font-family:monospace;font-size:20px;font-weight:700;color:#F1F5F9">₹{price:,.2f}</div>
            <div style="font-family:monospace;font-size:12px;color:{color}">{chg:+.2f} ({pct:+.2f}%)</div>
            {'<div style="font-size:11px;color:#8DA4BF;margin-top:4px">Buy: ₹' + f'{bp:.0f} → <span style="color:' + color + '">' + f'{unr:+.1f}%</span></div>' if unr is not None else ''}
            <div style="display:flex;gap:4px;margin-top:8px;font-size:11px;color:#8DA4BF">
                <span>H:₹{high_str}</span><span>|</span><span>L:₹{low_str}</span>{vwap_str}
            </div>{circuit_str}
        </div>""", unsafe_allow_html=True)

st.divider()

# ── AI Analysis ─────────────────────────────────────────────────────────────
st.subheader("🤖 AI Analysis — Select Watchlist Stock")
col1, col2 = st.columns([3,1])
with col1:
    selected = st.selectbox("Stock", df["Symbol"].tolist(), label_visibility="collapsed")
with col2:
    run_ai = st.button("🤖 Analyse", type="primary", use_container_width=True)

if run_ai and selected:
    with st.spinner(f"Analysing {selected}..."):
        hist    = get_history(selected, "1y", "1d")
        info    = get_fundamentals(selected)
        signals = compute_all_signals(hist) if not hist.empty else {}

    if signals:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("RSI", f"{signals['rsi']:.1f}")
        c2.metric("Signal", signals["overall"])
        c3.metric("Stop 1.5×ATR", f"₹{signals['stop_1x']:.0f}")
        c4.metric("Stop 2.5×ATR", f"₹{signals['stop_2x']:.0f}")

    with st.spinner("Gemini deep analysis..."):
        result = ai_utils.analyse_stock(info, signals or {})
    st.markdown(result)
    st.error("⚠️ AI research only — not investment advice.")

# ── Auto-refresh ─────────────────────────────────────────────────────────
st.divider()
st.caption("💡 Tip: Press F5 or click 'Run Screener' to refresh prices. Streamlit auto-refreshes when you interact with the page.")
if st.button("🔄 Refresh Prices"):
    st.cache_data.clear()
    st.rerun()
