"""Make bundled Qt and Shiboken DLLs visible to Windows' native loader."""

import os
import sys


if sys.platform == "win32" and getattr(sys, "frozen", False):
    _bundle_root = sys._MEIPASS
    _dll_directories = (
        os.path.join(_bundle_root, "PySide6"),
        os.path.join(_bundle_root, "shiboken6"),
    )

    # Keep these handles alive for the lifetime of the process. Qt extension
    # modules load their dependent DLLs from these package-specific folders.
    _dll_directory_handles = [
        os.add_dll_directory(path)
        for path in _dll_directories
        if os.path.isdir(path)
    ]

    os.environ["PATH"] = os.pathsep.join(
        (*_dll_directories, os.environ.get("PATH", ""))
    )
