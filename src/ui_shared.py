from PyQt6.QtWidgets import (QWidget,
                             QButtonGroup,
                             QCheckBox,
                             QDoubleSpinBox,
                             QPushButton,
                             QLabel,
                             QGridLayout,
                             QFrame,
                             QComboBox,
                             QSpinBox,
                             QRadioButton,
                             QCompleter,
                             QFileDialog)
from PyQt6.QtGui import QKeySequence, QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QSize

class SizeButton(QPushButton):
    """A button used to alter the sizes of placement tools."""
    size = 40
    
    set_width = pyqtSignal(float, str)
    set_height = pyqtSignal(float, str)
    
    def __init__(self, width: int, height: int, text: str, mode: str, shortcut: QKeySequence):
        super().__init__(text)
        
        self.width, self.height = width, height
        self.mode = mode
        self.shortcut = shortcut
        self.setCheckable(True)
        self.setFixedSize(SizeButton.size*width, SizeButton.size*height)
        self.setToolTip("Shortcut: {}".format(shortcut.toString()))
        
        self.clicked.connect(lambda: self.set_width.emit(width, mode))
        self.clicked.connect(lambda: self.set_height.emit(height, mode))
        
    def set_state(self, checked: bool):
        """Sets the state of the button to not checked."""
        self.setEnabled(not checked)
        if not checked and self.isChecked():
            self.set_width.emit(self.width, self.mode)
            self.set_height.emit(self.height, self.mode)
    
    def set_shortcut(self):
        """Sets the button's key shortchut to shortcut."""
        self.setShortcut(self.shortcut)

class SizeBox(QDoubleSpinBox):
    """A spin box used to alter the sizes of placement tools."""
    set_dim = pyqtSignal(float, str)
    
    def __init__(self, step: float, maximum: int, decimals: int, mode: str, dim: str):
        super().__init__()
        
        self.setSingleStep(step)
        self.setMinimum(step)
        self.setMaximum(maximum)
        self.setDecimals(decimals)
        self.setValue(1)
        self.setEnabled(False)
        self.step = step
        self.mode = mode
        self.setToolTip(dim)
        
        self.editingFinished.connect(self.round_input)
        self.valueChanged.connect(lambda: self.set_dim.emit(self.value(), mode))
        
    def round_input(self):
        """Rounds the input to the nearest valid value."""
        value = self.value()
        lower = int(value / self.step)
        rounded_value = lower if value < lower + 0.5 else lower + 1
        self.setValue(self.step * rounded_value)
        
    def set_state(self, checked):
        """Sets thes state of the spin box to checked."""
        self.setEnabled(checked)
        if checked:
            self.set_dim.emit(self.value(), self.mode)

class SizeFrame(QFrame):
    """Contains widgets used to change the size of a placement tool."""
    max_width, max_height = 3, 3
    shortcuts = [QKeySequence('1'),
                 QKeySequence('Shift+2'),
                 QKeySequence('Shift+3'),
                 QKeySequence('Alt+2'),
                 QKeySequence('2'),
                 QKeySequence('Ctrl+2'),
                 QKeySequence('Alt+3'),
                 QKeySequence('Ctrl+3'),
                 QKeySequence('3')]
                 
    set_width = pyqtSignal(float, str)
    set_height = pyqtSignal(float, str)
    set_shortcuts = pyqtSignal()
    
    def __init__(self,
                 maximum: int,
                 step: float,
                 mode: str,
                 default_width: int,
                 default_height: int):
        super().__init__()
        layout = QGridLayout()
        
        # Buttons which set the placement size to fixed dimensions.
        fixed_size_buttons = QButtonGroup(parent=self)
        for i in range(self.max_width * self.max_height):
            width, height = 1 + (i % self.max_width), 1 + i // self.max_height
            button = SizeButton(width,
                                height,
                                "{}×{}".format(width, height),
                                mode,
                                self.shortcuts[i])
            if width == default_width and height == default_height:
                button.setChecked(True)
            fixed_size_buttons.addButton(button)
            layout.addWidget(button,
                             1 + height*(height - 1) // 2,
                             3 + width*(width - 1) // 2,
                             height,
                             width)
            button.set_width.connect(self.set_width)
            button.set_height.connect(self.set_height)
            self.set_shortcuts.connect(button.set_shortcut)

        # Spin boxes which allow the user to set the placement size to dimensions not encompassed
        # by the above buttons.
        decimals = 0 if mode == "Terrain" else 2
        step = 1 if mode == "Terrain" else 0.25
        custom_width_box = SizeBox(step, maximum, decimals, mode, "Width")
        custom_height_box = SizeBox(step, maximum, decimals, mode, "Height")
        custom_size_checkbox = QCheckBox("Custom:")
        
        custom_size_layout = QGridLayout()
        custom_size_layout.addWidget(custom_width_box, 0, 0, 1, 3)
        custom_size_layout.addWidget(QLabel("×"), 0, 3, alignment=Qt.AlignmentFlag.AlignCenter)
        custom_size_layout.addWidget(custom_height_box, 0, 4, 1, 3)
        custom_size_frame = QFrame()
        custom_size_frame.setLayout(custom_size_layout)
        
        row = 1 + self.max_height*(self.max_height + 1) // 2
        layout.addWidget(QLabel("Size:"), 0, 0)
        layout.addWidget(QLabel("Fixed:"), 1, 0)
        layout.addWidget(custom_size_checkbox, row, 0, 1, 3)
        layout.addWidget(custom_size_frame, row, 3, 1, 6, alignment=Qt.AlignmentFlag.AlignLeft)
        self.setLayout(layout)
        
        custom_width_box.set_dim.connect(self.set_width)
        custom_height_box.set_dim.connect(self.set_height)
        custom_size_checkbox.clicked.connect(custom_width_box.set_state)
        custom_size_checkbox.clicked.connect(custom_height_box.set_state)
        for button in fixed_size_buttons.buttons():
            custom_size_checkbox.clicked.connect(button.set_state)
            
class IconButton(QPushButton):
    """A button with an icon on it."""

    def __init__(self, icon: QIcon, icon_size: int, size: int, tooltip: str, checkable: bool):
        super().__init__()

        self.setIcon(icon)
        self.setIconSize(QSize(icon_size, icon_size))
        self.setFixedSize(size, size)
        self.setToolTip(tooltip)
        self.setCheckable(checkable)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

    def set_state(self, enabled: bool):
        """Sets the state of the button to enabled and unchecks it if enabled is false."""
        self.setEnabled(enabled)
        if not enabled:
            self.setChecked(False)
            
class FixedWidthButton(QPushButton):
    """A push button with a fixed width."""
    
    def __init__(self, width: int, text: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(text)
        
        self.shortcut = shortcut
        self.setFixedWidth(width)
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
    
    def set_shortcut(self):
        """Sets the button's shortcut."""
        self.setShortcut(self.shortcut)
        
class RadioButton(QRadioButton):
    """A radio button with a tooltip and shortcut."""
    
    def __init__(self, text: str, tooltip: str, shortcut: QKeySequence=None):
        super().__init__(text)
        
        self.shortcut = shortcut
        if shortcut:
            self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        else:
            self.setToolTip(tooltip)
    
    def set_shortcut(self):
        """Sets the button's shortcut."""
        if self.shortcut:
            self.setShortcut(self.shortcut)
    
class PlayerMenu(QComboBox):
    """A menu of Starcraft players to choose from."""
    
    def __init__(self, tooltip: str, include_current: bool=False):
        super().__init__()

        players = ["Current Player"] if include_current else []
        players.extend(["Player 1",
                        "Player 2",
                        "Player 3",
                        "Player 4",
                        "Player 5",
                        "Player 6",
                        "Player 7",
                        "Player 8"])
        self.addItems(players)
        self.setToolTip(tooltip)
        self.setCurrentIndex(0)
        
class EventMenu(QComboBox):
    """A menu of obstacle events with icons."""
    icon_size = QSize(32, 32)
    
    def __init__(self, icons: list[QIcon], items: list[str], width: int):
        super().__init__()
        
        for icon, item, in zip(icons, items):
            self.addItem(icon, item)
        self.setIconSize(self.icon_size)
        self.setEditable(True)
        self.setMinimumWidth(width)
        self.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        
        completer = QCompleter(items, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(completer)
        self.clear()

    def clear(self):
        """Clears the current selection."""
        self.setCurrentIndex(-1)
        
class SCMenu(QComboBox):
    """A menu of Starcraft units."""
    
    def __init__(self, items: list[str], width: int):
        super().__init__()
        
        self.addItems(items)
        self.setEditable(True)
        self.setMinimumWidth(width)
        completer = QCompleter(items, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.setCompleter(completer)
        
class FileDialog(QFileDialog):
    """A file dialog for opening and saving files."""
    
    def __init__(self, parent: QWidget, title: str, path: str, file_type: str):
        super().__init__(parent, title, path, file_type)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        
class DialogButton(QPushButton):
    """A push button with a tooltip and disabled focusing."""
    
    def __init__(self, text: str, tooltip: str):
        super().__init__(text)
        self.setToolTip(tooltip)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        
class NamedSpinBox(QSpinBox):
    """A spin box with an object name."""
    
    def __init__(self, name: str, minimum: int):
        super().__init__()
        
        self.setObjectName(name)
        self.setMinimum(minimum)