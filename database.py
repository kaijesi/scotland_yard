import random
import sqlite3

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
    cursor.execute('INSERT INTO session (playercount, turn, status, map, mrx)\
                    VALUES (:playercount, 1, "session_running", :map_id, :mrx)',\
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
    # For ever turn you need to know:
    # What is the current session 
    #   Get this via a WHERE clause using .get('game_session') from the browser session
    #   Get this also joined with all map information via lookup already
    #   Function for this in database.py should return a dict with all values of this joined table
    #   Attention that the possible turns are currently saved in a JSON file, unparse this in the database.py function and return as a separate dict
    cursor = database_open()
    session_info = cursor.execute('SELECT * FROM session \
                                   LEFT JOIN map \
                                   ON session.map = map.map_id \
                                   WHERE session.session_id = :session_id').fetchall()

                                   # You can cast this as a dict (https://www.programcreek.com/python/example/3926/sqlite3.Row)
    