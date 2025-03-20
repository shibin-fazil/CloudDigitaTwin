import streamlit as st
import requests
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime

# Database setup
conn = sqlite3.connect('data.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS measurements (
    timestamp TEXT,
    height REAL,
    voltage REAL
)
''')
conn.commit()

# API endpoint configuration (replace with your actual server URL)
API_URL = "http://localhost:8000/api"

# Function to send data to server via API with basic error handling
def send_api_request(endpoint, payload):
    try:
        response = requests.post(f"{API_URL}/{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        st.error("API Connection Failed", icon="⚠️")
        return None

# Function to fetch data from server periodically and store in database
def fetch_and_store_data():
    data = send_api_request("fetch_data", {})
    if data:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        height = data.get('height', 0.0)
        voltage = data.get('voltage', 0.0)
        
        cursor.execute('INSERT INTO measurements (timestamp, height, voltage) VALUES (?, ?, ?)',
                       (timestamp, height, voltage))
        conn.commit()

# Layout setup using Streamlit columns
st.set_page_config(layout="wide")  # Set wide layout for better visualization

# Title section aligned in the top blank area with blue background
st.markdown(
    """
    <style>
    .title-container {
        background-color: #1E90FF; /* Blue background */
        padding: 15px;
        text-align: center;
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    </style>
    <div class="title-container">
        IIoT based Digital Twin process model controller
    </div>
    """,
    unsafe_allow_html=True,
)

# Divide the screen into 10 vertical parts: 3 for control panel, 7 for graphs
left_col, right_col = st.columns([3, 7])

# Left column for control panel (3/10 of the screen)
with left_col:
    st.sidebar.header("Navigation")
    if st.sidebar.button("Open Loop Control"):
        send_api_request("mode", {"mode": "open_loop"})
    if st.sidebar.button("Closed Loop Control"):
        send_api_request("mode", {"mode": "closed_loop"})
    if st.sidebar.button("Select the Model"):
        send_api_request("action", {"action": "model_select"})
    if st.sidebar.button("Tune Your Controller"):
        send_api_request("action", {"action": "controller_tuning"})

    # Parameter input fields
    st.subheader("Set Controller Parameters")
    setpoint = st.text_input("Set Point Height (m):", value="0.08")
    kp = st.text_input("Proportional Gain (Kp):", value="27")
    ki = st.text_input("Integral Gain (Ki):", value="0.9")
    kd = st.text_input("Derivative Gain (Kd):", value="0.05")

    if st.button("Enter"):
        payload = {
            "setpoint": float(setpoint),
            "kp": float(kp),
            "ki": float(ki),
            "kd": float(kd)
        }
        send_api_request("parameters", payload)

    # Buttons for model control
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Start All Models"):
            send_api_request("start_models", {})
    with col2:
        if st.button("Stop All Models"):
            send_api_request("stop_models", {})

    # Checkboxes for model plots
    st.subheader("Select your Model")
    first_principle_plot = st.checkbox("First Principle Model")
    real_system_plot = st.checkbox("Real System Only")
    pinn_model_plot = st.checkbox("PINN Model Only")
    tf_model_plot = st.checkbox("Transfer Function")
    data_driven_model_plot = st.checkbox("Data Driven Model Only")

# Right column for real-time plots (7/10 of the screen)
with right_col:
    # Retrieve stored data from SQL database for plotting
    df = pd.read_sql_query('SELECT * FROM measurements ORDER BY timestamp ASC', conn)

    # Height vs Time plot
    fig1, ax1 = plt.subplots(figsize=(12, 4))  # Extend graph horizontally
    if not df.empty:
        ax1.plot(pd.to_datetime(df['timestamp']), df['height'], marker='o', linestyle='-', color='blue', label="First Principle Model" if first_principle_plot else "")
        ax1.plot(pd.to_datetime(df['timestamp']), df['height'], marker='x', linestyle='-', color='orange', label="Real System Only" if real_system_plot else "")
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Height (m)')
        ax1.set_title('Height (m) vs Time')
        ax1.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
    else:
        ax1.set_title('Height (m) vs Time')
        ax1.set_xlabel('Time')
        ax1.set_ylabel('Height (m)')
    
    st.pyplot(fig1)

    # Voltage vs Time plot
    fig2, ax2 = plt.subplots(figsize=(12, 4))  # Extend graph horizontally
    if not df.empty:
        ax2.plot(pd.to_datetime(df['timestamp']), df['voltage'], marker='o', linestyle='-', color='blue', label="First Principle Model" if first_principle_plot else "")
        ax2.plot(pd.to_datetime(df['timestamp']), df['voltage'], marker='x', linestyle='-', color='orange', label="Real System Only" if real_system_plot else "")
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Voltage (V)')
        ax2.set_title('Voltage (V) vs Time')
        ax2.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()
    else:
        ax2.set_title('Voltage (V) vs Time')
        ax2.set_xlabel('Time')
        ax2.set_ylabel('Voltage (V)')
    
    st.pyplot(fig2)

# Button to manually fetch new data
if left_col.button("Fetch Latest Data"):
    fetch_and_store_data()

# Footer with copyright information at the bottom of the page
st.markdown(
    """
    ---
    
    © IIoT liked Digital Twin process model controller developed in National Institute of Technology Calicut.
    
"""

)
