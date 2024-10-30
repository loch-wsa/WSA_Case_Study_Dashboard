import streamlit as st
import sys
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from utils.data_loader import load_data, RELEVANT_PARAMS
from utils.charts import create_radar_chart, create_parameter_table

# Page config
st.set_page_config(page_title="Treated Water Analysis", page_icon="💧", layout="wide")

# Load data
influent_data, treated_data, influent_ranges, treated_ranges = load_data()

# Sidebar controls
st.sidebar.title('Control Panel')
week_num = st.sidebar.slider('Select Week', 1, 7, 1)
show_all = st.sidebar.checkbox('Show All Parameters', value=False)

# Get parameters based on selection
params = treated_data['Influent Water'].tolist() if show_all else RELEVANT_PARAMS

# Main content
st.header('Treated Water Analysis')
st.markdown(f"""
Showing treated water quality parameters for Week {week_num}.  
This represents the Brolga system's output water quality after full treatment.
""")

# Create and display radar chart
fig = create_radar_chart(
    week_num, 
    params, 
    influent_data, 
    treated_data, 
    influent_ranges, 
    treated_ranges, 
    'treated'
)
st.plotly_chart(fig, use_container_width=True)

# Display parameter table
st.markdown("### Treated Water Parameters")
df_display = create_parameter_table(week_num, params, treated_data, treated_ranges)
st.dataframe(df_display)

# Warning message
st.sidebar.markdown('---')
st.sidebar.warning('Note: Values below detection limits are shown as the detection limit value. Actual values may be lower.')