import plotly.graph_objects as go
import pandas as pd
import numpy as np

def normalize_parameter(value, param_name, param_min, param_max, param_type='standard'):
    """
    Normalize parameter values based on their type and range
    
    param_type options:
    - 'standard': normalize from 0 to max (default)
    - 'centered': normalize around a center point (like pH)
    """
    if pd.isna(value) or pd.isna(param_min) or pd.isna(param_max):
        return 0
        
    try:
        value = float(value)
        param_min = float(param_min)
        param_max = float(param_max)
        
        if param_type == 'centered':
            # For parameters like pH that have an optimal middle range
            mid_point = (param_max + param_min) / 2
            max_distance = max(param_max - mid_point, mid_point - param_min)
            
            # Calculate how far the value is from the midpoint
            distance_from_mid = abs(value - mid_point)
            
            # Convert to a 0-1 scale where 1 is at the midpoint and 0 is at the extremes
            normalized = 1 - (distance_from_mid / max_distance)
            return max(0, min(1, normalized))
        else:
            # Standard normalization from min to max
            if param_max == param_min:
                return 1 if value >= param_max else 0
            normalized = (value - param_min) / (param_max - param_min)
            return max(0, min(1, normalized))
    except (TypeError, ValueError):
        return 0

def create_radar_chart(week_num, params, influent_data, treated_data, influent_ranges, treated_ranges, data_type='influent', show_comparison=False):
    """
    Create an enhanced radar chart with parameter ranges, hover information, and zoom functionality
    while maintaining existing normalization and comparison capabilities.
    """
    # Select appropriate dataframes based on data type
    ranges_df = treated_ranges if data_type == 'treated' else influent_ranges
    data_df = treated_data if data_type == 'treated' else influent_data
    
    # Filter data for selected parameters
    df_filtered = data_df[data_df['Influent Water'].isin(params)].copy()
    week_col = f'Week {week_num}'
    
    # Ensure we have the required columns
    required_columns = ['Influent Water', week_col]
    if not all(col in df_filtered.columns for col in required_columns):
        print(f"Missing required columns. Available columns: {df_filtered.columns}")
        return None
    
    values = df_filtered[week_col].values
    param_names = df_filtered['Influent Water'].tolist()
    
    # Define which parameters should use centered normalization
    centered_params = {'pH'}  # Add other parameters that should be centered
    
    # Prepare arrays for values
    actual_values = []
    normalized_values = []
    min_values = []
    max_values = []
    range_texts = []
    
    for param, value in zip(param_names, values):
        range_row = ranges_df[ranges_df['Influent Water'] == param]
        if len(range_row) > 0:
            min_val = range_row['Min'].iloc[0]
            max_val = range_row['Max'].iloc[0]
        else:
            # If no range data found, use the dataset min/max
            param_data = data_df[data_df['Influent Water'] == param]
            week_cols = [col for col in param_data.columns if col.startswith('Week')]
            min_val = param_data[week_cols].min().min()
            max_val = param_data[week_cols].max().max()
        
        try:
            min_val = float(min_val)
            max_val = float(max_val)
            actual_val = float(value)
            
            param_type = 'centered' if param in centered_params else 'standard'
            norm_val = normalize_parameter(actual_val, param, min_val, max_val, param_type)
            
            actual_values.append(actual_val)
            normalized_values.append(norm_val)
            min_values.append(min_val)
            max_values.append(max_val)
            range_texts.append(f"{min_val:.2f} - {max_val:.2f}")
        except (TypeError, ValueError) as e:
            print(f"Error processing {param}: {e}")
            actual_values.append(0)
            normalized_values.append(0)
            min_values.append(0)
            max_values.append(1)
            range_texts.append("N/A")
    
    # Create figure
    fig = go.Figure()
    
    # Load zoom settings
    try:
        settings_file = Path(__file__).parent.parent / "config" / "settings.json"
        if settings_file.exists():
            settings = json.loads(settings_file.read_text())
            zoom_levels = [
                settings["zoom_levels"]["level1"],
                settings["zoom_levels"]["level2"],
                settings["zoom_levels"]["level3"]
            ]
        else:
            zoom_levels = [1.5, 2.0, 4.0]  # defaults
    except Exception as e:
        print(f"Error loading settings: {e}")
        zoom_levels = [1.5, 2.0, 4.0]  # defaults
    
    # Add range area traces
    fig.add_trace(go.Scatterpolar(
        r=[1] * len(param_names) + [1],
        theta=param_names + [param_names[0]],
        fill='tonext',
        fillcolor='rgba(128, 128, 128, 0.2)',
        line=dict(color='rgba(128, 128, 128, 0.5)'),
        name='Acceptable Range',
        hoverinfo='skip'
    ))
    
    # Add main trace
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=param_names,
        name='Influent Water' if data_type == 'influent' else 'Treated Water',
        fill='toself',
        line=dict(color='#1f77b4' if data_type == 'influent' else '#2ca02c'),
        hovertemplate=(
            "<b>%{theta}</b><br>" +
            "Value: %{customdata:.2f}<br>" +
            "Range: %{text}<br>" +
            "<extra></extra>"
        ),
        customdata=actual_values,
        text=range_texts
    ))
    
    # Reorder traces to ensure treated water is on top if showing comparison
    if show_comparison:
        # Remove the main trace we just added
        fig.data = fig.data[:-1]
        
        # Get treated water data
        treated_filtered = treated_data[treated_data['Influent Water'].isin(params)]
        treated_values = treated_filtered[week_col].values
        treated_actual_values = []
        treated_normalized = []
        treated_range_texts = []
        
        for param, value in zip(param_names, treated_values):
            range_row = treated_ranges[treated_ranges['Influent Water'] == param]
            if len(range_row) > 0:
                min_val = range_row['Min'].iloc[0]
                max_val = range_row['Max'].iloc[0]
                
                try:
                    min_val = float(min_val)
                    max_val = float(max_val)
                    actual_val = float(value)
                    
                    param_type = 'centered' if param in centered_params else 'standard'
                    norm_val = normalize_parameter(actual_val, param, min_val, max_val, param_type)
                    
                    treated_actual_values.append(actual_val)
                    treated_normalized.append(norm_val)
                    treated_range_texts.append(f"{min_val:.2f} - {max_val:.2f}")
                except (TypeError, ValueError):
                    treated_actual_values.append(0)
                    treated_normalized.append(0)
                    treated_range_texts.append("N/A")
            else:
                treated_actual_values.append(0)
                treated_normalized.append(0)
                treated_range_texts.append("N/A")
        
        fig.add_trace(go.Scatterpolar(
            r=treated_normalized,
            theta=param_names,
            name='Treated Water',
            fill='toself',
            line=dict(color='#2ca02c'),
            hovertemplate=(
                "<b>%{theta}</b><br>" +
                "Value: %{customdata:.2f}<br>" +
                "Range: %{text}<br>" +
                "<extra></extra>"
            ),
            customdata=treated_actual_values,
            text=treated_range_texts
        ))
    
    # Update layout with zoom capabilities
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickmode='array',
                ticktext=['0%', '25%', '50%', '75%', '100%'],
                tickvals=[0, 0.25, 0.5, 0.75, 1],
            )
        ),
        showlegend=True,
        height=600,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(label="Reset View", method="relayout", args=[{"polar.radialaxis.range": [0, 1]}]),
                    dict(label=f"{zoom_levels[0]}×", method="relayout", 
                         args=[{"polar.radialaxis.range": [max(0, 1-1/zoom_levels[0]), 1]}]),
                    dict(label=f"{zoom_levels[1]}×", method="relayout", 
                         args=[{"polar.radialaxis.range": [max(0, 1-1/zoom_levels[1]), 1]}]),
                    dict(label=f"{zoom_levels[2]}×", method="relayout", 
                         args=[{"polar.radialaxis.range": [max(0, 1-1/zoom_levels[2]), 1]}])
                ],
                direction="right",
                x=0.1,
                y=1.1,
                pad={"r": 10, "t": 10}
            )
        ]
    )
    
    return fig

def create_parameter_table(week_num, params, data_df, ranges_df):
    """Create a formatted parameter table for display"""
    week_col = f'Week {week_num}'
    
    # Create combined display dataframe
    df_display = pd.merge(
        data_df[data_df['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]],
        ranges_df[['Influent Water', 'Min', 'Max', 'Estimated', 'Notes']],
        on='Influent Water',
        how='left'
    )
    
    # Format the display
    df_display = df_display.rename(columns={week_col: 'Current Value'})
    df_display['Range'] = df_display.apply(lambda x: f"{x['Min']} - {x['Max']}", axis=1)
    display_cols = ['Details', 'Current Value', 'Range', 'Estimated', 'Notes']
    
    return df_display[display_cols].set_index('Details')