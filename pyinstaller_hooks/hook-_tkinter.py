"""Collect the Tcl/Tk script libraries from the active Python installation."""

import os
import sys


_TCL_ROOT = os.path.join(sys.base_prefix, "tcl")

datas = [
    (os.path.join(_TCL_ROOT, "tcl8.6"), "_tcl_data"),
    (os.path.join(_TCL_ROOT, "tk8.6"), "_tk_data"),
    (os.path.join(_TCL_ROOT, "tcl8"), "tcl8"),
]
