import time
from pathlib import Path

from PySide6.QtCore import (
    QObject, Signal, Slot
)

from shell_delta.ui.opengl import OpenGLImageWidget
from shell_delta.render import time_map
from shell_delta import gb_var

class SequencePlayer(QObject):
    SIG = Signal(int)

    def __init__(self,
                 gl_widget: OpenGLImageWidget,
                 fps: float,
                 current_idx: int,
                 meta_filename: str,
                 sequence_root_dir: Path,
                 frame_notation_len: int,
                 frame_img_dict: dict
                 ) -> None:
        super().__init__()
        self.is_playing = False
        self.gl_widget = gl_widget
        self.spf = 1 / fps
        self.seq_idx = current_idx
        self.meta_filename = meta_filename
        gb_var.sequence_root_dir = sequence_root_dir
        gb_var.frame_notation_len = frame_notation_len
        time_map.time_map = frame_img_dict

    def _get_actual_img_idx(self) -> int:
        actual_img_idx = time_map.time_map.get(self.seq_idx, None)
        if actual_img_idx is not None:
            return actual_img_idx
        checking_idx = self.seq_idx - 1
        while actual_img_idx is None and checking_idx >= 0:
            actual_img_idx = time_map.time_map.get(checking_idx, None)
            checking_idx -= 1
        return actual_img_idx if actual_img_idx is not None else -1

    def move_sequence(self, 
                      is_foward: bool,
                      target_time: float
                      ):
        if self.meta_filename is None:
            return
        self.inputting = False
        self.seq_idx += 1 if is_foward else -1
        actual_img_idx = self._get_actual_img_idx()
        actual_filename = self.meta_filename.replace(
            '#' * gb_var.frame_notation_len, 
            f"{actual_img_idx:0{gb_var.frame_notation_len}d}"
            )
        new_image_path = gb_var.sequence_root_dir / actual_filename
        if not new_image_path.exists():
            new_image_path = ""
        self.gl_widget.change_image(
            new_image_path=str(new_image_path),
            target_time=target_time
            )

    @Slot()
    def play_sequence(self):
        self.is_playing = True
        target_time = time.time()
        while self.is_playing and self.seq_idx <= 1000:
            target_time += self.spf
            self.move_sequence(
                is_foward=True,
                target_time=target_time
                )
            self.seq_idx += 1
        self.SIG.emit(self.seq_idx)

    @Slot()
    def stop(self):
        self.is_playing = False