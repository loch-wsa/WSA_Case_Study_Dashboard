import plotly.graph_objects as go
import pandas as pd
import numpy as np

def normalize_parameter(value, param, min_val, max_val, param_type='standard'):
    """
    Normalize parameter values with special handling for pH.
    """
    # Safely convert param to string and handle None case
    param_str = str(param) if param is not None else ''
    
    if param_str.upper() == 'PH':  # Make case-insensitive
        try:
            value = float(value)
            # For pH, calculate difference from neutral (7)
            diff_from_neutral = abs(value - 7.0)
            # Maximum possible deviation is max(|max_val - 7|, |min_val - 7|)
            max_deviation = max(abs(max_val - 7), abs(min_val - 7))
            # Normalize the difference
            return diff_from_neutral / max_deviation if max_deviation != 0 else 0
        except (ValueError, TypeError):
            return 0
    else:
        try:
            # Handle special string values
            if isinstance(value, str):
                if value.startswith('<'):
                    # Extract number from strings like '<0.001'
                    value = float(value.replace('<', ''))
                elif value == 'N/R':
                    return 0
                elif 'LINT' in value:
                    # Handle '<5 LINT' case
                    value = float(value.split()[0].replace('<', ''))
            
            value = float(value)
            range_size = max_val - min_val
            return (value - min_val) / range_size if range_size != 0 else 0
        except (ValueError, TypeError):
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
    # Select appropriate dataframes based on data type
    ranges_df = treated_ranges if data_type == 'treated' else influent_ranges
    data_df = treated_data if data_type == 'treated' else influent_data
    
    # Filter data for selected parameters and sort them alphabetically
    df_filtered = data_df[data_df['Influent Water'].isin(params)].copy()
    df_filtered = df_filtered.sort_values('Influent Water')
    week_col = f'Week {week_num}'
    
    # Get ordered parameter names
    param_names = df_filtered['Influent Water'].tolist()
    
    # Ensure the radar chart closes by duplicating the first point at the end
    param_names = param_names + [param_names[0]]
    
    # Check for missing values
    missing_params = []
    values = []
    for idx, row in df_filtered.iterrows():
        param = row['Influent Water']
        value = row[week_col]
        
        # Handle various types of missing values
        if pd.isna(value) or value == 'N/R' or str(value).strip() == '':
            values.append(0)
            missing_params.append(param)
        else:
            values.append(value)
    
    # Add the first value again at the end to close the shape
    values = np.array(values)
    values = np.append(values, values[0])
    
    # Create warning message if there are missing values
    warning_message = None
    if missing_params:
        warning_message = f"Warning: Missing values for Week {week_num} in parameters: {', '.join(missing_params)}"
    
    # Define parameter types with special handling for pH
    param_types = {
        'PH': 'ph_difference',  # Special type for pH
    }
    # Default to 'standard' for unlisted parameters
    param_types.update({param: 'standard' for param in param_names[:-1] if param not in param_types})
    
    # Prepare arrays for values
    actual_values = []
    normalized_values = []
    min_values = []
    max_values = []
    hover_texts = []
    
    for param, value in zip(param_names[:-1], values[:-1]):  # Process original points only
        try:
            range_row = ranges_df[ranges_df['Influent Water'] == param]
            if len(range_row) > 0:
                min_val = float(range_row['Min'].values[0])
                max_val = float(range_row['Max'].values[0])
            else:
                param_data = data_df[data_df['Influent Water'] == param]
                week_cols = [col for col in param_data.columns if col.startswith('Week')]
                numeric_values = []
                
                for col in week_cols:
                    try:
                        val = param_data[col].iloc[0] if not param_data[col].empty else None
                        if val is None or val == 'N/R':
                            continue
                            
                        if isinstance(val, str):
                            if val.startswith('<'):
                                val = float(val.replace('<', ''))
                            elif 'LINT' in val:
                                val = float(val.split()[0].replace('<', ''))
                            else:
                                try:
                                    val = float(val)
                                except ValueError:
                                    continue
                        numeric_values.append(float(val))
                    except (IndexError, ValueError):
                        continue
                
                if numeric_values:
                    min_val = min(numeric_values)
                    max_val = max(numeric_values)
                else:
                    min_val = 0
                    max_val = 1
            
            # Process the actual value
            try:
                if isinstance(value, str):
                    if value.startswith('<'):
                        actual_val = float(value.replace('<', ''))
                    elif value == 'N/R' or value.strip() == '':
                        actual_val = 0
                    elif 'LINT' in value:
                        actual_val = float(value.split()[0].replace('<', ''))
                    else:
                        actual_val = float(value)
                else:
                    actual_val = float(value) if value is not None else 0
            except (ValueError, TypeError):
                actual_val = 0
            
            norm_val = normalize_parameter(actual_val, param, min_val, max_val)
            
            actual_values.append(actual_val)
            normalized_values.append(norm_val)
            min_values.append(min_val)
            max_values.append(max_val)
            
            # Create hover text
            param_str = str(param) if param is not None else ''
            if param_str.upper() == 'PH':
                if actual_val == 0:
                    hover_texts.append(f"pH: No data available")
                else:
                    diff_from_neutral = abs(actual_val - 7.0)
                    max_deviation = max(abs(max_val - 7), abs(min_val - 7))
                    hover_texts.append(
                        f"pH: {actual_val:.2f}<br>" +
                        f"Difference from neutral: ±{diff_from_neutral:.2f}<br>" +
                        f"Max allowed deviation: ±{max_deviation:.2f}"
                    )
            else:
                if actual_val == 0 and param in missing_params:
                    hover_texts.append(f"{param}: No data available")
                else:
                    hover_texts.append(
                        f"{param}<br>" +
                        f"Value: {actual_val:.2f}<br>" +
                        f"Range: {min_val:.2f} - {max_val:.2f}"
                    )
                
        except Exception as e:
            print(f"Error processing parameter {param}: {e}")
            actual_values.append(0)
            normalized_values.append(0)
            min_values.append(0)
            max_values.append(1)
            hover_texts.append(f"{param}: Error processing data")
    
    # Add the first point's data to the end to close the shape
    actual_values.append(actual_values[0])
    normalized_values.append(normalized_values[0])
    hover_texts.append(hover_texts[0])
    
    # Create figure
    fig = go.Figure()
    
    # Add main trace
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=param_names,
        name='Influent Water' if data_type == 'influent' else 'Treated Water',
        fill='toself',
        line=dict(
            color='#8B4513' if data_type == 'influent' else '#1E90FF',
            shape='linear'  # Ensure linear connections between points
        ),
        connectgaps=True,  # Connect any gaps in the data
        hovertemplate=(
            "<b>%{theta}</b><br>" +
            "%{text}<br>" +
            "Quality: %{customdata:.0%}<br>" +
            "<extra></extra>"
        ),
        customdata=[1 - v for v in normalized_values],
        text=hover_texts
    ))
    
    # Add comparison trace if requested
    if show_comparison:
        treated_filtered = treated_data[treated_data['Influent Water'].isin(params)].copy()
        treated_filtered = treated_filtered.sort_values('Influent Water')
        treated_values = treated_filtered[week_col].values
        treated_actual_values = []
        treated_normalized = []
        treated_hover_texts = []
        
        for param, value in zip(param_names[:-1], treated_values):  # Process original points only
            range_row = treated_ranges[treated_ranges['Influent Water'] == param]
            if len(range_row) > 0:
                min_val = float(range_row['Min'].values[0])
                max_val = float(range_row['Max'].values[0])
            else:
                continue
                
            try:
                if isinstance(value, str):
                    if value.startswith('<'):
                        actual_val = float(value.replace('<', ''))
                    elif value == 'N/R':
                        continue
                    elif 'LINT' in value:
                        actual_val = float(value.split()[0].replace('<', ''))
                    else:
                        actual_val = float(value)
                else:
                    actual_val = float(value)
                
                norm_val = normalize_parameter(actual_val, param, min_val, max_val)
                
                treated_actual_values.append(actual_val)
                treated_normalized.append(norm_val)
                
                param_str = str(param) if param is not None else ''
                if param_str.upper() == 'PH':
                    diff_from_neutral = abs(actual_val - 7.0)
                    max_deviation = max(abs(max_val - 7), abs(min_val - 7))
                    treated_hover_texts.append(
                        f"pH: {actual_val:.2f}<br>" +
                        f"Difference from neutral: ±{diff_from_neutral:.2f}<br>" +
                        f"Max allowed deviation: ±{max_deviation:.2f}"
                    )
                else:
                    treated_hover_texts.append(f"Value: {actual_val:.2f}<br>Range: {min_val:.2f} - {max_val:.2f}")
                    
            except (ValueError, TypeError) as e:
                print(f"Error processing treated parameter {param}: {e}")
                treated_actual_values.append(0)
                treated_normalized.append(0)
                treated_hover_texts.append("N/A")
                continue
        
        # Add the first point's data to the end to close the shape
        treated_actual_values.append(treated_actual_values[0])
        treated_normalized.append(treated_normalized[0])
        treated_hover_texts.append(treated_hover_texts[0])
        
        fig.add_trace(go.Scatterpolar(
            r=treated_normalized,
            theta=param_names,
            name='Treated Water',
            fill='toself',
            line=dict(
                color='#1E90FF',
                shape='linear'  # Ensure linear connections between points
            ),
            connectgaps=True,  # Connect any gaps in the data
            hovertemplate=(
                "<b>%{theta}</b><br>" +
                "%{text}<br>" +
                "Quality: %{customdata:.0%}<br>" +
                "<extra></extra>"
            ),
            customdata=[1 - v for v in treated_normalized],
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
    
    # Update layout with fixed angular axis settings
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1],
                tickmode='array',
                ticktext=['Ideal', 'Good', 'Fair', 'Poor', 'Critical'],
                tickvals=[0, 0.25, 0.5, 0.75, 1]
            ),
            angularaxis=dict(
                direction="clockwise",
                period=len(param_names) - 1,  # Subtract 1 since we added a duplicate point
                rotation=90  # Rotate to ensure better alignment
            ),
            bgcolor='rgba(0,0,0,0)'
        ),
        showlegend=True,
        height=600,
        title=dict(
            text=f"Water Quality Parameters - Week {week_num}",
            x=0.5,
            y=0.95,
            xanchor='center'
        ),
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
        ],
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    
    return fig, warning_message
    
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