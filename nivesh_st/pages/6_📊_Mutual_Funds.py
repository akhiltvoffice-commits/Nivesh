"""
Mutual Fund Explorer — NAV history, returns, exit load, expense ratio,
probability engine, AI analysis. With fallback when mfapi.in is unavailable.
"""
import streamlit as st
import pandas as pd
from utils.style import inject_css, theme_toggle
from utils.data import get_all_mf_schemes, get_mf_data, get_mf_scheme_details
from utils.math_utils import return_probabilities
from utils.charts import nav_chart
from utils import ai_utils

st.set_page_config(page_title="Mutual Funds — NIVESH", page_icon="📊", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("📊 Mutual Fund Explorer")
st.caption("6000+ schemes · NAV history · Exit load · Expense ratio · Probability engine · AI analysis")

# ── POPULAR SCHEMES ─────────────────────────────────────────────────────────
POPULAR = [
    (119598, "Parag Parikh Flexi Cap",     "Flexi Cap",  "Direct"),
    (120503, "Mirae Asset Large Cap",       "Large Cap",  "Direct"),
    (118834, "SBI Small Cap",               "Small Cap",  "Direct"),
    (118989, "Axis Bluechip",               "Large Cap",  "Direct"),
    (120505, "Mirae Emerging Bluechip",     "Mid Cap",    "Direct"),
    (119062, "HDFC Mid-Cap Opportunities",  "Mid Cap",    "Direct"),
    (122639, "Quant Small Cap",             "Small Cap",  "Direct"),
    (120701, "ICICI Pru Bluechip",          "Large Cap",  "Direct"),
    (125354, "Motilal Oswal Midcap",        "Mid Cap",    "Direct"),
    (120716, "Kotak Emerging Equity",       "Mid Cap",    "Direct"),
]

# ── SEARCH ──────────────────────────────────────────────────────────────────
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("", placeholder="Search fund — Parag Parikh, SBI Small Cap, HDFC Mid...",
                          label_visibility="collapsed")
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_go = st.button("Search", type="primary", use_container_width=True)

# Load scheme list with fallback
with st.spinner("Loading schemes..."):
    all_schemes = get_all_mf_schemes()

is_fallback = len(all_schemes) < 100
if is_fallback:
    st.warning("⚠️ mfapi.in is temporarily unavailable. Showing popular funds. Full search will resume when the API recovers.")

selected_code = None

if query:
    matches = {s["schemeName"]: s["schemeCode"]
               for s in all_schemes if query.lower() in s["schemeName"].lower()}
    if matches:
        sel_name = st.selectbox("Select Fund", list(matches.keys())[:20])
        selected_code = matches[sel_name]
    else:
        st.warning("No funds matched. Try shorter keywords like 'SBI' or 'HDFC'.")
else:
    st.markdown("**Popular Funds**")
    cols = st.columns(5)
    for i, (code, name, cat, plan) in enumerate(POPULAR):
        with cols[i % 5]:
            cat_color = "#22C55E" if "Small" in cat else "#F59E0B" if "Mid" in cat else "#3B82F6"
            if st.button(f"{name}", use_container_width=True, key=f"pop_{code}",
                         help=f"{cat} · {plan} Plan"):
                st.session_state["selected_mf"] = code
    selected_code = st.session_state.get("selected_mf")

if not selected_code:
    st.info("Search for a fund above or click a popular fund.")
    st.stop()

# ── LOAD FUND DATA ───────────────────────────────────────────────────────────
with st.spinner("Fetching NAV history and fund details..."):
    fund     = get_mf_data(int(selected_code))
    details  = get_mf_scheme_details(int(selected_code))

if not fund or "meta" not in fund:
    st.error("Could not fetch fund data from mfapi.in.")
    st.info("**Fallback:** Visit [AMFI NAV History](https://www.amfiindia.com/nav-history-download) or the fund's AMC website directly.")
    st.stop()

meta    = fund["meta"]
returns = fund.get("returns", {})
nav_df  = fund.get("navDf")
cur_nav = fund.get("currentNAV", 0)

# ── FUND HEADER ──────────────────────────────────────────────────────────────
st.markdown(f"""<div style="margin:8px 0 16px 0">
  <div style="font-size:18px;font-weight:700;color:#FAFAFA">{meta.get("scheme_name","")}</div>
  <div style="color:#71717A;font-size:13px;margin-top:4px">
    {meta.get("fund_house","")} &nbsp;·&nbsp; {meta.get("scheme_category","")} &nbsp;·&nbsp;
    <span style="color:#F59E0B;font-weight:600">{meta.get("scheme_type","")}</span>
  </div>
</div>""", unsafe_allow_html=True)

# Current NAV + key stats
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Current NAV", f"₹{cur_nav:.4f}")
c2.metric("1Y Return",   f"{returns.get('1Y','—')}%" if returns.get('1Y') else "—")
c3.metric("3Y CAGR",     f"{returns.get('3Y','—')}%" if returns.get('3Y') else "—")
c4.metric("5Y CAGR",     f"{returns.get('5Y','—')}%" if returns.get('5Y') else "—")
# Exit load
exit_rule = details.get("exit_load_rule","—")
exit_pct  = details.get("exit_load_pct","")
exit_days = details.get("exit_load_days", 0)
exit_str  = f"{'1%' if exit_pct else 'Nil'} within {exit_days}D" if exit_days else "Nil"
c5.metric("Exit Load", exit_str, help=exit_rule)

st.divider()

# ── SCHEME DETAILS BOX ───────────────────────────────────────────────────────
st.markdown("### 📋 Scheme Details")
d1, d2, d3 = st.columns(3)

with d1:
    st.markdown('<div class="nv-label">EXIT LOAD</div>', unsafe_allow_html=True)
    exit_color = "#22C55E" if exit_days == 0 else "#F59E0B"
    st.markdown(f"""<div class="nv-card" style="border-left:3px solid {exit_color}">
      <div style="font-size:14px;font-weight:700;color:{exit_color}">
        {'🟢 NIL' if exit_days==0 else f'⚠️ {exit_pct}% within {exit_days} days'}
      </div>
      <div style="font-size:12px;color:#A1A1AA;margin-top:6px">{exit_rule}</div>
      <div style="font-size:11px;color:#64748B;margin-top:4px">
        💡 {'No cost to exit anytime' if exit_days==0 else
            f'Hold {exit_days}+ days to avoid exit load. On ₹1L: saves ₹{exit_pct*1000 if exit_pct else 0:,.0f}' if exit_pct else ''}
      </div>
    </div>""", unsafe_allow_html=True)

with d2:
    st.markdown('<div class="nv-label">EXPENSE RATIO</div>', unsafe_allow_html=True)
    exp_actual = details.get("expense_ratio")
    exp_est    = details.get("expense_ratio_est","—")
    exp_display= f"{exp_actual:.2f}%" if exp_actual else f"Est. {exp_est}"
    is_direct  = "direct" in meta.get("scheme_name","").lower()
    exp_color  = "#22C55E" if is_direct else "#F59E0B"
    st.markdown(f"""<div class="nv-card" style="border-left:3px solid {exp_color}">
      <div style="font-size:14px;font-weight:700;color:{exp_color}">{exp_display}</div>
      <div style="font-size:12px;color:#A1A1AA;margin-top:6px">
        {'Direct plan — lower expense ratio. Same fund, same manager.' if is_direct else 'Regular plan — higher expense ratio (includes distributor commission).'}
      </div>
      <div style="font-size:11px;color:#64748B;margin-top:4px">
        💡 On ₹10L over 10Y: 1% extra expense = ~₹1.1L less wealth
      </div>
    </div>""", unsafe_allow_html=True)

with d3:
    st.markdown('<div class="nv-label">SCHEME INFO</div>', unsafe_allow_html=True)
    min_inv = details.get("min_investment_est","₹500 SIP")
    st.markdown(f"""<div class="nv-card">
      <div style="font-size:12px;color:#A1A1AA;line-height:1.8">
        <b>Category:</b> {meta.get("scheme_category","—")}<br>
        <b>Type:</b> {meta.get("scheme_type","—")}<br>
        <b>Min Investment:</b> {min_inv}<br>
        <b>Risk:</b> {'🔴 High' if any(x in meta.get("scheme_category","").lower() for x in ["small","sectoral","thematic"]) else '🟡 Moderate' if "mid" in meta.get("scheme_category","").lower() else '🟢 Moderate-Low'}<br>
        <b>Source:</b> {details.get("source","—")}
      </div>
    </div>""", unsafe_allow_html=True)

if details.get("disclaimer"):
    st.caption(f"ℹ️ {details['disclaimer']}")

st.divider()

# ── TRAILING RETURNS ─────────────────────────────────────────────────────────
st.markdown("### 📈 Trailing Returns")
ret_cols = st.columns(7)
for i, (period, label) in enumerate(zip(
    ["1W","1M","3M","6M","1Y","3Y","5Y"],
    ["1W","1M","3M","6M","1Y","3Y CAGR","5Y CAGR"]
)):
    ret = returns.get(period)
    if ret is not None:
        color = "#22C55E" if ret > 0 else "#EF4444"
        ret_cols[i].markdown(f"""<div style="text-align:center;padding:8px;background:#111113;border-radius:8px;border:1px solid #27272A">
          <div class="nv-label">{label}</div>
          <div class="nv-mono" style="font-size:16px;font-weight:700;color:{color};margin-top:4px">{ret:+.2f}%</div>
        </div>""", unsafe_allow_html=True)
    else:
        ret_cols[i].markdown(f"""<div style="text-align:center;padding:8px;background:#111113;border-radius:8px;border:1px solid #27272A">
          <div class="nv-label">{label}</div>
          <div class="nv-mono" style="font-size:16px;color:#3F3F46;margin-top:4px">—</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── NAV CHART ────────────────────────────────────────────────────────────────
if nav_df is not None and not nav_df.empty:
    st.markdown("### 📊 NAV History")
    period_filter = st.select_slider("Period",
        ["1M","3M","6M","1Y","3Y","5Y","All"], value="1Y")
    period_days = {"1M":30,"3M":90,"6M":180,"1Y":365,"3Y":1095,"5Y":1825,"All":99999}
    from datetime import datetime, timedelta
    cutoff = datetime.now() - timedelta(days=period_days[period_filter])
    chart_df = nav_df[nav_df["date"] >= cutoff]
    st.plotly_chart(nav_chart(chart_df, meta.get("scheme_name","")), use_container_width=True)

st.divider()

# ── PROBABILITY ENGINE ────────────────────────────────────────────────────────
st.markdown("### 🎲 Return Probability Engine")
st.caption("Log-normal distribution model based on trailing returns")

if returns.get("1Y") and returns.get("3Y"):
    mu1  = returns["1Y"] / 100
    mu3  = returns["3Y"] / 100
    mu   = mu1 * 0.35 + mu3 * 0.65
    sigma= max(0.10, abs(mu1 - mu3) * 1.5 + 0.10)

    pc1, pc2 = st.columns(2)
    with pc1:
        horizon = st.slider("Investment Horizon (years)", 1, 10, 3, key="mf_horizon")
        target  = st.slider("Target CAGR %", 8, 20, 12, key="mf_target")
    with pc2:
        probs = return_probabilities(mu, sigma, horizon, target/100)
        st.metric("Prob of Positive Return", f"{probs['prob_pos']:.1f}%")
        st.metric("Prob of Loss",            f"{probs['prob_loss']:.1f}%")
        st.metric(f"Prob of Beating {target}% CAGR", f"{probs['prob_beat']:.1f}%")

    c3,c4,c5 = st.columns(3)
    c3.metric("Worst Case (5%ile)",  f"{probs['worst']:+.1f}%")
    c4.metric("Expected Return",     f"{probs['expected']:+.1f}%")
    c5.metric("Best Case (95%ile)",  f"{probs['best']:+.1f}%")

    # SIP vs Lump Sum quick calc
    st.markdown("#### Quick SIP Calculator")
    s1, s2, s3 = st.columns(3)
    with s1: monthly = st.number_input("Monthly SIP ₹", value=10000, step=1000, format="%d", key="mf_sip")
    with s2: sip_yrs = st.slider("Duration (years)", 1, 20, 5, key="mf_sip_yrs")
    with s3:
        r_m = mu / 12
        n_m = sip_yrs * 12
        sip_fv = monthly * ((1+r_m)**n_m - 1) / r_m * (1+r_m) if r_m > 0 else monthly * n_m
        total_inv = monthly * n_m
        st.metric("SIP Future Value", f"₹{sip_fv/1e5:.1f}L", f"Invested ₹{total_inv/1e5:.1f}L")

    # Exit load warning
    if exit_days > 0 and exit_pct and horizon * 12 < exit_days / 30:
        st.warning(f"⚠️ Your horizon ({horizon}Y = {horizon*12}M) is less than the exit load period ({exit_days} days = {exit_days//30}M). You will pay {exit_pct}% exit load on redemption.")

else:
    st.info("Need 1Y and 3Y return data to compute probabilities.")

st.divider()

# ── AI ANALYSIS ──────────────────────────────────────────────────────────────
st.markdown("### 🤖 AI Fund Analysis")
st.caption(f"Powered by {ai_utils.get_model_name()} · Includes exit load, expense ratio, risk assessment")

question = st.text_input("", placeholder="Specific question — SIP or lump sum? Category comparison? Tax efficiency?",
                          label_visibility="collapsed")

if st.button("🤖 Analyse This Fund", type="primary"):
    scheme_name = meta.get("scheme_name","")
    fund_house  = meta.get("fund_house","")
    scheme_cat  = meta.get("scheme_category","")
    r1m  = returns.get("1M","—")
    r3m  = returns.get("3M","—")
    r1y  = returns.get("1Y","—")
    r3y  = returns.get("3Y","—")
    r5y  = returns.get("5Y","—")

    extra = f"Question: {question}" if question else (
        "Analyse: return consistency, risk-adjusted returns, impact of exit load on short-term redeeming, "
        "expense ratio impact over 10 years, ideal investor and horizon.")

    prompt = (
        f"Mutual Fund Research Note:\n"
        f"Fund: {scheme_name}\n"
        f"House: {fund_house} | Category: {scheme_cat}\n"
        f"NAV: ₹{cur_nav:.4f}\n"
        f"Returns: 1M={r1m}% | 3M={r3m}% | 1Y={r1y}% | 3Y CAGR={r3y}% | 5Y CAGR={r5y}%\n"
        f"Exit Load: {exit_rule}\n"
        f"Expense Ratio: {details.get('expense_ratio_est','—')}\n"
        f"Min Investment: {details.get('min_investment_est','—')}\n\n"
        f"{extra}\n\n"
        "Provide:\n"
        "1. **Return Consistency** — consistent alpha or lumpy?\n"
        "2. **Exit Load Impact** — when does it actually hurt? At what holding period is break-even?\n"
        "3. **Expense Ratio Impact** — ₹ cost on ₹10L over 10 years vs a cheaper alternative\n"
        "4. **Risk Assessment** — volatility, max drawdown potential, category risk\n"
        "5. **Ideal Investor** — who should invest, who should avoid\n"
        "6. **SIP Recommendation** — SIP amount range for typical investor\n"
        "7. **Red Flags** — any concerns"
    )

    with st.spinner("Generating fund analysis..."):
        result = ai_utils.generate(prompt, temperature=0.4, max_tokens=65536)
    st.markdown(result)
