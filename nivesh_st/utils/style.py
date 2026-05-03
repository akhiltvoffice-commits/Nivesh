"""
NIVESH — Global CSS. Injected into every page via inject_css().
Minimalist dark theme. Single gold accent. Clean typography.
"""
import streamlit as st

NIVESH_CSS = """
<style>
/* ── Reset & base ─────────────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #09090B; }
[data-testid="stSidebar"]          { background: #111113 !important; border-right: 1px solid #27272A; }
[data-testid="stHeader"]           { background: transparent; }
footer                             { display: none !important; }
#MainMenu                          { display: none; }

/* ── Typography ────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #FAFAFA;
}

/* ── Metric cards ──────────────────────────────────────────────────────── */
div[data-testid="metric-container"] {
  background: #111113 !important;
  border: 1px solid #27272A !important;
  border-radius: 8px !important;
  padding: 14px 16px !important;
}
div[data-testid="metric-container"] label {
  color: #71717A !important;
  font-size: 11px !important;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 20px !important;
  font-weight: 700 !important;
  color: #FAFAFA !important;
}
div[data-testid="metric-container"] [data-testid="stMetricDelta"] {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px !important;
}

/* ── Buttons ────────────────────────────────────────────────────────────── */
button[kind="primary"] {
  background: #F59E0B !important;
  color: #09090B !important;
  border: none !important;
  border-radius: 6px !important;
  font-weight: 600 !important;
  font-size: 13px !important;
  padding: 8px 16px !important;
}
button[kind="primary"]:hover { background: #D97706 !important; }
button[kind="secondary"] {
  background: transparent !important;
  border: 1px solid #27272A !important;
  color: #A1A1AA !important;
  border-radius: 6px !important;
}
button[kind="secondary"]:hover { border-color: #F59E0B !important; color: #F59E0B !important; }

/* ── DataFrames ─────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
  border: 1px solid #27272A;
  border-radius: 8px;
  overflow: hidden;
}
[data-testid="stDataFrame"] table { background: #111113; }
[data-testid="stDataFrame"] thead tr { background: #1A1A1D !important; }
[data-testid="stDataFrame"] thead th {
  color: #A1A1AA !important;
  font-size: 11px !important;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  border-bottom: 1px solid #27272A !important;
}
[data-testid="stDataFrame"] tbody tr:hover { background: #1A1A1D !important; }
[data-testid="stDataFrame"] tbody td {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px !important;
  color: #FAFAFA !important;
}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] {
  background: transparent;
  border-bottom: 1px solid #27272A;
  gap: 0;
}
[data-testid="stTabs"] button[role="tab"] {
  color: #71717A !important;
  font-size: 13px !important;
  font-weight: 500;
  padding: 10px 20px !important;
  border-radius: 0 !important;
  border: none !important;
  background: transparent !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
  color: #F59E0B !important;
  border-bottom: 2px solid #F59E0B !important;
  font-weight: 600 !important;
}

/* ── Inputs ─────────────────────────────────────────────────────────────── */
[data-testid="textInput"] input, [data-testid="stSelectbox"] > div, textarea {
  background: #111113 !important;
  border: 1px solid #27272A !important;
  border-radius: 6px !important;
  color: #FAFAFA !important;
  font-size: 13px !important;
}
[data-testid="textInput"] input:focus { border-color: #F59E0B !important; }

/* ── Expanders ──────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
  background: #111113;
  border: 1px solid #27272A !important;
  border-radius: 8px !important;
  margin-bottom: 8px;
}
[data-testid="stExpander"] summary {
  color: #A1A1AA !important;
  font-size: 13px !important;
}

/* ── Info / Warning / Error boxes ─────────────────────────────────────── */
[data-testid="stAlert"][class*="info"]    { background: #1A1A1D; border-left: 3px solid #3B82F6; border-radius: 0 6px 6px 0; }
[data-testid="stAlert"][class*="success"] { background: #0D1F14; border-left: 3px solid #22C55E; border-radius: 0 6px 6px 0; }
[data-testid="stAlert"][class*="warning"] { background: #1C1609; border-left: 3px solid #F59E0B; border-radius: 0 6px 6px 0; }
[data-testid="stAlert"][class*="error"]   { background: #1C0909; border-left: 3px solid #EF4444; border-radius: 0 6px 6px 0; }

/* ── Dividers ───────────────────────────────────────────────────────────── */
hr { border-color: #27272A !important; margin: 20px 0 !important; }

/* ── Sidebar links ──────────────────────────────────────────────────────── */
[data-testid="stSidebarNavLink"] {
  border-radius: 6px;
  margin: 1px 8px;
  color: #A1A1AA !important;
  font-size: 13px;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: #F59E0B18 !important;
  color: #F59E0B !important;
  font-weight: 600 !important;
}

/* ── Custom components ─────────────────────────────────────────────────── */
.nv-price-hero {
  font-family: 'JetBrains Mono', monospace;
  font-size: 40px;
  font-weight: 800;
  color: #FAFAFA;
  line-height: 1;
}
.nv-change-pos { color: #22C55E; font-family: monospace; font-weight: 600; }
.nv-change-neg { color: #EF4444; font-family: monospace; font-weight: 600; }
.nv-label { color: #71717A; font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; }
.nv-card {
  background: #111113;
  border: 1px solid #27272A;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 12px;
}
.nv-card-gold { border-left: 3px solid #F59E0B; }
.nv-card-green { border-left: 3px solid #22C55E; }
.nv-card-red   { border-left: 3px solid #EF4444; }
.nv-verdict-buy      { color: #22C55E; font-weight: 700; font-size: 18px; }
.nv-verdict-hold     { color: #F59E0B; font-weight: 700; font-size: 18px; }
.nv-verdict-sell     { color: #EF4444; font-weight: 700; font-size: 18px; }
.nv-event-pill {
  display: inline-block;
  background: #1A1A1D;
  border: 1px solid #27272A;
  border-radius: 20px;
  padding: 4px 12px;
  font-size: 12px;
  color: #A1A1AA;
  margin: 3px;
}
.nv-section-label {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: #71717A;
  margin-bottom: 8px;
}
.nv-divider { border-top: 1px solid #27272A; margin: 16px 0; }
.nv-mono { font-family: 'JetBrains Mono', monospace; }
.nv-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}
.nv-badge-gold  { background: #F59E0B18; color: #F59E0B; border: 1px solid #F59E0B33; }
.nv-badge-green { background: #22C55E18; color: #22C55E; border: 1px solid #22C55E33; }
.nv-badge-red   { background: #EF444418; color: #EF4444; border: 1px solid #EF444433; }
.nv-badge-blue  { background: #3B82F618; color: #3B82F6; border: 1px solid #3B82F633; }
.nv-badge-grey  { background: #27272A;   color: #A1A1AA; border: 1px solid #3F3F46;   }
</style>
"""


LIGHT_CSS = """
<style>
/* ── Light Mode Overrides ─────────────────────────────────────────────── */
[data-testid="stAppViewContainer"] { background: #F8FAFC !important; }
[data-testid="stSidebar"]          { background: #F1F5F9 !important; border-right: 1px solid #CBD5E1 !important; }
html, body, [class*="css"]         { color: #0F172A !important; }

div[data-testid="metric-container"] {
  background: #FFFFFF !important;
  border: 1px solid #CBD5E1 !important;
}
div[data-testid="metric-container"] label {
  color: #475569 !important;
}
div[data-testid="metric-container"] [data-testid="stMetricValue"] {
  color: #0F172A !important;
}

button[kind="primary"] {
  background: #F59E0B !important; color: #0F172A !important;
}
button[kind="secondary"] {
  background: #FFFFFF !important; border: 1px solid #CBD5E1 !important; color: #334155 !important;
}

[data-testid="stDataFrame"] { border: 1px solid #CBD5E1; }
[data-testid="stDataFrame"] table { background: #FFFFFF !important; }
[data-testid="stDataFrame"] thead tr { background: #F1F5F9 !important; }
[data-testid="stDataFrame"] thead th { color: #475569 !important; }
[data-testid="stDataFrame"] tbody tr:hover { background: #F8FAFC !important; }
[data-testid="stDataFrame"] tbody td { color: #0F172A !important; }

[data-testid="stTabs"] [role="tablist"] { border-bottom: 1px solid #CBD5E1; }
[data-testid="stTabs"] button[role="tab"] { color: #475569 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #F59E0B !important; border-bottom: 2px solid #F59E0B !important; }

[data-testid="textInput"] input, [data-testid="stSelectbox"] > div, textarea {
  background: #FFFFFF !important; border: 1px solid #CBD5E1 !important; color: #0F172A !important;
}

[data-testid="stExpander"] { background: #FFFFFF; border: 1px solid #CBD5E1 !important; }
[data-testid="stExpander"] summary { color: #334155 !important; }

[data-testid="stAlert"][class*="info"]    { background: #EFF6FF; border-left: 3px solid #3B82F6; }
[data-testid="stAlert"][class*="success"] { background: #F0FDF4; border-left: 3px solid #22C55E; }
[data-testid="stAlert"][class*="warning"] { background: #FFFBEB; border-left: 3px solid #F59E0B; }
[data-testid="stAlert"][class*="error"]   { background: #FEF2F2; border-left: 3px solid #EF4444; }

hr { border-color: #CBD5E1 !important; }
[data-testid="stSidebarNavLink"] { color: #475569 !important; }
[data-testid="stSidebarNavLink"][aria-current="page"] {
  background: #FEF3C718 !important; color: #D97706 !important;
}

.nv-card     { background: #FFFFFF !important; border-color: #CBD5E1 !important; color: #0F172A !important; }
.nv-label    { color: #475569 !important; }
.nv-mono     { color: #0F172A !important; }
.nv-price-hero { color: #0F172A !important; }
.nv-event-pill { background: #F1F5F9 !important; border-color: #CBD5E1 !important; color: #334155 !important; }
.nv-section-label { color: #475569 !important; }
.nv-divider  { border-top-color: #CBD5E1 !important; }

/* Override hardcoded dark colours in HTML components */
div[style*="background:#111827"], div[style*="background:#0D111C"],
div[style*="background:#111113"], div[style*="background:#1A1A1D"],
div[style*="background:#09090B"] {
  background: #FFFFFF !important;
}
div[style*="color:#FAFAFA"], div[style*="color:#F1F5F9"],
div[style*="color:#CBD5E1"]   { color: #0F172A !important; }
div[style*="color:#8DA4BF"], div[style*="color:#A1A1AA"],
div[style*="color:#71717A"], div[style*="color:#64748B"] { color: #475569 !important; }
.nv-tt { background: #FFFFFF !important; color: #334155 !important; border-color: rgba(245,158,11,0.5) !important; }
div[style*="color:#3F3F46"]   { color: #94A3B8 !important; }

/* ── Hover Tooltips with × close button ─────────────────────────────────── */
.nv-hw {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    cursor: default;
}
.nv-tt {
    display: none;
    position: absolute;
    top: calc(100% + 10px);
    left: 0;
    min-width: 280px;
    max-width: 360px;
    background: #1A1A2E;
    border: 1px solid rgba(245,158,11,0.45);
    border-radius: 10px;
    padding: 14px 36px 14px 14px;
    z-index: 9999;
    font-size: 13px;
    color: #CBD5E1;
    line-height: 1.6;
    box-shadow: 0 8px 30px rgba(0,0,0,0.6);
    pointer-events: auto;
}
.nv-hw:hover .nv-tt:not(.nv-closed) { display: block; }
.nv-tt strong { color: #F59E0B; }
.nv-tt .nv-tt-tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    margin-bottom: 6px;
}
.nv-tt .past  { background: #1E293B; color: #94A3B8; }
.nv-tt .curr  { background: #1E3A2E; color: #4ADE80; }
.nv-tt .fwd   { background: #2D1B3D; color: #C084FC; }
.nv-tt-x {
    position: absolute;
    top: 8px; right: 10px;
    font-size: 17px; font-weight: 700;
    color: #475569; cursor: pointer;
    line-height: 1; padding: 2px 4px;
    border-radius: 3px;
}
.nv-tt-x:hover { color: #F59E0B; background: rgba(245,158,11,0.1); }
.nv-info-dot {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 15px; height: 15px;
    border-radius: 50%;
    background: rgba(245,158,11,0.15);
    color: #F59E0B;
    font-size: 9px;
    font-weight: 800;
    flex-shrink: 0;
    cursor: help;
}
/* Light mode tooltip override */
.light-mode .nv-tt {
    background: #FFFFFF;
    border-color: rgba(245,158,11,0.5);
    color: #334155;
    box-shadow: 0 8px 30px rgba(0,0,0,0.15);
}

</style>
"""


def inject_css(light_mode: bool = False):
    """Inject NIVESH global styles. Call after set_page_config. Supports dark/light mode."""
    import streamlit as st
    st.markdown(LIGHT_CSS if light_mode else NIVESH_CSS, unsafe_allow_html=True)

def theme_toggle():
    """Renders dark/light mode toggle in sidebar. Returns current mode."""
    import streamlit as st
    if "light_mode" not in st.session_state:
        st.session_state.light_mode = False
    with st.sidebar:
        st.divider()
        col1, col2 = st.columns([1,3])
        with col1:
            icon = "☀️" if st.session_state.light_mode else "🌙"
            st.markdown(f"<div style='font-size:20px;padding-top:6px'>{icon}</div>", unsafe_allow_html=True)
        with col2:
            st.session_state.light_mode = st.toggle(
                "Light Mode", value=st.session_state.light_mode,
                help="Switch between dark and light theme"
            )
    return st.session_state.light_mode


def price_hero(symbol: str, name: str, price: float, change: float, pct: float,
               sector: str = "", market_cap: str = "", source: str = ""):
    """Large price display component."""
    up    = change >= 0
    ccolor= "#22C55E" if up else "#EF4444"
    arrow = "▲" if up else "▼"
    src_html = f'<span class="nv-badge nv-badge-green">● {source}</span>' if "NSE" in source else \
               f'<span class="nv-badge nv-badge-gold">◔ {source}</span>' if source else ""
    meta  = "  ·  ".join(filter(None, [sector, market_cap]))
    st.markdown(f"""<div style="padding:4px 0 20px 0">
      <div class="nv-label">{symbol}</div>
      <div style="display:flex;align-items:baseline;gap:16px;margin:6px 0">
        <div class="nv-price-hero">₹{price:,.2f}</div>
        <div style="color:{ccolor};font-family:monospace;font-size:20px;font-weight:600">
          {arrow} {abs(change):,.2f} ({abs(pct):.2f}%)
        </div>
        {src_html}
      </div>
      <div style="color:#71717A;font-size:13px">{name} {"· " + meta if meta else ""}</div>
    </div>""", unsafe_allow_html=True)

def research_card(research: dict):
    """Display auto-research results as a clean card."""
    verdict = research.get("verdict","HOLD").upper()
    verdict_reason = research.get("verdict_reason","")
    vcolor  = "#22C55E" if verdict in ["BUY","STRONG BUY"] else \
              "#EF4444" if verdict in ["SELL","REDUCE","AVOID"] else "#F59E0B"
    vtag    = "nv-verdict-buy" if "BUY" in verdict else \
              "nv-verdict-sell" if verdict in ["SELL","REDUCE","AVOID"] else "nv-verdict-hold"

    events  = research.get("recent_events", [])
    catalysts = research.get("key_catalysts", [])
    risks   = research.get("key_risks", [])
    macro   = research.get("macro_impact","")
    results = research.get("latest_results","")
    next_r  = research.get("next_results","")
    fii     = research.get("fii_activity","")
    analyst = research.get("analyst_changes","")
    geo     = research.get("geo_political","")
    tgt_low = research.get("price_target_low")
    tgt_base= research.get("price_target_base")
    tgt_hi  = research.get("price_target_high")

    # Verdict row
    st.markdown(f"""<div class="nv-card nv-card-{'gold' if 'HOLD' in verdict else 'green' if 'BUY' in verdict else 'red'}">
      <div style="display:flex;justify-content:space-between;align-items:start">
        <div>
          <div class="{vtag}">{verdict}</div>
          <div style="color:#A1A1AA;font-size:13px;margin-top:4px">{verdict_reason}</div>
        </div>
        {f'<div style="text-align:right"><div class="nv-label">12M Targets</div><div class="nv-mono" style="color:#22C55E;font-size:15px">₹{tgt_low:,.0f} – ₹{tgt_base:,.0f} – ₹{tgt_hi:,.0f}</div></div>' if tgt_base else ''}
      </div>
    </div>""", unsafe_allow_html=True)

    # Events row
    if events:
        pills = " ".join(f'<span class="nv-event-pill">{e}</span>' for e in events[:4])
        st.markdown(f"""<div style="margin-bottom:12px">
          <div class="nv-label" style="margin-bottom:6px">Recent Events</div>
          {pills}
        </div>""", unsafe_allow_html=True)

    # Data grid
    cols = st.columns(3)
    if results:
        with cols[0]:
            st.markdown(f'<div class="nv-label">Latest Results</div><div style="font-size:13px;color:#FAFAFA">{results}</div>', unsafe_allow_html=True)
    if next_r:
        with cols[1]:
            st.markdown(f'<div class="nv-label">Next Results</div><div style="font-size:13px;color:#FAFAFA">{next_r}</div>', unsafe_allow_html=True)
    if fii:
        with cols[2]:
            st.markdown(f'<div class="nv-label">FII Activity</div><div style="font-size:13px;color:#FAFAFA">{fii}</div>', unsafe_allow_html=True)

    if macro or geo:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        cols2 = st.columns(2)
        if macro:
            with cols2[0]:
                st.markdown(f'<div class="nv-label">Macro Impact</div><div style="font-size:12px;color:#A1A1AA">{macro}</div>', unsafe_allow_html=True)
        if geo:
            with cols2[1]:
                st.markdown(f'<div class="nv-label">Geopolitical / Global</div><div style="font-size:12px;color:#A1A1AA">{geo}</div>', unsafe_allow_html=True)

    # Catalysts + Risks
    if catalysts or risks:
        st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
        cols3 = st.columns(2)
        with cols3[0]:
            st.markdown('<div class="nv-label">Catalysts</div>', unsafe_allow_html=True)
            for cat in catalysts[:3]:
                st.markdown(f'<div style="font-size:12px;color:#22C55E;margin:2px 0">→ {cat}</div>', unsafe_allow_html=True)
        with cols3[1]:
            st.markdown('<div class="nv-label">Key Risks</div>', unsafe_allow_html=True)
            for r in risks[:3]:
                st.markdown(f'<div style="font-size:12px;color:#EF4444;margin:2px 0">⚠ {r}</div>', unsafe_allow_html=True)

    if analyst:
        st.markdown(f'<div style="margin-top:8px"><span class="nv-badge nv-badge-blue">Analyst</span> <span style="font-size:12px;color:#A1A1AA">{analyst}</span></div>', unsafe_allow_html=True)

def stat_row(items: list):
    """
    items: list of (label, value, help_text)
    Renders a clean horizontal stat row.
    """
    cols = st.columns(len(items))
    for i, (label, value, tip) in enumerate(items):
        with cols[i]:
            st.markdown(f"""<div style="padding:8px 0">
              <div class="nv-label">{label}</div>
              <div class="nv-mono" style="font-size:15px;font-weight:700;color:#FAFAFA;margin-top:3px">{value}</div>
            </div>""", unsafe_allow_html=True)

def hover_section(title: str, explanation: str,
                  tag: str = "", tag_type: str = "curr",
                  size: str = "16px", weight: str = "600") -> str:
    """
    Renders a section header with always-visible info caption below.
    No hover needed — info shown as a subtle caption under the title.
    """
    tag_colors = {"past": "#94A3B8", "curr": "#4ADE80", "fwd": "#C084FC"}
    tag_bg     = {"past": "#1E293B", "curr": "#1E3A2E", "fwd": "#2D1B3D"}
    tc = tag_colors.get(tag_type, "#94A3B8")
    tb = tag_bg.get(tag_type, "#1E293B")
    tag_html = f'<span style="background:{tb};color:{tc};font-size:10px;font-weight:700;padding:2px 7px;border-radius:4px;margin-left:8px">{tag}</span>' if tag else ''
    return f"""<div style="margin:4px 0 2px 0">
  <span style="font-size:{size};font-weight:{weight};color:#FAFAFA">{title}</span>{tag_html}
  <div style="font-size:12px;color:#71717A;margin-top:4px;line-height:1.5;padding-left:2px">{explanation}</div>
</div>"""


def metric_tip(label: str, explanation: str, tag: str = "", tag_type: str = "curr") -> str:
    """Compact hover tooltip for metric labels (smaller size)."""
    return hover_section(label, explanation, tag, tag_type, size="11px", weight="700")

