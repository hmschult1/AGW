import pandas as pd
import dash
from dash import dcc, html
import dash_table

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
click_df = click_df[(click_df['Click Rate (%)'].notna()) & (click_df['Click Rate (%)'] >= 0)]

# === Merge giving and click rate data ===
combined_df = mapped_giving.merge(
    click_df[['Subject Line', 'Age Group', 'Click Rate (%)']],
    on=['Subject Line', 'Age Group'], how='inner'
)

# === Add count of givers and clickers ===
combined_df['Giver'] = combined_df['Lifetime Giving'] > 0
combined_df['Clicked'] = combined_df['Click Rate (%)'] > 0

# === Group for table ===
grouped_df = combined_df.groupby(['Sport', 'Age Group', 'Subject Line'], observed=True).agg({
    'Click Rate (%)': 'mean',
    'Giver': 'sum',
    'Clicked': 'sum'
}).reset_index().rename(columns={'Giver': 'Number of Givers', 'Clicked': 'Number of Clickers'})

# === Compute conversion rate ===
grouped_df['Click-to-Giver Conversion Rate (%)'] = grouped_df.apply(
    lambda row: (row['Number of Givers'] / row['Number of Clickers'] * 100) if row['Number of Clickers'] > 0 else 0,
    axis=1
)

# === Ensure Age Group Order for Plotting ===
age_order = ['0-18', '19-30', '31-40', '41-50', '51-60', '61-70', '70+']
grouped_df['Age Group'] = pd.Categorical(grouped_df['Age Group'], categories=age_order, ordered=True)

# === Dash App ===
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Click Rate and Giving by Sport and Age Group", style={'textAlign': 'center'}),

    html.Label("Select Sport:"),
    dcc.Dropdown(
        id='sport-dropdown',
        options=[{"label": sport, "value": sport} for sport in grouped_df['Sport'].unique()],
        value=grouped_df['Sport'].unique()[0]
    ),

    html.Label("Select Subject Line:"),
    dcc.Dropdown(id='subject-dropdown'),

    html.Br(),
    html.H3("Click Rate by Age Group"),
    dcc.Graph(id='click-rate-graph'),

    html.Br(),
    html.H3("Data Table"),
    dash_table.DataTable(
        id='correlation-table',
        columns=[{"name": col, "id": col} for col in [
            'Sport', 'Age Group', 'Subject Line',
            'Click Rate (%)', 'Number of Givers', 'Number of Clickers',
            'Click-to-Giver Conversion Rate (%)'
        ]],
        style_table={'overflowX': 'auto'},
        style_cell={'padding': '5px', 'textAlign': 'center'},
        style_header={'fontWeight': 'bold'}
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
    dash.dependencies.Output('correlation-table', 'data'),
    [
        dash.dependencies.Input('sport-dropdown', 'value'),
        dash.dependencies.Input('subject-dropdown', 'value')
    ]
)
def update_table(selected_sport, selected_subject):
    filtered = grouped_df[
        (grouped_df['Sport'] == selected_sport) &
        (grouped_df['Subject Line'] == selected_subject)
    ]
    return filtered.to_dict('records')

@app.callback(
    dash.dependencies.Output('click-rate-graph', 'figure'),
    [
        dash.dependencies.Input('sport-dropdown', 'value'),
        dash.dependencies.Input('subject-dropdown', 'value')
    ]
)
def update_click_rate_graph(selected_sport, selected_subject):
    filtered = grouped_df[
        (grouped_df['Sport'] == selected_sport) &
        (grouped_df['Subject Line'] == selected_subject)
    ].sort_values('Age Group')

    return {
        'data': [{
            'x': filtered['Age Group'],
            'y': filtered['Click Rate (%)'],
            'type': 'bar',
            'name': selected_subject
        }],
        'layout': {
            'title': f"Click Rate by Age Group for {selected_sport}",
            'xaxis': {'title': 'Age Group'},
            'yaxis': {'title': 'Click Rate (%)'},
            'margin': {'l': 60, 'r': 20, 't': 40, 'b': 60}
        }
    }

if __name__ == '__main__':
    app.run_server(debug=True)
