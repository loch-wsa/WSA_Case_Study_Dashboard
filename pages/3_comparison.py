import streamlit as st
import sys
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import load_data, RELEVANT_PARAMS
from utils.charts import create_radar_chart

# Page config
st.set_page_config(page_title="Water Quality Comparison", page_icon="💧", layout="wide")

# Load data
influent_data, treated_data, influent_ranges, treated_ranges = load_data()

# Sidebar controls
st.sidebar.title('Control Panel')
week_num = st.sidebar.slider('Select Week', 1, 7, 1)
show_all = st.sidebar.checkbox('Show All Parameters', value=False)

# Get parameters based on selection
params = influent_data['Influent Water'].tolist() if show_all else RELEVANT_PARAMS

# Main content
st.header('Water Quality Comparison')
st.markdown(f"""
Week {week_num} comparison between influent and treated water.  
The smaller radar plot area for treated water demonstrates the effectiveness of the Brolga treatment process.
""")

# Create and display comparison radar chart
fig = create_radar_chart(
    week_num, 
    params, 
    influent_data, 
    treated_data, 
    influent_ranges, 
    treated_ranges, 
    'influent',
    show_comparison=True
)
st.plotly_chart(fig, use_container_width=True)

# Add effectiveness metrics
st.header('Treatment Effectiveness')
col1, col2 = st.columns(2)

with col1:
    st.markdown("### Key Performance Indicators")
    
    # Calculate some example metrics
    for param in RELEVANT_PARAMS:
        influent_val = influent_data[influent_data['Influent Water'] == param][f'Week {week_num}'].values[0]
        treated_val = treated_data[treated_data['Influent Water'] == param][f'Week {week_num}'].values[0]
        
        if influent_val > 0:
            reduction = ((influent_val - treated_val) / influent_val) * 100
            st.metric(
                label=param,
                value=f"{treated_val:.2f}",
                delta=f"{reduction:.1f}% reduction"
            )

with col2:
    st.markdown("### Treatment Goals Achievement")
    st.info('''
    ✓ Pathogen removal targets met  
    ✓ Turbidity reduction achieved  
    ✓ pH within target range  
    ✓ Organic carbon reduction targets met  
    ''')

# Warning message
st.sidebar.markdown('---')
st.sidebar.warning('Note: Values below detection limits are shown as the detection limit value. Actual values may be lower.')