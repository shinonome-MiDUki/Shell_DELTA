import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtGui import QIcon

from shell_delta.ui.main_win import MainUserUi


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationDisplayName("Shell DELTA")
    app.setApplicationName("Shell_DELTA")
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "_resources/icon")))

    window = QMainWindow()
    window.setWindowTitle("Shell DELTA")
    window.resize(800, 600)

    main_ui = MainUserUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())