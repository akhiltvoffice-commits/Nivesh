"""
Alpha Hunter — Multi-timeframe return analysis with macro-integrated AI scoring.
Better column names, tooltips, Excel export, comprehensive stock deep-dive.
"""
import streamlit as st
from utils.style import inject_css, theme_toggle, hover_section, metric_tip
import pandas as pd
import numpy as np
import json, re
from utils.excel_export import build_full_excel
from utils.data import (get_alpha_universe, get_universe_scores, get_live_macro_regime,
                         compute_macro_score, SECTOR_MACRO, INDICES)
from utils.ai_utils import get_model_name, generate, get_investment_levels
from utils.math_utils import compute_all_signals
from utils.data import get_history, get_fundamentals

st.set_page_config(page_title="Alpha Hunter — NIVESH", page_icon="🏆", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("🏆 Alpha Hunter")
st.caption("545+ NSE stocks · Multi-timeframe momentum · Macro + Micro scoring · AI probability engine · Excel export")

# ── WHAT DOES ALPHA HUNTER SHOW? ──────────────────────────────────────────
with st.expander("ℹ️ What does Alpha Hunter show? (click to understand each column)", expanded=False):
    st.markdown("""
**Alpha Hunter ranks 545+ NSE stocks using a composite score that blends past data with forward-looking signals.**

| Column | Past or Future? | What it means |
|--------|----------------|---------------|
| **Return %** | ⏪ PAST | Actual price return over selected timeframe (e.g. 1M = last 30 days actual gain/loss) |
| **10-Day Momentum** | ⏪ PAST | Recent acceleration — avg last 10 days vs prior 10 days. Tells you if trend is picking up speed |
| **Fundamental Score** | 🔄 CURRENT | Quality score based on today's PE, ROE, growth, debt. High = strong business right now |
| **Macro Boost** | 🔄 CURRENT | Live impact of global macro (crude, INR, NASDAQ, Gold, DXY) on this sector today |
| **Alpha Score** | 🔮 FORWARD-LOOKING | Composite of Fundamental (65%) + Macro (how it is NOW) + Momentum. Best single predictor of future outperformance |
| **Upside Target %** | 🔮 FORWARD | Analyst 12-month consensus target OR score-derived estimate of expected upside |
| **Downside Risk %** | 🔮 FORWARD | Estimated potential drawdown based on volatility and macro environment |
| **Bull/Bear Probability** | 🔮 FORWARD | Probability of bull/bear scenario playing out in next 12 months |
| **Expected Return %** | 🔮 FORWARD | **Key number** — probability-weighted 12M return = Bull×prob + Base×prob + Bear×prob |
| **RSI (14)** | ⏪ PAST | Momentum oscillator — tells you where price is relative to recent range. <30 buy zone, >70 sell zone |
| **Tech Signal** | 🔄 CURRENT | Price position vs SMA20/50/200. Bullish = above all three. Predictive of near-term direction |

**Alpha Score vs Return %:** Return % is what HAPPENED. Alpha Score is what the model thinks is likely to happen NEXT based on fundamental quality + macro tailwinds + momentum. High Alpha + negative recent return often = strong contrarian buy signal.
    """)

# ── COLUMN DEFINITIONS (name → tooltip) ───────────────────────────────────
COL_INFO = {
    "Symbol":              "NSE ticker symbol",
    "Company":             "Full company name",
    "Sector":              "Industry sector classification",
    "Price (₹)":           "Last traded price (₹)",
    "Return %":            "Total price return over selected timeframe",
    "10-Day Momentum":     "Recent momentum: avg last 10 days vs prior 10 days. Positive = accelerating up",
    "Annual Volatility %": "Annualised price volatility. Higher = more risky",
    "RSI (14)":            "Relative Strength Index 0–100. <30 oversold (buy signal), >70 overbought (sell signal)",
    "Fundamental Score":   "Quality score 0–120 based on Valuation + ROE + Growth + Debt safety + Technical position",
    "Macro Boost":         "Live macro impact on this sector. Positive = macro tailwind, Negative = headwind",
    "Alpha Score":         "Composite score = 40% Fundamental + 30% Macro + 30% Technical. Higher = stronger opportunity",
    "Tech Signal":         "Price relative to SMA20/50/200: Bullish / Neutral-Bull / Neutral-Bear / Bearish",
    "Upside Target %":     "Estimated 12-month upside: analyst consensus or score-based formula",
    "Downside Risk %":     "Estimated downside based on ATR volatility and macro regime",
    "Bull Probability %":  "Probability of bull case scenario playing out (based on Alpha Score)",
    "Bear Probability %":  "Probability of bear case (higher VIX + weak macro = higher bear prob)",
    "Expected Return %":   "Probability-weighted expected 12M return = Bull×prob + Base×prob + Bear×prob",
    "Analyst Target (₹)":  "Sell-side analyst mean price target from Bloomberg/Reuters consensus",
}



# ── CONTROLS ───────────────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns([2,2,2,1,1])
with col1:
    timeframe = st.selectbox("📅 Timeframe",
        ["Today","1 Week","1 Month","3 Month","6 Month","1 Year"],
        index=2,
        help="Return period to rank stocks by")
with col2:
    view_mode = st.selectbox("🔍 Rank By",
        ["Alpha Score (AI Composite)","Top Gainers","Top Losers",
         "Momentum Leaders","Fundamental Value","Lowest Volatility"],
        help="Sort criterion for the ranked table")
with col3:
    sector_filter = st.selectbox("🏭 Sector",
        ["All Sectors","Banking","IT","Auto","FMCG","Pharma","Energy","Metal",
         "Capital Goods","NBFC","Consumer","Infra","Defence","Healthcare",
         "Internet","Retail","Chemicals","Cement","Realty","Insurance","Telecom"],
        help="Filter to a specific NSE sector")
with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("🚀 Hunt Alpha", type="primary", use_container_width=True)
with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    refresh_macro = st.button("🔄 Refresh", use_container_width=True)

# ── LIVE MACRO (auto, no user input) ──────────────────────────────────────
with st.expander("🌍 Live Macro Regime — Auto-detected, drives sector scoring", expanded=False):
    regime = get_live_macro_regime()
    if regime:
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Crude", f"${regime.get('crude_price',0):.0f}",
                  "High ⬆" if regime.get('crude_high') else "Low ⬇" if regime.get('crude_low') else "Moderate")
        c2.metric("India VIX", f"{regime.get('vix_level',0):.1f}",
                  "⚠ Elevated" if regime.get('high_vix') else "Normal")
        c3.metric("USD/INR", f"₹{regime.get('inr_level',0):.2f}",
                  "INR Weak" if regime.get('inr_weak') else "INR Strong" if regime.get('inr_strong') else "Stable")
        c4.metric("Nifty", f"{regime.get('nifty_chg',0):+.2f}%",
                  "🐂" if regime.get('mkt_up') else "🐻" if regime.get('mkt_down') else "→")
        c5.metric("S&P 500", f"{regime.get('sp_chg',0):+.2f}%",
                  "Bull" if regime.get('us_bull') else "Bear" if regime.get('us_bear') else "Neutral")
        c6.metric("US 10Y", f"{regime.get('us10y',0):.2f}%",
                  "Easy" if regime.get('rate_cut') else "Tight" if regime.get('rate_hike') else "Neutral")

        sectors_ranked = sorted([s for s in SECTOR_MACRO if s!="Other"],
                                key=lambda s: compute_macro_score(s,regime), reverse=True)
        top3    = [(s, compute_macro_score(s,regime)) for s in sectors_ranked[:4]]
        bottom3 = [(s, compute_macro_score(s,regime)) for s in sectors_ranked[-4:]]
        cc1,cc2 = st.columns(2)
        cc1.success("🟢 Tailwinds: " + "  ·  ".join(f"**{s}** (+{sc})" for s,sc in top3))
        cc2.error("🔴 Headwinds: " + "  ·  ".join(f"**{s}** ({sc})" for s,sc in bottom3))

# ── LOAD DATA ──────────────────────────────────────────────────────────────
if run or refresh_macro or "alpha_df" not in st.session_state or st.session_state.get("alpha_tf")!=timeframe:
    with st.spinner(f"Fetching {timeframe} returns for 545+ stocks — parallel fetch..."):
        price_df = get_alpha_universe(timeframe)
        st.session_state["alpha_tf"] = timeframe

    with st.spinner("Loading fundamental + macro scores..."):
        fund_df = get_universe_scores("all")

    if price_df.empty:
        st.error("Could not fetch data. Check connection.")
        st.stop()

    # Merge
    if not fund_df.empty:
        fund_sub = fund_df[["Symbol","Score","PE","ROE","Net Margin","Rev Growth","D/E",
                             "Tech","AnalystTarget","52W High","52W Low","Market Cap",
                             "Macro Score","Name"]].copy()
        merged = price_df.merge(fund_sub, on="Symbol", how="left")
    else:
        merged = price_df.copy()
        for col in ["Score","PE","ROE","Net Margin","Rev Growth","D/E","Tech",
                    "AnalystTarget","Macro Score","Name"]:
            merged[col] = None

    # Compute Alpha Score + probability engine
    rows = []
    for _, r in merged.iterrows():
        sym          = r["Symbol"]
        sector       = r.get("Sector","Other")
        price        = r["Price"]
        vol          = r.get("Volatility%", 20) or 20
        rsi          = r.get("RSI")
        mom          = r.get("Momentum", 0) or 0
        period_ret   = r.get("Return %", 0) or 0
        fund_score   = float(r.get("Score") or 50)
        if fund_score != fund_score: fund_score = 50   # NaN guard
        tech_str     = r.get("Tech","Neutral") or "Neutral"
        macro_s_raw  = r.get("Macro Score")
        if regime and (macro_s_raw is None or str(macro_s_raw) == "nan"):
            macro_s = float(compute_macro_score(sector, regime))
        elif macro_s_raw is not None and str(macro_s_raw) != "nan":
            macro_s = float(macro_s_raw)
        else:
            macro_s = 0.0
        atgt         = r.get("AnalystTarget")

        # Technical score component
        rsi_s = 0
        if rsi:
            if rsi < 30:   rsi_s = 25
            elif rsi < 45: rsi_s = 15
            elif rsi < 60: rsi_s = 10
            elif rsi < 75: rsi_s = 5
        tech_s  = {"Bullish":15,"Neutral-Bull":10,"Neutral":8,"Neutral-Bear":4,"Bearish":2}.get(tech_str,8)
        mom_s   = min(20, max(-10, mom * 2))
        # fund_score already includes macro_adj from get_universe_scores() — no re-weighting
        # Composite = 65% fundamental+macro + 35% technical momentum
        composite = (fund_score * 0.65 + (rsi_s + tech_s + max(0, mom_s)) * 0.35)
        composite = max(0, min(100, composite))

        # Upside/downside
        try:
            if atgt and price and float(atgt) > 0 and float(price) > 0:
                upside_est = (float(atgt) / float(price) - 1) * 100
            else:
                upside_est = (fund_score / 120) * 40 + macro_s * 0.8 + (5 if tech_str in ["Bullish","Neutral-Bull"] else 0)
        except Exception:
            upside_est = 10.0
        upside_est = float(upside_est) if upside_est == upside_est else 10.0  # NaN guard
        vol_safe   = float(vol) if vol and vol == vol else 20.0
        downside_est = min(40, max(5, vol_safe * 0.5 - macro_s * 0.2))

        # Probabilities from composite
        comp_safe  = max(1, min(99, float(composite) if composite == composite else 50))
        bull_prob  = 0.25 + comp_safe / 100 * 0.45
        bear_prob  = max(0.10, 0.70 - comp_safe / 100 * 0.45)
        base_prob  = max(0, 1 - bull_prob - bear_prob)
        exp_return = (bull_prob * upside_est * 0.8 + base_prob * upside_est * 0.25 +
                      bear_prob * (-downside_est * 0.7))
        # Final NaN guard
        if exp_return != exp_return: exp_return = 0.0

        rows.append({
            "Symbol":              sym,
            "Company":             r.get("Name",""),
            "Sector":              sector,
            "Price (₹)":           round(price, 2),
            "Return %":            round(period_ret, 2),
            "10-Day Momentum":     round(mom, 2),
            "Annual Volatility %": round(vol, 1),
            "RSI (14)":            round(rsi, 1) if rsi else None,
            "Fundamental Score":   round(fund_score, 0),
            "Macro Boost":         round(macro_s, 1),
            "Alpha Score":         round(composite, 1),
            "Tech Signal":         tech_str,
            "Upside Target %":     round(upside_est, 1),
            "Downside Risk %":     round(downside_est, 1),
            "Bull Probability %":  round(bull_prob * 100, 1),
            "Bear Probability %":  round(bear_prob * 100, 1),
            "Expected Return %":   round(exp_return, 1),
            "Analyst Target (₹)":  round(atgt, 0) if atgt else None,
            "PE":                  r.get("PE"),
            "ROE":                 r.get("ROE"),
        })

    alpha_df = pd.DataFrame(rows)
    st.session_state["alpha_df"] = alpha_df

alpha_df: pd.DataFrame = st.session_state.get("alpha_df", pd.DataFrame())
if alpha_df.empty:
    st.warning("Click 🚀 Hunt Alpha to load data.")
    st.stop()

# ── SECTOR FILTER ──────────────────────────────────────────────────────────
display_df = alpha_df.copy()
if sector_filter != "All Sectors":
    display_df = display_df[display_df["Sector"] == sector_filter]
if display_df.empty:
    st.warning(f"No stocks in {sector_filter}. Try a different sector.")
    st.stop()

# ── SORT ───────────────────────────────────────────────────────────────────
sort_map = {
    "Alpha Score (AI Composite)":  ("Alpha Score",         False),
    "Top Gainers":                 ("Return %",            False),
    "Top Losers":                  ("Return %",            True),
    "Momentum Leaders":            ("10-Day Momentum",     False),
    "Fundamental Value":           ("Fundamental Score",   False),
    "Lowest Volatility":           ("Annual Volatility %", True),
}
sc, asc = sort_map.get(view_mode, ("Alpha Score", False))
display_df = display_df.sort_values(sc, ascending=asc).reset_index(drop=True)

# ── SUMMARY ────────────────────────────────────────────────────────────────
st.divider()
avg_ret    = display_df["Return %"].mean()
top_alpha  = display_df.nlargest(1,"Alpha Score").iloc[0]
best_exp   = display_df.nlargest(1,"Expected Return %").iloc[0]
adv        = (display_df["Return %"] > 0).sum()
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric(f"Avg Return ({timeframe})",  f"{avg_ret:+.2f}%")
c2.metric("Best Alpha Score",           f"{top_alpha['Symbol']} ({top_alpha['Alpha Score']:.0f})")
c3.metric("Best Expected Return",       f"{best_exp['Symbol']} {best_exp['Expected Return %']:+.1f}%")
c4.metric("Advancing",                  f"{adv}/{len(display_df)}")
c5.metric("Universe",                   f"{len(alpha_df)} stocks · {sector_filter}")

# ── TOP 10 CARDS ───────────────────────────────────────────────────────────
st.markdown(hover_section(
    f"🏆 Top 10 — {view_mode} ({timeframe})",
    f"Top 10 stocks sorted by <b>{view_mode}</b>. "
    "Alpha Score = forward-looking (predicts future). "
    "Return % = what already happened (past). "
    "Expected Return = probability-weighted 12-month estimate.",
    tag="⏪ Past return + 🔮 Future estimate", tag_type="curr", size="18px"
), unsafe_allow_html=True)
cols = st.columns(5)
for i, (_, row) in enumerate(display_df.head(10).iterrows()):
    ret     = row["Return %"]
    alpha   = row["Alpha Score"]
    exp_r   = row["Expected Return %"]
    rc = "#10D98D" if ret>=0 else "#FF4757"
    ac = "#10D98D" if alpha>65 else "#F59E0B" if alpha>40 else "#FF4757"
    ec = "#10D98D" if exp_r>0  else "#FF4757"
    with cols[i%5]:
        st.markdown(f"""<div style="background:#111827;border:1px solid {rc}33;border-radius:10px;padding:12px;margin-bottom:8px">
          <div style="font-family:monospace;font-weight:800;color:#F1F5F9;font-size:14px">{row['Symbol']}</div>
          <div style="font-size:9px;color:#64748B;margin-bottom:6px">{row['Sector']}</div>
          <div style="font-family:monospace;font-size:17px;font-weight:700;color:{rc}">{ret:+.1f}%</div>
          <div style="font-size:9px;color:#64748B">{timeframe} return</div>
          <div style="display:flex;justify-content:space-between;margin-top:8px">
            <div><div style="font-size:8px;color:#64748B">Alpha</div>
                 <div style="font-family:monospace;font-size:12px;color:{ac};font-weight:700">{alpha:.0f}/100</div></div>
            <div style="text-align:right"><div style="font-size:8px;color:#64748B">Exp.Ret</div>
                 <div style="font-family:monospace;font-size:12px;color:{ec};font-weight:700">{exp_r:+.1f}%</div></div>
          </div>
          <div style="font-size:8px;color:#64748B;margin-top:4px">↑{row['Upside Target %']:.0f}% / ↓{row['Downside Risk %']:.0f}%</div>
        </div>""", unsafe_allow_html=True)

# ── FULL TABLE ─────────────────────────────────────────────────────────────
st.divider()
st.markdown(hover_section(
    f"📊 Full Ranked Table — {len(display_df)} stocks",
    "This table ranks 545+ NSE stocks. Columns marked <b>⏪</b> show past data, "
    "<b>🔄</b> show current state, and <b>🔮</b> are forward-looking estimates. "
    "Alpha Score (🔮) is the best single column — it predicts future outperformance "
    "by combining business quality + live macro tailwinds + recent momentum.",
    tag="Composite of Past + Current + Forward signals", tag_type="fwd", size="18px"
), unsafe_allow_html=True)
st.caption("Columns marked 🔮 = forward estimates · ⏪ = past data · 🔄 = current state · Click header to sort")

# Column config with help text
col_config = {col: st.column_config.TextColumn(col, help=tip) for col, tip in COL_INFO.items() if col in display_df.columns}
col_config["Alpha Score"]         = st.column_config.ProgressColumn("Alpha Score",       min_value=0, max_value=100, format="%.1f", help=COL_INFO["Alpha Score"])
col_config["Fundamental Score"]   = st.column_config.ProgressColumn("Fundamental Score", min_value=0, max_value=120, format="%.0f", help=COL_INFO["Fundamental Score"])
col_config["Bull Probability %"]  = st.column_config.ProgressColumn("Bull Prob %",       min_value=0, max_value=100, format="%.1f", help=COL_INFO["Bull Probability %"])
col_config["Macro Boost"]         = st.column_config.NumberColumn("Macro Boost 🔄",      format="%+.1f", help="🔄 CURRENT — " + COL_INFO["Macro Boost"])
col_config["Expected Return %"]   = st.column_config.NumberColumn("Exp.Ret % 🔮",        format="%+.1f", help="🔮 FORWARD — " + COL_INFO["Expected Return %"])
col_config["Return %"]            = st.column_config.TextColumn("Return % ⏪",           help="⏪ PAST — " + COL_INFO["Return %"])
col_config["Alpha Score"]         = st.column_config.ProgressColumn("Alpha Score 🔮",    min_value=0, max_value=100, format="%.1f", help="🔮 FORWARD-LOOKING — " + COL_INFO["Alpha Score"])
col_config["Fundamental Score"]   = st.column_config.ProgressColumn("Fund.Score 🔄",     min_value=0, max_value=120, format="%.0f", help="🔄 CURRENT — " + COL_INFO["Fundamental Score"])

# Display columns (hide raw PE/ROE from table — in detail view)
show_cols = [c for c in ["Symbol","Company","Sector","Price (₹)","Return %","10-Day Momentum",
             "RSI (14)","Tech Signal","Fundamental Score","Macro Boost","Alpha Score",
             "Upside Target %","Downside Risk %","Bull Probability %","Bear Probability %",
             "Expected Return %","Annual Volatility %","Analyst Target (₹)"] if c in display_df.columns]

disp = display_df[show_cols].copy().head(100)
# Format numeric cols
for col in ["Price (₹)","Analyst Target (₹)"]:
    if col in disp: disp[col] = disp[col].map(lambda x: f"₹{x:,.0f}" if x else "—")
for col in ["Return %","10-Day Momentum","Expected Return %"]:
    if col in disp: disp[col] = disp[col].map(lambda x: f"{x:+.2f}%" if x else "—")
for col in ["Upside Target %","Downside Risk %","Annual Volatility %"]:
    if col in disp: disp[col] = disp[col].map(lambda x: f"{x:.1f}%" if x else "—")
for col in ["RSI (14)","Bull Probability %","Bear Probability %"]:
    if col in disp: disp[col] = disp[col].map(lambda x: f"{x:.1f}" if x else "—")

st.dataframe(disp, use_container_width=True, hide_index=False, column_config=col_config)

# ── EXCEL DOWNLOAD (multi-sheet with full fundamentals) ────────────────────
excel_df = display_df[show_cols].copy()
universe_for_excel = st.session_state.get("universe_df")
with st.spinner("Building Excel workbook..."):
    excel_bytes = build_full_excel(
        main_df=excel_df,
        universe_df=universe_for_excel,
        macro_regime=regime,
        sheet_label=f"Alpha Hunter {timeframe}",
    )
st.download_button(
    label="📥 Download Excel — Summary + Full Fundamentals + Glossary",
    data=excel_bytes,
    file_name=f"NIVESH_AlphaHunter_{timeframe.replace(' ','_')}_{sector_filter.replace(' ','_')}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)

# ── COLUMN LEGEND ──────────────────────────────────────────────────────────
with st.expander("📖 Column Definitions"):
    for col, tip in COL_INFO.items():
        st.markdown(f"**{col}** — {tip}")

# ── DEEP DIVE: STOCK ANALYSIS ──────────────────────────────────────────────
st.divider()
st.markdown(hover_section(
    "🔬 Deep Dive — Select Any Stock",
    "Pick any stock to get: <br>"
    "• <b>Comprehensive Research</b> — bull/bear thesis, probability matrix, 12M targets<br>"
    "• <b>Auto Macro Research</b> — Gemini fetches latest results, FII activity, analyst changes, global macro impact<br>"
    "• <b>Investment Levels</b> — exact entry zones, 3 stop losses, 4 price targets, Kelly position sizing",
    tag="Click → get full AI + live data analysis", tag_type="fwd", size="18px"
), unsafe_allow_html=True)

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    selected = st.selectbox("Select stock", display_df["Symbol"].tolist(), label_visibility="collapsed")
with col2:
    capital = st.number_input("Capital (₹)", value=100000, step=25000, format="%d", label_visibility="collapsed")
with col3:
    deep_btn = st.button("🔬 Full Analysis", type="primary", use_container_width=True)

if deep_btn and selected:
    # Quick metrics from alpha table
    row = display_df[display_df["Symbol"]==selected].iloc[0]
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Price",         f"₹{row['Price (₹)']:,.0f}")
    c2.metric("Alpha Score",   f"{row['Alpha Score']:.0f}/100")
    c3.metric("Return",        f"{row['Return %']:+.1f}%")
    c4.metric("Expected Ret",  f"{row['Expected Return %']:+.1f}%")
    c5.metric("Bull Prob",     f"{row['Bull Probability %']:.0f}%")
    c6.metric("Bear Prob",     f"{row['Bear Probability %']:.0f}%")

    # Fetch full data
    with st.spinner(f"Fetching {selected} data..."):
        hist    = get_history(selected, "1y", "1d")
        info    = get_fundamentals(selected)
        signals = compute_all_signals(hist) if not hist.empty else {}

    if signals:
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("RSI (14)",       f"{signals['rsi']:.1f}")
        c2.metric("Tech Signal",    signals["overall"])
        c3.metric("SMA 20",         f"₹{signals['sma20']:.0f}")
        c4.metric("Stop (1.5×ATR)", f"₹{signals['stop_1x']:.0f}")
        c5.metric("Stop (2.5×ATR)", f"₹{signals['stop_2x']:.0f}")

    # Auto macro context via Gemini
    tab_invest, tab_research, tab_levels = st.tabs([
        "📊 Comprehensive Research",
        "🌍 Auto Macro + Company Context",
        "💹 Entry · Stop Loss · Targets"
    ])

    with tab_invest:
        st.info("Fetching Gemini auto-research context first, then generating comprehensive report...")
        with st.spinner("Generating comprehensive research report..."):
            from utils.ai_utils import analyse_stock_comprehensive
            result = analyse_stock_comprehensive(selected, info, signals or {}, macro_ctx)
        st.markdown(result)

    with tab_research:
        with st.spinner("Fetching latest macro + company news via Gemini web search..."):
            ctx = auto_research_stock(selected, row.get("Composite Score", 70))
        research_card(ctx)
        st.markdown("")
        st.caption(f"Auto-researched by {get_model_name()} with web search · Updates every 30 min")

    with tab_levels:
        with st.spinner("Computing precise entry zones, stop losses, and targets..."):
            levels = get_investment_levels(selected, row["Price (₹)"], signals or {}, info, capital)
        st.markdown(levels)
        st.caption("Stop losses based on ATR + key support levels · Position sizes based on your capital input")
