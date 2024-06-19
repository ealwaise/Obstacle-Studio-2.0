from collections import deque
import pandas as pd
from src import sc_data

def deaths(player: str, unit: str, quantifier: str, num: int) -> str:
    """Returns a death count condition."""
    return '\tDeaths("{}", "{}", {}, {});\n'.format(player, unit, quantifier, num)
    
def EUD_action(addr: int, operation: str, value: int) -> str:
    """Returns an EUD action."""
    return '\tMemoryAddr({}, {}, {});\n'.format(hex(addr), operation, value)

def masked_EUD_action(addr: int, operation: str, value: int, mask: int) -> str:
    """Returns an EUD action with a mask."""
    return '\tMasked MemoryAddr({}, {}, {}, {});\n'.format(hex(addr), operation, value, hex(mask))
    
def create_unit(player: str, unit: str, num: int, loc: str) -> str:
    """Returns a Create Unit action."""
    return '\tCreate Unit("{}", "{}", {}, "{}");\n'.format(player, unit, num, loc)
    
def create_unit_with_properties(player: str,
                                unit: str,
                                num: int,
                                loc: str,
                                properties: int) -> str:
    """Returns a Create Unit with Properties action."""
    return '\tCreate Unit with Properties("{}", "{}", {}, "{}", {});\n'.format(player,
                                                                                 unit,
                                                                                 num,
                                                                                 loc,
                                                                                 properties)

def kill_unit_at_location(player: str, unit: str, quantifier: str, loc: str) -> str:
    """Returns a Kill Unit At Location action."""
    return '\tKill Unit At Location("{}", "{}", {}, "{}");\n'.format(player, unit, quantifier, loc)

def kill_unit(player: str, unit: str) -> str:
    """Returns a Kill Unit action."""
    return '\tKill Unit("{}", "{}");\n'.format(player, unit)
    
def remove_unit(player: str, unit: str) -> str:
    """Returns a Remove Unit action."""
    return '\tRemove Unit("{}", "{}");\n'.format(player, unit)
    
def remove_unit_at_location(player: str, unit: str, quantifier: str, loc: str) -> str:
    """Returns a Remove Unit At Location action."""
    return '\tRemove Unit At Location("{}", "{}", {}, "{}");\n'.format(player,
                                                                       unit,
                                                                       quantifier,
                                                                       loc)
    
def set_deaths(player: str, unit: str, quantifier: str, num: int) -> str:
    """Returns a Set Deaths action."""
    return '\tSet Deaths("{}", "{}", {}, {});\n'.format(player, unit, quantifier, num)
    
def move_unit(player, unit, quantifier, start, end):
    """Returns a Move Unit action."""
    return '\tMove Unit("{}", "{}", {}, "{}", "{}");\n'.format(player,
                                                               unit,
                                                               quantifier,
                                                               start,
                                                               end)
    
def wait(time: int) -> str:
    """Returns a Wait action."""
    return '\tWait({});\n'.format(int)
    
def preserve() -> str:
    """Returns a Preserve Trigger action."""
    return '\tPreserve Trigger();\n'

def comment(text: str) -> str:
    """Returns a Comment action."""
    return '\tComment("{}");\n'.format(text)
    
def format_comment(ob_num: int,
                   count_num: int,
                   part_num: int,
                   multi_part: bool,
                   options: dict) -> str:
    """Formats a comment depending on the input schema."""
    pieces = ['{}{}'.format(options['Obstacle text'], ob_num),
              '{}{}'.format(options['Count text'], count_num),
              '{}{}'.format(options['Part text'], part_num)]
    if not multi_part:
        pieces.pop()
    return options['Delineator'].join(pieces)

def create_trigger(player: str, conditions: list[str], actions: list[str]) -> str:
    """Creates a Starcraft trigger."""
    trigger = ['Trigger("{}"){{\nConditions:\n'.format(player)]
    trigger.extend(conditions)
    trigger.append('\nActions:\n')
    trigger.extend(actions)
    trigger.append('}\n\n//-----------------------------------------------------------------//')
    return ''.join(trigger)
    
def move_loc(ID: int, position_delta: list[int]):
    """Returns a list of EUD actions which move a location.
    
    ID is the ID of the location to be moved.
    position_delta is the change in the location's position
    """
    position_delta = [int(delta) for delta in position_delta]
    addr_left = 5823584 + 20*(ID - 1)
    actions = []
    if position_delta[0] < 0:
        actions.append(EUD_action(addr_left, 'Subtract', abs(position_delta[0])))
        actions.append(EUD_action(addr_left + 8, 'Subtract', abs(position_delta[0])))
    if position_delta[0] > 0:
        actions.append(EUD_action(addr_left, 'Add', abs(position_delta[0])))
        actions.append(EUD_action(addr_left + 8, 'Add', abs(position_delta[0])))
    if position_delta[1] < 0:
        actions.append(EUD_action(addr_left + 4, 'Subtract', abs(position_delta[1])))
        actions.append(EUD_action(addr_left + 12, 'Subtract', abs(position_delta[1])))
    if position_delta[1] > 0:
        actions.append(EUD_action(addr_left + 4, 'Add', abs(position_delta[1])))
        actions.append(EUD_action(addr_left + 12, 'Add', abs(position_delta[1])))
    return actions
    
def is_unit(explosion_ID):
    """Checks if explosion_ID corresponds to a unit or a sprite."""
    return sc_data.event_data.loc[explosion_ID]['Type'] == 'Unit'
    
def get_unit(explosion_ID):
    """Gets the unit name corresponding to explosion_ID."""
    return sc_data.event_data.loc[explosion_ID]['Name']
    
def get_player(num: int) -> str:
    """Converts a number to a string describing a player in a Starcraft trigger."""
    if num == 0:
        return 'Current Player'
    if num <= 8:
        return 'Player {}'.format(int(num))
    return 'All players'
    
def count_triggers(use_frames: bool,
                   delays: list[int],
                   location_names: list[int],
                   location_IDs: list[int],
                   location_centers: list[int],
                   explosions: pd.DataFrame,
                   walls: pd.DataFrame,
                   teleports: pd.DataFrame,
                   audio_mapping: pd.DataFrame,
                   num_counts: int,
                   count_num: int,
                   ob_num: int,
                   death_count_options: dict,
                   trigger_player: str,
                   kill_remove: str,
                   bounding_unit: str,
                   force_name: str,
                   comment_options: dict) -> str:
    """Generates the triggers to create a count of an obstacle."""
    add_comments = comment_options['Add comments']
    DC_player = death_count_options['Player']
    ob_tracker_unit = death_count_options['Ob']
    count_tracker_unit = death_count_options['Count']
    delay_tracker_unit = death_count_options['Delay']
    delay = delays[count_num - 1]
    triggers = []
    
    # Generate audio mapping trigger if an audio mapping has been applied to this count.
    if use_frames:
        # Add a new column indicating how many frames before the explosion the trigger should fire.
        frames = pd.DataFrame(columns=['Frames'], data=audio_mapping.apply(
            lambda row: int(sc_data.event_data.loc[row['Explosion']]['Audio']),
            axis=1
        ))
        audio = pd.concat([audio_mapping, frames], axis=1)

        # The audio trigger should fire when the death counter for the count tracking unit is equal
        # to the current count, unless the previous delay was 1 frame and the audio needs to play 1
        # frame before the explosion, in which case the trigger should fire when the death counter
        # is equal to the previous count.
        prev_count = (count_num - 2) % num_counts + 1
        audio_actions = [[], []]
        for frames in audio['Frames'].unique():
            for index, row in audio[audio['Frames'] == frames].iterrows():
                explosion_ID = row.loc['Explosion']
                DC_unit_index = row.loc['DC Unit']
                DC_unit = sc_data.unit_list[DC_unit_index]
                audio_actions[frames - 1].append(set_deaths(force_name,
                                                            DC_unit,
                                                            'Set to',
                                                            1))
            audio_actions[frames - 1].append(preserve())
            # Adds a comment according to the user options.
            if add_comments:
                audio_actions[frames - 1].append(
                    comment('{}{}'.format(format_comment(ob_num,
                                                         count_num,
                                                         1,
                                                         False,
                                                         comment_options),
                                          comment_options["Audio text"]))
                )
                
        # Create trigger for audio that should play on the same frame as the explosion.
        if audio_actions[0]:
            audio_conditions = [deaths(DC_player, ob_tracker_unit, 'Exactly', ob_num),
                                deaths(DC_player, count_tracker_unit, 'Exactly', count_num),
                                deaths(DC_player, delay_tracker_unit, 'Exactly', 1)]
            triggers.append(create_trigger(trigger_player, audio_conditions, audio_actions[0]))
        
        # Create trigger for audio that should play 1 frame before the explosion.        
        if audio_actions[1]:
            prev_count = (count_num - 2) % num_counts + 1
            audio_count_num = count_num if delays[prev_count - 1] > 1 else prev_count
            frames = 2 if delays[prev_count - 1] > 1 else 1
            audio_conditions = [deaths(DC_player, ob_tracker_unit, 'Exactly', ob_num),
                                deaths(DC_player, count_tracker_unit, 'Exactly', audio_count_num),
                                deaths(DC_player, delay_tracker_unit, 'Exactly', frames)]
            triggers.append(create_trigger(trigger_player, audio_conditions, audio_actions[1]))
    
    conditions, actions = [], deque()
    # Conditions which track the ob and count numbers.
    conditions.append(deaths(DC_player, ob_tracker_unit, 'Exactly', ob_num))
    conditions.append(deaths(DC_player, count_tracker_unit, 'Exactly', count_num))

    # The condition that the frame counter is at 0 is necessary if using frame-based delays.
    if use_frames:
        conditions.append(deaths(DC_player, delay_tracker_unit, 'Exactly', 0))
    
    sprite_used = False
    prev_explosion_ID = -1
    # Iterate through all locations with explosion events which occur during the input count.
    for loc in sorted(explosions['Location'].unique().astype(int)):
        explosions_loc = explosions[explosions['Location'] == loc].sort_values(['y', 'x'])
        loc_name = location_names[loc - 1]
        ID = location_IDs[loc - 1]
        center_x, center_y = location_centers[loc - 1]
        prev_x, prev_y = center_x, center_y
        positions = {
            (event.loc['x'], event.loc['y']) for index, event in explosions_loc.iterrows()
        }
        
        # Iterate through all positions at which an explosion occurs at the given location.
        for (x, y) in positions:
            explosions_loc_pos = explosions_loc[(explosions_loc['x'] == x)
                                                & (explosions_loc['y'] == y)]
            
            # Iterate through all explosions occuring at the given location and position.
            for index, event in explosions_loc_pos.iterrows():
                player = get_player(event.loc['Player'])
                explosion_ID = event.loc['Explosion']
                x, y = event.loc['x'], event.loc['y']
                
                # Move the location to the position of the explosion.
                actions.extend(move_loc(ID, [x - prev_x, y - prev_y]))
                prev_x, prev_y = x, y
                
                # Create the explosion.
                # We check if the explosion is a unit, as we must otherwise create a Scanner Sweep and
                # create a EUD action to change the image of Scanner Sweep.
                unit = 'Scanner Sweep'
                if is_unit(explosion_ID):
                    unit = get_unit(explosion_ID)
                else:
                    sprite_used = True
                    if explosion_ID != prev_explosion_ID:
                        actions.append(masked_EUD_action(6710360, 'Set To', int(explosion_ID), 65535))
                        prev_explosion_ID = explosion_ID
                actions.append(create_unit(player, unit, 1, loc_name))
                if kill_remove == 'Remove Unit' and unit != 'Scanner Sweep':
                    actions.append(kill_unit_at_location(player, unit, 'All', loc_name))
            
            # Create the actions which kill the player at the given position.
            if kill_remove == "Kill Unit":
                actions.append(kill_unit_at_location('All players', 'Men', 'All', loc_name))
            else:
                actions.append(remove_unit_at_location(force_name, bounding_unit, 'All', loc_name))
                
        # Move the location back to its original position.
        actions.extend(move_loc(ID, [center_x - prev_x, center_y - prev_y]))
                
    # Iterate through all locations with wall events which occur during the input count.
    for loc in sorted(walls['Location'].unique().astype(int)):
        walls_loc = walls[walls['Location'] == loc].sort_values(['x', 'y'])
        loc_name = location_names[loc - 1]
        ID = location_IDs[loc - 1]
        center_x, center_y = location_centers[loc - 1]
        prev_x, prev_y = center_x, center_y
        
        # Iterate through all wall events occuring at the given location.
        for index, event in walls_loc.iterrows():
            player = get_player(event.loc['Player'])
            unit = get_unit(event.loc['Unit'])
            add_remove = event.loc['Add/Remove']
            x, y = event.loc['x'], event.loc['y']
            
            # Move the location to the position of the explosion.
            position_delta = [x - prev_x, y - prev_y]
            actions.extend(move_loc(ID, position_delta))
            prev_x, prev_y = x, y
            
            # Create/remove the wall.
            if add_remove == 0:
                actions.append(remove_unit_at_location('All players', unit, 'All', loc_name))
            elif add_remove == 1:
                actions.append(kill_unit_at_location('All players', unit, 'All', loc_name))
            else:
                # We use create unit with properties to make the wall invincible.
                actions.append(create_unit_with_properties(player, unit, 1, loc_name, 3))
                
        # Move the location back to its original position.
        actions.extend(move_loc(ID, [center_x - prev_x, center_y - prev_y]))

    # Iterate through all teleport events which occur during the input count.
    for index, event in teleports.sort_values('Location from').iterrows():
        player_from = get_player(event.loc['Player from'])
        image_from = event.loc['Image from']
        loc_from = event.loc['Location from']
        loc_from_name = location_names[loc_from - 1]
        player_to = get_player(event.loc['Player to'])
        image_to = event.loc['Image to']
        loc_to = event.loc['Location to']
        loc_to_name = location_names[loc_to - 1]
        data_from = [player_from, image_from, loc_from_name]
        data_to = [player_to, image_to, loc_to_name]
        
        # Create the explosions used to indicate the teleport start and end locations.
        for data in [data_from, data_to]:
            player, image, loc_name = data
            # If the explosion is a unit, we create the unit with the hallucinated property.
            # Otherwise, we must create a Scanner Sweep.
            unit = 'Scanner Sweep'
            if is_unit(image):
                unit = get_unit(image)
                actions.append(create_unit_with_properties(player, unit, 1, loc_name, 1))
                actions.append(kill_unit_at_location(player, unit, 'All', loc_name))
            else:
                sprite_used = True 
                actions.append(create_unit(player, unit, 1, loc_name))

        # Move the player from loc_from to loc_to.
        actions.append(move_unit(force_name, bounding_unit, 'All', loc_from_name, loc_to_name))
        
    # If a sprite explosion or teleport marker was used, we must remove the Scanner Sweep units.
    if sprite_used:
        actions.append(remove_unit("All players", "Scanner Sweep"))

    # Append the actions which create the delay and cycle to the next count.
    if use_frames:
        actions.append(set_deaths(DC_player,
                                  count_tracker_unit,
                                  'Set to',
                                  count_num % num_counts + 1))
        actions.append(set_deaths(DC_player, delay_tracker_unit, 'Set to', delay))
    else:
        actions.append(wait(delay))
    
    # We store the actions for a single trigger in actions_trigger.
    # We need to reserve an extra action if using comments.
    action_limit = 62 if add_comments else 63
    multi_part = len(actions) > action_limit
    actions_trigger = []
    part_num = 1
    
    # Generate the triggers for the count.
    while actions:
        # If using frames, we need to ensure the actions which set the delay and set the next count
        # are in the same trigger
        if ((len(actions_trigger) == action_limit and len(actions) > 0)
            or (use_frames and len(actions_trigger) == action_limit - 1 and len(actions) == 2)):
            actions_trigger.append(preserve())
            if add_comments:
                actions_trigger.append(comment(format_comment(ob_num,
                                                              count_num,
                                                              part_num,
                                                              multi_part,
                                                              comment_options)))
            triggers.append(create_trigger(trigger_player,
                                           conditions,
                                           actions_trigger))
            actions_trigger.clear()
            part_num += 1
        actions_trigger.append(actions.popleft())
    actions_trigger.append(preserve())
    if add_comments:
        actions_trigger.append(comment(format_comment(ob_num,
                                                      count_num,
                                                      part_num,
                                                      multi_part,
                                                      comment_options)))
    triggers.append(create_trigger(trigger_player,
                                   conditions,
                                   actions_trigger))
    return '\n\n'.join(triggers)
                  
def obstacle_triggers(locations: list,
                      ob,
                      ob_num: int,
                      death_count_options: dict,
                      trigger_player: str,
                      kill_remove: str,
                      bounding_unit: str,
                      force_name: str,
                      comment_options: dict) -> str:
    """Generates the triggers to create an obstacle."""
    triggers = []
    delays = ob.delays
    use_frames = ob.use_frames
    num_counts = len(delays)
    location_names = [loc.name for loc in locations]
    location_IDs = [loc.ID for loc in locations]
    location_centers = [[loc.center().x(), loc.center().y()] for loc in locations]
    
    # Iterate through each count and create the corresponding triggers.

    for count in range(num_counts):
        explosions = ob.explosions[ob.explosions["Count"] == count + 1]
        walls = ob.walls[ob.walls["Count"] == count + 1]
        teleports = ob.teleports[ob.teleports["Count"] == count + 1]
        audio_mapping = ob.audio[ob.audio["Count"] == count + 1]
        triggers.append(count_triggers(use_frames,
                                       delays,
                                       location_names,
                                       location_IDs,
                                       location_centers,
                                       explosions,
                                       walls,
                                       teleports,
                                       audio_mapping,
                                       num_counts,
                                       count + 1,
                                       ob_num,
                                       death_count_options,
                                       trigger_player,
                                       kill_remove,
                                       bounding_unit,
                                       force_name,
                                       comment_options))
    return '\n\n'.join(triggers)