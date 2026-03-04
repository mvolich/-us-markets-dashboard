"""
US Yield Curve Dashboard
Rubrics Asset Management
"""
import math
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_manager import get_supabase_client, refresh_data, TENORS

st.set_page_config(page_title="US Yield Curve Dashboard | Rubrics", layout="wide")

st.markdown("""
<style>
    @import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");
    :root {
        --rb-blue: #001E4F;
        --rb-mblue: #2C5697;
        --rb-lblue: #7BA4DB;
        --rb-grey: #D8D7DF;
        --rb-orange: #CF4520;
        --rb-bg: #f4f5f7;
    }
    .stApp { background: var(--rb-bg); font-family: "Inter", Arial, sans-serif; }
    .block-container { padding-top: 1.5rem; padding-bottom: 0rem; max-width: 1400px; }
    /* Header bar */
    .dash-header {
        background: linear-gradient(135deg, #001E4F 0%, #0a2a5e 100%);
        padding: 24px 32px; border-radius: 10px; margin-bottom: 24px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .dash-header h1 { color: #fff; font-size: 1.6rem; font-weight: 700; margin: 0; }
    .dash-header .subtitle { color: rgba(255,255,255,0.6); font-size: 13px; margin-top: 2px; }
    .dash-header .data-date { color: var(--rb-lblue); font-size: 13px; font-weight: 500; }
    /* Cards */
    div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlock"] {
        background: #fff; border-radius: 10px; padding: 20px 24px;
        box-shadow: 0 1px 3px rgba(0,30,79,0.06), 0 4px 12px rgba(0,30,79,0.04);
        border: 1px solid rgba(0,30,79,0.04); margin-bottom: 16px;
    }
    /* Subheaders */
    .stSubheader, h3 {
        color: var(--rb-blue) !important; font-size: 15px !important;
        font-weight: 700 !important; padding-bottom: 8px !important;
        border-bottom: 2px solid var(--rb-grey) !important; margin-bottom: 12px !important;
    }
    /* Caption styling */
    .stCaption, figcaption { color: #6b7280 !important; font-size: 11px !important; }
    /* Control bar */
    .control-bar {
        background: #fff; border-radius: 10px; padding: 16px 24px;
        box-shadow: 0 1px 3px rgba(0,30,79,0.06); margin-bottom: 20px;
        border: 1px solid rgba(0,30,79,0.04);
    }
    /* Radio buttons inline */
    div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 16px; }
    div[data-testid="stRadio"] label {
        background: var(--rb-bg); border: 1px solid var(--rb-grey); border-radius: 6px;
        padding: 6px 16px; font-size: 13px; font-weight: 500; transition: all 0.2s;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: var(--rb-mblue); color: #fff; border-color: var(--rb-mblue);
    }
    /* Divider */
    hr { border-color: var(--rb-grey) !important; opacity: 0.5; }
    /* Hide Streamlit elements */
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    font=dict(family="Inter, Arial, sans-serif", color="#001E4F"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(bgcolor="#001E4F", font_color="#fff", font_size=12),
)

supabase = get_supabase_client()
with st.spinner("Loading data..."):
    df, status = refresh_data(supabase)

if df.empty:
    st.error("No data available. Please run load_initial_data.py to seed the database.")
    st.stop()

latest_date = df["observation_date"].max().strftime("%b %Y")
st.markdown(f"""
<div class="dash-header">
    <div>
        <h1>US Yield Curve Dashboard</h1>
        <div class="subtitle">Treasury Yield Curve Analysis</div>
    </div>
    <div class="data-date">Data as of {latest_date}</div>
</div>
""", unsafe_allow_html=True)

min_date = df["observation_date"].min().date()
max_date = df["observation_date"].max().date()

c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
with c1:
    start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
with c2:
    end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
with c3:
    spacing_mode = st.radio(
        "Maturity spacing",
        ["Linear (actual years)", "Log scale", "Even spacing"],
        horizontal=True,
    )

if start_date >= end_date:
    st.warning("Start date must be before end date.")
    st.stop()

TENOR_YEARS = [0.25, 0.5, 1, 2, 3, 5, 10, 30]
if spacing_mode.startswith("Log"):
    tenor_positions = [math.log(t) for t in TENOR_YEARS]
elif spacing_mode.startswith("Even"):
    tenor_positions = list(range(len(TENORS)))
else:
    tenor_positions = TENOR_YEARS

mask = (df["observation_date"].dt.date >= start_date) & (df["observation_date"].dt.date <= end_date)
df_filtered = df.loc[mask].copy()
if df_filtered.empty:
    st.warning("No data in selected range.")
    st.stop()

df_monthly = df_filtered.set_index("observation_date").resample("MS").mean().dropna(how="all")

RB_BLUE = "#001E4F"
RB_MBLUE = "#2C5697"
RB_ORANGE = "#CF4520"

col1, col2 = st.columns(2)

with col1:
    st.subheader("Yield Curve Historical Evolution")
    z_data = df_monthly[TENORS].values
    fig_surface = go.Figure(data=[go.Surface(
        z=z_data, x=tenor_positions, y=df_monthly.index,
        colorscale="RdBu_r", colorbar=dict(title="Yield %", len=0.75, thickness=15),
    )])
    fig_surface.update_layout(
        **PLOTLY_LAYOUT,
        scene=dict(
            xaxis=dict(title="Maturity", tickvals=tenor_positions, ticktext=TENORS,
                       autorange="reversed", gridcolor="rgba(0,30,79,0.08)"),
            yaxis=dict(title="Date", gridcolor="rgba(0,30,79,0.08)"),
            zaxis=dict(title="Yield %", gridcolor="rgba(0,30,79,0.08)"),
            camera=dict(eye=dict(x=-2.0, y=-0.8, z=0.6)),
            aspectratio=dict(x=1, y=2.5, z=0.8),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=40), height=480,
    )
    st.plotly_chart(fig_surface, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

with col2:
    st.subheader("Yield Curve Heatmap")
    z_heat = df_monthly[TENORS].T.values
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_heat, x=df_monthly.index, y=TENORS,
        colorscale="RdBu_r", colorbar=dict(title="Yield %", len=0.75, thickness=15),
        hovertemplate="Date: %{x|%b %Y}<br>Tenor: %{y}<br>Yield: %{z:.2f}%<extra></extra>",
    ))
    fig_heat.update_layout(
        **PLOTLY_LAYOUT,
        margin=dict(l=0, r=0, t=10, b=40), height=480,
        yaxis=dict(type="category"),
        xaxis=dict(gridcolor="rgba(0,30,79,0.08)"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

col3, col4 = st.columns(2)

with col3:
    st.subheader("Yield Curve Monthly Replay")
    dates_list = df_monthly.index.tolist()
    if len(dates_list) > 0:
        global_max = df_monthly[TENORS].max().max()
        y_max = max(7, global_max + 0.5) if not np.isnan(global_max) else 7
        first_curve = df_monthly.iloc[0][TENORS]
        fig_anim = go.Figure(data=[go.Scatter(
            x=tenor_positions, y=first_curve.values,
            mode="lines+markers+text",
            text=[f"{v:.2f}" if not np.isnan(v) else "" for v in first_curve.values],
            textposition="top center", textfont=dict(size=11, color=RB_BLUE),
            line=dict(color=RB_MBLUE, width=2.5),
            marker=dict(size=8, color=RB_MBLUE, line=dict(width=1, color="#fff")),
        )])
        frames = []
        for dt in dates_list:
            curve = df_monthly.loc[dt, TENORS]
            frames.append(go.Frame(
                data=[go.Scatter(
                    x=tenor_positions, y=curve.values,
                    mode="lines+markers+text",
                    text=[f"{v:.2f}" if not np.isnan(v) else "" for v in curve.values],
                    textposition="top center", textfont=dict(size=11, color=RB_BLUE),
                    line=dict(color=RB_MBLUE, width=2.5),
                    marker=dict(size=8, color=RB_MBLUE, line=dict(width=1, color="#fff")),
                )],
                name=dt.strftime("%Y-%m"),
            ))
        fig_anim.frames = frames
        slider_steps = [
            dict(
                args=[[dt.strftime("%Y-%m")], dict(frame=dict(duration=0, redraw=True), mode="immediate")],
                label=dt.strftime("%Y-%m"), method="animate",
            )
            for dt in dates_list
        ]
        fig_anim.update_layout(
            **PLOTLY_LAYOUT,
            xaxis=dict(title="", tickvals=tenor_positions, ticktext=TENORS,
                       gridcolor="rgba(0,30,79,0.08)", zeroline=False),
            yaxis=dict(title="Yield (%)", range=[0, y_max],
                       gridcolor="rgba(0,30,79,0.08)", zeroline=False),
            margin=dict(l=50, r=20, t=10, b=10), height=480,
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=0.0, y=-0.02, xanchor="left", yanchor="top",
                font=dict(size=12),
                buttons=[
                    dict(label="▶ Play", method="animate",
                         args=[None, dict(frame=dict(duration=150, redraw=True),
                                          fromcurrent=True, transition=dict(duration=80))]),
                    dict(label="⏸ Pause", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False),
                                            mode="immediate", transition=dict(duration=0))]),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix="Date: ", font=dict(size=13, color=RB_BLUE)),
                pad=dict(b=5, t=30),
                steps=slider_steps,
                activebgcolor=RB_MBLUE,
                bordercolor="rgba(0,30,79,0.1)",
            )],
        )
        st.plotly_chart(fig_anim, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

with col4:
    st.subheader("10Y-3M Spread")
    df_spread = df_filtered.copy()
    df_spread["spread"] = (df_spread["10Y"] - df_spread["3M"]) * 100
    fig_spread = go.Figure()
    # Shade negative spread region
    fig_spread.add_hline(y=0, line_dash="dot", line_color="rgba(0,30,79,0.3)", line_width=1)
    fig_spread.add_trace(go.Scatter(
        x=df_spread["observation_date"], y=df_spread["spread"],
        fill="tozeroy",
        fillcolor="rgba(44,86,151,0.15)",
        line=dict(color=RB_MBLUE, width=1.5),
        hovertemplate="Date: %{x|%b %d, %Y}<br>Spread: %{y:.0f} bps<extra></extra>",
    ))
    fig_spread.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title="", gridcolor="rgba(0,30,79,0.08)", zeroline=False),
        yaxis=dict(title="Spread (bps)", gridcolor="rgba(0,30,79,0.08)", zeroline=False),
        margin=dict(l=50, r=20, t=10, b=40), height=480,
    )
    st.plotly_chart(fig_spread, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")
