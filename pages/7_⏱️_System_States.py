import streamlit as st
import pandas as pd
import plotly.figure_factory as ff
import plotly.graph_objects as go
from datetime import datetime
import sys
from pathlib import Path

# Add the root directory to Python path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

# Page config
st.set_page_config(page_title="System States Timeline", page_icon="⏱️", layout="wide")

# Define color map globally
COLOR_MAP = {
    'START': '#2ecc71',           # Green
    'INITIALIZATION': '#2ecc71',   # Green (same as START)
    '2000': '#2ecc71',           # Green (for INITIALIZATION)
    'PRODUCTION': '#3498db',      # Blue
    '2002': '#3498db',           # Blue (for PRODUCTION)
    'WAIT': '#f39c12',           # Orange
    '2021': '#f39c12',           # Orange (for WAIT)
    'TAGOUT': '#e74c3c',          # Red
    '2020': '#e74c3c',           # Red (for TAGOUT)
    'MEMBRANE_AIRSOUR': '#9b59b6', # Purple
    '2015': '#9b59b6',           # Purple (for MEMBRANE_AIRSOUR)
    'MEMBRANE_DIT': '#1abc9c',     # Turquoise
    '2022': '#1abc9c',           # Turquoise (for MEMBRANE_DIT)
    'SLEEP': '#95a5a6',            # Gray
    '2035': '#95a5a6',           # Gray (for SLEEP)
    '2076': '#95a5a6'            # Gray (for SLEEP)
}

def load_sequence_data():
    """Load and process sequence data"""
    sequences_df = pd.read_csv('data/Sequences.csv')
    
    # Parse timestamps in DD/MM/YYYY HH:MM:SS format
    def parse_timestamp(ts):
        try:
            return pd.to_datetime(ts, format="%d/%m/%Y %H:%M")
        except:
            try:
                # Handle case where seconds are included
                return pd.to_datetime(ts, format="%d/%m/%Y %H:%M:%S")
            except:
                return None

    sequences_df['timestamp'] = sequences_df['timestamp'].apply(parse_timestamp)
    # Remove any rows with invalid timestamps
    sequences_df = sequences_df[sequences_df['timestamp'].notna()]
    # Use the code column directly for states
    sequences_df = sequences_df[sequences_df['code'].notna()]
    
    # Map numeric and special codes to state names
    state_map = {
        '2000': 'INITIALIZATION',
        '2002': 'PRODUCTION',
        '2020': 'TAGOUT',
        '2021': 'WAIT',
        '2022': 'MEMBRANE_DIT',
        '2035': 'SLEEP',
        '2076': 'SLEEP',
        'START': 'START',
        'WAIT': 'WAIT',
        'TAGOUT': 'TAGOUT',
        'PRODUCTION': 'PRODUCTION',
        'MEMBRANEAIRSCOUR': 'MEMBRANE_AIRSOUR',
        'MEMBRANEDIRECTINTEGRITYTEST': 'MEMBRANE_DIT'
    }
    
    # Convert codes to states
    sequences_df['state'] = sequences_df['code'].map(lambda x: state_map.get(str(x), x))
    
    # Remove rows with unmapped states
    sequences_df = sequences_df[sequences_df['state'].isin(state_map.values())]
    
    # Calculate duration for each state
    sequences_df['duration'] = sequences_df['timestamp'].diff().shift(-1).dt.total_seconds() / 60
    
    return sequences_df

# Update the timeline function
def create_state_timeline(df):
    df_timeline = []

    for _, row in df.iterrows():
        end_time = row['timestamp'] + pd.Timedelta(minutes=row['duration']) if pd.notna(row['duration']) else row['timestamp']
        color = COLOR_MAP.get(row['state'], '#95a5a6')  # Use grey if the state is unknown

        df_timeline.append(dict(
            Task='System State',
            Start=row['timestamp'],
            Finish=end_time,
            State=row['state'],
            Description=row['message'],
            Color=color
        ))
    
    # Create figure
    fig = ff.create_gantt(
        df_timeline,
        colors=[item['Color'] for item in df_timeline],
        index_col='State',
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True
    )
    
    fig.update_layout(
        title='System State Timeline',
        height=400,
        xaxis_title='Time'
    )
    
    return fig

def create_state_summary(df):
    """Create summary statistics for states"""
    summary = df.groupby('state').agg({
        'duration': ['count', 'sum', 'mean']
    }).round(2)
    
    summary.columns = ['Count', 'Total Duration (min)', 'Avg Duration (min)']
    return summary

def create_transition_sankey(df):
    """Create a Sankey diagram for state transitions"""
    # Create state transitions
    transitions = pd.DataFrame({
        'source': df['state'].iloc[:-1].values,
        'target': df['state'].iloc[1:].values
    })
    
    # Count transitions
    transition_counts = transitions.groupby(['source', 'target']).size().reset_index(name='value')
    
    # Get unique states for node creation
    states = pd.unique(transitions[['source', 'target']].values.ravel('K'))
    
    # Create node-index mapping
    node_map = {state: idx for idx, state in enumerate(states)}
    
    # Get colors for each node and link
    node_colors = [COLOR_MAP.get(state, '#95a5a6') for state in states]
    link_colors = [COLOR_MAP.get(source, '#95a5a6') for source in transition_counts['source']]
    
    # Create Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=states,
            color=node_colors,
            hovertemplate='%{label}<br>Total Transitions: %{value}<extra></extra>'
        ),
        link=dict(
            source=[node_map[s] for s in transition_counts['source']],
            target=[node_map[t] for t in transition_counts['target']],
            value=transition_counts['value'],
            color=link_colors,
            hovertemplate='%{source.label} → %{target.label}<br>Transitions: %{value}<extra></extra>'
        )
    )])
    
    fig.update_layout(
        title=dict(
            text="State Transitions",
            x=0.5,
            xanchor='center'
        ),
        height=500,
        font=dict(size=12),
    )
    
    return fig

# Main content
st.title('⏱️ System State Analysis')
st.markdown("""
This page provides analysis of the system's operational states and transitions over time.
The visualization shows when and how long the system spent in different states, as well as the flow between states.
""")

# Load data
df = load_sequence_data()

# Create timeline visualization
st.subheader('System State Timeline')
timeline_fig = create_state_timeline(df)
st.plotly_chart(timeline_fig, use_container_width=True)

# Create state transition diagram
st.subheader('State Transitions')
sankey_fig = create_transition_sankey(df)
st.plotly_chart(sankey_fig, use_container_width=True)

# Show summary statistics
st.subheader('State Summary Statistics')
summary_df = create_state_summary(df)
st.dataframe(summary_df)

# Add explanation of states
st.markdown("""
### State Descriptions
- **PRODUCTION**: System is actively producing potable water
- **WAIT**: System is idle but ready to operate
- **TAGOUT**: System is tagged out for maintenance or due to an error
- **INITIALIZATION**: System is initializing
- **MEMBRANE_AIRSOUR**: Membrane cleaning cycle is in progress
- **MEMBRANE_DIT**: System is performing membrane integrity testing
- **SLEEP**: System is in low-power sleep mode
""")

# Add filters and controls in sidebar
st.sidebar.title('Controls')
date_range = st.sidebar.date_input(
    'Select Date Range',
    [df['timestamp'].min().date(), df['timestamp'].max().date()]
)

# Add warning message for errors
st.sidebar.markdown('---')
st.sidebar.warning('Note: Transitions to TAGOUT state may indicate system errors or maintenance events.')