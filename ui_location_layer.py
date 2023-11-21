import os
from PyQt6.QtWidgets import (QWidget,
                             QFrame,
                             QVBoxLayout,
                             QHBoxLayout,
                             QLineEdit,
                             QListWidget,
                             QListWidgetItem,
                             QScrollArea,
                             QAbstractItemView,
                             QDialog,
                             QScrollArea)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import (Qt,
                          QVariant,
                          QEvent,
                          pyqtSignal)
from graphics import Location
from ui_shared import IconButton
import read_write

class LocationListItem(QListWidgetItem):
    """An item representing a location for display in a list."""
    
    def __init__(self, loc: Location):
        super().__init__("{} (Location ID: {})".format(loc.name, loc.ID))
        self.setData(256, QVariant(loc.num))
        self.loc = loc
        
    def update(self) -> None:
        """Updates the item data."""
        self.setData(256, QVariant(self.loc.num))
        self.setText("{} (Location ID: {})".format(self.loc.name, self.loc.ID))
        
class LocationLayer(QListWidget):
    """A list of locations."""
    # Allows for simultaneous manipulation of multiple locations.
    # Using layers, the user can hide select locations or move multiple locations at once.
    update_locs = pyqtSignal()
    visibility = pyqtSignal(bool)
    delete_layer = pyqtSignal(int)
    set_motion = pyqtSignal(bool)
    selected_locs = pyqtSignal(list, int)
    
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        
    def add_loc(self, loc: Location) -> None:
        """Adds the input location to the layer."""
        item = LocationListItem(loc)
        self.update_locs.connect(item.update)
        self.addItem(item)
        self.parent().empty = False
        self.visibility.connect(loc.set_visibility)
        self.set_motion.connect(loc.in_moving_layer_group)
    
    def delete_loc(self, num: int) -> None:
        """Deletes the location of the input number from the layer."""
        for i in range(self.count()):
            item = self.item(i)
            if item.data(256) == num:
                self.takeItem(i)
                break
                
        # If the layer is empty, delete it.
        if self.count() == 0:
            self.delete_layer.emit(self.parent().num)

    def move_locs_from(self, num: int) -> None:
        """Moves locations from this layer to another layer."""
        # If this is the layer to which locations are being moved, do nothing.
        if self.parent().num == num:
            return

        selected_items = self.selectedItems()
        locs = []
        for item in selected_items:
            locs.append(item.loc)
            self.takeItem(self.row(item))

        self.selected_locs.emit(locs, num)
        
        # If the layer is empty, delete it.
        if self.count() == 0:
            self.delete_layer.emit(self.parent().num)
            
    def save(self, layer_data: dict) -> None:
        """Saves the location layer data."""
        for i in range(self.count()):
            layer_data["locs"].append(self.item(i).data(256))
            
    def load(self, num: int, locs: list) -> None:
        """Loads locations onto the layer from saved data."""
        if self.parent().num != num:
            return
        for loc in locs:
            self.add_loc(loc)
    
class LocationLayerFrame(QFrame):
    """Contains a LocationLayer and widgets for interacting with the layer."""
    set_name = pyqtSignal(str)
    update_locs = pyqtSignal()
    add_loc = pyqtSignal(Location)
    delete_loc = pyqtSignal(int)
    delete_layer = pyqtSignal(int)
    move_from = pyqtSignal(int)
    selected_locs = pyqtSignal(list, int)
    movable = pyqtSignal(bool)
    
    save_layer = pyqtSignal(dict)
    load_layer = pyqtSignal(int, list)

    def __init__(self, num: int, name: str):
        super().__init__()
        
        self.num = num
        self.name = name
        self.empty = True
        layer = LocationLayer()
 
        icons_path = read_write.get_path("Icons")
        visibility_icon = QIcon(os.path.join(icons_path, "visible.png"))
        visibility_tooltip = "Toggle the visibility of all locations in this layer."
        visibility_button = IconButton(visibility_icon, 32, 36, visibility_tooltip, True)
        visibility_button.setChecked(True)
        move_icon = QIcon(os.path.join(icons_path, "move.png"))
        move_tooltip = "Move all locations in this layer as a group."
        move_button = IconButton(move_icon, 32, 36, move_tooltip, True)
        move_button.setEnabled(False)
        move_to_layer_icon = QIcon(os.path.join(icons_path, "move_to_layer.png"))
        move_to_layer_tooltip = "Move all selected locations to this layer."
        move_to_layer_button = IconButton(move_to_layer_icon, 32, 36, move_to_layer_tooltip, False)
        select_icon = QIcon(os.path.join(icons_path, "select.png"))
        select_tooltip = "Set this layer to the active layer."
        select_button = IconButton(select_icon, 32, 36, select_tooltip, False)
        label = QLineEdit(name)

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(visibility_button)
        buttons_layout.addWidget(move_button)
        buttons_layout.addWidget(move_to_layer_button)
        buttons_layout.addWidget(select_button)
        buttons_layout.addWidget(label)
        buttons = QFrame()
        buttons.setLayout(buttons_layout)
 
        layout = QVBoxLayout()
        layout.addWidget(buttons)
        layout.addWidget(layer)
        self.setLayout(layout)
        
        self.set_name.connect(label.setText)
        label.textChanged.connect(self.change_name)
        self.update_locs.connect(layer.update_locs)
        self.add_loc.connect(layer.add_loc)
        self.delete_loc.connect(layer.delete_loc)
        self.delete_loc.connect(self.update_locs)
        self.move_from.connect(layer.move_locs_from)
        self.movable.connect(move_button.set_state)
        
        visibility_button.toggled.connect(layer.visibility)
        move_button.toggled.connect(layer.set_motion)
        move_to_layer_button.clicked.connect(self.move_locs_to)
        select_button.clicked.connect(self.activate)

        layer.delete_layer.connect(self.delete_layer)
        layer.selected_locs.connect(self.selected_locs)
        
        self.save_layer.connect(layer.save)
        self.load_layer.connect(layer.load)
        
    def change_name(self, name: str):
        """Changes the name of the layer."""
        self.name = name
        
    def activate(self) -> None:
        """Sets this layer to the active layer."""
        self.parent().active_layer = self.parent().layout().indexOf(self)
        
    def move_locs_to(self) -> None:
        """Sends a signal to move selected locations from other layers to this layer."""
        self.parent().move_locs_to(self.num)
        
    def save(self, data: dict) -> None:
        """Saves location layer data."""
        layer_data = {"num": self.num, "name": self.name, "locs": []}
        index = self.parent().layout().indexOf(self)
        data["Location layers"] = data.get("Location layers", {})
        data["Location layers"][index] = layer_data
        self.save_layer.emit(layer_data)
        
class LocationLayerList(QFrame):
    """An interface for managing location layers."""
    update_locs = pyqtSignal()
    delete_loc = pyqtSignal(int)
    loc_layers_movable = pyqtSignal(bool)
    
    save = pyqtSignal(dict)
    load_layer = pyqtSignal(int, list)
    
    def __init__(self):
        super().__init__()
        self.nums = set()
        
        icons_path = read_write.get_path("Icons")
        add_layer_icon = QIcon(os.path.join(icons_path, "add_layer.png"))
        add_layer_tooltip = "Add a new layer."
        add_layer_button = IconButton(add_layer_icon, 32, 36, add_layer_tooltip, False)

        layout = QVBoxLayout()
        layout.addWidget(add_layer_button)
        self.setLayout(layout)
        
        add_layer_button.clicked.connect(lambda: self.add_layer())
        self.add_layer(1)
        self.active_layer = 0
        
    def find_next_num(self) -> int:
        """Finds the number to assign to the next layer created."""
        num = 1
        while num in self.nums:
            num += 1
        return num
        
    def add_layer(self, num: int=0, name: str="") -> LocationLayer:
        """Adds a new layer with the specified number and name and returns it."""
        # If any layer is empty, a new layer cannot be created
        for i in range(self.layout().count() - 1):
            layer = self.layout().itemAt(i).widget()
            if layer.empty:
                return
            
        num = num if num else self.find_next_num()
        layer_name = name if name else "Layer {}".format(num)
        new_layer = LocationLayerFrame(num, layer_name)
        self.layout().insertWidget(self.layout().count() - 1, new_layer)
        self.nums.add(num)
        self.active_layer = self.layout().count() - 2
        
        self.delete_loc.connect(new_layer.delete_loc)
        self.update_locs.connect(new_layer.update_locs)
        self.loc_layers_movable.connect(new_layer.movable)
        new_layer.delete_layer.connect(self.delete_layer)
        new_layer.selected_locs.connect(self.move_selected_locs)
        self.save.connect(new_layer.save)
        self.load_layer.connect(new_layer.load_layer)
        return new_layer
    
    def delete_layer(self, num: int, delete_first=False) -> None:
        """Deletes the layer of the input number."""
        # Every location must belong to a layer, so there must always be at least one location layer.
        if self.layout().count() == 2 and not delete_first:
            return
            
        self.nums.remove(num)
        for i in range(self.layout().count() - 1):
            layer = self.layout().itemAt(i).widget()
            if layer.num == num:
                self.layout().removeWidget(layer)
                layer.deleteLater()
                break
        
        # If the last layer was deleted, decrement the active layer index.
        if i == self.layout().count() - 1:
            self.active_layer -= 1
            
    def add_loc(self, loc: Location) -> None:
        """Adds the input location to the active layer."""
        self.layout().itemAt(self.active_layer).widget().add_loc.emit(loc)
        
    def set_active_layer(self, num: int) -> None:
        """Sets the active layer to the layer of the input number."""
        self.active_layer = num
        
    def move_locs_to(self, num: int) -> None:
        """Sends a signal to layers to move selected locations."""
        for i in range(self.layout().count() - 1):
            layer = self.layout().itemAt(i).widget()
            if type(layer) is not LocationLayerFrame or layer.num == num:
                continue
            layer.move_from.emit(num)
            
    def move_selected_locs(self, locs: list[Location], num: int) -> None:
        """Moves all input locations to the layer of the input number."""
        for i in range(self.layout().count() - 1):
            layer = self.layout().itemAt(i).widget()
            if layer.num != num:
                continue
            for loc in locs:
                layer.add_loc.emit(loc)
        
    def get_layers(self) -> list[LocationLayer]:
        """Returns a list of all location layers."""
        layers = []
        for layer in self.children():
            if type(layer) is LocationLayer:
                layers.append(layer)
        return layers
        
    def get_moving_layers(self) -> list[list[Location]]:
        """Retruns a list of all location layers which are movable."""
        moving_layers = []
        for layer in self.children():
            if type(layer) is LocationLayer and layer.is_movable():
                for loc in layer.layer:
                    moving_layers.append(loc)
        return moving_layers
        
    def layers_in_motion(self) -> bool:
        """Returns true if at least one layer is movable and false otherwise."""
        for layer in self.children():
            if type(layer) is LocationLayer and layer.is_movable():
                return True
        return False
            
    def set_movable(self, state: bool) -> None:
        """Enables the movability button for the location layers."""
        # We only want to be able to move location layers when the move/resize tool is selected.
        for layer in self.get_layers():
            layer.move_button.setEnabled(state)
            if not state:
                for loc in layer.layer:
                    loc.set_color(Location.interior_color)
                layer.move_button.setEnabled(False)
                layer.move_button.setChecked(False)
                
    def reset(self) -> None:
        """Deletes the last remainig layer and adds a new layer."""
        num = self.nums.pop()
        self.nums.add(num)
        self.delete_layer(num, True)
        self.add_layer(1)
        
    def load(self, data: dict, locations: list[Location]) -> None:
        """Reconstructs the location layers from saved data."""
        serialized_layers = data["Location layers"]
        for index in sorted(serialized_layers):
            layer_data = serialized_layers[index]
            num = layer_data["num"]
            name = layer_data["name"]
            layer_locs = [locations[num - 1] for num in layer_data["locs"]]
            self.add_layer(num, name)
            self.load_layer.emit(num, layer_locs)
        
class LocationLayerDialog(QDialog):
    """A window which shows all location layers."""
    location_layer_dialog = pyqtSignal(str)
    update_locs = pyqtSignal()
    add_loc = pyqtSignal(Location)
    delete_loc = pyqtSignal(int)
    closed = pyqtSignal(bool)
    loc_layers_movable = pyqtSignal(bool)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load_layers = pyqtSignal(dict, list)
    
    def __init__(self, scroll: QScrollArea, locations: list[Location], parent: QWidget):
        super().__init__(parent)

        self.setWindowTitle("Location layers")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.locations = locations
        
        location_layer_list = LocationLayerList()
        scroll.setWidget(location_layer_list)
        
        layout = QHBoxLayout()
        layout.addWidget(scroll)
        self.setLayout(layout)
        
        self.update_locs.connect(location_layer_list.update_locs)
        self.add_loc.connect(location_layer_list.add_loc)
        self.delete_loc.connect(location_layer_list.delete_loc)
        self.loc_layers_movable.connect(location_layer_list.loc_layers_movable)
        
        self.reset.connect(location_layer_list.reset)
        self.save.connect(location_layer_list.save)
        self.load_layers.connect(location_layer_list.load)
        
    def closeEvent(self, event: QEvent) -> None:
        """Sends a signal when the window is closed."""
        self.closed.emit(False)
        event.accept()
        
    def dock(self, state: bool) -> None:
        """Shows the dialog if state is true and hides it otherwise."""
        if state:
            self.show()
        else:
            self.hide()
            
    def load(self, data: dict) -> None:
        """Emits a signal to load location layers from saved data."""
        self.load_layers.emit(data, self.locations)