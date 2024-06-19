import os
from PyQt6.QtWidgets import (QFrame,
                             QLabel,
                             QHBoxLayout,
                             QVBoxLayout,
                             QGridLayout,
                             QButtonGroup)
from PyQt6.QtGui import QIcon, QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from .ui_shared import PlayerMenu, EventMenu, RadioButton
from src import read_write
from src import sc_data

class WallMenuFrame(QFrame):
    """Contains an organized collection of wall menus."""
    data = sc_data.event_data[sc_data.event_data["Wall Image"].notna()]
    
    wall_unit = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        self.unit = None
        layout = QGridLayout()
        layout.addWidget(QLabel("Walls: "), 0, 0)
        
        # We organize the list of wall unit options into various lists sorted by the type of wall
        # unit, whether or not the unit is creatable with triggers, etc. This is mostly to keep the
        # menu size manageable.
        rows = self.num_subtypes(sorted(self.data["Creatable"].unique())[0]) + 1
        image_path = read_write.get_path("Wall")
        
        for i, creatable in enumerate(sorted(self.data["Creatable"].unique())):
            data_fixed_type = self.data[self.data["Creatable"] == creatable]
            label = "Creatable: " if creatable else "Noncreatable: "
            layout.addWidget(QLabel(label), rows*i + 1, 0)
            for j, subtype in enumerate(sorted(data_fixed_type["Subtype"].unique())):
                data_fixed_subtype = data_fixed_type[
                    data_fixed_type["Subtype"] == subtype
                    ].sort_values("Name")
                    
                items = data_fixed_subtype["Name"].tolist()
                wall_IDs = data_fixed_subtype["Wall Image"].tolist()
                # Create the wall icons.
                icons = []
                for wall_ID in wall_IDs:
                    path = os.path.join(image_path, str(int(wall_ID)))
                    path = os.path.join(path, "static.png")
                    icon = QIcon(path)
                    icons.append(icon)
                    
                menu = EventMenu(icons, items, 275)
                menu.textActivated.connect(self.set_selection)
                layout.addWidget(QLabel("{}: ".format(subtype)), rows*i + 2 + j, 0)
                layout.addWidget(menu, rows*i + 2 + j, 1)
                
        self.setLayout(layout)

    def num_subtypes(self, creatable: bool) -> None:
        """Returns the number of unique subtypes appearing in rows of the data with the input
        creatability.
        """
        # Used to organize the layout.
        data_fixed_type = self.data[(self.data["Creatable"] == creatable)]
        return len(data_fixed_type["Subtype"].unique())
    
    def set_selection(self, unit: str) -> None:
        """Sets the wall unit to the selected option and clears the other menus."""
        for widget in self.children():
            if type(widget) is EventMenu and widget.currentText() != unit:
                widget.setCurrentIndex(-1)
        self.wall_unit.emit(unit)
                
class WallOptionsFrame(QFrame):
    """Contains widgets for wall placement."""
    wall_player = pyqtSignal(int)
    wall_option = pyqtSignal(str)
    set_shortcuts = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        player_menu = PlayerMenu("The selected player will own the wall units.", True)
        
        place_button = RadioButton("Place",
                                   "Place walls.",
                                   QKeySequence("P"))
        place_button.setChecked(True)
        remove_button = RadioButton("Remove",
                                    "Remove walls.",
                                    QKeySequence("R"))
        
        placement_buttons = QButtonGroup(parent=self)
        placement_buttons.addButton(place_button)
        placement_buttons.addButton(remove_button)
        
        placement_layout = QVBoxLayout()
        placement_layout.addWidget(QLabel("Place/Remove:"))
        placement_layout.addWidget(place_button)
        placement_layout.addWidget(remove_button)
        placement_frame = QFrame()
        placement_frame.setLayout(placement_layout)
        
        kill_unit_button = RadioButton("Kill Unit",
                                       "Remove walls via the Kill Unit action.")
        remove_unit_button = RadioButton("Remove Unit",
                                         "Remove walls via the Remove Unit action.")
        
        removal_type_buttons = QButtonGroup(parent=self)
        removal_type_buttons.addButton(kill_unit_button)
        removal_type_buttons.addButton(remove_unit_button)
        
        removal_type_layout = QVBoxLayout()
        removal_type_layout.addWidget(QLabel("Removal type:"))
        removal_type_layout.addWidget(kill_unit_button)
        removal_type_layout.addWidget(remove_unit_button)
        removal_type_frame = QFrame()
        removal_type_frame.setLayout(removal_type_layout)

        layout = QGridLayout()
        layout.addWidget(QLabel("Options: "), 0, 0)
        layout.addWidget(QLabel("Player: "), 1, 0)
        layout.addWidget(player_menu, 1, 1)
        layout.addWidget(placement_frame, 2, 0, 3, 1)
        layout.addWidget(removal_type_frame, 2, 1, 3, 1)
        self.setLayout(layout)
                                
        player_menu.setCurrentIndex(read_write.read_setting("Wall player"))
        kill_wall = read_write.read_setting("Wall removal type") == "Kill Unit"
        kill_unit_button.setChecked(kill_wall)
        remove_unit_button.setChecked(not kill_wall)

        self.set_shortcuts.connect(place_button.set_shortcut)
        self.set_shortcuts.connect(remove_button.set_shortcut)

        player_menu.currentIndexChanged.connect(self.wall_player)
        place_button.clicked.connect(self.set_wall_option)
        remove_button.clicked.connect(self.set_wall_option)
        kill_unit_button.clicked.connect(self.set_wall_option)
        remove_unit_button.clicked.connect(self.set_wall_option)

        player_menu.currentIndexChanged.connect(self.save_wall_player)
        kill_unit_button.clicked.connect(self.save_wall_removal_type)
        remove_unit_button.clicked.connect(self.save_wall_removal_type)

    def set_wall_option(self, option: str):
        """Sends a signal indicating a wall option has been chosen."""
        self.wall_option.emit(self.sender().text())
        
    def save_wall_player(self, player: int):
        """When the wall player is changed, saves the setting in settings.json."""
        read_write.write_setting("Wall player", player)
        
    def save_wall_removal_type(self, option: str):
        """When the wall removal type is changed, saves the setting in settings.json."""
        read_write.write_setting("Wall removal type", self.sender().text())
        
class WallUIframe(QFrame):
    """Contains widgets for editing wall events."""
    set_shortcuts = pyqtSignal()
    wall_unit = pyqtSignal(str)
    wall_player = pyqtSignal(int)
    wall_option = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        wall_menu_frame = WallMenuFrame()
        wall_options_frame = WallOptionsFrame()
        
        layout = QHBoxLayout()
        layout.addWidget(wall_menu_frame, alignment = Qt.AlignmentFlag.AlignTop)
        layout.addWidget(wall_options_frame, alignment = Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        self.set_shortcuts.connect(wall_options_frame.set_shortcuts)
        wall_menu_frame.wall_unit.connect(self.wall_unit)
        wall_options_frame.wall_player.connect(self.wall_player)
        wall_options_frame.wall_option.connect(self.wall_option)