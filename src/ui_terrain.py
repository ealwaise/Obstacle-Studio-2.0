import os
from PyQt6.QtWidgets import (QButtonGroup,
                             QPushButton,
                             QLabel,
                             QGridLayout,
                             QHBoxLayout,
                             QStackedWidget,
                             QComboBox,
                             QFrame)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from .ui_shared import SizeFrame
from src import sc_data
from src import read_write

class TileButton(QPushButton):
    """A button for selecting a terrain tile."""
    size = 40
    set_tile = pyqtSignal(int)
    
    def __init__(self, num, icon):
        super().__init__()

        self.setIcon(icon)
        self.setIconSize(QSize(32, 32))
        self.setFixedSize(QSize(self.size, self.size))
        self.setCheckable(True)
        self.num = num
        self.clicked.connect(self.pressed)
        
    def pressed(self) -> None:
        """Emits a signal when the button is pressed."""
        self.set_tile.emit(self.num)

class Tileset(QFrame):
    """Contains buttons to select terrain tiles from a particular tileset."""
    row_width = 8
    default_tile_index = 0
    
    set_tile = pyqtSignal(int)

    def __init__(self, tileset_index: int):
        super().__init__()
        layout = QGridLayout()
        
        # Gets the path containing the tile images and the number of tile images.
        path = read_write.get_path(sc_data.tilesets[tileset_index])
        count = len(os.listdir(path))
            
        # Buttons which select the depicted terrain tile.
        for i in range(count):    
            image_path = os.path.join(path, "{}.png".format(i))
            tile_num = (i << 3) + tileset_index
            icon = QIcon(image_path)
            button = TileButton(tile_num, icon)
            layout.addWidget(button,
                             i // self.row_width,
                             i % self.row_width,
                             alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            if (tileset_index == TileSelectionFrame.default_tileset_index
                and i == self.default_tile_index):
                button.setChecked(True)
            button.set_tile.connect(self.set_tile)
            i += 1

        self.setLayout(layout)

class TileSelectionFrame(QFrame):
    """Contains widgets used to select terrain tiles."""
    default_tileset_index = 1
    set_tile = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        # A menu to select the tileset.
        tileset_menu = QComboBox()
        tileset_menu.addItems(sc_data.tilesets)
        tileset_menu.setCurrentIndex(self.default_tileset_index)
        
        # A stacked widget to hold the tile menu for each tileset.
        # Placing the tile buttons in a group prevents simlutaneous selection.
        buttons = QButtonGroup(parent=self)
        stack = QStackedWidget()
        for i, tileset_name in enumerate(sc_data.tilesets):
            tileset = Tileset(i)
            for widget in tileset.children():
                if type(widget) is not TileButton:
                    continue
                buttons.addButton(widget)
            tileset.set_tile.connect(self.set_tile)
            
            # We encase the tile menu in a frame for proper alignment.
            frame = QFrame()
            frame_layout = QHBoxLayout()
            frame_layout.addWidget(
                tileset,
                alignment=Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
            )
            frame.setLayout(frame_layout)
            stack.addWidget(frame)
        stack.setCurrentIndex(self.default_tileset_index)
            
        layout = QGridLayout()
        layout.addWidget(QLabel("Tileset: "), 0, 0)
        layout.addWidget(tileset_menu, 0, 1)
        layout.addWidget(stack, 1, 0, 2, 2)
        self.setLayout(layout)
        
        tileset_menu.currentIndexChanged.connect(stack.setCurrentIndex)
        
class TerrainUIframe(QFrame):
    """Contains widgets used to edit terrain."""
    set_width = pyqtSignal(float, str)
    set_height = pyqtSignal(float, str)
    set_tile = pyqtSignal(int)
    remove_terrain = pyqtSignal(bool)
    set_shortcuts = pyqtSignal()

    def __init__(self):
        super().__init__()
        
        remove_terrain_button = QPushButton("Remove all terrain")
        remove_terrain_button.setToolTip("Remove all currently placed terrain.")
        tile_selection_frame = TileSelectionFrame()
        size_frame = SizeFrame(50, 1, "Terrain", 1, 1)

        layout = QHBoxLayout()
        layout.addWidget(tile_selection_frame, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(size_frame, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addWidget(remove_terrain_button, alignment=Qt.AlignmentFlag.AlignBottom)
        self.setLayout(layout)
        
        remove_terrain_button.clicked.connect(self.remove_terrain)
        size_frame.set_width.connect(self.set_width)
        size_frame.set_height.connect(self.set_height)
        tile_selection_frame.set_tile.connect(self.set_tile)
        self.set_shortcuts.connect(size_frame.set_shortcuts)
        self.set_shortcuts.emit()