import os
from PyQt6.QtWidgets import (QWidget,
                             QLabel,
                             QGridLayout,
                             QLineEdit,
                             QDialog)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from ui_shared import SCMenu, DialogButton, IconButton
from obstacle import Obstacle
import sc_data
import read_write

class AudioMappingDialog(QDialog):
    """Contains widgets for mapping explosions to death counters."""
    closed = pyqtSignal(bool)
    
    def __init__(self, ob: Obstacle, parent: QWidget):
        super().__init__(parent)
        
        self.setWindowTitle("Audio mapping")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.ob = ob
        self.counts = set()
        self.mapping_size = 0
        
        apply_button = DialogButton("Apply", "Apply the selected audio mapping to counts in the input ranges.")
        apply_all_button = DialogButton("Apply all", "Apply the selected audio mapping to all counts.")
        counts_entry = QLineEdit()
        counts_entry.setToolTip("Enter a list of hyphen-separated ranges, separated by commas.")
        
        layout = QGridLayout()
        layout.addWidget(QLabel("Explosions:"), 0, 0)
        layout.addWidget(QLabel("Audio death count unit:"), 0, 1)
        layout.addWidget(QLabel("Counts: "), 1, 0)
        layout.addWidget(counts_entry, 1, 1)
        layout.addWidget(apply_button, 1, 2)
        layout.addWidget(apply_all_button, 2, 2)
        self.setLayout(layout)
        
        counts_entry.textChanged.connect(self.change_count_range)
        apply_button.clicked.connect(self.apply_mapping_to_input_counts)
        apply_all_button.clicked.connect(self.apply_mapping_to_all_counts)
        
    def closeEvent(self, event: QEvent) -> None:
        """Sends a signal when the window is closed."""
        self.closed.emit(False)
        event.accept()

    def copy_explosion(self) -> None:
        """Copies a row of the audio mapping with the input explosion ID."""
        layout = self.layout()
        sender = self.sender()
        row = 1
            
        # Finds the copied row.
        while row <= self.mapping_size:
             widget = layout.itemAtPosition(row, 2).widget()
             if widget == self.sender():
                break
             row += 1
        label = layout.itemAtPosition(row, 0).widget()
        explosion_name = label.text()
        ID = sc_data.name_to_ID[explosion_name]
         
        # Moves the buttons down one row.
        for lower_row in reversed(range(row + 1, self.mapping_size + 3)):
            for col in range(3):
                widget = layout.itemAtPosition(lower_row, col)
                if not widget:
                    continue
                widget = widget.widget()
                layout.removeWidget(widget)
                layout.addWidget(widget, lower_row + 1, col)
                
        # Adds the explosion label and the death count menu.
        explosion_name = QLabel(explosion_name)
        death_count_menu = SCMenu(sc_data.unit_list, 260)
        audio_settings = read_write.read_setting("Audio DC unit")
        # Sets a default death count for unit death sprite explosions, else sets a blank default.
        if str(ID) in audio_settings:
            index = sc_data.unit_indices[audio_settings[str(ID)]]
            death_count_menu.setCurrentIndex(index)
        else:
            death_count_menu.setCurrentIndex(-1)
        
        icons_path = read_write.get_path("Icons")
        copy_button = IconButton(QIcon(os.path.join(icons_path, "copy.png")),
                                28,
                                24,
                                "Insert a copy of this row into the audio mapping.",
                                False)
        copy_button.clicked.connect(self.copy_explosion)
        
        layout.addWidget(explosion_name, row + 1, 0)
        layout.addWidget(death_count_menu, row + 1, 1)
        layout.addWidget(copy_button, row + 1, 2)
        self.mapping_size += 1
        
    def add_explosion(self, ID: int) -> None:
        """Adds an explosion and an associated death count menu to the mapping."""
        # If the ID does not correspond to an audioless explosion, do nothing.
        if sc_data.event_data.loc[ID]["Audio"] == float('NaN'):
            return
            
        # Moves the buttons down one row.
        layout = self.layout()
        for row in reversed(range(self.mapping_size + 1, self.mapping_size + 3)):
            for col in range(3):
                widget = layout.itemAtPosition(row, col)
                if not widget:
                    continue
                widget = widget.widget()
                layout.removeWidget(widget)
                layout.addWidget(widget, row + 1, col)
                
        # Adds the explosion label and the death count menu.
        explosion_name = QLabel(sc_data.event_data.loc[ID]["Name"])
        death_count_menu = SCMenu(sc_data.unit_list, 260)
        audio_settings = read_write.read_setting("Audio DC unit")
        # Sets a default death count for unit death sprite explosions, else sets a blank default.
        if str(ID) in audio_settings:
            index = sc_data.unit_indices[audio_settings[str(ID)]]
            death_count_menu.setCurrentIndex(index)
        else:
            death_count_menu.setCurrentIndex(-1)
        
        icons_path = read_write.get_path("Icons")
        copy_button = IconButton(QIcon(os.path.join(icons_path, "copy.png")),
                                28,
                                24,
                                "Insert a copy of this row into the audio mapping.",
                                False)
        copy_button.clicked.connect(self.copy_explosion)
        
        layout.addWidget(explosion_name, self.mapping_size + 1, 0)
        layout.addWidget(death_count_menu, self.mapping_size + 1, 1)
        layout.addWidget(copy_button, self.mapping_size + 1, 2)
        self.mapping_size += 1
        
    def delete_explosion(self, ID: int) -> None:
        """Removes an explosion and its associated death count menu from the mapping."""
        layout = self.layout()
        explosion_name = sc_data.event_data.loc[ID]["Name"]
        
        # Find and remove the explosion label and death count menu.
        for row in range(1, self.mapping_size + 1):
            widget = layout.itemAtPosition(row, 0).widget()
            if widget.text() != explosion_name:
                continue
            layout.removeWidget(widget)
            layout.removeWidget(layout.itemAtPosition(row, 1).widget())
            
            # Move the remaining rows up.
            for other_row in range(row + 1, self.mapping_size + 3):
                for col in range(3):
                    widget = layout.itemAtPosition(other_row, col)
                    if not widget:
                        continue
                    widget = widget.widget()
                    layout.removeWidget(widget)
                    layout.addWidget(widget, other_row - 1, col)
            self.mapping_size -= 1
            
    def get_mapping(self) -> list[list[int, int]]:
        """Returns the currently selected audio mapping."""
        layout = self.layout()
        mapping = []
        for row in range(1, self.mapping_size + 1):
            label = layout.itemAtPosition(row, 0).widget()
            DC_menu = layout.itemAtPosition(row, 1).widget()
            DC_unit_index = DC_menu.currentIndex()
            if DC_unit_index == -1:
                continue
            explosion_name = label.text()
            explosion_ID = sc_data.name_to_ID[explosion_name]
            mapping.append([explosion_ID, DC_unit_index])
        return mapping
        
    def apply_mapping_to_count(self, count: int, mapping: list[list[int, int]]) -> None:
        """Applies the currently selected audio mapping to the input count."""
        self.ob.delete_audio_on_count(count)
        for explosion_ID, DC_unit_index in mapping:
            self.ob.add_audio(count, explosion_ID, DC_unit_index)
        
    def apply_mapping_to_input_counts(self) -> None:
        """Applies the currently selected audio mapping to all counts in the input ranges."""
        for count in self.counts:
            self.apply_mapping_to_count(count, self.get_mapping())
    
    def apply_mapping_to_all_counts(self) -> None:
        """Applies the currently selected audio mapping to all counts."""
        for count in range(1, len(self.ob.delays) + 1):
            self.apply_mapping_to_count(count, self.get_mapping())
            
    def change_count_range(self, text: str) -> None:
        """Updates the selected count ranges when the entry box is edited."""
        self.counts.clear()
        # Iterate through the comma separated ranges.
        for count_range in text.split(","):
            num_hypens = count_range.count("-")
            
            # There can be at most 1 hypen.
            if num_hypens > 1:
                return
                
            # If there are no hypens and the text is an integer, we add it to the set of counts.
            if num_hypens == 0:
                try:
                    count_num = int(count_range)
                    self.counts.add(count_num)
                except:
                    return
                    
            # If there are two hyphems and the text is two integers separated by a hyphen in
            # nondecreasing order, we had all counts in the range to the set of counts.
            else:
                start, end = count_range.split("-")
                try:
                    start, end = int(start), int(end)
                    if start > end:
                        return
                    for count in range(start, end + 1):
                        self.counts.add(count)
                except:
                    return
                   
    def reset(self) -> None:
        """Clears the current audio mapping."""
        layout = self.layout()
        while self.mapping_size > 0:
            explosion_name = layout.itemAtPosition(1, 0).widget().text()
            explosion_ID = sc_data.name_to_ID[explosion_name]
            self.delete_explosion(explosion_ID)