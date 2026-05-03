"""Events & Corporate Actions — Results calendar, dividends, bulk deals, FII activity."""
import streamlit as st
from utils.style import inject_css, theme_toggle
import pandas as pd
from utils.data import get_corporate_actions, get_nse_bulk_deals, get_fundamentals, NIFTY50, NIFTY100
from utils import ai_utils

st.set_page_config(page_title="Events & Actions — NIVESH", page_icon="📅", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("📅 Events & Corporate Actions")
st.caption("Results calendar · Dividends & Splits · NSE Bulk/Block Deals · FII Activity · AI Market Events Brief")

tab1, tab2, tab3, tab4 = st.tabs([
    "📆 Results Calendar",
    "💰 Dividends & Splits",
    "📊 Bulk/Block Deals",
    "🤖 AI Events Brief"
])

# ── TAB 1: Results Calendar ────────────────────────────────────────────────
with tab1:
    st.subheader("📆 Upcoming Results Calendar")
    st.caption("Auto-fetched from yfinance | Nifty 50 stocks")

    results = []
    watchlist = st.session_state.get("watchlist", [])
    stocks_to_check = list(dict.fromkeys(watchlist + NIFTY50[:20]))

    if st.button("🔄 Fetch Calendar for Nifty 50 + Watchlist", type="primary"):
        progress = st.progress(0)
        for i, sym in enumerate(stocks_to_check[:30]):
            try:
                actions = get_corporate_actions(sym)
                cal = actions.get("calendar", {})
                if cal:
                    earnings_date = None
                    if isinstance(cal, dict):
                        ed = cal.get("Earnings Date", cal.get("earnings_date"))
                        if ed:
                            earnings_date = str(ed) if not isinstance(ed, list) else str(ed[0])
                    if earnings_date and "nan" not in str(earnings_date).lower():
                        results.append({"Symbol": sym, "Event": "Earnings Results", "Date": earnings_date})
            except Exception:
                pass
            progress.progress((i+1)/30)
        progress.empty()

    if results:
        df = pd.DataFrame(results).sort_values("Date")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Click the button above to fetch upcoming earnings dates for Nifty 50 + your watchlist stocks.")

    st.divider()

    # Manual lookup
    st.subheader("🔍 Corporate Calendar for Specific Stock")
    col1, col2 = st.columns([3,1])
    with col1:
        sym_cal = st.text_input("NSE Symbol", placeholder="e.g. RELIANCE", key="cal_sym").upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Fetch", type="primary") and sym_cal:
            with st.spinner(f"Fetching calendar for {sym_cal}..."):
                actions = get_corporate_actions(sym_cal)
                st.session_state["cal_actions"] = actions
                st.session_state["cal_sym_last"] = sym_cal

    actions = st.session_state.get("cal_actions", {})
    if actions:
        sym_last = st.session_state.get("cal_sym_last","")
        st.markdown(f"#### Corporate Events — {sym_last}")
        if "calendar" in actions and actions["calendar"]:
            cal_data = actions["calendar"]
            if isinstance(cal_data, dict):
                for key, val in cal_data.items():
                    if key and val and str(val).lower() not in ["nan","none",""]:
                        st.metric(str(key).replace("_"," ").title(), str(val)[:50])

# ── TAB 2: Dividends & Splits ──────────────────────────────────────────────
with tab2:
    st.subheader("💰 Dividends & Bonus/Splits")
    col1, col2 = st.columns([3,1])
    with col1:
        sym_div = st.text_input("NSE Symbol", placeholder="e.g. ITC, HDFCBANK", key="div_sym").upper()
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        fetch_div = st.button("Fetch Dividends", type="primary") and sym_div

    if fetch_div:
        with st.spinner(f"Fetching {sym_div} corporate actions..."):
            actions = get_corporate_actions(sym_div)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 💵 Recent Dividends")
            divs = actions.get("dividends", [])
            if divs:
                div_df = pd.DataFrame(divs)
                div_df.columns = ["Date", "Dividend (₹/share)"]
                st.dataframe(div_df, use_container_width=True, hide_index=True)
                annual = actions.get("annual_div", 0)
                info = get_fundamentals(sym_div)
                price = info.get("regularMarketPrice",0)
                yield_pct = (annual / price * 100) if price else 0
                st.metric("Annual Dividend", f"₹{annual}", f"{yield_pct:.2f}% yield")
            else:
                st.info("No dividend history found.")

        with c2:
            st.markdown("#### ✂️ Stock Splits / Bonus")
            split = actions.get("last_split")
            if split:
                st.metric("Last Split Date", split["date"])
                st.metric("Split Ratio", f"1 : {split['ratio']:.0f}")
            else:
                st.info("No split history found.")

    # Top dividend stocks from universe
    st.divider()
    st.subheader("💰 Top Dividend Yield Stocks — Nifty Universe")
    if "universe_df" in st.session_state:
        df = st.session_state["universe_df"]
        div_stocks = df[df["Div Yield"].notna()].nlargest(20, "Div Yield")[
            ["Symbol","Name","Sector","Price","Div Yield","Payout Ratio","PE"]
        ].copy()
        div_stocks["Price"]       = div_stocks["Price"].map("₹{:,.0f}".format)
        div_stocks["Div Yield"]   = div_stocks["Div Yield"].map(lambda x: f"{x*100:.2f}%" if x else "—")
        div_stocks["Payout Ratio"]= div_stocks["Payout Ratio"].map(lambda x: f"{x*100:.1f}%" if x else "—")
        div_stocks["PE"]          = div_stocks["PE"].map(lambda x: f"{x:.1f}" if x else "—")
        st.dataframe(div_stocks, use_container_width=True, hide_index=True)
    else:
        st.info("Run the Screener first to populate universe data.")

# ── TAB 3: Bulk/Block Deals ────────────────────────────────────────────────
with tab3:
    st.subheader("📊 NSE Bulk & Block Deals")
    st.caption("Large institutional transactions > ₹5Cr — signals smart money activity")

    if st.button("🔄 Fetch Recent Bulk/Block Deals", type="primary"):
        with st.spinner("Fetching from NSE..."):
            deals_df = get_nse_bulk_deals()
            st.session_state["bulk_deals"] = deals_df

    deals_df = st.session_state.get("bulk_deals", pd.DataFrame())
    if not deals_df.empty:
        st.dataframe(deals_df, use_container_width=True, hide_index=True)
        from io import BytesIO
        buf = BytesIO()
        deals_df.to_excel(buf, index=False, engine="openpyxl")
        st.download_button("📥 Download Bulk Deals Excel", buf.getvalue(),
                           "bulk_deals.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    else:
        st.info("""NSE bulk deals show when institutions (FIIs, mutual funds, HNIs) buy/sell large blocks.
Click the button above to fetch. If NSE rate-limits, try again in 30 seconds.

**What to look for:**
- **Repeated buying** by a single FII → strong conviction
- **Mutual fund buying** across multiple schemes → sector rotation signal
- **Promoter buying** at current price → management confidence
- **Large sell blocks** by insiders → potential red flag""")

# ── TAB 4: AI Events Brief ─────────────────────────────────────────────────
with tab4:
    st.subheader("🤖 AI Events & Calendar Brief")
    st.caption("Gemini researches this week's key events affecting Indian markets")

    if st.button("🤖 Get AI Events Brief", type="primary"):
        from datetime import datetime
        today = datetime.now().strftime("%A, %d %B %Y")
        prompt = f"""Today is {today}. Research and list this week's key events for Indian equity investors:

1. **Corporate Results**: Which major Nifty companies are reporting results this week? Expected numbers?
2. **RBI/Macro Events**: Any RBI decisions, policy announcements, economic data releases?
3. **Global Events**: US Fed, ECB decisions, major economic data (NFP, CPI, PMI)?
4. **IPOs & Listings**: Any major IPOs opening/listing this week?
5. **FII Activity**: Recent FII flow trend — buying or selling Indian equities?
6. **Sector Events**: Any sector-specific events (budget announcements, regulatory changes)?
7. **Key Technical Levels**: Nifty 50 — key support/resistance to watch this week?

Be specific with company names, dates, and ₹ figures where possible."""

        with st.spinner("Gemini researching this week's events..."):
            result = ai_utils.generate(prompt, temperature=0.2, max_tokens=65536, use_search=True)
        st.markdown(result)
        st.caption(f"Researched by {ai_utils.get_model_name()} with web search")
