import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from functools import lru_cache

# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Brolga Water Treatment Trial - Point Leo",
    page_icon="💧"
)

@lru_cache(maxsize=None)
def process_data(value):
    """Process data values with caching for better performance"""
    try:
        if isinstance(value, str):
            if value.startswith('<'):
                return float(value.strip('<'))
            elif value.startswith('>'):
                value = value.strip('>')
                if value.isdigit():
                    return float(value)
                return 2000
            elif value == 'N/R':
                return 0
            elif value.endswith('LINT'):
                return float(value.split()[0].strip('<'))
            try:
                return float(value)
            except ValueError:
                return 0
        elif value is None:
            return 0
        else:
            return float(value)
    except Exception:
        return 0

# Load and process data with caching
@st.cache_data(ttl=3600)
def load_data():
    try:
        # Load all data files
        influent_data = pd.read_csv('Point Leo Influent Water.csv')
        treated_data = pd.read_csv('Point Leo Treated Water.csv')
        influent_ranges = pd.read_csv('Brolga Influent Parameters.csv')
        treated_ranges = pd.read_csv('Brolga Treated Parameters.csv')
        
        # Check if we need to rename columns in treated data
        if 'Product Water' in treated_data.columns and 'Influent Water' not in treated_data.columns:
            treated_data = treated_data.rename(columns={'Product Water': 'Influent Water'})
        
        # Process numeric columns for both dataframes
        for df in [influent_data, treated_data]:
            for col in df.columns:
                if col not in ['Influent Water', 'Details', 'Pond']:
                    df[col] = df[col].apply(process_data)
                    
        return influent_data, treated_data, influent_ranges, treated_ranges
        
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        raise e

    # Process both influent and treated data
    for df in [influent_data, treated_data]:
        for col in df.columns:
            if col not in ['Influent Water', 'Details', 'Pond']:
                df[col] = df[col].apply(process_data)

    return influent_data, treated_data, influent_ranges, treated_ranges

influent_data, treated_data, influent_ranges, treated_ranges = load_data()

# Define relevant parameters
RELEVANT_PARAMS = [
    'TURBIDITY',
    'PH',
    'TOC',
    'E COLI(C)',
    'EC',
    'TDS_180',
    'COLIFORM (C)',
    'DOC'
]

# Project Overview Section
st.title('Brolga Water Treatment System - Point Leo Trial')

# Define column layout
col1, col2 = st.columns([2, 1])

# First column with main project description
with col1:
    st.text_area(
        "Project Description",
        "The Point Leo trial demonstrates Water Source Australia's Brolga water treatment system in a real-world application. "
        "This pilot project processes pond water through a multi-barrier treatment approach to achieve potable water quality standards.",
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )

# Second column with key project details
with col2:
    st.text_area(
        "Key Details",
        "Trial Location: Point Leo Farm, Frankston-Flinders Road\n"
        "Source Water: Farm Pond\n"
        "Treatment Goal: Potable Water Quality",
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )

# System Overview
st.header('System Overview')
st.markdown("""
    The Brolga treatment system employs multiple barriers for water treatment:
    - Pre-filtration for large particle removal
    - Mixed media filtration for iron and manganese removal
    - Ultrafiltration for pathogen and particle removal
    - Carbon filtration for taste, odor, and color removal
    - UV disinfection for final pathogen inactivation
""")

# Create tabs
tab1, tab2, tab3 = st.tabs(['Influent Water', 'Treated Water', 'Comparison'])

def create_radar_chart(week_num, params, data_type='influent', show_comparison=False):
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

# Sidebar controls
st.sidebar.title('Control Panel')
week_num = st.sidebar.slider('Select Week', 1, 7, 1)
show_all = st.sidebar.checkbox('Show All Parameters', value=False)

# Get parameters based on selection
params = influent_data['Influent Water'].tolist() if show_all else RELEVANT_PARAMS

# Warning message
st.sidebar.markdown('---')
st.sidebar.warning('Note: Values below detection limits are shown as the detection limit value. Actual values may be lower.')

# Display content in tabs
with tab1:
    st.header('Influent Water Analysis')
    st.markdown(f"""
    Analyzing raw pond water characteristics for Week {week_num}.  
    The data represents untreated water entering the Brolga system.
    """)
    
    fig = create_radar_chart(week_num, params, 'influent')
    st.plotly_chart(fig, use_container_width=True)

    # Add actual values and parameter ranges table
    st.markdown("### Raw Water Parameters")
    week_col = f'Week {week_num}'
    
    # Create combined display dataframe
    df_display = pd.merge(
        influent_data[influent_data['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]],
        influent_ranges[['Influent Water', 'Min', 'Max', 'Estimated', 'Notes']],
        on='Influent Water',
        how='left'
    )
    
    # Format the display
    df_display = df_display.rename(columns={week_col: 'Current Value'})
    df_display['Range'] = df_display.apply(lambda x: f"{x['Min']} - {x['Max']}", axis=1)
    display_cols = ['Details', 'Current Value', 'Range', 'Estimated', 'Notes']
    
    st.dataframe(
        df_display[display_cols].set_index('Details'),
        height=400
    )

with tab2:
    st.header('Treated Water Analysis')
    st.markdown(f"""
    Showing treated water quality parameters for Week {week_num}.  
    This represents the Brolga system's output water quality after full treatment.
    """)
    
    fig = create_radar_chart(week_num, params, 'treated')
    st.plotly_chart(fig, use_container_width=True)

    # Add treated water values and parameter ranges table
    st.markdown("### Treated Water Parameters")
    week_col = f'Week {week_num}'
    
    # Create combined display dataframe
    df_display = pd.merge(
        treated_data[treated_data['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]],
        treated_ranges[['Influent Water', 'Min', 'Max', 'Estimated', 'Notes']],
        on='Influent Water',
        how='left'
    )
    
    # Format the display
    df_display = df_display.rename(columns={week_col: 'Current Value'})
    df_display['Range'] = df_display.apply(lambda x: f"{x['Min']} - {x['Max']}", axis=1)
    display_cols = ['Details', 'Current Value', 'Range', 'Estimated', 'Notes']
    
    st.dataframe(
        df_display[display_cols].set_index('Details'),
        height=400
    )

with tab3:
    st.header('Water Quality Comparison')
    st.markdown(f"""
    Week {week_num} comparison between influent and treated water.  
    The smaller radar plot area for treated water demonstrates the effectiveness of the Brolga treatment process.
    """)
    
    fig = create_radar_chart(week_num, params, 'influent', show_comparison=True)
    st.plotly_chart(fig, use_container_width=True)

# System Performance Metrics
# Header for the section
st.header('Treatment System Performance')

# Define column layout
col1, col2, col3 = st.columns(3)

# First column for Pathogen Removal details
with col1:
    st.text_area(
        "Pathogen Removal",
        "✓ >7 log bacteria removal\n"
        "✓ >6.5 log virus removal\n"
        "✓ >7 log protozoa removal",
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )

# Second column for Physical Treatment details
with col2:
    st.text_area(
        "Physical Treatment",
        "✓ Turbidity < 0.1 NTU\n"
        "✓ Color reduction to < 15 HU\n"
        "✓ TDS reduction to spec",
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )

# Third column for Chemical Treatment details
with col3:
    st.text_area(
        "Chemical Treatment",
        "✓ Iron/Manganese removal\n"
        "✓ pH correction\n"
        "✓ Organic carbon reduction",
        height=150,
        disabled=True,
        label_visibility="collapsed"
    )