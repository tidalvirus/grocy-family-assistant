import dash
from dash import html
from dash import dcc
#import dash_core_components as dcc
#import dash_html_components as html
from pygrocy import Grocy

# Obtain a grocy instance
grocy = Grocy("host", "key", port = 443)

# Get users and chores
users = grocy.users()
chores = grocy.chores(get_details=True)

# Create the Dash app
app = dash.Dash(__name__)

# Define the layout
app.layout = html.Div([
    html.H1('Chores Dashboard'),
    html.Label('Select your name:'),
    dcc.Dropdown(
        options=[{'label': user.display_name, 'value': user.id} for user in users]),
#        value=users.id),#[0]['id']
    html.Label('Select the chore you completed:'),
    dcc.Dropdown(#chores, id='chores-list'),
        options=[{'label': chore.name, 'value': chore.id} for chore in chores]),
#        value=chores[0]['id']
#    ),
    html.Button('Submit', id='submit-button', n_clicks=0),
    html.Div(id='output')
])

# Define the callback
@app.callback(
    dash.dependencies.Output('output', 'children'),
    [dash.dependencies.Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('user-dropdown', 'value'),
     dash.dependencies.State('chore-dropdown', 'value')])
def update_output(n_clicks, user_id, chore_id):
    # Update the database with the chore completion
    grocy.execute_chore(chore_id, user_id)
    return 'Chore completed!'

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
