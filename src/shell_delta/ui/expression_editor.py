from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QPlainTextEdit,
    QPushButton
)

from shell_delta import gb_var
from shell_delta.io.io_sadpj import IO_SADPJ

class ExpressionEditor(QDialog):
    def __init__(self):
        super().__init__()

        dialog_lo = QVBoxLayout()

        self.scripting_area = QPlainTextEdit()
        self.scripting_area.setPlaceholderText("Custom Expression")
        self.set_expression()
        dialog_lo.addWidget(self.scripting_area)

        save_btn = QPushButton("Save")
        dialog_lo.addWidget(save_btn)

        self.setLayout(dialog_lo)

    def save_expression(self):
        saving_path = gb_var.saving_path
        if saving_path is None:
            self.reject()
            return
        IO_SADPJ.write_sadpj(
            saving_path=str(saving_path),
            writing_info={"expression" : self.scripting_area.toPlainText()}
        )

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