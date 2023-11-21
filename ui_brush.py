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
from ui_shared import NamedSpinBox, DialogButton
from brushes import (Brush,
                     HorizontalLine,
                     VerticalLine,
                     Rectangle,
                     Square,
                     PuncturedRectangle,
                     PuncturedSquare)
import read_write

class BrushStack(QStackedWidget):
    """A stacked widget containing various brushes."""
    send_brush = pyqtSignal(str, list)

    def __init__(self):
        super().__init__()

    def add_widget(self, brush: QWidget) -> None:
        """Adds the input brush to the stack."""
        # Encases the input widget in a frame for alignment purposes.
        layout = QHBoxLayout()
        layout.addWidget(brush, alignment=Qt.AlignmentFlag.AlignTop)
        frame = QFrame()
        frame.setLayout(layout)
        brush.send_brush.connect(self.send_brush)
        super().addWidget(frame)
        
    def current_brush(self) -> QWidget:
        """Returns the currently displayed brush."""
        return self.currentWidget().layout().itemAt(0).widget()
        
    def add_brush(self) -> None:
        """Adds the current brush to the list of brushes."""
        brush = self.currentWidget().children()[1]
        brush.set_shape()
        brush.emit_brush()

class BrushEditor(QDialog):
    """Contains widgets for editing brushes."""
    closed = pyqtSignal(bool)
    send_brush = pyqtSignal(str, list)
    
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        
        self.setWindowTitle("Brush editor")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.shape = [[1]]
        
        brush_box = QComboBox()
        brush_box.addItems(["Horizontal line",
                            "Vertical line",
                            "Rectangle",
                            "Square",
                            "Punctured rectangle",
                            "Punctured square"])
        stack = BrushStack()
        stack.add_widget(HorizontalLine())
        stack.add_widget(VerticalLine())
        stack.add_widget(Rectangle())
        stack.add_widget(Square())
        stack.add_widget(PuncturedRectangle())
        stack.add_widget(PuncturedSquare())
        add_button = DialogButton("Add",
                                  "Add the brush to the list of brushes.")
        
        layout = QVBoxLayout()
        layout.addWidget(brush_box)
        layout.addWidget(stack)
        layout.addWidget(add_button)
        self.setLayout(layout)
        
        add_button.clicked.connect(stack.add_brush)
        stack.send_brush.connect(self.send_brush)
        brush_box.currentIndexChanged.connect(stack.setCurrentIndex)

    def closeEvent(self, event: QEvent) -> None:
        """Sends a signal when the window is closed."""
        self.closed.emit(False)
        event.accept()
        
class BrushListItem(QListWidgetItem):
    """A list item represeting a brush."""
    
    def __init__(self, name: str, shape: list[list[int]]):
        super().__init__(name)
        
        self.shape = shape
        
class BrushList(QListWidget):
    """A list of brushes to select."""
    change_brush = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        default_brush = BrushListItem("Default", [[1]])
        self.addItem(default_brush)
        
        self.itemSelectionChanged.connect(self.emit_selected_brush)
        
    def emit_selected_brush(self) -> None:
        """Emits a signal when the selected brush changes."""
        brush = self.selectedItems()[0]
        self.change_brush.emit(brush.shape)
    
    def add_brush(self, name: str, shape: list[list[int]]) -> None:
        """Adds a brush with the input name and shape to the list."""
        # If the list already contains a brush with the input name, do nothing.
        for i in range(self.count()):
            item = self.item(i)
            if item.text() == name:
                return
                
        brush = BrushListItem(name, shape)
        self.addItem(brush)
        
    def remove_brush(self, name: str) -> None:
        """Delete the brush with the input name and selects the default brush."""
        # The default brush cannot be deleted.
        if name == "Default":
            return
            
        for i in range(self.count()):
            item = self.item(i)
            if item.text() == name:
                self.takeItem(i)
                break
        self.item(0).setSelected(True)
        
    def remove_selected_brush(self) -> None:
        """Removes the selected_brush from the list."""
        item = self.selectedItems()[0]
        self.remove_brush(item.text())
        
    def select_default(self, disabled: bool) -> None:
        """Selects the default brush if disabled is true."""
        if disabled:
            self.item(0).setSelected(True)

class BrushUI(QFrame):
    """Contains a list for selecting brushes and opening the brush editor."""
    open_brush_editor = pyqtSignal()
    send_brush = pyqtSignal(str, list)
    send_shape = pyqtSignal(list)
    disable = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.setEnabled(False)
        brush_list = BrushList()
        brush_list.item(0).setSelected(True)
        brush_editor_button = QPushButton("Brush editor")
        brush_editor_button.setToolTip("Open the brush editor.")
        remove_button = QPushButton("Remove")
        remove_button.setToolTip("Remove the selected brush from the list of brushes.")
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Brushes:"), 0, 0)
        layout.addWidget(brush_list, 1, 0, 2, 2)
        layout.addWidget(brush_editor_button, 3, 0)
        layout.addWidget(remove_button, 3, 1)
        self.setLayout(layout)
        
        brush_editor_button.clicked.connect(self.open_brush_editor)
        brush_list.change_brush.connect(self.send_shape)
        self.send_brush.connect(brush_list.add_brush)
        remove_button.clicked.connect(brush_list.remove_selected_brush)
        self.disable.connect(brush_list.select_default)
        
    def switch_event(self, event: str) -> None:
        """Sets the state of the brush UI according to the selected event type."""
        flag = event != "Teleport"
        self.setEnabled(flag)
        self.disable.emit(not flag)
    
    def switch_placement(self, placement: str) -> None:
        """Sets the state of the brush UI according to the selected placement type."""
        flag = placement == "Mobile"
        self.setEnabled(flag)
        self.disable.emit(not flag)