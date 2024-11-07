import plotly.graph_objects as go
import pandas as pd
import numpy as np

def normalize_parameter(value, param_name, param_min, param_max, param_type='standard'):
    """
    Normalize parameter values based on their type and range
    
    param_type options:
    - 'standard': normalize from max to 0 (default, for parameters like turbidity)
    - 'centered': normalize as difference from center point (like pH)
    - 'ph_difference': special handling for pH to show difference from neutral (7)
    """
    if pd.isna(value) or pd.isna(param_min) or pd.isna(param_max):
        return 0
        
    try:
        if param_type == 'ph_difference':
            # For pH, calculate absolute difference from 7 (neutral)
            # Max possible difference is from neutral to either extreme
            neutral_ph = 7.0
            max_possible_diff = max(abs(param_max - neutral_ph), abs(param_min - neutral_ph))
            actual_diff = abs(value - neutral_ph)
            # Normalize to 0-1 scale where 0 = neutral (good) and 1 = maximum difference (bad)
            return min(actual_diff / max_possible_diff, 1)
        elif param_type == 'centered':
            # For other centered parameters
            mid_point = (param_max + param_min) / 2
            max_distance = max(param_max - mid_point, mid_point - param_min)
            normalized = abs(value - mid_point) / max_distance
            return max(0, min(1, normalized))
        else:
            # Standard normalization from max to 0 (inverse of original)
            if param_max == param_min:
                return 0 if value >= param_max else 1
            normalized = (value - param_min) / (param_max - param_min)
            return max(0, min(1, normalized))
    except (TypeError, ValueError):
        return 0

def get_zoom_ranges(param_types, zoom_level):
    """
    Calculate zoom ranges based on parameter types and zoom level
    """
    zoom_ranges = {}
    for param, param_type in param_types.items():
        if param_type in ['centered', 'ph_difference']:
            # For centered parameters and pH, zoom into the middle (good values)
            margin = 0.5 / zoom_level
            zoom_ranges[param] = [0.5 - margin, 0.5 + margin]
        else:
            # For standard parameters, zoom towards 0 (good values)
            zoom_ranges[param] = [0, 1/zoom_level]
    return zoom_ranges

def create_radar_chart(week_num, params, influent_data, treated_data, influent_ranges, treated_ranges, data_type='influent', show_comparison=False):
    """
    Create an enhanced radar chart with parameter ranges, hover information, and improved zoom functionality
    that handles pH differently by showing difference from neutral (7).
    """
    # Select appropriate dataframes based on data type
    ranges_df = treated_ranges if data_type == 'treated' else influent_ranges
    data_df = treated_data if data_type == 'treated' else influent_data
    
    # Filter data for selected parameters
    df_filtered = data_df[data_df['Influent Water'].isin(params)]
    week_col = f'Week {week_num}'
    values = df_filtered[week_col].values
    param_names = df_filtered['Influent Water'].tolist()
    
    # Define parameter types with special handling for pH
    param_types = {
        'pH': 'ph_difference',  # Special type for pH
        # Add other centered parameters here
    }
    # Default to 'standard' for unlisted parameters
    param_types.update({param: 'standard' for param in param_names if param not in param_types})
    
    # Prepare arrays for values
    actual_values = []
    normalized_values = []
    min_values = []
    max_values = []
    hover_texts = []
    
    for param, value in zip(param_names, values):
        range_row = ranges_df[ranges_df['Influent Water'] == param]
        if len(range_row) > 0:
            min_val = float(range_row['Min'].values[0])
            max_val = float(range_row['Max'].values[0])
        else:
            param_data = data_df[data_df['Influent Water'] == param]
            week_cols = [col for col in param_data.columns if col.startswith('Week')]
            min_val = min([float(param_data[col].min()) for col in week_cols])
            max_val = max([float(param_data[col].max()) for col in week_cols])
        
        try:
            actual_val = float(value)
            param_type = param_types.get(param, 'standard')
            norm_val = normalize_parameter(actual_val, param, min_val, max_val, param_type)
            
            actual_values.append(actual_val)
            normalized_values.append(norm_val)
            min_values.append(min_val)
            max_values.append(max_val)
            
            # Create custom hover text for pH
            if param == 'pH':
                diff_from_neutral = abs(actual_val - 7.0)
                hover_texts.append(f"pH: {actual_val:.2f}<br>Difference from neutral: ±{diff_from_neutral:.2f}")
            else:
                hover_texts.append(f"{min_val:.2f} - {max_val:.2f}")
                
        except (TypeError, ValueError):
            actual_values.append(0)
            normalized_values.append(0)
            min_values.append(0)
            max_values.append(1)
            hover_texts.append("N/A")
    
    # Create figure
    fig = go.Figure()
    
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
    
    # Add main trace with custom hover template for pH
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=param_names,
        name='Influent Water' if data_type == 'influent' else 'Treated Water',
        fill='toself',
        line=dict(color='#8B4513' if data_type == 'influent' else '#1E90FF'),
        hovertemplate=(
            "<b>%{theta}</b><br>" +
            "%{text}<br>" +
            "Quality: %{r:.0%}<br>" +
            "<extra></extra>"
        ),
        customdata=actual_values,
        text=hover_texts
    ))
    
    # Add comparison trace if requested
    if show_comparison:
        treated_filtered = treated_data[treated_data['Influent Water'].isin(params)]
        treated_values = treated_filtered[week_col].values
        treated_actual_values = []
        treated_normalized = []
        treated_hover_texts = []
        
        for param, value in zip(param_names, treated_values):
            range_row = treated_ranges[treated_ranges['Influent Water'] == param]
            if len(range_row) > 0:
                min_val = float(range_row['Min'].values[0])
                max_val = float(range_row['Max'].values[0])
            else:
                continue
                
            try:
                actual_val = float(value)
                param_type = param_types.get(param, 'standard')
                norm_val = normalize_parameter(actual_val, param, min_val, max_val, param_type)
                
                treated_actual_values.append(actual_val)
                treated_normalized.append(norm_val)
                
                if param == 'pH':
                    diff_from_neutral = abs(actual_val - 7.0)
                    treated_hover_texts.append(f"pH: {actual_val:.2f}<br>Difference from neutral: ±{diff_from_neutral:.2f}")
                else:
                    treated_hover_texts.append(f"{min_val:.2f} - {max_val:.2f}")
                    
            except (TypeError, ValueError):
                treated_actual_values.append(0)
                treated_normalized.append(0)
                treated_hover_texts.append("N/A")
        
        fig.add_trace(go.Scatterpolar(
            r=treated_normalized,
            theta=param_names,
            name='Treated Water',
            fill='toself',
            line=dict(color='#1E90FF'),
            hovertemplate=(
                "<b>%{theta}</b><br>" +
                "%{text}<br>" +
                "Quality: %{r:.0%}<br>" +
                "<extra></extra>"
            ),
            customdata=treated_actual_values,
            text=treated_hover_texts
        ))
    
    # Create zoom buttons
    zoom_levels = [1.5, 2, 4]
    buttons = [dict(label="Reset Zoom", method="relayout", args=[{"polar.radialaxis.range": [0, 1]}])]
    
    for zoom_level in zoom_levels:
        zoom_ranges = get_zoom_ranges(param_types, zoom_level)
        buttons.append(dict(
            label=f"{zoom_level}x Zoom",
            method="relayout",
            args=[{"polar.radialaxis.range": [0, 1/zoom_level]}]
        ))
    
    # Update layout with custom ticktext for pH scale
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickmode='array',
                ticktext=['Neutral/Optimal', 'Small Deviation', 'Moderate', 'Large', 'Extreme'],
                tickvals=[0, 0.25, 0.5, 0.75, 1],
            )
        ),
        showlegend=True,
        height=600,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=buttons,
                direction="right",
                x=0.1,
                y=1.1,
                pad={"r": 10, "t": 10}
            )
        ]
    )
    
    return fig

def create_parameter_table(week_num, params, data_df, ranges_df):
    """Create a formatted parameter table with special handling for pH display"""
    week_col = f'Week {week_num}'
    
    # Create combined display dataframe
    df_display = pd.merge(
        data_df[data_df['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]],
        ranges_df[['Influent Water', 'Min', 'Max', 'Estimated', 'Notes']],
        on='Influent Water',
        how='left'
    )
    
    # Add pH difference column if pH is present
    if 'pH' in params:
        mask = df_display['Influent Water'] == 'pH'
        df_display.loc[mask, 'pH Difference'] = abs(df_display.loc[mask, week_col].astype(float) - 7.0)
    
    # Format the display
    df_display = df_display.rename(columns={week_col: 'Current Value'})
    df_display['Range'] = df_display.apply(lambda x: f"{x['Min']} - {x['Max']}", axis=1)
    
    # Define display columns with conditional pH difference
    display_cols = ['Details', 'Current Value']
    if 'pH' in params:
        display_cols.append('pH Difference')
    display_cols.extend(['Range', 'Estimated', 'Notes'])
    
    return df_display[display_cols].set_index('Details')