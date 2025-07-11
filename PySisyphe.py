"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - PyQtDarkTheme, dark theme management for win32 platform, https://pyqtdarktheme.readthedocs.io/en/stable/index.html
    - pywinstyles, customize window title bar for win32 platform, https://github.com/Akascape/py-window-styles
    - vtk, visualization, https://vtk.org/
"""

if __name__ == "__main__":
    # noinspection PyUnresolvedReferences
    from multiprocessing import freeze_support
    """
    Enable support for multiprocessing in frozen code
    """
    # < Revision 21/06/2025
    # enable support for multiprocessing in frozen code
    freeze_support()
    # Revision 21/06/2025 >

import os

# Disable debugger warnings from IPython frozen modules
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
# Disable tensorflow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from os.path import exists
from os.path import join
from os.path import splitext
from os.path import expanduser

import sys

import logging
import traceback

import ctypes

import argparse

# fix Qt crash on macOS BigSur platform
if sys.platform == 'darwin':
    os.environ["QT_MAC_WANTS_LAYER"] = "1"

from vtk import vtkObject

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.gui.dialogSplash import DialogSplash

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import qInstallMessageHandler
from PyQt5.QtCore import QtMsgType
from PyQt5.QtCore import QMessageLogContext
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

if sys.platform == 'win32':
    import pywinstyles
    import qdarktheme

from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.core.sisypheSettings import initPySisypheUserPath

"""
PySisyphe main

Last revision: 13/03/2025
"""

BACKGROUND: QColor | None = None
PALETTE: QPalette | None = None

"""
functions
~~~~~~~~~

    - getPalette
    - getBackgroundAsQColor
    - getBackgroundAsStr
    - getForegroundAsQColor
    - getForegroundAsStr
    - qtMessageHandler
    
"""

def getPalette() -> QPalette:
    return PALETTE

def getBackgroundAsQColor() -> QColor:
    return PALETTE.base().color()

def getBackgroundAsStr() -> str:
    cl = PALETTE.base().color()
    return '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())

def getForegroundAsQColor() -> QColor:
    return PALETTE.button().color()

def getForegroundAsStr() -> str:
    cl = PALETTE.button().color()
    return '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())

def updateWindowTitleBarColor(window):
    if sys.platform == 'win32':
        pywinstyles.change_header_color(window, getBackgroundAsStr())
        QApplication.processEvents()

# noinspection PyUnusedLocal,PyShadowingBuiltins
def qtMessageHandler(type: QtMsgType, context: QMessageLogContext, msg: str):
    # disable qt stdout warnings to avoid console output in frozen code
    pass

# < Revision 04/07/2025
# Global management of uncaught exceptions
# Display a dialog box and log the traceback
# noinspection PyUnusedLocal
def globalExceptionHandler(tp, value, tb):
    messageBox(None,
               'PySisyphe uncaught exception',
               '{}\nSee PySisyphe.log for traceback details.'.format(str(value)))
    stack = traceback.format_list(traceback.extract_stack())
    summary = traceback.format_list(traceback.extract_tb(tb))
    if len(summary) > 0: summary = summary[0]
    else: summary = ''
    if len(stack) > 1: msg = ''.join(stack[:-1])
    else: msg = ''
    logging.error('{}{}  {}'.format(msg, summary, str(value)))
# Revision 04/07/2025 >

if __name__ == "__main__":

    """
    Disable Qt, vtk and python console stdout
    """

    # < Revision 20/02/2025
    # redirect python stdout and stderr to null file to avoid console output in frozen code
    # if sys.stdout is None: sys.stdout = open(os.devnull, 'w')
    # if sys.stderr is None: sys.stderr = open(os.devnull, 'w')
    # sys.stdout = open(os.devnull, 'w')
    # sys.stderr = open(os.devnull, 'w')
    # Revision 20/02/2025 >

    # < Revision 03/03/2025
    # disable qt stdout warnings to avoid console output in frozen code
    qInstallMessageHandler(qtMessageHandler)
    # Revision 03/03/2025 >

    # < Revision 19/03/2025
    # disable vtk stdout warnings to avoid console output in frozen code
    # noinspection PyArgumentList
    vtkObject.GlobalWarningDisplayOff()
    # Revision 19/03/2025 >

    """
    Parse input arguments
    """

    parser = argparse.ArgumentParser()
    parser.add_argument('-o', '--open', help='Open PySisyphe volume (*.xvol)', nargs="*", type=str)
    args = parser.parse_args()

    """
    Logging
    """
    userdir = join(expanduser('~'), '.PySisyphe')
    if not exists(userdir): initPySisypheUserPath()
    filename = join(userdir, 'PySisyphe.log')
    logging.basicConfig(filename=filename,
                        encoding='utf-8',
                        filemode='w',
                        level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s\n%(message)s')
    logger = logging.getLogger(__name__)

    """
    Create application
    """
    from Sisyphe.gui.windowSisyphe import WindowSisyphe

    app = QApplication(sys.argv)
    # < Revision 18/02/2025
    QApplication.setApplicationName('PySisyphe')
    QApplication.setWindowIcon(QIcon(join(WindowSisyphe.getDefaultIconDirectory(), 'pysisyphe.png')))
    # Revision 18/02/2025 >

    sys.excepthook = globalExceptionHandler

    # < Revision 07/12/2024
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    # Revision 07/12/2024 >

    # noinspection PyTypeChecker
    QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    # noinspection PyTypeChecker
    QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, False)

    if sys.platform == 'win32':
        # High DPI scaling bugfix
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
        # Set theme
        PALETTE = qdarktheme.load_palette('auto')
        c = ('background-color: {0}; '
             'border-color: {0}; '
             'border: 0px;').format(getBackgroundAsStr())
        qss = 'QToolBar { ' + c + ' }'
        c = ('border-color: {0}; '
             'border: 0px; '
             'spacing: 20px;').format(getBackgroundAsStr())
        qss += ' QMenuBar { ' + c + ' }'
        c = ('border-style: solid; '
             'border-radius: 10px; '
             'border-width: 1px; '
             'border-color: {0};').format(getForegroundAsStr())
        qss += ' QMenu { ' + c + ' }'
        qss += ' QToolTip { color: #000000; background-color: #FFFFE0; border: 0px; font-size: 8pt; }'
        c = 'border-style: none; background-color: {0};'.format(getBackgroundAsStr())
        qss += ' QStatusBar { ' + c + ' }'
        # qss += ' QCheckBox, QComboBox, QLabel, QLineEdit, QPushButton, QListWidget, QTreeWidget { margin: 5px; }'
        qss += ' QCheckBox, QComboBox, QLineEdit, QPushButton, QListWidget, QTreeWidget { margin: 5px; }'
        qss += ' QGroupBox { margin: 5px; font-size: 8pt; font-weight: normal; }'
        qss += ' QPushButton#RoundedButton { margin: 0px; }'
        qss += ' QPushButton#iconPushButton { margin: 0px; }'
        qss += ' QLabel#iconButton { margin: 0px; }'
        qss += ' QLabel#colorPushButton { margin: 0px; }'
        qss += ' QLabel#visibilityButton { margin: 0px; }'
        qss += ' QLabel#lockButton { margin: 0px; }'
        qss += ' QLabel#opacityButton { margin: 0px; }'
        qss += ' QLabel#widthButton { margin: 0px; }'
        qss += ' QLabel#widthButton { margin: 0px; }'
        qdarktheme.setup_theme('auto', corner_shape='rounded', additional_qss=qss)
    else:
        PALETTE = app.palette()
        # Qt bug fix, lost macOS style when button height > 30px
        app.setStyleSheet('QPushButton { max-height: 30px; }')

    """
    Set up main window
    """

    splash = DialogSplash()
    if sys.platform == 'win32': updateWindowTitleBarColor(splash)
    splash.buttonVisibilityOff()
    splash.progressBarVisibilityOn()
    splash.show()

    main = WindowSisyphe(splash)
    if sys.platform == 'win32': updateWindowTitleBarColor(main)
    splash.close()

    if args.open is not None:
        for filename in args.open:
            if exists(filename):
                if splitext(filename)[1] == SisypheVolume.getFileExt():
                    main.open(filename)

    logger.info('session start')
    sys.exit(app.exec_())
