"""
US Markets Dashboard - Streamlit app with Supabase backend and FRED auto-update.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from data_manager import get_supabase_client, refresh_data, TENORS

# Page config
st.set_page_config(page_title="US Markets Dashboard", layout="wide")

st.markdown(
    "<style>.block-container{padding-top:1rem;padding-bottom:0rem;}"
    "h1{text-align:center;}"
    ".stTabs [data-baseweb='tab-list']{justify-content:center;}</style>",
    unsafe_allow_html=True,
)

st.markdown("<h1>US MARKETS DASHBOARD</h1>", unsafe_allow_html=True)

# Load data
supabase = get_supabase_client()

with st.spinner("Loading data..."):
    df, status = refresh_data(supabase)

if df.empty:
    st.error("No data available. Please run load_initial_data.py to seed the database.")
    st.stop()

latest_date = df["observation_date"].max().strftime("%b-%Y")
st.caption(f"*Data as of {latest_date}*  |  {status}")

# Tabs
tab_treasuries, tab_equities, tab_pca = st.tabs(
    ["TREASURIES", "EQUITIES", "PCA+CLUSTERING"]
)

# ---- TREASURIES TAB ----
with tab_treasuries:
    df_monthly = df.set_index("observation_date").resample("MS").mean().dropna(how="all")
    tenor_positions = [0.25, 0.5, 1, 2, 3, 5, 10, 30]

    col1, col2 = st.columns(2)

    # 3D Surface
    with col1:
        st.subheader("Yield Curve Historical Evolution")
        z_data = df_monthly[TENORS].values

        fig_surface = go.Figure(
            data=[
                go.Surface(
                    z=z_data,
                    x=tenor_positions,
                    y=df_monthly.index,
                    colorscale="RdBu_r",
                    colorbar=dict(title="Yield %", len=0.75),
                )
            ]
        )
        fig_surface.update_layout(
            scene=dict(
                xaxis=dict(title="Maturity", tickvals=tenor_positions, ticktext=TENORS),
                yaxis=dict(title="Date"),
                zaxis=dict(title="Yield %"),
                camera=dict(eye=dict(x=-1.8, y=-1.5, z=0.8)),
            ),
            margin=dict(l=0, r=0, t=10, b=40),
            height=450,
        )
        st.plotly_chart(fig_surface, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

    # Heatmap
    with col2:
        st.subheader("Yield Curve Heatmap")
        z_heat = df_monthly[TENORS].T.values

        fig_heat = go.Figure(
            data=go.Heatmap(
                z=z_heat,
                x=df_monthly.index,
                y=TENORS,
                colorscale="RdBu_r",
                colorbar=dict(title="Yield %", len=0.75),
                hovertemplate=(
                    "Date: %{x|%b %Y}<br>Tenor: %{y}<br>"
                    "Yield: %{z:.2f}%<extra></extra>"
                ),
            )
        )
        fig_heat.update_layout(
            margin=dict(l=0, r=0, t=10, b=40),
            height=450,
            yaxis=dict(type="category"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

    col3, col4 = st.columns(2)

    # Yield Curve Replay
    with col3:
        st.subheader("Yield Curve Monthly Replay")
        dates_list = df_monthly.index.tolist()
        date_strings = [d.strftime("%Y-%m") for d in dates_list]

        selected_idx = st.select_slider(
            "Select date",
            options=range(len(dates_list)),
            value=len(dates_list) - 1,
            format_func=lambda i: date_strings[i],
            key="replay_slider",
        )

        selected_date = dates_list[selected_idx]
        curve = df_monthly.loc[selected_date, TENORS]

        fig_replay = go.Figure()
        fig_replay.add_trace(
            go.Scatter(
                x=TENORS,
                y=curve.values,
                mode="lines+markers+text",
                text=[
                    f"{v:.2f}" if not np.isnan(v) else "" for v in curve.values
                ],
                textposition="top center",
                line=dict(color="#555", width=2),
                marker=dict(size=8, color="#333"),
            )
        )
        y_max = max(7, curve.max() + 0.5) if not curve.isna().all() else 7
        fig_replay.update_layout(
            xaxis_title="",
            yaxis_title="Yield",
            yaxis=dict(range=[0, y_max]),
            margin=dict(l=40, r=20, t=10, b=40),
            height=400,
        )
        st.plotly_chart(fig_replay, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

    # 10Y-3M Spread
    with col4:
        st.subheader("10Y-3M Spread in bps")
        df_spread = df.copy()
        df_spread["spread"] = (df_spread["10Y"] - df_spread["3M"]) * 100

        fig_spread = go.Figure()
        fig_spread.add_trace(
            go.Scatter(
                x=df_spread["observation_date"],
                y=df_spread["spread"],
                fill="tozeroy",
                fillcolor="rgba(180,180,180,0.4)",
                line=dict(color="#555", width=1),
                hovertemplate=(
                    "Date: %{x|%b %d, %Y}<br>"
                    "Spread: %{y:.0f} bps<extra></extra>"
                ),
            )
        )
        fig_spread.update_layout(
            xaxis_title="",
            yaxis_title="Spread (bps)",
            margin=dict(l=40, r=20, t=10, b=40),
            height=400,
        )
        st.plotly_chart(fig_spread, use_container_width=True)
        st.caption("Data Source: FRED - Federal Reserve Economic Data")

# ---- EQUITIES TAB ----
with tab_equities:
    st.info("Equities tab - coming soon.")

# ---- PCA + CLUSTERING TAB ----
with tab_pca:
    st.info("PCA + Clustering tab - coming soon.")
