import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

# Add the utils directory to the Python path
utils_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'utils'))
sys.path.append(utils_path)

def load_and_process_telemetry():
    """Load and process telemetry data"""
    df = pd.read_csv('data/Telemetry.csv', parse_dates=['TIMESTAMP'])
    df.columns = df.columns.str.lower()
    return df

def create_combined_chart(telemetry_df, thresholds_df, component):
    """Create a combined chart showing both telemetry data and thresholds."""
    fig = go.Figure()
    
    # Get component data
    component_lower = component.lower()
    telemetry_data = telemetry_df[['timestamp', component_lower]].dropna()
    component_thresholds = thresholds_df[thresholds_df['Component'].str.lower() == component_lower]
    
    # Calculate y-axis range including both telemetry and thresholds
    y_values = [telemetry_data[component_lower].min(), telemetry_data[component_lower].max()]
    threshold_cols = ['LowLow', 'Low', 'OpLow', 'OpHigh', 'High', 'HighHigh']
    for col in threshold_cols:
        vals = component_thresholds[col].dropna()
        if not vals.empty:
            y_values.extend([vals.min(), vals.max()])
    
    y_min, y_max = min(y_values), max(y_values)
    y_range = y_max - y_min
    y_min -= y_range * 0.1  # Add 10% padding
    y_max += y_range * 0.1
    
    # Get time range for threshold lines
    x_min, x_max = telemetry_data['timestamp'].min(), telemetry_data['timestamp'].max()
    
    # Add threshold regions and lines
    for _, row in component_thresholds.iterrows():
        # Add LowLow region
        if pd.notna(row['LowLow']) and pd.notna(row['Low']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['LowLow'], row['LowLow']],
                fill='tonexty',
                fillcolor='rgba(255,0,0,0.2)',
                line=dict(color='red', width=1, dash='dash'),
                name='LowLow Threshold',
                showlegend=True
            ))
        
        # Add Low region
        if pd.notna(row['Low']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['Low'], row['Low']],
                line=dict(color='orange', width=1, dash='dash'),
                name='Low Threshold',
                showlegend=True
            ))
        
        # Add High region
        if pd.notna(row['High']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['High'], row['High']],
                line=dict(color='orange', width=1, dash='dash'),
                name='High Threshold',
                showlegend=True
            ))
        
        # Add HighHigh region
        if pd.notna(row['HighHigh']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['HighHigh'], row['HighHigh']],
                line=dict(color='red', width=1, dash='dash'),
                name='HighHigh Threshold',
                showlegend=True
            ))
        
        # Add OpLow line
        if pd.notna(row['OpLow']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['OpLow'], row['OpLow']],
                line=dict(color='green', width=2),
                name='OpLow Threshold',
                showlegend=True
            ))
        
        # Add OpHigh line
        if pd.notna(row['OpHigh']):
            fig.add_trace(go.Scatter(
                x=[x_min, x_max],
                y=[row['OpHigh'], row['OpHigh']],
                line=dict(color='green', width=2),
                name='OpHigh Threshold',
                showlegend=True
            ))
    
    # Add telemetry data
    fig.add_trace(go.Scatter(
        x=telemetry_data['timestamp'],
        y=telemetry_data[component_lower],
        mode='lines',
        name='Telemetry Data',
        line=dict(color='blue', width=2),
        showlegend=True
    ))
    
    # Update layout
    fig.update_layout(
        title=f'Telemetry and Thresholds for {component}',
        xaxis_title='Time',
        yaxis_title=component,
        height=800,
        showlegend=True,
        yaxis=dict(range=[y_min, y_max]),
        xaxis=dict(range=[x_min, x_max]),
        hovermode='x unified'
    )
    
    return fig

def main():
    st.title('Telemetry and Threshold Visualization')
    
    try:
        # Load data
        telemetry_df = load_and_process_telemetry()
        thresholds_df = pd.read_csv('data/Thresholds.csv')
        
        # Get available components (case-insensitive matching)
        telemetry_columns = {col.lower() for col in telemetry_df.columns} - {'timestamp'}
        threshold_components = {comp.lower() for comp in thresholds_df['Component'].unique()}
        available_components = sorted(telemetry_columns.intersection(threshold_components))
        
        # Default to ctr101_conductivity if available
        default_index = available_components.index('ctr101_conductivity') if 'ctr101_conductivity' in available_components else 0
        
        # Component selector
        selected_component = st.selectbox(
            'Select Component',
            available_components,
            index=default_index
        )
        
        # Show timestamp range
        st.sidebar.write("Data Range:")
        st.sidebar.write(f"Start: {telemetry_df['timestamp'].min()}")
        st.sidebar.write(f"End: {telemetry_df['timestamp'].max()}")
        
        # Create and display combined chart
        fig = create_combined_chart(telemetry_df, thresholds_df, selected_component)
        st.plotly_chart(fig, use_container_width=True)
        
        # Display raw data in expandable section
        with st.expander("View Raw Data"):
            st.write("Telemetry Data Sample (last 5 records):")
            st.dataframe(telemetry_df[['timestamp', selected_component.lower()]].tail())
            
            st.write("\nThreshold Settings:")
            st.dataframe(thresholds_df[thresholds_df['Component'].str.lower() == selected_component.lower()])
            
    except Exception as e:
        st.error(f"Error loading or processing data: {str(e)}")
        st.write("Please check that both 'Telemetry.csv' and 'thresholds.csv' files are in the correct location")
        st.write("Error details:", str(e))

if __name__ == "__main__":
    main()