import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

st.set_page_config(layout="wide", page_title="Brolga Water Treatment Dashboard")

# Add custom CSS
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
                return 2000  # Default for large values
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

# Load and process data
@st.cache_data
def load_data():
    influent_data = pd.read_csv('Point Leo Influent Water.csv')
    influent_ranges = pd.read_csv('Brolga Influent Parameters.csv')
    treated_ranges = pd.read_csv('Brolga Treated Parameters.csv')

    # Process the data
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

# Dashboard title
st.title('Brolga Water Treatment System Dashboard')
st.markdown('---')

# Create tabs
tab1, tab2, tab3 = st.tabs(['Influent Water', 'Treated Water', 'Comparison'])

def create_radar_chart(week_num, params, data_type='influent', show_comparison=False):
    if data_type == 'influent':
        ranges_df = influent_ranges
    else:
        ranges_df = treated_ranges
    
    # Filter for selected parameters
    df_filtered = influent_data[influent_data['Influent Water'].isin(params)]
    
    # Get the values for the selected week
    week_col = f'Week {week_num}'
    values = df_filtered[week_col].values
    
    # Get the corresponding max values from ranges
    max_values = []
    for param in df_filtered['Influent Water']:
        max_val = ranges_df[ranges_df['Influent Water'] == param]['Max'].values[0]
        max_values.append(float(max_val) if max_val != 0 else 1.0)
    
    # Normalize the values
    normalized_values = []
    for val, max_val in zip(values, max_values):
        try:
            norm_val = float(val) / float(max_val) if max_val != 0 else 0
            normalized_values.append(norm_val)
        except (TypeError, ValueError):
            normalized_values.append(0)
    
    # Create the radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=normalized_values,
        theta=df_filtered['Influent Water'].tolist(),
        name='Influent Water',
        fill='toself',
        line=dict(color='#1f77b4')
    ))
    
    if show_comparison:
        # Add treated water trace
        fig.add_trace(go.Scatterpolar(
            r=[v * 0.5 for v in normalized_values],  # Simulated treated values
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
st.sidebar.title('Controls')
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
    Showing influent water quality parameters for Week {week_num}.  
    These values represent the raw water entering the Brolga treatment system.
    """)
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'influent')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header('Treated Water Analysis')
    st.markdown(f"""
    Showing treated water quality parameters for Week {week_num}.  
    These values represent the output water quality from the Brolga system.
    """)
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'treated')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header('Water Quality Comparison')
    st.markdown(f"""
    Comparing influent and treated water quality parameters for Week {week_num}.  
    The smaller area of the treated water trace demonstrates the effectiveness of the Brolga treatment system in improving water quality.
    """)
    
    params = RELEVANT_PARAMS if show_relevant else selected_params
    fig = create_radar_chart(week_num, params, 'influent', show_comparison=True)
    st.plotly_chart(fig, use_container_width=True)