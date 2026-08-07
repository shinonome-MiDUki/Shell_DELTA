from shell_delta.render import time_map
from shell_delta import gb_var

class EditingUtils:
    @classmethod
    def get_actual_img_idx(cls,
                            seq_idx: int
                            ) -> int:
        actual_img_idx = time_map.time_map.get(seq_idx, None)
        if actual_img_idx is not None:
            return actual_img_idx
        checking_idx = seq_idx - 1
        while actual_img_idx is None and checking_idx >= 0:
            actual_img_idx = time_map.time_map.get(checking_idx, None)
            checking_idx -= 1
        return actual_img_idx if actual_img_idx is not None else -1

    @classmethod
    def get_actual_filepath(cls,
                            img_idx: int) -> str:
        actual_filename = gb_var.mata_filename.replace(
            '#' * gb_var.frame_notation_len, 
            f"{img_idx:0{gb_var.frame_notation_len}d}"
            )
        return actual_filename