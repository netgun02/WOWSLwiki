"""Keep tkinter discoverable when PyInstaller's Tcl probe fails.

The local Python installation contains the Tcl/Tk runtime files, but its
automatic ``tkinter.Tcl()`` probe can fail before PyInstaller collects them.
The matching ``hook-_tkinter.py`` collects those files explicitly.
"""


def pre_find_module_path(hook_api):
    return None
