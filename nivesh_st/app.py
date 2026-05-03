"""
NIVESH — Indian Investment OS
Market Pulse — LIVE data from NSE India (~15 sec delay for Indian stocks)
"""
import streamlit as st
from utils.style import inject_css, theme_toggle
import pandas as pd
from datetime import datetime
import time

st.set_page_config(
    page_title="NIVESH — Live Indian Investment OS",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stSidebar"] { background-color:#0D111C; }
  div[data-testid="metric-container"] { background:#111827; border:1px solid #1E2A3A; border-radius:10px; padding:12px; }
  .live-badge { background:#10D98D22; border:1px solid #10D98D55; color:#10D98D;
                padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700; }
  .delayed-badge { background:#F59E0B22; border:1px solid #F59E0B55; color:#F59E0B;
                   padding:2px 8px; border-radius:10px; font-size:10px; font-weight:700; }
  .closed-badge { background:#4B5E7822; border:1px solid #4B5E7844; color:#8DA4BF;
                  padding:2px 8px; border-radius:10px; font-size:10px; }
</style>
""", unsafe_allow_html=True)

from utils.data import (get_macro, get_sectors, get_multiple_quotes,
                         get_nse_live_indices, get_nse_market_status,
                         market_status_label, INDICES, NIFTY50)
from utils.charts import sector_heatmap
from utils import ai_utils

# ── Market status — from NSE directly ─────────────────────────────────────
nse_status = get_nse_market_status()
status_text, status_color, mkt_open = market_status_label()
actual_open = nse_status.get("isOpen", mkt_open)
trade_date  = nse_status.get("tradeDate","")

# ── Header ─────────────────────────────────────────────────────────────────
col_title, col_status = st.columns([3,1])
with col_title:
    st.markdown("# 📈 NIVESH")
    st.caption("Indian Investment OS · NSE Live Data (~15 sec delay) · Gemini AI · v3.0")
with col_status:
    sub = f"Trade Date: {trade_date}" if trade_date else datetime.now().strftime('%d %b %Y, %H:%M IST')
    badge = "🟢 NSE Live Feed" if actual_open else "⛔ Market Closed"
    st.markdown(f"""<div style="background:{status_color}18;border:1px solid {status_color}44;border-radius:8px;padding:12px;text-align:center;margin-top:12px">
        <div style="color:{status_color};font-weight:700;font-size:13px">{status_text}</div>
        <div style="color:#8DA4BF;font-size:11px;margin-top:3px">{badge}</div>
        <div style="color:#64748B;font-size:10px;margin-top:2px">{sub}</div>
    </div>""", unsafe_allow_html=True)

# Data freshness note
if actual_open:
    st.success("🟢 **Market is OPEN** — Index data from NSE Live API (~15 sec delay). Fundamentals are quarterly (updated each results season).")
else:
    st.info("⛔ **Market is CLOSED** — Showing last recorded prices. NSE Live feed resumes at 9:15 AM IST on trading days.")

# Auto-refresh during market hours
auto_refresh = False  # default: off
if actual_open:
    col_r1, col_r2, col_r3 = st.columns([1,1,4])
    with col_r1:
        auto_refresh = st.toggle("🔄 Auto-Refresh", value=False, help="Refresh live data every 30 seconds")
    with col_r2:
        if st.button("Refresh Now"):
            st.cache_data.clear()
            st.rerun()

st.divider()

# ── LIVE INDICES from NSE API ──────────────────────────────────────────────
st.subheader("🏦 NSE Indices — Live Feed" if actual_open else "🏦 NSE Indices — Last Recorded")
st.markdown("""<span class="live-badge">NSE India API</span>&nbsp;
<span style="font-size:11px;color:#64748B">~15 second delay for indices · Updates on refresh</span>""",
unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

live_indices = get_nse_live_indices()
key_indices  = ["NIFTY 50","NIFTY BANK","NIFTY IT","NIFTY MIDCAP 100","INDIA VIX"]

if not live_indices.empty:
    sub_idx = live_indices[live_indices["Index"].isin(key_indices)]
    cols = st.columns(len(sub_idx) if not sub_idx.empty else 5)
    for i, (_, row) in enumerate(sub_idx.iterrows()):
        price = row["Price"]
        pct   = row["Change%"]
        chg   = row["Change"]
        up    = pct >= 0 if pct is not None else True
        with cols[i]:
            st.metric(
                label=row["Index"],
                value=f"{price:,.2f}" if price else "—",
                delta=f"{chg:+.2f} ({pct:+.2f}%)" if pct is not None else None,
            )
else:
    # Fallback to yfinance if NSE API fails
    st.warning("⚠️ NSE Live Feed unavailable (rate-limited or maintenance) — showing yfinance data (15-20 min delay). Retry in 30 seconds.")
    macro_df = get_macro()
    if not macro_df.empty:
        idx_data = macro_df[macro_df["Symbol"].isin(list(INDICES.values()))]
        cols = st.columns(4)
        for i, (name, sym) in enumerate(INDICES.items()):
            row = idx_data[idx_data["Symbol"]==sym]
            if row.empty: continue
            price = row["Price"].iloc[0]; chg = row["Change"].iloc[0]; pct = row["Change%"].iloc[0]
            with cols[i]:
                st.metric(name, f"{price:,.2f}", f"{chg:+.2f} ({pct:+.2f}%)")

# ── All NSE Indices grid ───────────────────────────────────────────────────
if not live_indices.empty:
    with st.expander("📊 All NSE Indices — Full Live Dashboard"):
        display_idx = live_indices.copy()
        display_idx["Price"]   = display_idx["Price"].map(lambda x: f"{x:,.2f}" if x else "—")
        display_idx["Change"]  = display_idx["Change"].map(lambda x: f"{x:+.2f}" if x is not None else "—")
        display_idx["Change%"] = display_idx["Change%"].map(lambda x: f"{x:+.2f}%" if x is not None else "—")
        st.dataframe(display_idx[["Index","Price","Change","Change%","Open","High","Low"]],
                    use_container_width=True, hide_index=True)

st.divider()

# ── Sector Heatmap ─────────────────────────────────────────────────────────
st.subheader("🔥 Sector Performance")
st.markdown("""<span class="delayed-badge">yfinance ~15-20 min delay</span>""", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Fetching sector data..."):
    sector_df = get_sectors()

if not sector_df.empty:
    st.plotly_chart(sector_heatmap(sector_df), use_container_width=True)
    scols = st.columns(min(11, len(sector_df)))
    for i, (_, row) in enumerate(sector_df.iterrows()):
        pct = row["Change%"]
        color = "#10D98D" if pct>1 else "#6EE7B7" if pct>0 else "#FCA5A5" if pct>-1 else "#FF4757"
        with scols[i % len(scols)]:
            st.markdown(f"""<div style="background:{color}18;border:1px solid {color}44;border-radius:8px;padding:8px;text-align:center">
                <div style="font-size:10px;color:#CBD5E1;font-weight:600">{row['Sector']}</div>
                <div style="font-family:monospace;font-weight:700;font-size:13px;color:{color}">{pct:+.2f}%</div>
            </div>""", unsafe_allow_html=True)

st.divider()

# ── Global Macro ───────────────────────────────────────────────────────────
st.subheader("🌍 Global Markets & Macro")
st.markdown("""<span class="delayed-badge">yfinance ~15-20 min delay</span>&nbsp;
<span style="font-size:10px;color:#64748B">US · Asia · Europe · Currencies · Commodities · Rates</span>""",
unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

with st.spinner("Fetching global market data..."):
    macro_df = get_macro()
    idx_syms = list(INDICES.values())

if not macro_df.empty:
    macro_show = macro_df[~macro_df["Symbol"].isin(idx_syms)]
    # Group display
    US_NAMES     = ["S&P 500","NASDAQ","Dow Jones","US 10Y"]
    ASIA_NAMES   = ["Nikkei 225","Hang Seng"]
    EUR_NAMES    = ["FTSE 100"]
    COMM_NAMES   = ["Brent Crude","Gold","Silver","Copper"]
    FX_NAMES     = ["USD/INR","DXY (Dollar Index)"]

    def show_group(label, names, df):
        grp = df[df["Name"].isin(names)]
        if grp.empty: return
        st.markdown(f'<div class="nv-label" style="margin:8px 0 4px 0">{label}</div>', unsafe_allow_html=True)
        cols = st.columns(len(grp)+1)
        for i, (_, row) in enumerate(grp.iterrows()):
            pct = row["Change%"]; price = row["Price"]; name = row["Name"]
            if "INR" in row.get("Symbol","") or name=="USD/INR":   val = f"₹{price:.2f}"
            elif name in ["Gold","Silver","Brent Crude","WTI Crude","Copper"]: val = f"${price:.2f}"
            elif "10Y" in name or "Rate" in name:                   val = f"{price:.2f}%"
            elif name=="DXY (Dollar Index)":                         val = f"{price:.2f}"
            else:                                                     val = f"{price:,.2f}"
            with cols[i]: st.metric(name, val, f"{pct:+.2f}%")

    show_group("🇺🇸 United States", US_NAMES, macro_show)
    show_group("🌏 Asia", ASIA_NAMES, macro_show)
    show_group("🌍 Europe", EUR_NAMES, macro_show)
    show_group("🛢 Commodities", COMM_NAMES, macro_show)
    show_group("💱 FX & Dollar", FX_NAMES, macro_show)

    # Any remaining
    shown_names = US_NAMES+ASIA_NAMES+EUR_NAMES+COMM_NAMES+FX_NAMES
    others = macro_show[~macro_show["Name"].isin(shown_names)]
    if not others.empty:
        cols = st.columns(4)
        for i, (_, row) in enumerate(others.iterrows()):
            with cols[i%4]:
                st.metric(row["Name"], f"{row['Price']:,.2f}", f"{row['Change%']:+.2f}%")

st.divider()

# ── Gainers / Losers from NSE (LIVE) ──────────────────────────────────────
st.subheader("📊 Nifty 50 — Live Movers")
st.markdown("""<span class="live-badge">NSE Live</span>&nbsp;
<span style="font-size:11px;color:#64748B">~15 sec delay · Individual NSE API calls</span>""",
unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

from utils.data import get_nse_live_multiple
with st.spinner("Fetching live Nifty 50 prices from NSE..."):
    stocks_df = get_nse_live_multiple(NIFTY50[:30])

# Fallback to yfinance if NSE fails
if stocks_df.empty:
    st.caption("NSE live unavailable — using yfinance (15-20 min delay)")
    stocks_df = get_multiple_quotes(NIFTY50[:30])

if not stocks_df.empty:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🟢 Top Gainers")
        g = stocks_df.nlargest(5,"Change%")[["Symbol","Price","Change%"]].copy()
        g["Price"]   = g["Price"].map("₹{:,.2f}".format)
        g["Change%"] = g["Change%"].map("{:+.2f}%".format)
        st.dataframe(g, use_container_width=True, hide_index=True)
    with col2:
        st.subheader("🔴 Top Losers")
        l = stocks_df.nsmallest(5,"Change%")[["Symbol","Price","Change%"]].copy()
        l["Price"]   = l["Price"].map("₹{:,.2f}".format)
        l["Change%"] = l["Change%"].map("{:+.2f}%".format)
        st.dataframe(l, use_container_width=True, hide_index=True)

    adv = (stocks_df["Change%"] > 0).sum()
    dec = (stocks_df["Change%"] < 0).sum()
    b1,b2,b3,b4 = st.columns(4)
    b1.metric("Advancing", adv)
    b2.metric("Declining", dec)
    b3.metric("Unchanged", len(stocks_df)-adv-dec)
    b4.metric("A/D Ratio",  f"{adv/dec:.2f}" if dec else "∞")

    # Last update time
    if "Last Update" in stocks_df.columns:
        last_update = stocks_df["Last Update"].dropna().iloc[0] if not stocks_df["Last Update"].dropna().empty else ""
        if last_update:
            st.caption(f"⏱️ NSE last update: {last_update}")

st.divider()

# ── DATA FRESHNESS TABLE ───────────────────────────────────────────────────
with st.expander("ℹ️ Data Sources & Freshness"):
    st.markdown("""
| Data Type | Source | Delay | Notes |
|-----------|--------|-------|-------|
| 🟢 NSE Index prices | NSE India API | ~15 seconds | Live feed during market hours |
| 🟢 Indian stock prices | NSE India API | ~15 seconds | Best available free source |
| 🟡 USD/INR, Crude, Gold, US indices | Yahoo Finance | 15-20 minutes | Industry standard free delay |
| 🟡 Sector indices | Yahoo Finance | 15-20 minutes | NSE sector indices |
| 🔵 Fundamentals (PE, ROE, etc.) | Yahoo Finance | Quarterly | Updated each results season (not intraday) |
| 🔵 Mutual Fund NAV | mfapi.in | End-of-day | NAV declared by 9 PM daily |
| 🔵 NSE Options Chain | NSE India API | ~15 seconds | Live during market hours |
| 🤖 AI Analysis | Gemini 3.1 Pro + Web Search | On-demand | Researches latest news via web |
""")

st.divider()

# ── AI Briefing ────────────────────────────────────────────────────────────
st.subheader("🤖 AI Market Briefing")
st.caption(f"Powered by {ai_utils.get_model_name()} with web search · Researches latest market news automatically")
if st.button("📰 Get Today's AI Briefing", type="primary"):
    with st.spinner("Gemini researching today's market..."):
        briefing = ai_utils.market_briefing()
    st.markdown(briefing)
    st.caption(f"Generated at {datetime.now().strftime('%H:%M IST')} by {ai_utils.get_model_name()}")

# ── Auto-refresh logic ─────────────────────────────────────────────────────
if actual_open and auto_refresh:
    st.caption(f"🔄 Auto-refresh active — next refresh in 30 seconds")
    time.sleep(30)
    st.cache_data.clear()
    st.rerun()
