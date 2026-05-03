"""Stock Screener — filter 545+ NSE stocks · Better columns · Excel download · AI analysis."""
import streamlit as st
from utils.style import inject_css, theme_toggle, hover_section, metric_tip, research_card
import pandas as pd
from utils.excel_export import build_full_excel
from utils.data import get_universe_scores, get_history, get_fundamentals
from utils.math_utils import compute_all_signals
from utils.ai_utils import analyse_stock, get_investment_levels, get_model_name, auto_research_stock

st.set_page_config(page_title="Screener — NIVESH", page_icon="🔍", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("🔍 Stock Screener")
st.caption("545+ NSE stocks · Filter by fundamentals + macro · Click stock for AI analysis + investment levels")
# Show live universe status
try:
    live_u = get_live_universe()
    is_live = len(live_u) > 545
    st.caption(f"{'✅ Live NSE universe' if is_live else '📋 Cached universe'}: **{len(live_u)} stocks** · Auto-updates daily · New index additions appear within 24 hours")
except Exception:
    pass

col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
with col1:
    category = st.selectbox("Filter by",
        ["all","value","growth","quality","dividend","smallcap"],
        format_func=lambda x: {
            "all":      "🌐 All 545+ Stocks",
            "value":    "💎 Value — PE < 20 (undervalued)",
            "growth":   "🚀 Growth — Revenue growth > 15%",
            "quality":  "⭐ Quality — ROE > 15%, margin > 10%",
            "dividend": "💰 Dividend — Yield > 1%",
            "smallcap": "🔥 Small Cap — Market cap < ₹20,000Cr",
        }[x], help="Filter criteria applied to 545-stock universe")
with col2:
    sort_by = st.selectbox("Sort by",
        ["Composite Score","P/E Ratio","Return on Equity","Net Profit Margin",
         "Revenue Growth","Day Change %","Analyst Upside"],
        help="Primary sort column")
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    go = st.button("🔍 Run Screener", type="primary", use_container_width=True)
with col4:
    capital = st.number_input("Capital ₹", value=100000, step=25000, format="%d",
                              label_visibility="collapsed")

if go or "screener_df" not in st.session_state:
    with st.spinner("Screening 545+ stocks with live macro... (~60-90 sec)"):
        df = get_universe_scores(category)
        st.session_state["screener_df"] = df

df: pd.DataFrame = st.session_state.get("screener_df", pd.DataFrame())
if df.empty:
    st.warning("No data. Retry.")
    st.stop()

# Sort mapping
sort_col_map = {
    "Composite Score":    "Score",
    "P/E Ratio":          "PE",
    "Return on Equity":   "ROE",
    "Net Profit Margin":  "Net Margin",
    "Revenue Growth":     "Rev Growth",
    "Day Change %":       "Change%",
    "Analyst Upside":     "Analyst Upside%",
}
sort_col = sort_col_map.get(sort_by, "Score")
sort_asc  = sort_by in ["P/E Ratio"]
df = df.sort_values(sort_col, ascending=sort_asc, na_position="last").reset_index(drop=True)

st.success(f"✓ {len(df)} stocks matched")

# Search filter
search = st.text_input("Filter results", placeholder="Type symbol or name...",
                        label_visibility="collapsed")
if search:
    df = df[df["Symbol"].str.contains(search.upper(),na=False) |
            df["Name"].str.contains(search,case=False,na=False)]

# Rename columns for display
RENAME = {
    "Symbol":          "Symbol",
    "Name":            "Company Name",
    "Sector":          "Sector",
    "Price":           "Price (₹)",
    "Change%":         "Day Change %",
    "Score":           "Composite Score",
    "Macro Score":     "Macro Boost",
    "PE":              "P/E Ratio",
    "ROE":             "Return on Equity %",
    "Net Margin":      "Net Profit Margin %",
    "Rev Growth":      "Revenue Growth %",
    "D/E":             "Debt/Equity",
    "Tech":            "Technical Signal",
    "Analyst Upside%": "Analyst Upside %",
    "Reasons":         "Score Drivers",
}
show_cols = [c for c in RENAME if c in df.columns]
disp = df[show_cols].head(200).copy().rename(columns=RENAME)

# Format
disp["Price (₹)"] = disp["Price (₹)"].map("₹{:,.0f}".format)
disp["Day Change %"] = disp["Day Change %"].map("{:+.2f}%".format)
if "Return on Equity %" in disp:
    disp["Return on Equity %"] = disp["Return on Equity %"].map(lambda x: f"{x*100:.1f}%" if x else "—")
if "Net Profit Margin %" in disp:
    disp["Net Profit Margin %"] = disp["Net Profit Margin %"].map(lambda x: f"{x*100:.1f}%" if x else "—")
if "Revenue Growth %" in disp:
    disp["Revenue Growth %"] = disp["Revenue Growth %"].map(lambda x: f"{x*100:.1f}%" if x else "—")
if "P/E Ratio" in disp:
    disp["P/E Ratio"] = disp["P/E Ratio"].map(lambda x: f"{x:.1f}" if x else "—")
if "Debt/Equity" in disp:
    disp["Debt/Equity"] = disp["Debt/Equity"].map(lambda x: f"{x:.0f}" if x else "—")
if "Analyst Upside %" in disp:
    disp["Analyst Upside %"] = disp["Analyst Upside %"].map(lambda x: f"{x:+.1f}%" if x else "—")

st.dataframe(disp, use_container_width=True, hide_index=False,
    column_config={
        "Composite Score": st.column_config.ProgressColumn(
            "Composite Score", min_value=0, max_value=120, format="%.0f",
            help="Score 0–120 = Valuation(25) + Quality(30) + Growth(25) + Safety(20) + Technical(10) + Live Macro(±20)"),
        "Macro Boost": st.column_config.NumberColumn(
            "Macro Boost", format="%+.0f",
            help="Live macro regime impact on this sector. Positive = tailwind, Negative = headwind"),
    })

# Excel Download — multi-sheet with full fundamentals
with st.spinner("Building Excel..."):
    excel_bytes = build_full_excel(
        main_df=disp,
        universe_df=df,
        macro_regime=None,
        sheet_label=f"Screener {category}",
    )
st.download_button("📥 Download Excel — Screener + Full Fundamentals + Glossary",
    data=excel_bytes,
    file_name=f"NIVESH_Screener_{category}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

st.divider()
st.markdown(hover_section("📋 Score Drivers Legend",
    "<b>Low PE ✓</b> = stock cheaper than sector average<br>"
    "<b>High ROE ✓</b> = generating strong returns on capital<br>"
    "<b>Rev/EPS growth ✓</b> = earnings growing<br>"
    "<b>Low debt ✓</b> = safe balance sheet, less risk<br>"
    "<b>Near 52W low ✓</b> = value opportunity, buying near historical cheap<br>"
    "<b>Macro +</b> = live global macro (crude/INR/NASDAQ/Gold/DXY) tailwind for sector",
    tag="🔄 Based on current + recent data", tag_type="curr"
), unsafe_allow_html=True)
st.caption("""**Score Drivers**: Low PE ✓ = cheap valuation · High ROE ✓ = quality business · Rev/EPS growth ✓ = growing earnings
Low debt ✓ = safe balance sheet · Near 52W low ✓ = value opportunity · Macro± = live sector impact from crude/INR/VIX/rates""")

# ── AI Analysis + Investment Levels ────────────────────────────────────────
st.divider()
st.subheader("🔬 Stock Deep Dive")
col1, col2 = st.columns([3,1])
with col1:
    selected = st.selectbox("Select stock", df["Symbol"].tolist(), label_visibility="collapsed")
with col2:
    analyse_btn = st.button("🔬 Analyse", type="primary", use_container_width=True)

if analyse_btn and selected:
    row = df[df["Symbol"]==selected].iloc[0]
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Price",           f"₹{row['Price']:,.0f}")
    c2.metric("Composite Score", f"{row['Score']:.0f}/120")
    c3.metric("Tech Signal",     row.get("Tech","—"))
    c4.metric("Macro Boost",     f"{row.get('Macro Score',0):+.0f}")

    if row.get("Reasons"):
        st.info(f"📋 Score drivers: {row['Reasons']}")

    with st.spinner("Fetching chart + fundamentals..."):
        hist    = get_history(selected, "1y","1d")
        info    = get_fundamentals(selected)
        signals = compute_all_signals(hist) if not hist.empty else {}

    tab_research, tab_levels, tab_ai = st.tabs([
        "🌍 Auto Macro Research", "💹 Investment Levels", "🤖 AI Report"
    ])

    with tab_research:
        with st.spinner(f"Gemini researching macro + {selected} context..."):
            ctx = ai_utils.analyse_stock(selected, info or {}, signals or {})
        st.markdown(ctx)

    with tab_levels:
        if signals:
            with st.spinner("Computing entry zones, stop losses, targets..."):
                levels = get_investment_levels(selected, row["Price"], signals, info, capital)
            st.markdown(levels)
        else:
            st.warning("Need chart data for level calculation.")

    with tab_ai:
        # Auto-research always runs first
        with st.spinner(f"Auto-researching {selected} — latest results, news, macro..."):
            research = auto_research_stock(selected, row["Price"])
        research_card(research)
        st.divider()
        # Deep AI report on demand
        if st.button("📋 Generate Full Detailed Report"):
            with st.spinner("Generating detailed research report..."):
                result = analyse_stock(info, signals or {})
            st.markdown(result)
