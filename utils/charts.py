import plotly.graph_objects as go
import pandas as pd

def create_radar_chart(week_num, params, influent_data, treated_data, influent_ranges, treated_ranges, data_type='influent', show_comparison=False):
    """Create a radar chart for the specified data type and parameters"""
    ranges_df = treated_ranges if data_type == 'treated' else influent_ranges
    data_df = treated_data if data_type == 'treated' else influent_data
    
    df_filtered = data_df[data_df['Influent Water'].isin(params)]
    week_col = f'Week {week_num}'
    values = df_filtered[week_col].values
    
    max_values = []
    for param in df_filtered['Influent Water']:
        range_row = ranges_df[ranges_df['Influent Water'] == param]
        if len(range_row) > 0:
            max_val = range_row['Max'].values[0]
            max_values.append(float(max_val) if max_val != 0 else 1.0)
        else:
            # If no range data found, use the maximum value in the dataset
            param_data = data_df[data_df['Influent Water'] == param]
            max_val = max([float(param_data[col].max()) for col in param_data.columns if col.startswith('Week')])
            max_values.append(max_val if max_val != 0 else 1.0)
    
    normalized_values = []
    for val, max_val in zip(values, max_values):
        try:
            norm_val = float(val) / float(max_val) if max_val != 0 else 0
            normalized_values.append(norm_val)
        except (TypeError, ValueError):
            normalized_values.append(0)
    
    fig = go.Figure()
    
    # Add main trace
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=df_filtered['Influent Water'].tolist(),
        name='Influent Water' if data_type == 'influent' else 'Treated Water',
        fill='toself',
        line=dict(color='#1f77b4' if data_type == 'influent' else '#2ca02c')
    ))
    
    if show_comparison:
        # Get treated water values for comparison
        treated_filtered = treated_data[treated_data['Influent Water'].isin(params)]
        treated_values = treated_filtered[week_col].values
        treated_normalized = []
        for val, max_val in zip(treated_values, max_values):
            try:
                norm_val = float(val) / float(max_val) if max_val != 0 else 0
                treated_normalized.append(norm_val)
            except (TypeError, ValueError):
                treated_normalized.append(0)
        
        fig.add_trace(go.Scatterpolar(
            r=treated_normalized,
            theta=df_filtered['Influent Water'].tolist(),
            name='Treated Water',
            fill='toself',
            line=dict(color='#2ca02c')
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True,
        height=600
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