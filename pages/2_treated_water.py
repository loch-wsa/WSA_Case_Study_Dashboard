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

# Zoom controls
zoom_method = st.sidebar.radio(
    'Zoom Control Method',
    ['Slider', 'Preset Levels'],
    help='Choose how you want to control the zoom level'
)

if zoom_method == 'Slider':
    zoom_level = st.sidebar.slider(
        'Zoom Level',
        min_value=1.0,
        max_value=8.0,
        value=1.0,
        step=0.5,
        help='Drag to adjust the zoom level (1x-8x)'
    )
else:
    zoom_level = st.sidebar.selectbox(
        'Select Zoom Level',
        options=[1, 2, 4, 8],
        format_func=lambda x: f'{x}x',
        help='Choose a preset zoom level'
    )

# Main content
st.header('Treated Water Analysis')
st.markdown(f"""
Showing treated water quality parameters for Week {week_num}.  
This represents the Brolga system's output water quality after full treatment.
""")

# Get parameters based on selection
params = treated_data['Influent Water'].tolist() if show_all else RELEVANT_PARAMS

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

# Update zoom level based on sidebar selection
fig.update_layout({
    "polar.radialaxis.range": [0, 1/zoom_level]  # Since we're using normalized values (0-1)
})

# Display the chart
st.plotly_chart(fig, use_container_width=True)

# Add a note about zooming
st.info("""
💡 **Zoom Tips:**
- Use the sidebar controls to adjust the zoom level
- You can also use the chart's built-in zoom slider or reset button
- Double-click the chart to reset the view
""")

# Display parameter table
st.markdown("### Treated Water Parameters")
df_display = create_parameter_table(week_num, params, treated_data, treated_ranges)
st.dataframe(df_display)

# Warning message
st.sidebar.markdown('---')
st.sidebar.warning('Note: Values below detection limits are shown as the detection limit value. Actual values may be lower.')