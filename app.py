from crypt import methods
import os
from flask import Flask, redirect, render_template, request, url_for, session
import database

# Set up app object
app = Flask(__name__)
app.secret_key = os.urandom(12).hex()
app.session_permanent = False

# Set up error messages dict (put this into separate module if it becomes too big)
error_messages = {'running_session' : 'There is already a running game session!'}

# Home page
@app.route('/')
def home():
    return render_template('index.html')

# Session setup page route
@app.route('/session-setup', methods=['GET'])
def session_setup():
    if session.get('game_session'):
        return render_template('error.html', error_code='running_session', message=error_messages['running_session'])
    else:
        return render_template('session-setup.html')

# Session erase (e.g. via button or after game closure)
@app.route('/session-erase', methods=['POST'])
def session_erase():
    # Erase game session from database
    database.erase_session(session.get('game_session'))
    # Pop game session from browser session
    session.pop('game_session', None)
    # Return to Home Page
    return redirect(url_for('home'))

# Player setup page
@app.route('/player-setup', methods=['POST'])
def player_setup():
    # Gather game session information from the form
    selected_map = request.form.get('mapselector').capitalize()
    # TO DO: Validation, find out if a map with this name exists
    players = int(request.form.get('playercount'))
    return render_template('player-setup.html', selected_map=selected_map, players=players)

# Start game page
@app.route('/start-game', methods=['POST'])
def start_game():
    # See if there is already a game session for the current browser session
    if session.get('game_session'):
        # TO DO: Expand this to allow for discarding the current session and creating a new one
        return render_template('error.html', error_code='running_session', message=error_messages['running_session'])
    # Gather game session and player information from the form
    information = request.form
    # Get playernames
    players = dict()
    for i in range(int(information.get('playercount'))):
        players[i + 1] = information.get(str(i + 1))
    # Get mrx name
    mrx = players[int(information.get('mrx'))]
    # Get map
    selected_map = information.get('selected_map').lower()
    # Create game session (function returns ID)
    game_session = database.create_game(players.values(), mrx, selected_map)
    session['game_session'] = game_session

    return render_template('start-game.html', information=information, session=session['game_session'])






