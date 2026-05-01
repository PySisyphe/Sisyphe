"""
External packages/modules
-------------------------

    - Matplotlib, Graph tool, https://matplotlib.org/
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
    - PyQtDarkTheme, dark theme management for win32 platform, https://pyqtdarktheme.readthedocs.io/en/stable/index.html
    - pywinstyles, customize window title bar for win32 platform, https://github.com/Akascape/py-window-styles
    - vtk, visualization, https://vtk.org/
"""

# < Revision 21/06/2025
# enable support for multiprocessing in frozen code
from multiprocessing import freeze_support
freeze_support()
# Revision 21/06/2025 >

import sys
import ctypes

import os
from os import mkdir
from os.path import exists
from os.path import join
from os.path import splitext
from os.path import dirname
from os.path import basename
from os.path import expanduser
from os.path import abspath

# Disable IPython warnings
os.environ['PYDEVD_DISABLE_FILE_VALIDATION'] = '1'
# Disable tensorflow warnings
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

if sys.platform == 'darwin':
    # fix Qt crash on macOS BigSur platform
    os.environ['QT_MAC_WANTS_LAYER'] = '1'
    # Fix matplotlib crash when scanning X11 fonts
    os.environ['X11_PREFERENCE'] = '0'
elif sys.platform == 'win32':
    # Fix PyTorch DLL loading issue on Windows
    # < Revision 23/04/2026
    from importlib.util import find_spec
    try:
        if (spec := find_spec('torch')) and spec.origin and os.path.exists(dll_path := os.path.join(os.path.dirname(spec.origin), 'lib', 'c10.dll')):
            ctypes.CDLL(os.path.normpath(dll_path))
    except Exception: pass
    # Revision 23/04/2026 >
    # < Revision 10/01/2026
    # Force console hide for Windows Terminal compatibility (PyInstaller console=True)
    if hasattr(sys, '_MEIPASS'):
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            # 0 = SW_HIDE
            user32.ShowWindow(hWnd, 0)
    # Revision 10/01/2026 >

# < Revision 10/01/2026
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
# Revision 10/01/2026 >

import traceback


# < Revision 30/04/2026
mpl_cache_dir = abspath(join(expanduser('~'), '.matplotlib'))
if not exists(mpl_cache_dir): mkdir(mpl_cache_dir)
os.environ['MPLCONFIGDIR'] = mpl_cache_dir

import Sisyphe
from glob import glob
fontlist_filename = glob(join(mpl_cache_dir, 'fontlist-v*.json'))
tag = exists(join(dirname(Sisyphe.__file__), 'tag'))
if len(fontlist_filename) == 0 or tag:
    import json
    path = join(dirname(Sisyphe.__file__), 'gui', 'font')
    filename = join(path, 'template.json')
    if exists(filename):
        with open(filename, 'r') as f:
            fontlist = json.load(f)
        for font in fontlist['ttflist']:
            fname = basename(font['fname'])
            font['fname'] = join(path, fname)
        fontlist_filename = join(mpl_cache_dir, 'fontlist-v{}.json'.format(fontlist['_version']))
        with open(fontlist_filename, 'w') as f:
            json.dump(fontlist, f, indent=4)

import matplotlib
matplotlib.use('Qt5Agg')
# Revision 30/04/2026 >

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QLocale
from PyQt5.QtCore import qInstallMessageHandler
from PyQt5.QtCore import QtMsgType
from PyQt5.QtCore import QMessageLogContext
from PyQt5.QtCore import QUrl
from PyQt5.QtCore import QEvent
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QPalette
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication

if sys.platform == 'win32':
    # noinspection PyUnresolvedReferences
    import pywinstyles
    # noinspection PyUnresolvedReferences
    import qdarktheme

from vtk import vtkObject

from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.core.sisypheSettings import initPySisypheUserPath
from Sisyphe.gui.dialogSplash import DialogSplash

"""
PySisyphe main

Last revision: 16/03/2026
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
    - updateWindowTitleBarColor
    - qtMessageHandler
    - globalExceptionHandler

Class
~~~~~

    - QApplicationEventHandler
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
    # < Revision 13/07/2025
    # Close wait dialog if it exists
    for w in QApplication.topLevelWindows():
        if w.objectName() == 'DialogWaitWindow':
            w.close()
    # Revision 13/07/2025 >
    # < Revision 16/03/2026
    if tp.__name__ == 'UserAbortException': return
    # Revision 16/03/2026 >
    try: messageBox(None,
                    'PySisyphe uncaught exception',
                    '{}\nSee PySisyphe.log for traceback details.'.format(str(value)))
    except: pass
    msg = ''.join(traceback.format_exception(tp, value, tb))
    try: logging.error(msg)
    except:
        sys.stderr.write(msg)
        sys.stderr.flush()

# Revision 04/07/2025 >

sys.excepthook = globalExceptionHandler

# < Revision 22/07/2025
# add QApplicationEventHandler class
class QApplicationEventHandler(QApplication):

    openFileRequest = pyqtSignal(QUrl, name='openFileRequest')

    def event(self, event):
        # noinspection PyUnresolvedReferences
        if event.type() == QEvent.FileOpen:
            # noinspection PyUnresolvedReferences
            self.openFileRequest.emit(event.url())
            return True
        return super().event(event)
# Revision 22/07/2025 >


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
    Windows registry
    """

    # < Revision 22/07/2025
    # Windows registry management
    if sys.platform == 'win32':
        if hasattr(sys, '_MEIPASS'):
            # noinspection PyProtectedMember
            path = dirname(sys.executable)
            # Set file type associations in Windows registry
            import winreg
            from Sisyphe.version import getVersion
            try:
                # key exists, PySisyphe is already installed
                winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,r'Software\\Classes\\Applications\\PySisyphe')
                flag = False
            except:
                # key does not exist, PySisyphe is already installed
                flag = True
            # Install PySisyphe Windows registry
            if flag:
                try:
                    root = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,r'Software\\Classes\\Applications')
                    k = winreg.CreateKey(root, r'PySisyphe.exe')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\ApplicationCompany')
                    winreg.SetValue(root, r'PySisyphe.exe\\ApplicationCompany', winreg.REG_SZ, 'PySisyphe')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\FriendlyAppName')
                    winreg.SetValue(root, r'PySisyphe.exe\\FriendlyAppName', winreg.REG_SZ, 'PySisyphe')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\Path')
                    winreg.SetValue(root, r'PySisyphe.exe\\Path', winreg.REG_SZ, path)
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\Version')
                    winreg.SetValue(root, r'PySisyphe.exe\\Version', winreg.REG_SZ, getVersion())
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\Capabilities')
                    winreg.SetValueEx(k, 'ApplicationDescription', 0, winreg.REG_SZ, 'PySisyphe neuroimaging software')
                    winreg.SetValueEx(k, 'ApplicationName', 0, winreg.REG_SZ, 'PySisyphe')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\shell')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\shell\\open')
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\shell\\open\\command')
                    v = '\"{}\" \"%1\"'.format(sys.executable)
                    winreg.SetValue(root, r'PySisyphe.exe\\shell\\open\\command', winreg.REG_SZ, v)
                    if k: winreg.CloseKey(k); k = None
                    k = winreg.CreateKey(root, r'PySisyphe.exe\\SupportedTypes')
                    winreg.SetValue(root, r'PySisyphe.exe\\SupportedTypes', winreg.REG_SZ, '.xvol')
                    if k: winreg.CloseKey(k); k = None
                    if root: winreg.CloseKey(root)
                except: pass
            # Update PySisyphe Windows registry
            else:
                try:
                    root = winreg.OpenKeyEx(winreg.HKEY_CURRENT_USER,r'Software\\Classes\\Applications\\PySisyphe.exe')
                    # Update path and shell command
                    rpath = winreg.QueryValue(root, r'Path')
                    if path != rpath:
                        winreg.SetValue(root, r'Path', winreg.REG_SZ, path)
                        v = '\"{}\" \"%1\"'.format(sys.executable)
                        winreg.SetValue(root, r'PySisyphe.exe\\shell\\open\\command', winreg.REG_SZ, v)
                    if root: winreg.CloseKey(root)
                    # Update version
                    rversion = winreg.QueryValue(root, r'Version')
                    if rversion != getVersion(): winreg.SetValue(root, r'Version', winreg.REG_SZ, getVersion())
                except: pass
    # Revision 22/07/2025 >

    """
    Parse filename argument
    """

    filename = None
    args = sys.argv
    if len(args) > 1:
        filename = sys.argv[1]
        if exists(filename):
            ext = splitext(filename)[1]
            if ext != SisypheVolume.getFileExt(): filename = None

    """
    Create application
    """

    from Sisyphe.gui.windowSisyphe import WindowSisyphe

    # < Revision 22/07/2025
    if sys.platform == 'win32': app = QApplication(sys.argv)
    elif sys.platform == 'darwin': app = QApplicationEventHandler(sys.argv)
    else: sys.exit(0)
    # Revision 22/07/2025 >

    # < Revision 18/02/2025
    QApplication.setApplicationName('PySisyphe')
    QApplication.setWindowIcon(QIcon(join(WindowSisyphe.getDefaultIconDirectory(), 'pysisyphe.png')))
    # Revision 18/02/2025 >

    # < Revision 07/12/2024
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    # Revision 07/12/2024 >

    # noinspection PyTypeChecker,PyUnresolvedReferences
    QApplication.setAttribute(Qt.AA_DontShowIconsInMenus, True)
    # noinspection PyTypeChecker,PyUnresolvedReferences
    QApplication.setAttribute(Qt.AA_DontUseNativeMenuBar, False)

    if sys.platform == 'win32':
        # High DPI scaling bugfix
        # noinspection PyUnresolvedReferences
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
    Logging
    PySisyphe.log file in ~/.PySisyphe
    """

    import logging
    userdir = abspath(join(expanduser('~'), '.PySisyphe'))
    if not exists(userdir): initPySisypheUserPath()
    filelog = join(userdir, 'PySisyphe.log')
    logging.basicConfig(filename=filelog,
                        encoding='utf-8',
                        filemode='w',
                        level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s\n%(message)s')
    logger = logging.getLogger(__name__)

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
    elif sys.platform == 'darwin':
        # noinspection PyUnresolvedReferences
        app.openFileRequest.connect(main.open)
    # < Revision 17/02/2026
    # use a persistent DialogSplash to avoid further creation
    # splash.close()
    splash.hide()
    # Revision 17/02/2026 >

    # < Revision 23/04/2026
    main.versionControl()
    # Revision 23/04/2026 >

    if filename is not None:
        if exists(filename):
            try: main.open(filename)
            except: pass

    if logger is not None: logger.info('session start')
    app.exec_()

    if logger is not None: logger.info('session end')
    sys.exit(0)
