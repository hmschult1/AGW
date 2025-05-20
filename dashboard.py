import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

# Load and prepare data
df = pd.read_csv("data/athletic giving week report.csv")
df.columns = df.columns.str.strip()
df["Click Rate (%)"] = pd.to_numeric(df["Click Rate (%)"], errors='coerce')

# Create Dash app
app = dash.Dash(__name__)
server = app.server  # For Render deployment

# Layout
app.layout = html.Div([
    html.H1("AGW 2025 Data", style={'textAlign': 'center'}),
    
    html.Label("Select Sport:"),
    dcc.Dropdown(
        id='sport-dropdown',
        options=[{"label": sport, "value": sport} for sport in df["Sport"].unique()],
        value=df["Sport"].unique()[0]
    ),
    
    dcc.Graph(id='click-rate-graph')
])

# Callback to update graph based on selected sport
@app.callback(
    Output("click-rate-graph", "figure"),
    Input("sport-dropdown", "value")
)
def update_graph(selected_sport):
    filtered_df = df[df["Sport"] == selected_sport]
    fig = px.bar(
        filtered_df,
        x="Age Group",
        y="Click Rate (%)",
        color="Subject Line",
        barmode="group",
        title=f"Click Rate by Age Group and Subject Line ({selected_sport})",
        labels={"Click Rate (%)": "Click Rate (%)"}
    )
    return fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
