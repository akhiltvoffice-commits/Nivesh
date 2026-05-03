"""
Stock Explorer — minimalist research terminal.
Auto-research runs on every stock search. Clean price hero. Single scroll.
"""
import streamlit as st
from utils.style import inject_css, theme_toggle, price_hero, research_card, stat_row, hover_section, metric_tip
from utils.data import get_history, get_fundamentals, get_nse_live_quote, get_screener_data, get_nse_delivery_data, get_live_macro_regime
from utils.math_utils import (compute_all_signals_enhanced, compute_pivot_points,
                               compute_sharpe, compute_sortino, compute_var,
                               kelly_position_size)
from utils.charts import candlestick_chart
from utils.ai_utils import (auto_research_stock, get_investment_levels,
                             analyse_stock, get_model_name)

st.set_page_config(page_title="Stock Explorer — NIVESH", page_icon="📈", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)

# ── Search bar ─────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([4, 1, 1])
with col1:
    symbol = st.text_input("", placeholder="Search NSE symbol — RELIANCE, TCS, ZOMATO...",
                            label_visibility="collapsed").upper().strip()
with col2:
    period_label = st.selectbox("", ["1W","1M","3M","6M","1Y","2Y","5Y"],
                                index=4, label_visibility="collapsed")
    period_map = {"1W":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y","2Y":"2y","5Y":"5y"}
with col3:
    capital = st.number_input("Capital ₹", value=100000, step=25000,
                              format="%d", label_visibility="collapsed",
                              help="Your capital for position sizing calculations")

# Quick picks
QUICK = ["RELIANCE","TCS","HDFCBANK","ICICIBANK","INFOSYS","BHARTIARTL",
         "SBIN","MARUTI","SUNPHARMA","TITAN","ZOMATO","BAJFINANCE"]
q_cols = st.columns(12)
for i, s in enumerate(QUICK):
    if q_cols[i].button(s, use_container_width=True, key=f"qp_{s}"):
        symbol = s

if not symbol:
    # Landing state — clean
    st.markdown("""<div style="padding:60px 0;text-align:center;color:#3F3F46">
      <div style="font-size:48px;margin-bottom:12px">📈</div>
      <div style="font-size:20px;font-weight:600;color:#71717A">Search any NSE stock above</div>
      <div style="font-size:13px;color:#3F3F46;margin-top:6px">
        Auto-research runs immediately · Live NSE price · Full technical + fundamental analysis
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

# ── Load data ──────────────────────────────────────────────────────────────
interval_map = {"5d":"15m","1mo":"1d","3mo":"1d","6mo":"1d","1y":"1d","2y":"1wk","5y":"1mo"}
yf_period = period_map[period_label]

with st.spinner(""):
    nse_live = get_nse_live_quote(symbol)
    df       = get_history(symbol, period=yf_period, interval=interval_map[yf_period])
    info     = get_fundamentals(symbol)

if df.empty:
    st.error(f"**{symbol}** not found. Check the NSE symbol — no .NS suffix needed.")
    st.stop()

# Price from NSE live or history fallback
if nse_live and nse_live.get("price"):
    cp    = nse_live["price"]
    chg   = nse_live.get("change", 0)
    pct   = nse_live.get("changePercent", 0)
    src   = "NSE Live"
else:
    close = df["Close"].dropna()
    cp    = float(close.iloc[-1])
    prev  = float(close.iloc[-2]) if len(close) > 1 else cp
    chg   = cp - prev
    pct   = chg / prev * 100
    src   = "yfinance"

name   = info.get("longName") or info.get("shortName") or symbol
sector = info.get("sector","")
mc_raw = info.get("marketCap", 0)
mc_str = f"₹{mc_raw/1e7:.0f}Cr" if mc_raw >= 1e7 else f"₹{mc_raw/1e5:.0f}L" if mc_raw else ""

# Compute signals
signals = compute_all_signals_enhanced(df)

# ── PRICE HERO ─────────────────────────────────────────────────────────────
price_hero(symbol, name, cp, chg, pct, sector, mc_str, src)

# ── AUTO-RESEARCH (always-on — no button needed) ───────────────────────────
st.markdown(hover_section(
    "🔍 AI Research",
    "Automatically researches this stock every 5 minutes during market hours. "
    "Covers: <b>latest quarterly results</b> (beat/miss), "
    "<b>upcoming events</b> (next results date, dividend, bonus), "
    "<b>FII activity</b>, <b>analyst upgrades/downgrades</b>, "
    "<b>macro impact</b> (how crude/INR/NASDAQ specifically affect this stock), "
    "<b>geopolitical risks</b>. Powered by Gemini with live web search.",
    tag="🔮 Updates every 5 min in market hours", tag_type="fwd", size="12px"
), unsafe_allow_html=True)
st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

# Show spinner while research loads (cached 30 min per stock)
research_placeholder = st.empty()
with research_placeholder:
    with st.spinner(f"Researching {symbol} — latest results, macro, news, geopolitical..."):
        research = auto_research_stock(symbol, cp)

research_card(research)

st.markdown('<div class="nv-divider"></div>', unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────
tab_chart, tab_fund, tab_tech, tab_levels = st.tabs([
    "Chart", "Fundamentals", "Technicals", "Entry & Sizing"
])

# ── CHART ─────────────────────────────────────────────────────────────────
with tab_chart:
    fig = candlestick_chart(df, symbol, signals, height=480)
    st.plotly_chart(fig, use_container_width=True)
    if nse_live:
        vwap = nse_live.get("vwap")
        hi   = nse_live.get("high")
        lo   = nse_live.get("low")
        uc   = nse_live.get("upperCircuit")
        lc   = nse_live.get("lowerCircuit")
        items = []
        if vwap: items.append(("VWAP", f"₹{vwap:,.2f}", "Volume Weighted Average Price"))
        if hi:   items.append(("Day High", f"₹{hi:,.2f}", ""))
        if lo:   items.append(("Day Low",  f"₹{lo:,.2f}", ""))
        if uc:   items.append(("Upper Ckt",f"₹{uc}", "Upper circuit limit — max price today"))
        if lc:   items.append(("Lower Ckt",f"₹{lc}", "Lower circuit limit — min price today"))
        if items: stat_row(items)

    # Delivery % — critical Indian market signal (fetched from NSE)
    deliv = get_nse_delivery_data(symbol)
    dp = deliv.get("delivery_pct")
    if dp:
        try:
            dp_f = float(str(dp).replace("%",""))
            sig  = "🟢 Strong" if dp_f > 60 else "🟡 Moderate" if dp_f > 40 else "🔴 Weak"
            st.markdown(f"""<div class="nv-card" style="margin-top:8px">
              <span class="nv-label">DELIVERY % — CONVICTION SIGNAL</span>&nbsp;
              <span class="nv-mono" style="font-size:16px;font-weight:700;color:#F59E0B">{dp_f:.1f}%</span>&nbsp;
              <span style="font-size:12px;color:#A1A1AA">{sig} &nbsp;·&nbsp; High delivery = long-term holders buying, not traders. >60% = strong conviction.</span>
            </div>""", unsafe_allow_html=True)
        except: pass

# ── FUNDAMENTALS ──────────────────────────────────────────────────────────
with tab_fund:
    # NSE live PE vs sector PE
    nse_pe  = nse_live.get("symbolPE") if nse_live else None
    nse_spe = nse_live.get("sectorPE") if nse_live else None
    if nse_pe or nse_spe:
        st.markdown('<div class="nv-label">LIVE VALUATION — FROM NSE</div>', unsafe_allow_html=True)
        live_items = []
        if nse_pe:  live_items.append(("Live P/E", str(nse_pe), "Live PE from NSE — intraday"))
        if nse_spe: live_items.append(("Sector P/E", str(nse_spe), "NSE sector median PE"))
        if nse_pe and nse_spe:
            try:
                pe_vs = round((float(nse_pe)/float(nse_spe) - 1)*100, 1)
                live_items.append(("PE vs Sector", f"{pe_vs:+.1f}%", "Negative = cheaper than sector peers"))
            except: pass
        stat_row(live_items)
        st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    # Valuation + Quality in 2 cols
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="nv-label">VALUATION</div>', unsafe_allow_html=True)
        rows = [
            ("P/E (TTM)",      info.get("trailingPE","—")),
            ("P/E (Forward)",  info.get("forwardPE","—")),
            ("P/B",            info.get("priceToBook","—")),
            ("P/S",            info.get("priceToSalesTrailing12Months","—")),
            ("EV/EBITDA",      info.get("enterpriseToEbitda","—")),
            ("EPS (₹)",        info.get("trailingEps","—")),
        ]
        for k, v in rows:
            col_a, col_b = st.columns([2,1])
            col_a.markdown(f'<div style="font-size:13px;color:#71717A">{k}</div>', unsafe_allow_html=True)
            col_b.markdown(f'<div class="nv-mono" style="font-size:13px;color:#FAFAFA">{v}</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="nv-label">QUALITY & GROWTH</div>', unsafe_allow_html=True)
        roe = info.get("returnOnEquity")
        mg  = info.get("profitMargins")
        rg  = info.get("revenueGrowth")
        eg  = info.get("earningsGrowth")
        rows2 = [
            ("ROE",             f"{roe*100:.1f}%" if roe else "—"),
            ("Net Margin",      f"{mg*100:.1f}%"  if mg  else "—"),
            ("Rev Growth (YoY)",f"{rg*100:.1f}%"  if rg  else "—"),
            ("EPS Growth",      f"{eg*100:.1f}%"  if eg  else "—"),
            ("D/E",             info.get("debtToEquity","—")),
            ("Current Ratio",   info.get("currentRatio","—")),
        ]
        for k, v in rows2:
            col_a, col_b = st.columns([2,1])
            col_a.markdown(f'<div style="font-size:13px;color:#71717A">{k}</div>', unsafe_allow_html=True)
            col_b.markdown(f'<div class="nv-mono" style="font-size:13px;color:#FAFAFA">{v}</div>', unsafe_allow_html=True)

    # Screener.in data (more accurate for Indian stocks)
    screener = get_screener_data(symbol)
    if screener:
        st.markdown('<div class="nv-label" style="margin-top:12px">SCREENER.IN — VERIFIED INDIAN DATA</div>', unsafe_allow_html=True)
        sc_items = []
        if screener.get("screener_pe"):    sc_items.append(("P/E (Screener)", f"{screener['screener_pe']:.1f}", "Verified PE from Screener.in"))
        if screener.get("screener_roce"):  sc_items.append(("ROCE", f"{screener['screener_roce']:.1f}%", "Return on Capital Employed — better than ROE for asset-heavy cos"))
        if screener.get("screener_roe"):   sc_items.append(("ROE (Screener)", f"{screener['screener_roe']:.1f}%", ""))
        if screener.get("screener_debt"):  sc_items.append(("D/E (Screener)", f"{screener['screener_debt']:.2f}", ""))
        if screener.get("sales_cagr_3y"):  sc_items.append(("Sales CAGR 3Y", f"{screener['sales_cagr_3y']:.1f}%", "Revenue CAGR over 3 years"))
        if screener.get("profit_cagr_3y"): sc_items.append(("Profit CAGR 3Y", f"{screener['profit_cagr_3y']:.1f}%", "Net profit CAGR over 3 years"))
        pledged = screener.get("promoter_pledged_pct")
        if pledged is not None:
            p_color = "🔴" if pledged > 20 else "🟡" if pledged > 5 else "🟢"
            sc_items.append(("Promoter Pledged", f"{p_color} {pledged:.1f}%", ">20% pledging = HIGH RISK. Promoter sold shares as collateral."))
        if sc_items: stat_row(sc_items[:6])
        if screener.get("screener_url"):
            st.caption(f"Source: [Screener.in]({screener['screener_url']}) · Updated every 6 hours")

    st.markdown('<div class="nv-divider"></div>', unsafe_allow_html=True)
    # Analyst
    tgt = info.get("targetMeanPrice","—")
    rec = str(info.get("recommendationKey","—")).upper()
    upside = round((info.get("targetMeanPrice",0)/cp - 1)*100, 1) if info.get("targetMeanPrice") and cp else None
    stat_row([
        ("Analyst Target", f"₹{tgt}" if tgt != "—" else "—", "Mean sell-side target"),
        ("Upside to Target", f"{upside:+.1f}%" if upside else "—", "vs current price"),
        ("Consensus", rec, "Aggregated analyst recommendation"),
        ("Beta", str(info.get("beta","—")), "Volatility vs Nifty"),
    ])

# ── TECHNICALS ────────────────────────────────────────────────────────────
with tab_tech:
    if not signals:
        st.warning("Need 30+ data points for technical analysis.")
    else:
        overall = signals.get("overall","Neutral")
        ocolor  = "#22C55E" if "Buy" in overall else "#EF4444" if "Sell" in overall else "#F59E0B"
        st.markdown(f"""<div class="nv-card" style="border-left:3px solid {ocolor}">
          <span style="font-size:20px;font-weight:700;color:{ocolor}">{overall}</span>
          <span style="color:#71717A;font-size:13px;margin-left:12px">Score: {signals.get("score",0):+d}</span>
        </div>""", unsafe_allow_html=True)

        # Momentum
        st.markdown(hover_section("📈 Momentum",
            "<b>RSI</b> — 0–100. Below 30 = oversold (good entry). Above 70 = overbought (be careful).<br>"
            "<b>Stochastic %K</b> — Similar to RSI, more sensitive for short-term timing.<br>"
            "<b>Williams %R</b> — −80 to −100 = buy zone. 0 to −20 = sell zone.<br>"
            "<b>OBV Trend</b> — Volume confirming price. Rising = strong signal.<br>"
            "<b>Rel. Volume</b> — Today vs 20-day avg. >1.5× = significant activity.",
            tag="⏪ Based on past price + volume data", tag_type="past", size="13px"
        ), unsafe_allow_html=True)
        stat_row([
            ("RSI (14)",        f"{signals.get('rsi',0):.1f}",      "<30 oversold  |  >70 overbought"),
            ("Stochastic %K",   f"{signals.get('stoch_k','—')}",    "<20 oversold  |  >80 overbought"),
            ("Williams %R",     f"{signals.get('williams_r','—')}", "-80 to -100 oversold"),
            ("OBV Trend",       signals.get("obv_trend","—"),       "Rising = volume confirming price"),
            ("Rel. Volume",     f"{signals.get('rel_volume','—')}×","vs 20D avg volume"),
        ])

        # Trend
        st.markdown(hover_section("📊 Trend",
            "<b>20/50/200 DMA</b> — Price above all 3 = strong uptrend. Below all 3 = downtrend.<br>"
            "<b>Ichimoku</b> — 'Above Cloud' = bullish. 'Below Cloud' = bearish. 'In Cloud' = uncertain.",
            tag="🔄 Current price vs moving averages", tag_type="curr", size="13px"
        ), unsafe_allow_html=True)
        stat_row([
            ("20 DMA",  f"₹{signals.get('sma20',0):.0f}",   ""),
            ("50 DMA",  f"₹{signals.get('sma50',0):.0f}",   ""),
            ("200 DMA", f"₹{signals.get('sma200',0):.0f}" if signals.get("sma200") else "—", ""),
            ("Ichimoku",signals.get("ichimoku","—"),         "Above/Below/In Cloud"),
        ])

        # Pivot Points
        pivots = signals.get("pivots",{})
        if pivots:
            st.markdown(hover_section("📍 Pivot Points",
                "Calculated from yesterday's High/Low/Close. Used by professionals as support/resistance.<br>"
                "<b>S1, S2, S3</b> = Support levels (price likely bounces here if it falls).<br>"
                "<b>Pivot</b> = Daily reference. Above = bullish. Below = bearish.<br>"
                "<b>R1, R2, R3</b> = Resistance levels (selling pressure expected here).<br>"
                "Tip: Buy near S1/S2 with stop below S2. Target R1/R2.",
                tag="🔄 Resets daily from previous session", tag_type="curr", size="13px"
            ), unsafe_allow_html=True)
            stat_row([
                ("S3 (support)", f"₹{pivots.get('S3',0):,.0f}", ""),
                ("S2",           f"₹{pivots.get('S2',0):,.0f}", ""),
                ("S1",           f"₹{pivots.get('S1',0):,.0f}", ""),
                ("Pivot",        f"₹{pivots.get('Pivot',0):,.0f}", "Bullish above"),
                ("R1",           f"₹{pivots.get('R1',0):,.0f}", ""),
                ("R2",           f"₹{pivots.get('R2',0):,.0f}", ""),
                ("R3 (resist)",  f"₹{pivots.get('R3',0):,.0f}", ""),
            ])

        # Risk
        var = signals.get("var",{})
        st.markdown(hover_section("⚖️ Risk Metrics",
            "<b>Sharpe Ratio</b> — Risk-adjusted return vs 6.5% FD rate. >1 = good, >2 = excellent.<br>"
            "<b>Sortino</b> — Like Sharpe but only penalises downside. More fair measure.<br>"
            "<b>VaR 95%</b> — On 95% of days, loss won't exceed this %. The 5% tail = extreme risk.<br>"
            "<b>Ann. Volatility</b> — Annual price swing. <15% = stable, >40% = very risky.",
            tag="⏪ Calculated from past 1-year returns", tag_type="past", size="13px"
        ), unsafe_allow_html=True)
        stat_row([
            ("Sharpe Ratio",   f"{signals.get('sharpe','—')}", ">1 good  |  >2 excellent"),
            ("Sortino Ratio",  f"{signals.get('sortino','—')}","Penalises only downside"),
            ("VaR 95%",        f"{var.get('VaR_95%','—')}%",  "Worst daily loss — 95% of days"),
            ("Ann. Volatility",f"{var.get('Ann_Vol','—')}%",  "Annualised volatility"),
        ])

        # Signal table
        st.markdown('<div class="nv-label" style="margin-top:12px">ALL SIGNALS</div>', unsafe_allow_html=True)
        sig_df = [{"Indicator":s[0],"Value":s[1],"Signal":s[2],"":""+s[3]} for s in signals.get("signals",[])]
        st.dataframe(sig_df, use_container_width=True, hide_index=True)

# ── ENTRY & SIZING ────────────────────────────────────────────────────────
with tab_levels:
    st.markdown(hover_section("💹 Investment Levels",
    "Calculated from ATR (Average True Range) — the stock's typical daily price swing.<br>"
    "<b>Entry Zones</b> — 3 options: Aggressive (buy now), Ideal (wait for dip), Conservative (only at deep value).<br>"
    "<b>Stop Losses</b> — Tight (1.5×ATR, for short-term traders), Normal (2.5×ATR, for investors), Wide (key support level).<br>"
    "<b>Targets</b> — T1 to T4 based on resistance levels + analyst targets + fair value.<br>"
    "Tip: Use Normal stop loss. Position size so your max loss = 2% of total capital.",
    tag="🔮 Forward-looking price levels", tag_type="fwd", size="12px"
), unsafe_allow_html=True)
    if signals:
        # Auto-compute levels (no button needed)
        with st.spinner("Computing entry zones, stop losses, targets..."):
            levels = get_investment_levels(symbol, cp, signals, info, capital)
        st.markdown(levels)

        st.markdown('<div class="nv-divider"></div>', unsafe_allow_html=True)
        st.markdown('<div class="nv-label">KELLY CRITERION — OPTIMAL POSITION SIZE</div>', unsafe_allow_html=True)

        k1, k2, k3 = st.columns(3)
        with k1: win_p = st.slider("Win Probability", 30, 80, 55, key="k_wp") / 100
        with k2: win_r = st.number_input("Expected Win %", value=20.0, step=1.0, key="k_wr") / 100
        with k3: loss_r= st.number_input("Stop Loss %", min_value=1.0,
                                          value=round(signals.get("atr",cp*0.02)/cp*150,1) if signals else 10.0,
                                          step=0.5, key="k_lr") / 100
        kelly = kelly_position_size(win_p, win_r, loss_r, capital)

        kc1,kc2,kc3,kc4 = st.columns(4)
        kc1.metric("Full Kelly",    f"{kelly['kelly_pct']}% = ₹{kelly['kelly_amount']:,.0f}")
        kc2.metric("Half Kelly ✅", f"{kelly['half_kelly_pct']}% = ₹{kelly['half_kelly_amount']:,.0f}",
                   help="Recommended — balances growth and safety")
        kc3.metric("Quarter Kelly", f"{kelly['quarter_kelly_pct']}% = ₹{kelly.get('quarter_kelly_amount',0):,.0f}")
        kc4.metric("Assessment",    kelly["interpretation"])
    else:
        st.info("Load more data (1Y chart) to compute investment levels.")
