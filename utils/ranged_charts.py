import plotly.graph_objects as go
import pandas as pd
import numpy as np
import streamlit as st


def plot_sensors(dataframes, high_high_threshold=12, high_threshold=9, low_threshold=5, low_low_threshold=2):
    """
    Plots readings from multiple sensors with shaded areas indicating unsafe ranges.

    Parameters:
    - dataframes (dict): Dictionary where keys are sensor names and values are DataFrames with 'Timestamp' and 'Value' columns.
    - high_threshold (float): Upper safe Value limit. Default is 9.
    - low_threshold (float): Lower safe Value limit. Default is 5.
    """
    fig = go.Figure()

    # Determine the full time range and y-axis range across all sensors
    all_timestamps = pd.concat([df['Timestamp'] for df in dataframes.values()])
    x_min, x_max = all_timestamps.min(), all_timestamps.max()

    all_values = pd.concat([df['Value'] for df in dataframes.values()])
    y_min, y_max = all_values.min() - 1, all_values.max() + 1

    # Adjust y_min and y_max if the max/min values don't exceed the thresholds
    top_y = max(y_max, high_high_threshold + 0.1)
    bottom_y = min(y_min, low_low_threshold - 0.1)

    # Plot each sensor's data
    for sensor_name, df in dataframes.items():
        fig.add_trace(go.Scatter(
            x=df['Timestamp'],
            y=df['Value'],
            mode='lines',
            name=sensor_name,
            line=dict(width=2)
        ))

    # Add shaded regions for unsafe Value values, setting bounds correctly
    # HIGH HIGH
    fig.add_shape(type="rect",
                  xref="x", yref="y",
                  x0=x_min, y0=top_y,
                  x1=x_max, y1=high_threshold,
                  fillcolor="red", opacity=0.3, line_width=0, layer="below")
                 
    # HIGH
    fig.add_shape(type="rect",
                  xref="x", yref="y",
                  x0=x_min, y0=high_threshold,
                  x1=x_max, y1=high_high_threshold,
                  fillcolor="yellow", opacity=0.3, line_width=0, layer="below")

    # LOW
    fig.add_shape(type="rect",
                  xref="x", yref="y",
                  x0=x_min, y0=low_threshold,
                  x1=x_max, y1=low_low_threshold,
                  fillcolor="yellow", opacity=0.3, line_width=0, layer="below")
    
    # LOW LOW 
    fig.add_shape(type="rect",
                  xref="x", yref="y",
                  x0=x_min, y0=low_low_threshold,
                  x1=x_max, y1=bottom_y,
                  fillcolor="red", opacity=0.3, line_width=0, layer="below")

    # Add horizontal dashed lines for the thresholds
    #HIGH HIGH
    fig.add_hline(y=high_high_threshold, line=dict(color="red", dash="dash"),
                  annotation_text="High High Threshold", annotation_position="top right")
    
    #HIGH
    fig.add_hline(y=high_threshold, line=dict(color="yellow", dash="dash"),
                  annotation_text="High Threshold", annotation_position="top right")
    
    # LOW 
    fig.add_hline(y=low_threshold, line=dict(color="yellow", dash="dash"),
                  annotation_text="Low Threshold", annotation_position="bottom right")

    # LOW LOW 
    fig.add_hline(y=low_low_threshold, line=dict(color="red", dash="dash"),
                  annotation_text="Low Low Threshold", annotation_position="bottom right")

    # Update layout for clear display
    fig.update_layout(
        title='Sensor Readings with Thresholds',
        xaxis_title='Time',
        yaxis_title='Value Level',
        xaxis=dict(range=[x_min, x_max]),
        yaxis=dict(range=[low_low_threshold, high_high_threshold]),
        showlegend=True,
        template="plotly_white"
    )

    # Display in Streamlit
    st.plotly_chart(fig)

def create_parameter_table(week_num, params, data_df, ranges_df):
    """Create a formatted parameter table with special handling for Value display"""
    week_col = f'Week {week_num}'
    
    # Create combined display dataframe
    df_display = pd.merge(
        data_df[data_df['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]],
        ranges_df[['Influent Water', 'Min', 'Max', 'Estimated', 'Notes']],
        on='Influent Water',
        how='left'
    )
    
    # Add Value difference column if Value is present
    if 'Value' in params:
        mask = df_display['Influent Water'] == 'Value'
        df_display.loc[mask, 'Value Difference'] = abs(df_display.loc[mask, week_col].astype(float) - 7.0)
    
    # Format the display
    df_display = df_display.rename(columns={week_col: 'Current Value'})
    df_display['Range'] = df_display.apply(lambda x: f"{x['Min']} - {x['Max']}", axis=1)
    
    # Define display columns with conditional Value difference
    display_cols = ['Details', 'Current Value']
    if 'Value' in params:
        display_cols.append('Value Difference')
    display_cols.extend(['Range', 'Estimated', 'Notes'])
    
    return df_display[display_cols].set_index('Details')