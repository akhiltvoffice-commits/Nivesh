"""
AI Best Picks — Timeframe-aware scoring from Day to 3 Years.
545 NSE stocks · Gemini AI top 5 · Full probability engine.
"""
import streamlit as st
import pandas as pd
import numpy as np
import json, re
from utils.style import inject_css, theme_toggle
from utils.data import (get_universe_scores, get_live_macro_regime, compute_macro_score,
                         SECTOR_MACRO, get_sector_pe_averages, get_sector_rotation_signal,
                         get_alpha_universe, FULL_UNIVERSE)
from utils.ai_utils import analyse_best_picks, get_model_name
from utils.excel_export import build_full_excel

st.set_page_config(page_title="AI Best Picks — NIVESH", page_icon="🤖", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)

st.title("🤖 AI Best Picks")
st.caption("545 NSE stocks · Gemini scores by timeframe · Probability engine · Full sector rotation")

# ── TIMEFRAME SELECTOR ────────────────────────────────────────────────────
st.divider()
TIMEFRAMES = {
    "Day":     {"label":"Today",        "yf":"2d",   "interval":"15m", "horizon":"1 day",   "hot":"Intraday momentum, volume surge, gap-ups"},
    "Week":    {"label":"This Week",    "yf":"10d",  "interval":"1d",  "horizon":"1 week",  "hot":"Short-term breakouts, news catalysts"},
    "Month":   {"label":"This Month",   "yf":"1mo",  "interval":"1d",  "horizon":"1 month", "hot":"Monthly momentum, upcoming results"},
    "3 Months":{"label":"3 Months",     "yf":"3mo",  "interval":"1d",  "horizon":"3 months","hot":"Earnings cycle, sector rotation"},
    "6 Months":{"label":"6 Months",     "yf":"6mo",  "interval":"1d",  "horizon":"6 months","hot":"Mid-term trend, H1/H2 rotation"},
    "1 Year":  {"label":"1 Year",       "yf":"1y",   "interval":"1d",  "horizon":"12 months","hot":"Annual CAGR, cycle stocks"},
    "2 Years": {"label":"2 Years",      "yf":"2y",   "interval":"1wk", "horizon":"2 years", "hot":"Multi-year compounders, capex themes"},
    "3 Years": {"label":"3 Years",      "yf":"3y",   "interval":"1wk", "horizon":"3 years", "hot":"Long-term quality compounders"},
}

tf_cols = st.columns(8)
for i, (tf_key, tf_val) in enumerate(TIMEFRAMES.items()):
    if tf_cols[i].button(tf_key, use_container_width=True,
                          type="primary" if st.session_state.get("sel_tf")==tf_key else "secondary"):
        st.session_state.sel_tf = tf_key

sel_tf = st.session_state.get("sel_tf", "1 Year")
tf = TIMEFRAMES[sel_tf]

st.markdown(f"""<div style="background:#F59E0B18;border:1px solid #F59E0B44;border-radius:8px;padding:10px 16px;margin:8px 0">
  <span style="color:#F59E0B;font-weight:700">{sel_tf}</span>
  <span style="color:#A1A1AA;font-size:13px;margin-left:12px">Horizon: {tf['horizon']}
  &nbsp;·&nbsp; Focus: {tf['hot']}</span>
</div>""", unsafe_allow_html=True)

# ── CATEGORY FILTER ────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2,2,1])
with col1:
    category = st.selectbox("Filter by",
        ["all","value","growth","quality","dividend","smallcap"],
        format_func={"all":"All 545+ Stocks","value":"💎 Value","growth":"🚀 Growth",
                     "quality":"⭐ Quality","dividend":"💰 Dividend","smallcap":"🔥 Small Cap"}.get)
with col2:
    sort_by = st.selectbox("Sort universe by",
        ["Composite Score","Return for Period","Momentum","Fundamental Quality"])
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    run = st.button("🚀 Get Picks", type="primary", use_container_width=True)

# ── AUTO MACRO ─────────────────────────────────────────────────────────────
with st.expander("🌍 Live Global Macro — auto-detected, drives all scores", expanded=False):
    with st.spinner("Fetching global markets..."):
        regime = get_live_macro_regime()

    if regime:
        g1,g2,g3,g4,g5,g6,g7,g8 = st.columns(8)
        g1.metric("Nifty",   f"{regime.get('nifty_chg',0):+.2f}%")
        g2.metric("S&P 500", f"{regime.get('sp_chg',0):+.2f}%")
        g3.metric("NASDAQ",  f"{regime.get('nasdaq_chg',0):+.2f}%")
        g4.metric("Nikkei",  f"{regime.get('nikkei_chg',0):+.2f}%")
        g5.metric("HSI",     f"{regime.get('hsi_chg',0):+.2f}%")
        g6.metric("Gold",    f"${regime.get('gold_price',0):,.0f}")
        g7.metric("DXY",     f"{regime.get('dxy_level',0):.1f}")
        g8.metric("USD/INR", f"₹{regime.get('inr_level',0):.2f}")

        # Sector rotation
        rotation = get_sector_rotation_signal(regime)
        if rotation:
            st.markdown(f"**Cycle:** {rotation['stage']}")
            rc1,rc2 = st.columns(2)
            rc1.success("🟢 Overweight: " + " · ".join(f"**{s}**" for s in rotation['overweight'][:5]))
            rc2.error("🔴 Underweight: " + " · ".join(f"**{s}**" for s in rotation['underweight'][:5]))
    else:
        regime = {}
        st.warning("Could not fetch live macro. Using neutral macro regime.")

# ── LOAD UNIVERSE ──────────────────────────────────────────────────────────
if run or (f"universe_{category}_{sel_tf}" not in st.session_state):
    with st.spinner(f"Scoring 545 stocks for {sel_tf} horizon..."):
        universe_df = get_universe_scores(category)
        st.session_state[f"universe_{category}_{sel_tf}"] = universe_df
        st.session_state["universe_df"] = universe_df
        st.session_state["universe_cat"] = category

universe_df: pd.DataFrame = st.session_state.get(f"universe_{category}_{sel_tf}",
                             st.session_state.get("universe_df", pd.DataFrame()))

if universe_df.empty:
    st.warning("Click 🚀 Get Picks to load data.")
    st.stop()

n = len(universe_df)

# ── MOMENTUM LAYER — fetch period returns for selected timeframe ───────────
if run or f"momentum_{sel_tf}" not in st.session_state:
    with st.spinner(f"Fetching {sel_tf} price momentum for top 200 stocks..."):
        try:
            top_syms = universe_df.nlargest(200,"Score")["Symbol"].tolist()
            momentum_df = get_alpha_universe(sel_tf)
            if not momentum_df.empty:
                momentum_df = momentum_df[momentum_df["Symbol"].isin(top_syms)]
                st.session_state[f"momentum_{sel_tf}"] = momentum_df
        except Exception:
            momentum_df = pd.DataFrame()
else:
    momentum_df = st.session_state.get(f"momentum_{sel_tf}", pd.DataFrame())

# Merge momentum into universe
if not momentum_df.empty and "Symbol" in momentum_df.columns:
    period_ret_col = "Period Ret%"
    if period_ret_col in momentum_df.columns:
        universe_df = universe_df.merge(
            momentum_df[["Symbol",period_ret_col]].rename(columns={period_ret_col:"Period Return%"}),
            on="Symbol", how="left"
        )

# ── SCORE CANDIDATES with timeframe weights ───────────────────────────────
rows = []
for _, r in universe_df.iterrows():
    sym      = r["Symbol"]
    sector   = r.get("Sector","Other")
    fund_s   = float(r.get("Score") or 50)
    macro_s  = float(r.get("Macro Score") or compute_macro_score(sector,regime))
    period_r = float(r.get("Period Return%",0) or 0)
    tech_str = r.get("Tech","Neutral") or "Neutral"

    # Timeframe-specific weight adjustments
    tf_weights = {
        "Day":      {"fund":0.20,"macro":0.25,"momentum":0.55},
        "Week":     {"fund":0.25,"macro":0.25,"momentum":0.50},
        "Month":    {"fund":0.35,"macro":0.30,"momentum":0.35},
        "3 Months": {"fund":0.45,"macro":0.30,"momentum":0.25},
        "6 Months": {"fund":0.55,"macro":0.30,"momentum":0.15},
        "1 Year":   {"fund":0.65,"macro":0.25,"momentum":0.10},
        "2 Years":  {"fund":0.75,"macro":0.20,"momentum":0.05},
        "3 Years":  {"fund":0.80,"macro":0.15,"momentum":0.05},
    }
    w = tf_weights.get(sel_tf, tf_weights["1 Year"])

    # Momentum score (normalised period return → 0-30)
    mom_score = min(30, max(0, period_r * 1.5 + 15))

    composite = (fund_s * w["fund"] +
                 min(30, max(0, macro_s + 15)) * w["macro"] +
                 mom_score * w["momentum"])
    composite = max(0, min(100, composite))

    # Analyst upside
    a_upside = r.get("Analyst Upside%")
    a_target = r.get("AnalystTarget")

    rows.append({
        "Symbol":         sym,
        "Name":           r.get("Name",""),
        "Sector":         sector,
        "Price":          r.get("Price",0),
        "Score":          round(composite,1),
        "Fund Score":     round(fund_s,1),
        "Macro Score":    round(macro_s,1),
        "Period Return%": round(period_r,2),
        "Tech":           tech_str,
        "PE":             r.get("PE"),
        "ROE":            r.get("ROE"),
        "Net Margin":     r.get("Net Margin"),
        "Rev Growth":     r.get("Rev Growth"),
        "D/E":            r.get("D/E"),
        "Graham Number":  r.get("Graham Number"),
        "PEG":            r.get("PEG"),
        "Promoter Holding%": r.get("Promoter Holding%"),
        "Interest Coverage": r.get("Interest Coverage"),
        "Analyst Upside%": a_upside,
        "AnalystTarget":  a_target,
        "Reasons":        r.get("Reasons",""),
    })

scored_df = pd.DataFrame(rows).sort_values("Score", ascending=False).reset_index(drop=True)

# ── AI BEST PICKS ─────────────────────────────────────────────────────────
st.divider()
if run:
    with st.spinner(f"Gemini selecting top 5 for {sel_tf} horizon..."):
        # Enrich prompt with timeframe context
        horizon_hint = f"Timeframe focus: {sel_tf} ({tf['horizon']}). {tf['hot']}."
        raw = analyse_best_picks(scored_df.head(20), category,
                                  {**regime, "horizon_hint": horizon_hint})
        try:
            clean = re.sub(r"```json|```","",raw).strip()
            s = clean.find("["); e = clean.rfind("]")+1
            picks = json.loads(clean[s:e]) if s!=-1 and e>s else []
        except Exception:
            picks = []
        st.session_state[f"picks_{sel_tf}_{category}"] = picks

picks = st.session_state.get(f"picks_{sel_tf}_{category}", [])

if picks:
    st.markdown(f"### 🏆 Gemini Top 5 — {sel_tf} Horizon")
    for idx, p in enumerate(picks[:5]):
        sym         = p.get("symbol","")
        name        = p.get("name","")
        price       = float(p.get("price",0) or 0)
        sector      = p.get("sector","")
        thesis      = p.get("thesis","")
        entry       = p.get("entryZone","")
        stop        = p.get("stopLoss","")
        conv        = p.get("conviction","")

        # Timeframe-appropriate target
        tgt_map = {"Day":"target3m","Week":"target3m","Month":"target3m",
                   "3 Months":"target6m","6 Months":"target12m",
                   "1 Year":"target12m","2 Years":"target24m","3 Years":"target36m"}
        tgt_key = tgt_map.get(sel_tf,"target12m")
        tgt     = p.get(tgt_key) or p.get("target12m","—")

        bull_p  = float(p.get("bullProb",55)  or 55)
        base_p  = float(p.get("baseProb",30)  or 30)
        bear_p  = float(p.get("bearProb",15)  or 15)
        exp_r   = float(p.get("expectedReturn12m",0) or 0)

        # Downside
        try:
            stp_num = float(str(stop).replace("₹","").replace(",",""))
            dn_p    = abs((price/stp_num - 1)*100) if stp_num > 0 else 10
        except Exception:
            dn_p = 10

        try:
            upside_p = (float(str(tgt).replace("₹","").replace(",",""))/price - 1)*100 if price > 0 else 0
        except Exception:
            upside_p = 0

        conv_color = "#22C55E" if conv=="High" else "#F59E0B"
        pw_color   = "#22C55E" if exp_r > 0 else "#EF4444"

        with st.expander(f"#{idx+1} {sym} — {name}", expanded=(idx==0)):
            r1c1,r1c2,r1c3,r1c4,r1c5 = st.columns(5)
            def mcard(col, label, val, color, delta=""):
                col.markdown(f"""<div style="background:#111113;border:1px solid {color}44;border-radius:8px;padding:10px;text-align:center">
                  <div style="font-size:10px;color:#71717A;text-transform:uppercase">{label}</div>
                  <div style="font-family:monospace;font-size:14px;font-weight:700;color:{color};margin-top:3px">{val}</div>
                  {f'<div style="font-size:11px;color:#64748B">{delta}</div>' if delta else ''}
                </div>""", unsafe_allow_html=True)
            mcard(r1c1,"Entry Zone",    entry,              "#F59E0B")
            mcard(r1c2,f"Target ({sel_tf})", str(tgt),     "#22C55E", f"↑ {upside_p:+.1f}%")
            mcard(r1c3,"Stop Loss",     stop,               "#EF4444", f"↓ {dn_p:.1f}%")
            mcard(r1c4,"Risk:Reward",   p.get("riskReward","—"), "#38BDF8")
            mcard(r1c5,"Position Size", p.get("positionSize","—"), conv_color)

            c1,c2 = st.columns([3,1])
            with c1:
                st.markdown(f"**Thesis:** {thesis}")
                cats = p.get("catalysts",[])
                risks = p.get("risks",[])
                if cats:  st.markdown("**Catalysts:** " + " · ".join(f"✅ {c}" for c in cats[:3]))
                if risks: st.markdown("**Risks:** "     + " · ".join(f"⚠️ {r}" for r in risks[:2]))
            with c2:
                st.markdown(f"""<div style="background:#111113;border:1px solid #27272A;border-radius:8px;padding:12px;text-align:center">
                  <div style="font-size:10px;color:#71717A">EXPECTED RETURN</div>
                  <div style="font-family:monospace;font-size:22px;font-weight:800;color:{pw_color}">{exp_r:+.1f}%</div>
                  <div style="font-size:10px;color:#64748B;margin-top:2px">{tf['horizon']} probability-weighted</div>
                  <div style="font-size:10px;color:#64748B">🐂{bull_p:.0f}% / ⚖{base_p:.0f}% / 🐻{bear_p:.0f}%</div>
                </div>""", unsafe_allow_html=True)
else:
    st.info(f"Select a timeframe above and click **🚀 Get Picks** to see Gemini's top 5 for the **{sel_tf}** horizon.")

# ── UNIVERSE TABLE ─────────────────────────────────────────────────────────
st.divider()
sector_pe = get_sector_pe_averages(universe_df)
with st.expander(f"📊 Scored Universe — {n} stocks ranked for {sel_tf} horizon", expanded=False):
    search = st.text_input("Search", key="u_search", placeholder="Symbol or name...")
    disp = scored_df.copy()
    disp["Sector PE"] = disp["Sector"].map(sector_pe)
    disp["PE vs Sector"] = disp.apply(
        lambda r: round((r["PE"]/r["Sector PE"]-1)*100,1)
        if (r.get("PE") and r.get("Sector PE") and r["Sector PE"]>0) else None, axis=1)
    if search:
        disp = disp[disp["Symbol"].str.contains(search.upper(),na=False)|
                    disp["Name"].str.contains(search,case=False,na=False)]

    show = [c for c in ["Symbol","Name","Sector","Price","Score","Macro Score",
                         "Period Return%","PE","Sector PE","PE vs Sector","PEG",
                         "Graham Number","ROE","Net Margin","Rev Growth","D/E",
                         "Promoter Holding%","Interest Coverage","Tech",
                         "Analyst Upside%","Reasons"] if c in disp.columns]
    d = disp[show].head(200).copy()

    for col,fn in [("ROE",lambda x:f"{x*100:.1f}%"),("Net Margin",lambda x:f"{x*100:.1f}%"),
                   ("Rev Growth",lambda x:f"{x*100:.1f}%"),("PE",lambda x:f"{x:.1f}"),
                   ("D/E",lambda x:f"{x:.0f}"),("PEG",lambda x:f"{x:.2f}"),
                   ("Promoter Holding%",lambda x:f"{x*100:.1f}%"),
                   ("Interest Coverage",lambda x:f"{x:.1f}x"),
                   ("Graham Number",lambda x:f"₹{x:,.0f}"),
                   ("Analyst Upside%",lambda x:f"{x:+.1f}%"),
                   ("PE vs Sector",lambda x:f"{x:+.1f}%"),
                   ("Period Return%",lambda x:f"{x:+.2f}%")]:
        if col in d: d[col] = d[col].map(lambda x,f=fn: f(x) if x else "—")
    for col in [("Price","₹{:,.0f}"),("Sector PE","{:.1f}")]:
        if col[0] in d: d[col[0]] = d[col[0]].map(lambda x,f=col[1]: f.format(x) if x else "—")

    st.dataframe(d, use_container_width=True, hide_index=False,
        column_config={
            "Score": st.column_config.ProgressColumn("Score",min_value=0,max_value=100,format="%.1f",
                      help=f"Composite for {sel_tf}: Fund×{int(tf_weights.get(sel_tf,tf_weights['1 Year'])['fund']*100)}% + Macro×{int(tf_weights.get(sel_tf,tf_weights['1 Year'])['macro']*100)}% + Momentum×{int(tf_weights.get(sel_tf,tf_weights['1 Year'])['momentum']*100)}%"),
            "Macro Score": st.column_config.NumberColumn("Macro",format="%+.0f",
                           help="Global macro: crude/INR/VIX/NASDAQ/Nikkei/HSI/Gold/DXY"),
            "PE vs Sector": st.column_config.TextColumn("PE vs Sector",
                            help="Negative = cheaper than sector peers"),
        })

    with st.spinner("Building Excel..."):
        excel_bytes = build_full_excel(disp[show].head(200), universe_df, regime,
                                       f"AI Picks — {sel_tf}")
    st.download_button("📥 Download Excel — Full Universe",
        data=excel_bytes, file_name=f"NIVESH_Picks_{sel_tf.replace(' ','_')}_{category}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    st.caption(f"Score formula for {sel_tf}: **Fundamental {int(tf_weights.get(sel_tf,tf_weights['1 Year'])['fund']*100)}%** + **Macro {int(tf_weights.get(sel_tf,tf_weights['1 Year'])['macro']*100)}%** + **Momentum {int(tf_weights.get(sel_tf,tf_weights['1 Year'])['momentum']*100)}%**")
