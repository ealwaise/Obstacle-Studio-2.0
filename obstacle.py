import pandas as pd
from PyQt6.QtCore import QPointF
import read_write
import sc_data

class Obstacle:
    """A storage class for obstacle data."""
    
    def __init__(self):
        super().__init__()
        
        # We store obstacle data in pandas data frames with numerical values.
        # self.explosions = pd.DataFrame(
            # {"Count": pd.Series(dtype='int'),
             # "Player": pd.Series(dtype='int'),
             # "Explosion": pd.Series(dtype='int'),
             # "Location": pd.Series(dtype='int'),
             # "x": pd.Series(dtype='int'),
             # "y": pd.Series(dtype='int')}
        # )
        self.explosions = pd.DataFrame(columns=["Count",
                                                "Player",
                                                "Explosion",
                                                "Location",
                                                "x",
                                                "y"])
        self.walls = pd.DataFrame(columns=["Count",
                                           "Player",
                                           "Unit",
                                           "Add/Remove",
                                           "Location",
                                           "x",
                                           "y"])
        self.teleports = pd.DataFrame(columns=["Count",
                                               "Player from",
                                               "Player to",
                                               "Image from",
                                               "Image to",
                                               "Location from",
                                               "Location to"])
        self.audio = pd.DataFrame(columns=["Count",
                                           "Explosion",
                                           "DC Unit"])
        self.use_frames = read_write.read_setting("Use frames")
        self.delays = [int(self.use_frames)]
    
    def set_timing_type(self, use_frames: bool) -> None:
        """Sets the timing type to frames if use_frames is true or waits otherwise."""
        self.use_frames = use_frames
        
    def delete_count(self, count: int) -> None:
        """Deletes the input count from the obstacle and shifts the later counts down."""
        self.explosions.drop(self.explosions[self.explosions["Count"] == count].index,
                             inplace=True)
        self.walls.drop(self.walls[self.walls["Count"] == count].index,
                        inplace=True)
        self.teleports.drop(self.teleports[self.teleports["Count"] == count].index,
                            inplace=True)
        self.audio.drop(self.audio[self.audio["Count"] == count].index,
                        inplace=True)
        self.shift_counts(count + 1, -1)
        
    def insert_count(self, count: int) -> None:
        """Inserts a new count at the input position and shifts later counts up."""
        self.shift_counts(count, 1)

    def shift_counts(self, lower: int, shift: int) -> None:
        """Shifts all counts which are >= lower by shift."""
        # Needed for count deletion and insertion.
        self.explosions.loc[self.explosions["Count"] >= lower, "Count"] += shift
        self.walls.loc[self.walls["Count"] >= lower, "Count"] += shift
        self.teleports.loc[self.teleports["Count"] >= lower, "Count"] += shift
        self.audio.loc[self.audio["Count"] >= lower, "Count"] += shift
        
        self.explosions.reset_index(drop=True, inplace=True)
        self.walls.reset_index(drop=True, inplace=True)
        self.teleports.reset_index(drop=True, inplace=True)
        self.audio.reset_index(drop=True, inplace=True)
        
    def delete_location(self, loc: int) -> None:
        """Deletes all obstacle events occuring at location number loc."""
        self.explosions.drop(
            self.explosions[self.explosions["Location"] == loc].index,
            inplace=True
        )
        self.walls.drop(
            self.walls[self.walls["Location"] == loc].index,
            inplace=True
        )
        self.teleports.drop(
            self.teleports[(self.teleports["Location from"] == loc)
            | (self.teleports["Location to"] == loc)].index,
            inplace=True
        ) 
        self.explosions.reset_index(drop=True, inplace=True)
        self.walls.reset_index(drop=True, inplace=True)
        self.teleports.reset_index(drop=True, inplace=True)
        self.delete_audio()
        self.shift_locations_down(loc)
        
    def shift_locations_down(self, lower: int) -> None:
        """Shifts all locations of number > lower down by 1."""
        # Needed for location deletion.
        self.explosions.loc[self.explosions["Location"] > lower, "Location"] -= 1
        self.walls.loc[self.walls["Location"] > lower, "Location"] -= 1
        self.teleports.loc[self.teleports["Location from"] > lower, "Location from"] -= 1
        self.teleports.loc[self.teleports["Location to"] > lower, "Location to"] -= 1
        
    def find_explosion(self, explosion: int) -> None:
        """Checks if the input explosion is present in the ob."""
        # Used to modify the audio mapping menus.
        return (self.explosions["Explosion"] == explosion).any()
        
    def find_explosion_in_count(self, count: int, explosion: int) -> None:
        """Checks if the input explosion is present in the ob during the input count."""
        # Used to modify the audio mapping menus.
        return ((self.explosions["Count"] == count)
                & (self.explosions["Explosion"] == explosion)).any()

    def find_explosion_at(self, count: int, explosion: int, loc: int, pos: QPointF) -> bool:
        """Checks for the existence of an explosion.
        
        explosion is the ID of the explosion being searched for.
        loc is the number of the location the explosion is at.
        (x, y) is the position of the explosion relative to the location.
        """
        # Used to ensure identical explosions aren't placed at the same point.
        return ((self.explosions["Count"] == count)
                & (self.explosions["Explosion"] == explosion)
                & (self.explosions["Location"] == loc)
                & (self.explosions["x"] == pos.x())
                & (self.explosions["y"] == pos.y())).any()
        
    def add_explosion(self,
                      count: int,
                      player: int,
                      explosion: int,
                      loc: int,
                      x: float,
                      y: float) -> None:
        """Adds an explosion to the obstacle.
        
        count is the count on which the explosion occurs.
        loc is the number of the location at which the explosion is placed.
        player is the player owning the explosion unit.
        (x, y) are the coordinates of the explosion relative to the location.
        """
        self.explosions.loc[len(self.explosions)] = [count, player, explosion, loc, x, y]
        
    def delete_explosion(self, count: int, explosion: int, loc: int, x: int, y: int) -> None:
        """Deletes an explosion at the input Location and coordinates occuring at the input count."""
        self.explosions.drop(self.explosions[(self.explosions["Count"] == count)
                              & (self.explosions["Explosion"] == explosion)
                              & (self.explosions["Location"] == loc)
                              & (self.explosions["x"] == x)
                              & (self.explosions["y"] == y)].index,
                              inplace=True)
        self.explosions.reset_index(drop=True, inplace=True)
        self.delete_audio()
        
    def search_wall(self, count: int, loc: int, pos: QPointF) -> list[int]:
        """Checks for a wall event. If a wall event is found, returns two integers, the first of
        which represents if the wall was placed, removed, or killed, and the other which represents
        the count on which the wall event occured. If no wall event is found, returns [-1, -1].
        
        Events prior to count will be searched for.
        loc is the location at which the wall occurs.
        pos is the position of the wall event being searched for relative to the location.
        """
        # Used to prevent overlapping wall placements / removals.
        num_counts = len(self.delays)
        for i in range(num_counts):
            prev_count = (count - i - 1) % num_counts + 1
            walls = self.walls[(self.walls["Count"] == prev_count)
                               & (self.walls["Location"] == loc)
                               & (self.walls["x"] == pos.x())
                               & (self.walls["y"] == pos.y())].reset_index(drop=True)
            if not walls.empty:
                return [walls.iloc[0]["Add/Remove"], walls.iloc[0]["Count"]]
        return [-1, -1]
        
    def find_wall(self, count: int, loc: int, pos: QPointF) -> int:
        """Returns the most recent prior count on which a wall was placed.
        Returns 0 if no such wall is found.

        Events prior to count will be searched for.
        loc is the number of the location at which the wall occurs.
        pos is the position of the wall event being searched for relative to the location.
        """
        # Used to properly display wall images.
        num_counts = len(self.delays)
        for i in range(num_counts):
            prev_count = (count - i - 1) % num_counts + 1
            if ((self.walls["Count"] == prev_count)
                & (self.walls["Location"] == loc)
                & (self.walls["Add/Remove"] == 2)
                & (self.walls["x"] == pos.x())
                & (self.walls["y"] == pos.y())).any():
                return prev_count
        return 0
        
    def place_wall(self, count: int, player: int, unit: int, loc: int, x: float, y: float) -> None:
        """Places a wall.
        
        count is the count number on which the wall will be placed.
        unit is the type of unit used as a wall.
        loc is the number of the Location at which the wall is placed.
        player is the player owning the wall unit.
        (x, y) are the coordinates of the wall.
        """
        self.walls.loc[len(self.walls)] = [count, player, unit, 2, loc, x, y]
    
    def remove_wall(self,
                    count: int,
                    unit: int,
                    removal_type: int,
                    loc: int,
                    x: float,
                    y: float) -> None:
        """Removes a wall.
        
        count is the count number on which the wall will be removed.
        unit is the type of unit used as a wall.
        removal_type indicates if the wall should be removed (0) or killed (1).
        loc is the number of the Location at which the wall was placed.
        player is the player owning the wall unit.
        (x, y) are the coordinates of the wall.
        """
        self.walls.loc[len(self.walls)] = [count, 9, unit, removal_type, loc, x, y]
        
    def delete_wall(self, count: int, loc: int, x: float, y: float) -> None:
        """Deletes a wall.
        
        count is the count number on which the wall was placed.
        loc is the number of the Location at which the wall was placed.
        player is the player owning the wall unit.
        (x, y) are the coordinates of the wall.
        """
        # Deletes the wall placement event.
        self.walls.drop(self.walls[(self.walls["Count"] == count)
                        & (self.walls["Location"] == loc)
                        & (self.walls["x"] == x)
                        & (self.walls["y"] == y)].index, inplace=True)
        
        # If the wall was removed, we also need to delete the wall removal event.
        num_counts = len(self.delays)
        for i in range(1, num_counts):
            later_count = ((count + i) - 1) % num_counts + 1
            if not ((self.walls["Count"] == later_count)
                    & (self.walls["Location"] == loc)
                    & (self.walls["x"] == x)
                    & (self.walls["y"] == y)).any():
                continue
            self.walls.drop(self.walls[(self.walls["Count"] == later_count)
                            & (self.walls["Location"] == loc)
                            & (self.walls["x"] == x)
                            & (self.walls["y"] == y)].index, inplace=True)
            break
        self.walls.reset_index(drop=True, inplace=True)
        
    def add_teleport(self,
                     count: int,
                     player_from: int,
                     player_to: int,
                     img_from: int,
                     img_to: int,
                     loc_from: int,
                     loc_to: int) -> None:
        """Adds a teleport to the obstacle.
        
        count is the count number on which the teleport occurs.
        The player will teleport from Location # loc_from to Location # loc_to.
        img_from is the type of decorative explosion used on loc_from.
        img_from is the type of decorative explosion used on loc_to.
        player is the player owning the decorative explosion unit.
        """
        row = [count, player_from, player_to, img_from, img_to, loc_from, loc_to]
        self.teleports.loc[len(self.explosions)] = row
                             
    def delete_teleport(self, count: int, loc: int) -> None:
        """Deletes a teleport event.
        
        count is the count on which the teleport occurs.
        loc is either the start or end location of the teleport.
        """
        self.teleports.drop(self.teleports[(self.teleports["Count"] == count)
                                           & (self.teleports["Location from"] == loc)
                                           & (self.teleports["Location to"] == loc)].index,
                                           inplace=True)
        self.teleports.reset_index(drop=True, inplace=True)
        
    def add_audio(self, count: int, explosion: int, dc_unit: int) -> None:
        """Adds an audio event.
        
        count is the count on which the audio event occurs.
        explosion is the ID of the explosion associated to the audio event.
        dc_unit is the index of the unit whose death count is associated to the audio event.
        """
        # If the input explosion doesn't occur in the input count, do nothing.
        if not self.find_explosion_in_count(count, explosion):
            return
            
        # If an identical audio event occurs in the input count, do nothing.
        if ((self.audio["Count"] == count)
            & (self.audio["Explosion"] == explosion)
            & (self.audio["DC Unit"] == dc_unit)).any():
            return

        self.audio.loc[len(self.audio)] = [count, explosion, dc_unit]
        
    def delete_audio(self) -> None:
        """Deletes audio events which correspond to explosions which have been deleted."""
        self.audio.drop(
            self.audio[~self.audio.apply(
                lambda row: self.find_explosion_in_count(row["Count"], row["Explosion"]),
                axis=1
                )].index,
            inplace=True
        )
        self.audio.reset_index(drop=True, inplace=True)
        
    def delete_audio_on_count(self, count: int) -> None:
        """Deletes audio events occuring during the input count."""
        self.audio.drop(self.audio[(self.audio["Count"] == count)].index, inplace=True)
        self.audio.reset_index(drop=True, inplace=True)
            
    def shift_events(self, loc: int, shift: QPointF) -> None:
        """Shifts the positions of all events at loc by shift."""
        # Needed for location resizing.
        self.explosions.loc[self.explosions["Location"] == loc, "x"] += shift.x()
        self.explosions.loc[self.explosions["Location"] == loc, "y"] += shift.y()
            
    def reset(self) -> None:
        """Deletes the obstacle data."""
        self.delays.clear()
        self.delays.append(int(self.use_frames))
        self.audio.drop(self.audio.index, inplace=True) 
        
    def serialize(self) -> dict:
        """Serializes the obstacle."""
        return {"Use frames": self.use_frames,
                "Delays": self.delays,
                "Explosions": self.explosions.to_dict(orient='index'),
                "Walls": self.walls.to_dict(orient='index'),
                "Teleports": self.teleports.to_dict(orient='index'),
                "Audio": self.audio.to_dict(orient='index')}
                           
    def load(self, data: dict) -> None:
        """Reconstructs the delays and audio from saved data."""
        delays = data["Obstacle"]["Delays"]
        audio = data["Obstacle"]["Audio"]
        
        while len(self.delays) < len(delays):
            self.delays.append(-1)
        for i, delay in enumerate(delays):
            self.delays[i] = delays[i]
            
        self.audio = pd.DataFrame.from_dict(audio,
                                            columns=["Count",
                                                     "Explosion",
                                                     "DC Unit"],
                                            orient='index')