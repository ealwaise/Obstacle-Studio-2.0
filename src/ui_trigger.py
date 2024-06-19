import json
from PyQt6.QtWidgets import (QWidget,
                             QButtonGroup,
                             QCheckBox,
                             QRadioButton,
                             QSpinBox,
                             QPushButton,
                             QLabel,
                             QGridLayout,
                             QVBoxLayout,
                             QFrame,
                             QTextEdit,
                             QLineEdit,
                             QDialog)
from PyQt6.QtCore import Qt, pyqtSignal
from .ui_shared import PlayerMenu, SCMenu
from .graphics import Location
from .obstacle import Obstacle
from src import sc_data
from src import trig_gen
from src import read_write

class PlayerMenuKeyed(PlayerMenu):
    """A player menu with an attached dictionary key for storing the menu's value."""
    set_option = pyqtSignal(str, int)
    
    def __init__(self, key: str, tooltip: str, include_current: bool=False) -> None:
        super().__init__(tooltip, include_current)
        self.key = key
        self.setToolTip(tooltip)
        self.setCurrentText(read_write.read_setting(key))
        self.currentTextChanged.connect(self.emit_option)
        
    def emit_option(self, index: int) -> None:
        """Emits a signal when an option is selected."""
        self.set_option.emit(self.key, index)

class SCMenuKeyed(SCMenu):
    """A SC menu with an attached dictionary key for storing the menu's value."""
    set_option = pyqtSignal(str, str)
    
    def __init__(self, key: str, tooltip: str, items: list[str], width: int):
        super().__init__(items, width)
        self.key = key
        self.setToolTip(tooltip)
        self.setCurrentText(read_write.read_setting(key))
        self.currentTextChanged.connect(self.emit_option)
        
    def emit_option(self, text: str) -> None:
        """Emits a signal when an option is selected."""
        self.set_option.emit(self.key, text)
        
class LineEditKeyed(QLineEdit):
    """A QLineEdit with an attached dictionary key for storing the input text."""
    set_option = pyqtSignal(str, str)
    
    def __init__(self, key: str, tooltip: str):
        super().__init__()
        self.key = key
        self.setToolTip(tooltip)
        self.setText(read_write.read_setting(key))
        self.textChanged.connect(self.emit_option)
        
    def emit_option(self, text: str) -> None:
        """Emits a signal when the text is altered."""
        self.set_option.emit(self.key, text)
        
class CheckBoxKeyed(QCheckBox):
    """A QCheckBox with an attached dictionary key for storing the box's state."""
    set_option = pyqtSignal(str, int)
    
    def __init__(self, key: str, text: str):
        super().__init__(text)
        self.key = key
        self.setChecked(read_write.read_setting(key))
        self.stateChanged.connect(self.emit_option)
        
    def emit_option(self, state: int) -> None:
        """Emits a signal when the text is altered."""
        self.set_option.emit(self.key, state)

class ObNumberBox(QSpinBox):
    """A QSpinBox for setting the obstacle number."""
    
    def __init__(self):
        super().__init__()
        self.setMinimum(1)
        
    def reset(self) -> None:
        """Sets the box's value to 1."""
        self.setValue(1)
        
    def save(self, data: dict) -> None:
        """Saves the box's value in data."""
        data["Obstacle number"] = self.value()
        
    def load(self, data: dict) -> None:
        """Sets the box's value to the value stored in the data."""
        self.setValue(data["Obstacle number"])
        
class QRadioButtonKeyed(QRadioButton):
    """A QRadioButton with an attached dictionary key for storing the input text."""
    set_option = pyqtSignal(str, str)
    
    def __init__(self, key: str, text: str, tooltip: str) -> None:
        super().__init__(text)
        self.key = key
        self.setToolTip(tooltip)
        if read_write.read_setting(key) == text:
            self.setChecked(True)
        self.clicked.connect(self.emit_option)
    
    def emit_option(self) -> None:
        """Emits a signal when the text is altered."""
        self.set_option.emit(self.key, self.text())

class TriggerGeneratorWindow(QDialog):
    """Contains widgets used to generate obstacle triggers and adjust related settings."""
    print_triggers = pyqtSignal(str)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)
    
    def __init__(self, locations: list[Location], ob: Obstacle, parent: QWidget):
        super().__init__(parent)
        
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle("Trigger generator")
        self.locations = locations
        self.ob = ob
        self.ob_number = 1
        path = read_write.get_path("Settings")
        with open(path, 'r') as file:
            self.options = json.load(file)
        
        text_box = QTextEdit()
        ui_frame = QFrame()

        # Widgets for selecting players.
        trigger_player_menu = PlayerMenuKeyed(
            "Trigger player",
            "The selected player will own the obstacle triggers."
        )
        force_name_entry = LineEditKeyed(
            "Force name",
            "The name of the Force containing the human players."
        )
        death_count_player_menu = PlayerMenuKeyed(
            "DC player",
            "Death counts in the obstacle triggers will be assigned to the selected player."""
        )
        
        # Menus for selecting death count units.
        ob_num_unit_menu = SCMenuKeyed(
            "Obstacle DC unit",
            "The unit used for a death count which tracks the obstacle number.",
            sc_data.unit_list,
            260
        )
        count_num_unit_menu = SCMenuKeyed(
            "Count DC unit",
            "The unit used for a death count which tracks the count number.",
            sc_data.unit_list,
            260
        )
        delay_unit_menu = SCMenuKeyed(
            "Delay DC unit",
            "The unit used for a death count whcih tracks obstacle delays.",
            sc_data.unit_list,
            260
        )
        
        # Widgets for styling trigger comments.
        add_comments_checkbox = CheckBoxKeyed("Add comments", "Add comments:")
        ob_text_entry = LineEditKeyed(
            "Obstacle text",
            "The text entered will appear before the obstacle number in trigger comments."
        )
        count_text_entry = LineEditKeyed(
            "Count text",
            "The text entered will appear before the count number in trigger comments."
        )
        part_text_entry = LineEditKeyed(
            "Part text",
            """The text entered will appear before the part number in trigger comments when a count
            is split into multiple triggers."""
        )
        delineator_entry = LineEditKeyed(
            "Delineator",
            """The text entered will be placed between the obstacle, count, and part number text in
            trigger comments."""
        )
        audio_text_entry = LineEditKeyed(
            "Audio text",
            """The text entered will be placed at the end of comments for audio mapping
            triggers."""
        )
        
        # Radio buttons to select how players die in the obstacle.
        kill_unit_button = QRadioButtonKeyed(
            "Death type",
            "Kill Unit",
            "Kill players in the obstacle via the Kill Unit action."
        )
        remove_unit_button = QRadioButtonKeyed(
            "Death type",
            "Remove Unit",
            "Kill players in the obstacle via the Remove Unit action."
        )
        death_buttons = QButtonGroup(parent=self)
        death_buttons.addButton(kill_unit_button)
        death_buttons.addButton(remove_unit_button)
        
        # Menu to select which unit the player controls.
        player_unit_menu = SCMenuKeyed(
            "Player unit",
            "The unit the player controls.",
            sc_data.men_list, 
            260
        )
        
        # Spinbox for setting the ob number.
        ob_number_box = ObNumberBox()
        
        # Button for generating triggers.
        generate_button = QPushButton("Generate")
        replace_button = QPushButton("Replace")

        ui_layout = QGridLayout()
        ui_layout.addWidget(QLabel("Player options:"), 0, 0)
        ui_layout.addWidget(QLabel("Trigger owner: "), 1, 0)
        ui_layout.addWidget(trigger_player_menu, 1, 1)
        ui_layout.addWidget(QLabel("Player Force name: "), 2, 0)
        ui_layout.addWidget(force_name_entry, 2, 1)
        
        ui_layout.addWidget(QLabel("Death count options: "), 0, 2)
        ui_layout.addWidget(QLabel("Player:"), 1, 2)
        ui_layout.addWidget(death_count_player_menu, 1, 3)
        ui_layout.addWidget(QLabel("Units:"), 2, 3)
        ui_layout.addWidget(QLabel("Obstacle #: "), 3, 2)
        ui_layout.addWidget(ob_num_unit_menu, 3, 3)
        ui_layout.addWidget(QLabel("Count #: "), 4, 2)
        ui_layout.addWidget(count_num_unit_menu, 4, 3)
        ui_layout.addWidget(QLabel("Delay (# frames): "), 5, 2)
        ui_layout.addWidget(delay_unit_menu, 5, 3)

        ui_layout.addWidget(QLabel("Comment schema:"), 0, 4)
        ui_layout.addWidget(add_comments_checkbox, 1, 4)
        ui_layout.addWidget(QLabel("Obstacle text: "), 2, 4)
        ui_layout.addWidget(ob_text_entry, 2, 5)
        ui_layout.addWidget(QLabel("Count text: "), 3, 4)
        ui_layout.addWidget(count_text_entry, 3, 5)
        ui_layout.addWidget(QLabel("Part text: "), 4, 4)
        ui_layout.addWidget(part_text_entry, 4, 5)
        ui_layout.addWidget(QLabel("Delineator: "), 5, 4)
        ui_layout.addWidget(delineator_entry, 5, 5)
        ui_layout.addWidget(QLabel("Audio text: "), 6, 4)
        ui_layout.addWidget(audio_text_entry, 6, 5)
        
        ui_layout.addWidget(QLabel("Player unit:"), 0, 6)
        ui_layout.addWidget(player_unit_menu, 1, 6)

        ui_layout.addWidget(QLabel("Death type:"), 0, 7)
        ui_layout.addWidget(kill_unit_button, 1, 7)
        ui_layout.addWidget(remove_unit_button, 2, 7)
        
        ui_layout.addWidget(QLabel("Obstacle number:"), 0, 8)
        ui_layout.addWidget(ob_number_box, 1, 8)
        
        ui_layout.addWidget(QLabel("Trigger generation:"), 0, 9)
        ui_layout.addWidget(generate_button, 1, 9)
        ui_layout.addWidget(replace_button, 2, 9)
        ui_frame.setLayout(ui_layout)
        
        layout = QVBoxLayout()
        layout.addWidget(text_box)
        layout.addWidget(ui_frame)
        self.setLayout(layout)
        
        self.print_triggers.connect(text_box.setText)
        trigger_player_menu.set_option.connect(self.change_option)
        force_name_entry.set_option.connect(self.change_option)
        death_count_player_menu.set_option.connect(self.change_option)
        ob_num_unit_menu.set_option.connect(self.change_option)
        count_num_unit_menu.set_option.connect(self.change_option)
        delay_unit_menu.set_option.connect(self.change_option)
        add_comments_checkbox.set_option.connect(self.change_option)
        ob_text_entry.set_option.connect(self.change_option)
        count_text_entry.set_option.connect(self.change_option)
        part_text_entry.set_option.connect(self.change_option)
        delineator_entry.set_option.connect(self.change_option)
        player_unit_menu.set_option.connect(self.change_option)
        kill_unit_button.set_option.connect(self.change_option)
        ob_number_box.valueChanged.connect(self.set_ob_number)
        remove_unit_button.set_option.connect(self.change_option)
        generate_button.clicked.connect(self.generate_triggers)
        
        self.reset.connect(ob_number_box.reset)
        self.save.connect(ob_number_box.save)
        self.load.connect(ob_number_box.load)
        
    def change_option(self, key: str, value: int | str) -> None:
        """Sets self.options[key] = value when an option is changed."""
        self.options[key] = value
        
    def set_ob_number(self, num: int) -> None:
        """Sets the obstacle number when the value in the obstacle number box is changed."""
        self.ob_number = num
        
    def generate_triggers(self) -> None:
        """Prints the triggers to generate the obstacle in the text box."""
        death_count_options = {
            "Player": self.options["DC player"],
            "Ob": self.options["Obstacle DC unit"],
            "Count": self.options["Count DC unit"],
            "Delay": self.options["Delay DC unit"],
        }
        comment_options = {
            "Add comments": self.options["Add comments"],
            "Obstacle text": self.options["Obstacle text"],
            "Count text": self.options["Count text"],
            "Part text": self.options["Part text"],
            "Delineator": self.options["Delineator"],
            "Audio text": self.options["Audio text"]
        }

        self.print_triggers.emit(
            trig_gen.obstacle_triggers(
                self.locations,
                self.ob,
                self.ob_number,
                death_count_options,
                self.options["Trigger player"],
                self.options["Death type"],
                self.options["Player unit"],
                self.options["Force name"],
                comment_options
            )
        )