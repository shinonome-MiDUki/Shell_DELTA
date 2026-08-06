import sys

from PySide6.QtWidgets import QApplication, QMainWindow

from shell_delta.ui.main_win import MainUserUi


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    window = QMainWindow()
    window.setWindowTitle("PySide OpenGL Aspect Ratio Fixed")
    window.resize(800, 600)

    main_ui = MainUserUi()
    window.setCentralWidget(main_ui)

    window.show()
    sys.exit(app.exec())