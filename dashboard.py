import pandas as pd
import dash
from dash import dcc, html
import dash_table
import plotly.express as px

# === Load data ===
click_df = pd.read_csv("data/athletic giving week report.csv")
giving_df = pd.read_csv("laf_email data 4.19.2025-5.2.2025.CSV")

# === Clean headers ===
click_df.columns = click_df.columns.str.strip()
giving_df.columns = giving_df.columns.str.strip()

# === Clean and normalize for mapping ===
click_df['Subject Line Clean'] = click_df['Subject Line'].str.lower().str.replace(r'[^a-z0-9 ]', '', regex=True)
giving_df['Appeal Description Clean'] = giving_df['Assigned Appeal Description'].str.lower().str.replace(r'[^a-z0-9 ]', '', regex=True)

# === Match subject lines to giving data by substring ===
def match_subject(subject, appeal_list):
    matches = [appeal for appeal in appeal_list if subject in appeal]
    return matches[0] if matches else None

appeal_descriptions = giving_df['Appeal Description Clean'].unique().tolist()
click_df['Matched Appeal Description'] = click_df['Subject Line Clean'].apply(lambda x: match_subject(x, appeal_descriptions))

# === Join matched descriptions to get Appeal ID ===
appeals_df = giving_df[['Assigned Appeal Description', 'Assigned Appeal ID', 'Appeal Description Clean']]
matches_df = click_df.merge(
    appeals_df,
    left_on='Matched Appeal Description',
    right_on='Appeal Description Clean',
    how='left'
)
matches_df = matches_df.drop_duplicates(subset=['Sport', 'Subject Line'])

# === Prepare giving data ===
giving_df['Assigned Appeal ID'] = giving_df['Assigned Appeal ID'].astype(str).str.strip()
giving_df['Lifetime Giving'] = giving_df['Lifetime Giving'].replace('[\$,]', '', regex=True).astype(float)
giving_df['Age'] = pd.to_numeric(giving_df['Age'], errors='coerce')
giving_df = giving_df.dropna(subset=['Age'])
giving_df['Age Group'] = pd.cut(
    giving_df['Age'],
    bins=[0, 18, 30, 40, 50, 60, 70, 150],
    labels=['0-18', '19-30', '31-40', '41-50', '51-60', '61-70', '70+']
)

# === Merge giving with mapped campaign data ===
mapped_giving = giving_df.merge(
    matches_df[['Subject Line', 'Sport', 'Assigned Appeal ID']],
    on='Assigned Appeal ID', how='inner'
)

# === Prepare click data ===
click_df['Click Rate (%)'] = pd.to_numeric(click_df['Click Rate (%)'], errors='coerce')
click_df = click_df.dropna(subset=['Click Rate (%)'])

# === Merge giving and click rate data ===
combined_df = mapped_giving.merge(
    click_df[['Subject Line', 'Age Group', 'Click Rate (%)']],
    on=['Subject Line', 'Age Group'], how='inner'
)

# === Group for plotting ===
grouped_df = combined_df.groupby(['Sport', 'Age Group', 'Subject Line'], observed=True).agg({
    'Click Rate (%)': 'mean',
    'Lifetime Giving': 'sum'
}).reset_index()

# === Dash App ===
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Click Rate vs Giving by Sport and Age Group", style={'textAlign': 'center'}),

    html.Label("Select Sport:"),
    dcc.Dropdown(
        id='sport-dropdown',
        options=[{"label": sport, "value": sport} for sport in grouped_df['Sport'].unique()],
        value=grouped_df['Sport'].unique()[0]
    ),

    html.Label("Select Subject Line:"),
    dcc.Dropdown(
        id='subject-dropdown'
    ),

    dcc.Graph(id='correlation-graph'),

    html.Br(),
    html.H3("Data Table"),
    dash_table.DataTable(
        id='correlation-table',
        columns=[
            {"name": col, "id": col} for col in ['Sport', 'Age Group', 'Subject Line', 'Click Rate (%)', 'Lifetime Giving']
        ],
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '5px', 'textAlign': 'center'},
        style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'}
    )
])

@app.callback(
    dash.dependencies.Output('subject-dropdown', 'options'),
    dash.dependencies.Output('subject-dropdown', 'value'),
    dash.dependencies.Input('sport-dropdown', 'value')
)
def update_subject_options(selected_sport):
    filtered = grouped_df[grouped_df['Sport'] == selected_sport]
    options = [{'label': s, 'value': s} for s in filtered['Subject Line'].unique()]
    value = options[0]['value'] if options else None
    return options, value

@app.callback(
    [
        dash.dependencies.Output('correlation-graph', 'figure'),
        dash.dependencies.Output('correlation-table', 'data')
    ],
    [
        dash.dependencies.Input('sport-dropdown', 'value'),
        dash.dependencies.Input('subject-dropdown', 'value')
    ]
)
def update_graph_and_table(selected_sport, selected_subject):
    filtered = grouped_df[
        (grouped_df['Sport'] == selected_sport) &
        (grouped_df['Subject Line'] == selected_subject)
    ]
    fig = px.scatter(
        filtered,
        x='Click Rate (%)',
        y='Lifetime Giving',
        color='Age Group',
        size='Lifetime Giving',
        hover_data=['Subject Line'],
        title=f"Click Rate vs Giving for '{selected_subject}' ({selected_sport})"
    )
    return fig, filtered.to_dict('records')

if __name__ == '__main__':
    app.run_server(debug=True)
