"""
Macro Dashboard — fully auto-detected from live data.
No manual inputs needed. Sector rotation + AI analysis auto-run.
"""
import streamlit as st
from utils.style import inject_css, theme_toggle
from utils.data import (get_macro, get_sectors, get_live_macro_regime,
                         get_sector_rotation_signal, compute_macro_score, SECTOR_MACRO)
from utils import ai_utils

st.set_page_config(page_title="Macro — NIVESH", page_icon="🌍", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)

st.title("🌍 Global Macro Dashboard")
st.caption("Live auto-detected macro regime · No manual inputs · Sector rotation · AI analysis")

# ── AUTO-DETECT ALL MACRO DATA ─────────────────────────────────────────────
with st.spinner("Fetching live global macro data..."):
    regime = get_live_macro_regime()
    macro_df = get_macro()

if not regime:
    st.error("Could not fetch live macro data. Check connection.")
    st.stop()

# ── LIVE MACRO SNAPSHOT ────────────────────────────────────────────────────
st.subheader("📡 Live Global Macro — Auto-Detected")
st.caption("All values fetched live from NSE, yfinance. No manual input required.")

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Brent Crude",    f"${regime.get('crude_price',80):.0f}/bbl",
          "⬆ High" if regime.get('crude_high') else "⬇ Low" if regime.get('crude_low') else "Moderate")
c2.metric("India VIX",      f"{regime.get('vix_level',15):.1f}",
          "⚠️ Elevated" if regime.get('high_vix') else "Normal")
c3.metric("USD/INR",        f"₹{regime.get('inr_level',84):.2f}",
          "Weak INR" if regime.get('inr_weak') else "Strong INR" if regime.get('inr_strong') else "Stable")
c4.metric("US 10Y Yield",   f"{regime.get('us10y',4.5):.2f}%",
          "Easy policy" if regime.get('rate_cut') else "Tight" if regime.get('rate_hike') else "Neutral")
c5.metric("Gold",           f"${regime.get('gold_price',2000):,.0f}",
          "Risk-off" if regime.get('gold_high') else "Normal")
c6.metric("DXY (Dollar)",   f"{regime.get('dxy_level',104):.1f}",
          "Strong $" if regime.get('dollar_strong') else "Weak $" if regime.get('dollar_weak') else "Neutral")

st.divider()

c7,c8,c9,c10 = st.columns(4)
c7.metric("Nifty Day",     f"{regime.get('nifty_chg',0):+.2f}%",
          "🐂 Bull" if regime.get('mkt_up') else "🐻 Bear" if regime.get('mkt_down') else "→")
c8.metric("S&P 500",       f"{regime.get('sp_chg',0):+.2f}%",
          "Bull" if regime.get('us_bull') else "Bear" if regime.get('us_bear') else "Neutral")
c9.metric("NASDAQ",        f"{regime.get('nasdaq_chg',0):+.2f}%",
          "IT positive" if regime.get('nasdaq_bull') else "IT negative" if regime.get('nasdaq_bear') else "Neutral")
c10.metric("Hang Seng",    f"{regime.get('hsi_chg',0):+.2f}%",
           "China bull" if regime.get('china_bull') else "China bear" if regime.get('china_bear') else "Neutral")

st.divider()

# ── ACTIVE MACRO FLAGS ─────────────────────────────────────────────────────
st.subheader("🚦 Active Macro Flags")
st.caption("Flags that are currently TRUE — these drive sector rotation scores")
flag_map = {
    "crude_high":    ("🛢 High Crude (>$90)",         "⚠️ Headwind for Auto, Aviation, FMCG. Tailwind for Energy, Metal."),
    "crude_low":     ("🛢 Low Crude (<$70)",           "✅ Tailwind for Auto, Aviation, FMCG. Headwind for Energy."),
    "high_vix":      ("⚡ High VIX (>20)",             "⚠️ Risk-off. Move to defensives: FMCG, Pharma, IT."),
    "inr_weak":      ("💱 Weak INR (>₹85)",           "✅ Exporters gain: IT, Pharma, Metal. Importers lose: Oil, Aviation."),
    "inr_strong":    ("💱 Strong INR (<₹82)",          "⚠️ Exporters lose. Importers gain."),
    "us_bear":       ("🇺🇸 US Bear Market",            "⚠️ FII outflows from India likely. IT sector at risk."),
    "nasdaq_bear":   ("💻 NASDAQ Falling",             "⚠️ Indian IT stocks correlated. TCS, Infosys, Wipro at risk."),
    "china_bear":    ("🇨🇳 China Bear (HSI down)",    "⚠️ Metal demand falls. JSW Steel, Tata Steel headwind."),
    "gold_high":     ("🥇 Gold >$2200",                "📊 Risk-off signal. Defensives outperform cyclicals."),
    "dollar_strong": ("💵 Strong Dollar (DXY>106)",   "⚠️ FII sells EM including India. All sectors face headwind."),
    "rate_cut":      ("🏦 Rate Cut Regime",            "✅ Banking, NBFC, Realty, Consumer — all benefit from cheaper credit."),
    "rate_hike":     ("🏦 Rate Hike Regime",           "⚠️ Banking margins squeeze. NBFC, Realty under pressure."),
    "mkt_up":        ("📈 Nifty Uptrend",              "✅ Risk-on. Cyclicals, Midcap, Smallcap outperform."),
    "mkt_down":      ("📉 Nifty Downtrend",            "⚠️ Defensive tilt. FMCG, Pharma, IT hold better."),
    "nikkei_up":     ("🇯🇵 Nikkei Rising",            "📊 Global risk-on signal. Cyclicals benefit."),
    "nasdaq_bull":   ("💻 NASDAQ Rising",              "✅ Indian IT sector boost. TCS, Infosys, HCL Tech up."),
    "china_bull":    ("🇨🇳 China Bull",                "✅ Metal demand rises. JSW Steel, Tata Steel benefit."),
    "dollar_weak":   ("💵 Weak Dollar",                "✅ FII buys EM. India gets capital inflows. Broad market positive."),
}
active_flags = [(k,v) for k,v in flag_map.items() if regime.get(k)]
if active_flags:
    cols = st.columns(2)
    for i,(flag,(label,impact)) in enumerate(active_flags):
        with cols[i%2]:
            color = "#22C55E" if "✅" in impact else "#EF4444" if "⚠️" in impact else "#F59E0B"
            st.markdown(f"""<div style="background:#111113;border-left:3px solid {color};border-radius:0 8px 8px 0;padding:10px 14px;margin:4px 0">
              <div style="font-size:13px;font-weight:600;color:#FAFAFA">{label}</div>
              <div style="font-size:12px;color:#A1A1AA;margin-top:3px">{impact}</div>
            </div>""", unsafe_allow_html=True)
else:
    st.info("No strong macro flags active. Market in neutral/transition regime.")

st.divider()

# ── SECTOR ROTATION ────────────────────────────────────────────────────────
st.subheader("🔄 Sector Rotation Signal — Auto from Live Data")
rotation = get_sector_rotation_signal(regime)
if rotation:
    stage_color = "#22C55E" if "BULL" in rotation["stage"] else "#EF4444" if "RISK" in rotation["stage"] else "#F59E0B"
    st.markdown(f"""<div style="background:{stage_color}18;border:2px solid {stage_color}44;border-radius:10px;padding:16px;margin-bottom:12px">
      <div style="font-size:18px;font-weight:700;color:{stage_color}">📍 {rotation['stage']}</div>
    </div>""", unsafe_allow_html=True)
    rc1,rc2 = st.columns(2)
    rc1.success("🟢 Overweight: " + " · ".join(f"**{s}**" for s in rotation["overweight"][:7]))
    rc2.error("🔴 Underweight: " + " · ".join(f"**{s}**" for s in rotation["underweight"][:7]))
    for r in rotation["rationale"]: st.caption(f"• {r}")

st.divider()

# ── SECTOR MACRO SCORES ─────────────────────────────────────────────────────
st.subheader("📊 Live Macro Score — All Sectors")
st.caption("Score = how current global macro helps (+) or hurts (−) each sector. Range: −20 to +20")
sectors = list(SECTOR_MACRO.keys())
scores = [(s, compute_macro_score(s, regime)) for s in sectors if s != "Other"]
scores.sort(key=lambda x: x[1], reverse=True)
cols = st.columns(5)
for i, (sector, score) in enumerate(scores):
    color = "#22C55E" if score > 5 else "#EF4444" if score < -5 else "#F59E0B"
    with cols[i%5]:
        st.markdown(f"""<div style="background:#111113;border:1px solid {color}33;border-radius:8px;padding:10px;text-align:center;margin:3px 0">
          <div style="font-size:11px;color:#A1A1AA">{sector}</div>
          <div style="font-family:monospace;font-size:18px;font-weight:700;color:{color}">{score:+d}</div>
        </div>""", unsafe_allow_html=True)

st.divider()

# ── AI MACRO ANALYSIS (auto, no manual input) ─────────────────────────────
st.subheader("🤖 AI Macro Analysis")
st.caption("Auto-analysis using live-detected macro regime. Gemini + web search for latest context.")

if st.button("🤖 Run AI Macro Analysis", type="primary"):
    macro_summary = (
        f"LIVE MACRO REGIME (auto-fetched):\n"
        f"Brent Crude: ${regime.get('crude_price',80):.0f}/bbl | India VIX: {regime.get('vix_level',15):.1f} | USD/INR: ₹{regime.get('inr_level',84):.2f}\n"
        f"US 10Y: {regime.get('us10y',4.5):.2f}% | Gold: ${regime.get('gold_price',2000):,.0f} | DXY: {regime.get('dxy_level',104):.1f}\n"
        f"Nifty: {regime.get('nifty_chg',0):+.2f}% | S&P500: {regime.get('sp_chg',0):+.2f}% | NASDAQ: {regime.get('nasdaq_chg',0):+.2f}%\n"
        f"Nikkei: {regime.get('nikkei_chg',0):+.2f}% | Hang Seng: {regime.get('hsi_chg',0):+.2f}%\n"
        f"Active flags: {', '.join(k for k,v in regime.items() if v is True and isinstance(v,bool))}\n"
        f"Cycle stage: {rotation.get('stage','') if rotation else ''}\n"
        f"Overweight sectors: {', '.join(rotation.get('overweight',[])[:5]) if rotation else ''}\n"
    )
    prompt = (
        f"{macro_summary}\n\n"
        "Based on this LIVE macro regime, provide:\n"
        "1. **Macro Regime Name** — what economic cycle phase are we in?\n"
        "2. **Top 3 Sector Overweights** — which sectors to own and exactly why given above data\n"
        "3. **Top 3 Sector Underweights** — which to avoid and exactly why\n"
        "4. **3 Specific Stock Ideas** — one from each overweight sector with thesis\n"
        "5. **Key Risk** — what single event could flip this regime?\n"
        "6. **Nifty Outlook** — 3-month direction, key levels to watch\n"
        "7. **Portfolio Action** — what to buy/sell/hold right now"
    )
    with st.spinner("Gemini analysing live macro regime..."):
        result = ai_utils.generate(prompt, temperature=0.3, max_tokens=65536, use_search=True)
    st.markdown(result)
