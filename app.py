from crypt import methods
import os
from re import I
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
    # TO DO: Don't allow duplicate names
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
    # Sort the players, mrx gets 1, other players get following numbers based on their IDs ascending
    police_players = [player for player in players if player['mrx']==0]
    police_player_ids = sorted([player['player_id'] for player in police_players])
    player_sorting = dict()
    i = 2
    for id in police_player_ids:
        player_sorting[i] = id
        i += 1
    # Find out if the current turn is over, if so, initiate next turn by increasing turn count and setting player turn back to 1
    if session_info['player_turn'] == session_info['playercount'] + 1:
        database.session_update(session_id, 'turn', session_info['turn'] + 1)
        database.session_update(session_id, 'player_turn', 1)
        return redirect(url_for('game-session'))
    # Find out whose turn it is (1 = mrx, other players ascending by player id)
    # If it's player turn 1 within overall turn, mrx needs to move
    if session_info['player_turn'] == 1:
        current_player = session_info['mrx']
        current_player_id = [player for player in players if player['mrx']==1][0]['player_id']
    # For all other turns, identify who's turn it is based on the player_sorting dict which stores the player ids
    else:
        current_player_id = player_sorting[session_info['player_turn']]
        for player in players:
            if player['player_id'] == current_player_id:
                current_player = player['nickname']

    # Find out which move options the current player has
    move_options = database.get_moves(session_id, current_player_id)
    # TO DO: Add the tickets logic to this, meaning only show the police players options for which they still have tickets left
    # TO DO: Test this function!
    # No two police players can be on the same field (but they can with mrx, ending the game)
    player_positions = [player['position'] for player in players if player['mrx']==0]
    for transport_method in ('metro','bus','taxi','ferry'):
        for item in move_options[transport_method]:
            if item in player_positions:
                move_options[transport_method].remove(item)
    # Render the current playing field
    return render_template('game-session.html', session_info=session_info, image=image, players=players, current_player_id=current_player_id, current_player=current_player, move_options=move_options)

# Process the move of a player when one of the move options is selected
@app.route('/process_turn', methods=['POST'])
def process_turn():
    move_selection = request.form
    print(move_selection)
    player_id = move_selection.get('current_player_id')
    mode_of_transport = move_selection.get('mode_of_transport')
    # Move the player to the position
    database.player_update(player_id,'position',move_selection.get('selected_move'))
    # Deduct the ticket from the player's account
    # Get current value for this player
    current_tickets = [dict(player) for player in database.get_players(move_selection.get('session_id')) if player['player_id']==int(player_id)][0].get(mode_of_transport)
    print(mode_of_transport, current_tickets)
    # database.player_update(player_id,mode_of_transport,)
    # Check for mrx lose conditions (are mrx and one of the police players on one field OR are all move options for mrx taken by police players)
    # Check for mrx win conditions (has the last player turn in round 24 been reached)
    # Update the session info so it becomes the next player's turn
    return redirect(url_for('game_session'), code=307)

