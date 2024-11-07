import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Performance Analytics", page_icon="📈", layout="wide")

# Load the event and alarm data
@st.cache_data
def load_data():
    events_df = pd.read_csv('data/Events.csv', parse_dates=['timestamp'])
    alarms_df = pd.read_csv('data/Alarms.csv', parse_dates=['timestamp'])
    warnings_df = pd.read_csv('data/Warnings.csv', parse_dates=['timestamp'])
    sequences_df = pd.read_csv('data/Sequences.csv', parse_dates=['timestamp'])
    telemetry_df = pd.read_csv('data/Telemetry.csv', parse_dates=['TIMESTAMP'])
    
    return events_df, alarms_df, warnings_df, sequences_df, telemetry_df

events_df, alarms_df, warnings_df, sequences_df, telemetry_df = load_data()

st.title('📈 Performance Analytics')
st.markdown("""
    This page provides detailed analysis of system performance, maintenance cycles, and operational efficiency.
    Data is analyzed from system events, alarms, and telemetry to provide insights into operation.
""")

# Create tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs([
    "System Uptime", 
    "Production Efficiency",
    "Maintenance Cycles",
    "CIP Analysis"
])

with tab1:
    st.header("System Uptime Analysis")
    
    # Calculate system states and durations
    def calculate_uptime_metrics(sequences_df):
        states = ['PRODUCTION', 'WAIT', 'TAGOUT', 'SLEEP']
        state_durations = {}
        
        for state in states:
            state_events = sequences_df[sequences_df['message'].str.contains(state, na=False)]
            duration = len(state_events) * 10  # Assuming 10-second intervals between readings
            state_durations[state] = duration
            
        total_time = sum(state_durations.values())
        uptime_percentage = (state_durations.get('PRODUCTION', 0) / total_time * 100) if total_time > 0 else 0
        
        return state_durations, uptime_percentage

    state_durations, uptime_percentage = calculate_uptime_metrics(sequences_df)
    
    # Create metrics display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("System Uptime", f"{uptime_percentage:.1f}%")
    with col2:
        total_alarms = len(alarms_df)
        st.metric("Total Alarms", total_alarms)
    with col3:
        total_warnings = len(warnings_df)
        st.metric("Total Warnings", total_warnings)
    
    # Create state distribution pie chart
    fig_states = go.Figure(data=[go.Pie(
        labels=list(state_durations.keys()),
        values=list(state_durations.values()),
        hole=.3
    )])
    fig_states.update_layout(title="System State Distribution")
    st.plotly_chart(fig_states, use_container_width=True)

with tab2:
    st.header("Production Efficiency Metrics")
    
    # Calculate production metrics from telemetry
    production_metrics = {
        'Average Flow Rate': telemetry_df['FTR102_FLOWRATE'].mean(),
        'Max Flow Rate': telemetry_df['FTR102_FLOWRATE'].max(),
        'Average TMP': telemetry_df['FLU101_TMP'].mean(),
        'Average UV Dose': telemetry_df['UVM101_DOSE'].mean()
    }
    
    # Display production metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Avg Flow Rate", f"{production_metrics['Average Flow Rate']:.1f} L/min")
    with col2:
        st.metric("Max Flow Rate", f"{production_metrics['Max Flow Rate']:.1f} L/min")
    with col3:
        st.metric("Avg TMP", f"{production_metrics['Average TMP']:.2f} bar")
    with col4:
        st.metric("Avg UV Dose", f"{production_metrics['Average UV Dose']:.1f} mJ/cm²")
    
    # Create flow rate over time chart
    fig_flow = px.line(telemetry_df, x='TIMESTAMP', y='FTR102_FLOWRATE',
                       title='System Flow Rate Over Time')
    fig_flow.update_layout(yaxis_title="Flow Rate (L/min)")
    st.plotly_chart(fig_flow, use_container_width=True)

with tab3:
    st.header("Maintenance Cycle Tracking")
    
    # Analyze maintenance-related sequences
    maintenance_sequences = sequences_df[
        sequences_df['message'].str.contains('MEMBRANEDIRECTINTEGRITYTEST|MEMBRANEAIRSCOUR|PREFILTERFLUSHCLEAN', na=False)
    ]
    
    # Group maintenance events by type
    maintenance_counts = maintenance_sequences.groupby(
        maintenance_sequences['message'].apply(
            lambda x: 'Membrane DIT' if 'MEMBRANEDIRECTINTEGRITYTEST' in str(x)
            else 'Membrane Air Scour' if 'MEMBRANEAIRSCOUR' in str(x)
            else 'Pre-filter Flush'
        )
    ).size()
    
    # Create maintenance events bar chart
    fig_maintenance = go.Figure(data=[
        go.Bar(x=maintenance_counts.index, y=maintenance_counts.values)
    ])
    fig_maintenance.update_layout(
        title="Maintenance Events by Type",
        xaxis_title="Maintenance Type",
        yaxis_title="Number of Events"
    )
    st.plotly_chart(fig_maintenance, use_container_width=True)
    
    # Display maintenance timeline
    maintenance_sequences['Type'] = maintenance_sequences['message'].apply(
        lambda x: 'Membrane DIT' if 'MEMBRANEDIRECTINTEGRITYTEST' in str(x)
        else 'Membrane Air Scour' if 'MEMBRANEAIRSCOUR' in str(x)
        else 'Pre-filter Flush'
    )
    
    fig_timeline = px.scatter(maintenance_sequences, x='timestamp', y='Type',
                            title='Maintenance Event Timeline')
    st.plotly_chart(fig_timeline, use_container_width=True)

with tab4:
    st.header("Clean-in-Place (CIP) Cycle Analysis")
    
    # Analyze CIP sequences and outcomes
    cip_sequences = sequences_df[
        sequences_df['message'].str.contains('CLEAN|CIP|FLUSH', na=False)
    ]
    
    # Calculate CIP metrics
    total_cip = len(cip_sequences)
    avg_cip_duration = 30  # Placeholder - would calculate from actual duration data
    
    # Display CIP metrics
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Total CIP Cycles", total_cip)
    with col2:
        st.metric("Avg CIP Duration", f"{avg_cip_duration} min")
    
    # Create CIP timeline visualization
    fig_cip = px.scatter(cip_sequences, x='timestamp', y='message',
                        title='CIP Event Timeline')
    st.plotly_chart(fig_cip, use_container_width=True)
    
    # Display alarms during CIP
    cip_alarms = alarms_df[
        alarms_df['timestamp'].isin(cip_sequences['timestamp'])
    ]
    
    if not cip_alarms.empty:
        st.subheader("Alarms During CIP Cycles")
        st.dataframe(cip_alarms[['timestamp', 'message']])

    # Add line chart for PTC107 and PTC110 pressures
    st.subheader("Pressure Trends During CIP Cycles")
    
    # Filter telemetry data to plot PTC107 and PTC110
    fig_pressure = go.Figure()
    fig_pressure.add_trace(go.Scatter(
        x=telemetry_df['TIMESTAMP'],
        y=telemetry_df['FLM101_PRESSUREDIFF'],
        mode='lines',
        name='PTC107 Pressure',
        line=dict(width=2)
    ))
    fig_pressure.add_trace(go.Scatter(
        x=telemetry_df['TIMESTAMP'],
        y=telemetry_df['FLM102_PRESSUREDIFF'],
        mode='lines',
        name='PTC110 Pressure',
        line=dict(width=2)
    ))
    
    # Customize chart layout
    fig_pressure.update_layout(
        title="PTC107 and PTC110 Pressure Over Time",
        xaxis_title="Timestamp",
        yaxis_title="Pressure (bar)",
        legend_title="Pressure Sensor",
        height=400
    )
    
    # Display the line chart
    st.plotly_chart(fig_pressure, use_container_width=True)