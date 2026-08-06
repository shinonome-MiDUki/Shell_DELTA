import tkinter

from shell_delta.io.io_sadpj import IO_SADPJ
from shell_delta import gb_var

class TCLEngine:
    def __init__(self):
        self.tcl_intepreter = tkinter.Tcl()
        reading_path = gb_var.saving_path
        if reading_path is None:
            print("TCL Engine used when reading_path is None")
            return
        self.expression = IO_SADPJ.read_sadpj(
            reading_path=str(reading_path),
            reading_attr="expression"
        )

    def get_procs(self) -> list[str]:
        all_procs = self.tcl_intepreter.eval("info procs").split()
        system_procs = {
            'unknown', 'auto_load', 'auto_load_index', 'auto_import', 
            'auto_execok', 'auto_qualify', 'tclLog'
            }
        function_procs = [p for p in all_procs if p not in system_procs]
        return function_procs