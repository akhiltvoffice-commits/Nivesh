"""Plotly chart builders for NIVESH."""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

BG  = "#0D111C"
BG2 = "#111827"
UP  = "#10D98D"
DN  = "#FF4757"
SA  = "#F59E0B"
SK  = "#38BDF8"
MU  = "#8DA4BF"
PU  = "#A78BFA"

LAYOUT = dict(
    plot_bgcolor=BG, paper_bgcolor=BG,
    font=dict(color=MU, family="JetBrains Mono, monospace", size=11),
    margin=dict(l=0, r=0, t=30, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor=BG2),
    xaxis=dict(gridcolor="#1E2A3A", gridwidth=0.5, zeroline=False),
    yaxis=dict(gridcolor="#1E2A3A", gridwidth=0.5, zeroline=False),
)

def candlestick_chart(df: pd.DataFrame, symbol: str, signals: dict = None, height: int = 500):
    """Full OHLCV candlestick chart with volume, SMA, BB overlays."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df["Open"], high=df["High"],
        low=df["Low"], close=df["Close"],
        increasing_line_color=UP, decreasing_line_color=DN,
        increasing_fillcolor=UP, decreasing_fillcolor=DN,
        name=symbol, showlegend=False,
    ), row=1, col=1)

    # Overlays from signals
    if signals:
        sma = signals.get("sma_series", {})
        if "20" in sma:
            fig.add_trace(go.Scatter(x=df.index, y=sma["20"], name="SMA 20",
                line=dict(color=SA, width=1), opacity=0.9, showlegend=True), row=1, col=1)
        if "50" in sma:
            fig.add_trace(go.Scatter(x=df.index, y=sma["50"], name="SMA 50",
                line=dict(color=SK, width=1), opacity=0.9, showlegend=True), row=1, col=1)
        if "200" in sma:
            fig.add_trace(go.Scatter(x=df.index, y=sma["200"], name="SMA 200",
                line=dict(color=PU, width=1), opacity=0.9, showlegend=True), row=1, col=1)
        bb = signals.get("bb_series", {})
        if "upper" in bb:
            fig.add_trace(go.Scatter(x=df.index, y=bb["upper"], name="BB Upper",
                line=dict(color=PU, width=1, dash="dash"), opacity=0.5, showlegend=False), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=bb["lower"], name="BB Lower",
                line=dict(color=PU, width=1, dash="dash"), opacity=0.5,
                fill="tonexty", fillcolor="rgba(167,139,250,0.04)", showlegend=False), row=1, col=1)

    # Volume
    colors = [UP if c >= o else DN for c, o in zip(df["Close"], df["Open"])]
    fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
        marker_color=colors, opacity=0.6, showlegend=False), row=2, col=1)

    # RSI
    if signals and "rsi" in signals:
        from utils.math_utils import compute_rsi
        rsi_series = compute_rsi(df["Close"])
        fig.add_trace(go.Scatter(x=df.index, y=rsi_series, name="RSI",
            line=dict(color=SA, width=1.5), showlegend=False), row=3, col=1)
        fig.add_hline(y=70, line_color=DN, line_dash="dot", line_width=1, row=3, col=1)
        fig.add_hline(y=30, line_color=UP, line_dash="dot", line_width=1, row=3, col=1)

    fig.update_layout(**LAYOUT, height=height, xaxis_rangeslider_visible=False,
                      hovermode="x unified")
    fig.update_yaxes(row=3, range=[0, 100], title_text="RSI", title_font_size=9)
    fig.update_yaxes(row=2, title_text="Vol", title_font_size=9)
    return fig


def sector_heatmap(df: pd.DataFrame):
    """Sector performance heatmap."""
    if df.empty:
        return go.Figure()
    df = df.copy().reset_index(drop=True)
    colors = [UP if v >= 0 else DN for v in df["Change%"]]
    fig = go.Figure(go.Bar(
        x=df["Sector"], y=df["Change%"],
        marker_color=colors,
        text=[f"{v:+.2f}%" for v in df["Change%"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>%{y:.2f}%<extra></extra>",
    ))
    fig.update_layout(**LAYOUT, height=300, title="NSE Sector Performance",
                      showlegend=False, xaxis_tickangle=-30)
    fig.add_hline(y=0, line_color=MU, line_width=1)
    return fig


def payoff_diagram(payoff_data: list, spot: float, breakevens: list):
    """Options payoff at expiry."""
    spots   = [d["spot"] for d in payoff_data]
    payoffs = [d["payoff"] for d in payoff_data]
    colors  = [UP if p >= 0 else DN for p in payoffs]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=spots, y=payoffs, mode="lines",
        line=dict(color=SA, width=2.5),
        fill="tozeroy",
        fillcolor="rgba(245,158,11,0.08)",
        name="P&L",
    ))
    fig.add_hline(y=0, line_color=MU, line_width=1.5)
    fig.add_vline(x=spot, line_color=SA, line_dash="dash", line_width=1.5,
                  annotation_text=f"Spot ₹{spot:,.0f}", annotation_font_color=SA)
    for be in breakevens:
        fig.add_vline(x=be, line_color=SK, line_dash="dot", line_width=1,
                      annotation_text=f"BE ₹{be:,.0f}", annotation_font_color=SK)
    fig.update_layout(**LAYOUT, height=350, xaxis_title="Spot Price at Expiry",
                      yaxis_title="Profit / Loss (₹)", showlegend=False)
    return fig


def monte_carlo_chart(mc_result: dict, horizon: int, initial: float):
    """Monte Carlo simulation paths + percentile bands."""
    fig = go.Figure()
    paths = mc_result.get("paths", np.array([]))
    if len(paths):
        x = list(range(paths.shape[1]))
        for path in paths[:30]:
            fig.add_trace(go.Scatter(
                x=x, y=path, mode="lines",
                line=dict(color="rgba(245,158,11,0.08)", width=1),
                showlegend=False, hoverinfo="skip",
            ))
    # Percentile lines
    for label, val, color in [
        ("P5 (Worst)", mc_result["p5"], DN),
        ("P50 (Median)", mc_result["p50"], SA),
        ("P95 (Best)", mc_result["p95"], UP),
    ]:
        fig.add_hline(y=val, line_color=color, line_dash="dash", line_width=1.5,
                      annotation_text=f"{label}: ₹{val:,.0f}", annotation_font_color=color)
    fig.add_hline(y=initial, line_color=MU, line_width=1, line_dash="dot",
                  annotation_text="Initial", annotation_font_color=MU)
    fig.update_layout(**LAYOUT, height=400, title=f"Monte Carlo — {horizon}Y Simulation (1,000 paths)",
                      xaxis_title="Trading Days", yaxis_title="Portfolio Value (₹)")
    return fig


def oi_bar_chart(chain_df: pd.DataFrame, underlying: float):
    """Options OI bar chart near ATM."""
    near = chain_df[abs(chain_df["Strike"] - underlying) / underlying < 0.06].copy()
    if near.empty:
        return go.Figure()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=near["Strike"], y=near["Call OI"]/1000, name="Call OI",
                         marker_color=DN, opacity=0.85))
    fig.add_trace(go.Bar(x=near["Strike"], y=near["Put OI"]/1000, name="Put OI",
                         marker_color=UP, opacity=0.85))
    fig.update_layout(**LAYOUT, height=300, barmode="group",
                      title="Open Interest by Strike (near ATM, 000s)",
                      xaxis_title="Strike", yaxis_title="OI (thousands)")
    return fig


def pie_chart(labels, values, title=""):
    """Simple pie chart."""
    fig = go.Figure(go.Pie(
        labels=labels, values=values, hole=0.4,
        marker=dict(colors=[SA, SK, UP, DN, PU, "#FB923C", "#F472B6"]),
        textfont=dict(size=11),
    ))
    fig.update_layout(**LAYOUT, height=320, title=title,
                      showlegend=True, margin=dict(l=0, r=0, t=40, b=0))
    return fig


def nav_chart(df: pd.DataFrame, scheme_name: str):
    """MF NAV history line chart."""
    fig = go.Figure(go.Scatter(
        x=df["date"], y=df["nav"], mode="lines",
        line=dict(color=SA, width=2),
        fill="tozeroy", fillcolor="rgba(245,158,11,0.06)",
        name="NAV",
        hovertemplate="<b>%{x|%d %b %Y}</b><br>NAV: ₹%{y:.4f}<extra></extra>",
    ))
    fig.update_layout(**LAYOUT, height=320, title=scheme_name[:60],
                      xaxis_title="", yaxis_title="NAV (₹)")
    return fig
