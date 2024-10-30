def create_radar_chart(week_num, params, influent_data, treated_data, influent_ranges, treated_ranges, data_type='influent', show_comparison=False):
    """
    Create an enhanced radar chart with parameter ranges, hover information, and zoom functionality
    while maintaining existing normalization and comparison capabilities.
    
    Args:
        week_num (int): Selected week number
        params (list): List of parameters to display
        influent_data (pd.DataFrame): Influent water data
        treated_data (pd.DataFrame): Treated water data
        influent_ranges (pd.DataFrame): Range values for influent parameters
        treated_ranges (pd.DataFrame): Range values for treated parameters
        data_type (str): Type of chart ('influent' or 'treated')
        show_comparison (bool): Whether to show comparison between influent and treated water
    """
    # Select appropriate dataframes based on data type
    ranges_df = treated_ranges if data_type == 'treated' else influent_ranges
    data_df = treated_data if data_type == 'treated' else influent_data
    
    # Filter data for selected parameters
    df_filtered = data_df[data_df['Influent Water'].isin(params)]
    week_col = f'Week {week_num}'
    values = df_filtered[week_col].values
    param_names = df_filtered['Influent Water'].tolist()
    
    # Calculate max values and normalize data
    max_values = []
    min_values = []
    actual_values = []  # Store non-normalized values for hover display
    
    for param in param_names:
        range_row = ranges_df[ranges_df['Influent Water'] == param]
        if len(range_row) > 0:
            max_val = range_row['Max'].values[0]
            min_val = range_row['Min'].values[0]
            max_values.append(float(max_val) if max_val != 0 else 1.0)
            min_values.append(float(min_val))
        else:
            # If no range data found, use the maximum value in the dataset
            param_data = data_df[data_df['Influent Water'] == param]
            max_val = max([float(param_data[col].max()) for col in param_data.columns if col.startswith('Week')])
            max_values.append(max_val if max_val != 0 else 1.0)
            min_values.append(0)  # Default minimum if no range data
    
    # Normalize values
    normalized_values = []
    for val, max_val in zip(values, max_values):
        try:
            actual_values.append(float(val))  # Store actual value for hover
            norm_val = float(val) / float(max_val) if max_val != 0 else 0
            normalized_values.append(norm_val)
        except (TypeError, ValueError):
            actual_values.append(0)
            normalized_values.append(0)
    
    # Create figure
    fig = go.Figure()
    
    # Add range area (if range data exists)
    normalized_min_values = [min_val / max_val if max_val != 0 else 0 
                           for min_val, max_val in zip(min_values, max_values)]
    
    # Add range area traces
    fig.add_trace(go.Scatterpolar(
        r=[1] * len(param_names) + [1],  # Normalized max values
        theta=param_names + [param_names[0]],  # Close the polygon
        fill='tonext',
        fillcolor='rgba(128, 128, 128, 0.2)',
        line=dict(color='rgba(128, 128, 128, 0.5)'),
        name='Acceptable Range',
        hoverinfo='skip'
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_min_values + [normalized_min_values[0]],  # Close the polygon
        theta=param_names + [param_names[0]],
        fill='tonext',
        fillcolor='rgba(128, 128, 128, 0.2)',
        line=dict(color='rgba(128, 128, 128, 0.5)'),
        showlegend=False,
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
        text=[f"{min_val:.2f} - {max_val:.2f}" for min_val, max_val in zip(min_values, max_values)]
    ))
    
    # Add comparison trace if requested
    if show_comparison:
        treated_filtered = treated_data[treated_data['Influent Water'].isin(params)]
        treated_values = treated_filtered[week_col].values
        treated_actual_values = []  # For hover display
        treated_normalized = []
        
        for val, max_val in zip(treated_values, max_values):
            try:
                treated_actual_values.append(float(val))
                norm_val = float(val) / float(max_val) if max_val != 0 else 0
                treated_normalized.append(norm_val)
            except (TypeError, ValueError):
                treated_actual_values.append(0)
                treated_normalized.append(0)
        
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
            text=[f"{min_val:.2f} - {max_val:.2f}" for min_val, max_val in zip(min_values, max_values)]
        ))
    
    # Update layout with zoom capabilities
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]  # Keep normalized range
            )
        ),
        showlegend=True,
        height=600,
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                buttons=[
                    dict(
                        label="Reset Zoom",
                        method="relayout",
                        args=[{"polar.radialaxis.range": [0, 1]}]
                    )
                ],
                x=0.1,
                y=1.1
            ),
            dict(
                type='slider',
                active=0,
                currentvalue={"prefix": "Zoom: "},
                pad={"t": 50},
                steps=[
                    dict(
                        method='relayout',
                        label=f'{i}x',
                        args=[{"polar.radialaxis.range": [0, 1/i]}]
                    ) for i in [1, 2, 4, 8]
                ]
            )
        ]
    )
    
    return fig