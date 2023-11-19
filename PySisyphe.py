"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

import os
import ctypes
from sys import argv, exit, platform

if platform == 'darwin':
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QApplication

from Sisyphe.gui.dialogSplash import DialogSplash
from Sisyphe.gui.windowSisyphe import WindowSisyphe

"""
    PySisyphe
"""

if __name__ == "__main__":

    app = QApplication(argv)
    settings = QSettings('PySisyphe', 'PySisyphe')

    if platform == 'darwin':
        QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, True)
        QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, False)
    elif platform == 'win32':
        # High DPI scaling bugfix
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        # QApplication.setAttribute(Qt.AA_DisableHighDpiScaling)

    splash = DialogSplash()
    splash.buttonVisibilityOff()
    splash.progressBarVisibilityOff()
    splash.show()
    QApplication.processEvents()

    main = WindowSisyphe()
    main.show()
    splash.close()

    exit(app.exec_())
