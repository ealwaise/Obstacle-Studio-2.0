import json
from PyQt6.QtWidgets import (QMainWindow,
                             QPushButton,
                             QVBoxLayout,
                             QFrame,
                             QScrollArea)
from PyQt6.QtGui import QKeySequence
from PyQt6.QtCore import pyqtSignal
from ui_location import LocationLimitPopup
from ui_location_layer import LocationLayerDialog
from ui_explosion import ExplosionMenuDialog
from ui import MainUIframe
from ui_trigger import TriggerGeneratorWindow
from ui_brush import BrushEditor
from ui_audio import AudioMappingDialog
from ui_shared import FileDialog
from graphics import Location
from view import Canvas, Display
from obstacle import Obstacle
import read_write

class MainWindow(QMainWindow):
    """The main application window."""
    save_path = read_write.get_path("Save")
    
    add_loc = pyqtSignal(Location)
    delete_loc = pyqtSignal(int)
    
    loc_layers_action_state = pyqtSignal(bool)
    show_loc_layers = pyqtSignal(bool)
    loc_layers_movable = pyqtSignal(bool)
    
    explosion_menu_state = pyqtSignal(bool)
    hide_explosion_menu = pyqtSignal(bool)
    
    hide_brush_editor = pyqtSignal()
    hide_audio_mapping_dialog = pyqtSignal()

    popup = pyqtSignal(bool)
    
    reset = pyqtSignal()
    get_save_data = pyqtSignal(dict)
    load = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Obstacle Studio")
        self.ob = Obstacle()
        self.editor_state = {"mode": "Terrain", "tool": "Place", "event": "Explosion"}
        self.current_file_path = None
        
        canvas = Canvas(0, 0, 8192, 8192, self.ob)
        main_display = Display(canvas)
        main_display.show()
        main_UI = MainUIframe(self.ob.delays, canvas.locations)

        trigger_generator_window = TriggerGeneratorWindow(canvas.locations, self.ob, self)
        trigger_generator_button = QPushButton("Trigger generator")
        trigger_generator_button.clicked.connect(trigger_generator_window.showMaximized)
        
        
        layout = QVBoxLayout()
        layout.addWidget(main_display)
        layout.addWidget(main_UI)
        layout.addWidget(trigger_generator_button)
        editor = QFrame()
        editor.setLayout(layout)
        self.setCentralWidget(editor)
        
        # editor.setObjectName("editor")
        # editor.setStyleSheet('QFrame#editor {background-color: rgb(25, 25, 25)}')
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        location_layer_dialog = LocationLayerDialog(scroll, canvas.locations, self)
        
        location_limit_popup = LocationLimitPopup(self)
        explosion_menu_dialog = ExplosionMenuDialog(self)
        
        brush_editor = BrushEditor(self)
        audio_mapping_dialog = AudioMappingDialog(self.ob, self)
 
        menu = self.menuBar()
        
        file_menu = menu.addMenu("&File")
        new_file_action = file_menu.addAction("New", QKeySequence("Ctrl+N"))
        new_file_action.triggered.connect(self.new_file)
        open_file_action = file_menu.addAction("Open", QKeySequence("Ctrl+O"))
        open_file_action.triggered.connect(self.open_file)
        save_file_action = file_menu.addAction("Save", QKeySequence("Ctrl+S"))
        save_file_action.triggered.connect(self.save_file)
        save_as_file_action = file_menu.addAction("Save as", QKeySequence("Ctrl+Shift+S"))
        save_as_file_action.triggered.connect(self.save_as_file)
        
        dialogs_menu = menu.addMenu("&Dialogs")
        
        loc_layers_action = dialogs_menu.addAction("Location layers", QKeySequence("Ctrl+L"))
        loc_layers_action.setCheckable(True)
        loc_layers_action.setEnabled(False)
        loc_layers_action.triggered.connect(self.show_loc_layers)
        self.loc_layers_action_state.connect(loc_layers_action.setEnabled)
        self.show_loc_layers.connect(loc_layers_action.setChecked)
        
        explosion_menu_action = dialogs_menu.addAction("Explosion menu",
                                                       QKeySequence("Ctrl+E"))
        explosion_menu_action.setCheckable(True)
        explosion_menu_action.setEnabled(False)
        explosion_menu_action.triggered.connect(explosion_menu_dialog.show)
        self.explosion_menu_state.connect(explosion_menu_action.setEnabled)
        explosion_menu_dialog.closed.connect(explosion_menu_action.setChecked)
        main_UI.open_explosion_menu.connect(explosion_menu_action.setChecked)
        self.hide_explosion_menu.connect(explosion_menu_dialog.hide)
        self.hide_explosion_menu.connect(explosion_menu_action.setChecked)
        
        settings_menu = menu.addMenu("&Settings")
        
        help_menu = menu.addMenu("&Help")
        manual = help_menu.addAction("User manual", QKeySequence("Ctrl+M"))
        about = help_menu.addAction("About", QKeySequence("Ctrl+A"))

        canvas.max_locs.connect(location_limit_popup.open)
        location_limit_popup.popup.connect(editor.setEnabled)
        location_limit_popup.popup.connect(self.popup)

        explosion_menu_dialog.explosions_selected.connect(main_UI.explosions_selected)
        main_UI.open_explosion_menu.connect(explosion_menu_dialog.show)
        
        main_UI.switch_mode.connect(canvas.set_mode)
        main_UI.switch_mode.connect(self.mode_signal)
        main_UI.set_grid_size.connect(canvas.set_grid_size)
        
        main_UI.set_width.connect(canvas.set_brush_width)
        main_UI.set_height.connect(canvas.set_brush_height)
        main_UI.set_tile.connect(canvas.set_terrain_tile)
        main_UI.set_tile.emit(1) # CHANGE 1 TO DEFAULT TILE NUM STORED IN SETTINGS
        main_UI.remove_terrain.connect(canvas.remove_all_terrain)
        
        main_UI.set_loc_tool.connect(self.tool_signal)
        main_UI.set_loc_tool.connect(canvas.set_loc_tool)
        main_UI.set_ID_offset.connect(Location.set_ID_offset)
        main_UI.set_ID_offset.connect(canvas.update_locs)
        main_UI.set_loc_prefix.connect(Location.set_prefix)
        main_UI.set_loc_prefix.connect(canvas.update_locs)
        main_UI.set_loc_numbering.connect(Location.set_numbering_convention)
        main_UI.set_loc_numbering.connect(canvas.update_locs)
        main_UI.delete_locs.connect(canvas.delete_all_locations)
        canvas.add_loc.connect(self.add_loc)
        canvas.delete_loc.connect(self.delete_loc)
        
        self.show_loc_layers.connect(location_layer_dialog.dock)
        main_UI.set_ID_offset.connect(location_layer_dialog.update_locs)
        main_UI.set_loc_numbering.connect(location_layer_dialog.update_locs)
        main_UI.set_loc_prefix.connect(location_layer_dialog.update_locs)
        canvas.add_loc.connect(location_layer_dialog.add_loc)
        canvas.delete_loc.connect(location_layer_dialog.delete_loc)
        self.loc_layers_movable.connect(location_layer_dialog.loc_layers_movable)
        self.popup.connect(location_layer_dialog.setEnabled)
        location_layer_dialog.closed.connect(self.show_loc_layers)
        
        main_UI.switch_event.connect(canvas.set_event_type)
        main_UI.switch_event.connect(self.event_signal)
        main_UI.switch_placement.connect(canvas.set_placement_type)
        main_UI.switch_placement.connect(self.placement_signal)
        
        main_UI.change_count.connect(canvas.set_count)
        main_UI.set_timing_type.connect(self.ob.set_timing_type)
        main_UI.delete_count.connect(canvas.delete_count)
        main_UI.insert_count.connect(canvas.insert_count)
        
        main_UI.explosion_palette_selection.connect(canvas.set_explosion_selection)
        main_UI.explosion_player.connect(canvas.set_explosion_player)
        
        main_UI.open_brush_editor.connect(brush_editor.show)
        brush_editor.send_brush.connect(main_UI.send_brush)
        main_UI.send_shape.connect(canvas.set_brush_shape)
        self.hide_brush_editor.connect(brush_editor.hide)
        
        main_UI.open_audio_dialog.connect(audio_mapping_dialog.show)
        canvas.add_explosion.connect(audio_mapping_dialog.add_explosion)
        canvas.del_explosion.connect(audio_mapping_dialog.delete_explosion)
        self.hide_audio_mapping_dialog.connect(audio_mapping_dialog.hide)
        
        main_UI.wall_unit.connect(canvas.set_wall_unit)
        main_UI.wall_player.connect(canvas.set_wall_player)
        main_UI.wall_option.connect(canvas.set_wall_option)
        
        main_UI.teleport_player.connect(canvas.set_teleport_player)
        main_UI.teleport_marker.connect(canvas.set_teleport_marker)
        main_UI.teleport_cell.connect(canvas.set_teleport_placement)
        canvas.add_tele.connect(main_UI.add_teleport)
        canvas.delete_loc.connect(main_UI.delete_loc)
        canvas.delete_tele.connect(main_UI.delete_teleport)
        
        self.reset.connect(canvas.reset)
        self.reset.connect(self.ob.reset)
        self.reset.connect(main_UI.reset)
        self.reset.connect(location_layer_dialog.reset)
        self.reset.connect(audio_mapping_dialog.reset)
        self.reset.connect(trigger_generator_window.reset)
        self.get_save_data.connect(canvas.save)
        self.get_save_data.connect(location_layer_dialog.save)
        self.get_save_data.connect(main_UI.save)
        self.get_save_data.connect(trigger_generator_window.save)
        self.load.connect(self.ob.load)
        self.load.connect(canvas.load)
        self.load.connect(location_layer_dialog.load)
        self.load.connect(main_UI.load)
        self.load.connect(trigger_generator_window.load)

    def mode_signal(self, mode: str) -> None:
        """Sends signals when the editor mode is changed."""
        # Used to enable/disable certain dialogs.
        self.editor_state["mode"] = mode
        if mode == "Terrain":
            self.loc_layers_action_state.emit(False)
            self.show_loc_layers.emit(False)
            self.loc_layers_movable.emit(False)
            self.hide_brush_editor.emit()
            self.hide_audio_mapping_dialog.emit()
        else:
            self.loc_layers_action_state.emit(True)
            self.loc_layers_movable.emit(self.editor_state["tool"] == "Adjust")
            self.hide_brush_editor.emit()
            self.hide_audio_mapping_dialog.emit()
        
        if mode == "Obstacle":
            self.explosion_menu_state.emit(self.editor_state["event"] == "Explosion")
        else:
            self.explosion_menu_state.emit(False)
            self.hide_explosion_menu.emit(False)
                
    def tool_signal(self, tool: str) -> None:
        """Sends a signal when the editor tool is changed."""
        # Used to make location layers unmovable when using the place tool.
        self.editor_state["tool"] = tool
        if tool == "Place":
            self.loc_layers_movable.emit(False)
        else:
            self.loc_layers_movable.emit(True)
            
    def event_signal(self, event: str) -> None:
        """Sends a signal when the editor event type is changed."""
        # Used to enable/disable the explosion menu.
        self.editor_state["event"] = event
        if event == "Explosion":
            self.explosion_menu_state.emit(True)
        else:
            self.explosion_menu_state.emit(False)
            self.hide_explosion_menu.emit(False)
            self.hide_brush_editor.emit()
            self.hide_audio_mapping_dialog.emit()
            
    def placement_signal(self, placement: str) -> None:
        """Sends a signal when the editor placement type is changed."""
        if placement == "Fixed":
            self.hide_brush_editor.emit()
            self.hide_audio_mapping_dialog.emit()

    def new_file(self) -> None:
        """Erases all edited data and creates a new, blank file."""
        self.reset.emit()
        self.current_file_path = None
        self.setWindowTitle("Obstacle Studio")
    
    def save_file(self) -> None:
        """Saves the current file."""
        if self.current_file_path:
            self.save_to_path(self.current_file_path)
        else:
            self.save_as_file()
        
    def save_as_file(self) -> None:
        """Opens a dialog to save the current file."""
        path, _ = FileDialog.getSaveFileName(self,
                                              "Save obstacle",
                                              MainWindow.save_path,
                                              "JSON files (*.json)")
        if not path:
            return
        self.save_to_path(path)
        
    def save_to_path(self, path: str) -> None:
        """Serializes the obstacle in a JSON file located at the input path."""
        writes = {}
        self.get_save_data.emit(writes)
        writes["Obstacle"] = self.ob.serialize()
        file = open(path, 'w')
        file.write(json.dumps(writes, indent=4))
        file.close()
        self.setWindowTitle("Obstacle Studio - {}".format(path))
        self.current_file_path = path
        
    def open_file(self) -> None:
        """Opens a dialog to load a saved file."""
        path, _ = FileDialog.getOpenFileName(self, "Open obstacle", MainWindow.save_path, "JSON files (*.json)")
        if not path:
            return
        self.open_from_path(path)
        
    def open_from_path(self, path: str) -> None:
        """Opens a file at the input path and deserializes the obstacle encoded in the file."""
        self.new_file()
        with open(path, 'r') as file:
            data = json.load(file)
        self.load.emit(data)
        file.close()
        self.setWindowTitle("Obstacle Studio - {}".format(path))
        self.current_file_path = path