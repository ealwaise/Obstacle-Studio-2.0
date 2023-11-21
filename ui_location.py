from PyQt6.QtWidgets import (QFrame,
                             QVBoxLayout,
                             QHBoxLayout,
                             QGridLayout,
                             QLineEdit,
                             QLabel,
                             QComboBox,
                             QSpinBox,
                             QPushButton,
                             QButtonGroup,
                             QRadioButton,
                             QDialog)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import (Qt,
                          QEvent,
                          pyqtSignal)
from ui_shared import SizeFrame
import read_write

class LocationLimitPopup(QDialog):
    """A popup appearing when the user attempts to place more than 255 locations."""
    popup = pyqtSignal(bool)
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setWindowTitle(" ")
        text = "You have reached the 255 location limit."
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel(text), alignment=Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)
        
    def open(self):
        """Opens the window and sends a signal to disable the editor."""
        self.popup.emit(False)
        self.show()
        
    def closeEvent(self, event: QEvent) -> None:
        """Closes the window."""
        self.popup.emit(True)
        event.accept()
        
class LocationToolButton(QRadioButton):
    """A radio button used to choose a location editing tool."""
    set_loc_tool = pyqtSignal(str)
    
    def __init__(self, checked: bool, text: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(text)
        
        self.setChecked(checked)
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        self.shortcut = shortcut
        self.clicked.connect(lambda: self.set_loc_tool.emit(text))
        
    def set_shortcut(self) -> None:
        """Sets the button's shortcut."""
        self.setShortcut(self.shortcut)
       
class LocationToolFrame(QFrame):
    """Contains radio buttons to switch between location editing tools."""
    set_loc_tool = pyqtSignal(str)
    set_shortcuts = pyqtSignal()
    
    def __init__(self):
        super().__init__()

        place_button = LocationToolButton(True,
                                          "Place",
                                          "Place locations",
                                          QKeySequence("P"))
        adjust_button = LocationToolButton(False,
                                           "Adjust",
                                           "Move and resize locations",
                                           QKeySequence("A"))
        
        buttons = QButtonGroup(parent=self)
        buttons.addButton(place_button)
        buttons.addButton(adjust_button)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tool:"),
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(place_button,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(adjust_button,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)
        
        place_button.set_loc_tool.connect(self.set_loc_tool)
        adjust_button.set_loc_tool.connect(self.set_loc_tool)
        self.set_shortcuts.connect(place_button.set_shortcut)
        self.set_shortcuts.connect(adjust_button.set_shortcut)
        
class LocationPrefixEdit(QLineEdit):
    """A line edit for editing location prefixes."""
    
    def __init__(self):
        super().__init__()
        self.setMinimumWidth(190)
        
    def save(self, data: dict) -> None:
        """Saves the current prefix."""
        data["Location prefix"] = self.text()
        
    def load(self, data: dict) -> None:
        """Loads the location prefix from saved data."""
        self.setText(data["Location prefix"])
        
class LocationNamingFrame(QFrame):
    """A frame containing widgets to choose how locations are named."""
    set_loc_prefix = pyqtSignal(str)
    set_loc_numbering = pyqtSignal(int)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()

        prefix_entry = LocationPrefixEdit()
        conventions = ["Numeric: No leading 0's",
                       "Numeric: Leading 0's",
                       "Alphabetic: lowercase",
                       "Alphabetic: uppercase"]
        convention_menu = QComboBox()
        convention_menu.setMinimumWidth(190)
        convention_menu.addItems(conventions)
        convention_menu.setCurrentIndex(read_write.read_setting("Location numbering convention"))
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Naming schema:"),
                         0,
                         0,
                         1,
                         2,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(QLabel("Prefix: "),
                         1,
                         0,
                         alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(prefix_entry,
                         1,
                         1,
                         alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(QLabel("Numbering convention: "),
                         2,
                         0,
                         alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(convention_menu,
                         2,
                         1,
                         alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)
        
        prefix_entry.textChanged.connect(self.set_loc_prefix)
        convention_menu.currentIndexChanged.connect(self.set_loc_numbering)
        convention_menu.currentIndexChanged.connect(self.save_location_numbering)
        
        self.reset.connect(prefix_entry.clear)
        self.save.connect(prefix_entry.save)
        self.load.connect(prefix_entry.load)
        
    def save_location_numbering(self, index: int) -> None:
        """When the location numbering convention is changed, save the setting to settings.json."""
        read_write.write_setting("Location numbering convention", index)
        
class LocationIDoffsetBox(QSpinBox):
    """A spinbox used to adjust the Location ID offset."""
    
    def __init__(self):
        super().__init__()
        
    def reset(self) -> None:
        """Resets the value to 0."""
        self.setValue(0)
        
    def save(self, data: dict) -> None:
        """Saves the current value."""
        data["Location ID offset"] = self.value()
        
    def load(self, data: dict) -> None:
        """Loads the ID offset from saved data."""
        self.setValue(int(data["Location ID offset"]))
        
class LocationUIframe(QFrame):
    """A frame containing all widgets used to edit locations."""
    set_shortcuts = pyqtSignal()
    set_loc_tool = pyqtSignal(str)
    set_width = pyqtSignal(float, str)
    set_height = pyqtSignal(float, str)
    set_ID_offset = pyqtSignal(int)
    set_loc_prefix = pyqtSignal(str)
    set_loc_numbering = pyqtSignal(int)
    delete_locs = pyqtSignal(bool)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        location_tool_frame = LocationToolFrame()
        size_frame = SizeFrame(256, 0.25, "Location", 1, 1)
        location_naming_frame = LocationNamingFrame()
        id_offset_box = LocationIDoffsetBox()
        delete_locs_button = QPushButton("Delete all locations")
        delete_locs_button.setToolTip("Delete all currently placed locations.")
        
        frame_layout = QGridLayout()
        frame_layout.addWidget(location_naming_frame, 0, 0, 3, 6, alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        frame_layout.addWidget(QLabel("Location ID offset: "), 3, 0)
        frame_layout.addWidget(id_offset_box, 3, 1)
        frame = QFrame()
        frame.setLayout(frame_layout)

        layout = QHBoxLayout()
        layout.addWidget(location_tool_frame,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(size_frame,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(frame,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(delete_locs_button,
                         alignment=Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)
        
        location_tool_frame.set_loc_tool.connect(self.set_loc_tool)
        size_frame.set_width.connect(self.set_width)
        size_frame.set_height.connect(self.set_height)
        id_offset_box.valueChanged.connect(self.set_ID_offset)
        location_naming_frame.set_loc_prefix.connect(self.set_loc_prefix)
        location_naming_frame.set_loc_numbering.connect(self.set_loc_numbering)
        delete_locs_button.clicked.connect(self.delete_locs)
        self.set_shortcuts.connect(location_tool_frame.set_shortcuts)
        self.set_shortcuts.connect(size_frame.set_shortcuts)
        
        self.reset.connect(location_naming_frame.reset)
        self.reset.connect(id_offset_box.reset)
        self.save.connect(location_naming_frame.save)
        self.save.connect(id_offset_box.save)
        self.load.connect(location_naming_frame.load)
        self.load.connect(id_offset_box.load)