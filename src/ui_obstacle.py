import math
from PyQt6.QtWidgets import (QWidget,
                             QButtonGroup,
                             QRadioButton,
                             QSpinBox,
                             QPushButton,
                             QLabel,
                             QGridLayout,
                             QHBoxLayout,
                             QVBoxLayout,
                             QFrame,
                             QLCDNumber,
                             QStackedWidget)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from .graphics import Location
from .ui_explosion import ExplosionUIframe
from .ui_wall import WallUIframe
from .ui_teleport import TeleportUIFrame
from .ui_shared import FixedWidthButton
from .ui_brush import BrushUI
from src import read_write

class EventButton(QRadioButton):
    """A radio button used to select the type of obstacle events to edit."""
    switch_event = pyqtSignal(str)
    
    def __init__(self, event: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(event)

        self.shortcut = shortcut
        
        if event == "Explosion":
            self.setChecked(True)
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        self.clicked.connect(self.emit)
        
    def emit(self):
        """Emits a signal when the button is clicked."""
        self.switch_event.emit(self.text())
        
    def set_shortcut(self):
        """Sets the button's shortcut."""
        self.setShortcut(self.shortcut)

class EventFrame(QFrame):
    """Contains radio buttons to select the type of obstacle events to edit."""
    switch_event = pyqtSignal(str)
    set_shortcuts = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        explosion_button = EventButton("Explosion",
                                       "Edit explosions.",
                                       QKeySequence("E"))
        wall_button = EventButton("Wall",
                                  "Edit walls.",
                                  QKeySequence("W"))
        teleport_button = EventButton("Teleport",
                                      "Edit teleports.",
                                      QKeySequence("T"))
                                      
        buttons = QButtonGroup()
        buttons.addButton(explosion_button)
        buttons.addButton(wall_button)
        buttons.addButton(teleport_button)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Event type:"), alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(explosion_button)
        layout.addWidget(wall_button)
        layout.addWidget(teleport_button)
        self.setLayout(layout)
        
        self.set_shortcuts.connect(explosion_button.set_shortcut)
        self.set_shortcuts.connect(wall_button.set_shortcut)
        self.set_shortcuts.connect(teleport_button.set_shortcut)
        
        explosion_button.switch_event.connect(self.switch_event)
        wall_button.switch_event.connect(self.switch_event)
        teleport_button.switch_event.connect(self.switch_event)
        
class EventUIstackedWidget(QStackedWidget):
    """A stack of UIs, one for each event type."""
    
    def __init__(self):
        super().__init__()
    
    def add_widget(self, widget: QWidget) -> None:
        """Adds the input widget to the stack."""
        # Encases the input widget in a frame for alignment purposes.
        layout = QHBoxLayout()
        layout.addWidget(widget, alignment=Qt.AlignmentFlag.AlignTop)
        frame = QFrame()
        frame.setLayout(layout)
        super().addWidget(frame)
        
    def current_UI(self) -> QWidget:
        """Returns the currently displayed UI widget."""
        return self.currentWidget().layout().itemAt(0).widget()
    
    def switch_event(self, event: str) -> None:
        """Displays the UI widget corresponding to the input event type."""
        if event == "Explosion":
            self.setCurrentIndex(0)
        elif event == "Wall":
            self.setCurrentIndex(1)
        else:
            self.setCurrentIndex(2)
        current_UI = self.current_UI()
        current_UI.set_shortcuts.emit()
        
class PlacementButton(QRadioButton):
    """A radio button used to select the type of placement."""
    switch_placement = pyqtSignal(str)
    
    def __init__(self, placement_type: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(placement_type)

        self.shortcut = shortcut
        
        if placement_type == "Fixed":
            self.setChecked(True)
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        self.clicked.connect(self.emit)
        
    def emit(self):
        """Emits a signal when the button is clicked."""
        self.switch_placement.emit(self.text())
        
    def set_shortcut(self):
        """Sets the button's shortcut."""
        self.setShortcut(self.shortcut)

class PlacementFrame(QFrame):
    """Contains radio buttons to select the placement type."""
    switch_placement = pyqtSignal(str)
    set_shortcuts = pyqtSignal()
    set_fixed_state = pyqtSignal(bool)
    set_mobile_state = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        fixed_placement_button = PlacementButton("Fixed",
                                                 "Place events directly on locations.",
                                                 QKeySequence("F"))
        mobile_placement_button = PlacementButton("Mobile",
                                                  "Place events anywhere relative to locations.",
                                                  QKeySequence("M"))

        buttons = QButtonGroup()
        buttons.addButton(fixed_placement_button)
        buttons.addButton(mobile_placement_button)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Placement type:"), alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(fixed_placement_button)
        layout.addWidget(mobile_placement_button)
        self.setLayout(layout)
        
        self.set_shortcuts.connect(fixed_placement_button.set_shortcut)
        self.set_shortcuts.connect(mobile_placement_button.set_shortcut)
        
        fixed_placement_button.switch_placement.connect(self.switch_placement)
        mobile_placement_button.switch_placement.connect(self.switch_placement)
        self.set_fixed_state.connect(fixed_placement_button.setChecked)
        self.set_mobile_state.connect(mobile_placement_button.setEnabled)
        
    def switch_event(self, event: str) -> None:
        """Sends signals to disable the mobile placement button when placing teleports and to
        enable it when placing explosions or walls.
        """
        self.set_fixed_state.emit(event == "Teleport")
        self.set_mobile_state.emit(event != "Teleport")
        
class CountNumberBox(QLCDNumber):
    """A box which displays the current count number."""

    def __init__(self):
        super().__init__()

        self.maximum = 1
        self.display(1)
        
    def reset(self):
        """Resets the displayed number to 1."""
        self.display(1)
        
class DelayBox(QSpinBox):
    """A spinbox for editing obstacle delays."""

    def __init__(self, delays: list[int]):
        super().__init__()

        self.use_frames = read_write.read_setting("Use frames")
        self.count = 1
        self.delays = delays
        if self.use_frames:
            self.setMinimum(1)
            self.setMaximum(999999999)
            self.setSingleStep(1)
        else:
            self.setMinimum(0)
            self.setMaximum(999999966)
            self.setSingleStep(42)
            
        self.editingFinished.connect(self.round_value)
        self.valueChanged.connect(self.set_delay)
        
    def set_delay(self, delay: int) -> None:
        """Updates the list of delays when the current delay is changed."""
        self.delays[self.count - 1] = delay
        
    def change_count(self, count: int) -> None:
        """Displays the delay following the input count and updates the list of delays."""
        self.count = count
        if count > len(self.delays):
            self.delays.append(self.value())
        self.setValue(self.delays[count - 1])
        
    def delete_count(self, count: int) -> None:
        """Deletes the input count."""
        new_count = count if count < len(self.delays) else max(1, count - 1)
        if len(self.delays) > 1:
            self.delays.pop(count - 1)
        self.setValue(self.delays[new_count - 1])
        self.count = count
        
    def insert_count(self, count: int) -> None:
        """Inserts a count at the input position."""
        delay = self.delays[count - 1]
        self.delays.insert(count - 1, delay)
        
    def set_timing_type(self, use_frames: bool) -> None:
        """Sets the timing type to frames if use_frames is true and waits otherwise."""
        self.use_frames = use_frames
        if use_frames:
            self.setMinimum(1)
            self.setMaximum(999999999)
            self.setSingleStep(1)
            for i, delay in enumerate(self.delays):
                self.delays[i] = 1 + delay // 42
        else:
            self.setMinimum(0)
            self.setMaximum(999999966)
            self.setSingleStep(42)
            for i, delay in enumerate(self.delays):
                self.delays[i] = 42*(delay - 1)
        self.setValue(self.delays[self.count - 1])
        
    def round_value(self) -> None:
        """Rounds the value to the nearest multiple of 42 when using waits."""
        if not self.use_frames:
            self.setValue(int(math.ceil(self.value() / 42)*42))
            
    def reset(self) -> None:
        """Resets the displayed wait."""
        self.count = 1
        self.setValue(self.delays[0])
        
    def load(self, data: dict) -> None:
        """Sets the box's value to the delay after the first count stored in the saved data."""
        delays = data["Obstacle"]["Delays"]
        while len(self.delays) < len(delays):
            self.delays.append(-1)
        for i, delay in enumerate(delays):
            self.delays[i] = delays[i]
        self.setValue(self.delays[0])

class DelayFrame(QFrame):
    """Contains widgets to edit the delays in an obstacle."""
    use_frames = pyqtSignal(bool)
    change_count = pyqtSignal(int)
    delete_count = pyqtSignal(int)
    insert_count = pyqtSignal(int)
    
    reset = pyqtSignal()
    load = pyqtSignal(dict)
    
    def __init__(self, delays: list[int]):
        super().__init__()
        
        delay_box = DelayBox(delays)
        frames_button = QRadioButton("Frames")
        waits_button = QRadioButton("Wait")
        use_frames = read_write.read_setting("Use frames")
        frames_button.setChecked(use_frames)
        waits_button.setChecked(not use_frames)
        
        timing_buttons = QButtonGroup()
        timing_buttons.addButton(frames_button)
        timing_buttons.addButton(waits_button)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Delay: "), 0, 0)
        layout.addWidget(delay_box, 0, 1)
        layout.addWidget(frames_button, 1, 1)
        layout.addWidget(waits_button, 2, 1)
        self.setLayout(layout)
        
        self.use_frames.connect(frames_button.setChecked)
        frames_button.toggled.connect(self.use_frames)
        frames_button.toggled.connect(self.save_timing_type)
        self.use_frames.connect(delay_box.set_timing_type)
        self.change_count.connect(delay_box.change_count)
        self.delete_count.connect(delay_box.delete_count)
        self.insert_count.connect(delay_box.insert_count)
        
        self.reset.connect(delay_box.reset)
        self.load.connect(delay_box.load)
        
    def save_timing_type(self, use_frames: bool) -> None:
        """When the timing type is changed, saves the setting in settings.json."""
        read_write.write_setting("Use frames", use_frames)
        
    def emit_load(self, data: dict) -> None:
        """Emits a signal to load data and loads the obstacle timing type from saved data."""
        self.use_frames.emit(data["Obstacle"]["Use frames"])
        self.load.emit(data)

class CountChangeButton(QPushButton):
    """A button for navigating through counts of an obstacle."""
    
    def __init__(self, text: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(text)

        self.shortcut = shortcut
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        self.setFixedSize(32, 32)
        
    def set_shortcut(self) -> None:
        """Sets the button's shortcut."""
        self.setShortcut(self.shortcut)
        
class CountControlFrame(QFrame):
    """Contains widgets for browsing throuh counts and adjusting delays in an obstacle."""
    set_shortcuts = pyqtSignal()
    
    set_timing_type = pyqtSignal(bool)
    change_count = pyqtSignal(int)
    delete_count = pyqtSignal(int)
    insert_count = pyqtSignal(int)
    
    reset = pyqtSignal()
    load = pyqtSignal(dict)
    
    def __init__(self, delays: list[int]):
        super().__init__()
        
        self.count = 1
        self.last_count = 1
        
        count_number_box = CountNumberBox()
        first_count_button = CountChangeButton("<<",
                                               "Go to the first count.",
                                               QKeySequence("Shift+["))
        prev_count_button = CountChangeButton("<",
                                              "Go to the previous count.",
                                              QKeySequence("["))
        next_count_button = CountChangeButton(">",
                                              "Go to the next count.",
                                              QKeySequence("]"))
        last_count_button = CountChangeButton(">>",
                                              "Go to the last count.",
                                              QKeySequence("Shift+]"))

        delete_count_button = FixedWidthButton(80,
                                               "Delete",
                                               "Delete the current count.",
                                               QKeySequence("Delete"))
        insert_count_button = FixedWidthButton(80,
                                               "Insert",
                                               "Insert a new count at the current position.",
                                               QKeySequence("Insert"))
        play_button = FixedWidthButton(80,
                                       "Play",
                                       "Animate the obstacle.",
                                       QKeySequence("+"))
        stop_button = FixedWidthButton(80,
                                       "Stop",
                                       "Stop the animation.",
                                       QKeySequence("-"))
        delay_frame = DelayFrame(delays)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Count #:"), 0, 2, 1, 2)
        layout.addWidget(first_count_button, 1, 0, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(prev_count_button, 1, 1, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(count_number_box, 1, 2, 1, 2)
        layout.addWidget(next_count_button, 1, 4, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(last_count_button, 1, 5, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(delete_count_button, 2, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(insert_count_button, 2, 4, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(delay_frame, 2, 2, 3, 2)
        layout.addWidget(play_button, 3, 0, 1, 2)
        layout.addWidget(stop_button, 3, 4, 1, 2)
        self.setLayout(layout)

        self.set_shortcuts.connect(first_count_button.set_shortcut)
        self.set_shortcuts.connect(prev_count_button.set_shortcut)
        self.set_shortcuts.connect(next_count_button.set_shortcut)
        self.set_shortcuts.connect(last_count_button.set_shortcut)
        self.set_shortcuts.connect(delete_count_button.set_shortcut)
        self.set_shortcuts.connect(insert_count_button.set_shortcut)
        self.set_shortcuts.connect(play_button.set_shortcut)
        self.set_shortcuts.connect(stop_button.set_shortcut)
        
        delay_frame.use_frames.connect(self.set_timing_type)
        first_count_button.clicked.connect(self.to_first_count)
        prev_count_button.clicked.connect(self.to_prev_count)
        next_count_button.clicked.connect(self.to_next_count)
        last_count_button.clicked.connect(self.to_last_count)
        delete_count_button.clicked.connect(self.delete_current_count)
        insert_count_button.clicked.connect(self.insert_new_count)
        self.change_count.connect(count_number_box.display)
        self.change_count.connect(delay_frame.change_count)
        self.delete_count.connect(delay_frame.delete_count)
        self.insert_count.connect(delay_frame.insert_count)

        self.reset.connect(delay_frame.reset)
        self.reset.connect(count_number_box.reset)
        self.reset.connect(self.reset_counts)
        self.load.connect(delay_frame.emit_load)

    def to_first_count(self) -> None:
        """Skips to the first count."""
        self.count = 1
        self.change_count.emit(1)
        
    def to_prev_count(self) -> None:
        """Decrements the count by 1."""
        self.count = (self.count - 2) % self.last_count + 1
        self.change_count.emit(self.count)
        
    def to_next_count(self) -> None:
        """Increments the count by 1."""
        self.count += 1
        self.last_count = max(self.last_count, self.count)
        self.change_count.emit(self.count)
        
    def to_last_count(self) -> None:
        """Skips to the last count."""
        self.count = self.last_count
        self.change_count.emit(self.last_count)
        
    def delete_current_count(self) -> None:
        """Deletes the current count."""
        self.delete_count.emit(self.count)
        if self.count == self.last_count:
            self.count = max(1, self.count - 1)
        self.last_count = max(1, self.last_count - 1)
        self.change_count.emit(self.count)
        
    def insert_new_count(self) -> None:
        """Inserts a new count at the current position."""
        self.insert_count.emit(self.count)
        self.last_count += 1
        
    def reset_counts(self) -> None:
        """Sets the first and last counts to 1 when a new file is created."""
        self.count = 1
        self.last_count = 1
        
    def emit_load(self, data: dict) -> None:
        """Lodas the number of counts from saved data and emits a signal to load data."""
        self.last_count = len(data["Obstacle"]["Delays"])
        self.load.emit(data)

class ObstacleUIframe(QFrame):
    """A frame containing all widgets used to edit obstacles."""
    set_shortcuts = pyqtSignal()
    
    switch_event = pyqtSignal(str)
    switch_placement = pyqtSignal(str)
    
    update_locs = pyqtSignal()
    delete_loc = pyqtSignal(int)
    
    change_count = pyqtSignal(int)
    set_delay = pyqtSignal(int, int)
    set_timing_type = pyqtSignal(bool)
    delete_count = pyqtSignal(int)
    insert_count = pyqtSignal(int)
    
    open_explosion_menu = pyqtSignal(bool)
    explosions_selected = pyqtSignal(list)
    explosion_palette_selection = pyqtSignal(list)
    explosion_player = pyqtSignal(int)
    
    open_brush_editor = pyqtSignal()
    send_brush = pyqtSignal(str, list)
    send_shape = pyqtSignal(list)
    open_audio_dialog = pyqtSignal()
    
    wall_unit = pyqtSignal(str)
    wall_player = pyqtSignal(int)
    wall_option = pyqtSignal(str)
    
    teleport_player = pyqtSignal(int)
    teleport_marker = pyqtSignal(str)
    teleport_cell = pyqtSignal(int, int)
    add_teleport = pyqtSignal(int, int,str, Location, list)
    delete_teleport = pyqtSignal(int, int)
    
    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)

    def __init__(self, delays: list[int], locations: list[Location]):
        super().__init__()

        event_frame = EventFrame()
        placement_frame = PlacementFrame()
        explosion_UI = ExplosionUIframe()
        wall_UI = WallUIframe()
        teleport_UI = TeleportUIFrame(locations)
        stack = EventUIstackedWidget()
        stack.add_widget(explosion_UI)
        stack.add_widget(wall_UI)
        stack.add_widget(teleport_UI)
        count_control_frame = CountControlFrame(delays)
        brush_UI = BrushUI()
        
        layout = QGridLayout()
        layout.addWidget(event_frame, 0, 0, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(placement_frame, 0, 1, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(brush_UI, 0, 2, alignment=Qt.AlignmentFlag.AlignBottom)
        layout.addWidget(count_control_frame, 1, 0, 1, 2, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(stack, 0, 3, 2, 1, alignment=Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        self.set_shortcuts.connect(count_control_frame.set_shortcuts)
        self.set_shortcuts.connect(event_frame.set_shortcuts)
        self.set_shortcuts.connect(placement_frame.set_shortcuts)
        
        count_control_frame.change_count.connect(self.change_count)
        count_control_frame.set_timing_type.connect(self.set_timing_type)
        count_control_frame.delete_count.connect(self.delete_count)
        count_control_frame.insert_count.connect(self.insert_count)
        
        event_frame.switch_event.connect(self.switch_event)
        event_frame.switch_event.connect(stack.switch_event)
        event_frame.switch_event.connect(placement_frame.switch_event)
        
        placement_frame.switch_placement.connect(self.switch_placement)
        
        explosion_UI.open_menu.connect(self.open_explosion_menu)
        self.explosions_selected.connect(explosion_UI.explosions_selected)
        explosion_UI.explosion_palette_selection.connect(self.explosion_palette_selection)
        explosion_UI.explosion_player.connect(self.explosion_player)
        
        brush_UI.open_brush_editor.connect(self.open_brush_editor)
        self.send_brush.connect(brush_UI.send_brush)
        brush_UI.send_shape.connect(self.send_shape)
        event_frame.switch_event.connect(brush_UI.switch_event)
        placement_frame.switch_placement.connect(brush_UI.switch_placement)
        explosion_UI.open_audio_dialog.connect(self.open_audio_dialog)
        
        wall_UI.wall_unit.connect(self.wall_unit)
        wall_UI.wall_player.connect(self.wall_player)
        wall_UI.wall_option.connect(self.wall_option)
        
        teleport_UI.teleport_player.connect(self.teleport_player)
        teleport_UI.teleport_marker.connect(self.teleport_marker)
        teleport_UI.teleport_cell.connect(self.teleport_cell)
        self.add_teleport.connect(teleport_UI.add_teleport)
        self.change_count.connect(teleport_UI.change_count)
        self.delete_count.connect(teleport_UI.delete_count)
        self.insert_count.connect(teleport_UI.insert_count)
        self.update_locs.connect(teleport_UI.update_locs)
        self.delete_loc.connect(teleport_UI.delete_loc)
        self.delete_teleport.connect(teleport_UI.delete_teleport)
        
        self.reset.connect(count_control_frame.reset)
        self.reset.connect(teleport_UI.reset)
        self.save.connect(teleport_UI.save)
        self.load.connect(count_control_frame.emit_load)
        self.load.connect(teleport_UI.load)