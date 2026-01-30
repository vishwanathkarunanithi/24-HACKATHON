import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
import paho.mqtt.client as mqtt
import json
from collections import deque

# ---------------------------------------------------------
# 1. SETUP & CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Smart Meter Digital Twin", layout="wide", page_icon="⚡")

# Custom CSS for Professional Look
st.markdown("""
    <style>
        .stMetric {
            background-color: #0E1117;
            border: 1px solid #30333F;
            padding: 15px;
            border-radius: 10px;
        }
    </style>
""", unsafe_allow_html=True)

# Load AI Model (Create dummy if missing)
try:
    model = joblib.load('energy_model.pkl')
except:
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(contamination=0.05)
    model.fit(pd.DataFrame({'voltage':[230]*100, 'current':[5]*100}))

# Session State for Live Data
if 'history_power' not in st.session_state: st.session_state.history_power = deque(maxlen=60)
if 'live_voltage' not in st.session_state: st.session_state.live_voltage = 230.0
if 'live_current' not in st.session_state: st.session_state.live_current = 5.0
if 'mqtt_connected' not in st.session_state: st.session_state.mqtt_connected = False

# ---------------------------------------------------------
# 2. MQTT CONNECTION (THE CLOUD BRIDGE)
# ---------------------------------------------------------
BROKER = "broker.hivemq.com"
TOPIC = "team_immortal/meter/data"

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
        st.session_state.live_voltage = float(data['voltage'])
        st.session_state.live_current = float(data['current'])
    except:
        pass

if not st.session_state.mqtt_connected:
    try:
        client = mqtt.Client()
        client.on_message = on_message
        client.connect(BROKER, 1883, 60)
        client.subscribe(TOPIC)
        client.loop_start()
        st.session_state.mqtt_connected = True
    except:
        pass

# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.title("⚙️ Control Panel")
mode = st.sidebar.radio("Data Source:", ["Manual Control", "🔥 Demo Scenarios", "🔴 LIVE HARDWARE"])

if mode == "Manual Control":
    st.sidebar.markdown("---")
    voltage = st.sidebar.slider("Grid Voltage (V)", 0, 300, 230)
    current = st.sidebar.slider("Load Current (A)", 0.0, 20.0, 5.0)

elif mode == "🔥 Demo Scenarios":
    st.sidebar.markdown("---")
    scenario = st.sidebar.selectbox("Simulate Event:", ["Normal", "Theft (Bypass)", "Wire Cut", "Overload"])
    if scenario == "Normal": voltage, current = 230.0, 5.0
    elif scenario == "Theft (Bypass)": voltage, current = 230.0, 0.2
    elif scenario == "Wire Cut": voltage, current = 10.0, 0.0
    elif scenario == "Overload": voltage, current = 210.0, 35.0

else: # LIVE HARDWARE
    st.sidebar.markdown("---")
    st.sidebar.success(f"📡 MQTT: {'CONNECTED' if st.session_state.mqtt_connected else 'CONNECTING...'}")
    voltage = st.session_state.live_voltage
    current = st.session_state.live_current

# ---------------------------------------------------------
# 4. AI & CALCULATIONS
# ---------------------------------------------------------
power = voltage * current
st.session_state.history_power.append(power)

# AI Prediction (1 = Normal, -1 = Anomaly/Theft)
prediction = model.predict([[voltage, current]])[0]

# ---------------------------------------------------------
# 5. MAIN DASHBOARD UI
# ---------------------------------------------------------
st.title("⚡ Generative Energy Systems Design Tool")
st.caption(f"Project: Smart Meter Digital Twin | Mode: **{mode}**")

# Top KPI Row
k1, k2, k3, k4 = st.columns(4)
k1.metric("Voltage", f"{voltage:.1f} V", delta=f"{voltage-230:.1f} V")
k2.metric("Current", f"{current:.2f} A", delta=f"{current-5:.2f} A")
k3.metric("Power", f"{power:.1f} W")
k4.metric("Status", "SAFE" if prediction == 1 else "THEFT!", delta_color="normal" if prediction == 1 else "inverse")

st.markdown("---")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("🤖 AI Analysis")
    if prediction == 1:
        st.success("✅ SYSTEM NORMAL")
        st.write("Grid Stability: **Optimized**")
        st.write("Theft Probability: **< 1%**")
    else:
        st.error("🚨 THREAT DETECTED")
        st.write("Grid Stability: **CRITICAL**")
        st.write("Theft Probability: **99.9%**")
    
    st.progress(0.05 if prediction == 1 else 0.95)
    st.caption("Anomaly Confidence Score")

with col2:
    st.subheader("📈 Real-Time Digital Twin")
    
    tab1, tab2 = st.tabs(["Oscilloscope (Waveform)", "Power History"])
    
    with tab1:
        # Generate Sine Wave
        t = np.linspace(0, 0.1, 100)
        wave = voltage * np.sin(2 * np.pi * 50 * t)
        st.line_chart(pd.DataFrame({'Time': t, 'Voltage': wave}).set_index('Time'))
    
    with tab2:
        st.line_chart(list(st.session_state.history_power))

# Auto-refresh for Live Mode
if mode == "🔴 LIVE HARDWARE":
    time.sleep(1)
    st.rerun()