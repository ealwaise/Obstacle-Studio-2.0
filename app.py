import os
from PyQt6.QtWidgets import QApplication
from ui_main_window import MainWindow

os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
app = QApplication([])

main_window = MainWindow()
main_window.showMaximized()

app.exec()