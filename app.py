import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from data_preprocessing import read_data, make_rfm, make_rfm_scores
from io import StringIO
import dash_bootstrap_components as dbc


data = read_data(path="Data/RFM_MEGAMAL_UPDATE.csv")
rfm = make_rfm(data)
rfm_scores = make_rfm_scores(rfm)


def generate_selected_group_data(segment):
    custom_df = rfm_scores[rfm_scores['Segment'] == segment][['phone_number', 'customer_name']]
    return custom_df


segment_product_counts = rfm_scores.groupby('Segment').size().reset_index(name='Count')

information = {
    "Lost Cheap Customers": "They don't have a good shopping history and haven't bought from us for a long time",
    "Lost Valuable Customers": "They have a good shopping history and haven't bought from us for a long time. we "
                               "suggest sending them back to your stores by text or call",
    "Need Attention (Normal Customers)": "They are who have normal shopping history and"
                                         " Buying them is normal and you can return them to your stores sooner"
                                         " by sending long-term credits.",
    "New Customers": "They are who bought recently from your brand and has not good shop history yet"
                     "You have to turn them into your regular customers by offering solutions.",
    "Potential To Be Best": "They are the people who buy from you continuously and have a good buying history,"
                            " they are your regular customers",
    "Best Customers": "They are your stars, they have the best shopping and more frequently shopping",
    "Others": "They are who haven't bought from us for an almost long time and have not good shopping history."}

external_stylesheets = [dbc.themes.MORPH]
# Create app theme
# external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
# Creating my dashboard application
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Define layout
app.layout = html.Div([
    html.H3("RFM Customer Segments by Value", style={'display': 'inline-block', 'vertical-align': 'middle',
                                                     'margin-left': '50px', 'margin-top': '20px'}),

    html.Div([
        dbc.Button('Help', id='help-button', n_clicks=0, color='primary', outline=True),
    ], style={'display': 'inline-block', 'vertical-align': 'middle', 'margin-right': '20px', 'margin-left': '890px'}),

    html.Div([dcc.Graph(
        id='treemap',
        figure=px.treemap(segment_product_counts,
                          path=['Segment'],
                          values='Count',
                          color='Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                          title='RFM Customer Segments by Value',
                          branchvalues='total')
    ),
    ]),
    html.Div(id='help-modal', style={'display': 'none'}, children=[
        html.Div([
            dcc.Markdown("""
                    This is a guide for using your dashboard.

                    All customers split in 6 groups based on their behaviours.
                    It will be possible one or more groups don't will create based on sales data.
                    you can click on each group in treemap and see the information and our suggestions about that group
                    and also there is a `download button` that give customers name and phone number in `csv` format who
                    are in that group. 

                    Enjoy using the dashboard!
                """, style={'color': 'white', 'background-color': 'rgba(13,152,186, 0.7)', 'padding': '10px',
                            'border-radius': '10px'}),

        ], style={'position': 'fixed', 'top': '5%', 'left': '65%', 'transform': 'translate(-40%, -13%)'}),
        html.Div(id='modal-background',
                 style={'position': 'fixed', 'top': 0, 'left': 0, 'width': '100%', 'height': '80%',
                        'background-color': 'rgba(0, 0, 0, 0.5)', 'display': 'none'}),
    ]),

    html.Div([
        html.Div(id='info-output'),
        dbc.Button("Download CSV", id='download-btn', n_clicks=0),  # Using Bootstrap Button
        dcc.Download(id="download-data"),
    ], style={'margin-left': '50px', 'margin-top': '30px'}),

])

# Your other imports and code

# Initialize info_state as an empty dictionary
info_state = {'segment': None, 'visible': False}


# Updated callback to handle toggling info visibility
@app.callback(
    [Output('info-output', 'children'),
     Output('info-output', 'style'),
     Output('download-btn', 'style')],
    [Input('treemap', 'clickData'),
     Input('download-btn', 'n_clicks'),
     Input('help-button', 'n_clicks')],
    prevent_initial_call=True
)
def display_info_and_download(clickData, n_clicks, help_clicks):
    # Initialize values
    info = ""
    info_style = {'display': 'none'}  # Hide the info div
    btn_style = {'display': 'none'}  # Hide the button

    # Check if treemap is clicked
    if clickData:
        clicked_segment = clickData['points'][0].get('label', "")

        # If the same segment is clicked again, hide the info
        if info_state['segment'] == clicked_segment:
            info_state['visible'] = not info_state['visible']
        else:
            info_state['segment'] = clicked_segment
            info_state['visible'] = True

        # Segment clicked
        if info_state['visible']:
            info = f"{clicked_segment} : {information[clicked_segment]}"
            info_style = {'display': 'block'}  # Show the info div
            btn_style = {'display': 'block'}  # Show the button

    # Toggle the modal based on the help button click
    if help_clicks and help_clicks % 2 == 1:
        modal_style = {'display': 'block'}
        modal_bg_style = {'display': 'block'}
    else:
        modal_style = {'display': 'none'}
        modal_bg_style = {'display': 'none'}

    return info, info_style, btn_style


# Callback to handle CSV download
@app.callback(
    Output("download-data", "data"),
    Input('download-btn', 'n_clicks'),
    prevent_initial_call=True
)
def download_csv(n_clicks):
    if n_clicks:
        # Replace this with your logic to generate the CSV data for the selected group
        df_selected_group = generate_selected_group_data(info_state['segment'])
        # Create a CSV file in memory
        csv_buffer = StringIO()
        df_selected_group.to_csv(csv_buffer, index=False)

        # Return the CSV file for download
        return dict(content=csv_buffer.getvalue(), filename=f"{info_state['segment']}_customer_data.csv")


# Define callback to update the graph
@app.callback(
    Output('treemap', 'figure'),
    Input('treemap', 'relayoutData')
)
def update_graph(relayout_data):
    # Assuming you have defined rfm_scores and grouped it into segment_product_counts
    segment_product_counts = rfm_scores.groupby('Segment').size().reset_index(name='Count')
    segment_product_counts = segment_product_counts.sort_values('Count', ascending=False)

    # Set the theme for the treemap
    fig = px.treemap(segment_product_counts,
                     path=['Segment'],
                     values='Count',
                     color='Segment', color_discrete_sequence=px.colors.qualitative.Pastel,
                     title='RFM Customer Segments by Value',
                     branchvalues='total')

    fig.update_layout(template='plotly',
                      plot_bgcolor='rgba(255, 255, 255, 0.5)',
                      # Change the background color here (RGB values with alpha for transparency)
                      paper_bgcolor='rgba(255, 255, 255, 0.5)'  # Change the plot area background color here
                      )  # Change the theme here
    return fig


@app.callback(
    Output('help-modal', 'style'),
    Output('modal-background', 'style'),
    Input('help-button', 'n_clicks'),
    prevent_initial_call=True
)
def toggle_modal(help_clicks):
    if help_clicks is None:
        help_clicks = 0
    if help_clicks % 2 == 1:  # Odd number of clicks on Help or Close button
        return {'display': 'block'}, {'display': 'block'}
    else:
        return {'display': 'none'}, {'display': 'none'}


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
