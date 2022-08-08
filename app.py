import os
from flask import Flask, redirect, render_template, request, url_for, session
import database
import helpers

# Set up app object
app = Flask(__name__)
app.secret_key = os.urandom(12).hex()

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

    return render_template('start-game.html', selected_map=selected_map, mrx=mrx, session=session['game_session'])

# TO DO: Turn page (shown on every turn)
@app.route('/game-session', methods=['POST'])
def game_session():
    # Get info about session
    session_info = database.session_info(session.get('game_session'))
    image = session_info['map_url']
    session_id = session_info['session_id']
    # Get info about players (as dict for easier further usage)
    players = database.get_players(session_id)
    for player in players:
        player = dict(player)
    # Find out if the current turn is over, if so, initiate next turn by increasing turn count and setting player turn back to 1
    if session_info['player_turn'] == session_info['playercount'] + 1:
        database.session_update(session_id, 'turn', session_info['turn'] + 1)
        database.session_update(session_id, 'player_turn', 1)
        return redirect(url_for('game-session'))
    # TO DO: Find out whose turn it is (1 = mrx, other players alphabetically)
    if session_info['player_turn'] == 1:
        current_player = session_info['mrx']

    # Find out which move options the current player has
    move_options = database.get_moves(session_id, current_player)
    
    # Render the current playing field
    return render_template('game-session.html', session_info=session_info, image=image, players=players, current_player=current_player, move_options=move_options)






