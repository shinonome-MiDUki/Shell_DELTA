import json
from pathlib import Path
from typing import Any

from shell_delta import gb_var
from shell_delta.render import time_map

class IO_SADPJ:
    def __init__(self):
        pass

    @classmethod
    def write_sadpj(cls, 
                    saving_path: str,
                    writing_info: dict
                    ) -> None:
        if not saving_path.endswith(".sadpj"):
            if "." in saving_path:
                saving_path_split = saving_path.split(".")
                saving_path_split.pop(-1)
                saving_path = "".join(saving_path_split)
            saving_path += ".sadpj"
        if Path(saving_path).exists:
            with open(saving_path, "r", encoding="utf-8") as f:
                current_sadpj = json.load(f)
            for writing_attr in writing_info:
                current_sadpj[writing_attr] = writing_info[writing_attr]
        else:
            current_sadpj = writing_info
        with open(saving_path, "w", encoding="utf-8") as f:
            json.dump(current_sadpj, f, indent=3, ensure_ascii=False)
        gb_var.saving_path = Path(saving_path)

    @classmethod
    def load_sadpj(cls,
                   reading_path: str
                   ) -> None:
        if not Path(reading_path).exists:
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sadpj = json.load(f)
        current_time_map = current_sadpj.get("time_map", {})
        time_map.time_map = current_time_map
        gb_var.sequence_root_dir = Path(current_sadpj["sequence_root_dir"]) if "sequence_root_dir" in current_sadpj else None
        gb_var.mata_filename = current_sadpj.get("mata_filename", None)
        gb_var.first_sequence_idx = current_sadpj.get("first_sequence_idx", 0)
        gb_var.frame_notation_len = current_sadpj.get("frame_notation_len", 0)
        gb_var.saving_path = Path(reading_path)

    @classmethod
    def read_sadpj(cls,
                   reading_path: str,
                   reading_attr: str
                   ) -> Any:
        if not Path(reading_path).exists:
            return
        with open(reading_path, "r", encoding="utf-8") as f:
            current_sadpj = json.load(f)
        return current_sadpj.get(reading_attr, None)


        