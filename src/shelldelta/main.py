import sys
from PySide6.QtWidgets import (
    QApplication, QLabel, QWidget, 
    QVBoxLayout, QHBoxLayout, 
)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("MY UI")
        self.resize(800, 800)
    
        layout = QVBoxLayout()
        label = QLabel("Hello World")
        
        label.setStyleSheet("font-size: 16px;")
    
        layout.addWidget(label)
        self.setLayout(layout)


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()