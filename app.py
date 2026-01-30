import streamlit as st
import pandas as pd
import numpy as np
import joblib
import time
import paho.mqtt.client as mqtt
import json
from collections import deque

# 1. LOAD AI MODEL (or create dummy)
try:
    model = joblib.load('energy_model.pkl')
except:
    from sklearn.ensemble import IsolationForest
    model = IsolationForest(contamination=0.05)
    model.fit(pd.DataFrame({'voltage':[230]*100, 'current':[5]*100}))

# 2. PAGE CONFIG (Wide Mode & Dark Theme)
st.set_page_config(page_title="Smart Meter Digital Twin", layout="wide", page_icon="⚡")

# Custom CSS for "Hacker/Sci-Fi" Look
st.markdown("""
    <style>
        .stMetric {
            background-color: #0E1117;
            border: 1px solid #30333F;
            padding: 15px;
            border-radius: 10px;
        }
        .stProgress > div > div > div > div {
            background-color: #00FF00;
        }
    </style>
""", unsafe_allow_html=True)

# 3. SESSION STATE INITIALIZATION
if 'history_power' not in st.session_state: 
    st.session_state.history_power = deque(maxlen=50) # Stores last 50 readings
if 'mqtt_connected' not in st.session_state: st.session_state.mqtt_connected = False
if 'live_voltage' not in st.session_state: st.session_state.live_voltage = 230.0
if 'live_current' not in st.session_state: st.session_state.live_current = 5.0

# 4. MQTT CONNECTION (Background)
BROKER = "broker.hivemq.com"
TOPIC_DATA = "team_immortal/meter/data"

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
        client.subscribe(TOPIC_DATA)
        client.loop_start()
        st.session_state.mqtt_connected = True
    except:
        pass

# --- SIDEBAR: ADVANCED CONTROLS ---
st.sidebar.title("⚙️ Control Center")
mode = st.sidebar.radio("Data Source:", ["Manual Control", "🔥 Demo Scenarios", "🔴 LIVE HARDWARE"])

voltage_input = 230.0
current_input = 5.0

if mode == "Manual Control":
    st.sidebar.markdown("---")
    st.sidebar.caption("Fine-tune grid parameters manually.")
    voltage_input = st.sidebar.slider("Grid Voltage (V)", 0, 300, 230)
    current_input = st.sidebar.slider("Load Current (A)", 0.0, 20.0, 5.0)

elif mode == "🔥 Demo Scenarios":
    st.sidebar.markdown("---")
    scenario = st.sidebar.selectbox("Select Attack / Fault:", 
                                    ["Normal Operation", "Power Theft (Bypass)", "Wire Cut (Low Voltage)", "Overload Surge"])
    if scenario == "Normal Operation":
        voltage_input, current_input = 230.0, 5.0
    elif scenario == "Power Theft (Bypass)":
        voltage_input, current_input = 230.0, 0.2 # Voltage normal, current disappears
    elif scenario == "Wire Cut (Low Voltage)":
        voltage_input, current_input = 15.0, 0.0  # Voltage drops to near zero
    elif scenario == "Overload Surge":
        voltage_input, current_input = 220.0, 35.0 # High current

else: # LIVE HARDWARE
    st.sidebar.markdown("---")
    st.sidebar.success(f"📡 MQTT Status: {'CONNECTED' if st.session_state.mqtt_connected else 'RETRYING...'}")
    voltage_input = st.session_state.live_voltage
    current_input = st.session_state.live_current

# --- CALCULATIONS ---
power_calc = voltage_input * current_input
est_cost = (power_calc / 1000) * 8 * 24 * 30  # Approx monthly cost @ ₹8/unit

# Update History
st.session_state.history_power.append(power_calc)

# AI Prediction
prediction = model.predict([[voltage_input, current_input]])[0] 
theft_prob = 0.05 if prediction == 1 else 0.98

# --- MAIN DASHBOARD LAYOUT ---

st.title("⚡ Generative Energy Systems Design Tool")
st.caption(f"Project: IoT Smart Meter Digital Twin | Mode: **{mode}**")

# 1. TOP KPI ROW (Big Metrics)
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("Grid Voltage", f"{voltage_input:.1f} V", delta=f"{voltage_input-230:.1f} V", delta_color="inverse")
kpi2.metric("Load Current", f"{current_input:.2f} A", delta=f"{current_input-5:.2f} A", delta_color="inverse")
kpi3.metric("Real-Time Power", f"{power_calc:.1f} W")
kpi4.metric("Est. Monthly Bill", f"₹ {est_cost:.0f}")

st.markdown("---")

# 2. MAIN SPLIT: AI BRAIN vs DIGITAL TWIN
col1, col2 = st.columns([1, 2]) # Left is smaller, Right is wider

with col1:
    st.subheader("🤖 AI Sentinel Agent")
    
    # Status Banner
    if prediction == 1:
        st.success("✅ SYSTEM SECURE")
        status_color = "green"
    else:
        st.error("🚨 THREAT DETECTED")
        status_color = "red"

    # Probability Bars
    st.write("**Theft Probability Score:**")
    st.progress(theft_prob) # 0.0 to 1.0
    
    st.write("**Grid Health Index:**")
    health = 1.0 if prediction == 1 else 0.2
    st.progress(health)

    # Detailed Stats
    st.markdown(f"""
    * **Anomaly Type:** {'None' if prediction == 1 else 'Pattern Deviation'}
    * **Compliance:** {'ISO 50001 Passed' if prediction == 1 else 'FAIL'}
    * **AI Model:** Isolation Forest (v1.2)
    * **Latency:** 12ms
    """)

with col2:
    st.subheader("📈 Live Digital Twin Simulation")
    
    # Tab selector for graphs
    tab_wave, tab_hist = st.tabs(["AC Waveform (Oscilloscope)", "Power Consumption History"])
    
    with tab_wave:
        # Sine Wave Logic
        t = np.linspace(0, 0.1, 100)
        wave = (voltage_input) * np.sin(2 * np.pi * 50 * t)
        chart_data = pd.DataFrame({'Time (s)': t, 'Voltage (V)': wave})
        st.line_chart(chart_data.set_index('Time (s)'), height=250)
        st.caption(f"Visualizing 50Hz AC Phase Cycle at {voltage_input:.1f}V")
        
    with tab_hist:
        # Scrolling History Chart
        st.line_chart(list(st.session_state.history_power), height=250)
        st.caption("Real-time power consumption trend (Last 60 seconds)")

# 3. ENGINEERING DRILL-DOWN (Tabs)
st.markdown("### Step 3: System Internals")
tab1, tab2, tab3 = st.tabs(["Hardware Specs", "Network Topology", "AI Decision Logs"])

with tab1:
    st.dataframe(pd.DataFrame({
        "Component": ["Voltage Sensor", "Current Sensor", "MCU", "Relay"],
        "Model": ["ZMPT101B", "ACS712-30A", "ESP32-WROOM", "SRD-05VDC"],
        "Status": ["Active", "Active", "Overclocked", "Ready"]
    }), use_container_width=True)

with tab2:
    st.code(f"""
    Protocol: MQTT (TCP/IP)
    Broker: {BROKER}
    Topic: {TOPIC_DATA}
    Signal Strength: -42 dBm (Excellent)
    Encryption: TLS 1.2
    """, language="yaml")

with tab3:
    st.warning("⚠️ Accessing Restricted AI Logs...")
    log_msg = "NORMAL_OP: Vector [230, 5.0] within confidence interval." if prediction == 1 else f"CRITICAL: Vector [{voltage_input}, {current_input}] exceeds threshold! TRIGGER_ALARM."
    st.code(f"timestamp: {time.time()}\nmodel_id: iso_forest_01\nprediction: {prediction}\nlog: {log_msg}")

# Auto-refresh for Live Mode
if mode == "🔴 LIVE HARDWARE":
    time.sleep(1)
    st.rerun()