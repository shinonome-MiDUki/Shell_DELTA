from pathlib import Path

from shell_delta.style import (
    dark_default, pure_skyblue,
    kawaii_pink, elegant_light
    )
styles = {
    "dark_default" : dark_default, 
    "pure_skyblue" : pure_skyblue,
    "kawaii_pink" : kawaii_pink, 
    "elegant_light" : elegant_light,
}
base_frame_list : list[int] = []
sequence_root_dir : Path | None = None
mata_filename : str | None = None
first_sequence_idx : int = 0
frame_notation_len : int = 0
saving_path : Path | None = None
ref_path: Path | None = None
ref_video_start: int = 0
style_script = dark_default