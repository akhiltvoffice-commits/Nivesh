"""
Gemini AI utilities — google.genai SDK.
Default: gemini-3.1-pro-preview
Features: web-search grounding, auto macro research, investment levels engine.
"""
import streamlit as st
from google import genai
from google.genai import types

DEFAULT_KEY   = ""  # Add your Gemini API key to Streamlit secrets: GEMINI_KEY = "your_key_here"
DEFAULT_MODEL = "gemini-2.0-flash"  # Free tier: 1500 req/day, 1M tokens/min

def get_key() -> str:
    if st.session_state.get("gemini_key"):
        return st.session_state.gemini_key
    try:
        return st.secrets["GEMINI_KEY"]
    except Exception:
        return DEFAULT_KEY

def get_model_name() -> str:
    return st.session_state.get("gemini_model", DEFAULT_MODEL)

@st.cache_resource
def _get_cached_client(api_key: str):
    """Cached Gemini client — prevents 'client closed' errors across reruns."""
    return genai.Client(api_key=api_key)

def _client():
    """Returns a cached Gemini client instance."""
    try:
        client = _get_cached_client(get_key())
        return client
    except Exception:
        # Fallback: create fresh client if cache fails
        return genai.Client(api_key=get_key())

SYSTEM = (
    "You are Nivesh AI — elite Indian equity and macro analyst. "
    "NSE/BSE, SEBI, RBI, F&O structure, Indian sector dynamics expert. "
    "Use **bold** for key numbers. Bullet points for lists. ₹ for INR. "
    "Be specific with price levels. Never say 'may go up' — give ₹ targets."
)

# ── Core generate functions ────────────────────────────────────────────────

def generate(prompt: str, temperature: float = 0.5, max_tokens: int = 4096,
             use_search: bool = False) -> str:
    """
    Generate a response from Gemini. Handles client lifecycle issues gracefully.
    If client is closed, clears cache and retries with fresh client.
    """
    def _attempt(with_search: bool) -> str:
        config_args = dict(
            system_instruction=SYSTEM,
            temperature=temperature,
            max_output_tokens=max_tokens,
        )
        if with_search:
            config_args["tools"] = [types.Tool(google_search=types.GoogleSearch())]
        return _client().models.generate_content(
            model=get_model_name(),
            contents=prompt,
            config=types.GenerateContentConfig(**config_args),
        ).text

    # Attempt 1: with requested settings
    try:
        return _attempt(use_search)
    except Exception as e1:
        err_str = str(e1).lower()
        # If client was closed — clear cache and retry with fresh client
        if "closed" in err_str or "client" in err_str:
            try:
                _get_cached_client.clear()  # clear st.cache_resource
            except Exception:
                pass
        # Attempt 2: without search (simpler request)
        if use_search:
            try:
                return _attempt(False)
            except Exception as e2:
                err_str2 = str(e2).lower()
                if "closed" in err_str2:
                    try: _get_cached_client.clear()
                    except Exception: pass
        # Attempt 3: brand new client, no search
        try:
            client = genai.Client(api_key=get_key())
            resp = client.models.generate_content(
                model=get_model_name(), contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM, temperature=temperature,
                    max_output_tokens=max_tokens)
            )
            return resp.text
        except Exception as e3:
            return f"⚠️ Gemini unavailable: {e3}"

def generate_json(prompt: str) -> str:
    try:
        resp = _client().models.generate_content(
            model=get_model_name(), contents=prompt,
            config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=4000)
        )
        return resp.text
    except Exception:
        return "[]"

def list_models() -> list:
    try:
        models = []
        for m in _client().models.list():
            name = m.name.replace("models/","")
            if not any(x in name for x in ["embed","tts","image","video","audio","live"]):
                models.append({"id": name, "name": getattr(m,"display_name",name) or name})
        return models
    except Exception:
        return [
            {"id":"gemini-2.0-flash",              "name":"Gemini 2.0 Flash ⭐ (Free tier: 1500/day)"},
            {"id":"gemini-2.5-flash",              "name":"Gemini 2.5 Flash (Fast)"},
            {"id":"gemini-1.5-flash",              "name":"Gemini 1.5 Flash (High free quota)"},
            {"id":"gemini-2.5-pro",                "name":"Gemini 2.5 Pro (Requires billing)"},
            {"id":"gemini-3.1-pro-preview",        "name":"Gemini 3.1 Pro Preview (Requires billing)"},
        ]

def chat_response(history: list, question: str) -> str:
    try:
        contents = [
            types.Content(role=h["role"] if h["role"]=="user" else "model",
                          parts=[types.Part(text=h["content"])])
            for h in history
        ]
        contents.append(types.Content(role="user", parts=[types.Part(text=question)]))
        resp = _client().models.generate_content(
            model=get_model_name(), contents=contents,
            config=types.GenerateContentConfig(system_instruction=SYSTEM, temperature=0.5)
        )
        return resp.text
    except Exception as e:
        return f"⚠️ {e}"

# ── AUTO MACRO RESEARCH (Gemini web search — no manual input needed) ────────

@st.cache_data(ttl=1800, show_spinner=False)
def get_auto_macro_context(symbol: str = None) -> str:
    """
    Gemini auto-researches macro + company context.
    Uses web search grounding for latest data.
    No manual parameter selection needed.
    """
    today = __import__("datetime").datetime.now().strftime("%B %Y")
    company_section = f"""
7. COMPANY-SPECIFIC ({symbol}):
   - Latest quarterly results (revenue, profit, margins YoY)
   - Management guidance and analyst upgrades/downgrades
   - Recent major deals, acquisitions, partnerships
   - Regulatory issues or tailwinds
   - Institutional holding changes (FII/DII)
   - Key upcoming events (results date, AGM, product launches)
""" if symbol else ""

    prompt = f"""Research and summarise the current Indian investment environment as of {today}:

1. RBI MONETARY POLICY: Current repo rate, last decision, next meeting date, rate trajectory
2. INDIA MACRO: Latest CPI, GDP growth, fiscal deficit, current account
3. CAPITAL FLOWS: FII net flows last 30 days, DII flows, sector-wise FII activity
4. GLOBAL MACRO: US Fed stance, US 10Y yield, crude oil price and trend, USD/INR outlook
5. KEY RISKS: Top 3 risks for Indian equities right now (geopolitical, regulatory, global)
6. SECTOR SPOTLIGHTS: Which sectors have strong tailwinds and headwinds right now and WHY
{company_section}
Format as a structured research note with specific numbers. Be concise but data-rich."""

    return generate(prompt, temperature=0.2, max_tokens=1500, use_search=True)

# ── INVESTMENT LEVELS ENGINE ───────────────────────────────────────────────

def get_investment_levels(symbol: str, price: float, signals: dict,
                          info: dict, capital: float = 100000) -> str:
    """
    Generate precise entry zones, stop losses (tight/normal/wide),
    targets (T1/T2/T3/bull), and position sizing for a given capital.
    """
    atr    = signals.get("atr", price * 0.02) or price * 0.02
    sma20  = signals.get("sma20", price) or price
    sma50  = signals.get("sma50", price) or price
    sma200 = signals.get("sma200") or price
    bb_l   = signals.get("bb_lower", price * 0.97) or price * 0.97
    rsi    = signals.get("rsi", 50) or 50
    overall= signals.get("overall","Neutral")
    hi52   = info.get("fiftyTwoWeekHigh", price * 1.3)
    lo52   = info.get("fiftyTwoWeekLow",  price * 0.7)
    atgt   = info.get("targetMeanPrice")
    pe     = info.get("trailingPE","—")
    sector = info.get("sector","—")

    tight_stop  = round(price - 1.5 * atr, 2)
    normal_stop = round(price - 2.5 * atr, 2)
    wide_stop   = round(min(sma200 * 0.97, price * 0.85), 2)

    prompt = f"""Investment levels for {symbol} (₹{price:.2f}) — {sector}:

TECHNICAL DATA:
- ATR(14): ₹{atr:.2f} | RSI: {rsi:.1f} | Signal: {overall}
- SMA20: ₹{sma20:.0f} | SMA50: ₹{sma50:.0f} | SMA200: ₹{sma200:.0f}
- Bollinger Lower: ₹{bb_l:.0f} | 52W Range: ₹{lo52:.0f}–₹{hi52:.0f}
- Analyst consensus target: ₹{atgt or "—"} | P/E: {pe}
- Pre-calculated stops: Tight ₹{tight_stop} | Normal ₹{normal_stop} | Wide ₹{wide_stop}

INVESTOR CAPITAL: ₹{capital:,.0f}

Give PRECISE investment levels:

### 🎯 Entry Zones
| Type | Price | Rationale |
|------|-------|-----------|
| Aggressive (buy now) | ₹XXXX | ... |
| Ideal (wait for dip) | ₹XXXX–XXXX | ... |
| Conservative (deep value) | ₹XXXX | ... |

### 🛑 Stop Losses
| Type | Price | % Risk | For whom |
|------|-------|--------|----------|
| Tight (intraday/swing) | ₹{tight_stop} | {(price-tight_stop)/price*100:.1f}% | Traders |
| Normal (positional) | ₹{normal_stop} | {(price-normal_stop)/price*100:.1f}% | Investors |
| Wide (long-term) | ₹{wide_stop} | {(price-wide_stop)/price*100:.1f}% | Buy & hold |

### 🎯 Price Targets
| Target | Price | % Upside | Timeline | Trigger |
|--------|-------|----------|----------|---------|
| T1 (resistance) | ₹XXXX | XX% | 1–3 months | ... |
| T2 (momentum) | ₹XXXX | XX% | 3–6 months | ... |
| T3 (fair value) | ₹XXXX | XX% | 6–12 months | ... |
| T4 (bull case) | ₹XXXX | XX% | 12–24 months | ... |

### 💰 Position Sizing (₹{capital:,.0f} capital)
| Risk Level | Max Loss | Shares | Capital Used | % of Portfolio |
|------------|----------|--------|--------------|----------------|
| Conservative (1% risk) | ₹{capital*0.01:,.0f} | X | ₹XXXX | X% |
| Moderate (2% risk) | ₹{capital*0.02:,.0f} | X | ₹XXXX | X% |
| Aggressive (3% risk) | ₹{capital*0.03:,.0f} | X | ₹XXXX | X% |

Use the pre-calculated stop losses above for position sizing math.

### ⚡ Trading Notes
3 specific observations about current price action and what to watch."""

    return generate(prompt, temperature=0.3, max_tokens=1200)

# ── COMPREHENSIVE STOCK ANALYSIS ───────────────────────────────────────────

def analyse_stock_comprehensive(symbol: str, info: dict, signals: dict,
                                 macro_context: str = "",
                                 global_regime: dict = None) -> str:
    """Full research: positives, negatives, macro factors, micro factors, verdict."""
    p   = info.get("regularMarketPrice") or info.get("currentPrice") or 0
    roe = info.get("returnOnEquity")
    mg  = info.get("profitMargins")
    rg  = info.get("revenueGrowth")
    eg  = info.get("earningsGrowth")
    fcf = info.get("freeCashflow",0) or 0
    de  = info.get("debtToEquity","—")
    cr  = info.get("currentRatio","—")

    prompt = f"""Comprehensive investment research for {symbol}:

FUNDAMENTALS:
- Price: ₹{p} | Market Cap: ₹{info.get('marketCap',0)/1e7:.0f}Cr | Beta: {info.get('beta','—')}
- PE: {info.get('trailingPE','—')} | PB: {info.get('priceToBook','—')} | EPS: ₹{info.get('trailingEps','—')}
- ROE: {f"{roe*100:.1f}%" if roe else '—'} | Net Margin: {f"{mg*100:.1f}%" if mg else '—'}
- Rev Growth: {f"{rg*100:.1f}%" if rg else '—'} | EPS Growth: {f"{eg*100:.1f}%" if eg else '—'}
- D/E: {de} | Current Ratio: {cr} | FCF: ₹{fcf/1e7:.0f}Cr
- 52W: ₹{info.get('fiftyTwoWeekLow','—')}–₹{info.get('fiftyTwoWeekHigh','—')}
- Analyst Target: ₹{info.get('targetMeanPrice','—')} | Consensus: {info.get('recommendationKey','—')}

TECHNICALS:
- RSI(14): {signals.get('rsi',0):.1f if signals.get('rsi') else 'N/A'} | Signal: {signals.get('overall','N/A')}
- SMA20: ₹{signals.get('sma20',0):.0f} | SMA50: ₹{signals.get('sma50',0):.0f} | SMA200: ₹{signals.get('sma200') or 'N/A'}
- ATR: ₹{signals.get('atr',0):.2f} | BB: ₹{signals.get('bb_lower',0):.0f}–₹{signals.get('bb_upper',0):.0f}
- Stop 1.5×ATR: ₹{signals.get('stop_1x',0):.0f} | Stop 2.5×ATR: ₹{signals.get('stop_2x',0):.0f}

CURRENT MACRO/MARKET CONTEXT (auto-fetched):
{macro_context[:800] if macro_context else 'Use latest knowledge of Indian macro.'}

GLOBAL MARKET SIGNALS (live):
{f"S&P500: {global_regime.get('sp_chg',0):+.2f}% | NASDAQ: {global_regime.get('nasdaq_chg',0):+.2f}% | Nikkei: {global_regime.get('nikkei_chg',0):+.2f}% | Hang Seng: {global_regime.get('hsi_chg',0):+.2f}%" if global_regime else "Fetch latest global market data."}
{f"Gold: ${global_regime.get('gold_price',0):,.0f} | DXY: {global_regime.get('dxy_level',0):.1f} | Brent: ${global_regime.get('crude_price',0):.0f}/bbl | USD/INR: ₹{global_regime.get('inr_level',0):.2f}" if global_regime else ""}
{f"Flags: nasdaq_bull={global_regime.get('nasdaq_bull')} | dollar_strong={global_regime.get('dollar_strong')} | china_bull={global_regime.get('china_bull')} | gold_high={global_regime.get('gold_high')}" if global_regime else ""}

Write a comprehensive research report:

### 🎯 VERDICT: [STRONG BUY / BUY / ACCUMULATE / HOLD / REDUCE / AVOID]
One powerful sentence with the core thesis.

### ✅ BULL FACTORS — Why to Buy
List 5-7 specific positives with data:
- **Macro**: How current macro (rates, INR, crude, global) benefits this stock
- **Sector**: Sector tailwinds specific to company
- **Fundamental**: Key quality/growth/valuation metrics that are compelling
- **Technical**: Chart signals supporting entry
- **Micro**: Company-specific catalysts (deals, results, guidance)
- **Valuation**: Is it undervalued vs peers/history?

### ❌ BEAR FACTORS — Why Not to Buy
List 4-6 specific risks with data:
- **Macro Risk**: Macro headwinds that hurt this stock
- **Sector Risk**: Sector challenges
- **Fundamental Risk**: Weak metrics or declining trends
- **Valuation Risk**: Overvaluation concerns
- **Execution Risk**: Management/operational risks
- **Technical Risk**: Chart red flags

### 📊 SCORE BREAKDOWN (/100)
| Dimension | Score | Comment |
|-----------|-------|---------|
| Valuation | XX/25 | ... |
| Quality | XX/30 | ... |
| Growth | XX/25 | ... |
| Safety | XX/20 | ... |
| Macro Tailwind | +XX/−XX | ... |

### 🎲 PROBABILITY MATRIX
| Scenario | Probability | 12M Return | Price Target |
|----------|-------------|------------|--------------|
| Bull Case | XX% | +XX% | ₹XXXX |
| Base Case | XX% | +XX% | ₹XXXX |
| Bear Case | XX% | −XX% | ₹XXXX |
| **Expected Return** | | **+XX%** | **₹XXXX** |

### ⚡ 3 KEY CATALYSTS (next 6 months)
### 🛑 3 KEY RISKS (with magnitude)
### 🧮 HOW TO INVEST (SIP/lump sum, levels, profit booking)"""

    return generate(prompt, temperature=0.4, max_tokens=3000)

# ── BEST PICKS ENGINE ──────────────────────────────────────────────────────

def analyse_best_picks(candidates_df, category: str, macro_regime: dict = None) -> str:
    rows = []
    for _, r in candidates_df.head(15).iterrows():
        pe_s  = f"{r['PE']:.1f}"            if r.get('PE')  else "—"
        roe_s = f"{r['ROE']*100:.0f}%"      if r.get('ROE') else "—"
        mg_s  = f"{r['Net Margin']*100:.0f}%" if r.get('Net Margin') else "—"
        rg_s  = f"{r['Rev Growth']*100:.0f}%" if r.get('Rev Growth') else "—"
        eg_s  = f"{r['EPS Growth']*100:.0f}%" if r.get('EPS Growth') else "—"
        de_s  = f"{r['D/E']:.0f}"            if r.get('D/E') is not None else "—"
        ms_s  = f"{r.get('Macro Score',0):+.0f}"
        au_s  = f"{r.get('Analyst Upside%',0):+.1f}%" if r.get('Analyst Upside%') else "—"
        rows.append(
            f"{r['Symbol']}|{r.get('Sector','?')}|₹{r['Price']:.0f}"
            f"|Score:{r['Score']:.0f}|Macro:{ms_s}|PE:{pe_s}|ROE:{roe_s}"
            f"|Margin:{mg_s}|RevGrowth:{rg_s}|EPSGrowth:{eg_s}|D/E:{de_s}"
            f"|Tech:{r.get('Tech','?')}|AnalystUpside:{au_s}|{r.get('Reasons','')}"
        )

    macro_ctx = ""
    if macro_regime:
        macro_ctx = (
            f"\nLIVE MACRO SNAPSHOT: Crude=${macro_regime.get('crude_price',80):.0f} | "
            f"VIX={macro_regime.get('vix_level',15):.1f} | USD/INR=₹{macro_regime.get('inr_level',84):.2f} | "
            f"Nifty {macro_regime.get('nifty_chg',0):+.2f}% | US S&P {macro_regime.get('sp_chg',0):+.2f}% | "
            f"US10Y={macro_regime.get('us10y',6.5):.2f}%\n"
            f"Active regime: {', '.join(k for k,v in macro_regime.items() if v is True and isinstance(v,bool))}"
        )

    prompt = f"""You are an elite Indian equity fund manager. Category: {category}
{macro_ctx}

Top 15 scored stocks from 545-stock NSE universe (Score includes live macro adjustment):
{chr(10).join(rows)}

Pick the BEST 5 investment opportunities RIGHT NOW.
Consider: risk-reward at current price, macro tailwinds, technical momentum, sector diversification.
Max 2 from same sector.

Return ONLY a JSON array, no markdown:
[{{
  "symbol": "SYMBOL",
  "name": "Company Name",
  "price": 1234,
  "sector": "Sector",
  "category": "Value/Growth/Quality/Momentum/Turnaround",
  "conviction": "High/Medium",
  "thesis": "2-3 sentences with specific numbers",
  "entryZone": "₹XXXX–XXXX",
  "target3m": "₹XXXX",
  "target6m": "₹XXXX",
  "target12m": "₹XXXX",
  "target24m": "₹XXXX",
  "target36m": "₹XXXX",
  "stopLoss": "₹XXXX",
  "riskReward": "1:X.X",
  "positionSize": "X–X%",
  "bullProb": 60,
  "baseProb": 25,
  "bearProb": 15,
  "bullReturn12m": 35.5,
  "baseReturn12m": 15.0,
  "bearReturn12m": -12.0,
  "expectedReturn12m": 22.3,
  "catalysts": ["catalyst1","catalyst2","catalyst3"],
  "risks": ["risk1","risk2"],
  "bullCase": "Specific bull scenario with ₹ target and trigger",
  "bearCase": "Specific bear scenario with downside and trigger",
  "verdict": "One actionable sentence"
}}]"""

    # First attempt with full prompt
    result = generate_json(prompt)

    # Validate it's parseable JSON with expected structure
    import json as _json, re as _re
    try:
        clean = _re.sub(r"```json|```","", result).strip()
        s = clean.find("["); e = clean.rfind("]")+1
        if s != -1 and e > s:
            parsed = _json.loads(clean[s:e])
            if parsed and isinstance(parsed, list) and parsed[0].get("symbol"):
                return result  # Good JSON
    except Exception:
        pass

    # Retry with simpler, more constrained prompt
    simple_prompt = (
        f"Pick 5 Indian stocks from this list as best investments right now. "
        f"Category: {category}.\n\nCandidates:\n" +
        "\n".join(rows[:10]) +
        "\n\nReturn ONLY a JSON array of 5 objects with keys: "
        'symbol, name, price, sector, conviction, thesis, entryZone, '
        'target12m, upside, stopLoss, riskReward, positionSize, '
        'bullProb, baseProb, bearProb, bullReturn12m, baseReturn12m, bearReturn12m, '
        'expectedReturn12m, catalysts, risks, bullCase, bearCase, verdict, '
        'target3m, target6m, target24m, target36m, category. No other text.'
    )
    return generate_json(simple_prompt)

# ── OTHER FUNCTIONS ────────────────────────────────────────────────────────

def analyse_macro(macro_data: dict) -> str:
    prompt = f"""INDIA MACRO:
Repo: {macro_data.get('repo_rate','6.5')}% | CPI: {macro_data.get('cpi','4.6')}% | GDP: {macro_data.get('gdp','7.2')}%
USD/INR: ₹{macro_data.get('usdinr','84.5')} | Brent: ${macro_data.get('crude','75')}/bbl
VIX: {macro_data.get('vix','13.5')} | 10Y G-Sec: {macro_data.get('gsec','6.85')}%

1. **Macro Regime** — name and describe
2. **Sector Signals** — explicit overweight/underweight with reasoning
3. **Portfolio Positioning** — specific allocation guidance
4. **Top 3 Risks** — with magnitude and hedge idea
5. **Scenarios** — Bull/Base/Bear for Nifty 12M with probability % and Nifty level"""
    return generate(prompt, temperature=0.4)

def analyse_portfolio(holdings: list, risk_profile: dict) -> str:
    h_str = "\n".join([f"- {h['name']}: ₹{h['value']:,.0f} ({h['weight']:.1f}%, {h['type']})" for h in holdings])
    prompt = f"""PORTFOLIO ANALYSIS:
Risk: Max DD {risk_profile['max_dd']}% | Horizon {risk_profile['horizon']}Y | Target {risk_profile['target']}% CAGR
Capital: ₹{risk_profile['capital']:,.0f}
{h_str}

1. Concentration risk — any >25% position?
2. Asset allocation gaps
3. Specific rebalancing with ₹ amounts
4. Expected return range and drawdown probability
5. What to add/trim now"""
    return generate(prompt, temperature=0.4)

def market_briefing() -> str:
    from datetime import datetime
    today = datetime.now().strftime("%A, %d %B %Y")
    prompt = f"""Indian equity markets morning briefing — {today}:
1. **Nifty & Sensex** — direction, key levels
2. **Sector Movers** — 2 best, 2 worst with reasons
3. **Stock Moves** — 3-4 stocks with reasons
4. **Global Cues** — US, crude, USD/INR
5. **Week Ahead** — RBI, earnings, events
Max 350 words. Specific ₹ and % levels."""
    return generate(prompt, temperature=0.2, use_search=True)

def analyse_stock(info: dict, signals: dict, extra_context: str = "") -> str:
    """Legacy single-function analysis — used by Screener/Watchlist."""
    p   = info.get("regularMarketPrice") or info.get("currentPrice") or 0
    roe = info.get("returnOnEquity")
    mg  = info.get("profitMargins")
    rg  = info.get("revenueGrowth")
    eg  = info.get("earningsGrowth")
    fcf = info.get("freeCashflow",0) or 0

    prompt = f"""Research report for {info.get('longName','N/A')} ({info.get('symbol','')}):
Sector: {info.get('sector','N/A')} | Market Cap: ₹{info.get('marketCap',0)/1e7:.0f}Cr | Beta: {info.get('beta','—')}
Price: ₹{p} | PE: {info.get('trailingPE','—')} | PB: {info.get('priceToBook','—')}
ROE: {f"{roe*100:.1f}%" if roe else '—'} | Margin: {f"{mg*100:.1f}%" if mg else '—'}
Rev Growth: {f"{rg*100:.1f}%" if rg else '—'} | EPS Growth: {f"{eg*100:.1f}%" if eg else '—'}
D/E: {info.get('debtToEquity','—')} | FCF: ₹{fcf/1e7:.0f}Cr
RSI: {signals.get('rsi',0):.1f if signals.get('rsi') else 'N/A'} | Signal: {signals.get('overall','N/A')}
Stop 1.5×ATR: ₹{signals.get('stop_1x',0):.0f if signals.get('stop_1x') else 'N/A'}
Stop 2.5×ATR: ₹{signals.get('stop_2x',0):.0f if signals.get('stop_2x') else 'N/A'}
Analyst Target: ₹{info.get('targetMeanPrice','—')} | Consensus: {info.get('recommendationKey','—')}
{extra_context}

### 🎯 Verdict | ### 🏢 Business Quality | ### 💰 Valuation | ### 📈 Technical Setup
### 🎲 Risk-Reward (Entry Zone, Target 12M, Stop Loss, Position Size, R:R)
### 🐂 Bull Case (prob%) | ### 🐻 Bear Case (prob%) | ### ⚡ 3 Catalysts | ### 🛑 3 Risks | ### 🧮 How to Invest"""
    return generate(prompt, temperature=0.4, max_tokens=2500)

def auto_research_stock(symbol: str, current_price: float = 0) -> dict:
    """
    Cache key adapts to market session:
    - Market hours (9:15–15:30 IST weekdays): refreshes every 15 minutes
    - Outside market hours: refreshes once per day
    This ensures research stays current during volatile sessions.
    """
    from datetime import datetime
    now = datetime.now()
    mins = now.hour * 60 + now.minute
    is_market = (9*60+15 <= mins <= 15*60+30) and now.weekday() < 5

    if is_market:
        # 5-minute intervals: slot changes every 5 min during market hours
        slot = mins // 5
        cache_key = f"{now.strftime('%Y%m%d')}_{slot}"
    else:
        # Outside market: once per day is enough
        cache_key = now.strftime("%Y%m%d")

    return _auto_research_cached(symbol, cache_key)

@st.cache_data(ttl=300, show_spinner=False)  # 5-min TTL; cache_key controls refresh frequency
def _auto_research_cached(symbol: str, cache_key: str) -> dict:
    """
    ALWAYS-ON deep research — runs automatically every time a stock is viewed.
    Covers: recent results, news, macro impact, geopolitical, FII, analysts.
    Uses Gemini web search grounding for latest data.
    Returns structured dict for the research_card() UI component.
    """
    from datetime import datetime
    today = datetime.now().strftime("%B %d, %Y")

    prompt = f"""You are a senior equity research analyst. Research {symbol} (NSE-listed Indian stock) as of {today}.
Fetch the current live price yourself.

MANDATORY: Use web search to find the LATEST information. Do NOT rely on training data alone.

Find and include ALL of the following:
1. LATEST QUARTERLY RESULTS — Most recent Q (revenue, net profit, margins vs est. and YoY). Beat/miss? Management commentary?
2. SIGNIFICANT RECENT EVENTS (last 60 days) — M&A, management changes, large orders, regulatory approvals/issues, fundraising, debt restructuring
3. UPCOMING CORPORATE EVENTS — Next results date + consensus EPS/revenue estimates, upcoming AGM, dividend ex-date, bonus/split announced, rights issue, QIP/FPO planned
4. MACRO TAILWINDS/HEADWINDS — How do current RBI rates, USD/INR, crude oil, NASDAQ direction, DXY (dollar index), Hang Seng (China demand) specifically impact this company?
5. GEOPOLITICAL/GLOBAL — Wars, trade tensions, export restrictions, US tariffs, China slowdown, supply chain shifts that affect this company specifically
6. FII/DII ACTIVITY — FII buying or selling? Promoter buying/pledging? Mutual fund accumulation or distribution?
7. ANALYST ACTIVITY — Upgrades/downgrades + target price changes in last 30 days. Which brokers changed view and why?
8. SECTOR HEALTH & COMPETITION — Is sector growing or contracting? Any new entrant, disruption, pricing pressure, regulatory change?
9. TECHNICAL SETUP — Is price at key support/resistance? 52W high/low proximity? Volume trend?
10. VERDICT — BUY/ACCUMULATE/HOLD/REDUCE/AVOID with 3 price targets and investment horizon recommendation

Return ONLY a JSON object with these exact keys:
{{
  "verdict": "STRONG BUY / BUY / ACCUMULATE / HOLD / REDUCE / AVOID",
  "verdict_reason": "One compelling sentence why",
  "current_price_context": "Cheap/fair/expensive vs history and peers",
  "recent_events": ["brief event 1 with impact", "brief event 2", "brief event 3"],
  "latest_results": "Q_FY__ revenue ₹XXCr (+/-XX% YoY), PAT ₹XXCr, margin XX%",
  "next_results": "Expected in Month YYYY, consensus EPS ₹XX",
  "macro_impact": "Specific macro factors helping or hurting this stock right now",
  "geo_political": "Any global/geopolitical factor affecting this company specifically",
  "fii_activity": "Buying/selling trend with approximate magnitude",
  "analyst_changes": "Recent upgrades/downgrades and target changes",
  "key_catalysts": ["catalyst 1", "catalyst 2", "catalyst 3"],
  "key_risks": ["risk 1", "risk 2", "risk 3"],
  "price_target_low": 0,
  "price_target_base": 0,
  "price_target_high": 0,
  "time_horizon": "12 months"
}}"""

    try:
        import streamlit as st
        raw = generate_json(prompt)
        # Also try with search
        raw_search = generate(prompt + "\n\nIMPORTANT: Return ONLY valid JSON.",
                              temperature=0.1, max_tokens=2000, use_search=True)

        import json, re
        for raw_try in [raw_search, raw]:
            try:
                clean = re.sub(r"```json|```","", raw_try).strip()
                s = clean.find("{"); e = clean.rfind("}")+1
                if s != -1 and e > s:
                    data = json.loads(clean[s:e])
                    # Validate
                    if data.get("verdict") and data.get("verdict_reason"):
                        return data
            except Exception:
                continue
    except Exception as e:
        pass

    return {
        "verdict": "RESEARCH UNAVAILABLE",
        "verdict_reason": "Could not fetch real-time research. Check API key or retry.",
        "recent_events": [], "key_catalysts": [], "key_risks": [],
        "latest_results": "", "next_results": "", "macro_impact": "",
        "geo_political": "", "fii_activity": "", "analyst_changes": "",
        "price_target_low": 0, "price_target_base": 0, "price_target_high": 0,
    }
