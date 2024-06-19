import os
from PyQt6.QtWidgets import (QFrame,
                             QLabel,
                             QHBoxLayout,
                             QGridLayout,
                             QStackedWidget,
                             QTableWidget,
                             QTableWidgetItem)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal
from .graphics import Location
from .ui_shared import PlayerMenu, EventMenu, IconButton
from src import sc_data
from src import read_write

class TeleportMenuFrame(QFrame):
    """Contains an organized collection of wall menus."""
    data = sc_data.event_data[sc_data.event_data["Teleport Image"].notna()]
    
    teleport_marker = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        layout = QGridLayout()
        
        # We organize the list of teleport sprite options into various lists sorted by
        # the type of wall unit, whether or not the unit is creatable with triggers, etc.
        # This is mostly to keep the menu size manageable.
        units = self.data[self.data["Type"] == "Unit"]
        sprites = self.data[self.data["Type"] == "Sprite"]
        image_path = read_write.get_path("Teleport")
        layout.addWidget(QLabel("Markers:"), 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        row = 1
        
        if not sprites.empty:
            layout.addWidget(QLabel("Sprites: "), row, 0)
            for subtype in sorted(sprites["Subtype"].unique()):
                data_fixed_subtype = sprites[sprites["Subtype"] == subtype].sort_values("Name")
                items = data_fixed_subtype["Name"].tolist()
                teleport_IDs = data_fixed_subtype["Teleport Image"].tolist()
                # Create the teleport icons.
                icons = []
                for teleport_ID in teleport_IDs:
                    path = os.path.join(image_path, str(int(teleport_ID)))
                    path = os.path.join(path, "static.png")
                    icon = QIcon(path)
                    icons.append(icon)
                    
                menu = EventMenu(icons, items, 275)
                menu.textActivated.connect(self.set_selection)
                layout.addWidget(QLabel("{}:".format(subtype)), row, 1)
                layout.addWidget(menu, row + 1, 1)
                row += 1
                
        if not units.empty:
            layout.addWidget(QLabel("Hallucinations: "), row + 1, 0)
            data = units.sort_values("Name")
            items = data["Name"].tolist()
            teleport_IDs = data["Teleport Image"].tolist()
            # Create the teleport icons.
            icons = []
            for teleport_ID in teleport_IDs:
                path = os.path.join(image_path, str(int(teleport_ID)))
                path = os.path.join(path, "static.png")
                icon = QIcon(path)
                icons.append(icon)
                
            menu = EventMenu(icons, items, 275)
            menu.textActivated.connect(self.set_selection)
            layout.addWidget(menu, row + 1, 1)
                
        self.setLayout(layout)
    
    def set_selection(self, marker: str) -> None:
        """Sets the teleport marker to the selected option and clears the other menus."""
        for widget in self.children():
            if type(widget) is EventMenu and widget.currentText() != marker:
                widget.setCurrentIndex(-1)
        self.teleport_marker.emit(marker)
        
class TeleportTableItem(QTableWidgetItem):
    """An item representing a teleport for display in a table."""
    
    def __init__(self, player: int, ID: int, icon: QIcon, loc: Location):
        super().__init__(icon, loc.name)
        self.player = player
        self.ID = ID
        self.loc = loc
        
    def update(self) -> None:
        """Updates the item data."""
        self.setText(self.loc.name)
        
class TeleportTable(QTableWidget):
    """A table displaying teleports placed on a given count."""
    teleport_cell = pyqtSignal(int, int)
    update_locs = pyqtSignal()
    
    def __init__(self, locations: list[Location]):
        super().__init__()
        
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setVisible(False)
        self.setRowCount(2)
        self.setColumnCount(2)
        self.setItem(0, 0, QTableWidgetItem("Start"))
        self.setItem(0, 1, QTableWidgetItem("End"))
        self.locations = locations
        
        # Cache teleport icons
        teleport_image_path = read_write.get_path("Teleport")
        teleport_IDs = sc_data.event_data[
            sc_data.event_data["Teleport Image"].notna()
        ]["Teleport Image"].tolist()
        self.teleport_icons = {}
        for teleport_ID in teleport_IDs:
            path = os.path.join(teleport_image_path, str(int(teleport_ID)))
            path = os.path.join(path, "static.png")
            self.teleport_icons[teleport_ID] = QIcon(path)
        
        self.cellClicked.connect(self.teleport_cell)
        
    def add_teleport(self, player: int, marker: str, loc: Location, cell: list[int]) -> None:
        """Adds a teleport to the table in the input cell."""
        ID = sc_data.name_to_ID[marker]
        teleport_ID = sc_data.event_data.loc[ID]["Teleport Image"]
        icon = self.teleport_icons[teleport_ID]
        item = TeleportTableItem(player, ID, icon, loc)
        self.setItem(cell[0], cell[1], item)
        self.update_locs.connect(item.update)
        
    def delete_teleport(self, loc: int) -> None:
        """Deletes teleports occuring at the input location from the table."""
        for i in range(1, self.rowCount()):
            for j in range(2):
                item = self.item(i, j)
                if item and item.loc.num == loc:
                    self.takeItem(i, j)
                    
    def reset(self) -> None:
        """Resets the table."""
        i = self.rowCount() - 1
        while i > 0:
            self.removeRow(i)
            i -= 1
            
    def save(self, index: int, data: dict) -> None:
        """Saves the table data."""
        for i in range(1, self.rowCount()):
            row = [0, 0]
            for j in range(2):
                item = self.item(i, j)
                if not item:
                    continue
                row[j] = {"player": item.player, "img": item.ID, "loc": item.loc.num}
            data.append(row)
            
    def load(self, table_data: dict) -> None:
        """Recreates the table from saved data."""
        for i in range(len(table_data)):
            self.insertRow(self.rowCount())
            for j in range(2):
                if table_data[i][j] == 0:
                    continue
                player = table_data[i][j]["player"]
                marker = sc_data.event_data.loc[table_data[i][j]["img"]]["Name"]
                loc = self.locations[table_data[i][j]["loc"] - 1]
                self.add_teleport(player, marker, loc, [i + 1, j])
        
class TeleportTableStack(QStackedWidget):
    """A stack of teleport tables, one for each count."""
    teleport_cell = pyqtSignal(int, int)
    update_locs = pyqtSignal()
    
    def __init__(self, locations: list[Location]):
        super().__init__()
        self.locations = locations
    
    def insert_table(self, index: int) -> None:
        """Inserts a table to the stack at position index."""
        # Encases the input table in a frame for alignment purposes.
        table = TeleportTable(self.locations)
        layout = QHBoxLayout()
        layout.addWidget(table, alignment=Qt.AlignmentFlag.AlignTop)
        frame = QFrame()
        frame.setLayout(layout)
        super().insertWidget(index, frame)
        
        table.teleport_cell.connect(self.teleport_cell)
        self.update_locs.connect(table.update_locs)
        
    def emit_change(self) -> None:
        """Emits a signal when the current table is changed."""
        self.teleport_cell.emit(-1, -1)
        
    def get_table(self, index: int) -> None:
        """Returns the table at the input index."""
        return self.widget(index).layout().itemAt(0).widget()
        
    def add_teleport(self,
                     count: int,
                     player: int,
                     marker: str,
                     loc: Location,
                     cell: list[int]) -> None:
        """Adds a teleport to the table corresponding to the input count."""
        table = self.get_table(count - 1)
        table.add_teleport(player, marker, loc, cell)
        
    def delete_teleport(self, count: int, loc: int) -> None:
        """Updates the relevant teleport table after deleting a teleport."""
        table = self.get_table(count - 1)
        table.delete_teleport(loc)
        
    def delete_loc(self, loc: int) -> None:
        """Updates the teleport tables after deleting a location."""
        for i in range(self.count()):
            table = self.get_table(i)
            table.delete_teleport(loc)
        self.update_locs.emit()
        
    def change_count(self, count: int) -> None:
        """Displays the table corresponding to the input count."""
        if count > self.count():
            self.insert_table(self.count())
        self.setCurrentIndex(count - 1)
        
    def delete_count(self, count: int) -> None:
        """Deletes the table corresponding to the input count."""
        self.removeWidget(self.widget(count - 1))
    
    def insert_count(self, count: int) -> None:
        """Inserts a table at position count."""
        self.insert_table(count - 1)
        
    def add_row(self) -> None:
        """Adds a row to the current table."""
        table = self.get_table(self.currentIndex())
        table.insertRow(table.rowCount())
        
    def reset(self) -> None:
        """Clears the teleport table corresponding to count 1 and deletes the rest."""
        while self.count() > 1:
            self.removeWidget(self.widget(self.count() - 1))
        table = self.get_table(0)
        table.reset()
        
    def save(self, data: dict) -> None:
        """Creates a key in data for saving teleport table data and passes data to each table to
        save the data from individual tables.
        """
        data["Teleport tables"] = {i: [] for i in range(self.count())}
        for i in range(self.count()):
            table = self.get_table(i)
            table.save(i, data["Teleport tables"][i])
            
    def load(self, data: dict) -> None:
        """Recreates the teleport tables from saved data."""
        table_data = data["Teleport tables"]
        num_tables = len(table_data)
        for i in range(num_tables - 1):
            self.insert_table(self.count())
        for i in range(num_tables):
            self.get_table(i).load(table_data[str(i)])
        
class TeleportUIFrame(QFrame):
    """Contains widgets for editing wall events."""
    set_shortcuts = pyqtSignal()
    
    update_locs = pyqtSignal()
    delete_loc = pyqtSignal(int)

    change_count = pyqtSignal(int)
    delete_count = pyqtSignal(int)
    insert_count = pyqtSignal(int)
    
    teleport_player = pyqtSignal(int)
    teleport_marker = pyqtSignal(str)
    teleport_cell = pyqtSignal(int, int)
    add_teleport = pyqtSignal(int, int, str, Location, list)
    delete_teleport = pyqtSignal(int, int)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)
    
    def __init__(self, locations: list[Location]):
        super().__init__()
        
        teleport_menu_frame = TeleportMenuFrame()
        stack = TeleportTableStack(locations)
        stack.insert_table(0)
        player_menu = PlayerMenu("The selected player will own the teleport markers", True)
        icon_path = os.path.join(read_write.get_path("Icons"), "add.png")
        add_teleport_button = IconButton(QIcon(icon_path), 32, 36, "Add a teleport event", False)

        layout = QGridLayout()
        layout.addWidget(teleport_menu_frame, 0, 0, 5, 3)
        layout.addWidget(QLabel("Player: "), 5, 0)
        layout.addWidget(player_menu, 5, 1)
        layout.addWidget(QLabel("Teleports:"), 0, 3)
        layout.addWidget(stack, 1, 3, 4, 3)
        layout.addWidget(add_teleport_button, 5, 4)
        self.setLayout(layout)

        self.update_locs.connect(stack.update_locs)
        self.delete_loc.connect(stack.delete_loc)
       
        self.change_count.connect(stack.change_count)
        self.delete_count.connect(stack.delete_count)
        self.insert_count.connect(stack.insert_count)
        
        player_menu.currentIndexChanged.connect(self.teleport_player)
        teleport_menu_frame.teleport_marker.connect(self.teleport_marker)
        stack.teleport_cell.connect(self.teleport_cell)
        self.add_teleport.connect(stack.add_teleport)
        self.delete_teleport.connect(stack.delete_teleport)
        add_teleport_button.clicked.connect(stack.add_row)

        self.reset.connect(stack.reset)
        self.save.connect(stack.save)
        self.load.connect(stack.load)