import os
from PyQt6.QtWidgets import QApplication
from src import ui_main_window

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
app = QApplication([])

main_window = ui_main_window.MainWindow()
main_window.showMaximized()

app.exec()