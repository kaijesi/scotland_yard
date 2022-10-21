import random
import sqlite3
import json

""" Collection of functions to interact with the game's database, e.g. creating/deleting new game sessions """
# Function that returns a usable cursor for the database
def database_open():
    global data
    data = sqlite3.connect('game_data.db')
    data.row_factory = sqlite3.Row
    cursor = data.cursor()
    return cursor

# Function that commits changes to the database
def commit_changes():
    data.commit()
    data.close()

# Function that creates a new game session in the database and returns its ID
def create_game(players, mrx, selected_map):
    cursor = database_open()
    # Find the map_id for the selected map
    map_id = int(cursor.execute('SELECT map_id FROM map WHERE name = :selected_map', {'selected_map' : selected_map}).fetchall()[0][0])
    # Create the session with the selected map
    cursor.execute('INSERT INTO session (playercount, turn, status, map, mrx, player_turn)\
                    VALUES (:playercount, 1, "session_running", :map_id, :mrx, 1)',\
                    {'playercount' : len(players), 'map_id' : map_id, 'mrx' : mrx})
    # Get the ID of the session just inserted
    session_id = cursor.lastrowid
    # Get random starting positions for law players
    possible_starting_positions_law = cursor.execute('SELECT position \
                                                  FROM starting_position \
                                                  WHERE mrx_position = 0 AND map = :map_id;', {'map_id' : map_id}).fetchall()
    # Get random starting position for mrx
    possible_starting_positions_mrx = cursor.execute('SELECT position \
                                                  FROM starting_position \
                                                  WHERE mrx_position = 1 AND map = :map_id;', {'map_id' : map_id}).fetchall()
    # Assign positions to players
    players_w_positions = dict()
    for player in players:
        if player != mrx:
            position = random.choice(possible_starting_positions_law)
            possible_starting_positions_law.remove(position)
            players_w_positions[player] = position
        else:
            position = random.choice(possible_starting_positions_mrx)
            players_w_positions[player] = position
            # No need to remove as per definition there can only be one mrx per session so the else branch should only happen once
    
    # Create players
    for name in players_w_positions.keys():
        position = int(players_w_positions.get(name)[0])
        if name != mrx:
            cursor.execute('INSERT INTO player (nickname, position, mrx, police, session, metro, bus, taxi, hidden_ferry, double_move)\
                            VALUES (:player, :position, 0, 0, :session_id, 4, 8, 11, 0, 0)', \
                            {'player' : name, 'position' : position, 'session_id' : session_id})
        else:
            # Mr. X has unlimited travel and there will be logic to not deduct any tickets but for debugging I'm adding them here (1000 each)
            cursor.execute('INSERT INTO player (nickname, position, mrx, police, session, metro, bus, taxi, hidden_ferry, double_move)\
                            VALUES (:player, :position, 1, 0, :session_id, 1000, 1000, 1000, 5, 2)', \
                            {'player' : name, 'position' : position, 'session_id' : session_id})

    commit_changes()
    return session_id

# Function that erases a session and all players for it by id of the session
def erase_session(session_id):
    cursor = database_open()
    # Delete the players
    cursor.execute('DELETE FROM player WHERE session = :session_id', {'session_id' : session_id})
    # Delete the session
    cursor.execute('DELETE FROM session WHERE session_id = :session_id', {'session_id' : session_id})
    commit_changes()

# Function that gets current session information joined with other information
def session_info(session_id):
    cursor = database_open()
    session_info = dict(cursor.execute('SELECT * FROM session \
                                   LEFT JOIN map \
                                   ON session.map = map.map_id \
                                   WHERE session.session_id = :session_id', {'session_id' : session_id}).fetchall()[0])
    commit_changes()
    return session_info

# Function that gets current players
def get_players(session_id):
    cursor = database_open()
    player_info = cursor.execute('SELECT * FROM player WHERE session = :session_id ORDER BY nickname ASC', {'session_id' : session_id}).fetchall()
    commit_changes()
    return player_info 

# Function that gets a specific player's information
def get_player(player_id):
    cursor = database_open()
    player_info = cursor.execute('SELECT * FROM player WHERE player_id = :player_id', {'player_id' : player_id}).fetchall()[0]
    return player_info

# Function that updates the provided field of the player to the provided value
def player_update(player_id, field, value):
    cursor = database_open()
    query = 'UPDATE player SET ' + str(field) + ' = ' + str(value) + ' WHERE player_id = ' + str(player_id)
    print(query)
    cursor.execute(query)
    commit_changes()  

# Function that updates the provided field of the session to the provided value
def session_update(session_id, field, value):
    cursor = database_open()
    query = 'UPDATE session SET ' + str(field) + ' = ' + str(value) + ' WHERE session_id = ' + str(session_id)
    cursor.execute(query)
    commit_changes()

# Function that finds the current move option for a given player in a session
def get_moves(session_id, player_id):
    cursor = database_open()
    # Find the player's current position
    players = get_players(session_id)
    current_position = None
    for player in players:
        dict(player)
        if player['player_id'] == player_id:
            current_position = player['position']
    # Get the JSON move map for the current session's map
    current_map = dict(cursor.execute('SELECT map FROM session WHERE session_id = :session_id', {'session_id' : session_id}).fetchall()[0])
    map_id = current_map['map']
    json_string = dict(cursor.execute('SELECT json FROM map WHERE map_id = :map_id', {'map_id' : map_id}).fetchall()[0])['json']
    # Gets the move options from the given map JSON and the player's position
    move_options = [position_options for position_options in json.loads(json_string) if position_options['position'] == str(current_position)][0]
    return move_options