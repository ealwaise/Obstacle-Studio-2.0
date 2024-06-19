import os
from PyQt6.QtWidgets import (QWidget,
                             QPushButton,
                             QLabel,
                             QGridLayout,
                             QHBoxLayout,
                             QVBoxLayout,
                             QFrame,
                             QComboBox,
                             QStackedWidget,
                             QListWidget,
                             QListWidgetItem,
                             QDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from .ui_shared import NamedSpinBox, DialogButton
from src import read_write

class Brush(QFrame):
    """Contains widgets for creating and editing regions in which obstacle events are placed."""
    send_brush = pyqtSignal(str, list)
    
    def __init__(self):
        super().__init__()
        
        self.name = ""
        self.shape = [[1]]
        
    def emit_brush(self) -> None:
        """Emits a signal containing the brush's name and shape."""
        self.send_brush.emit(self.name, self.shape)
        
class HorizontalLine(Brush):
    """A brush whose shape is a rectangle of height 1."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1]]
        self.dimensions = {"width": 1}
                           
        width_box = NamedSpinBox("width", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Width: "), 0, 0, 1, 2)
        layout.addWidget(width_box, 0, 2)
        self.setLayout(layout)
        
        width_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        width = self.dimensions["width"]
        self.shape = [[1]*width]
        self.name = "Horizontal Line({})".format(width)
        
class VerticalLine(Brush):
    """A brush whose shape is a rectangle of width 1."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1]]
        self.dimensions = {"height": 1}
                           
        height_box = NamedSpinBox("height", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Height: "), 0, 0, 1, 2)
        layout.addWidget(height_box, 0, 2)
        self.setLayout(layout)
        
        height_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        height = self.dimensions["height"]
        self.shape = [[1] for i in range(height)]
        self.name = "Vertical Line({})".format(height)
        
class Rectangle(Brush):
    """A brush whose shape is a rectangle."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1]]
        self.dimensions = {"width": 1, "height": 1}
                           
        width_box = NamedSpinBox("width", 1)
        height_box = NamedSpinBox("height", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Dimensions: "), 0, 0, 1, 2)
        layout.addWidget(width_box, 0, 2)
        layout.addWidget(QLabel("×"), 0, 3)
        layout.addWidget(height_box, 0, 4)
        self.setLayout(layout)
        
        width_box.valueChanged.connect(self.set_dimension)
        height_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        width = self.dimensions["width"]
        height = self.dimensions["height"]
        self.shape = [[1]*width for i in range(height)]
        self.name = "Rectangle({}, {})".format(width, height)
        
class Square(Brush):
    """A brush whose shape is a square."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1]]
        self.dimensions = {"width": 1}
                           
        width_box = NamedSpinBox("width", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Dimension: "), 0, 0, 1, 2)
        layout.addWidget(width_box, 0, 2)
        self.setLayout(layout)
        
        width_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        width = self.dimensions["width"]
        self.shape = [[1]*width for i in range(width)]
        self.name = "Square({})".format(width)
        
class PuncturedRectangle(Brush):
    """A brush whose shape is a rectangle with a smaller rectangle removed from the center."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
        self.dimensions = {"outer width": 3,
                           "outer height": 3,
                           "inner width": 1,
                           "inner height": 1}
                           
        outer_width_box = NamedSpinBox("outer width", 3)
        outer_height_box = NamedSpinBox("outer height", 3)
        inner_width_box = NamedSpinBox("inner width", 1)
        inner_height_box = NamedSpinBox("inner height", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Outer dimensions: "), 0, 0, 1, 2)
        layout.addWidget(outer_width_box, 0, 2)
        layout.addWidget(QLabel("×"), 0, 3)
        layout.addWidget(outer_height_box, 0, 4)
        layout.addWidget(QLabel("Inner dimensions: "), 1, 0, 1, 2)
        layout.addWidget(inner_width_box, 1, 2)
        layout.addWidget(QLabel("×"), 1, 3)
        layout.addWidget(inner_height_box, 1, 4)
        self.setLayout(layout)
        
        outer_width_box.valueChanged.connect(self.set_dimension)
        outer_height_box.valueChanged.connect(self.set_dimension)
        inner_width_box.valueChanged.connect(self.set_dimension)
        inner_height_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        outer_width = self.dimensions["outer width"]
        outer_height = self.dimensions["outer height"]
        inner_width = self.dimensions["inner width"]
        inner_height = self.dimensions["inner height"]
        
        # If the shape is invalid, return None.
        if outer_width <= inner_width or outer_height <= inner_height:
            return
        if outer_width % 2 != inner_width % 2 or outer_height % 2 != inner_height % 2:
            return
        
        # Compute the shape and name.
        diff_horz = (outer_width - inner_width) // 2
        diff_vert = (outer_height - inner_height) // 2
        shape = []
        for j in range(outer_height):
            row = [1]*outer_width
            if diff_vert <= j < inner_height + diff_vert:
                for i in range(diff_horz, inner_width + diff_vert):
                    row[i] = 0
            shape.append(row)
        self.shape = shape
        self.name = "Punctured rectangle({}, {}, {}, {})".format(outer_width,
                                                                 outer_height,
                                                                 inner_width,
                                                                 inner_height)
                                                                 
class PuncturedSquare(Brush):
    """A brush whose shape is a square with a smaller square removed from the center."""

    def __init__(self):
        super().__init__()
        
        self.shape = [[1, 1, 1], [1, 0, 1], [1, 1, 1]]
        self.dimensions = {"outer width": 3, "inner width": 1}
                           
        outer_width_box = NamedSpinBox("outer width", 3)
        inner_width_box = NamedSpinBox("inner width", 1)
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Outer dimension: "), 0, 0, 1, 2)
        layout.addWidget(outer_width_box, 0, 2)
        layout.addWidget(QLabel("Inner dimension: "), 1, 0, 1, 2)
        layout.addWidget(inner_width_box, 1, 2)
        self.setLayout(layout)
        
        outer_width_box.valueChanged.connect(self.set_dimension)
        inner_width_box.valueChanged.connect(self.set_dimension)

    def set_dimension(self, dim: int) -> None:
        """Changes a dimension of the brush depending on dim and the widget sending the signal."""
        name = self.sender().objectName()
        self.dimensions[name] = dim
        
    def set_shape(self) -> None:
        """Sets the shape if it is valid."""
        outer_width = self.dimensions["outer width"]
        inner_width = self.dimensions["inner width"]
        
        # If the shape is invalid, return None.
        if outer_width <= inner_width:
            return
        if outer_width % 2 != inner_width % 2:
            return
        
        # Compute the shape and name.
        diff = (outer_width - inner_width) // 2
        shape = []
        for j in range(outer_width):
            row = [1]*outer_width
            if diff <= j < inner_width + diff:
                for i in range(diff, inner_width + diff):
                    row[i] = 0
            shape.append(row)
        self.shape = shape
        self.name = "Punctured square({}, {})".format(outer_width,
                                                                 inner_width)
                                                                 
