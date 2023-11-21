from PyQt6.QtWidgets import (QWidget,
                             QButtonGroup,
                             QRadioButton,
                             QLabel,
                             QHBoxLayout,
                             QVBoxLayout,
                             QFrame,
                             QComboBox,
                             QStackedWidget)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import Qt, pyqtSignal
from graphics import Location
from ui_terrain import TerrainUIframe
from ui_location import LocationUIframe
from ui_obstacle import ObstacleUIframe
        
class GridSizeFrame(QFrame):
    """Containins a menu to adjust the grid size."""
    set_grid_size = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        
        size_menu = QComboBox()
        for item in ["Normal (32px)", "Fine (16px)", "Ultra Fine (8px)"]:
            size_menu.addItem(item)
        size_menu.setCurrentIndex(0)
        
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Grid size: "))
        layout.addWidget(size_menu)
        self.setLayout(layout)
        
        size_menu.currentIndexChanged.connect(self.set_grid_size)
        
class ModeButton(QRadioButton):
    """A radio button which changes the editor mode when clicked."""
    switch_mode = pyqtSignal(str)
    
    def __init__(self, mode: str, tooltip: str, shortcut: QKeySequence):
        super().__init__(mode)
        if mode == "Terrain":
            self.setChecked(True)
        self.setToolTip("{}\nShortcut: {}".format(tooltip, shortcut.toString()))
        self.setShortcut(shortcut)
        self.clicked.connect(self.emit)
        
    def emit(self):
        """Emits a signal when the button is clicked."""
        self.switch_mode.emit(self.text())
        
class ModeFrame(QFrame):
    """Contains radio buttons used to change between tne three editing modes."""
    switch_mode = pyqtSignal(str)

    def __init__(self):
        super().__init__()
  
        terrain_button = ModeButton("Terrain",
                                    "Edit terrain",
                                    QKeySequence("Shift+T"))
        location_button = ModeButton("Location",
                                    "Edit locations",
                                    QKeySequence("Shift+L"))
        obstacle_button = ModeButton("Obstacle",
                                    "Edit the obstacle",
                                    QKeySequence("Shift+O"))

        group = QButtonGroup()
        group.addButton(terrain_button)
        group.addButton(location_button)
        group.addButton(obstacle_button)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mode:"), alignment=Qt.AlignmentFlag.AlignLeft)
        for button in group.buttons():
            layout.addWidget(button, alignment=Qt.AlignmentFlag.AlignLeft)
            button.switch_mode.connect(self.switch_mode)
        self.setLayout(layout)

class UIstackedWidget(QStackedWidget):
    """A stack of UIs, one for each editing mode."""
    
    def __init__(self):
        super().__init__()
    
    def add_widget(self, widget: QWidget) -> None:
        """Adds the input widget to the stack."""
        # Encases the input widget in a frame for alignment purposes.
        layout = QHBoxLayout()
        layout.addWidget(widget,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        frame = QFrame()
        frame.setLayout(layout)
        super().addWidget(frame)
        
    def current_UI(self) -> QWidget:
        """Returns the currently displayed UI widget."""
        return self.currentWidget().layout().itemAt(0).widget()
    
    def switch_mode(self, mode: str) -> None:
        """Displays the UI widget corresponding to the input mode."""
        if mode == "Terrain":
            self.setCurrentIndex(0)
        elif mode == "Location":
            self.setCurrentIndex(1)
        else:
            self.setCurrentIndex(2)
        current_UI = self.current_UI()
        current_UI.set_shortcuts.emit()

class MainUIframe(QFrame):
    """Containins the UI widgets for all three editing modes."""
    switch_mode = pyqtSignal(str)
    set_grid_size = pyqtSignal(int)
    
    set_width = pyqtSignal(float, str)
    set_height = pyqtSignal(float, str)
    set_tile = pyqtSignal(int)
    remove_terrain = pyqtSignal(bool)
    
    set_loc_tool = pyqtSignal(str)
    set_ID_offset = pyqtSignal(int)
    set_loc_prefix = pyqtSignal(str)
    set_loc_numbering = pyqtSignal(int)
    delete_loc = pyqtSignal(int)
    delete_locs = pyqtSignal(bool)
    
    switch_event = pyqtSignal(str)
    switch_placement = pyqtSignal(str)
    set_timing_type = pyqtSignal(bool)
    change_count = pyqtSignal(int)
    delete_count = pyqtSignal(int)
    insert_count = pyqtSignal(int)
    
    open_explosion_menu = pyqtSignal(bool)
    explosions_selected = pyqtSignal(list)
    explosion_palette_selection = pyqtSignal(list)
    explosion_player = pyqtSignal(int)
    
    open_brush_editor = pyqtSignal()
    send_shape = pyqtSignal(list)
    send_brush = pyqtSignal(str, list)
    open_audio_dialog = pyqtSignal()
    
    wall_unit = pyqtSignal(str)
    wall_player = pyqtSignal(int)
    wall_option = pyqtSignal(str)

    reset = pyqtSignal()
    save = pyqtSignal(dict)
    load = pyqtSignal(dict)
    
    teleport_player = pyqtSignal(int)
    teleport_marker = pyqtSignal(str)
    teleport_cell = pyqtSignal(int, int)
    add_teleport = pyqtSignal(int, int, str, Location, list)
    delete_teleport = pyqtSignal(int, int)
    
    def __init__(self, delays: list[int], locations: list[Location]):
        super().__init__()
        
        # UIs for each editing mode. We encase them in frames for alignment purposes.
        terrain_UI = TerrainUIframe()
        location_UI = LocationUIframe()
        obstacle_UI = ObstacleUIframe(delays, locations)
        
        stack = UIstackedWidget()
        stack.add_widget(terrain_UI)
        stack.add_widget(location_UI)
        stack.add_widget(obstacle_UI)
        stack.setCurrentIndex(0)
        
        mode_frame = ModeFrame()
        grid_size_frame = GridSizeFrame()
        
        # A frame containing the widgets for switching editing modes and adjusting grid sizes.
        control_frame_layout = QVBoxLayout()
        control_frame_layout.addWidget(
            mode_frame,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        control_frame_layout.addWidget(
            grid_size_frame,
            alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
        )
        control_frame = QFrame()
        control_frame.setLayout(control_frame_layout)
        
        layout = QHBoxLayout()
        layout.addWidget(control_frame,
                         alignment=Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(stack, alignment=Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        mode_frame.switch_mode.connect(self.switch_mode)
        mode_frame.switch_mode.connect(stack.switch_mode)
        grid_size_frame.set_grid_size.connect(self.set_grid_size)
        
        terrain_UI.set_width.connect(self.set_width)
        terrain_UI.set_height.connect(self.set_height)
        terrain_UI.set_tile.connect(self.set_tile)
        terrain_UI.remove_terrain.connect(self.remove_terrain)
        
        location_UI.set_loc_tool.connect(self.set_loc_tool)
        location_UI.set_width.connect(self.set_width)
        location_UI.set_height.connect(self.set_height)
        location_UI.set_ID_offset.connect(self.set_ID_offset)
        location_UI.set_loc_prefix.connect(self.set_loc_prefix)
        location_UI.set_loc_numbering.connect(self.set_loc_numbering)
        location_UI.delete_locs.connect(self.delete_locs)
        
        obstacle_UI.switch_event.connect(self.switch_event)
        obstacle_UI.switch_placement.connect(self.switch_placement)
        obstacle_UI.set_timing_type.connect(self.set_timing_type)
        obstacle_UI.change_count.connect(self.change_count)
        obstacle_UI.delete_count.connect(self.delete_count)
        obstacle_UI.insert_count.connect(self.insert_count)
        
        obstacle_UI.open_explosion_menu.connect(self.open_explosion_menu)
        obstacle_UI.explosion_palette_selection.connect(self.explosion_palette_selection)
        obstacle_UI.explosion_player.connect(self.explosion_player)
        self.explosions_selected.connect(obstacle_UI.explosions_selected)
        
        obstacle_UI.open_brush_editor.connect(self.open_brush_editor)
        self.send_brush.connect(obstacle_UI.send_brush)
        obstacle_UI.send_shape.connect(self.send_shape)
        obstacle_UI.open_audio_dialog.connect(self.open_audio_dialog)
        
        obstacle_UI.wall_unit.connect(self.wall_unit)
        obstacle_UI.wall_player.connect(self.wall_player)
        obstacle_UI.wall_option.connect(self.wall_option)
        
        obstacle_UI.teleport_player.connect(self.teleport_player)
        obstacle_UI.teleport_marker.connect(self.teleport_marker)
        obstacle_UI.teleport_cell.connect(self.teleport_cell)
        self.add_teleport.connect(obstacle_UI.add_teleport)
        location_UI.set_loc_prefix.connect(obstacle_UI.update_locs)
        location_UI.set_loc_numbering.connect(obstacle_UI.update_locs)
        self.delete_loc.connect(obstacle_UI.delete_loc)
        self.delete_teleport.connect(obstacle_UI.delete_teleport)

        self.reset.connect(location_UI.reset)
        self.reset.connect(obstacle_UI.reset)
        self.save.connect(location_UI.save)
        self.save.connect(obstacle_UI.save)
        self.load.connect(location_UI.load)
        self.load.connect(obstacle_UI.load)