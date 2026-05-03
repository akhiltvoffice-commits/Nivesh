"""Settings — Gemini model selection, data sources info."""
import streamlit as st
from utils.style import inject_css, theme_toggle
from utils import ai_utils

st.set_page_config(page_title="Settings — NIVESH", page_icon="⚙️", layout="wide")
light_mode = theme_toggle()
inject_css(light_mode)
st.title("⚙️ Settings")

# ── API Key ────────────────────────────────────────────────────────────────
st.subheader("🔑 Gemini API Key")
current_key = ai_utils.get_key()
is_default  = current_key == ai_utils.DEFAULT_KEY

if is_default:
    st.success("✓ Using pre-configured API key — app works out of the box")
else:
    st.info("✓ Using your custom API key")

with st.expander("Change API Key (optional)"):
    new_key = st.text_input("Enter your Gemini API key", type="password", placeholder="AIza...")
    if st.button("Save Key"):
        st.session_state.gemini_key = new_key
        st.success("Key saved for this session")
    st.caption("Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey)")

# ── Model Selection ────────────────────────────────────────────────────────
st.divider()
st.subheader("🤖 AI Model")
st.caption("Select the Gemini model to use for all AI analysis in this app")

# Current model lineup (May 2026)
MODELS = [
    {"id": "gemini-3.1-pro-preview",     "name": "Gemini 3.1 Pro Preview",     "tier": "⭐ Latest", "note": "Most powerful · Deep reasoning · Best for analysis"},
    {"id": "gemini-2.5-pro",             "name": "Gemini 2.5 Pro",             "tier": "✅ Stable", "note": "Highly capable · Production-stable · Recommended for production"},
    {"id": "gemini-2.5-flash",           "name": "Gemini 2.5 Flash",           "tier": "⚡ Fast",   "note": "Fast & smart · Good balance of speed and quality"},
    {"id": "gemini-2.5-flash-lite",      "name": "Gemini 2.5 Flash Lite",      "tier": "💰 Budget", "note": "Cheapest · Good for quick lookups · Less depth"},
    {"id": "gemini-3.1-flash-lite-preview","name":"Gemini 3.1 Flash Lite Preview","tier":"🆕 New",  "note": "Newest lite model · Gemini 3 quality at Flash Lite speed"},
]

current_model = ai_utils.get_model_name()

# Display model cards
cols = st.columns(len(MODELS))
for i, m in enumerate(MODELS):
    is_selected = current_model == m["id"]
    border_color = "#F59E0B" if is_selected else "#1E2A3A"
    with cols[i]:
        st.markdown(f"""<div style="border:2px solid {border_color};border-radius:10px;padding:12px;text-align:center;background:#111827;min-height:130px">
            <div style="font-size:11px;color:#F59E0B;font-weight:700">{m['tier']}</div>
            <div style="font-size:13px;font-weight:700;color:#F1F5F9;margin:4px 0">{m['name']}</div>
            <div style="font-size:10px;color:#8DA4BF">{m['note']}</div>
            {'<div style="margin-top:8px;font-size:10px;color:#10D98D;font-weight:700">✓ ACTIVE</div>' if is_selected else ''}
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
col1, col2 = st.columns([3,1])
with col1:
    model_options = {m["name"]: m["id"] for m in MODELS}
    current_name = next((m["name"] for m in MODELS if m["id"]==current_model), current_model)
    selected_name = st.selectbox("Select Model", list(model_options.keys()),
                                  index=list(model_options.keys()).index(current_name) if current_name in model_options else 0,
                                  label_visibility="collapsed")
with col2:
    if st.button("Save Model", type="primary", use_container_width=True):
        st.session_state.gemini_model = model_options[selected_name]
        st.success(f"✓ Saved: {selected_name}")
        st.rerun()

# Also try to fetch live model list
with st.expander("Browse all available models from Google API"):
    if st.button("Refresh model list from Google"):
        with st.spinner("Fetching..."):
            live_models = ai_utils.list_models()
        if live_models:
            for m in live_models[:20]:
                st.text(f"{m['id']} — {m['name']}")

# ── Data Sources ───────────────────────────────────────────────────────────
st.divider()
st.subheader("📡 Data Sources")

sources = [
    ("Yahoo Finance", "NSE/BSE stocks, ETFs, indices, macro — via yfinance", "✅ Active"),
    ("NSE India",     "Real options chain — NIFTY, BANKNIFTY F&O", "✅ Active (may rate-limit)"),
    ("mfapi.in",      "6000+ Indian mutual fund NAV history — free public API", "✅ Active"),
    ("Google Gemini", f"AI analysis — model: {current_model}", "✅ Configured"),
]

for name, desc, status in sources:
    col1, col2, col3 = st.columns([2,4,2])
    col1.markdown(f"**{name}**")
    col2.caption(desc)
    col3.markdown(status)

# ── Deploy ─────────────────────────────────────────────────────────────────
st.divider()
st.subheader("🚀 Streamlit Cloud Deployment")
st.markdown("""
1. Upload `nivesh_st` folder to GitHub (browser drag-and-drop)
2. Go to **share.streamlit.io** → Create app → select your repo → `nivesh_st/app.py`
3. Secrets: `GEMINI_KEY = "AIzaSy..."`
4. Deploy → live at `https://yourname-nivesh.streamlit.app`
""")
st.divider()
st.caption("NIVESH v2.0 · Python + Streamlit + yfinance + Gemini 3.1 · Educational purposes only")
