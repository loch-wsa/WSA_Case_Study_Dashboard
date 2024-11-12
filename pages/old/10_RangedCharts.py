import streamlit as st
import pandas as pd
import os
import sys
from datetime import datetime
import plotly.graph_objects as go

# Add the utils directory to the Python path
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(utils_path)

# Import the function from ranged_charts.py
from ranged_charts import plot_sensors

def load_and_process_telemetry():
    """Load and process telemetry data"""
    df = pd.read_csv('data/Telemetry.csv', parse_dates=['TIMESTAMP'])
    df.columns = df.columns.str.lower()
    return df

if __name__ == "__main__":
    st.title('Telemetry and Threshold Visualization')

try:
    # Load telemetry and threshold data
    telemetry_df = load_and_process_telemetry()
    thresholds_df = pd.read_csv('data/Thresholds.csv')
    
    # Get available components (case-insensitive matching)
    telemetry_columns = {col.lower() for col in telemetry_df.columns} - {'timestamp'}
    threshold_components = {comp.lower() for comp in thresholds_df['Component'].unique()}
    available_components = sorted(telemetry_columns.intersection(threshold_components))
    
    # Component selector with multiselect checkboxes
    selected_components = st.multiselect(
        'Select Components to Display',
        options=available_components,
        default=['ptc109_pressure'] if 'ptc109_pressure' in available_components else []
    )
    
    # Show timestamp range
    st.sidebar.write("Data Range:")
    st.sidebar.write(f"Start: {telemetry_df['timestamp'].min()}")
    st.sidebar.write(f"End: {telemetry_df['timestamp'].max()}")
    
    # Filter telemetry data to selected components
    dataframes = {}
    for component in selected_components:
        # Ensure both telemetry and threshold data are available for the component
        component_data = telemetry_df[['timestamp', component]].dropna()
        if not component_data.empty:
            dataframes[component] = component_data.rename(columns={'timestamp': 'Timestamp', component: 'Value'})
    
    # Get thresholds for each component
    high_high_thresholds = {}
    high_thresholds = {}
    low_thresholds = {}
    low_low_thresholds = {}
    
    for component in selected_components:
        threshold = thresholds_df[thresholds_df['Component'].str.lower() == component]
        if not threshold.empty:
            high_high_thresholds[component] = threshold['HighHigh'].values[0]
            high_thresholds[component] = threshold['High'].values[0]
            low_thresholds[component] = threshold['Low'].values[0]
            low_low_thresholds[component] = threshold['LowLow'].values[0]
    
    # Plot each selected component with its thresholds
    for component in selected_components:
        highhigh = high_high_thresholds.get(component, 12)  # Default high high threshold
        high = high_thresholds.get(component, 9)  # Default high threshold
        low = low_thresholds.get(component, 5)    # Default low threshold
        lowlow = low_low_thresholds.get(component, 2)    # Default low low threshold
        
        st.subheader(f"{component.upper()} Sensor Readings")
       
        # Use the imported function to plot the component data
        plot_sensors({component: dataframes[component]}, high_high_threshold=highhigh, high_threshold=high, low_threshold=low, low_low_threshold=lowlow)
        
    # Display raw data in an expandable section
    with st.expander("View Raw Data"):
        st.write("Telemetry Data Sample (last 5 records):")
        st.dataframe(telemetry_df[['timestamp'] + selected_components].tail())
        
        st.write("\nThreshold Settings for Selected Components:")
        st.dataframe(thresholds_df[thresholds_df['Component'].str.lower().isin(selected_components)])

except Exception as e:
    st.error(f"Error loading or processing data: {str(e)}")
    st.write("Please check that both 'Telemetry.csv' and 'thresholds.csv' files are in the correct location")
    st.write("Error details:", str(e))
