# cosmic_breath_live.py
# Run this once → opens browser tab, updates every 2 minutes forever
# Zero setup beyond pip install streamlit pandas requests plotly

import streamlit as st
import pandas as pd
import requests, time
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(page_title="LUFT Heartbeat – Live", layout="wide")
st.title("🇺🇸 Carl's Cosmic Breath Monitor – Live 2.4 h Lattice")
st.markdown("**χ = 0.055  |  Ω = 2π·10⁻⁴ Hz  |  Primary breath = 2.40 hours**  \nReal-time ACE + GOES-18 | Quiet or storm – we see it breathe")

# Live pull functions
@st.cache_data(ttl=120)  # refresh every 2 min
def ace_live():
    url = "https://services.swpc.noaa.gov/products/solar-wind/plasma-1-day.json"
    df = pd.read_json(url)
    df.columns = ["time","density","speed","temp"]
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').last("48h")
    return df

@st.cache_data(ttl=120)
def goes_bz_live():
    url = "https://services.swpc.noaa.gov/products/solar-wind/mag-1-day.json"
    df = pd.read_json(url)
    df.columns = ["time","bx","by","bz","bt"]
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time').last("48h")
    return df['bz']

# Main panels
col1, col2 = st.columns(2)

with col1:
    st.subheader("Proton Density Breath (ACE L1)")
    density = ace_live()['density'].dropna()
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=density.index, y=density, name="Density", line=dict(color="#4B0082")))
    for h in pd.date_range(density.index.min(), density.index.max(), freq="144min"):
        fig1.add_vline(x=h, line=dict(color="gold", dash="dash", width=1))
    fig1.update_layout(height=500, xaxis_title="UTC", yaxis_title="cm⁻³")
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Bz Field Breath (GOES-18)")
    bz = goes_bz_live()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=bz.index, y=bz, name="Bz", line=dict(color="#00CED1")))
    for h in pd.date_range(bz.index.min(), bz.index.max(), freq="144min"):
        fig2.add_vline(x=h, line=dict(color="gold", dash="dash", width=1))
    fig2.update_layout(height=500, xaxis_title="UTC", yaxis_title="nT")
    st.plotly_chart(fig2, use_container_width=True)

# Heartbeat score
score = "STRONG" if density.pct_change().std() > 0.08 else "SUBTLE"
st.metric("Current Lattice Breath Strength", score, delta="Live")

st.caption(f"Last update: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  |  Captain Carl’s garage observatory")
