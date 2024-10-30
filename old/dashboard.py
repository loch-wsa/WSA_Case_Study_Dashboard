import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from dash.exceptions import PreventUpdate

# Read and process the data
def process_data(value):
    try:
        if isinstance(value, str):
            # Print the problematic value for debugging
            print(f"Processing string value: {value}")
            
            if value.startswith('<'):
                return float(value.strip('<'))
            elif value.startswith('>'):
                value = value.strip('>')
                # Handle cases like '>2000'
                if value.isdigit():
                    return float(value)
                return 2000  # Default for other cases
            elif value == 'N/R':
                return 0
            elif value.endswith('LINT'):
                return float(value.split()[0].strip('<'))
            # Try direct conversion for other string cases
            try:
                return float(value)
            except ValueError:
                print(f"Could not convert {value} to float, returning 0")
                return 0
        elif value is None:
            return 0
        else:
            return float(value)
    except Exception as e:
        print(f"Error processing value {value}: {e}")
        return 0

# Load the datasets
influent_data = pd.read_csv('Point Leo Influent Water.csv')
influent_ranges = pd.read_csv('Brolga Influent Parameters.csv')
treated_ranges = pd.read_csv('Brolga Treated Parameters.csv')

# Process the data
for col in influent_data.columns:
    if col not in ['Influent Water', 'Details', 'Pond']:
        influent_data[col] = influent_data[col].apply(process_data)

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

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Create the layout
app.layout = html.Div([
    html.H1('Brolga Water Treatment System Dashboard',
            style={'textAlign': 'center', 'marginBottom': '30px'}),
    
    dcc.Tabs(id='tabs', value='tab-influent', children=[
        dcc.Tab(label='Influent Water', value='tab-influent'),
        dcc.Tab(label='Treated Water', value='tab-treated'),
        dcc.Tab(label='Comparison', value='tab-comparison')
    ]),
    
    html.Div([
        html.Div([
            html.Div([
                html.Button('←', id='prev-week', style={'margin': '10px'}),
                dcc.Dropdown(
                    id='week-selector',
                    options=[{'label': f'Week {i}', 'value': i} 
                            for i in range(1, 8)],
                    value=1,
                    style={'width': '150px', 'display': 'inline-block', 
                           'margin': '10px'}
                ),
                html.Button('→', id='next-week', style={'margin': '10px'})
            ], style={'textAlign': 'center'}),
            
            html.Div([
                html.Label('Show Relevant Parameters Only'),
                dcc.Checklist(
                    id='relevant-params-switch',
                    options=[{'label': '', 'value': 'relevant'}],
                    value=[],
                    style={'display': 'inline-block', 'margin-left': '10px'}
                )
            ], style={'margin': '20px'}),
            
            html.Div([
                html.Label('Select Parameters to Display'),
                dcc.Dropdown(
                    id='parameter-selector',
                    options=[{'label': str(param), 'value': str(param)} 
                            for param in influent_data['Influent Water'].tolist()],
                    value=RELEVANT_PARAMS,
                    multi=True
                )
            ], style={'margin': '20px'}),
            
            html.Div(id='detection-limit-warning', 
                    style={'margin': '20px', 'color': 'orange'})
        ], style={'width': '30%', 'display': 'inline-block', 
                  'vertical-align': 'top'}),
        
        html.Div([
            dcc.Graph(id='radar-chart')
        ], style={'width': '70%', 'display': 'inline-block'})
    ]),
    
    html.Div(id='description-text', 
             style={'margin': '20px', 'padding': '20px', 
                    'backgroundColor': '#f8f9fa'})
])

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
        max_values.append(float(max_val) if max_val != 0 else 1.0)  # Avoid division by zero
    
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
        fill='toself'
    ))
    
    if show_comparison:
        # Add treated water trace (using same data for now)
        fig.add_trace(go.Scatterpolar(
            r=[v * 0.5 for v in normalized_values],  # Simulated treated values
            theta=df_filtered['Influent Water'].tolist(),
            name='Treated Water',
            fill='toself'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        showlegend=True
    )
    
    return fig

@app.callback(
    [Output('radar-chart', 'figure'),
     Output('detection-limit-warning', 'children'),
     Output('description-text', 'children')],
    [Input('tabs', 'value'),
     Input('week-selector', 'value'),
     Input('relevant-params-switch', 'value'),
     Input('parameter-selector', 'value')]
)
def update_content(tab, week, show_relevant, selected_params):
    # Determine which parameters to show
    params = RELEVANT_PARAMS if 'relevant' in (show_relevant or []) else (selected_params or RELEVANT_PARAMS)
    
    # Generate detection limit warning
    warning = ("Note: Values below detection limits are shown as the detection limit value. "
              "Actual values may be lower.")
    
    # Create description based on tab
    if tab == 'tab-influent':
        description = f"""
        Showing influent water quality parameters for Week {week}. 
        These values represent the raw water entering the Brolga treatment system.
        """
        fig = create_radar_chart(week, params, 'influent')
    
    elif tab == 'tab-treated':
        description = f"""
        Showing treated water quality parameters for Week {week}.
        These values represent the output water quality from the Brolga system.
        Note: Currently showing influent data as treated data is not available.
        """
        fig = create_radar_chart(week, params, 'treated')
    
    else:  # Comparison tab
        description = f"""
        Comparing influent and treated water quality parameters for Week {week}.
        The smaller area of the treated water trace demonstrates the effectiveness
        of the Brolga treatment system in improving water quality.
        Note: Currently showing simulated treated data.
        """
        fig = create_radar_chart(week, params, 'influent', show_comparison=True)
    
    return fig, warning, description

@app.callback(
    Output('week-selector', 'value'),
    [Input('prev-week', 'n_clicks'),
     Input('next-week', 'n_clicks')],
    [State('week-selector', 'value')]
)
def update_week(prev_clicks, next_clicks, current_week):
    ctx = dash.callback_context
    if not ctx.triggered:
        raise PreventUpdate
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if button_id == 'prev-week':
        return max(1, current_week - 1)
    else:
        return min(7, current_week + 1)

if __name__ == '__main__':
    app.run_server(debug=True)