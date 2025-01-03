import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Sensor Data Overview", page_icon="📊", layout="wide")

# Load telemetry data
@st.cache_data
def load_telemetry_data():
    # Explicitly specify parse_dates and date parser
    telemetry_df = pd.read_csv('data/Telemetry.csv')
    # Convert TIMESTAMP column to datetime
    telemetry_df['TIMESTAMP'] = pd.to_datetime(telemetry_df['TIMESTAMP'], dayfirst=True)
    return telemetry_df

# Define readable names for sensors
SENSOR_NAMES = {
    'FLM101_PRESSUREDIFF': 'Pre-Filter 1 Pressure Differential',
    'FLM102_PRESSUREDIFF': 'Pre-Filter 2 Pressure Differential',
    'FLM103_PRESSUREDIFF': 'Pre-Filter 3 Pressure Differential',
    'FLM105_PRESSUREDIFF': 'Carbon Filter Pressure Differential',
    'FLU101_TMP': 'Membrane Trans-membrane Pressure',
    'FLU101_TCSF': 'Membrane Temperature Corrected Specific Flux',
    'UVM101_DOSE': 'UV Disinfection Dose',
    'CTR101_CONDUCTIVITY': 'Input Water Conductivity',
    'CTR101_TEMPERATURE': 'Input Water Temperature',
    'TRB101_TURBIDITY': 'Input Water Turbidity',
    'TRB101_TEMPERATURE': 'Input Water Temperature',
    'TRB102_TURBIDITY': 'Output Water Turbidity',
    'TRB102_TEMPERATURE': 'Output Water Temperature'
}

# Define units for sensors
SENSOR_UNITS = {
    'FLM101_PRESSUREDIFF': 'bar',
    'FLM102_PRESSUREDIFF': 'bar',
    'FLM103_PRESSUREDIFF': 'bar',
    'FLM105_PRESSUREDIFF': 'bar',
    'FLU101_TMP': 'bar',
    'FLU101_TCSF': 'lmh/bar',
    'UVM101_DOSE': 'mJ/cm²',
    'CTR101_CONDUCTIVITY': 'µS/cm',
    'CTR101_TEMPERATURE': '°C',
    'TRB101_TURBIDITY': 'NTU',
    'TRB101_TEMPERATURE': '°C',
    'TRB102_TURBIDITY': 'NTU',
    'TRB102_TEMPERATURE': '°C'
}

telemetry_df = load_telemetry_data()

# Title and description
st.title("📊 Sensor Data Overview")
st.markdown("""
    This page provides line charts for various sensor measurements over time. Each chart represents data from a specific sensor.
    Use the controls below to adjust the time range and view specific periods of interest.
""")

# Time range controls in sidebar
st.sidebar.title("Time Range Controls")

# Preset time range buttons
time_ranges = {
    "Last Day": timedelta(days=1),
    "Last Week": timedelta(days=7),
    "Last Month": timedelta(days=30),
    "Last Year": timedelta(days=365),
    "Custom Range": None
}

selected_range = st.sidebar.radio("Select Time Range", list(time_ranges.keys()))

# Convert to pandas timestamp for calculations
latest_date = telemetry_df['TIMESTAMP'].max()
earliest_date = telemetry_df['TIMESTAMP'].min()

# Date range selector (only shown for custom range)
if selected_range == "Custom Range":
    start_date = st.sidebar.date_input(
        "Start Date",
        earliest_date.date()
    )
    end_date = st.sidebar.date_input(
        "End Date",
        latest_date.date()
    )
    start_datetime = pd.Timestamp(start_date)
    end_datetime = pd.Timestamp(end_date) + pd.Timedelta(days=1)
else:
    end_datetime = latest_date
    start_datetime = end_datetime - pd.Timedelta(time_ranges[selected_range])

# Filter data based on selected time range
filtered_df = telemetry_df[
    (telemetry_df['TIMESTAMP'] >= start_datetime) & 
    (telemetry_df['TIMESTAMP'] <= end_datetime)
].copy()

# Format timestamps based on selected range
if selected_range == "Last Day":
    filtered_df['display_time'] = filtered_df['TIMESTAMP'].dt.strftime('%H:%M')
elif selected_range == "Last Week":
    filtered_df['display_time'] = filtered_df['TIMESTAMP'].dt.strftime('%a %H:%M')
elif selected_range == "Last Month":
    filtered_df['display_time'] = filtered_df['TIMESTAMP'].dt.strftime('%d-%b')
else:
    filtered_df['display_time'] = filtered_df['TIMESTAMP'].dt.strftime('%d-%b-%Y')

# Define the tags to be plotted
tags = [
    'FLM101_PRESSUREDIFF', 'FLM102_PRESSUREDIFF', 'FLM103_PRESSUREDIFF', 'FLM105_PRESSUREDIFF',
    'FLU101_TMP', 'FLU101_TCSF',
    'UVM101_DOSE',
    'CTR101_CONDUCTIVITY', 'CTR101_TEMPERATURE',
    'TRB101_TURBIDITY', 'TRB101_TEMPERATURE',
    'TRB102_TURBIDITY', 'TRB102_TEMPERATURE'
]

# Plot each tag as a line chart
for tag in tags:
    if tag in filtered_df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filtered_df['display_time'],
            y=filtered_df[tag],
            mode='lines',
            name=SENSOR_NAMES.get(tag, tag),
            line=dict(width=2)
        ))
        
        # Customize chart layout
        fig.update_layout(
            title=SENSOR_NAMES.get(tag, tag),
            xaxis_title="Time",
            yaxis_title=f"{SENSOR_NAMES.get(tag, tag)} ({SENSOR_UNITS.get(tag, '')})",
            height=400,
            showlegend=False
        )
        
        # Update x-axis layout based on time range
        if selected_range in ["Last Day", "Last Week"]:
            fig.update_xaxes(nticks=24)
        
        # Display each chart
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"Column {tag} is missing in telemetry data.")

# Add information about data timespan
st.sidebar.markdown("---")
st.sidebar.markdown(f"**Data Range:**  \n{start_datetime.strftime('%Y-%m-%d %H:%M')} to {end_datetime.strftime('%Y-%m-%d %H:%M')}")

# Print data info for debugging
st.sidebar.markdown("---")
if st.sidebar.checkbox("Show Debug Info"):
    st.sidebar.write("Data Types:")
    st.sidebar.write(telemetry_df.dtypes)
    st.sidebar.write("Date Range:")
    st.sidebar.write(f"Earliest: {earliest_date}")
    st.sidebar.write(f"Latest: {latest_date}")