from .object_cleanerUI import ObjectCleanerUI
from PySide6 import QtWidgets

def run():
    """Run the Object Cleaner UI in Maya."""
    # Close any existing Object Cleaner windows
    for w in QtWidgets.QApplication.allWidgets():
        if isinstance(w, ObjectCleanerUI):
            w.close()
    dlg = ObjectCleanerUI()
    dlg.show()
    return dlg
