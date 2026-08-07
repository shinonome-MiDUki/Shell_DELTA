from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPlainTextEdit,
    QPushButton, QHBoxLayout, QFileDialog
)

from shell_delta import gb_var
from shell_delta.io.io_sadpj import IO_SADPJ

# --- Visual theme ---------------------------------
_BG = "#1b1c22"
_PANEL = "#24252c"
_BORDER = "#3a3b45"
_TEXT = "#e6e6ec"
_ACCENT = "#5b8cff"
_ACCENT_HOVER = "#6f9bff"
_ACCENT_PRESSED = "#4a76e0"

STYLE_SHEET = f"""
QDialog {{
    background-color: {_BG};
    color: {_TEXT};
    font-family: 'Segoe UI', 'Helvetica Neue', sans-serif;
    font-size: 13px;
}}
QPlainTextEdit {{
    background-color: {_PANEL};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 8px;
    font-family: Consolas, 'Courier New', monospace;
}}
QPlainTextEdit:focus {{
    border: 1px solid {_ACCENT};
}}
QPushButton {{
    background-color: {_PANEL};
    color: {_TEXT};
    border: 1px solid {_BORDER};
    border-radius: 6px;
    padding: 6px 14px;
}}
QPushButton:hover {{
    background-color: #34353f;
    border: 1px solid {_ACCENT};
}}
QPushButton:pressed {{
    background-color: #202128;
}}
QPushButton#primaryButton {{
    background-color: {_ACCENT};
    color: #ffffff;
    border: 1px solid {_ACCENT};
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background-color: {_ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: {_ACCENT_PRESSED};
}}
"""


class ExpressionEditor(QDialog):
    def __init__(self):
        super().__init__()
        self.resize(600,390)

        dialog_lo = QVBoxLayout()
        dialog_lo.setSpacing(10)
        dialog_lo.setContentsMargins(16, 16, 16, 16)

        self.scripting_area = QPlainTextEdit()
        self.scripting_area.setPlaceholderText("Custom Expression")
        self.set_expression()
        dialog_lo.addWidget(self.scripting_area)

        btn_lo = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_expression)
        btn_lo.addWidget(save_btn)
        open_tcl_btn = QPushButton("Load TCL")
        open_tcl_btn.clicked.connect(self.load_tcl_script)
        btn_lo.addWidget(open_tcl_btn)
        dialog_lo.addLayout(btn_lo)

        self.setStyleSheet(STYLE_SHEET)
        self.setLayout(dialog_lo)

    def load_tcl_script(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open TCL Script", "", "TCL Script (*.tcl)")
        if not filename:
            return
        with open(filename, "r", encoding="utf-8") as f:
            expression_content = f.read()
        self.scripting_area.setPlainText(expression_content)

    def save_expression(self):
        saving_path = gb_var.saving_path
        if saving_path is None:
            self.reject()
            return
        IO_SADPJ.write_sadpj(
            saving_path=str(saving_path),
            writing_info={"expression" : self.scripting_area.toPlainText()}
        )
        self.accept()

    def set_expression(self):
        saving_path = gb_var.saving_path
        if saving_path is None:
            self.reject()
            return
        current_expression = IO_SADPJ.read_sadpj(
            reading_path=str(saving_path),
            reading_attr="expression"
        )
        if current_expression is not None:
            self.scripting_area.setPlainText(current_expression)