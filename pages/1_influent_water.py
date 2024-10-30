import streamlit as st
from utils.data_loader import load_data, RELEVANT_PARAMS
from utils.charts import create_radar_chart, create_parameter_table

# Page config
st.set_page_config(page_title="Influent Water Analysis", page_icon="💧", layout="wide")

# Load data
influent_data, treated_data, influent_ranges, treated_ranges = load_data()

# Sidebar controls
st.sidebar.title('Control Panel')
week_num = st.sidebar.slider('Select Week', 1, 7, 1)
show_all = st.sidebar.checkbox('Show All Parameters', value=False)

# Get parameters based on selection
params = influent_data['Influent Water'].tolist() if show_all else RELEVANT_PARAMS

# Main content
st.header('Influent Water Analysis')
st.markdown(f"""
Analysing raw pond water characteristics for Week {week_num}.  
The data represents untreated water entering the Brolga system.
""")

# Create and display radar chart
fig = create_radar_chart(
    week_num, 
    params, 
    influent_data, 
    treated_data, 
    influent_ranges, 
    treated_ranges, 
    'influent'
)
st.plotly_chart(fig, use_container_width=True)

# Display parameter table
st.markdown("### Raw Water Parameters")
df_display = create_parameter_table(week_num, params, influent_data, influent_ranges)
st.dataframe(df_display)

# Warning message
st.sidebar.markdown('---')
st.sidebar.warning('Note: Values below detection limits are shown as the detection limit value. Actual values may be lower.')