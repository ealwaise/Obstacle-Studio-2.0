import os
from PyQt6.QtWidgets import (QFrame,
                             QLabel,
                             QHBoxLayout,
                             QVBoxLayout,
                             QGridLayout,
                             QPushButton,
                             QListWidget,
                             QListWidgetItem,
                             QAbstractItemView,
                             QDialog,
                             QFileDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from ui_shared import IconButton, PlayerMenu, EventMenu
import sc_data
import read_write

class ExplosionMenuDialog(QDialog):
    """Contains an organized collection of explosion menus."""
    data = sc_data.event_data[sc_data.event_data["Explosion Image"].notna()]
    
    explosions_selected = pyqtSignal(list)
    closed = pyqtSignal(bool)
    
    def __init__(self, parent):
        super().__init__(parent)
        
        self.setWindowTitle("Explosion menu")
        clear_button = QPushButton("Clear")
        clear_button.setToolTip("Clear all selected explosions.")
        clear_button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        layout = QGridLayout()

        # We organize the list of explosion options into various lists sorted by whether the
        # explosion is a unit or a sprite, the type of unit, whether or not the sprite crashes
        # Starcraft, etc. This is mostly to keep the menu size manageable.
        row = self.num_rows(sorted(self.data["Type"].unique())[0]) + 1
        total_rows = len(self.data["Type"].unique())
        image_path = read_write.get_path("Explosion")
        
        for i, main_type in enumerate(sorted(self.data["Type"].unique())):
            layout.addWidget(QLabel("{}: ".format(main_type)),
                             row*i,
                             0)
            data_fixed_type = self.data[self.data["Type"] == main_type]
            subtypes = sorted(data_fixed_type["Subtype"].unique())
            total_rows += self.num_rows(main_type)
            
            for j, subtype in enumerate(subtypes):
                layout.addWidget(QLabel("{}:".format(subtype)),
                                 row*i,
                                 2*j + 1)
                data_fixed_subtype = data_fixed_type[data_fixed_type["Subtype"] == subtype]
                subsubtypes = sorted(data_fixed_subtype["Subsubtype"].unique())
                
                for k, subsubtype in enumerate(subsubtypes):
                    empty_rows = (self.num_rows(main_type)
                                  - self.num_subsubtypes(main_type, subtype))
                    layout.addWidget(QLabel("{}:".format(subsubtype)),
                                     row*i + k + 1 + empty_rows,
                                     2*j + 1)
                    data_fixed_subsubtype = data_fixed_subtype[
                        data_fixed_subtype["Subsubtype"] == subsubtype
                        ].sort_values("Name")
                    items = data_fixed_subsubtype["Name"].tolist()
                    explosion_IDs = data_fixed_subsubtype["Explosion Image"].tolist()
                    # Create the explosion icons.
                    icons = []
                    for explosion_ID in explosion_IDs:
                        path = os.path.join(image_path, str(int(explosion_ID)))
                        path = os.path.join(path, "static.png")
                        icon = QIcon(path)
                        icons.append(icon)
                        
                    menu = EventMenu(icons, items, 275)
                    clear_button.clicked.connect(menu.clear)
                    layout.addWidget(menu,
                                     row*i + k + 1 + empty_rows,
                                     2*j + 2)
        
        icons_path = read_write.get_path("Icons")
        add_icon = QIcon(os.path.join(icons_path, "add.png"))
        add_tooltip = "Add all selected explosions to the palette."
        add_button = IconButton(add_icon, 32, 36, add_tooltip, False)

        layout.addWidget(add_button, total_rows, 0)
        layout.addWidget(clear_button, total_rows, 1)
        self.setLayout(layout)
        
        add_button.clicked.connect(self.get_selection)
        
    def closeEvent(self, event: QEvent) -> None:
        """Sends a signal when the window is closed."""
        self.closed.emit(False)
        event.accept()

    def num_subsubtypes(self, main_type: str, subtype: str) -> None:
        """Returns the number of unique subsubtypes appearing in rows of the data with the input type
        and subtype.
        """
        # Used to organize the layout.
        data_fixed_type = self.data[(self.data["Type"] == main_type)
                                    & (self.data["Subtype"] == subtype)]
        return len(data_fixed_type["Subsubtype"].unique())
        
    def num_rows(self, main_type: str) -> None:
        """Returns the maximum number of unique subsubtypes among all subtypes appearing in rows of
        the data with the input type.
        """
        # Used to organize the layout.
        data_fixed_type = self.data[self.data["Type"] == main_type]
        rows = 0
        for subtype in data_fixed_type["Subtype"].unique():
            rows = max(rows, self.num_subsubtypes(main_type, subtype))
        return rows
        
    def get_selection(self) -> None:
        """Emits a list of all currently selected explosions as a signal."""
        explosions = []
        for widget in self.children():
            if type(widget) != EventMenu:
                continue
            explosion = widget.currentText()
            if explosion in self.data["Name"].values:
                explosions.append(explosion)
        self.explosions_selected.emit(explosions)
                
class ExplosionPalette(QListWidget):
    """An editable list of explosions to place in an obstacle."""
    data = sc_data.event_data[sc_data.event_data["Explosion Image"].notna()]

    explosion_palette_selection = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.setMinimumWidth(275)
        self.model().rowsInserted.connect(self.get_items)
        self.model().rowsRemoved.connect(self.get_items)
        self.itemSelectionChanged.connect(self.emit_selection)

        # Cache explosion icons.
        self.icons = {}
        icons_path = read_write.get_path("Explosion")
        for ID in self.data.index:
            explosion_image = self.data.loc[ID]["Explosion Image"]
            image_path = os.path.join(icons_path, str(int(explosion_image)))
            image_path = os.path.join(image_path, "static.png")
            self.icons[self.data.loc[ID]["Name"]] = QIcon(image_path)
        
    def get_items(self) -> list[str]:
        """Gets the items in the palette."""
        self.parent().items = [self.item(i).text() for i in range(self.count())]
    
    def get_selection(self) -> list[str]:
        """Gets the selected items in the palette."""
        self.parent().explosions_selected.emit([item.text() for item in self.selectedItems()])
        
    def emit_selection(self) -> None:
        """Emits a signal when the selection is changed."""
        selection = [item.text() for item in self.selectedItems()]
        self.explosion_palette_selection.emit(selection)
        
    def get_row(self, item: str) -> None:
        """Returns the row of item if item in the list, otherwise returns -1."""
        match = self.findItems(item, Qt.MatchFlag.MatchExactly)
        return self.row(match[0]) if match else -1
        
    def add_item(self, explosion: str) -> None:
        """Adds an item to the palette if it is not currently in the list."""
        item = QListWidgetItem(self.icons[explosion], explosion)
        if self.get_row(explosion) == -1:
            self.addItem(item)

    def remove_selected_items(self) -> None:
        """Removes all selected items from the palette."""
        for item in self.selectedItems():
            self.takeItem(self.row(item))
                
class ExplosionPaletteFrame(QFrame):
    """Contains widgets for editing an explosion palette."""
    remove = pyqtSignal()
    clear_palette = pyqtSignal()
    load = pyqtSignal(str)
    open_menu = pyqtSignal(bool)
    explosion_palette_selection = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.items = []
        self.selection = []
        self.save_path = read_write.get_path("Palette")
        
        explosion_palette = ExplosionPalette()
        icons_path = read_write.get_path("Icons")
        open_menu_button = IconButton(QIcon(os.path.join(icons_path, "open_menu.png")),
                                      32,
                                      36,
                                      "Open the explosion menu.",
                                      False)
        remove_button = IconButton(QIcon(os.path.join(icons_path, "remove.png")),
                                   32,
                                   36,
                                   "Remove all selected explosions from the palette.",
                                   False)
        save_button = IconButton(QIcon(os.path.join(icons_path, "save.png")),
                                 32,
                                 36,
                                 "Save the current palette.",
                                 False)
        load_button = IconButton(QIcon(os.path.join(icons_path, "load.png")),
                                 32,
                                 36,
                                 "Load a saved palette.",
                                 False)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(open_menu_button)
        button_layout.addWidget(remove_button)
        button_layout.addWidget(save_button)
        button_layout.addWidget(load_button)
        button_frame = QFrame()
        button_frame.setLayout(button_layout)
        
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Explosion palette:"), alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(explosion_palette, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(button_frame, alignment=Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        self.load.connect(explosion_palette.add_item)
        self.clear_palette.connect(explosion_palette.clear)
        open_menu_button.clicked.connect(self.open_menu)
        remove_button.clicked.connect(explosion_palette.remove_selected_items)
        save_button.clicked.connect(self.save_palette)
        load_button.clicked.connect(self.load_palette)
        explosion_palette.explosion_palette_selection.connect(self.explosion_palette_selection)
        
    def save_palette(self) -> None:
        """Saves the current palette."""
        path, _ = QFileDialog.getSaveFileName(self,
                                              "Save palette",
                                              self.save_path,
                                              "Text files (*.txt)")
        if not path:
            return
        file = open(path, 'w')
        file.write('\n'.join(self.items))
        file.close()
        
    def load_palette(self) -> None:
        """Loads a saved palette."""
        path, _ = QFileDialog.getOpenFileName(self,
                                              "Open palette",
                                              self.save_path,
                                              "Textfiles (*.txt)")
        if not path:
            return
        self.clear_palette.emit()
        file = open(path, 'r')
        for line in file.readlines():
            self.load.emit(line.rstrip())
        file.close()
        
    def add_to_palette(self, items: list[str]) -> None:
        """Adds all explosions in items to the palette."""
        for item in items:
            self.load.emit(item)
            
    def remove(self) -> None:
        """Removes all selected explosions from the palette."""
        self.remove.emit()
        
class ExplosionUIframe(QFrame):
    """Contains widgets for editing explosions."""
    set_shortcuts = pyqtSignal()
    open_menu = pyqtSignal(bool)
    explosions_selected = pyqtSignal(list)
    explosion_palette_selection = pyqtSignal(list)
    explosion_player = pyqtSignal(int)
    open_audio_dialog = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        
        explosion_palette = ExplosionPaletteFrame()
        player_menu = PlayerMenu("The selected player will own the explosion units.", True)
        player_menu.setCurrentIndex(read_write.read_setting("Explosion player"))
        player_menu.currentIndexChanged.connect(self.explosion_player)
        player_menu.currentIndexChanged.connect(self.save_explosion_player)
        audio_dialog_button = QPushButton("Audio")
        audio_dialog_button.setToolTip("Edit explosion audio.")
        
        frame_layout = QGridLayout()
        frame_layout.addWidget(explosion_palette, 0, 0, 4, 2, alignment=Qt.AlignmentFlag.AlignTop)
        frame_layout.addWidget(QLabel("Player: "), 4, 0)
        frame_layout.addWidget(player_menu, 4, 1)
        frame_layout.addWidget(audio_dialog_button, 0, 2)
        frame = QFrame()
        frame.setLayout(frame_layout)
        
        layout = QHBoxLayout()
        layout.addWidget(frame, alignment=Qt.AlignmentFlag.AlignTop)
        self.setLayout(layout)
        
        explosion_palette.open_menu.connect(self.open_menu)
        explosion_palette.explosion_palette_selection.connect(self.explosion_palette_selection)
        self.explosions_selected.connect(explosion_palette.add_to_palette)
        audio_dialog_button.clicked.connect(self.open_audio_dialog)
        
    def save_explosion_player(self, player: int) -> None:
        """When the explosion player is changed, saves the setting to settings.json."""
        read_write.write_setting("Explosion player", player)