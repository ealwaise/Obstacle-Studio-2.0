import os
import pandas as pd
from PyQt6.QtWidgets import (QGraphicsView,
                             QGraphicsScene,
                             QGraphicsSceneMouseEvent,
                             QGraphicsRectItem)
from PyQt6.QtGui import (QColor,
                         QCursor,
                         QPixmap)
from PyQt6.QtCore import (Qt,
                          QPointF,
                          pyqtSignal)
from graphics import (Grid,
                      GridSnappingItemGroup,
                      BrushHighlight,
                      TerrainTile,
                      Location,
                      EventImage)
import sc_data
import read_write

class Canvas(QGraphicsScene):
    """A scene on which graphical items such as terrain, locations, explosions, etc. are placed."""
    background_color = QColor(0, 0, 0)
    
    terrain_Z = 1
    grid_Z = 2
    location_Z = 3
    wall_Z = 4
    explosion_teleport_Z = 5
    brush_Z = 6

    add_loc = pyqtSignal(Location)
    delete_loc = pyqtSignal(int)
    max_locs = pyqtSignal()
    
    add_explosion = pyqtSignal(int)
    del_explosion = pyqtSignal(int)
    
    add_tele = pyqtSignal(int, int, str, Location, list)
    delete_tele = pyqtSignal(int, int)

    def __init__(self, x, y, w, z, ob):
        super().__init__(x, y, w, z)

        self.setBackgroundBrush(self.background_color)
        self.width, self.height = int(self.width() / 32), int(self.height() / 32)
        self.mouse_pos = QPointF(-1, -1)
        
        self.edit_mode = "Terrain"
        
        # Create the grid.
        self.grid_size = 32
        self.grid_32 = Grid(32*self.width, 32*self.height, 32)
        self.subgrid = None
        self.addItem(self.grid_32)
        self.grid_32.setZValue(self.grid_Z)
        
        # Create the brushes for each editing mode.
        self.shapes = {"Terrain": [[1]],
                       "Location": [[1]],
                       "Obstacle": [[1]]}
        self.brushes = {"Terrain": BrushHighlight([[1]], 1, 1),
                        "Location": BrushHighlight([[1]], 1, 1),
                        "Obstacle": BrushHighlight([[1]], 1, 1)}
        for mode in self.brushes:
            brush = self.brushes[mode]
            brush.setZValue(self.brush_Z)
            self.addItem(brush)
            brush.setVisible(mode == "Terrain")
        self.current_brush = self.brushes["Terrain"]
        
        # The currently selected terrain tile and a map of currently placed terrain.
        self.tile_num = 0
        self.terrain = [[None]*self.width for i in range(self.height)]
        
        # Cache terrain tile images.
        self.terrain_images = {}
        for tileset_index, tileset_name in enumerate(sc_data.tilesets):
            path = read_write.get_path(tileset_name)
            count = len(os.listdir(path))
            for i in range(count):    
                image = QPixmap(os.path.join(path, "{}.png".format(i)))
                tile_num = (i << 3) + tileset_index
                self.terrain_images[tile_num] = QPixmap(image)

        self.loc_tool = "Place"
        self.locations = []
        self.loc_adjusted = None
        self.moving_layer_group = None
        
        self.event_type = "Explosion"
        self.placement_type = "Fixed"
        self.mobile_location = None
        self.ob = ob
        self.current_count = 1
        self.selected_explosions = []
        
        self.wall_unit = None
        self.wall_removal_type = "Remove Unit"
        self.wall_place_remove = "Place"
        self.explosion_player = 0
        self.wall_player = 0
        
        self.teleport_player = 0
        self.teleport_marker = None
        self.teleport_placement = [-1, -1]
        
        # Cache explosion images.
        explosion_image_path = read_write.get_path("Explosion")
        self.static_explosion_images = {}
        for ID in sc_data.event_data[sc_data.event_data["Explosion Image"].notna()].index:
            explosion_ID = int(sc_data.event_data.loc[ID]["Explosion Image"])
            path = os.path.join(explosion_image_path, str(explosion_ID))
            path = os.path.join(path, "static.png")
            self.static_explosion_images[ID] = QPixmap(path)

        # Cache wall images.
        wall_image_path = read_write.get_path("Wall")
        self.static_wall_images = {}
        for ID in sc_data.event_data[sc_data.event_data["Wall Image"].notna()].index:
            wall_ID = int(sc_data.event_data.loc[ID]["Wall Image"])
            path = os.path.join(wall_image_path, str(wall_ID))
            path = os.path.join(path, "static.png")
            self.static_wall_images[ID] = QPixmap(path)
            
        # Cache teleport images.
        teleport_image_path = read_write.get_path("Teleport")
        self.static_teleport_images = {}
        for ID in sc_data.event_data[sc_data.event_data["Teleport Image"].notna()].index:
            teleport_ID = int(sc_data.event_data.loc[ID]["Teleport Image"])
            path = os.path.join(teleport_image_path, str(teleport_ID))
            path = os.path.join(path, "static.png")
            self.static_teleport_images[ID] = QPixmap(path)
            
    def set_grid_size(self, index: int) -> None:
        """Draws a grid with size x size cells on the scene."""
        size = 32 // 2**index
        if self.subgrid:
            self.removeItem(self.subgrid)
            self.subgrid = None
        if size != 32:
            self.subgrid = Grid(32 * self.width, 32 * self.height, size, True)
            self.addItem(self.subgrid)
        self.grid_size = size
        
    def point_in_bounds(self, p: int, dist: float) -> float:
        """Returns the point closest to p in the range[0, 8192 - dist]."""
        # Used to ensure items are never placed out of bounds.
        return min(8192 - dist, max(0, p))
        
    def snap_to_grid(self, x: int, y: int, grid_size: int, width: float, height: float) -> list[int]:
        """Returns the point pos snapped to a grid of size grid_size.
        
        If pos + 32*size is out of bounds, returns the closest point in bounds."""
        # Used to snap the top-left corner of objects to the grid,
        # so the size parameter is for checking bounds.
        x, y = self.point_in_bounds(x, 32*width), self.point_in_bounds(y, 32*height)
        snapped_point = grid_size * (QPointF(x, y) / grid_size).toPoint()
        return [snapped_point.x(), snapped_point.y()]
        
    def set_current_brush(self, mode: str) -> None:
        """Sets the current brush to the brush corresponding to mode."""
        self.current_brush = self.brushes[mode]
        for other_mode in self.brushes:
            if other_mode != mode:
                self.brushes[other_mode].hide()
                
    def set_brush_visibility(self) -> None:
        """Sets the visibility of the brush depending on the state of the editor."""
        if self.edit_mode == "Terrain":
            self.current_brush.show()
        elif self.edit_mode == "Location":
            self.current_brush.setVisible(self.loc_tool == "Place")
        else:
            self.current_brush.setVisible(self.mobile_location is not None)
        grid_size = 32 if self.edit_mode == "Terrain" else self.grid_size
        self.move_brush(grid_size)
        
    def set_brush_shape(self, shape: list[list[int]]) -> None:
        """Changes the shape of the brush to shape."""
        if self.edit_mode != "Obstacle":
            return
        else:
            width, height = self.current_brush.width, self.current_brush.height
            self.change_brush(self.edit_mode, shape, width, height)
        
    def change_brush(self,
                     mode: str,
                     shape: list[list[int]],
                     width: float,
                     height: float) -> None:
        """Changes the geometry of the brush corresponding to mode and repositions it."""
        brush = self.brushes[mode]
        brush.change_geometry(shape, width, height)
        grid_size = 32 if mode == "Terrain" else self.grid_size
        self.move_brush(grid_size)

    def move_brush(self, grid_size: int) -> None:
        """Moves the current brush based upon the mouse position and grid_size."""
        x, y = self.mouse_pos.x(), self.mouse_pos.y()
        x_place, y_place = self.snap_to_grid(x - 16*self.current_brush.total_width,
                                             y - 16*self.current_brush.total_height,
                                             grid_size,
                                             self.current_brush.total_width,
                                             self.current_brush.total_height)
        self.current_brush.setPos(x_place, y_place)
        
    def set_brush_width(self, width: float, mode: str) -> None:
        """Changes the width of the brush corresponding to mode."""
        width = int(width) if mode == "Terrain" else width
        height = self.brushes[mode].height
        self.change_brush(mode, [[1]], width, height)
            
    def set_brush_height(self, height: float, mode: str) -> None:
        """Changes the height of the brush corresponding to mode."""
        height = int(height) if mode == "Terrain" else height
        width = self.brushes[mode].width
        self.change_brush(mode, [[1]], width, height)
        
    def set_cursor(self) -> None:
        """Sets the cursor according to the state of the editor and the mouse position."""
        if self.edit_mode == "Terrain":
            self.views()[0].set_cursor("pointing")
        elif self.edit_mode == "Location":
            if self.loc_tool == "Place":
                self.views()[0].set_cursor("pointing")
            else:
                pass
            
    def set_mode(self, mode: str) -> None:
        """Sets the editor mode to mode."""
        self.edit_mode = mode
        self.set_current_brush(mode)
        if mode == "Terrain":
            self.set_location_visibility(False)
            self.set_obstacle_visibility(False)
            for loc in self.locations:
                loc.set_color(Location.interior_color)
            self.destroy_moving_layer_group()
            self.mobile_location = None
        elif mode == "Location":
            self.set_location_visibility(True)
            self.set_obstacle_visibility(False)
            self.mobile_location = None
            self.set_loc_tool(self.loc_tool)
        else:
            self.set_location_visibility(True)
            self.set_obstacle_visibility(True)
        self.set_brush_visibility()
        self.set_cursor()

    def set_loc_tool(self, tool: str) -> None:
        """Sets location mode to the input tool."""
        self.loc_tool = tool
        if tool == "Place":
            self.loc_adjusted = None
            self.destroy_moving_layer_group()
        else:
            self.views()[0].set_cursor("open")
        self.set_brush_visibility()
        self.set_cursor()
            
    def set_event_type(self, event_type: str) -> None:
        """Sets the obstacle event type being edited to event_type."""
        self.event_type = event_type
        self.set_brush_visibility()
        self.set_cursor()
        
    def set_placement_type(self, placement_type: str) -> None:
        """Sets the placement type to placement_type."""
        self.placement_type = placement_type
        if self.placement_type == "Fixed":
            self.mobile_location = None
            self.find_location_under_cursor(self.mouse_pos.x(), self.mouse_pos.y())
            self.change_brush("Obstacle", [[1]], 1, 1)
        else:
            pass
        self.set_brush_visibility()
        
    def set_terrain_tile(self, num: int) -> None:
        """Sets the currently selected terrain tile to num."""
        self.tile_num = num
        
    def place_terrain(self, x: int, y: int, width: int, height: int, tile_num: int) -> None:
        """Places a block of terrain tiles.
        
        (x, y) is the top-left coordinate of the block,
        width x height are the dimensions of the block.
        tile_num is the number of the tile to be placed.
        """
        i0, j0 = x // 32, y // 32
        for i in range(width):
            for j in range(height):
                old_tile = self.terrain[i0 + i][j0 + j]
                
                # If a previously placed tile is the same, we ignore it, otherwise we delete it.
                if old_tile and old_tile.num == tile_num:
                    continue
                if old_tile and old_tile.num != tile_num:
                    self.removeItem(old_tile)

                # Places the tile on the canvas and stores it in the terrain map.
                tile = TerrainTile(tile_num, self.terrain_images[tile_num])
                self.terrain[i0 + i][j0 + j] = tile
                self.addItem(tile)
                tile.setPos(x + 32*i, y + 32*j)
                tile.setZValue(self.terrain_Z)

    def remove_terrain(self, x: int, y: int, width: int, height: int) -> None:
        """Removes all terrain in a (width x height)-sized block with top-left corner at (x, y)."""
        i0, j0 = x // 32, y // 32
        for i in range(width):
            for j in range(height):
                item = self.terrain[i0 + i][j0 + j]
                if item:
                    self.removeItem(item)
                    self.terrain[i0 + i][j0 + j] = None
                    
    def remove_all_terrain(self) -> None:
        """Removes all terrain on the scene."""
        for i in range(self.width):
            for j in range(self.height):
                self.remove_terrain(32*i, 32*j, 1, 1)
                
    def set_location_visibility(self, visible: bool) -> None:
        """Sets the visibilty of locations to the input boolean."""
        # We need to show locations when the user switches to Location or Obstacle mode.
        for loc in self.locations:
            loc.setVisible(visible)
    
    def place_location(self, x: int,
                             y: int,
                             width: int,
                             height: int,
                             add_to_layer: bool=True) -> None:
        """Places a location of dimensions width x height and top-left corner at (x, y)."""
        for loc in self.locations:
            loc.set_color(Location.interior_color)
        num = len(self.locations)
        
        # We impose a 255 location limit in accordance with Starcraft behavior.
        if num == 255:
            self.max_locs.emit()
            return

        loc = Location(width, height, num + 1, num + 1)
        self.locations.append(loc)
        self.update_locs()
        self.addItem(loc)
        loc.setPos(x, y)
        loc.setZValue(self.location_Z)
        
        # When loading a save file, it's more convenient to reconstruct the layers separately.
        if add_to_layer:
            self.add_loc.emit(loc)
        
    def delete_location(self, loc: Location) -> None:
        """Deletes the input location."""
        # If loc is null, do nothing.
        if not loc:
            return
            
        num = loc.num
        deleted_loc = self.locations.pop(num - 1)
        
        # Decrement the number of each location placed after the deleted location.
        for i in range(num - 1, len(self.locations)):
            loc = self.locations[i]
            loc.num -= 1
            loc.ID -= 1
        self.update_locs()
        self.removeItem(deleted_loc)
        
        self.ob.delete_location(num)
        self.delete_loc.emit(num)
        
    def delete_all_locations(self) -> None:
        """Deletes all currently placed locations."""
        while self.locations:
            self.delete_location(self.locations[-1])
            
    def update_locs(self) -> None:
        """Updates the location names and IDs."""
        for loc in self.locations:
            loc.update_data(len(self.locations))
            
    def find_location_under_cursor(self, x: int, y: int) -> Location:
        """Highlights and returns the top-most location which contains the point (x, y)."""
        # If a location is currently being adjusted or layers are being moved or a location has
        # been selected to place off-centered events on, do nothing.
        if self.loc_adjusted or self.moving_layer_group or self.mobile_location:
            return
            
        # Find and highlight the location under the cursor.
        loc_under_cursor = None
        for loc in reversed(self.locations):
            if (loc.contains(loc.mapFromScene(QPointF(x, y))) and loc.isVisible()):
                loc.set_color(Location.interior_color_highlight)
                loc_under_cursor = loc
                break
        
        # Locations not under the cursor are set back to the default color.
        for loc in self.locations:
            if loc != loc_under_cursor:
                loc.set_color(Location.interior_color)
        return loc_under_cursor
  
    def loc_adjustment_type(self, x: int, y: int, loc: Location) -> int:
        """Determines the type of adjustment to be made to loc based on the mouse position (x, y)."""
        tolerance = Location.pixel_tolerance
        adjustment_type = 0
        if x - loc.x() <= tolerance:
            adjustment_type |= 1
        if loc.x() + 32*loc.width - x <= tolerance:
            adjustment_type |= 2
        if y - loc.y() <= tolerance:
            adjustment_type |= 4
        if loc.y() + 32*loc.height - y <= tolerance:
            adjustment_type |= 8
        return adjustment_type
        
    def location_adjusment_cursor(self, adjustment_type: int) -> None:
        """Determines the cursor shape depending on adjustment_type.
        The value of adjustment_type corresponds to the position of the mouse.
        """
        # We use different cursor shapes to indicate whether or not we are moving or resizing a
        # location and the direction of resizing.
        if adjustment_type in [1, 2]:
            self.views()[0].set_cursor("hor")
        elif adjustment_type in [4, 8]:
            self.views()[0].set_cursor("vert")
        elif adjustment_type in [6, 9]:
            self.views()[0].set_cursor("pos_diag")
        elif adjustment_type in [5, 10]:
            self.views()[0].set_cursor("neg_diag")
        else:
            self.views()[0].set_cursor("open")

    def resize_loc(self,
                   x: int,
                   y: int,
                   original_data: [Location, int, int, int, int, int],
                   grid_size: int) -> None:
        """Resizes a location, snapping to a grid_size x grid_size grid.
        
        (x, y) is the mouse position.
        original_data contains the location to resize and its original dimensions.
        """
        loc = original_data[0]
        adjustment_type = original_data[1]
        corner_x, corner_y = original_data[2], original_data[3]
        width, height = original_data[4], original_data[5]
        new_x, new_y = loc.x(), loc.y()
        new_width, new_height = loc.width, loc.height
        if adjustment_type & 1: 
            new_x = x if x <= corner_x + 32*width else corner_x + 32*width
            new_width = max(grid_size / 32, abs(x - corner_x - 32*width) / 32)
        if adjustment_type & 2:
            new_x = x if x < corner_x else corner_x
            new_width = max(grid_size / 32, abs(x - corner_x) / 32)
        if adjustment_type & 4:
            new_y = y if y <= corner_y + 32*height else corner_y + 32*height
            new_height = max(grid_size / 32, abs(y - corner_y - 32*height) / 32)
        if adjustment_type & 8:
            new_y = y if y < corner_y else corner_y
            new_height = max(grid_size / 32, abs(y - corner_y) / 32)
        loc.setPos(new_x, new_y)
        self.ob.shift_events(loc.num,
                             loc.resize(loc.center(), new_x, new_y, new_width, new_height))
        
    def adjust_moving_layer_group(self, loc: Location, motion: bool):
        """If motion is true, adds the location of the input number to the moving layer group.
        If motion is false, removes the location of the input number from the moving layer group.
        """
        x = loc.x() if motion else self.width
        y = loc.y() if motion else self.height

        # Computes the correct position for the moving layer group.
        if self.moving_layer_group:
            for other_loc in self.moving_layer_group.childItems():
                if other_loc == loc:
                    continue
                pos = other_loc.mapToScene(other_loc.pos())
                x, y = min(x, pos.x()), min(y, pos.y())

        # Creates a new group.
        locs = self.moving_layer_group.childItems() if self.moving_layer_group else []
        self.destroy_moving_layer_group()
        group = GridSnappingItemGroup()
        self.addItem(group)
        group.setPos(x, y)
        for other_loc in locs:
            if other_loc == loc:
                continue
            group.addToGroup(other_loc)
        if motion:
            group.addToGroup(loc)
        if len(group.childItems()):
            self.moving_layer_group = group
            
    def destroy_moving_layer_group(self):
        """Destroys the moving layer group."""
        if self.moving_layer_group:
            self.destroyItemGroup(self.moving_layer_group)
            self.moving_layer_group = None
            
    def set_obstacle_visibility(self, visible: bool) -> None:
        """Sets the visibility of obstacle events to the input boolean."""
        for loc in self.locations:
            for child in loc.childItems():
                child.setVisible(visible and child.count == self.current_count)

    def show_count(self, count: int) -> None:
        """Shows all obstacle events occuring on the input count."""
        # Show explosions and teleports.
        for loc in self.locations:
            for child in loc.childItems():
                if child.event_type == "Wall":
                    continue
                child.setVisible(child.count == count)
                
        # Show walls.
        num_counts = len(self.ob.delays)
        positions = set()
        for i in range(num_counts):
            prev_count = (count - i - 1) % num_counts + 1
            walls = self.ob.walls[self.ob.walls["Count"] == prev_count]
            for index, event in walls.iterrows():
                loc = self.locations[int(event.loc["Location"]) - 1]
                pos = QPointF(event.loc["x"], event.loc["y"])
                place_count = self.ob.find_wall(prev_count, loc.num, pos)
                scene_pos = loc.mapToScene(pos)
                x, y = scene_pos.x(), scene_pos.y()
                if (x, y) in positions:
                    continue
                for child in loc.childItems():
                    if (child.count != place_count
                        or child.event_type != "Wall"
                        or child.pos() != pos):
                        continue
                    positions.add((x, y))
                    child.setVisible(bool(event.loc["Add/Remove"] == 2))    

    def set_count(self, count: int) -> None:
        """Sets the current count to count."""
        self.current_count = count
        self.show_count(count)
        
    def delete_count(self, count: int) -> None:
        """Deletes the input count."""
        # Delete and shift the counts of images.
        for loc in self.locations:
            for child in loc.childItems():
                if child.count > count:
                    child.count = child.count - 1
                    continue
                if child.count != count:
                    continue
                child.setParentItem(None)
                self.removeItem(child)
                
        new_count = count if count < len(self.ob.delays) else max(1, count - 1)
        self.ob.delete_count(count)
        self.set_count(new_count)
        
    def insert_count(self, count: int) -> None:
        """Inserts a new count at the input position."""
        # Shift the counts of items.
        for loc in self.locations:
            for child in loc.childItems():
                if child.count >= count:
                    child.count = child.count + 1
                    continue
                    
        self.ob.insert_count(count)
        self.show_count(count)
        
    def set_explosion_player(self, player: int) -> None:
        """Sets the player owning the placed explosions to index."""
        self.explosion_player = player
        
    def set_explosion_selection(self, explosions: list[str]) -> None:
        """Sets the currently selected list of explosions to explosions."""
        self.selected_explosions.clear()
        for explosion in explosions:
            self.selected_explosions.append(explosion)

    def place_explosions(self,
                         count: int,
                         player: int,
                         explosions: list[str],
                         loc: Location,
                         pos: QPointF) -> None:
        """Places explosions on the scene and adds them to the obstacle."""
        # Iterate through explosions. The explosions argument is a list so that multi-explosions
        # can be placed in a single click.
        for explosion in explosions:
            ID = int(sc_data.name_to_ID[explosion])
            pixmap = self.static_explosion_images[ID]
            
            # If an identical explosion exists on the current count, we don't place a new one.
            flag = False
            for other_loc in self.locations:
                rel_pos = other_loc.mapFromScene(loc.mapToScene(pos))
                if self.ob.find_explosion_at(count, ID, other_loc.num, rel_pos):
                    flag = True
                    break
            if flag:
                continue

            # Add the image and explosion event.
            explosion_image = EventImage("Explosion", count, ID, pixmap)
            explosion_image.setParentItem(loc)
            explosion_image.setPos(pos)
            explosion_image.setZValue(self.explosion_teleport_Z)
            # If the explosion type did not previously exist the ob, send a signal to add the
            # explosion to the audio mapping.
            if not self.ob.find_explosion(ID):
                self.add_explosion.emit(ID)
            self.ob.add_explosion(count, player, ID, loc.num, pos.x(), pos.y())

    def delete_explosions(self, count: int, loc: Location, pos: QPointF) -> bool:
        """Deletes explosions on loc at pos on count and returns a boolean representing whether or
        not any explosions to delete were found.
        """
        flag = False
        # Iterate through obstacle events at the location.
        for child in loc.childItems():
            if child.count != count or child.pos() != pos or child.event_type != "Explosion":
                continue
            flag = True
            ID = child.ID
            self.ob.delete_explosion(count, ID, loc.num, pos.x(), pos.y())
            child.setParentItem(None)
            self.removeItem(child)
            # If the explosion type no longer exists in the ob, send a signal to remove the
            # explosion from the audio mapping.
            if not self.ob.find_explosion(ID):
                self.del_explosion.emit(ID)
        return flag
            
    def set_wall_player(self, player: int) -> None:
        """Sets the player owning the placed walls to player."""
        self.wall_player = player
        
    def set_wall_unit(self, wall_unit: str) -> None:
        """Sets the selected wall unit to wall_unit."""
        self.wall_unit = wall_unit
        
    def set_wall_option(self, option: str) -> None:
        """Depending on the value of option, sets either whether walls are being placed or removed,
        or whether walls are removed by Kill Unit or Remove Unit."""
        if option in ["Place", "Remove"]:
            self.wall_place_remove = option
        else:
            self.wall_removal_type = option
            
    def place_wall(self, count: int, player: int, wall: str, loc: Location, pos: QPointF) -> None:
        """Places a wall addition event and adds it to the obstacle."""
        # If no valid wall unit has been selected, do nothing.
        if ((wall not in sc_data.name_to_ID)
            or (sc_data.name_to_ID[wall] not in self.static_wall_images)):
            return

        # If a wall was previously added at this position, we do not place an overlapping one.
        for other_loc in self.locations:
            rel_pos = other_loc.mapFromScene(loc.mapToScene(pos))
            if self.ob.search_wall(count, other_loc.num, rel_pos)[0] == 2:
                return

        # Place wall image.
        ID = sc_data.name_to_ID[wall]
        pixmap = self.static_wall_images[ID]
        wall_image = EventImage("Wall", count, ID, pixmap)
        wall_image.setParentItem(loc)
        wall_image.setPos(pos)
        wall_image.setZValue(self.wall_Z)
        self.ob.place_wall(count, player, ID, loc.num, pos.x(), pos.y())
            
    def remove_wall(self, count: int, removal_type: str, loc: Location, pos: QPointF) -> None:
        """Places a wall removal event and adds it to the obstacle."""
        # If no previously placed wall exists, we do not add a wall removal event.
        prev_wall_event, prev_count = self.ob.search_wall(count, loc.num, pos)
        if prev_wall_event != 2:
            return
        
        # Find previously placed wall and add a wall removal event.
        for child in loc.childItems():
            if child.count != prev_count or child.pos() != pos or child.event_type != "Wall":
                continue
            ID = child.ID
            add_remove = 0 if removal_type == "Remove Unit" else 1
            self.ob.remove_wall(count, ID, add_remove, loc.num, pos.x(), pos.y())
            return
            
    def delete_wall(self, count: int, loc: Location, pos: QPointF) -> bool:
        """Attempts to delete a wall. Returns true if a wall is deleted and false if no wall to
        delte is found.
        """
        prev_wall_event, prev_count = self.ob.search_wall(count, loc.num, pos)
        # If no wall was previously placed, do nothing.
        if prev_wall_event != 2:
            return False

        # Find and delete the wall placement (and possibly removal) events and the image.
        for child in loc.childItems():
            if child.count != prev_count or child.pos() != pos or child.event_type != "Wall":
                continue
            child.setParentItem(None)
            self.removeItem(child)
            self.ob.delete_wall(prev_count, loc.num, pos.x(), pos.y())
            return True
        return False
            
    def set_teleport_marker(self, marker: str) -> None:
        """Sets the selected teleport marker to marker."""
        self.teleport_marker = marker
        
    def set_teleport_player(self, player: int) -> None:
        """Sets the player owning the teleport marker to player."""
        self.teleport_player = player
        
    def set_teleport_placement(self, row: int, col: int) -> None:
        """Sets a cell in the teleport table to place a teleport."""
        self.teleport_placement = [row, col]
        
    def place_teleport(self,
                       count: int,
                       player: int,
                       marker: str,
                       loc: Location,
                       cell: list[int],
                       add_to_table=True) -> None:
        """Places a teleport."""
        # If no valid marker is selected, do nothing.
        if ((marker not in sc_data.name_to_ID)
            or (sc_data.name_to_ID[marker] not in self.static_teleport_images)):
            return
            
        # If an invalid cell is selected, do nothing.
        if cell[0] < 1 and add_to_table:
            return

        # If a teleport has already been placed on this count at this location, do nothing.
        for child in loc.childItems():
            if child.event_type == "Teleport" and child.count == count:
                return
                
        # If the cell is occupied, do nothing.
        for other_loc in self.locations:
            for child in other_loc.childItems():
                if add_to_table and child.teleport_cell == cell and child.count == count:
                    return

        # Place teleport image.
        ID = sc_data.name_to_ID[marker]
        pixmap = self.static_teleport_images[ID]
        teleport_image = EventImage("Teleport", count, ID, pixmap, cell, player)
        teleport_image.setParentItem(loc)
        teleport_image.setPos(loc.center())
        teleport_image.setZValue(self.explosion_teleport_Z)
        
        # It is more convenient to reconstruct the teleport tables independently when loading a
        # save file.
        if add_to_table:
            self.add_tele.emit(count, player, marker, loc, cell)
        
        # If a start and end teleport are now connected, add a teleport event.
        for loc_end in self.locations:
            if loc_end == loc:
                continue
            for child in loc_end.childItems():
                if child.count != count or child.teleport_cell[0] != cell[0]:
                    continue
                if cell[0] == 0:
                    self.ob.add_teleport(count,
                                         player,
                                         child.teleport_player,
                                         ID,
                                         child.ID,
                                         loc.num,
                                         loc_end.num)
                else:
                    self.ob.add_teleport(count,
                                         child.teleport_player,
                                         player,
                                         child.ID,
                                         ID,
                                         loc_end.num,
                                         loc.num)
                return
                
    def delete_teleport(self, count: int, loc: Location) -> None:
        """Deletes a teleport."""
        for child in loc.childItems():
            if child.count == count and child.event_type == "Teleport":
                child.setParentItem(None)
                self.removeItem(child)
                self.ob.delete_teleport(count, loc.num)
                self.delete_tele.emit(count, loc.num)
                return
        
    def mouseMoveEvent(self, event) -> None:
        """Executes functions when the mouse is moved within the scene."""
        x, y = event.scenePos().x(), event.scenePos().y()
        self.mouse_pos.setX(x)
        self.mouse_pos.setY(y)
        width_terrain = self.brushes["Terrain"].width
        height_terrain = self.brushes["Terrain"].height
        x_place_32, y_place_32 = self.snap_to_grid(x - 16*width_terrain,
                                                   y - 16*height_terrain,
                                                   32,
                                                   width_terrain,
                                                   height_terrain)
        width_loc = self.brushes["Location"].width
        height_loc = self.brushes["Location"].height
        x_place, y_place = self.snap_to_grid(x - 16*width_loc,
                                             y - 16*height_loc,
                                             self.grid_size,
                                             width_loc,
                                             height_loc)
        
        if self.edit_mode == "Terrain":
            self.move_brush(32)
        
        if self.edit_mode == "Location":
            loc = self.find_location_under_cursor(x, y)
            # When using the location placement tool, move the brush.
            if self.loc_tool == "Place":
                self.move_brush(self.grid_size)
                
            # When using the location adjust tool, modify the cursor if no location or layer group
            # is being adjusted.
            if self.loc_tool == "Adjust":
                if not self.loc_adjusted and not self.moving_layer_group:
                    if loc:
                        self.location_adjusment_cursor(self.loc_adjustment_type(x, y, loc))
                    else:
                        self.views()[0].set_cursor("open")
                        
        if self.edit_mode == "Obstacle":
            if self.placement_type == "Fixed" or not self.mobile_location:
                self.find_location_under_cursor(x, y)
            else:
                self.move_brush(self.grid_size)
        
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Place terrain
            if self.edit_mode == "Terrain":
                self.place_terrain(x_place_32,
                                   y_place_32,
                                   width_terrain,
                                   height_terrain,
                                   self.tile_num)
            
            # Resize a location if applicable.
            if self.edit_mode == "Location":
                if self.loc_tool == "Adjust":
                    if not self.moving_layer_group and self.loc_adjusted and self.loc_adjusted[1]:
                        new_x, new_y = self.snap_to_grid(x, y, self.grid_size, 0, 0)
                        self.resize_loc(new_x, new_y, list(self.loc_adjusted), self.grid_size)
                        
        elif event.buttons() == Qt.MouseButton.RightButton:
            # Remove terrain.
            if self.edit_mode == "Terrain":
                self.remove_terrain(x_place_32, y_place_32, width_terrain, height_terrain)
                
        QGraphicsScene.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        """Executes functions when a mouse button is pressed within the scene."""
        x, y = event.scenePos().x(), event.scenePos().y()
        width_terrain = self.brushes["Terrain"].width
        height_terrain = self.brushes["Terrain"].height
        x_place_32, y_place_32 = self.snap_to_grid(x - 16*width_terrain,
                                                   y - 16*height_terrain,
                                                   32,
                                                   width_terrain,
                                                   height_terrain)
        width_loc = self.brushes["Location"].width
        height_loc = self.brushes["Location"].height
        x_place, y_place = self.snap_to_grid(x - 16*width_loc,
                                             y - 16*height_loc,
                                             self.grid_size,
                                             width_loc,
                                             height_loc)
        
        if event.buttons() == Qt.MouseButton.LeftButton:
            # Place terrain.
            if self.edit_mode == "Terrain":
                self.place_terrain(x_place_32,
                                   y_place_32,
                                   width_terrain,
                                   height_terrain,
                                   self.tile_num)
                
            elif self.edit_mode == "Location":
                loc = self.find_location_under_cursor(x, y)
                # Place a location.
                if self.loc_tool == "Place":
                    self.place_location(x_place, y_place, width_loc, height_loc)
                    
                else:
                    # Change the cursor when starting to move location layers.
                    if self.moving_layer_group:
                        point = self.moving_layer_group.mapFromScene(QPointF(x, y))
                        if self.moving_layer_group.contains(point):
                            self.views()[0].set_cursor("closed")
                            
                    # Begin to adjust a single location.
                    elif loc and not self.loc_adjusted:
                        self.loc_adjusted = [loc,
                                             self.loc_adjustment_type(x, y, loc),
                                             loc.x(),
                                             loc.y(),
                                             loc.width,
                                             loc.height]
                        if self.loc_adjusted and self.loc_adjusted[1] == 0:
                            self.loc_adjusted[0].set_movable(True)
                            self.views()[0].set_cursor("closed")

            else:
                if self.placement_type == "Fixed":
                    loc = self.find_location_under_cursor(x, y)
                    
                    # Place explosions at loc.
                    if self.event_type == "Explosion":
                        if loc:
                            self.place_explosions(self.current_count,
                                                  self.explosion_player,
                                                  self.selected_explosions,
                                                  loc,
                                                  loc.center())

                    elif self.event_type == "Wall":
                        if loc:
                            # Place a wall at loc.
                            if self.wall_place_remove == "Place":
                                self.place_wall(self.current_count,
                                                self.wall_player,
                                                self.wall_unit,
                                                loc,
                                                loc.center())
                                
                            # Remove a wall at loc.
                            else:
                                self.remove_wall(self.current_count,
                                                 self.wall_removal_type,
                                                 loc,
                                                 loc.center())
                                self.show_count(self.current_count)
                                
                    else:
                        if loc:
                            # Place a teleport at loc
                            self.place_teleport(self.current_count,
                                                self.teleport_player,
                                                self.teleport_marker,
                                                loc,
                                                self.teleport_placement)
                else:
                    if not self.mobile_location:
                        loc = self.find_location_under_cursor(x, y)
                        if loc:
                            self.mobile_location = loc
                            self.change_brush("Obstacle",
                                              self.brushes["Obstacle"].shape,
                                              loc.width,
                                              loc.height)
                            self.set_brush_visibility()
                    else:
                        # Place explosions on loc at all positions in the brush.
                        if self.event_type == "Explosion":
                            for rect in self.current_brush.childItems():
                                scene_pos = rect.mapToScene(rect.boundingRect().center())
                                rel_pos = self.mobile_location.mapFromScene(scene_pos)
                                self.place_explosions(self.current_count,
                                                      self.explosion_player,
                                                      self.selected_explosions,
                                                      self.mobile_location,
                                                      rel_pos)
                        elif self.event_type == "Wall":
                            # Place walls at all positions in the brush.
                            if self.wall_place_remove == "Place":
                                for rect in self.current_brush.childItems():
                                    scene_pos = rect.mapToScene(rect.boundingRect().center())
                                    rel_pos = self.mobile_location.mapFromScene(scene_pos)
                                    self.place_wall(self.current_count,
                                                    self.wall_player,
                                                    self.wall_unit,
                                                    self.mobile_location,
                                                    rel_pos)
                                
                            # Remove walls at all positions in the brush.
                            else:
                                for rect in self.current_brush.childItems():
                                    scene_pos = rect.mapToScene(rect.boundingRect().center())
                                    rel_pos = self.mobile_location.mapFromScene(scene_pos)
                                    self.remove_wall(self.current_count,
                                                     self.wall_removal_type,
                                                     self.mobile_location,
                                                     rel_pos)
                                    self.show_count(self.current_count)

        elif event.buttons() == Qt.MouseButton.RightButton:
            # Remove terrain.
            if self.edit_mode == "Terrain":
                self.remove_terrain(x_place_32, y_place_32, width_terrain, height_terrain)
            
            # Delete a location.
            elif self.edit_mode == "Location":
                loc = self.find_location_under_cursor(x, y)
                self.delete_location(loc)

            else:
                if self.placement_type == "Fixed":
                    loc = self.find_location_under_cursor(x, y)
                    if loc:
                        # Delete explosions at loc.
                        if self.event_type == "Explosion":
                            self.delete_explosions(self.current_count, loc, loc.center())
                            
                        # Delete a wall at loc
                        elif self.event_type == "Wall":
                            self.delete_wall(self.current_count, loc, loc.center())
                        
                        # Delete a teleport at loc.
                        else:
                            self.delete_teleport(self.current_count, loc)
                elif self.mobile_location:
                    flag = False
                    # Delete explosions on loc at all positions in the brush.
                    if self.event_type == "Explosion":
                        for rect in self.current_brush.childItems():
                            scene_pos = rect.mapToScene(rect.boundingRect().center())
                            rel_pos = self.mobile_location.mapFromScene(scene_pos)
                            flag |= self.delete_explosions(self.current_count,
                                                           self.mobile_location,
                                                           rel_pos)
                    elif self.event_type == "Wall":
                        for rect in self.current_brush.childItems():
                            scene_pos = rect.mapToScene(rect.boundingRect().center())
                            rel_pos = self.mobile_location.mapFromScene(scene_pos)
                            flag |= self.delete_wall(self.current_count,
                                                     self.mobile_location,
                                                     rel_pos)
                    # If nothing to delete was found, unselects the mobile location.
                    if not flag:
                        self.mobile_location.set_color(Location.interior_color)
                        self.mobile_location = None
                        self.set_brush_visibility()
                
        QGraphicsScene.mousePressEvent(self, event)
                
    def mouseReleaseEvent(self, event):
        """Handles all functions that should execute when a mouse button is released within the
        scene.
        """
        x, y = event.scenePos().x(), event.scenePos().y()
        
        if self.edit_mode == "Location":
            if self.loc_tool == "Adjust":
                # Change the cursor when a moving layer group is released.
                if self.moving_layer_group:
                    self.views()[0].set_cursor("open")

                # Change the cursor when no moving layer group exists.
                else:
                    if self.loc_adjusted:
                        self.loc_adjusted[0].set_movable(False)
                    self.loc_adjusted = None
                    loc = self.find_location_under_cursor(x, y)
                    if loc:
                        self.location_adjusment_cursor(self.loc_adjustment_type(x, y, loc))
                    else:
                        self.views()[0].set_cursor("open")
                
        QGraphicsScene.mouseReleaseEvent(self, event)
        
    def reset(self) -> None:
        """Erases all canvas data."""
        self.remove_all_terrain()
        self.delete_all_locations()
        self.current_count = 1
        
        # Reset the edit mode for appearance purposes.
        self.mobile_location = None
        self.set_mode(self.edit_mode)
        
    def save(self, data: dict) -> None:
        """Serializes obstacle data."""
        
        # Serializes the array representing the terrain.
        terrain = {}
        for i in range(self.width):
            for j in range(self.height):
                if self.terrain[i][j] is None:
                    continue
                terrain[i] = terrain.get(i, {})
                terrain[i][j] = self.terrain[i][j].num
        data["Terrain"] = terrain
        
        # Serializes the list of locations.
        locations = []
        for loc in self.locations:
            locations.append({"x": loc.pos().x(),
                        "y": loc.pos().y(),
                        "width": loc.width,
                        "height": loc.height})
        data["Locations"] = locations
        
    def load(self, data: dict) -> None:
        """Reconstructs a serialized obstacle."""
        # Reconstruct the terrain.
        terrain = data["Terrain"]

        for i in terrain:
            for j in terrain[i]:
                x, y = 32*int(i), 32*int(j)
                self.place_terrain(x, y, 1, 1, terrain[i][j])

        # Reconstruct the locations.
        locations = data["Locations"]
        for loc_data in locations:
            x, y = loc_data["x"], loc_data["y"]
            width, height = loc_data["width"], loc_data["height"]
            self.place_location(x, y, width, height, False)
        
        # Reconstruct the obstacle.
        obstacle = data["Obstacle"]
        explosions = pd.DataFrame.from_dict(obstacle["Explosions"],
                                            columns=["Count",
                                                     "Player",
                                                     "Explosion",
                                                     "Location",
                                                     "x",
                                                     "y"],
                                            orient='index')
        walls = pd.DataFrame.from_dict(obstacle["Walls"], 
                                       columns=["Count",
                                                "Player",
                                                "Unit",
                                                "Add/Remove",
                                                "Location",
                                                "x",
                                                "y"],
                                       orient='index')

        for i, event in explosions.iterrows():
            count = event.loc["Count"]
            player = event.loc["Player"]
            explosion = [sc_data.event_data.loc[event.loc["Explosion"]]["Name"]]
            loc = self.locations[int(event.loc["Location"]) - 1]
            pos = QPointF(event.loc["x"], event.loc["y"])
            self.place_explosions(count, player, explosion, loc, pos)
        for i, event in walls.iterrows():
            count = event.loc["Count"]
            player = event.loc["Player"]
            unit_name = sc_data.event_data.loc[event.loc["Unit"]]["Name"]
            add_remove = event.loc["Add/Remove"]
            loc = self.locations[int(event.loc["Location"]) - 1]
            pos = QPointF(event.loc["x"], event.loc["y"])
            if add_remove == 2:
                self.place_wall(count, player, unit_name, loc, pos)
            else:
                kill_remove = "Kill Unit" if add_remove else "Remove Unit"
                self.remove_wall(count, kill_remove, loc, pos)
        for count in data["Teleport tables"]:
            table_data = data["Teleport tables"][count]
            for i, row in enumerate(table_data):
                if row[0]:
                    player_from = row[0]["player"]
                    marker_from = sc_data.event_data.loc[row[0]["img"]]["Name"]
                    loc_from = self.locations[row[0]["loc"] - 1]
                    self.place_teleport(int(count) + 1,
                                        player_from,
                                        marker_from,
                                        loc_from,
                                        [i + 1, 0],
                                        False)
                if row[1]:
                    player_to = row[1]["player"]
                    marker_to = sc_data.event_data.loc[row[1]["img"]]["Name"]
                    loc_to = self.locations[row[1]["loc"] - 1]
                    self.place_teleport(int(count) + 1,
                                        player_to,
                                        marker_to,
                                        loc_to,
                                        [i + 1, 1],
                                        False)

        # Reset the edit mode for appearance purposes.
        self.mobile_location = None
        self.show_count(1)
        self.set_mode(self.edit_mode)

class Display(QGraphicsView):
    """A display which allows the user to view the scene."""

    def __init__(self, scene):
        super().__init__(scene)

        self.setMouseTracking(True)
        self.pointing_hand_cursor = QCursor(Qt.CursorShape.PointingHandCursor)
        self.closed_hand_cursor = QCursor(Qt.CursorShape.ClosedHandCursor)
        self.open_hand_cursor = QCursor(Qt.CursorShape.OpenHandCursor)
        self.horizontal_cursor = QCursor(Qt.CursorShape.SizeHorCursor)
        self.vertical_cursor = QCursor(Qt.CursorShape.SizeVerCursor)
        self.positive_diag_cursor = QCursor(Qt.CursorShape.SizeBDiagCursor)
        self.negative_diag_cursor = QCursor(Qt.CursorShape.SizeFDiagCursor)
        self.setCursor(self.pointing_hand_cursor)
        
    def set_cursor(self, cursor: str) -> None:
        """Sets the cursor to a cursor corresponding to the input string."""
        if cursor == "pointing":
            self.setCursor(self.pointing_hand_cursor)
        elif cursor == "closed":
            self.setCursor(self.closed_hand_cursor)
        elif cursor == "open":
            self.setCursor(self.open_hand_cursor)
        elif cursor == "hor":
            self.setCursor(self.horizontal_cursor)
        elif cursor == "vert":
            self.setCursor(self.vertical_cursor)
        elif cursor == "pos_diag":
            self.setCursor(self.positive_diag_cursor)
        else:
            self.setCursor(self.negative_diag_cursor)