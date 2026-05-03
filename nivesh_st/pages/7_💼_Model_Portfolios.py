"""Model Portfolios — pre-built allocation frameworks + risk calculator + Monte Carlo."""
import streamlit as st
from utils.style import inject_css, theme_toggle
import numpy as np
import pandas as pd
from utils.math_utils import monte_carlo, risk_parity_weights
from utils.charts import pie_chart, monte_carlo_chart
from utils import ai_utils

st.set_page_config(page_title="Model Portfolios — NIVESH", page_icon="💼", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("💼 Model Portfolios")
st.info("📊 Using pre-built model portfolios — no external data required")
st.caption("Pre-built allocation frameworks · Risk-return calculator · Monte Carlo simulator · No personal data needed")

# ── Pre-built Model Portfolios ─────────────────────────────────────────────
MODELS = {
    "🛡 Conservative (Capital Preservation)": {
        "Nifty 50 Index ETF":     {"alloc":15,"type":"Large Cap Equity","vol":14},
        "Debt MF (Short Duration)":{"alloc":35,"type":"Debt","vol":5},
        "Gold ETF":               {"alloc":15,"type":"Commodity","vol":12},
        "FMCG / Pharma Stocks":   {"alloc":15,"type":"Defensive Equity","vol":12},
        "Liquid Fund":            {"alloc":20,"type":"Cash Equiv","vol":1},
    },
    "⚖️ Balanced (Growth + Safety)": {
        "Nifty 50 Index ETF":     {"alloc":25,"type":"Large Cap Equity","vol":14},
        "Flexi Cap Mutual Fund":  {"alloc":20,"type":"Diversified Equity","vol":16},
        "Debt MF (Med Duration)": {"alloc":25,"type":"Debt","vol":6},
        "Gold ETF":               {"alloc":10,"type":"Commodity","vol":12},
        "Midcap ETF":             {"alloc":10,"type":"Mid Cap Equity","vol":20},
        "REIT / InvIT":           {"alloc":10,"type":"Real Estate","vol":10},
    },
    "🚀 Aggressive (High Growth)": {
        "Nifty 50 ETF":           {"alloc":20,"type":"Large Cap","vol":14},
        "Midcap MF":              {"alloc":25,"type":"Mid Cap","vol":20},
        "Smallcap MF":            {"alloc":15,"type":"Small Cap","vol":28},
        "Thematic / Sector Fund": {"alloc":15,"type":"Sectoral","vol":22},
        "International ETF":      {"alloc":15,"type":"International","vol":18},
        "Gold ETF":               {"alloc":10,"type":"Commodity","vol":12},
    },
    "💡 Momentum (Tactical)": {
        "Banking ETF (BankNifty)":{"alloc":20,"type":"Sector","vol":20},
        "IT Stocks":              {"alloc":20,"type":"Sector","vol":18},
        "Defence / PSU":          {"alloc":15,"type":"Thematic","vol":24},
        "Momentum Factor ETF":    {"alloc":20,"type":"Factor","vol":18},
        "F&O Hedged Positions":   {"alloc":15,"type":"Derivatives","vol":25},
        "Debt (Tactical)":        {"alloc":10,"type":"Debt","vol":5},
    },
    "🌱 Young Investor SIP (25Y horizon)": {
        "Nifty 50 Index (SIP)":   {"alloc":30,"type":"Large Cap","vol":14},
        "Midcap Fund (SIP)":      {"alloc":25,"type":"Mid Cap","vol":20},
        "Smallcap Fund (SIP)":    {"alloc":20,"type":"Small Cap","vol":28},
        "International Fund":     {"alloc":15,"type":"International","vol":18},
        "ELSS (Tax Saving)":      {"alloc":10,"type":"ELSS","vol":18},
    },
}

selected_model = st.selectbox("Select Model Portfolio", list(MODELS.keys()))
portfolio = MODELS[selected_model]

c1, c2 = st.columns([2,2])
with c1:
    labels = list(portfolio.keys())
    values = [v["alloc"] for v in portfolio.values()]
    st.plotly_chart(pie_chart(labels, values, f"{selected_model} — Allocation"), use_container_width=True)

with c2:
    st.markdown("#### Portfolio Composition")
    rows = []
    for name, meta in portfolio.items():
        rows.append({"Asset": name, "Allocation": f"{meta['alloc']}%", 
                     "Type": meta["type"], "Est. Vol": f"{meta['vol']}%"})
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Portfolio stats
    weights = [v["alloc"]/100 for v in portfolio.values()]
    sigmas  = [v["vol"]/100 for v in portfolio.values()]
    port_vol = np.sqrt(sum((w*s)**2 for w,s in zip(weights,sigmas))) * 100
    rp_weights = risk_parity_weights(sigmas) 

    st.metric("Portfolio Volatility (est.)", f"{port_vol:.1f}% annualized")

# ── Return Expectation Calculator ─────────────────────────────────────────
st.divider()
st.subheader("📐 Return Expectation Calculator")

col1, col2, col3 = st.columns(3)
with col1:
    capital     = st.number_input("Starting Capital ₹", value=1000000, step=100000, format="%d")
    monthly_sip = st.number_input("Monthly SIP ₹ (0 = lump sum only)", value=0, step=5000, format="%d")
with col2:
    horizon     = st.slider("Investment Horizon (years)", 1, 30, 10)
    exp_return  = st.slider("Expected Annual Return %", 8, 22, 12)
with col3:
    est_vol     = st.number_input("Portfolio Volatility %", value=port_vol, format="%.1f")
    inflation   = st.slider("Inflation % (to compute real return)", 3, 8, 5)

# Compute lump sum projection
r = exp_return / 100
n_years = horizon
fv_lump = capital * (1 + r) ** n_years

# Compute SIP FV (if applicable)
if monthly_sip > 0:
    monthly_r = r / 12
    n_months  = horizon * 12
    fv_sip    = monthly_sip * ((1 + monthly_r)**n_months - 1) / monthly_r * (1 + monthly_r)
else:
    fv_sip = 0

total_fv = fv_lump + fv_sip
total_invested = capital + monthly_sip * horizon * 12
wealth_gain = total_fv - total_invested
real_return = ((1 + r) / (1 + inflation/100) - 1) * 100
inflation_adjusted_fv = total_fv / (1 + inflation/100)**horizon

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Invested",     f"₹{total_invested/1e5:.1f}L")
c2.metric("Projected Value",    f"₹{total_fv/1e5:.1f}L",   f"+₹{wealth_gain/1e5:.1f}L gain")
c3.metric("Real Return %",      f"{real_return:.1f}%")
c4.metric("Inflation-Adj Value",f"₹{inflation_adjusted_fv/1e5:.1f}L")
c5.metric("CAGR",               f"{exp_return}%")

# ── Monte Carlo ────────────────────────────────────────────────────────────
st.divider()
st.subheader("🎲 Monte Carlo Risk Simulation")
st.caption("Simulate 1000 possible portfolio journeys — shows range of outcomes")

if st.button("▶ Run Monte Carlo Simulation", type="primary"):
    with st.spinner("Simulating 1000 portfolio paths..."):
        mc = monte_carlo(exp_return/100, est_vol/100, horizon, 1000, capital)
        st.session_state["mc_result"] = mc

mc = st.session_state.get("mc_result")
if mc:
    cc1,cc2,cc3,cc4,cc5 = st.columns(5)
    cc1.metric("Worst Case (5%ile)",  f"₹{mc['p5']/1e5:.1f}L")
    cc2.metric("Conservative (25%)", f"₹{mc['p25']/1e5:.1f}L")
    cc3.metric("Median Outcome",      f"₹{mc['p50']/1e5:.1f}L")
    cc4.metric("Optimistic (75%)",    f"₹{mc['p75']/1e5:.1f}L")
    cc5.metric("Best Case (95%ile)",  f"₹{mc['p95']/1e5:.1f}L")

    cc6,cc7 = st.columns(2)
    cc6.metric("Probability of Loss", f"{mc['prob_loss']:.1f}%")
    cc7.metric("90th %ile Max Drawdown", f"{mc['p90_dd']:.1f}%")

    st.plotly_chart(monte_carlo_chart(mc, horizon, capital), use_container_width=True)

# ── Risk Parity ─────────────────────────────────────────────────────────────
st.divider()
st.subheader("⚖️ Risk-Parity Rebalancing Guide")
rp_wts = risk_parity_weights(sigmas)
rows = []
for (name, meta), cw, rw in zip(portfolio.items(), weights, rp_wts):
    rows.append({
        "Asset": name, "Current Alloc %": f"{meta['alloc']}%",
        "Risk-Parity Alloc %": f"{rw:.1f}%", "Difference": f"{rw - meta['alloc']:+.1f}%",
        "Est. Volatility": f"{meta['vol']}%",
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
st.caption("Risk-Parity: inverse-volatility weighting to equalise risk contribution across assets")

# ── AI Portfolio Advice ────────────────────────────────────────────────────
st.divider()
st.subheader("🤖 AI Portfolio Advice")
if st.button("🤖 Get AI Advice for This Model Portfolio", type="primary"):
    holdings_data = [
        {"name": name, "type": meta["type"], "value": meta["alloc"] * 10000,
         "weight": meta["alloc"]}
        for name, meta in portfolio.items()
    ]
    risk_profile = {
        "max_dd": 25, "horizon": horizon, "target": exp_return, "capital": capital
    }
    with st.spinner("Gemini analysing portfolio..."):
        result = ai_utils.analyse_portfolio(holdings_data, risk_profile)
    st.markdown(result)
    st.caption(f"Model: {ai_utils.get_model_name()}")
