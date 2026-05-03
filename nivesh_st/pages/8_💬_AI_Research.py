"""
AI Research Terminal — connected intelligence.
Knows live prices, macro, fundamentals, sector rotation, global markets.
Ask anything about Indian equities and get data-backed answers.
"""
import streamlit as st
import re
from datetime import datetime
from utils.style import inject_css, theme_toggle
from utils import ai_utils
from utils.data import (get_nse_live_quote, get_fundamentals, get_screener_data,
                         get_live_macro_regime, get_sector_rotation_signal,
                         compute_macro_score, SECTOR_MACRO, NIFTY50,
                         get_nse_delivery_data, get_history)
from utils.math_utils import compute_all_signals_enhanced

st.set_page_config(page_title="AI Research Terminal — NIVESH", page_icon="💬", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("💬 AI Research Terminal")
st.caption(f"Powered by {ai_utils.get_model_name()} · Web search grounding · Live NSE prices · Global macro context · Connected to everything")

# ── CAPABILITIES EXPLAINER ─────────────────────────────────────────────────
with st.expander("🧠 What can I ask? (examples)"):
    st.markdown("""
**Stock Research**
- *"Analyse Reliance Industries for long-term investment"*
- *"Compare TCS vs Infosys vs HCL Tech — which is better now?"*
- *"Zomato — is the current price a good entry?"*
- *"What are the top 5 small cap stocks to buy in the infra theme?"*

**Macro & Sector**
- *"How will a US recession affect Indian IT stocks?"*
- *"With crude at $90, which Indian sectors benefit and which suffer?"*
- *"What is the impact of a strong dollar on FII flows and Nifty?"*
- *"Explain the current RBI rate cycle and what to buy/avoid"*

**Portfolio**
- *"Build me a 10L portfolio for 3-year horizon, moderate risk"*
- *"I hold HDFC Bank, TCS and Reliance — should I rebalance?"*
- *"SIP in which mutual funds makes sense for 15-year wealth creation?"*

**Events & News**
- *"What happened to Adani stocks this week?"*
- *"What are the key risks for the Indian market in the next 3 months?"*
- *"Which stocks are reporting results this week and what to expect?"*

**Education**
- *"Explain PEG ratio and how to use it for Indian stocks"*
- *"What is the difference between LTCG and STCG tax in India?"*
- *"How does the Kelly Criterion work for position sizing?"*
    """)

# ── CONTEXT BUILDER ────────────────────────────────────────────────────────
def build_context(question: str) -> str:
    """
    Smart context injection — detects what the question is about,
    fetches relevant live data, injects it into the prompt.
    This is what makes the terminal 'connected'.
    """
    context_parts = []
    today = datetime.now().strftime("%A, %d %B %Y, %H:%M IST")
    context_parts.append(f"Current date and time: {today}")

    # ── Detect NSE stock tickers mentioned ─────────────────────────────────
    q_upper = question.upper()
    # Common stock references — check both symbol and company name patterns
    found_stocks = []
    for sym in NIFTY50[:50]:
        if sym in q_upper or sym.lower() in question.lower():
            found_stocks.append(sym)

    # Also detect patterns like "Reliance", "Tata Motors", etc.
    common_names = {
        "RELIANCE":["reliance"], "TCS":["tcs","tata consultancy"],
        "HDFCBANK":["hdfc bank","hdfcbank"], "ICICIBANK":["icici bank"],
        "INFOSYS":["infosys","infy"], "BHARTIARTL":["airtel","bharti"],
        "SBIN":["sbi","state bank"], "MARUTI":["maruti","suzuki"],
        "ZOMATO":["zomato"], "ADANIENT":["adani"], "TATAMOTORS":["tata motor"],
        "TATASTEEL":["tata steel"], "SUNPHARMA":["sun pharma"],
        "WIPRO":["wipro"], "BAJFINANCE":["bajaj finance"],
        "TITAN":["titan"], "HCLTECH":["hcl tech"], "AXISBANK":["axis bank"],
        "KOTAKBANK":["kotak"], "NTPC":["ntpc"], "ONGC":["ongc"],
        "POWERGRID":["power grid"], "COALINDIA":["coal india"],
        "ULTRACEMCO":["ultratech"], "ASIANPAINT":["asian paint"],
        "NESTLEIND":["nestle"], "HINDUNILVR":["hindustan unilever","hul"],
        "BAJAJFINSV":["bajaj finserv"], "JSWSTEEL":["jsw steel"],
        "LTIM":["ltimindtree","lti"], "TECHM":["tech mahindra"],
        "TRENT":["trent"], "APOLLOHOSP":["apollo hospital"],
    }
    for sym, aliases in common_names.items():
        if any(alias in question.lower() for alias in aliases):
            if sym not in found_stocks:
                found_stocks.append(sym)

    # Fetch live data for detected stocks (max 3)
    if found_stocks:
        for sym in found_stocks[:3]:
            try:
                live = get_nse_live_quote(sym)
                info = get_fundamentals(sym)
                screener = get_screener_data(sym)
                hist = get_history(sym, "3mo", "1d")
                signals = compute_all_signals_enhanced(hist) if not hist.empty else {}
                deliv = get_nse_delivery_data(sym)

                stock_ctx = [f"\n📊 LIVE DATA — {sym}:"]
                if live and live.get("price"):
                    stock_ctx.append(f"  Price: ₹{live['price']:,.2f} | Change: {live.get('change',0):+.2f} ({live.get('changePercent',0):+.2f}%)")
                    if live.get("vwap"):     stock_ctx.append(f"  VWAP: ₹{live['vwap']:,.2f}")
                    if live.get("symbolPE"): stock_ctx.append(f"  Live PE (NSE): {live['symbolPE']} | Sector PE: {live.get('sectorPE','—')}")
                    if live.get("upperCircuit"): stock_ctx.append(f"  Circuit: ₹{live['lowerCircuit']}–₹{live['upperCircuit']}")

                if info:
                    mc = info.get("marketCap",0)
                    if mc: stock_ctx.append(f"  Market Cap: ₹{mc/1e7:.0f}Cr")
                    pe  = info.get("trailingPE")
                    pb  = info.get("priceToBook")
                    roe = info.get("returnOnEquity")
                    mg  = info.get("profitMargins")
                    rg  = info.get("revenueGrowth")
                    eg  = info.get("earningsGrowth")
                    de  = info.get("debtToEquity")
                    if pe:  stock_ctx.append(f"  PE: {pe:.1f} | PB: {pb or '—'}")
                    if roe: stock_ctx.append(f"  ROE: {roe*100:.1f}% | Net Margin: {mg*100:.1f}%" if mg else f"  ROE: {roe*100:.1f}%")
                    if rg:  stock_ctx.append(f"  Rev Growth: {rg*100:.1f}% | EPS Growth: {eg*100:.1f}%" if eg else f"  Rev Growth: {rg*100:.1f}%")
                    if de:  stock_ctx.append(f"  D/E: {de:.2f} | Analyst Target: ₹{info.get('targetMeanPrice','—')}")

                if screener:
                    sc = []
                    if screener.get("screener_roce"):  sc.append(f"ROCE={screener['screener_roce']:.1f}%")
                    if screener.get("screener_pe"):    sc.append(f"PE(Screener)={screener['screener_pe']:.1f}")
                    pledged = screener.get("promoter_pledged_pct")
                    if pledged is not None:            sc.append(f"Pledged={pledged:.1f}%{'⚠️' if pledged>10 else ''}")
                    if screener.get("sales_cagr_3y"):  sc.append(f"Sales3YCAGR={screener['sales_cagr_3y']:.1f}%")
                    if sc: stock_ctx.append(f"  Screener.in: {' | '.join(sc)}")

                if signals:
                    stock_ctx.append(f"  Technical: {signals.get('overall','—')} | RSI={signals.get('rsi',0):.1f} | ATR=₹{signals.get('atr',0):.2f}")
                    pvt = signals.get("pivots",{})
                    if pvt: stock_ctx.append(f"  Pivots: S1=₹{pvt.get('S1',0):,.0f} P=₹{pvt.get('Pivot',0):,.0f} R1=₹{pvt.get('R1',0):,.0f}")

                dp = deliv.get("delivery_pct")
                if dp:
                    try: stock_ctx.append(f"  Delivery %: {float(str(dp).replace('%','')):.1f}% (high=conviction buying)")
                    except: pass

                context_parts.append('\n'.join(stock_ctx))
            except Exception:
                pass

    # ── Global Macro Context ────────────────────────────────────────────────
    macro_keywords = ["macro","market","nifty","sensex","rbi","rate","inflation","crude",
                      "rupee","inr","dollar","dxy","nasdaq","nikkei","fed","global",
                      "sector","buy","sell","portfolio","invest","pick","economy"]
    needs_macro = any(kw in question.lower() for kw in macro_keywords)

    if needs_macro or found_stocks:
        try:
            regime = get_live_macro_regime()
            if regime:
                rotation = get_sector_rotation_signal(regime)
                macro_ctx = ["\n🌍 LIVE GLOBAL MACRO:"]
                macro_ctx.append(f"  Nifty: {regime.get('nifty_chg',0):+.2f}% | S&P500: {regime.get('sp_chg',0):+.2f}% | NASDAQ: {regime.get('nasdaq_chg',0):+.2f}%")
                macro_ctx.append(f"  Nikkei: {regime.get('nikkei_chg',0):+.2f}% | Hang Seng: {regime.get('hsi_chg',0):+.2f}% (China)")
                macro_ctx.append(f"  Brent: ${regime.get('crude_price',80):.0f}/bbl | Gold: ${regime.get('gold_price',2000):,.0f} | DXY: {regime.get('dxy_level',104):.1f}")
                macro_ctx.append(f"  USD/INR: ₹{regime.get('inr_level',84):.2f} | India VIX: {regime.get('vix_level',15):.1f} | US 10Y: {regime.get('us10y',4.5):.2f}%")
                macro_ctx.append(f"  Flags: crude_high={regime.get('crude_high',False)} | INR_weak={regime.get('inr_weak',False)} | dollar_strong={regime.get('dollar_strong',False)} | high_vix={regime.get('high_vix',False)}")
                if rotation:
                    macro_ctx.append(f"  Cycle: {rotation['stage']}")
                    macro_ctx.append(f"  Overweight: {', '.join(rotation['overweight'][:5])}")
                    macro_ctx.append(f"  Underweight: {', '.join(rotation['underweight'][:5])}")
                context_parts.append('\n'.join(macro_ctx))

                # Sector-specific macro for mentioned stocks
                if found_stocks:
                    from utils.data import SECTOR_MAP
                    for sym in found_stocks[:2]:
                        sector = SECTOR_MAP.get(sym,"Other")
                        macro_score = compute_macro_score(sector, regime)
                        context_parts.append(f"  {sym} sector ({sector}) macro impact: {macro_score:+d}/20 ({'tailwind' if macro_score>5 else 'headwind' if macro_score<-5 else 'neutral'})")
        except Exception:
            pass

    return '\n'.join(context_parts)

# ── SYSTEM PROMPT ──────────────────────────────────────────────────────────
SYSTEM = """You are NIVESH — India's most comprehensive equity research AI terminal.

You have access to live data injected into each conversation:
- NSE live prices, VWAP, circuit limits, delivery %
- Verified fundamentals: PE, ROE, ROCE, margins, D/E, promoter pledging (Screener.in)
- Technical signals: RSI, pivot points, ATR, momentum
- Global macro: Nifty, S&P500, NASDAQ, Nikkei, Hang Seng, Gold, DXY, USD/INR, Brent crude, US 10Y
- Sector rotation signal based on live economic cycle position

RULES:
1. Always give DEEP, EXHAUSTIVE analysis — never a summary. User wants the full picture.
2. Always give specific ₹ prices, % numbers, bps, dates — never vague
3. When live data is in context, reference it explicitly ("RELIANCE is at ₹2,940, RSI=64...")
4. For EVERY sector mentioned: which specific stocks to buy, which to sell, entry zone, target, stop loss
5. For macro questions: explain the TRANSMISSION MECHANISM in full — how does repo rate → lending rate → EMI → demand → sales → earnings → stock price
6. For rate cycle questions: cover ALL affected sectors with specific NSE stocks, analyst targets, and 12M price targets
7. Always include: Bull case / Bear case / Base case with probabilities
8. Always include tail risks with specific triggers
9. Format: Use headers (###), bold key numbers, tables where helpful, bullet points for stock lists
10. MANDATORY STOCK TABLE: Every macro/sector question MUST end with a stock table:
    | NSE Symbol | Company | CMP (₹) | 12M Target | Stop Loss | Why now | Rating |
    Always include minimum 5-8 stocks. This is NON-NEGOTIABLE.
11. For stock picks: Symbol (NSE), CMP ₹, entry zone, 12M target, stop loss, upside%, why NOW in 1 line
12. Connect global macro to Indian stocks: "RBI cuts repo → HDFC Bank NIMs compress short-term → stock dips → BUY"
13. Use Indian context: Nifty levels, RBI MPC, SEBI, NSE/BSE, FII/DII flows, F&O OI data
14. Structure every macro answer as: 
    MACRO CONTEXT (2 para) → BENEFICIARY SECTORS → STOCK PICKS TABLE → SECTORS TO AVOID → RISKS
15. If user asks about a rate cycle/sector/theme — give at least 8 stock picks with full details

You are connected to web search. Search for: latest analyst reports, current stock prices, recent RBI MPC decisions.
CRITICAL: User wants ACTIONABLE STOCK PICKS. Always end with a stock table. Never give only narrative."""

# ── CHAT STATE ─────────────────────────────────────────────────────────────
if "research_history" not in st.session_state:
    st.session_state.research_history = []
    st.session_state.research_contexts = []

# ── QUICK PROMPTS ──────────────────────────────────────────────────────────
QUICK = [
    ("Nifty outlook",         "What is the current Nifty 50 outlook? Key levels, near-term direction, and what could change the trend?"),
    ("Rate cycle impact",     "RBI rate cycle analysis — I need SPECIFIC STOCKS. Give me: (1) Current repo rate, MPC stance, expected next move. (2) For EACH beneficiary sector (Banking, NBFC, Realty, Auto, Consumer, Infra) — name 2 specific NSE stocks with: current price ₹, 12-month target ₹, stop loss ₹, and 1-line why. (3) For sectors to avoid — name stocks to sell/avoid with downside target. (4) Top 3 highest-conviction buys right now in this rate environment with full entry thesis. FORMAT: Lead with a stock picks table, then explain the macro."),
    ("US/Global impact",      "How are US markets, dollar strength, and global macro affecting Indian equities right now? Which Indian sectors are most exposed?"),
    ("Best buys now",         "Given current macro regime, global signals, and valuations — which 5 Indian stocks offer the best risk-reward right now?"),
    ("FII activity",          "Deep analysis of current FII activity: exact net flows last 30 days in ₹Cr, which sectors FIIs are buying vs selling, which specific stocks have seen highest FII accumulation, what does DXY level and US Fed stance mean for FII flows in next 3-6 months, and which Indian stocks benefit most from FII buying — with entry zones and targets."),
    ("Crude oil impact",      "With crude at current levels, analyse the impact on Indian aviation, paints, chemicals, OMCs, and auto sectors specifically."),
    ("Portfolio 10L",         "Build an optimal 10-lakh portfolio for a 3-year horizon with moderate risk — specific stocks, allocation %, and reasoning."),
    ("NASDAQ fall impact",    "If NASDAQ falls 10%, what happens to Indian IT stocks? Which ones are most/least vulnerable?"),
    ("Gold & defensives",     "Current gold price signal — what does it mean for defensive sectors? Should I move to FMCG and pharma?"),
    ("Dollar DXY impact",     "Strong DXY/dollar — how does it affect FII flows, INR, and which Indian sectors benefit/suffer?"),
    ("Results this week",     "Which major Indian companies are announcing quarterly results this week? What are consensus estimates?"),
    ("PSU vs Private banks",  "Compare PSU banks (SBI, PNB, Bank of Baroda) vs private banks (HDFC, ICICI, Kotak) — which to hold now?"),
]

st.markdown("**Quick Research:**")
q_cols = st.columns(6)
for i, (label, prompt) in enumerate(QUICK):
    if q_cols[i%6].button(label, key=f"qp_{i}", use_container_width=True):
        st.session_state.research_history.append({"role":"user","content":prompt})
        ctx = build_context(prompt)
        st.session_state.research_contexts.append(ctx)
        full_prompt = f"[LIVE MARKET DATA]\n{ctx}\n[END DATA]\n\nUser question: {prompt}"
        with st.spinner("Researching with live data + web search..."):
            response = ai_utils.generate(full_prompt, temperature=0.4, max_tokens=2000, use_search=True)
        st.session_state.research_history.append({"role":"assistant","content":response})
        st.rerun()

st.divider()

# ── CHAT DISPLAY ────────────────────────────────────────────────────────────
for msg in st.session_state.research_history:
    if msg["role"] == "user":
        st.markdown(f"""<div style="background:#1A1A2E;border-left:3px solid #F59E0B;border-radius:0 8px 8px 0;padding:12px 16px;margin:8px 0">
          <span style="font-size:10px;color:#71717A;text-transform:uppercase">You</span><br>
          <span style="color:#FAFAFA;font-size:14px">{msg['content']}</span>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="background:#0D111C;border-left:3px solid #3B82F6;border-radius:0 8px 8px 0;padding:12px 16px;margin:8px 0">
          <span style="font-size:10px;color:#71717A;text-transform:uppercase">NIVESH AI</span><br>
          {msg['content']}
        </div>""", unsafe_allow_html=True)

# ── INPUT ───────────────────────────────────────────────────────────────────
col_inp, col_btn, col_clr = st.columns([6,1,1])
with col_inp:
    question = st.text_input("", placeholder="Ask anything — stock analysis, macro impact, portfolio, sector rotation, global markets...",
                              key="research_q", label_visibility="collapsed")
with col_btn:
    send = st.button("Ask", type="primary", use_container_width=True)
with col_clr:
    if st.button("Clear", use_container_width=True):
        st.session_state.research_history = []
        st.session_state.research_contexts = []
        st.rerun()

if send and question.strip():
    st.session_state.research_history.append({"role":"user","content":question})

    # Build rich context from live data
    with st.spinner("Fetching live market data..."):
        ctx = build_context(question)

    # Inject context + history into Gemini
    history_for_ai = st.session_state.research_history[:-1]  # exclude current question
    full_question = f"[LIVE MARKET DATA — fetched right now]\n{ctx}\n[END LIVE DATA]\n\nQuestion: {question}"

    with st.spinner("NIVESH AI researching with web search..."):
        if len(history_for_ai) > 0:
            response = ai_utils.chat_response(history_for_ai, full_question)
        else:
            response = ai_utils.generate(full_question, temperature=0.4, max_tokens=4000, use_search=True)

    st.session_state.research_history.append({"role":"assistant","content":response})
    st.rerun()

# ── CONTEXT TRANSPARENCY ────────────────────────────────────────────────────
if st.session_state.research_contexts:
    with st.expander("🔍 Live data injected into last question", expanded=False):
        st.code(st.session_state.research_contexts[-1], language="text")
    st.caption(f"Model: {ai_utils.get_model_name()} · Each question: live NSE prices + fundamentals + global macro + web search")
