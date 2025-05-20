import pandas as pd
import dash
from dash import dcc, html
import plotly.express as px

# Load and prepare the data
df = pd.read_csv("athletic giving week report.csv")
df.columns = df.columns.str.strip()
df["Click Rate (%)"] = pd.to_numeric(df["Click Rate (%)"], errors='coerce')

# Create Dash app
app = dash.Dash(__name__)
server = app.server
app.title = "Click Rate by Age Group and Sport"

# Create a bar chart
fig = px.bar(
    df,
    x="Age Group",
    y="Click Rate (%)",
    color="Sport",
    barmode="group",
    title="Click Rate by Age Group for Each Sport",
    labels={"Click Rate (%)": "Click Rate (%)"},
    category_orders={"Age Group": sorted(df["Age Group"].unique())}
)

# Layout
app.layout = html.Div([
    html.H1("Click Rate by Age Group and Sport", style={'textAlign': 'center'}),
    dcc.Graph(figure=fig)
])

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
