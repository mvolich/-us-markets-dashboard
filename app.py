"""
US Yield Curve Dashboard
Rubrics Asset Management
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import time
from data_manager import get_supabase_client, refresh_data, TENORS

st.set_page_config(page_title="US Yield Curve Dashboard | Rubrics", layout="wide")

st.markdown("""
<style>
    :root {
        --rb-blue: #001E4F;
        --rb-mblue: #2C5697;
        --rb-lblue: #7BA4DB;
        --rb-grey: #D8D7DF;
        --rb-orange: #CF4520;
        --rb-bg: #f4f5f7;
    }
    * { font-family: Arial, Helvetica, sans-serif !important; }
    .stApp { background: var(--rb-bg); }
    .block-container { padding-top: 1rem; padding-bottom: 2rem; max-width: 95%; padding-left: 2rem; padding-right: 2rem; }
    .dash-header {
        background: linear-gradient(135deg, #001E4F 0%, #0a2a5e 100%);
        padding: 20px 32px; border-radius: 10px; margin-bottom: 20px;
        display: flex; align-items: center; justify-content: space-between;
    }
    .dash-header h1 { color: #fff; font-size: 1.5rem; font-weight: 700; margin: 0; }
    .dash-header .subtitle { color: rgba(255,255,255,0.6); font-size: 12px; margin-top: 2px; }
    .dash-header-right { display: flex; align-items: center; gap: 20px; }
    .dash-header .data-date { color: var(--rb-lblue); font-size: 12px; font-weight: 500; }
    .dash-header img { height: 36px; }
    .stSubheader, h3 {
        color: var(--rb-blue) !important; font-size: 14px !important;
        font-weight: 700 !important; padding-bottom: 6px !important;
        border-bottom: 2px solid var(--rb-grey) !important; margin-bottom: 8px !important;
    }
    .stCaption, figcaption { color: #6b7280 !important; font-size: 11px !important; }
    div[data-testid="stRadio"] > div { flex-direction: row !important; gap: 8px; }
    hr { border-color: var(--rb-grey) !important; opacity: 0.5; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;}
    header[data-testid="stHeader"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

PLOTLY_LAYOUT = dict(
    font=dict(family="Arial, Helvetica, sans-serif", color="#001E4F", size=11),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(bgcolor="#001E4F", font_color="#fff", font_size=12),
)
RB_BLUE = "#001E4F"
RB_MBLUE = "#2C5697"
GHOST_COLOR = "rgba(0,30,79,0.08)"

supabase = get_supabase_client()
with st.spinner("Loading data..."):
    df, status = refresh_data(supabase)

if df.empty:
    st.error("No data available. Please run load_initial_data.py to seed the database.")
    st.stop()

latest_date = df["observation_date"].max().strftime("%b %Y")
st.markdown(f'''
<div class="dash-header">
    <div>
        <h1>US Yield Curve Dashboard</h1>
        <div class="subtitle">Treasury Yield Curve Analysis</div>
    </div>
    <div class="dash-header-right">
        <div class="data-date">Data as of {latest_date}</div>
        <img src="https://rubricsam.com/wp-content/uploads/2021/01/cropped-rubrics-logo-tight.png" alt="Rubrics">
    </div>
</div>
''', unsafe_allow_html=True)

min_date = df["observation_date"].min().date()
max_date = df["observation_date"].max().date()

c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
with c2:
    end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)
with c3:
    spacing_mode = st.radio("Maturity spacing", ["Actual years", "Even spacing"], horizontal=True)

if start_date >= end_date:
    st.warning("Start date must be before end date.")
    st.stop()

TENOR_YEARS = [0.25, 0.5, 1, 2, 3, 5, 10, 30]
if spacing_mode == "Even spacing":
    tenor_positions = list(range(len(TENORS)))
else:
    tenor_positions = TENOR_YEARS

mask = (df["observation_date"].dt.date >= start_date) & (df["observation_date"].dt.date <= end_date)
df_filtered = df.loc[mask].copy()
if df_filtered.empty:
    st.warning("No data in selected range.")
    st.stop()

df_monthly = df_filtered.set_index("observation_date").resample("MS").mean().dropna(how="all")

# ═══════════════════════════════════════════
# Row 1: 3D Surface + Heatmap
# ═══════════════════════════════════════════
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
                       gridcolor="rgba(0,30,79,0.08)"),
            yaxis=dict(title="Date", gridcolor="rgba(0,30,79,0.08)"),
            zaxis=dict(title="Yield %", gridcolor="rgba(0,30,79,0.08)"),
            camera=dict(eye=dict(x=-2.0, y=-1.5, z=0.7)),
            aspectratio=dict(x=1, y=2.5, z=0.8),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=10, b=30), height=550,
    )
    st.plotly_chart(fig_surface, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

with col2:
    st.subheader("Yield Curve Heatmap")
    z_heat = df_monthly[TENORS].T.values
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_heat, x=df_monthly.index, y=tenor_positions,
        colorscale="RdBu_r", colorbar=dict(title="Yield %", len=0.75, thickness=15),
        hovertemplate="Date: %{x|%b %Y}<br>Tenor: %{customdata}<br>Yield: %{z:.2f}%<extra></extra>",
        customdata=np.tile(np.array(TENORS).reshape(-1, 1), (1, len(df_monthly))),
    ))
    fig_heat.update_layout(
        **PLOTLY_LAYOUT,
        margin=dict(l=0, r=0, t=10, b=30), height=550,
        yaxis=dict(tickvals=tenor_positions, ticktext=TENORS, gridcolor="rgba(0,30,79,0.08)"),
        xaxis=dict(gridcolor="rgba(0,30,79,0.08)"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

# ═══════════════════════════════════════════
# Row 2: Yield Curve Replay + 10Y-3M Spread
# ═══════════════════════════════════════════
col3, col4 = st.columns(2)

with col3:
    st.subheader("Yield Curve Monthly Replay")
    dates_list = df_monthly.index.tolist()

    if len(dates_list) > 1:
        global_max = df_monthly[TENORS].max().max()
        y_max = max(7, global_max + 0.5) if not np.isnan(global_max) else 7
        date_strings = [d.strftime("%Y-%m") for d in dates_list]

        # Session state for animation
        if "replay_idx" not in st.session_state:
            st.session_state.replay_idx = 0
        if "playing" not in st.session_state:
            st.session_state.playing = False

        # Controls row: Play/Pause + Reset
        btn1, btn2, btn3 = st.columns([1, 1, 3])
        with btn1:
            if st.button("\u25b6 Play" if not st.session_state.playing else "\u23f8 Pause"):
                st.session_state.playing = not st.session_state.playing
                st.rerun()
        with btn2:
            if st.button("\u23ee Reset"):
                st.session_state.replay_idx = 0
                st.session_state.playing = False
                st.rerun()

        # Slider
        selected_idx = st.select_slider(
            "Select month",
            options=range(len(dates_list)),
            value=st.session_state.replay_idx,
            format_func=lambda i: date_strings[i],
            key="replay_slider",
        )
        # Sync slider back to session state
        st.session_state.replay_idx = selected_idx

        # Build chart
        fig_replay = go.Figure()

        # Ghost trails: only months BEFORE the selected index
        if selected_idx > 0:
            past_indices = list(range(0, selected_idx))
            max_ghosts = 30
            if len(past_indices) > max_ghosts:
                step = len(past_indices) / max_ghosts
                past_indices = [int(i * step) for i in range(max_ghosts)]
            for pi in past_indices:
                past_dt = dates_list[pi]
                past_curve = df_monthly.loc[past_dt, TENORS]
                fig_replay.add_trace(go.Scatter(
                    x=tenor_positions, y=past_curve.values,
                    mode="lines", line=dict(color=GHOST_COLOR, width=1),
                    hoverinfo="skip", showlegend=False,
                ))

        # Active curve
        selected_date = dates_list[selected_idx]
        curve = df_monthly.loc[selected_date, TENORS]
        fig_replay.add_trace(go.Scatter(
            x=tenor_positions, y=curve.values,
            mode="lines+markers+text",
            text=[f"{v:.2f}" if not np.isnan(v) else "" for v in curve.values],
            textposition="top center", textfont=dict(size=10, color=RB_BLUE),
            line=dict(color=RB_MBLUE, width=2.5),
            marker=dict(size=7, color=RB_MBLUE, line=dict(width=1, color="#fff")),
            showlegend=False,
        ))

        fig_replay.update_layout(
            **PLOTLY_LAYOUT,
            xaxis=dict(title="", tickvals=tenor_positions, ticktext=TENORS,
                       gridcolor="rgba(0,30,79,0.08)", zeroline=False),
            yaxis=dict(title="Yield (%)", range=[0, y_max],
                       gridcolor="rgba(0,30,79,0.08)", zeroline=False),
            margin=dict(l=50, r=20, t=10, b=30), height=480,
        )
        st.plotly_chart(fig_replay, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

        # Auto-advance if playing
        if st.session_state.playing:
            if st.session_state.replay_idx < len(dates_list) - 1:
                time.sleep(0.15)
                st.session_state.replay_idx += 1
                st.rerun()
            else:
                st.session_state.playing = False

with col4:
    st.subheader("10Y-3M Spread")
    df_spread = df_filtered.copy()
    df_spread["spread"] = (df_spread["10Y"] - df_spread["3M"]) * 100
    fig_spread = go.Figure()
    fig_spread.add_hline(y=0, line_dash="dot", line_color="rgba(0,30,79,0.3)", line_width=1)
    fig_spread.add_trace(go.Scatter(
        x=df_spread["observation_date"], y=df_spread["spread"],
        fill="tozeroy", fillcolor="rgba(44,86,151,0.15)",
        line=dict(color=RB_MBLUE, width=1.5),
        hovertemplate="Date: %{x|%b %d, %Y}<br>Spread: %{y:.0f} bps<extra></extra>",
    ))
    fig_spread.update_layout(
        **PLOTLY_LAYOUT,
        xaxis=dict(title="", gridcolor="rgba(0,30,79,0.08)", zeroline=False),
        yaxis=dict(title="Spread (bps)", gridcolor="rgba(0,30,79,0.08)", zeroline=False),
        margin=dict(l=50, r=20, t=10, b=30), height=550,
    )
    st.plotly_chart(fig_spread, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")
