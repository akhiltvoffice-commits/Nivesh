"""F&O Module — live NSE options chain, Black-Scholes, strategies."""
import streamlit as st
from utils.style import inject_css, theme_toggle
import pandas as pd
import numpy as np
from utils.data import get_options_chain
from utils.math_utils import compute_greeks, implied_vol, black_scholes
from utils.charts import payoff_diagram, oi_bar_chart
from utils import ai_utils

st.set_page_config(page_title="F&O — NIVESH", page_icon="🎯", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("🎯 F&O Analyser")
st.caption("Live NSE options chain · Black-Scholes Greeks · Strategy payoff diagrams")
st.error("⚠️ **Educational only — not trading advice.** F&O trading involves substantial risk of loss.")

tab1, tab2, tab3 = st.tabs(["📋 Live NSE Chain", "⚡ BS Pricer & Greeks", "📐 Strategy Builder"])

# ── LIVE CHAIN ────────────────────────────────────────────────────────────
with tab1:
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        symbol = st.selectbox("Symbol", ["NIFTY","BANKNIFTY","FINNIFTY","RELIANCE","TCS","HDFCBANK","INFY"])
    with col2:
        opt_type = "indices" if symbol in ["NIFTY","BANKNIFTY","FINNIFTY","MIDCPNIFTY"] else "equities"
        st.info(f"Type: {'Index' if opt_type=='indices' else 'Equity'} options")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        load = st.button("Load Live Chain", type="primary", use_container_width=True)

    if load:
        with st.spinner(f"Fetching {symbol} options chain from NSE..."):
            chain_data = get_options_chain(symbol, opt_type)
            st.session_state["chain_data"] = chain_data
            st.session_state["chain_symbol"] = symbol

    chain_data = st.session_state.get("chain_data", {})

    if chain_data.get("error"):
        st.error(f"NSE Error: {chain_data['error']}")
        st.info("NSE rate-limits aggressively. Wait 30 seconds and try again.")
    elif chain_data.get("chain"):
        und = chain_data.get("underlying", 0)
        pcr = chain_data.get("pcr", 0)
        mp  = chain_data.get("maxPain", 0)

        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Underlying", f"₹{und:,.2f}")
        c2.metric("PCR", f"{pcr}", help="Put-Call Ratio. >1 = bullish, <0.7 = bearish")
        c3.metric("Max Pain", f"₹{mp:,.0f}", help="Strike where option buyers lose most")
        c4.metric("Total Call OI", f"{chain_data.get('totalCallOI',0)/1e5:.1f}L")

        # Expiry filter
        expiries = chain_data.get("expiries", [])
        if expiries:
            selected_expiry = st.selectbox("Expiry", expiries)
            chain = [r for r in chain_data["chain"] if r["Expiry"] == selected_expiry]
        else:
            chain = chain_data["chain"]

        # Near ATM filter
        if chain and und:
            near = [r for r in chain if abs(r["Strike"] - und) / und < 0.06]
        else:
            near = chain

        # OI chart
        if near:
            chain_df = pd.DataFrame(near)
            st.plotly_chart(oi_bar_chart(chain_df, und), use_container_width=True)

        # Chain table
        st.markdown("#### Options Chain (±6% of spot)")
        if near:
            chain_df = pd.DataFrame(near)
            chain_df["ITM Call"] = chain_df["Strike"] < und
            chain_df["ITM Put"]  = chain_df["Strike"] > und

            def highlight_row(row):
                if abs(row["Strike"] - und) < 50:
                    return ["background-color: #F59E0B22"] * len(row)
                return [""] * len(row)

            display_cols = ["Call OI","Call IV","Call LTP","Call Chg","Strike","Put LTP","Put IV","Put OI","Put Chg"]
            st.dataframe(chain_df[display_cols].style.apply(highlight_row, axis=1),
                        use_container_width=True, hide_index=True)

        # AI Analysis
        st.divider()
        if st.button("🤖 AI Chain Analysis"):
            with st.spinner("Analysing options chain with Gemini..."):
                result = ai_utils.generate(
                    f"Analyse {symbol} options chain:\nUnderlying: ₹{und}\nPCR: {pcr}\nMax Pain: ₹{mp}\n"
                    f"Total Call OI: {chain_data.get('totalCallOI',0)/1e5:.1f}L\nTotal Put OI: {chain_data.get('totalPutOI',0)/1e5:.1f}L\n\n"
                    "What does this options data signal? Directional view, IV environment, impact of max pain, "
                    "PCR interpretation for weekly expiry."
                )
            st.markdown(result)
    else:
        st.info("Click 'Load Live Chain' to fetch real-time options data from NSE India.")

# ── BS PRICER ─────────────────────────────────────────────────────────────
with tab2:
    st.subheader("Black-Scholes Options Pricer")
    col1, col2 = st.columns(2)
    with col1:
        spot   = st.number_input("Spot Price ₹", value=24500.0, step=50.0)
        strike = st.number_input("Strike Price ₹", value=24500.0, step=50.0)
        dte    = st.number_input("Days to Expiry", value=7, min_value=1, max_value=365)
    with col2:
        iv_inp = st.number_input("Implied Volatility %", value=14.0, min_value=1.0, max_value=200.0, step=0.5)
        rf     = st.number_input("Risk-Free Rate %", value=6.5, step=0.25)
        opt_t  = st.selectbox("Option Type", ["call","put"])
        lot_sz = st.number_input("Lot Size", value=25, min_value=1)

    T, r, sigma = dte/365, rf/100, iv_inp/100

    greeks = compute_greeks(spot, strike, T, r, sigma, opt_t)

    st.divider()
    c1,c2,c3,c4,c5,c6 = st.columns(6)
    c1.metric("Option Price", f"₹{greeks['price']:.2f}")
    c2.metric("Delta Δ",  f"{greeks['delta']:.4f}", help="Price change per ₹1 spot move")
    c3.metric("Gamma Γ",  f"{greeks['gamma']:.5f}", help="Rate of delta change")
    c4.metric("Theta Θ",  f"₹{greeks['theta']:.2f}/day", help="Daily time decay")
    c5.metric("Vega V",   f"₹{greeks['vega']:.2f}", help="Per 1% IV move")
    c6.metric("Rho ρ",    f"{greeks['rho']:.4f}")

    # Moneyness
    intrinsic = max(0, spot-strike) if opt_t=="call" else max(0, strike-spot)
    time_val  = max(0, greeks['price'] - intrinsic)
    m_tag     = "ITM" if intrinsic > 0 else "ATM" if abs(spot-strike)/spot < 0.005 else "OTM"
    st.info(f"**{m_tag} {opt_t.upper()}** | Intrinsic: ₹{intrinsic:.2f} | Time Value: ₹{time_val:.2f} | Per Lot: ₹{greeks['price']*lot_sz:,.0f}")

    # IV Calculator
    st.markdown("#### Implied Volatility Calculator")
    mkt_price = st.number_input("Market Price of Option ₹", value=0.0, min_value=0.0, step=0.5)
    if mkt_price > 0:
        iv_calc = implied_vol(mkt_price, spot, strike, T, r, opt_t)
        st.metric("Implied Volatility", f"{iv_calc*100:.2f}%",
                  f"{(iv_calc - sigma)*100:+.2f}% vs your input IV")

    # Payoff diagram
    st.markdown("#### Payoff at Expiry")
    rng = spot * 0.12
    spots = np.linspace(spot - rng, spot + rng, 80)
    payoffs = []
    for s in spots:
        intrinsic = max(0, s-strike) if opt_t=="call" else max(0, strike-s)
        payoff = (intrinsic - greeks['price']) * lot_sz
        payoffs.append({"spot": s, "payoff": payoff})

    breakevens = []
    for i in range(1, len(payoffs)):
        if (payoffs[i-1]["payoff"] < 0) != (payoffs[i]["payoff"] < 0):
            breakevens.append((payoffs[i-1]["spot"]+payoffs[i]["spot"])/2)

    st.plotly_chart(payoff_diagram(payoffs, spot, breakevens), use_container_width=True)
    max_p = max(p["payoff"] for p in payoffs)
    min_p = min(p["payoff"] for p in payoffs)
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Max Profit", f"₹{max_p:,.0f}" if max_p < 1e7 else "Unlimited")
    cc2.metric("Max Loss",   f"₹{abs(min_p):,.0f}" if min_p > -1e7 else "Unlimited")
    cc3.metric("Breakeven",  f"₹{breakevens[0]:,.0f}" if breakevens else "—")

# ── STRATEGY BUILDER ──────────────────────────────────────────────────────
with tab3:
    st.subheader("Multi-Leg Strategy Builder")
    strategies = {
        "Long Call":       [("buy","call",0,1)],
        "Long Put":        [("buy","put",0,1)],
        "Covered Call":    [("sell","call",100,1)],
        "Long Straddle":   [("buy","call",0,1),("buy","put",0,1)],
        "Long Strangle":   [("buy","call",100,1),("buy","put",-100,1)],
        "Bull Call Spread":[("buy","call",0,1),("sell","call",100,1)],
        "Bear Put Spread": [("buy","put",0,1),("sell","put",-100,1)],
        "Iron Condor":     [("buy","put",-200,1),("sell","put",-100,1),("sell","call",100,1),("buy","call",200,1)],
        "Iron Butterfly":  [("buy","put",-150,1),("sell","put",0,1),("sell","call",0,1),("buy","call",150,1)],
    }

    col1, col2 = st.columns([2,1])
    with col1:
        strat_name = st.selectbox("Strategy", list(strategies.keys()))
    with col2:
        atm_strike = st.number_input("ATM Strike ₹", value=24500, step=50)

    spot2  = st.number_input("Current Spot ₹", value=24500, step=50, key="spot2")
    iv2    = st.number_input("IV %", value=14.0, step=0.5, key="iv2")
    dte2   = st.number_input("DTE", value=7, min_value=1, key="dte2")
    lot2   = st.number_input("Lot Size", value=25, min_value=1, key="lot2")
    T2, sigma2 = dte2/365, iv2/100

    legs = strategies[strat_name]
    st.markdown("#### Strategy Legs")
    leg_data = []
    for action, typ, offset, qty in legs:
        k = atm_strike + offset
        prem = black_scholes(spot2, k, T2, 6.5/100, sigma2, typ)
        leg_data.append({"Action":action.upper(),"Type":typ.upper(),"Strike":f"₹{k}","Premium":f"₹{prem:.2f}","Qty":qty})
    st.dataframe(pd.DataFrame(leg_data), use_container_width=True, hide_index=True)

    # Combined payoff
    rng2 = spot2 * 0.12
    spots2 = np.linspace(spot2 - rng2, spot2 + rng2, 80)
    payoffs2 = []
    for s in spots2:
        total = 0
        for action, typ, offset, qty in legs:
            k = atm_strike + offset
            prem = black_scholes(spot2, k, T2, 6.5/100, sigma2, typ)
            intr = max(0, s-k) if typ=="call" else max(0, k-s)
            pl   = intr - prem if action=="buy" else prem - intr
            total += pl * qty * lot2
        payoffs2.append({"spot": s, "payoff": total})

    bes2 = []
    for i in range(1, len(payoffs2)):
        if (payoffs2[i-1]["payoff"] < 0) != (payoffs2[i]["payoff"] < 0):
            bes2.append((payoffs2[i-1]["spot"]+payoffs2[i]["spot"])/2)

    st.plotly_chart(payoff_diagram(payoffs2, spot2, bes2), use_container_width=True)
    mp2 = max(p["payoff"] for p in payoffs2)
    ml2 = min(p["payoff"] for p in payoffs2)
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Max Profit", f"₹{mp2:,.0f}" if mp2 < 1e7 else "Unlimited")
    cc2.metric("Max Loss",   f"₹{abs(ml2):,.0f}" if ml2 > -1e7 else "Unlimited")
    cc3.metric("Breakevens", ", ".join(f"₹{b:,.0f}" for b in bes2) or "—")

    # Position sizer
    st.divider()
    st.markdown("#### Position Sizer")
    capital = st.number_input("Trading Capital ₹", value=500000, step=10000)
    risk_pct= st.slider("Risk per trade %", 1.0, 5.0, 2.0, 0.5)
    risk_amt = capital * risk_pct / 100
    prem_lot = abs(ml2) / lot2 if lot2 and ml2 else 0
    max_lots = int(risk_amt / abs(ml2)) if ml2 else 0
    cc1, cc2, cc3 = st.columns(3)
    cc1.metric("Risk Amount", f"₹{risk_amt:,.0f}")
    cc2.metric("Max Loss/Lot", f"₹{abs(ml2):,.0f}")
    cc3.metric("Max Lots", max_lots)
