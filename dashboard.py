import pandas as pd
import dash
from dash import dcc, html, Input, Output
import dash_table
import plotly.express as px

# --- Load and preprocess Giving Data ---
giving_df = pd.read_csv("laf_email data 4.19.2025-5.2.2025.CSV")
giving_df['Lifetime Giving'] = giving_df['Lifetime Giving'].replace('[\$,]', '', regex=True).astype(float)
giving_df['Appeal Date'] = giving_df['Assigned Appeal Description'].str.extract(r'(\d{8})$')
giving_df['Appeal Date'] = pd.to_datetime(giving_df['Appeal Date'], format='%Y%m%d', errors='coerce')
giving_df = giving_df.dropna(subset=['Age', 'Lifetime Giving', 'Appeal Date'])
giving_df = giving_df[(giving_df['Appeal Date'] >= "2025-04-19") & (giving_df['Appeal Date'] <= "2025-05-02")]

# --- Load and clean Click Rate Data ---
click_df = pd.read_csv("data/athletic giving week report.csv")
click_df.columns = click_df.columns.str.strip()
click_df["Click Rate (%)"] = pd.to_numeric(click_df["Click Rate (%)"], errors='coerce')

# --- Create Dash App ---
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Athletic Giving Dashboard", style={'textAlign': 'center'}),
    dcc.Tabs([
        dcc.Tab(label='Age and Lifetime Giving', children=[
            html.Br(),
            dash_table.DataTable(
                id='giving-table',
                columns=[
                    {"name": "Age", "id": "Age"},
                    {"name": "Lifetime Giving", "id": "Lifetime Giving"}
                ],
                data=giving_df[['Age', 'Lifetime Giving']].to_dict('records'),
                style_table={'overflowX': 'auto'},
                style_cell={'padding': '10px', 'textAlign': 'center'},
                style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
            ),
            html.Br(),
            dcc.Graph(
                id='giving-bar',
                figure=px.bar(
                    giving_df,
                    x='Age',
                    y='Lifetime Giving',
                    title='Lifetime Giving by Age',
                    labels={'Age': 'Age', 'Lifetime Giving': 'Lifetime Giving ($)'}
                )
            )
        ]),
        dcc.Tab(label='Click Rate Analysis', children=[
            html.Br(),
            html.Label("Select Sport:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='sport-dropdown',
                options=[{"label": sport, "value": sport} for sport in click_df["Sport"].dropna().unique()],
                value=click_df["Sport"].dropna().unique()[0]
            ),
            html.Br(),
            dcc.Graph(id='click-rate-graph')
        ])
    ])
])

# Callback for Click Rate chart
@app.callback(
    Output("click-rate-graph", "figure"),
    Input("sport-dropdown", "value")
)
def update_click_rate_graph(selected_sport):
    filtered_df = click_df[click_df["Sport"] == selected_sport]
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

# Run app
if __name__ == '__main__':
    app.run_server(debug=True)
