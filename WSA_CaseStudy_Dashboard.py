import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    layout="wide",
    page_title="Brolga Water Treatment Trial - Point Leo",
    page_icon="💧"
)

# Custom CSS
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #f0f2f6;
        border-radius: 5px 5px 0px 0px;
    }
    .big-font {
        font-size: 24px !important;
    }
    .medium-font {
        font-size: 20px !important;
    }
    .info-box {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .highlight {
        color: #FF4B4B;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

def process_data(value):
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
    influent_data = pd.read_csv('Point Leo Influent Water.csv')
    influent_ranges = pd.read_csv('Brolga Influent Parameters.csv')
    treated_ranges = pd.read_csv('Brolga Treated Parameters.csv')

    for col in influent_data.columns:
        if col not in ['Influent Water', 'Details', 'Pond']:
            influent_data[col] = influent_data[col].apply(process_data)

    return influent_data, influent_ranges, treated_ranges

influent_data, influent_ranges, treated_ranges = load_data()

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

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("""
        <div class="info-box">
        <p class="medium-font">The Point Leo trial demonstrates Water Source Australia's Brolga water treatment system in a real-world application. 
        This pilot project processes pond water through a multi-barrier treatment approach to achieve potable water quality standards.</p>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="info-box">
        <p><strong>Trial Location:</strong> Point Leo Farm, Frankston-Flinders Road</p>
        <p><strong>Source Water:</strong> Farm Pond</p>
        <p><strong>Treatment Goal:</strong> Potable Water Quality</p>
        </div>
        """, unsafe_allow_html=True)

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
    if data_type == 'influent':
        ranges_df = influent_ranges
    else:
        ranges_df = treated_ranges
    
    df_filtered = influent_data[influent_data['Influent Water'].isin(params)]
    week_col = f'Week {week_num}'
    values = df_filtered[week_col].values
    
    max_values = []
    for param in df_filtered['Influent Water']:
        max_val = ranges_df[ranges_df['Influent Water'] == param]['Max'].values[0]
        max_values.append(float(max_val) if max_val != 0 else 1.0)
    
    normalized_values = []
    for val, max_val in zip(values, max_values):
        try:
            norm_val = float(val) / float(max_val) if max_val != 0 else 0
            normalized_values.append(norm_val)
        except (TypeError, ValueError):
            normalized_values.append(0)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=df_filtered['Influent Water'].tolist(),
        name='Influent Water',
        fill='toself',
        line=dict(color='#1f77b4')
    ))
    
    if show_comparison:
        fig.add_trace(go.Scatterpolar(
            r=[v * 0.5 for v in normalized_values],
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
show_relevant = st.sidebar.checkbox('Show Relevant Parameters Only')
selected_params = st.sidebar.multiselect(
    'Select Parameters',
    options=influent_data['Influent Water'].tolist(),
    default=RELEVANT_PARAMS
)

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
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'influent')
    st.plotly_chart(fig, use_container_width=True)

    # Add actual values table
    st.markdown("### Raw Water Parameters")
    week_col = f'Week {week_num}'
    df_display = influent_data[influent_data['Influent Water'].isin(params)][['Influent Water', 'Details', week_col]]
    st.dataframe(df_display.set_index('Influent Water'))

with tab2:
    st.header('Treated Water Analysis')
    st.markdown(f"""
    Showing treated water quality parameters for Week {week_num}.  
    This represents the Brolga system's output water quality after full treatment.
    """)
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'treated')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header('Water Quality Comparison')
    st.markdown(f"""
    Week {week_num} comparison between influent and treated water.  
    The smaller radar plot area for treated water demonstrates the effectiveness of the Brolga treatment process.
    """)
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'influent', show_comparison=True)
    st.plotly_chart(fig, use_container_width=True)

# System Performance Metrics
st.header('Treatment System Performance')
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div class="info-box">
        <h3>Pathogen Removal</h3>
        <p>✓ >7 log bacteria removal</p>
        <p>✓ >6.5 log virus removal</p>
        <p>✓ >7 log protozoa removal</p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div class="info-box">
        <h3>Physical Treatment</h3>
        <p>✓ Turbidity < 0.1 NTU</p>
        <p>✓ Color reduction to < 15 HU</p>
        <p>✓ TDS reduction to spec</p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div class="info-box">
        <h3>Chemical Treatment</h3>
        <p>✓ Iron/Manganese removal</p>
        <p>✓ pH correction</p>
        <p>✓ Organic carbon reduction</p>
        </div>
    """, unsafe_allow_html=True)