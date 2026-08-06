import sys
import re
import time
import threading
from pathlib import Path

from PySide6.QtCore import (
    Qt, QThread, )
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, 
    QLineEdit, QComboBox
)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtGui import QDoubleValidator, QIntValidator

from shell_delta.ui.opengl import OpenGLImageWidget
from shell_delta.ui.render_dialog import RenderDialog
from shell_delta.ui.expression_editor import ExpressionEditor
from shell_delta.graphics.player import SequencePlayer
from shell_delta.render import time_map
from shell_delta.io.io_sadpj import IO_SADPJ
from shell_delta.expression.tcl_engine import TCLEngine
from shell_delta import gb_var

class MainUserUi(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        gb_var.frame_notation_len = 0
        self.inputting = False
        self.seq_idx = 0

        main_lo = QVBoxLayout()

        io_lo = QHBoxLayout()
        read_btn = QPushButton("Read Sequence")
        read_btn.clicked.connect(self.open_sequence)
        io_lo.addWidget(read_btn)
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_proj)
        io_lo.addWidget(save_btn)
        open_btn = QPushButton("Open")
        open_btn.clicked.connect(self.read_proj)
        io_lo.addWidget(open_btn)
        main_lo.addLayout(io_lo)
        
        labels_lo = QHBoxLayout()
        self.current_actual_img_idx_label = QLabel("----")
        self.current_actual_img_idx_label.setFixedWidth(50)
        self.current_actual_img_idx_label.setAlignment(Qt.AlignCenter) 
        self.current_actual_img_idx_label.setStyleSheet("border:2px solid #000000;")
        labels_lo.addWidget(self.current_actual_img_idx_label)
        self.current_opened_label = QLabel("Working Sequence : None")
        labels_lo.addWidget(self.current_opened_label)
        main_lo.addLayout(labels_lo)

        self.gl_widget = OpenGLImageWidget("")
        main_lo.addWidget(self.gl_widget, 6)

        btn_lo = QHBoxLayout()
        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(lambda: self.move_sequence(is_foward=False))
        self.current_frame_label = QLabel("0")
        self.current_frame_label.setAlignment(Qt.AlignCenter) 
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(lambda: self.move_sequence(is_foward=True))
        btn_lo.addWidget(prev_btn)
        btn_lo.addWidget(self.current_frame_label)
        btn_lo.addWidget(next_btn)
        main_lo.addLayout(btn_lo, 2)

        video_lo = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.clicked.connect(self.play_sequence)
        video_lo.addWidget(self.play_btn)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_sequence)
        self.pause_btn.setEnabled(False)
        video_lo.addWidget(self.pause_btn)
        render_btn = QPushButton("Render")
        render_btn.clicked.connect(self.render_sequence)
        video_lo.addWidget(render_btn)
        video_lo.addSpacing
        
        fps_input_lo = QHBoxLayout()
        fps_input_lo.addWidget(QLabel("FPS : "))
        self.fps_input_field = QLineEdit("24")
        self.fps_input_field.setValidator(QDoubleValidator())
        fps_input_lo.addWidget(self.fps_input_field)
        video_lo.addLayout(fps_input_lo)
        main_lo.addLayout(video_lo, 1) 

        command_lo = QHBoxLayout()
        self.command_func_combo = QComboBox()
        command_lo.addWidget(self.command_func_combo)
        self.exec_btn = QPushButton("Run Expression")
        command_lo.addWidget(self.exec_btn)
        self.edit_btn = QPushButton("Edit Expression")
        command_lo.addWidget(self.edit_btn)

        command_lo.addStretch
        self.from_word_label = QLabel("from")
        command_lo.addWidget(self.from_word_label)
        self.run_from_input = QLineEdit("0")
        self.run_from_input.setValidator(QIntValidator())
        command_lo.addWidget(self.run_from_input)
        self.to_word_label = QLabel("to")
        command_lo.addWidget(self.to_word_label)
        self.run_to_input = QLineEdit("1")
        self.run_to_input.setValidator(QIntValidator())
        command_lo.addWidget(self.run_to_input)
        main_lo.addLayout(command_lo)

        self.command_func_combo.hide()
        self.exec_btn.hide()
        self.edit_btn.hide()
        self.from_word_label.hide()
        self.run_from_input.hide()
        self.to_word_label.hide()
        self.run_to_input.hide()

        self.setLayout(main_lo)

    def _get_actual_img_idx(self) -> int:
        actual_img_idx = time_map.time_map.get(self.seq_idx, None)
        if actual_img_idx is not None:
            return actual_img_idx
        checking_idx = self.seq_idx - 1
        while actual_img_idx is None and checking_idx >= 0:
            actual_img_idx = time_map.time_map.get(checking_idx, None)
            checking_idx -= 1
        return actual_img_idx if actual_img_idx is not None else -1

    def _show_expression_panel(self):
        self.command_func_combo.show()
        self.exec_btn.show()
        self.edit_btn.show()
        self.from_word_label.show()
        self.run_from_input.show()
        self.to_word_label.show()
        self.run_to_input.show()
        self.command_func_combo.clear()
        self.command_func_combo.addItems(TCLEngine().get_procs())

    def read_proj(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "Shell Delta proj. (*.sadpj)")
        if not filename:
            return
        IO_SADPJ.load_sadpj(reading_path=filename)
        self.seq_idx = 0
        if gb_var.mata_filename is None:
            return
        self.inputting = False
        actual_img_idx = self._get_actual_img_idx()
        actual_filename = gb_var.mata_filename.replace(
            '#' * gb_var.frame_notation_len, 
            f"{actual_img_idx:0{gb_var.frame_notation_len}d}"
            )
        self.current_actual_img_idx_label.setText(str(actual_img_idx))
        new_image_path = gb_var.sequence_root_dir / actual_filename
        if not new_image_path.exists():
            new_image_path = ""
        self.current_frame_label.setText(str(self.seq_idx))
        self.gl_widget.change_image(
            new_image_path=str(new_image_path)
            )
        self.current_opened_label.setText(
            f"Working Sequence : {gb_var.sequence_root_dir / gb_var.mata_filename}"
            )
        self._show_expression_panel()

    def save_proj(self):
        if gb_var.saving_path is None:
            filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "Shell Delta proj. (*.sadpj)")
            if not filename:
                return
        else:
            filename = str(gb_var.saving_path)
        writing_info = {
            "time_map" : time_map.time_map,
            "sequence_root_dir" : str(gb_var.sequence_root_dir),
            "mata_filename" : gb_var.mata_filename,
            "first_sequence_idx" : gb_var.first_sequence_idx,
            "frame_notation_len" : gb_var.frame_notation_len
        }
        IO_SADPJ.write_sadpj(
            saving_path=filename,
            writing_info=writing_info
            )
        self._show_expression_panel()

    def move_sequence(self, is_foward: bool):
        if gb_var.mata_filename is None:
            return
        self.inputting = False
        self.seq_idx += 1 if is_foward else -1
        actual_img_idx = self._get_actual_img_idx()
        actual_filename = gb_var.mata_filename.replace(
            '#' * gb_var.frame_notation_len, 
            f"{actual_img_idx:0{gb_var.frame_notation_len}d}"
            )
        self.current_actual_img_idx_label.setText(str(actual_img_idx))
        new_image_path = gb_var.sequence_root_dir / actual_filename
        if not new_image_path.exists():
            new_image_path = ""
        self.current_frame_label.setText(str(self.seq_idx))
        self.gl_widget.change_image(
            new_image_path=str(new_image_path)
            )

    def open_sequence(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "PNG (*.png)")
        if not filename:
            return
        gb_var.sequence_root_dir = Path(filename).resolve().parent
        matches = re.findall(r'\d+', filename)
        if len(matches) != 1:
            return
        self.gl_widget.change_image(new_image_path=filename)
        gb_var.frame_notation_len = len(matches[0]) 
        gb_var.first_sequence_idx = int(matches[0])   
        sharps = '#' * gb_var.frame_notation_len       
        filename = re.sub(r'\d+', sharps, filename).split("/")[-1]
        gb_var.mata_filename = filename
        self.seq_idx = gb_var.first_sequence_idx
        self.current_opened_label.setText(
            f"Working Sequence : {gb_var.sequence_root_dir / gb_var.mata_filename}"
            )
        self.current_actual_img_idx_label.setText(str(self.seq_idx))
        self.current_frame_label.setText(str(gb_var.first_sequence_idx))

        parts = [re.escape(p) for p in gb_var.mata_filename.split(sharps)]
        regex_pattern = "^" + r"(\d+)".join(parts) + "$"
        numbers = [
            m.group(1)
            for item in gb_var.sequence_root_dir.iterdir()
            if item.is_file() and (m := re.match(regex_pattern, item.name))
        ]
        for num in numbers:
            num = int(num)
            time_map.time_map[num] = num

    def play_sequence(self):
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)

        self.td = QThread()
        self.worker = SequencePlayer(
            gl_widget=self.gl_widget,
            fps=float(self.fps_input_field.text()),
            current_idx=self.seq_idx,
            meta_filename=gb_var.mata_filename,
            sequence_root_dir=gb_var.sequence_root_dir,
            frame_notation_len=gb_var.frame_notation_len,
            frame_img_dict=time_map.time_map
        )
        self.worker.moveToThread(self.td)
        self.td.started.connect(self.worker.play_sequence)
        self.worker.SIG.connect(self.td.quit)
        self.worker.SIG.connect(self.worker.deleteLater)
        self.td.finished.connect(self.td.deleteLater)
        self.td.finished.connect(self.on_finished)

        self.td.start()

    def pause_sequence(self, arrived_idx):
        if self.worker:
            self.worker.stop()
            self.seq_idx = arrived_idx
            self.current_frame_label.setText(str(self.seq_idx))

    def on_finished(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def render_sequence(self):
        RenderDialog(fps=int(self.fps_input_field.text())).exec()

    def edit_expresion(self):
        ExpressionEditor().exec()

    def run_expression(self):
        func_name = self.command_func_combo.currentText()
        from_frame = int(self.run_from_input.text())
        to_frame = int(self.run_to_input.text())
        for frame in range(from_frame, to_frame+1):
            TCLEngine().run_tcl(
                func_name=func_name,
                frame=frame
            )


    def keyPressEvent(self, event):
        _move_seq_keys = [
            Qt.Key.Key_Right,
            Qt.Key.Key_Left
        ]
        _num_keys = {
            Qt.Key.Key_0 : 0,
            Qt.Key.Key_1 : 1,
            Qt.Key.Key_2 : 2,
            Qt.Key.Key_3 : 3,
            Qt.Key.Key_4 : 4,
            Qt.Key.Key_5 : 5,
            Qt.Key.Key_6 : 6,
            Qt.Key.Key_7 : 7, 
            Qt.Key.Key_8 : 8,
            Qt.Key.Key_9 : 9
        }
        pressed = event.key()
        if pressed == Qt.Key.Key_Return:
            if not self.inputting: 
                return
            self.inputting = False
            time_map.time_map[self.seq_idx] = int(self.input_frame_num_str)
            actual_filename = gb_var.mata_filename.replace(
                '#' * gb_var.frame_notation_len, 
                f"{time_map.time_map[self.seq_idx]:0{gb_var.frame_notation_len}d}"
                )
            designated_image_path = gb_var.sequence_root_dir / actual_filename
            if not designated_image_path.exists():
                designated_image_path = ""
            self.input_frame_num_str = ""
            self.gl_widget.change_image(new_image_path=designated_image_path)
        elif pressed in _move_seq_keys:
            if pressed == Qt.Key.Key_Right:
                self.move_sequence(is_foward=True)
            elif pressed == Qt.Key.Key_Left:
                self.move_sequence(is_foward=False)
        elif pressed in _num_keys:
            if gb_var.mata_filename is None:
                return
            if not self.inputting:
                self.inputting = True
                self.input_frame_num_str = ""
            self.input_frame_num_str += str(_num_keys[pressed])
            self.current_actual_img_idx_label.setText(self.input_frame_num_str)