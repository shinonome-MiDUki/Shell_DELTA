import re
from pathlib import Path

from PySide6.QtCore import (
    Qt, QThread, QTimer,
    QUrl
    )
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QFileDialog, 
    QLineEdit, QComboBox, QDialog
)
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QDoubleValidator, QIntValidator

from shell_delta.ui.opengl import OpenGLImageWidget
from shell_delta.ui.render_dialog import RenderDialog
from shell_delta.ui.expression_editor import ExpressionEditor
from shell_delta.graphics.player import SequencePlayer
from shell_delta.render import time_map
from shell_delta.io.io_sadpj import IO_SADPJ
from shell_delta.expression.tcl_engine import TCLEngine
from shell_delta.utils.editing_utils import EditingUtils
from shell_delta import gb_var



class MainUserUi(QWidget):
    def __init__(self):
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        gb_var.frame_notation_len = 0
        self.inputting = False
        self.seq_idx = 0

        main_lo = QVBoxLayout()
        main_lo.setSpacing(10)
        main_lo.setContentsMargins(16, 16, 16, 16)

        io_lo = QHBoxLayout()
        read_btn = QPushButton("Read Sequence")
        read_btn.clicked.connect(self.open_sequence)
        io_lo.addWidget(read_btn)
        read_ref_btn = QPushButton("Read Ref")
        read_ref_btn.clicked.connect(self.open_reference)
        io_lo.addWidget(read_ref_btn)
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
        self.current_actual_img_idx_label.setStyleSheet(
            f"border: 1px solid {gb_var.style_script.MAIN_WIN_ACCENT}; border-radius: 6px; "
            f"background-color: {gb_var.style_script.MAIN_WIN_PANEL}; color: {gb_var.style_script.MAIN_WIN_TEXT}; font-weight: 600;"
        )
        labels_lo.addWidget(self.current_actual_img_idx_label)
        self.current_opened_label = QLabel("Working Sequence : None")
        labels_lo.addWidget(self.current_opened_label)
        main_lo.addLayout(labels_lo)

        graphics_lo = QHBoxLayout()
        self.gl_widget = OpenGLImageWidget("")
        graphics_lo.addWidget(self.gl_widget, stretch=2)

        self.ref_player = QMediaPlayer()
        graphics_sublo = QVBoxLayout()
        self.ref_video_widget = QVideoWidget()
        graphics_sublo.addWidget(self.ref_video_widget)
        self.ref_player.setVideoOutput(self.ref_video_widget)
        self.ref_audio_widget = QAudioOutput()
        self.ref_player.setAudioOutput(self.ref_audio_widget)

        ref_seq_parent = QWidget()
        self.ref_gl_widget = OpenGLImageWidget("")
        graphics_sublo.addWidget(self.ref_gl_widget)
        graphics_lo.addLayout(graphics_sublo, stretch=1)
        main_lo.addLayout(graphics_lo, 6)

        btn_lo = QHBoxLayout()
        prev_btn = QPushButton("Previous")
        prev_btn.clicked.connect(lambda: self.move_sequence(is_foward=False))
        self.current_frame_label = QLineEdit("0")
        self.current_frame_label.setValidator(QIntValidator())
        self.current_frame_label.setAlignment(Qt.AlignCenter)
        self.current_frame_label.setFixedWidth(60) 
        self.current_frame_label.editingFinished.connect(
            lambda: self.move_sequence(is_foward=True, is_increment=False)
        )
        next_btn = QPushButton("Next")
        next_btn.clicked.connect(lambda: self.move_sequence(is_foward=True))
        btn_lo.addWidget(prev_btn)
        btn_lo.addWidget(self.current_frame_label)
        btn_lo.addWidget(next_btn)
        main_lo.addLayout(btn_lo, 2)

        video_lo = QHBoxLayout()
        self.play_btn = QPushButton("Play")
        self.play_btn.setObjectName("primaryButton")
        self.play_btn.clicked.connect(self.play_sequence)
        video_lo.addWidget(self.play_btn)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_sequence)
        self.pause_btn.setEnabled(False)
        video_lo.addWidget(self.pause_btn)
        self.render_btn = QPushButton("Render")
        self.render_btn.setObjectName("primaryButton")
        self.render_btn.clicked.connect(self.render_sequence)
        video_lo.addWidget(self.render_btn)
        video_lo.addSpacing
        
        fps_input_lo = QHBoxLayout()
        fps_label = QLabel("FPS : ")
        fps_label.setFixedWidth(60)
        fps_label.setAlignment(Qt.AlignRight)
        fps_input_lo.addWidget(fps_label)
        self.fps_input_field = QLineEdit("24")
        self.fps_input_field.setValidator(QDoubleValidator())
        self.fps_input_field.setFixedWidth(60)
        fps_input_lo.addWidget(self.fps_input_field)
        video_lo.addLayout(fps_input_lo)
        main_lo.addLayout(video_lo, 1) 

        command_lo = QHBoxLayout()
        self.command_func_combo = QComboBox()
        self.command_func_combo.setFixedWidth(300)
        command_lo.addWidget(self.command_func_combo)
        self.exec_btn = QPushButton("Run Expression")
        self.exec_btn.clicked.connect(self.run_expression)
        command_lo.addWidget(self.exec_btn)
        self.edit_btn = QPushButton("Edit Expression")
        self.edit_btn.clicked.connect(self.edit_expresion)
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

        self.setStyleSheet(gb_var.style_script.MAIN_WIN_STYLESHEET)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setLayout(main_lo)

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
        self.seq_idx = 1
        if gb_var.mata_filename is None:
            return
        self.inputting = False
        actual_img_idx = EditingUtils.get_actual_img_idx(seq_idx=self.seq_idx)
        actual_filename = EditingUtils.get_actual_filepath(img_idx=actual_img_idx)
        self.current_actual_img_idx_label.setText(str(actual_img_idx))
        new_image_path = gb_var.sequence_root_dir / actual_filename
        if not new_image_path.exists():
            new_image_path = ""
        self.current_frame_label.setText(str(self.seq_idx))
        self.gl_widget.change_image(
            new_image_path=str(new_image_path)
            )
        self.ref_gl_widget.change_image(
            new_image_path=str(new_image_path)
        )
        self.current_opened_label.setText(
            f"Working Sequence : {gb_var.sequence_root_dir / gb_var.mata_filename}"
            )
        self.ref_player.setSource(QUrl.fromLocalFile(str(gb_var.ref_path)))
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
            "frame_notation_len" : gb_var.frame_notation_len,
            "ref_path" : gb_var.ref_path
        }
        IO_SADPJ.write_sadpj(
            saving_path=filename,
            writing_info=writing_info
            )
        self._show_expression_panel()

    def move_sequence(self, 
                      is_foward: bool=True, 
                      is_increment: bool=True,
                      increment_step: int=1
                      ):
        if gb_var.mata_filename is None:
            return
        self.inputting = False
        if is_increment:
            self.seq_idx += increment_step if is_foward else -increment_step
        else:
            self.seq_idx = int(self.current_frame_label.text())
        actual_img_idx = EditingUtils.get_actual_img_idx(seq_idx=self.seq_idx)
        actual_filename = EditingUtils.get_actual_filepath(img_idx=actual_img_idx)
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
        self.ref_gl_widget.change_image(new_image_path=filename)
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

    def open_reference(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Sequence", "", "Video (*.mp4)")
        if not filename:
            return
        self.ref_player.setSource(QUrl.fromLocalFile(filename))
        gb_var.ref_path = filename

    def play_sequence(self):
        self.play_btn.setEnabled(False)
        self.pause_btn.setEnabled(True)
        self.ref_player.play()

    def pause_sequence(self, arrived_idx):
        self.ref_player.pause()
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def on_finished(self):
        self.play_btn.setEnabled(True)
        self.pause_btn.setEnabled(False)

    def render_sequence(self):
        render_dialog_call = RenderDialog(fps=int(self.fps_input_field.text())).exec()
        if render_dialog_call == QDialog.Accepted:
            self.render_btn.setStyleSheet(f"color : {gb_var.style_script.MAIN_WIN_SUCCESS} ;")
            self.render_btn.setText("Rendered")
            self.render_btn.setEnabled(False)
            QTimer().singleShot(
                2000, 
                lambda: self._recover_btn(
                    btn=self.render_btn,
                    original_text="Render")
                )

    def edit_expresion(self):
        expression_edit = ExpressionEditor().exec()
        if expression_edit == QDialog.Accepted:
            self.command_func_combo.clear()
            self.command_func_combo.addItems(TCLEngine().get_procs())

    def run_expression(self):
        func_name = self.command_func_combo.currentText()
        from_frame = int(self.run_from_input.text())
        to_frame = int(self.run_to_input.text())
        for frame in range(from_frame, to_frame+1):
            tcl_rtn = TCLEngine().run_tcl(
                func_name=func_name,
                frame=frame
            )
            time_map.time_map[frame] = int(tcl_rtn)
        self.exec_btn.setStyleSheet(f"color : {gb_var.style_script.MAIN_WIN_SUCCESS} ;")
        self.exec_btn.setText("Executed")
        self.exec_btn.setEnabled(False)
        QTimer().singleShot(
            2000, 
            lambda: self._recover_btn(
                btn=self.exec_btn,
                original_text="Run Expression")
            )

    def _recover_btn(self, 
                     btn: QPushButton,
                     original_text: str
                     ):
        btn.setStyleSheet(f"color : {gb_var.style_script.MAIN_WIN_TEXT} ;")
        btn.setText(original_text)
        btn.setEnabled(True)


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
        modifier = event.modifiers()
        if pressed == Qt.Key.Key_Return:
            if not self.inputting: 
                return
            self.inputting = False
            time_map.time_map[self.seq_idx] = int(self.input_frame_num_str)
            actual_filename = EditingUtils.get_actual_filepath(img_idx=time_map.time_map[self.seq_idx])
            designated_image_path = gb_var.sequence_root_dir / actual_filename
            if not designated_image_path.exists():
                designated_image_path = ""
            self.input_frame_num_str = ""
            self.gl_widget.change_image(new_image_path=designated_image_path)
        elif pressed in _move_seq_keys:
            if pressed == Qt.Key.Key_Right:
                if (modifier & Qt.KeyboardModifier.ShiftModifier):
                    self.move_sequence(is_foward=True, is_increment=True, increment_step=10)
                else:
                    self.move_sequence(is_foward=True)
            elif pressed == Qt.Key.Key_Left:
                if (modifier & Qt.KeyboardModifier.ShiftModifier):
                    self.move_sequence(is_foward=False, is_increment=True, increment_step=10)
                else:
                    self.move_sequence(is_foward=False)
        elif pressed in _num_keys:
            if gb_var.mata_filename is None:
                return
            if not self.inputting:
                self.inputting = True
                self.input_frame_num_str = ""
            self.input_frame_num_str += str(_num_keys[pressed])
            self.current_actual_img_idx_label.setText(self.input_frame_num_str)