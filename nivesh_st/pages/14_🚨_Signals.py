"""
Live Signals — 52W Breakouts · F&O Ban · Insider Buying · Sector Rotation
The edge page: alerts for high-conviction opportunities and risk events.
"""
import streamlit as st
from utils.style import inject_css, theme_toggle, hover_section, metric_tip
import pandas as pd
from utils.data import (get_52w_breakout_stocks, get_fo_ban_list,
                         get_insider_buying_signal, get_sector_rotation_signal,
                         get_live_macro_regime, get_rs_ratings, get_nse_bulk_deals)
from utils.ai_utils import generate, get_model_name

st.set_page_config(page_title="Live Signals — NIVESH", page_icon="🚨", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("🚨 Live Signals")
st.caption("52W Breakouts · F&O Ban List · Insider Buying · Sector Rotation · RS Ratings · AI Alerts")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🚀 52W Breakouts",
    "🚫 F&O Ban List",
    "🔍 Insider Buying",
    "🔄 Sector Rotation",
    "⭐ RS Ratings",
])

# ── TAB 1: 52W BREAKOUTS ──────────────────────────────────────────────────
with tab1:
    st.markdown(hover_section("🚀 52-Week High Breakout Scanner",
        "Stocks within 5% of their 52-week high with rising volume. "
        "This is the #1 signal in IBD/CANSLIM investing — <b>the strongest stocks make new highs repeatedly</b>. "
        "A breakout above 52W high with volume >1.5× average = institutional buying. "
        "It is NOT a sign the stock is expensive — strong stocks keep going higher.",
        tag="⏪ Past 52W range + 🔄 Today volume", tag_type="curr", size="18px"
    ), unsafe_allow_html=True)
    st.markdown("""**Why it matters:** Stocks breaking to 52W highs are in strong uptrends.
    The strongest stocks make new highs repeatedly. This is the IBD/CANSLIM #1 rule.

    ✅ = Volume confirmed (volume > 1.3× average = conviction buying)""")

    col1, col2 = st.columns([1,3])
    with col1:
        if st.button("🔍 Scan for Breakouts", type="primary", use_container_width=True):
            st.cache_data.clear()
    with col2:
        st.caption("Requires Screener to have run first (universe_df in memory)")

    breakouts = get_52w_breakout_stocks()
    if not breakouts.empty:
        st.success(f"Found {len(breakouts)} stocks within 5% of 52-week high")
        st.dataframe(breakouts, use_container_width=True, hide_index=True,
            column_config={
                "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=120),
                "% from 52W High": st.column_config.NumberColumn("% from 52W High", format="%.2f%%",
                    help="0% = at 52W high, -5% = 5% below 52W high"),
            })

        # AI analysis of top breakouts
        if st.button("🤖 AI Analysis of Top Breakouts"):
            top3 = breakouts.head(3)
            rows = "\n".join([f"{r['Symbol']} — {r['Name']} ({r['Sector']}) | Price: ₹{r['Price (₹)']} | 52W High: ₹{r['52W High (₹)']} | {r['Volume Confirm']}"
                              for _, r in top3.iterrows()])
            prompt = (f"These Indian stocks are breaking out to 52-week highs:\n{rows}\n\n"
                      "For each: 1) Why is it breaking out now? 2) Is the breakout valid (volume, fundamentals)? "
                      "3) Entry strategy, stop loss below breakout level, target. "
                      "4) Key risk: is this a false breakout? What would invalidate it?")
            with st.spinner("AI analysing breakouts..."):
                result = generate(prompt, temperature=0.3, max_tokens=1200)
            st.markdown(result)
    else:
        if "universe_df" not in st.session_state:
            st.info("Run the **Screener** or **AI Best Picks** page first to load the universe, then come back here.")
        else:
            st.info("No stocks currently within 5% of 52-week high. Market may be in correction phase.")

# ── TAB 2: F&O BAN LIST ───────────────────────────────────────────────────
with tab2:
    st.markdown(hover_section("🚫 NSE F&O Ban List",
        "Stocks where total F&O positions exceed 95% of market-wide limit. "
        "<b>Ban = no NEW positions can be opened</b> (existing can only be reduced). "
        "When a stock <b>exits the ban</b> = fresh money can come in → often triggers price move. "
        "For delivery-based (non-F&O) investors: this list doesn't restrict you at all.",
        tag="🔄 Updated daily by NSE", tag_type="curr", size="18px"
    ), unsafe_allow_html=True)
    st.markdown("""**What it means:** Stocks in the ban list have exceeded 95% of market-wide position limit.
**Impact:** No NEW F&O positions can be opened. Existing positions can only be REDUCED.
**Trading signal:** Stocks exiting the ban = fresh F&O positions can resume → often triggers price move.""")

    if st.button("🔄 Fetch Today's F&O Ban List", type="primary"):
        with st.spinner("Fetching from NSE..."):
            ban_list = get_fo_ban_list()
            st.session_state["fo_ban"] = ban_list

    ban_list = st.session_state.get("fo_ban", [])
    if ban_list:
        st.error(f"🚫 {len(ban_list)} stocks currently in F&O ban")
        cols = st.columns(5)
        for i, sym in enumerate(ban_list):
            with cols[i % 5]:
                st.markdown(f"""<div style="background:#FF475718;border:1px solid #FF475744;border-radius:8px;padding:8px;text-align:center;margin:3px">
                    <div style="font-family:monospace;font-weight:700;color:#FF4757;font-size:13px">{sym}</div>
                    <div style="font-size:9px;color:#64748B">F&O Banned</div>
                </div>""", unsafe_allow_html=True)

        st.info("💡 **Strategy:** Avoid buying these stocks in F&O. For delivery-based investors: ban doesn't affect spot buying/selling.")
    else:
        st.info("Click the button above to fetch today's F&O ban list from NSE.")

    # Check if watchlist stocks are in ban
    watchlist = st.session_state.get("watchlist", [])
    if watchlist and ban_list:
        banned_watchlist = [s for s in watchlist if s in ban_list]
        if banned_watchlist:
            st.warning(f"⚠️ Your watchlist stocks in F&O ban: **{', '.join(banned_watchlist)}**")
        else:
            st.success("✅ None of your watchlist stocks are in F&O ban")

# ── TAB 3: INSIDER BUYING ─────────────────────────────────────────────────
with tab3:
    st.subheader("🔍 Insider & Promoter Buying Signal")
    st.markdown("""**Why it matters:** When promoters/insiders buy their OWN stock at current market prices,
it's one of the strongest bullish signals. They know the business best.

**NSE Bulk Deals** = transactions > ₹5 Cr reported to exchange daily.""")

    if st.button("🔄 Fetch Latest Bulk Deals", type="primary"):
        with st.spinner("Fetching bulk deals from NSE..."):
            deals = get_nse_bulk_deals()
            st.session_state["bulk_deals_signals"] = deals

    deals = st.session_state.get("bulk_deals_signals", pd.DataFrame())

    if not deals.empty:
        st.success(f"Fetched {len(deals)} bulk deal entries")
        st.dataframe(deals, use_container_width=True, hide_index=True)

        # Identify potential promoter buying
        insider_df = get_insider_buying_signal()
        if not insider_df.empty:
            st.subheader("🎯 Potential Promoter/Insider Activity")
            st.dataframe(insider_df, use_container_width=True, hide_index=True)

        # AI interpretation
        if st.button("🤖 AI Interpret Bulk Deals"):
            top_deals = deals.head(10).to_string()
            prompt = (f"Analyse these NSE bulk deal transactions:\n{top_deals}\n\n"
                      "Identify: 1) Any promoter/insider buying signals, 2) FII accumulation patterns, "
                      "3) Institutional selling red flags, 4) Top 3 actionable insights for retail investors.")
            with st.spinner("AI analysing bulk deals..."):
                result = generate(prompt, temperature=0.3, max_tokens=800)
            st.markdown(result)
    else:
        st.info("Click the button to fetch latest NSE bulk deals. If NSE rate-limits, retry in 30 seconds.")

# ── TAB 4: SECTOR ROTATION ────────────────────────────────────────────────
with tab4:
    st.subheader("🔄 Sector Rotation Signal")
    st.markdown("""**Economic Cycle Investing:** Different sectors outperform at different stages of the cycle.
Current macro regime auto-detected from live data → mapped to sector positioning.""")

    with st.spinner("Detecting macro regime..."):
        regime = get_live_macro_regime()

    rotation = get_sector_rotation_signal(regime)

    if rotation:
        # Cycle stage banner
        stage_color = "#10D98D" if "BULL" in rotation["stage"] else "#FF4757" if "RISK" in rotation["stage"] else "#F59E0B"
        st.markdown(f"""<div style="background:{stage_color}18;border:2px solid {stage_color}44;border-radius:10px;padding:16px;margin-bottom:16px">
            <div style="font-size:18px;font-weight:700;color:{stage_color}">📍 {rotation['stage']}</div>
        </div>""", unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### 🟢 Overweight (Favour)")
            for sector in rotation["overweight"][:8]:
                st.markdown(f"→ **{sector}**")

        with col2:
            st.markdown("### 🔴 Underweight (Avoid)")
            for sector in rotation["underweight"][:8]:
                st.markdown(f"→ **{sector}**")

        st.divider()
        st.markdown("### 📊 Rationale")
        for r in rotation["rationale"]:
            st.markdown(f"• {r}")

    # Macro snapshot
    if regime:
        st.divider()
        st.subheader("📡 Live Macro Snapshot")
        c1,c2,c3,c4,c5 = st.columns(5)
        c1.metric("Brent Crude", f"${regime.get('crude_price',0):.0f}")
        c2.metric("India VIX",   f"{regime.get('vix_level',0):.1f}")
        c3.metric("USD/INR",     f"₹{regime.get('inr_level',0):.2f}")
        c4.metric("Nifty",       f"{regime.get('nifty_chg',0):+.2f}%")
        c5.metric("US Market",   f"{regime.get('sp_chg',0):+.2f}%")

    # AI sector rotation advice
    if st.button("🤖 Get AI Sector Rotation Advice"):
        prompt = (f"Current Indian market macro:\n"
                  f"Crude: ${regime.get('crude_price',80):.0f}/bbl | VIX: {regime.get('vix_level',15):.1f} | "
                  f"USD/INR: ₹{regime.get('inr_level',84):.2f} | Nifty: {regime.get('nifty_chg',0):+.2f}%\n\n"
                  f"Current cycle stage: {rotation.get('stage','')}\n\n"
                  "Provide: 1) Detailed sector rotation strategy for next 3 months, "
                  "2) Specific stocks to own in each favoured sector, "
                  "3) Sectors/stocks to exit immediately, "
                  "4) Key catalysts that could change the rotation signal.")
        with st.spinner("AI analysing sector rotation..."):
            result = generate(prompt, temperature=0.3, max_tokens=1200, use_search=True)
        st.markdown(result)

# ── TAB 5: RS RATINGS ─────────────────────────────────────────────────────
with tab5:
    st.markdown(hover_section("⭐ RS Ratings — Relative Strength",
        "IBD-style 1–99 score. Measures how this stock has performed vs Nifty 50. "
        "<b>RS > 80</b> = stock is in top 20% of market — strong momentum. "
        "<b>RS > 90</b> = top 10% — this is where multi-baggers come from. "
        "<b>RS < 40</b> = underperforming Nifty — avoid or short. "
        "Formula: 40% recent quarter return + 20% each of 3 prior quarters.",
        tag="🔮 Forward momentum predictor", tag_type="fwd", size="18px"
    ), unsafe_allow_html=True)
    st.markdown("""**IBD-style Relative Strength Rating (1–99):**
- **80–99**: Top-tier momentum — stock significantly outperforming Nifty
- **60–79**: Above-average momentum
- **40–59**: In-line with market
- **1–39**: Underperforming Nifty — avoid or short

*Formula: 40% recent quarter + 20% each of 3 prior quarters*""")

    if st.button("📊 Compute RS Ratings for All 545 Stocks", type="primary"):
        with st.spinner("Computing RS Ratings vs Nifty 50 for 545 stocks... (~90 sec)"):
            rs_ratings = get_rs_ratings()
            st.session_state["rs_ratings"] = rs_ratings

    rs_ratings = st.session_state.get("rs_ratings", {})

    if rs_ratings:
        df_rs = pd.DataFrame([
            {"Symbol": sym, "RS Rating": rating}
            for sym, rating in rs_ratings.items()
        ]).sort_values("RS Rating", ascending=False)

        # Add sector from universe
        if "universe_df" in st.session_state:
            udf = st.session_state["universe_df"][["Symbol","Name","Sector","Price","Score"]].copy()
            df_rs = df_rs.merge(udf, on="Symbol", how="left")

        col1, col2, col3 = st.columns(3)
        col1.metric("RS > 80 (Top Tier)",    len(df_rs[df_rs["RS Rating"] >= 80]))
        col2.metric("RS 60-80 (Strong)",      len(df_rs[(df_rs["RS Rating"] >= 60) & (df_rs["RS Rating"] < 80)]))
        col3.metric("RS < 40 (Weak)",         len(df_rs[df_rs["RS Rating"] < 40]))

        # Top 20
        st.subheader("🏆 Top 20 RS Stocks")
        top20 = df_rs.head(20).copy()
        if "Price" in top20.columns:
            top20["Price"] = top20["Price"].map(lambda x: f"₹{x:,.0f}" if x else "—")
        st.dataframe(top20, use_container_width=True, hide_index=True,
            column_config={"RS Rating": st.column_config.ProgressColumn(
                "RS Rating", min_value=0, max_value=99, format="%.0f",
                help="1-99. >80 = top-tier momentum vs Nifty 50")})

        # Filter UI
        min_rs = st.slider("Minimum RS Rating", 1, 99, 70)
        filtered = df_rs[df_rs["RS Rating"] >= min_rs]
        st.info(f"{len(filtered)} stocks with RS Rating ≥ {min_rs}")
        st.dataframe(filtered, use_container_width=True, hide_index=True)

        # Excel download
        from io import BytesIO
        buf = BytesIO()
        df_rs.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("📥 Download RS Ratings Excel",
            buf.getvalue(), "rs_ratings.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("Click 'Compute RS Ratings' above. Requires fetching 12-month history for 545 stocks.")
