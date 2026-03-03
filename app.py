"""
US Yield Curve Dashboard - Streamlit app with Supabase backend and FRED auto-update.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_manager import get_supabase_client, refresh_data, TENORS

st.set_page_config(page_title="US Yield Curve Dashboard", layout="wide")

st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:0rem;}"
    "h1{text-align:center;}</style>",
    unsafe_allow_html=True,
)

st.markdown("<h1>US YIELD CURVE DASHBOARD</h1>", unsafe_allow_html=True)

supabase = get_supabase_client()

with st.spinner("Loading data..."):
    df, status = refresh_data(supabase)

if df.empty:
    st.error("No data available. Please run load_initial_data.py to seed the database.")
    st.stop()

latest_date = df["observation_date"].max().strftime("%b-%Y")
st.caption(f"*Data as of {latest_date}*  |  {status}")

# Date range controls
min_date = df["observation_date"].min().date()
max_date = df["observation_date"].max().date()

col_start, col_end, col_spacer = st.columns([1, 1, 3])
with col_start:
    start_date = st.date_input("Start date", value=min_date, min_value=min_date, max_value=max_date)
with col_end:
    end_date = st.date_input("End date", value=max_date, min_value=min_date, max_value=max_date)

if start_date >= end_date:
    st.warning("Start date must be before end date.")
    st.stop()

mask = (df["observation_date"].dt.date >= start_date) & (df["observation_date"].dt.date <= end_date)
df_filtered = df.loc[mask].copy()

if df_filtered.empty:
    st.warning("No data in selected range.")
    st.stop()

df_monthly = df_filtered.set_index("observation_date").resample("MS").mean().dropna(how="all")
tenor_positions = [0.25, 0.5, 1, 2, 3, 5, 10, 30]

st.divider()

# Row 1: 3D Surface + Heatmap
col1, col2 = st.columns(2)

with col1:
    st.subheader("Yield Curve Historical Evolution")
    z_data = df_monthly[TENORS].values
    fig_surface = go.Figure(data=[go.Surface(
        z=z_data, x=tenor_positions, y=df_monthly.index,
        colorscale="RdBu_r", colorbar=dict(title="Yield %", len=0.75),
    )])
    fig_surface.update_layout(
        scene=dict(
            xaxis=dict(title="Maturity", tickvals=tenor_positions, ticktext=TENORS),
            yaxis=dict(title="Date"), zaxis=dict(title="Yield %"),
            camera=dict(eye=dict(x=-1.8, y=-1.5, z=0.8)),
        ),
        margin=dict(l=0, r=0, t=10, b=40), height=450,
    )
    st.plotly_chart(fig_surface, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

with col2:
    st.subheader("Yield Curve Heatmap")
    z_heat = df_monthly[TENORS].T.values
    fig_heat = go.Figure(data=go.Heatmap(
        z=z_heat, x=df_monthly.index, y=TENORS,
        colorscale="RdBu_r", colorbar=dict(title="Yield %", len=0.75),
        hovertemplate="Date: %{x|%b %Y}<br>Tenor: %{y}<br>Yield: %{z:.2f}%<extra></extra>",
    ))
    fig_heat.update_layout(
        margin=dict(l=0, r=0, t=10, b=40), height=450,
        yaxis=dict(type="category"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")

# Row 2: Animated Yield Curve Replay + 10Y-3M Spread
col3, col4 = st.columns(2)

with col3:
    st.subheader("Yield Curve Monthly Replay")
    dates_list = df_monthly.index.tolist()
    if len(dates_list) > 0:
        global_max = df_monthly[TENORS].max().max()
        y_max = max(7, global_max + 0.5) if not np.isnan(global_max) else 7
        first_curve = df_monthly.iloc[0][TENORS]
        fig_anim = go.Figure(data=[go.Scatter(
            x=TENORS, y=first_curve.values,
            mode="lines+markers+text",
            text=[f"{v:.2f}" if not np.isnan(v) else "" for v in first_curve.values],
            textposition="top center",
            line=dict(color="#555", width=2),
            marker=dict(size=8, color="#333"),
        )])
        frames = []
        for dt in dates_list:
            curve = df_monthly.loc[dt, TENORS]
            frames.append(go.Frame(
                data=[go.Scatter(
                    x=TENORS, y=curve.values,
                    mode="lines+markers+text",
                    text=[f"{v:.2f}" if not np.isnan(v) else "" for v in curve.values],
                    textposition="top center",
                    line=dict(color="#555", width=2),
                    marker=dict(size=8, color="#333"),
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
            xaxis_title="", yaxis_title="Yield",
            yaxis=dict(range=[0, y_max]),
            margin=dict(l=40, r=20, t=10, b=10), height=450,
            updatemenus=[dict(
                type="buttons", showactive=False,
                x=0.0, y=-0.02, xanchor="left", yanchor="top",
                buttons=[
                    dict(label="Play", method="animate",
                         args=[None, dict(frame=dict(duration=150, redraw=True),
                                          fromcurrent=True, transition=dict(duration=80))]),
                    dict(label="Pause", method="animate",
                         args=[[None], dict(frame=dict(duration=0, redraw=False),
                                            mode="immediate", transition=dict(duration=0))]),
                ],
            )],
            sliders=[dict(
                active=0,
                currentvalue=dict(prefix="Date: ", font=dict(size=13)),
                pad=dict(b=5, t=30),
                steps=slider_steps,
            )],
        )
        st.plotly_chart(fig_anim, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

with col4:
    st.subheader("10Y-3M Spread in bps")
    df_spread = df_filtered.copy()
    df_spread["spread"] = (df_spread["10Y"] - df_spread["3M"]) * 100
    fig_spread = go.Figure()
    fig_spread.add_trace(go.Scatter(
        x=df_spread["observation_date"], y=df_spread["spread"],
        fill="tozeroy", fillcolor="rgba(180,180,180,0.4)",
        line=dict(color="#555", width=1),
        hovertemplate="Date: %{x|%b %d, %Y}<br>Spread: %{y:.0f} bps<extra></extra>",
    ))
    fig_spread.update_layout(
        xaxis_title="", yaxis_title="Spread (bps)",
        margin=dict(l=40, r=20, t=10, b=40), height=450,
    )
    st.plotly_chart(fig_spread, use_container_width=True)
    st.caption("Data Source: FRED - Federal Reserve Economic Data")
