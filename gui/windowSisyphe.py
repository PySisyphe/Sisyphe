"""
External packages/modules
-------------------------

    - darkdetect, OS dark Mode detection, https://github.com/albertosottile/darkdetect
    - Matplotlib, plotting library, https://matplotlib.org/
    - Numpy, Scientific computing, https://numpy.org/
    - psutil, System utilities, https://github.com/giampaolo/psutil
    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os import mkdir
from os import chdir
from os import getcwd
from os import remove

from os.path import join
from os.path import isdir
from os.path import dirname
from os.path import abspath
from os.path import exists
from os.path import splitext
from os.path import basename
from os.path import expanduser

import importlib
import subprocess
import logging
import traceback

from psutil import virtual_memory

from pathlib import Path

from glob import glob

from shutil import rmtree

from zipfile import ZipFile
from zipfile import is_zipfile

from matplotlib import font_manager

from numpy import stack
from numpy import nanmean
from numpy import nanmedian
from numpy import nanstd
from numpy import nanmax
from numpy import nanmin

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtGui import QFont
from PyQt5.QtGui import QIcon
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtGui import QKeySequence
from PyQt5.QtGui import QFontDatabase
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenuBar
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QStatusBar
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox

import darkdetect

from Sisyphe import version
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.core.sisypheConstants import removeAllPrefixesFromFilename
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheImageAttributes import SisypheAcquisition
from Sisyphe.core.sisypheRecent import SisypheRecent
from Sisyphe.core.sisypheROI import SisypheROIDraw
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheSettings import initPySisypheUserPath
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.core.sisypheFiducialBox import SisypheFiducialBox
from Sisyphe.gui.dialogFileSelection import DialogFileSelection
from Sisyphe.gui.dialogFileSelection import DialogFilesSelection
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.gui.dialogSplash import DialogSplash
from Sisyphe.gui.dialogSettings import DialogSettings
from Sisyphe.widgets.consoleWidget import ConsoleWidget
from Sisyphe.widgets.databaseWidget import DatabaseWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
from Sisyphe.widgets.tabToolsWidgets import TabROIListWidget
from Sisyphe.widgets.tabToolsWidgets import TabMeshListWidget
from Sisyphe.widgets.tabToolsWidgets import TabTargetListWidget
from Sisyphe.widgets.tabToolsWidgets import TabROIToolsWidget
from Sisyphe.widgets.tabToolsWidgets import TabTrackingWidget
from Sisyphe.widgets.tabToolsWidgets import TabHelpWidget
from Sisyphe.widgets.attributesWidgets import ItemAttributesWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalSliceTrajectoryViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarMultiSliceGridViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarSynchronisedGridViewWidget
from Sisyphe.widgets.multiComponentViewWidget import IconBarMultiComponentViewWidget
from Sisyphe.widgets.projectionViewWidget import IconBarMultiProjectionViewWidget

# noinspection PyCompatibility
import __main__
from PyQt5.QtWidgets import QApplication

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QMainWindow -> WindowSisyphe
"""


class WindowSisyphe(QMainWindow):
    """
    Description
    ~~~~~~~~~~~

    Main window of the PySisyphe application.

    Inheritance
    ~~~~~~~~~~~

    QMainWindow ->   WindowSisyphe

    Last revision: 07/07/2025
    """

    # Class constants

    _ICONSIZE = 32
    _THUMBNAILSIZE = 96
    _TOOLBARICONSIZE = 16

    # Class methods

    @classmethod
    def getVersion(cls) -> str:
        return version.__version__

    @classmethod
    def isDarkMode(cls) -> bool:
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls) -> bool:
        return darkdetect.isLight()

    @classmethod
    def getMemoryUsage(cls) -> str:
        m = virtual_memory()
        u = m.used
        p = m.percent
        s1 = 1024
        s2 = s1 * s1
        if u <= s1: u = '{} Bytes'.format(u)
        elif u <= s1: u = '{:.1f} KB'.format(u / s1)
        else: u = '{:.1f} MB'.format(u / s2)
        return 'Memory usage {} ({:.1f}%)'.format(u, p)

    @classmethod
    def getMainDirectory(cls) -> str:
        import Sisyphe
        return dirname(abspath(Sisyphe.__file__))

    @classmethod
    def getDefaultIconDirectory(cls) -> str:
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkicons')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lighticons')

    @classmethod
    def getUserDirectory(cls) -> str:
        userdir = join(expanduser('~'), '.PySisyphe')
        if not exists(userdir): initPySisypheUserPath()
        return userdir

    # Special method

    """
    Private attributes

    _rois           Sisyphe.sisypheROI.SisypheROICollection
    _draw           Sisyphe.sisypheROI.SisypheROIDraw
    _recent         Sisyphe.sisypheRecent.SisypheRecent
    _action         dict[PyQt5.QtWidgets.QAction]
    _menu           dict[PyQt5.QtWidgets.QMenu]
    _menubar        PyQt5.QtWidgets.QMenuBar
    _splitter       PyQt5.QtWidgets.QSplitter
    _toolbar        PyQt5.QtWidgets.QToolBar
    _thumbnail      Sisyphe.widgets.toolBarThumbnail.ToolBarThumbnail
    _dock           PyQt5.QtWidgets.QTabWidget
    _views          Sisyphe.widgets.iconBarViewWidgets.IconBarViewWidgetCollection
    _sliceview      Sisyphe.widgets.iconBarViewWidgets.IconBarMultiSliceGridViewWidget
    _orthoview      Sisyphe.widgets.iconBarViewWidgets.IconBarOrthogonalSliceTrajectoryViewWidget
    _synchroview    Sisyphe.widgets.iconBarViewWidgets.IconBarSynchronisedGridViewWidget
    _projview       Sisyphe.widgets.projectionViewWidget.IconBarMultiProjectionViewWidget
    _compview       Sisyphe.widgets.multiComponentViewWidget.IconBarMultiComponentViewWidget
    _database       Sisyphe.widgets.databaseWidget.DatabaseWidget
    _console        Sisyphe.widgets.consoleWidget.ConsoleWidget
    _captures       Sisyphe.widgets.screenshotsGridWidget.ScreenshotsGridWidget
    _tabROIList     Sisyphe.widgets.tabToolsWidgets.TabROIListWidget
    _tabROITools    Sisyphe.widgets.tabToolsWidgets.TabROIToolsWidget
    _tabMeshList    Sisyphe.widgets.tabToolsWidgets.TabMeshListWidget
    _tabTargetList  Sisyphe.widgets.tabToolsWidgets.TabTargetListWidget
    _tabTrackingListSisyphe.widgets.tabToolsWidgets.TabTrackingWidget
    _tabHelp        TabHelpWidget
    _tabview        PyQt5.QtWidgets.QTabWidget
    _status         PyQt5.QtWidgets.QStatusBar
    _statuslabel    PyQt5.QtWidgets.QLabel
    _settings       Sisyphe.sisypheSettings.SisypheSettings
    _logger         logging.Logger
    """

    def __init__(self, splash: DialogSplash | None = None) -> None:
        super().__init__()

        # < Revision 01/07/2025
        self._logger = logging.getLogger(__name__)
        # Revision 01/07/2025 >

        if splash is not None:
            splash.getProgressBar().setRange(0, 17)
            splash.setMessage('Main window initialization...')
            splash.setProgressBarVisibility(True)

        self._splitter = QSplitter(parent=self)
        self.setCentralWidget(self._splitter)

        # Central widget

        self._tabview = QTabWidget(parent=self._splitter)
        self._splitter.addWidget(self._tabview)

        self._settings = SisypheSettings()
        self._views = IconBarViewWidgetCollection()
        self._draw = SisypheROIDraw()
        self._rois = SisypheROICollection()

        if splash is not None:
            splash.getProgressBar().setValue(1)
            splash.setMessage('Slice view initialization...')
        self._sliceview = IconBarMultiSliceGridViewWidget(parent=self._tabview, rois=self._rois, draw=self._draw)
        self._sliceview.setName('slices')
        self._sliceview.setFullscreenButtonAvailability(True)

        if splash is not None:
            splash.getProgressBar().setValue(2)
            splash.setMessage('Orthogonal view initialization...')
        self._orthoview = IconBarOrthogonalSliceTrajectoryViewWidget(parent=self._tabview)
        self._orthoview.setName('orthogonal')
        self._orthoview.setFullscreenButtonAvailability(True)

        if splash is not None:
            splash.getProgressBar().setValue(3)
            splash.setMessage('Synchronized view initialization...')
        self._synchroview = IconBarSynchronisedGridViewWidget(parent=self._tabview, rois=self._rois, draw=self._draw)
        self._synchroview.setName('synchronised')
        self._synchroview.setFullscreenButtonAvailability(True)

        if splash is not None:
            splash.getProgressBar().setValue(4)
            splash.setMessage('Projection view initialization...')
        self._projview = IconBarMultiProjectionViewWidget(parent=self._tabview)
        self._projview.setName('projections')
        self._projview.setFullscreenButtonAvailability(True)

        if splash is not None:
            splash.getProgressBar().setValue(5)
            splash.setMessage('Multi-component view initialization...')
        self._compview = IconBarMultiComponentViewWidget(parent=self._tabview)
        self._compview.setName('components')
        self._compview.setFullscreenButtonAvailability(True)

        if splash is not None:
            splash.getProgressBar().setValue(6)
            splash.setMessage('Database widget initialization...')
        self._database = DatabaseWidget(parent=self._tabview)
        self._database.setMainWindow(self)

        if splash is not None:
            splash.getProgressBar().setValue(7)
            splash.setMessage('Console widget initialization...')
        self._console = ConsoleWidget(parent=self._tabview)
        self._console.setMainWindow(self)

        if splash is not None:
            splash.getProgressBar().setValue(8)
            splash.setMessage('Screenshots widget initialization...')
        self._captures = ScreenshotsGridWidget(parent=self._tabview)

        self._views.append(self._sliceview)
        self._views.append(self._orthoview)
        self._views.append(self._synchroview)
        self._views.append(self._projview)
        self._views.append(self._compview)
        self._tabview.addTab(self._sliceview, 'Slice view')
        self._tabview.addTab(self._orthoview, 'Orthogonal view')
        self._tabview.addTab(self._synchroview, 'Synchronized view')
        self._tabview.addTab(self._projview, 'Projection view')
        self._tabview.addTab(self._compview, 'Multi-component view')
        self._tabview.addTab(self._database, 'Database')
        self._tabview.addTab(self._captures, 'Screenshots')
        self._tabview.addTab(self._console, 'IPython')
        self._tabview.setTabPosition(QTabWidget.South)
        # noinspection PyUnresolvedReferences
        self._tabview.currentChanged.connect(self.updateTimers)

        self._dialog = None
        self._recent = SisypheRecent()
        self._recent.load()

        # Menu bar

        if splash is not None:
            splash.getProgressBar().setValue(9)
            splash.setMessage('Menu bar initialization...')
        self._action = dict()
        self._menu = dict()
        self._menuView = list()
        self._menubar = QMenuBar(parent=self)
        if platform == 'win32':
            self.setMenuBar(self._menubar)
            # self._menubar.setStyleSheet('spacing: 20')
        self._menubar.setNativeMenuBar(True)
        self._initMenuBar()
        # < Revision 16/10/2024
        self.hideViewWidgets()
        # Revision 16/10/2024 >

        # Tool bar

        if platform == 'darwin':
            self.setStyleSheet('QToolBar { border-style: none; } '
                               'QStatusBar { border-style: none; }')

        if splash is not None:
            splash.getProgressBar().setValue(10)
            splash.setMessage('Tool bar initialization...')
        self._toolbar = QToolBar(parent=self)
        self._initToolBar()
        self._action['toolbar'].toggled.connect(self._toolbar.setVisible)

        # Thumbnail dock widget

        v = self._settings.getFieldValue('GUI', 'ThumbnailSize')
        if v is None: v = self._THUMBNAILSIZE
        self._thumbnail = ToolBarThumbnail(size=v, mainwindow=self, views=self._views, parent=self)
        # noinspection PyTypeChecker
        self.addToolBar(Qt.TopToolBarArea, self._thumbnail)
        self._sliceview.setThumbnail(self._thumbnail)
        self._orthoview.setThumbnail(self._thumbnail)
        self._synchroview.setThumbnail(self._thumbnail)
        self._projview.setThumbnail(self._thumbnail)
        self._compview.setThumbnail(self._thumbnail)
        self._action['thumb'].toggled.connect(self._thumbnail.setVisible)

        # Tools dock widget

        v = self._settings.getFieldValue('GUI', 'IconSize')
        if v is None: v = self._ICONSIZE
        self._dock = QTabWidget(parent=self._splitter)
        self._dock.setTabPosition(QTabWidget.West)
        self._splitter.addWidget(self._dock)

        if splash is not None:
            splash.getProgressBar().setValue(11)
            splash.setMessage('ROI dock initialization...')
        self._tabROIList = TabROIListWidget(parent=self._dock)
        self._tabROIList.setContentsMargins(10, 10, 10, 10)
        self._tabROIList.setViewCollection(self._views)
        self._tabROIList.setEnabled(False)
        self._tabROIList.setIconSize(v)
        # < Revision 02/11/2024
        # set max number of ROIs
        c = self._settings.getFieldValue('ROI', 'MaxCount')
        if c is None: c = 10
        self._tabROIList.setMaxCount(c)
        # Revision 02/11/2024 >
        self._dock.addTab(self._tabROIList, 'ROI')

        if splash is not None:
            splash.getProgressBar().setValue(12)
            splash.setMessage('ROI tools dock initialization...')
        self._tabROITools = TabROIToolsWidget(parent=self._dock)
        self._tabROITools.setContentsMargins(10, 10, 10, 10)
        self._tabROITools.setViewCollection(self._views)
        self._tabROITools.setEnabled(False)
        self._tabROITools.setIconSize(v)
        self._dock.addTab(self._tabROITools, 'Brush')
        self._tabROITools.setVisible(False)

        if splash is not None:
            splash.getProgressBar().setValue(13)
            splash.setMessage('Mesh dock initialization...')
        self._tabMeshList = TabMeshListWidget(parent=self._dock)
        self._tabMeshList.setContentsMargins(10, 10, 10, 10)
        self._tabMeshList.setViewCollection(self._views)
        self._tabMeshList.getMeshListWidget().setScreenshotsWidget(self._captures)
        self._tabMeshList.setEnabled(False)
        self._tabMeshList.setIconSize(v)
        c = self._settings.getFieldValue('Mesh', 'MaxCount')
        if c is None: c = 20
        self._tabMeshList.setMaxCount(c)
        self._dock.addTab(self._tabMeshList, 'Mesh')

        if splash is not None:
            splash.getProgressBar().setValue(14)
            splash.setMessage('Target dock initialization...')
        self._tabTargetList = TabTargetListWidget(parent=self._dock)
        self._tabTargetList.setContentsMargins(10, 10, 10, 10)
        self._tabTargetList.setViewCollection(self._views)
        self._tabTargetList.getToolListWidget().setScreenshotsWidget(self._captures)
        self._tabTargetList.setEnabled(False)
        self._tabTargetList.setIconSize(v)
        c = self._settings.getFieldValue('Tools', 'MaxCount')
        if c is None: c = 20
        self._tabTargetList.setMaxCount(c)
        self._dock.addTab(self._tabTargetList, 'Target')

        if splash is not None:
            splash.getProgressBar().setValue(15)
            splash.setMessage('Tracking dock initialization...')
        self._tabTrackingList = TabTrackingWidget(parent=self._dock)
        self._tabTrackingList.setContentsMargins(10, 10, 10, 10)
        self._tabTrackingList.setViewCollection(self._views)
        self._tabTrackingList.getTrackingListWidget().setScreenshotsWidget(self._captures)
        self._tabTrackingList.setEnabled(False)
        self._tabTrackingList.setIconSize(v)
        c = self._settings.getFieldValue('Bundles', 'MaxCount')
        if c is None: c = 20
        self._tabTrackingList.setMaxCount(c)
        self._dock.addTab(self._tabTrackingList, 'Tracking')

        if splash is not None:
            splash.getProgressBar().setValue(16)
            splash.setMessage('Help dock initialization...')
        self._tabHelp = TabHelpWidget(parent=self._dock)
        self._tabHelp.setContentsMargins(10, 10, 10, 10)
        self._tabHelp.setEnabled(True)
        self._tabHelp.setIconSize(v)
        # < Revision 14/03/2025
        z = self._settings.getFieldValue('GUI', 'ZoomFactor')
        self._tabHelp.setZoomFactor(z)
        # Revision 14/03/2025 >
        self._dock.addTab(self._tabHelp, 'Doc')

        roiListWidget = self._tabROIList.getROIListWidget()
        meshListWidget = self._tabMeshList.getMeshListWidget()
        roiListWidget.setListMeshAttributeWidget(meshListWidget)
        meshListWidget.setListROIAttributeWidget(roiListWidget)
        self._tabTrackingList.getTrackingListWidget().setListROIAttributeWidget(roiListWidget)
        self._tabTrackingList.getTrackingListWidget().setListMeshAttributeWidget(meshListWidget)
        self._action['dock'].triggered.connect(self.setDockVisibility)
        self._dock.setTabVisible(1, False)
        # < Revision 16/10/2024
        self.setDockEnabled(False)
        # Revision 16/10/2024 >

        # Status bar

        self._status = self.statusBar()
        self._statuslabel = QLabel(self.getMemoryUsage())
        # < Revision 07/03/2025
        if platform == 'darwin':
            font = QFont('Arial', 10)
            self._status.setFont(font)
            self._statuslabel.setFont(font)
        # Revision 07/03/2025 >
        self._status.addPermanentWidget(self._statuslabel)
        self._action['status'].toggled.connect(self._status.setVisible)

        # Font settings

        family = self._settings.getFieldValue('GUI', 'FontFamily')
        if family is None: family = self.font().defaultFamily()
        size = self._settings.getFieldValue('GUI', 'FontSize')
        if size is None: size = 12
        self.setApplicationFont(family, size)

        # Dialog settings initialization

        if splash is not None:
            splash.getProgressBar().setValue(17)
            splash.setMessage('Settings dialog initialization...')
        self._dialogSettings = DialogSettings()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialogSettings)
            except: pass
        self._dialogSettings.setMainWindow(self)

        # Main window

        self.setWindowTitle('PySisyphe')
        if platform == 'darwin':
            self.setUnifiedTitleAndToolBarOnMac(False)
        self.resize(QApplication.primaryScreen().availableSize())
        self.move(0, 0)
        self.show()
        # noinspection PyTypeChecker
        self.setWindowState(Qt.WindowMaximized)
        width = ItemAttributesWidget.getDefaultMinimumWidth() + 80
        self._splitter.setSizes([sum(self._splitter.sizes()) - width, width])

    # Private methods

    def _initMenuBar(self) -> None:

        # Icons

        icpath = self.getDefaultIconDirectory()
        icquit = QIcon(join(icpath, 'exit.png'))
        icpref = QIcon(join(icpath, 'settings.png'))
        icabout = QIcon(join(icpath, 'about.png'))

        # Actions

        self._action['about'] = QAction(icabout, 'About')
        self._action['pref'] = QAction(icpref, 'Preferences...')
        self._action['exit'] = QAction(icquit, 'Quit')

        self._action['pref'].setShortcut(QKeySequence.Preferences)
        self._action['exit'].setShortcut(QKeySequence.Quit)

        # Mac os
        if platform == 'darwin':
            self._action['about'].setMenuRole(QAction.AboutRole)
            self._action['pref'].setMenuRole(QAction.PreferencesRole)
            self._action['exit'].setMenuRole(QAction.QuitRole)

        # Init Menus

        self._initFileMenu()
        self._initFunctionsMenu()
        self._initRegistrationMenu()
        self._initSegmentationMenu()
        self._initMapMenu()
        self._initDiffusionMenu()
        self._initViewsMenu()
        self._initWindowMenu()

    def _initFileMenu(self) -> None:
        self._menu['file'] = self._menubar.addMenu('File')
        self._menu['file'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['file'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['file'].setAttribute(Qt.WA_TranslucentBackground, True)

        # Icons

        icpath = self.getDefaultIconDirectory()
        icload = QIcon(join(icpath, 'open.png'))
        icsave = QIcon(join(icpath, 'save.png'))
        icsaveall = QIcon(join(icpath, 'saveall.png'))
        icclose = QIcon(join(icpath, 'close.png'))
        iccloseall = QIcon(join(icpath, 'closeall.png'))
        icexport = QIcon(join(icpath, 'export.png'))
        icimport = QIcon(join(icpath, 'importdcm.png'))
        icattr = QIcon(join(icpath, 'list.png'))
        icid = QIcon(join(icpath, 'id.png'))
        icano = QIcon(join(icpath, 'anonymize.png'))
        iclabel = QIcon(join(icpath, 'labels.png'))
        iclut = QIcon(join(icpath, 'rgb.png'))
        icdown = QIcon(join(icpath, 'download.png'))
        icupdate = QIcon(join(icpath, 'update.png'))
        icimportnii = QIcon(join(icpath, 'importnii.png'))
        icimportmnc = QIcon(join(icpath, 'importmnc.png'))
        icimportnrrd = QIcon(join(icpath, 'importnrrd.png'))
        icimportvtk = QIcon(join(icpath, 'importvtk.png'))
        icimportvol = QIcon(join(icpath, 'importvol.png'))
        icopennii = QIcon(join(icpath, 'open-nii.png'))
        icopenmnc = QIcon(join(icpath, 'open-mnc.png'))
        icopenmgh = QIcon(join(icpath, 'open-mgh.png'))
        icopennrrd = QIcon(join(icpath, 'open-nrrd.png'))
        icopenvtk = QIcon(join(icpath, 'open-vtk.png'))
        icopenvol = QIcon(join(icpath, 'open-vol.png'))
        icopenvmr = QIcon(join(icpath, 'open-vmr.png'))
        icosavenii = QIcon(join(icpath, 'save-nii.png'))
        icosavenpy = QIcon(join(icpath, 'save-npy.png'))
        icosavemnc = QIcon(join(icpath, 'save-mnc.png'))
        icosavenrrd = QIcon(join(icpath, 'save-nrrd.png'))
        icosavevtk = QIcon(join(icpath, 'save-vtk.png'))

        # Actions

        self._action['open'] = self._menu['file'].addAction(icload, 'Open...')
        self._menu['template'] = self._menu['file'].addMenu('Open template...')
        self._menu['template'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['template'].triggered.connect(self._openTemplate)
        self._initTemplateMenu()
        submenu = self._menu['file'].addMenu('Open from format')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['opennii'] = submenu.addAction(icopennii, 'Open Nifti...')
        self._action['opennrrd'] = submenu.addAction(icopennrrd, 'Open Nrrd...')
        self._action['openmnc'] = submenu.addAction(icopenmnc, 'Open Minc...')
        self._action['openmgh'] = submenu.addAction(icopenmgh, 'Open FreeSurfer MGH...')
        self._action['openvol'] = submenu.addAction(icopenvol, 'Open Sisyphe...')
        self._action['openvmr'] = submenu.addAction(icopenvmr, 'Open BrainVoyager VMR...')
        self._action['openvtk'] = submenu.addAction(icopenvtk, 'Open VTK...')

        self._menu['recent'] = self._menu['file'].addMenu('Recent files...')
        self._menu['recent'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['recent'].aboutToShow.connect(self._updateRecentMenu)
        self._menu['recent'].triggered.connect(self._openRecent)

        self._action['user'] = self._menu['file'].addAction('Open user folder')

        self._menu['file'].addSeparator()
        self._action['save'] = self._menu['file'].addAction(icsave, 'Save')
        self._action['save'].setToolTip('Save reference volume')
        self._action['saveall'] = self._menu['file'].addAction(icsaveall, 'Save all')
        self._action['saveas'] = self._menu['file'].addAction(icsave, 'Save As...')
        submenu = self._menu['file'].addMenu('Save to format')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['savenii'] = submenu.addAction(icosavenii, 'Save Nifti...')
        self._action['savenpy'] = submenu.addAction(icosavenpy, 'Save Numpy...')
        self._action['savenrrd'] = submenu.addAction(icosavenrrd, 'Save Nrrd...')
        self._action['savemnc'] = submenu.addAction(icosavemnc, 'Save Minc...')
        self._action['savevtk'] = submenu.addAction(icosavevtk, 'Save VTK...')

        self._action['close'] = self._menu['file'].addAction(icclose, 'Close')
        self._action['close'].setToolTip('Close reference volume')
        self._action['closeall'] = self._menu['file'].addAction(iccloseall, 'Close All')

        self._menu['file'].addSeparator()
        self._menu['file'].addAction(self._action['pref'])

        self._menu['file'].addSeparator()
        self._action['download'] = self._menu['file'].addAction(icdown, 'Download manager...')
        self._action['update'] = self._menu['file'].addAction(icupdate, 'Check for update...')

        self._menu['file'].addSeparator()
        self._action['editattr'] = self._menu['file'].addAction(icattr, 'Edit Attributes...')
        self._action['editid'] = self._menu['file'].addAction(icid, 'ID replacement...')
        self._action['anonymize'] = self._menu['file'].addAction(icano, 'Anonymize...')
        self._action['editlabels'] = self._menu['file'].addAction(iclabel, 'Edit volume labels...')
        self._action['roi2label'] = self._menu['file'].addAction('ROIs to label volume...')
        self._action['vol2label'] = self._menu['file'].addAction('Volumes to label volume...')
        self._action['label2roi'] = self._menu['file'].addAction('Label volume to ROIs...')

        self._menu['file'].addSeparator()
        submenu = self._menu['file'].addMenu('Import')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['importnifti'] = submenu.addAction(icimportnii, 'Import Nifti...')
        self._action['importminc'] = submenu.addAction(icimportmnc, 'Import Minc...')
        self._action['importnrrd'] = submenu.addAction(icimportnrrd, 'Import Nrrd...')
        self._action['importvtk'] = submenu.addAction(icimportvtk, 'Import Vtk...')
        self._action['importsis'] = submenu.addAction(icimportvol, 'Import Sisyphe (*.vol)...')
        submenu = self._menu['file'].addMenu('Export')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['exportnifti'] = submenu.addAction(icexport, 'Export Nifti...')
        self._action['exportminc'] = submenu.addAction(icexport, 'Export Minc...')
        self._action['exportnrrd'] = submenu.addAction(icexport, 'Export Nrrd...')
        self._action['exportvtk'] = submenu.addAction(icexport, 'Export Vtk...')
        self._action['exportnpy'] = submenu.addAction(icexport, 'Export Numpy...')
        submenu = self._menu['file'].addMenu('DICOM')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['dcmimport'] = submenu.addAction(icimport, 'DICOM Import...')
        self._action['dcmrtimport'] = submenu.addAction(icimport, 'DICOM RT Import...')
        self._action['dcmexport'] = submenu.addAction(icexport, 'DICOM Export...')
        submenu.addSeparator()
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['dcmds'] = submenu.addAction('DICOM Dataset...')
        self._action['xdcm'] = submenu.addAction('Xml DICOM Attributes...')

        self._menu['file'].addSeparator()
        self._action['lutedit'] = self._menu['file'].addAction(iclut, 'Edit LUT...')

        self._menu['file'].addSeparator()
        self._menu['file'].addAction(self._action['exit'])

        # Shortcuts

        self._action['open'].setShortcut(QKeySequence.Open)
        self._action['save'].setShortcut(QKeySequence.Save)
        self._action['saveas'].setShortcut(QKeySequence.SaveAs)
        self._action['close'].setShortcut(QKeySequence.Delete)
        self._action['editattr'].setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Question))

        # Connect

        self._action['open'].triggered.connect(lambda dummy: self.open())
        self._action['user'].triggered.connect(self._openUser)
        self._action['save'].triggered.connect(self.save)
        self._action['saveall'].triggered.connect(self.saveall)
        self._action['saveas'].triggered.connect(self.saveAs)
        self._action['close'].triggered.connect(self.remove)
        self._action['closeall'].triggered.connect(self.removeAll)
        self._action['download'].triggered.connect(self.download)
        self._action['update'].triggered.connect(self.checkUpdate)
        self._action['editattr'].triggered.connect(self.editAttr)
        self._action['editid'].triggered.connect(self.editID)
        self._action['anonymize'].triggered.connect(self.anonymize)
        self._action['editlabels'].triggered.connect(lambda _: self.editLabels())
        self._action['lutedit'].triggered.connect(self.lutEdit)
        self._action['opennii'].triggered.connect(lambda _: self.loadNifti())
        self._action['openmnc'].triggered.connect(lambda _: self.loadMinc())
        self._action['opennrrd'].triggered.connect(lambda _: self.loadNrrd())
        self._action['openvtk'].triggered.connect(lambda _: self.loadVtk())
        self._action['openvol'].triggered.connect(lambda _: self.loadSis())
        self._action['openvmr'].triggered.connect(lambda _: self.loadVmr())
        self._action['openmgh'].triggered.connect(lambda _: self.loadMgh())
        self._action['savenii'].triggered.connect(self.saveNifti)
        self._action['savemnc'].triggered.connect(self.saveMinc)
        self._action['savenrrd'].triggered.connect(self.saveNrrd)
        self._action['savevtk'].triggered.connect(self.saveVtk)
        self._action['savenpy'].triggered.connect(self.saveNumpy)
        self._action['roi2label'].triggered.connect(self.roiToLabel)
        self._action['vol2label'].triggered.connect(self.volToLabel)
        self._action['label2roi'].triggered.connect(self.labelToRoi)
        self._action['importnifti'].triggered.connect(self.importNifti)
        self._action['importminc'].triggered.connect(self.importMinc)
        self._action['importnrrd'].triggered.connect(self.importNrrd)
        self._action['importvtk'].triggered.connect(self.importVtk)
        self._action['importsis'].triggered.connect(self.importSis)
        self._action['dcmimport'].triggered.connect(self.importDicom)
        self._action['dcmrtimport'].triggered.connect(self.importDicomRT)
        self._action['exportnifti'].triggered.connect(self.exportNifti)
        self._action['exportminc'].triggered.connect(self.exportMinc)
        self._action['exportnrrd'].triggered.connect(self.exportNrrd)
        self._action['exportvtk'].triggered.connect(self.exportVtk)
        self._action['exportnpy'].triggered.connect(self.exportNumpy)
        self._action['dcmexport'].triggered.connect(self.exportDicom)
        self._action['dcmds'].triggered.connect(self.datasetDicom)
        self._action['xdcm'].triggered.connect(self.xmlDicom)
        self._action['about'].triggered.connect(self.about)
        self._action['pref'].triggered.connect(self.preferences)
        self._action['exit'].triggered.connect(self.exit)

    def _initFunctionsMenu(self) -> None:
        """
            Functions menu
                Join single component volume(s)
                Split multi component volume(s)
                --
                Flip axis
                Axis order
                Remove neck slices
                Datatype conversion
                Attributes conversion
                --
                Filters
                    Median
                    Mean
                    Gaussian
                    Anisotropic diffusion
                    Non-local means
                    Gradient magnitude
                    Laplacian
                Intensity processing
                    Histogram intensity matching
                    Regression intensity matching
                    Intensity normalization
                Texture features
                Bias field correction
                --
                Voxel-by-voxel processing
                    Mean volume
                    Median volume
                    Standard Deviation volume
                    Minimum volume
                    Maximum volume
                    Algebra
                --
                Processing workflow
                Workflows >
                --
                Install plugin
                Remove plugin
                Plugins >
        """
        self._menu['func'] = self._menubar.addMenu('Functions')
        self._menu['func'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['func'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['func'].setAttribute(Qt.WA_TranslucentBackground, True)

        # Icons

        icpath = self.getDefaultIconDirectory()
        icjoin = QIcon(join(icpath, 'join.png'))
        icsplit = QIcon(join(icpath, 'split.png'))
        icflip = QIcon(join(icpath, 'flip.png'))
        icaxis = QIcon(join(icpath, 'axis.png'))
        icattrc = QIcon(join(icpath, 'editattr.png'))
        icaniso = QIcon(join(icpath, 'filteraniso.png'))
        icbias = QIcon(join(icpath, 'filterbias.png'))
        icgaussian = QIcon(join(icpath, 'filtergaussian.png'))
        icgrad = QIcon(join(icpath, 'filtergrad.png'))
        iclapl = QIcon(join(icpath, 'filterlapl.png'))
        icmean = QIcon(join(icpath, 'filtermean.png'))
        icmedian = QIcon(join(icpath, 'filtermedian.png'))
        ictexture = QIcon(join(icpath, 'texture.png'))
        icalgebra = QIcon(join(icpath, 'algebra.png'))
        icworkf = QIcon(join(icpath, 'workflow.png'))

        # Actions

        self._action['join'] = self._menu['func'].addAction(icjoin, 'Join single component volume(s)...')
        self._action['split'] = self._menu['func'].addAction(icsplit, 'Split multi component volume(s)...')

        self._menu['func'].addSeparator()
        self._action['flip'] = self._menu['func'].addAction(icflip, 'Flip axis...')
        self._action['axis'] = self._menu['func'].addAction(icaxis, 'Permute axis...')
        self._action['neck'] = self._menu['func'].addAction(icaxis, 'Remove neck slices...')
        self._action['datatype'] = self._menu['func'].addAction('Datatype conversion...')
        self._action['attributes'] = self._menu['func'].addAction(icattrc, 'Attributes conversion...')

        self._menu['func'].addSeparator()
        submenu = self._menu['func'].addMenu('Filters')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['mean'] = submenu.addAction(icmean, 'Mean...')
        self._action['median'] = submenu.addAction(icmedian, 'Median...')
        self._action['gaussian'] = submenu.addAction(icgaussian, 'Gaussian...')
        self._action['gradient'] = submenu.addAction(icgrad, 'Gradient Magnitude...')
        self._action['laplacian'] = submenu.addAction(iclapl, 'Laplacian...')
        self._action['aniso'] = submenu.addAction(icaniso, 'Anisotropic diffusion...')
        submenu = self._menu['func'].addMenu('Intensity processing')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['histmatch'] = submenu.addAction('Histogram intensity matching...')
        self._action['regmatch'] = submenu.addAction('Regression intensity matching...')
        self._action['signorm'] = submenu.addAction('Intensity normalization...')
        self._action['texture'] = self._menu['func'].addAction(ictexture, 'Texture feature maps...')
        self._action['bias'] = self._menu['func'].addAction(icbias, 'Bias field correction...')

        self._menu['func'].addSeparator()
        submenu = self._menu['func'].addMenu('Voxel-by-voxel processing')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['algmean'] = submenu.addAction('Mean volume...')
        self._action['algmedian'] = submenu.addAction('Median volume...')
        self._action['algstd'] = submenu.addAction('Standard deviation volume...')
        self._action['algmin'] = submenu.addAction('Minimum volume...')
        self._action['algmax'] = submenu.addAction('Maximum volume...')
        self._action['algebra'] = submenu.addAction(icalgebra, 'Algebra...')

        self._menu['func'].addSeparator()
        self._action['workflow'] = self._menu['func'].addAction(icworkf, 'Workflow processing...')
        self._menu['workflows'] = self._menu['func'].addMenu('Workflows')
        self._menu['workflows'].aboutToShow.connect(self._updateWorkflowsMenu)
        self._menu['workflows'].triggered.connect(self._openWorkflow)

        self._menu['func'].addSeparator()
        self._action['addplugin'] = self._menu['func'].addAction('Install plugin...')
        self._action['delplugin'] = self._menu['func'].addAction('Remove plugin...')
        self._menu['plugins'] = self._menu['func'].addMenu('Plugins')
        self._menu['plugins'].triggered.connect(self._openPlugin)
        self._updatePluginsMenu()

        # Connect

        self._action['join'].triggered.connect(self.join)
        self._action['split'].triggered.connect(self.split)
        self._action['flip'].triggered.connect(lambda: self.flip())
        self._action['axis'].triggered.connect(lambda: self.swap())
        self._action['neck'].triggered.connect(lambda: self.neck())
        self._action['datatype'].triggered.connect(self.datatype)
        self._action['attributes'].triggered.connect(self.attributes)
        self._action['algmean'].triggered.connect(self.algmean)
        self._action['algmedian'].triggered.connect(self.algmedian)
        self._action['algstd'].triggered.connect(self.algstd)
        self._action['algmin'].triggered.connect(self.algmin)
        self._action['algmax'].triggered.connect(self.algmax)
        self._action['algebra'].triggered.connect(self.algmath)
        self._action['texture'].triggered.connect(lambda: self.texture())
        self._action['mean'].triggered.connect(lambda: self.filterMean())
        self._action['median'].triggered.connect(lambda: self.filterMedian())
        self._action['gaussian'].triggered.connect(lambda: self.filterGaussian())
        self._action['gradient'].triggered.connect(lambda: self.filterGradient())
        self._action['laplacian'].triggered.connect(lambda: self.filterLaplacian())
        self._action['aniso'].triggered.connect(lambda: self.filterAniso())
        self._action['bias'].triggered.connect(lambda: self.filterBias())
        self._action['histmatch'].triggered.connect(lambda: self.histmatch())
        self._action['regmatch'].triggered.connect(lambda: self.regmatch())
        self._action['signorm'].triggered.connect(lambda: self.signalNorm())
        self._action['workflow'].triggered.connect(self.automate)
        self._action['addplugin'].triggered.connect(lambda: self.addPlugin())
        self._action['delplugin'].triggered.connect(lambda: self.removePlugin())

    def _initROIMenu(self) -> None:
        """
            ROI menu
                List, attributes
                Load, Save, Save as, Close, Close all, Duplicate
                Boolean Union/Intersection/Difference/Symmetric difference
                Morphology dilate, erode, close, open Global/Blob, 2D/3D
                Shrink/Expand
                Background
                Complement
                blob extent filtering
                blob to roi
                thresholding, region growing
                Statistics
        """
        self._menu['roi'] = self._menubar.addMenu('ROI')
        self._menu['roi'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['roi'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['roi'].setAttribute(Qt.WA_TranslucentBackground, True)

    def _initRegistrationMenu(self) -> None:
        """
            Registration menu
                Fiducial box detection
                Reorient
                AC-PC selection
                --
                Rigid registration
                Affine registration
                Displacement field registration
                ICBM Normalization
                Batch registration
                --
                Time series realignment
                Eddy current correction
                Resample
                --
                Displacement Field Jacobian Determinant
                Asymmetry displacement field
        """
        # Icons

        icpath = self.getDefaultIconDirectory()
        icframe = QIcon(join(icpath, 'frame.png'))
        icacpc = QIcon(join(icpath, 'acpc.png'))
        icreorient = QIcon(join(icpath, 'reorient.png'))
        icmanual = QIcon(join(icpath, 'manual.png'))
        icrigid = QIcon(join(icpath, 'rigid.png'))
        icaffine = QIcon(join(icpath, 'affine.png'))
        icdiffeo = QIcon(join(icpath, 'diffeo.png'))
        icicbm = QIcon(join(icpath, 'icbm.png'))
        icasym = QIcon(join(icpath, 'asym.png'))
        icjac = QIcon(join(icpath, 'field.png'))

        # Actions

        self._menu['reg'] = self._menubar.addMenu('Registration')
        self._menu['reg'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['reg'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['reg'].setAttribute(Qt.WA_TranslucentBackground, True)

        self._action['frame'] = self._menu['reg'].addAction(icframe, 'Stereotactic frame detection...')
        self._action['acpc'] = self._menu['reg'].addAction(icacpc, 'AC-PC selection...')
        self._action['orient'] = self._menu['reg'].addAction(icreorient, 'Volume reorientation...')

        self._menu['reg'].addSeparator()
        self._action['hand'] = self._menu['reg'].addAction(icmanual, 'Manual registration...')
        self._action['rigid'] = self._menu['reg'].addAction(icrigid, 'Rigid registration...')
        self._action['affine'] = self._menu['reg'].addAction(icaffine, 'Affine registration...')
        self._action['field'] = self._menu['reg'].addAction(icdiffeo, 'Displacement field registration...')
        self._action['icbm'] = self._menu['reg'].addAction(icicbm, 'ICBM normalization...')
        self._action['batchreg'] = self._menu['reg'].addAction('Batch registration...')

        self._menu['reg'].addSeparator()
        self._action['series'] = self._menu['reg'].addAction('Time series realignment...')
        self._action['eddy'] = self._menu['reg'].addAction('Eddy current correction...')

        self._menu['reg'].addSeparator()
        self._action['resample'] = self._menu['reg'].addAction('Resample...')

        self._menu['reg'].addSeparator()
        self._action['asym'] = self._menu['reg'].addAction(icasym, 'Asymmetry displacement field...')
        self._action['jac'] = self._menu['reg'].addAction(icjac, 'Displacement field jacobian determinant...')
        # self._action['inv'] = self._menu['reg'].addAction('Displacement field inversion...')

        # Connect

        self._action['frame'].triggered.connect(lambda dummy: self.frameDetection())
        self._action['acpc'].triggered.connect(lambda dummy: self.acpcSelection())
        self._action['orient'].triggered.connect(lambda dummy: self.reorient())
        self._action['hand'].triggered.connect(self.manualRegistration)
        self._action['rigid'].triggered.connect(lambda: self.rigidRegistration())
        self._action['affine'].triggered.connect(lambda: self.affineRegistration())
        self._action['field'].triggered.connect(lambda: self.displacementFieldRegistration())
        self._action['icbm'].triggered.connect(lambda: self.normalize())
        self._action['series'].triggered.connect(self.realignment)
        self._action['eddy'].triggered.connect(self.eddycurrent)
        self._action['batchreg'].triggered.connect(self.batchRegistration)
        self._action['resample'].triggered.connect(self.resample)
        self._action['asym'].triggered.connect(self.asymmetry)
        self._action['jac'].triggered.connect(self.jacobian)
        # self._action['inv'].triggered.connect(self.fieldinv)

    def _initSegmentationMenu(self) -> None:
        """
            Segmentation menu
                KMeans clustering
                KMeans segmentation
                Skull stripping
                Tissue segmentation
                Cortical thickness
                ---
                Registration based segmentation
                Structs
                ---
                Deep learning segmentation
                    Hippocampus segmentation
                    Medial temporal segmentation
                    Tumor segmentation
                    T1 hypo-intensity lesion segmentation
                    White matter hyper-intensities segmentation
                    Tissue segmentation
                    # TOF vessels segmentation


        """

        # Icons

        icpath = self.getDefaultIconDirectory()
        icskull = QIcon(join(icpath, 'strip.png'))
        icseg = QIcon(join(icpath, 'seg.png'))

        # Actions

        self._menu['seg'] = self._menubar.addMenu('Segmentation')
        self._menu['seg'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['seg'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['seg'].setAttribute(Qt.WA_TranslucentBackground, True)

        self._action['kmeans1'] = self._menu['seg'].addAction('KMeans clustering...')
        self._action['kmeans2'] = self._menu['seg'].addAction('KMeans segmentation...')
        self._action['skull'] = self._menu['seg'].addAction(icskull, 'Skull stripping...')
        self._action['seg'] = self._menu['seg'].addAction(icseg, 'Tissue segmentation...')
        self._action['thickness'] = self._menu['seg'].addAction('Cortical thickness...')

        self._menu['seg'].addSeparator()
        self._action['regseg'] = self._menu['seg'].addAction('Registration based segmentation...')
        self._menu['regseg'] = self._menu['seg'].addMenu('Structs')
        self._menu['regseg'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['regseg'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['regseg'].setAttribute(Qt.WA_TranslucentBackground, True)
        self._initStructMenu()
        self._menu['userseg'] = self._menu['regseg'].addMenu('User')
        self._menu['userseg'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['userseg'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['userseg'].setAttribute(Qt.WA_TranslucentBackground, True)
        self._menu['userseg'].aboutToShow.connect(self._updateStructsMenu)
        self._menu['regseg'].triggered.connect(self._openStruct)

        self._menu['seg'].addSeparator()

        submenu = self._menu['seg'].addMenu('Deep learning segmentation')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['hipp'] = submenu.addAction('Hippocampus segmentation...')
        self._action['lesion'] = submenu.addAction('Hypo-intensity lesion segmentation...')
        self._action['temporal'] = submenu.addAction('Medial temporal clustering...')
        # self._action['tof'] = submenu.addAction('TOF vessels segmentation...')
        self._action['tissue'] = submenu.addAction('Tissue segmentation...')
        self._action['tumor'] = submenu.addAction('Tumor clustering...')
        self._action['wmh'] = submenu.addAction('White matter hyper-intensities segmentation...')

        # Connect

        self._action['kmeans1'].triggered.connect(self.kMeansClustering)
        self._action['kmeans2'].triggered.connect(self.kMeansSegmentation)
        self._action['seg'].triggered.connect(lambda: self.priorBasedSegmentation())
        self._action['thickness'].triggered.connect(self.thickness)
        self._action['regseg'].triggered.connect(self.registrationSegmentation)
        self._action['skull'].triggered.connect(lambda: self.skullStriping())
        self._action['hipp'].triggered.connect(self.hippocampusSegmentation)
        self._action['temporal'].triggered.connect(self.temporalSegmentation)
        self._action['tumor'].triggered.connect(self.tumorSegmentation)
        self._action['lesion'].triggered.connect(self.lesionSegmentation)
        self._action['wmh'].triggered.connect(self.wmhSegmentation)
        # self._action['tof'].triggered.connect(self.vesselSegmentation)
        self._action['tissue'].triggered.connect(self.tissueSegmentation)

    def _initMapMenu(self) -> None:
        """
            Mapping
                Model
                    fMRI conditions
                    fMRI subjects/conditions
                    fMRI groups/subjects/conditions
                    ---
                    One sample t-test
                    Two sample t-test
                    ANOVA
                    ANCOVA
                    ----
                    GLM images conditions
                    GLM images subjects/conditions
                    GLM images groups/subjects/conditions
                    GLM images groups
                    ---
                    Models >
                        files in user/.Sisyphe/models
                        ---
                        Open model
                Contrast
                Result
                Conjunction
                ---
                Time series preprocessing
                Seed-to-voxel time series correlation
                Single-subject time series ICA
                Time series correlation matrix
                # Multi-subject time series ICA
                ---
                Dynamic susceptibility contrast MR perfusion
        """
        # Actions

        self._menu['statmap'] = self._menubar.addMenu('Mapping')
        self._menu['statmap'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['statmap'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['statmap'].setAttribute(Qt.WA_TranslucentBackground, True)

        submenu = self._menu['statmap'].addMenu('Model')
        submenu.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        submenu.setWindowFlag(Qt.FramelessWindowHint, True)
        submenu.setAttribute(Qt.WA_TranslucentBackground, True)
        self._action['fmricnd'] = submenu.addAction('fMRI conditions...')
        self._action['fmrisbj'] = submenu.addAction('fMRI subjects/conditions...')
        self._action['fmrigrp'] = submenu.addAction('fMRI groups/subjects/conditions...')
        submenu.addSeparator()
        self._action['onettest'] = submenu.addAction('One sample t-test...')
        self._action['twottest'] = submenu.addAction('Two sample t-test...')
        self._action['pairedttest'] = submenu.addAction('Paired t-test...')
        submenu.addSeparator()
        self._action['glmsbj'] = submenu.addAction('GLM subjects/conditions...')
        self._action['glmgrp'] = submenu.addAction('GLM groups/subjects/conditions...')
        self._action['glmgrp2'] = submenu.addAction('GLM groups...')
        self._action['glmgrp3'] = submenu.addAction('GLM groups/subjects...')
        submenu.addSeparator()
        self._menu['model'] = submenu.addMenu('Models')
        self._menu['model'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['model'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['model'].setAttribute(Qt.WA_TranslucentBackground, True)
        self._menu['model'].aboutToShow.connect(self._updateModelsMenu)
        self._menu['model'].triggered.connect(self._openModel)

        self._action['contrast'] = self._menu['statmap'].addAction('Contrast...')
        self._action['result'] = self._menu['statmap'].addAction('Result...')
        self._action['conj'] = self._menu['statmap'].addAction('Conjunction...')
        self._action['mapconv'] = self._menu['statmap'].addAction('t to z-map conversion...')
        self._menu['statmap'].addSeparator()
        self._action['confound'] = self._menu['statmap'].addAction('Time series preprocessing...')
        self._action['seedcorr'] = self._menu['statmap'].addAction('Seed-to-voxel time series correlation...')
        self._action['fastica'] = self._menu['statmap'].addAction('Single-subject time series ICA...')
        self._action['matcorr'] = self._menu['statmap'].addAction('Time series correlation matrix...')
        # self._action['groupica'] = self._menu['statmap'].addAction('Multi-subject time series ICA...')
        self._menu['statmap'].addSeparator()
        self._action['pwi'] = self._menu['statmap'].addAction('Dynamic susceptibility contrast...')

        # Connect

        self._action['fmricnd'].triggered.connect(lambda dummy: self.model(0))
        self._action['fmrisbj'].triggered.connect(lambda dummy: self.model(1))
        self._action['fmrigrp'].triggered.connect(lambda dummy: self.model(2))
        self._action['onettest'].triggered.connect(lambda dummy: self.model(3))
        self._action['twottest'].triggered.connect(lambda dummy: self.model(4))
        self._action['pairedttest'].triggered.connect(lambda dummy: self.model(5))
        self._action['glmsbj'].triggered.connect(lambda dummy: self.model(6))
        self._action['glmgrp'].triggered.connect(lambda dummy: self.model(7))
        self._action['glmgrp2'].triggered.connect(lambda dummy: self.model(8))
        self._action['glmgrp3'].triggered.connect(lambda dummy: self.model(9))
        self._action['contrast'].triggered.connect(self.contrast)
        self._action['result'].triggered.connect(self.result)
        self._action['conj'].triggered.connect(self.conjunction)
        self._action['mapconv'].triggered.connect(self.tmapTozmap)
        self._action['confound'].triggered.connect(self.confounders)
        self._action['seedcorr'].triggered.connect(self.seedCorrelation)
        self._action['matcorr'].triggered.connect(self.matrixCorrelation)
        self._action['fastica'].triggered.connect(self.fastICA)
        # self._action['groupica'].triggered.connect(self.groupICA)
        self._action['pwi'].triggered.connect(self.perfusion)

    def _initDiffusionMenu(self) -> None:
        """
            Diffusion
                Gradients...
                Preprocessing...
                Diffusion model...
                Tractogram generation...
                Bundle
                    ROI based streamlines selection...
                    Filter based streamlines selection...
                    Template based streamlines selection...
                    ---
                    Density map...
                    Path length map...
                    Connectivity matrix...
                    ---
                    Statistics...
        """

        # Actions

        self._menu['diffusion'] = self._menubar.addMenu('Diffusion')
        self._menu['diffusion'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['diffusion'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['diffusion'].setAttribute(Qt.WA_TranslucentBackground, True)

        self._action['grad'] = self._menu['diffusion'].addAction('Gradients...')
        self._action['prepoc'] = self._menu['diffusion'].addAction('Preprocessing...')
        self._action['fit'] = self._menu['diffusion'].addAction('Diffusion model...')
        self._action['tracto'] = self._menu['diffusion'].addAction('Tractogram generation...')
        submenu = self._menu['diffusion'].addMenu('Bundle')
        self._action['roisel'] = submenu.addAction('ROI based streamlines selection...')
        self._action['filtsel'] = submenu.addAction('Filter based streamlines selection...')
        self._action['tplsel'] = submenu.addAction('Template based streamlines selection...')
        submenu.addSeparator()
        self._action['density'] = submenu.addAction('Density map...')
        self._action['length'] = submenu.addAction('Path length map...')
        self._action['conn'] = submenu.addAction('Connectivity matrix...')

        # Connect

        self._action['grad'].triggered.connect(lambda _: self.diffusionGradients())
        self._action['prepoc'].triggered.connect(lambda _: self.diffusionPreprocessing())
        self._action['fit'].triggered.connect(lambda _: self.diffusionModel())
        self._action['tracto'].triggered.connect(lambda _: self.diffusionTractogram())
        self._action['roisel'].triggered.connect(lambda _: self.diffusionBundleROISelection())
        self._action['filtsel'].triggered.connect(lambda _: self.diffusionBundleFilterSelection())
        self._action['tplsel'].triggered.connect(lambda _: self.diffusionBundleAtlasSelection())
        self._action['density'].triggered.connect(lambda _: self.diffusionDensityMap())
        self._action['length'].triggered.connect(lambda _: self.diffusionPathLengthMap())
        self._action['conn'].triggered.connect(lambda _: self.diffusionConnectivityMatrix())

    def _initViewsMenu(self) -> None:
        self._menu['views'] = self._menubar.addMenu('Views')
        self._menu['views'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['views'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['views'].setAttribute(Qt.WA_TranslucentBackground, True)

        sliceview = self._sliceview()[0, 0].getPopup()
        sliceview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        sliceview.setWindowFlag(Qt.FramelessWindowHint, True)
        sliceview.setAttribute(Qt.WA_TranslucentBackground, True)
        orthoview = self._orthoview()[0, 0].getPopup()
        orthoview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        orthoview.setWindowFlag(Qt.FramelessWindowHint, True)
        orthoview.setAttribute(Qt.WA_TranslucentBackground, True)
        synchroview = self._synchroview()[0, 0].getPopup()
        synchroview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        synchroview.setWindowFlag(Qt.FramelessWindowHint, True)
        synchroview.setAttribute(Qt.WA_TranslucentBackground, True)
        projview = self._projview()[0, 0].getPopup()
        projview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        projview.setWindowFlag(Qt.FramelessWindowHint, True)
        projview.setAttribute(Qt.WA_TranslucentBackground, True)
        compview = self._compview()[0, 0].getPopup()
        compview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        compview.setWindowFlag(Qt.FramelessWindowHint, True)
        compview.setAttribute(Qt.WA_TranslucentBackground, True)
        sliceview.setTitle(self._tabview.tabText(0))
        orthoview.setTitle(self._tabview.tabText(1))
        synchroview.setTitle(self._tabview.tabText(2))
        projview.setTitle(self._tabview.tabText(3))
        compview.setTitle(self._tabview.tabText(4))
        self._menuView.append(self._menu['views'].addMenu(sliceview))
        self._menuView.append(self._menu['views'].addMenu(orthoview))
        self._menuView.append(self._menu['views'].addMenu(synchroview))
        self._menuView.append(self._menu['views'].addMenu(projview))
        self._menuView.append(self._menu['views'].addMenu(compview))
        self._menuView[0].setEnabled(False)
        self._menuView[1].setEnabled(False)
        self._menuView[2].setEnabled(False)
        self._menuView[3].setEnabled(False)
        self._menuView[4].setEnabled(False)
        database = self._database.getPopup()
        database.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        database.setWindowFlag(Qt.FramelessWindowHint, True)
        database.setAttribute(Qt.WA_TranslucentBackground, True)
        database.setTitle(self._tabview.tabText(5))
        self._menu['views'].addMenu(database)
        capview = self._captures.getPopup()
        capview.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        capview.setWindowFlag(Qt.FramelessWindowHint, True)
        capview.setAttribute(Qt.WA_TranslucentBackground, True)
        capview.setTitle(self._tabview.tabText(6))
        self._menu['views'].addMenu(capview)
        console = self._console.getPopup()
        console.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        console.setWindowFlag(Qt.FramelessWindowHint, True)
        console.setAttribute(Qt.WA_TranslucentBackground, True)
        console.setTitle(self._tabview.tabText(7))
        self._menu['views'].addMenu(console)

    def _initWindowMenu(self) -> None:
        """
            Window menu
                Minimize/Maximize
                Full screen
                ---
                Tool bar Hide/Show
                Thumbnail Hide/Show
                Dock Hide/Show
                Status Bar Hide/Show
                ---
                Slices view
                Orthogonal view
                Synchronized view
                Projection view
                Database view
                Screenshots view
                IPython view
        """
        # Icons

        icpath = self.getDefaultIconDirectory()
        icfullscrn = QIcon(join(icpath, 'fullscreen.png'))

        self._menu['window'] = self._menubar.addMenu('Window')
        self._menu['window'].setWindowFlag(Qt.NoDropShadowWindowHint, True)
        self._menu['window'].setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu['window'].setAttribute(Qt.WA_TranslucentBackground, True)

        self._menu['window'].addAction(self._action['about'])
        self._menu['window'].addSeparator()

        # Actions

        self._action['wmin'] = QAction('Minimize', parent=self)
        self._action['wmax'] = QAction('Maximize', parent=self)
        self._action['fullscrn'] = QAction(icfullscrn, 'Full screen', parent=self)
        self._action['fullscrn'].setCheckable(True)
        self._action['fullscrn'].setToolTip('Full screen\nF11 or ESC to quit full-screen mode')

        self._menu['window'].addAction(self._action['wmin'])
        self._menu['window'].addAction(self._action['wmax'])
        self._menu['window'].addAction(self._action['fullscrn'])

        self._menu['window'].addSeparator()
        self._action['toolbar'] = self._menu['window'].addAction('Show/Hide Toolbar')
        self._action['thumb'] = self._menu['window'].addAction('Show/Hide Thumbnail')
        self._action['dock'] = self._menu['window'].addAction('Show/Hide Dock')
        self._action['status'] = self._menu['window'].addAction('Show/Hide Status bar')
        self._action['toolbar'].setCheckable(True)
        self._action['thumb'].setCheckable(True)
        self._action['dock'].setCheckable(True)
        self._action['status'].setCheckable(True)
        self._action['toolbar'].setChecked(True)
        self._action['thumb'].setChecked(True)
        self._action['dock'].setChecked(True)
        self._action['status'].setChecked(True)

        self._menu['window'].addSeparator()
        self._action['next'] = QAction('Next tab', parent=self)
        self._action['previous'] = QAction('Previous tab', parent=self)
        self._menu['window'].addAction(self._action['next'])
        self._menu['window'].addAction(self._action['previous'])

        self._menu['window'].addSeparator()
        self._action['slice'] = QAction(QIcon(join(icpath, 'slice-view.png')), 'Slice view', parent=self)
        self._action['ortho'] = QAction(QIcon(join(icpath, 'ortho-view.png')), 'Orthogonal view', parent=self)
        self._action['synchro'] = QAction(QIcon(join(icpath, 'sync-view.png')), 'Synchronized view', parent=self)
        self._action['proj'] = QAction(QIcon(join(icpath, 'proj-view.png')), 'Projection view', parent=self)
        self._action['multi'] = QAction(QIcon(join(icpath, 'multi-view.png')), 'Multi-component view ', parent=self)
        self._action['database'] = QAction('Database', parent=self)
        self._action['scrshots'] = QAction('Screenshots', parent=self)
        self._action['ipython'] = QAction('IPython', parent=self)
        self._action['slice'].setToolTip('Slice view\nDisplays contiguous slices in a grid view.')
        self._action['ortho'].setToolTip('Orthogonal view\nDisplays three orthogonal slices and a 3D rendering.')
        self._action['synchro'].setToolTip('Synchronized view\nDisplays same slice of synchronized volumes.')
        self._action['proj'].setToolTip('Projection view\nDisplays projections of a volume in eight directions.')
        self._action['multi'].setToolTip('Multi-component view\nDisplays slices of a multi-component volume.')

        self._menu['window'].addAction(self._action['slice'])
        self._menu['window'].addAction(self._action['ortho'])
        self._menu['window'].addAction(self._action['synchro'])
        self._menu['window'].addAction(self._action['proj'])
        self._menu['window'].addAction(self._action['multi'])
        self._menu['window'].addAction(self._action['database'])
        self._menu['window'].addAction(self._action['scrshots'])
        self._menu['window'].addAction(self._action['ipython'])

        # Shortcuts

        self._action['wmin'].setShortcut(QKeySequence.ZoomOut)
        self._action['wmax'].setShortcut(QKeySequence.ZoomIn)
        self._action['fullscrn'].setShortcut(QKeySequence(Qt.Key_F11))
        self._action['next'].setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Right))
        self._action['previous'].setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Left))
        self._action['slice'].setShortcut(QKeySequence(Qt.Key_F1))
        self._action['ortho'].setShortcut(QKeySequence(Qt.Key_F2))
        self._action['synchro'].setShortcut(QKeySequence(Qt.Key_F3))
        self._action['proj'].setShortcut(QKeySequence(Qt.Key_F4))
        self._action['multi'].setShortcut(QKeySequence(Qt.Key_F5))
        self._action['database'].setShortcut(QKeySequence(Qt.Key_F6))
        self._action['scrshots'].setShortcut(QKeySequence(Qt.Key_F7))
        self._action['ipython'].setShortcut(QKeySequence(Qt.Key_F8))

        # Connect

        # noinspection PyTypeChecker
        self._action['wmin'].triggered.connect(lambda dummy: self.setWindowState(Qt.WindowMinimized))
        # noinspection PyTypeChecker
        self._action['wmax'].triggered.connect(lambda dummy: self.setWindowState(Qt.WindowMaximized))
        self._action['fullscrn'].triggered.connect(lambda dummy: self.toggleFullscreen())
        self._action['next'].triggered.connect(self._nextTab)
        self._action['previous'].triggered.connect(self._previousTab)
        self._action['slice'].triggered.connect(self.displayInSliceView)
        self._action['ortho'].triggered.connect(self.displayInOrthogonalView)
        self._action['synchro'].triggered.connect(self.displayInSynchronisedView)
        self._action['proj'].triggered.connect(self.displayInProjectionView)
        self._action['multi'].triggered.connect(self.displayInComponentView)
        self._action['database'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(5))
        self._action['scrshots'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(6))
        self._action['ipython'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(7))

    def _initToolBar(self) -> None:
        policy = QSizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Fixed)
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        self._toolbar.clear()
        self._toolbar.setMovable(False)
        self._toolbar.setSizePolicy(policy)
        size = self._settings.getFieldValue('GUI', 'ToolbarSize')
        if size is None: size = self._TOOLBARICONSIZE
        self._toolbar.setIconSize(QSize(size, size))
        if self._settings.getFieldValue('ToolbarIcons', 'open'): self._toolbar.addAction(self._action['open'])
        if self._settings.getFieldValue('ToolbarIcons', 'save'): self._toolbar.addAction(self._action['save'])
        if self._settings.getFieldValue('ToolbarIcons', 'saveall'): self._toolbar.addAction(self._action['saveall'])
        if self._settings.getFieldValue('ToolbarIcons', 'close'): self._toolbar.addAction(self._action['close'])
        if self._settings.getFieldValue('ToolbarIcons', 'closeall'): self._toolbar.addAction(self._action['closeall'])
        if self._settings.getFieldValue('ToolbarIcons', 'editattr'): self._toolbar.addAction(self._action['editattr'])
        if self._settings.getFieldValue('ToolbarIcons', 'editid'): self._toolbar.addAction(self._action['editid'])
        if self._settings.getFieldValue('ToolbarIcons', 'anonymize'): self._toolbar.addAction(self._action['anonymize'])
        if self._settings.getFieldValue('ToolbarIcons', 'editlabels'): self._toolbar.addAction(self._action['editlabels'])
        if self._settings.getFieldValue('ToolbarIcons', 'dcmimport'): self._toolbar.addAction(self._action['dcmimport'])
        n = len(self._toolbar.actions())
        if n > 0: self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'opennii'): self._toolbar.addAction(self._action['opennii'])
        if self._settings.getFieldValue('ToolbarIcons', 'opennrrd'): self._toolbar.addAction(self._action['opennrrd'])
        if self._settings.getFieldValue('ToolbarIcons', 'openmnc'): self._toolbar.addAction(self._action['openmnc'])
        if self._settings.getFieldValue('ToolbarIcons', 'openmgh'): self._toolbar.addAction(self._action['openmgh'])
        if self._settings.getFieldValue('ToolbarIcons', 'openvmr'): self._toolbar.addAction(self._action['openvmr'])
        if self._settings.getFieldValue('ToolbarIcons', 'openvol'): self._toolbar.addAction(self._action['openvol'])
        if self._settings.getFieldValue('ToolbarIcons', 'openvtk'): self._toolbar.addAction(self._action['openvtk'])
        if self._settings.getFieldValue('ToolbarIcons', 'savenii'): self._toolbar.addAction(self._action['savenii'])
        if self._settings.getFieldValue('ToolbarIcons', 'savenpy'): self._toolbar.addAction(self._action['savenpy'])
        if self._settings.getFieldValue('ToolbarIcons', 'savenrrd'): self._toolbar.addAction(self._action['savenrrd'])
        if self._settings.getFieldValue('ToolbarIcons', 'savemnc'): self._toolbar.addAction(self._action['savemnc'])
        if self._settings.getFieldValue('ToolbarIcons', 'savevtk'): self._toolbar.addAction(self._action['savevtk'])
        n = len(self._toolbar.actions())
        if n > 0: self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'slice'): self._toolbar.addAction(self._action['slice'])
        if self._settings.getFieldValue('ToolbarIcons', 'ortho'): self._toolbar.addAction(self._action['ortho'])
        if self._settings.getFieldValue('ToolbarIcons', 'synchro'): self._toolbar.addAction(self._action['synchro'])
        if self._settings.getFieldValue('ToolbarIcons', 'proj'): self._toolbar.addAction(self._action['proj'])
        if self._settings.getFieldValue('ToolbarIcons', 'multi'): self._toolbar.addAction(self._action['multi'])
        n = len(self._toolbar.actions())
        if n > 0 and not self._toolbar.actions()[n-1].isSeparator(): self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'join'): self._toolbar.addAction(self._action['join'])
        if self._settings.getFieldValue('ToolbarIcons', 'split'): self._toolbar.addAction(self._action['split'])
        if self._settings.getFieldValue('ToolbarIcons', 'flip'): self._toolbar.addAction(self._action['flip'])
        if self._settings.getFieldValue('ToolbarIcons', 'axis'): self._toolbar.addAction(self._action['axis'])
        if self._settings.getFieldValue('ToolbarIcons', 'attributes'): self._toolbar.addAction(self._action['attributes'])
        if self._settings.getFieldValue('ToolbarIcons', 'texture'): self._toolbar.addAction(self._action['texture'])
        if self._settings.getFieldValue('ToolbarIcons', 'gaussian'): self._toolbar.addAction(self._action['gaussian'])
        if self._settings.getFieldValue('ToolbarIcons', 'mean'): self._toolbar.addAction(self._action['mean'])
        if self._settings.getFieldValue('ToolbarIcons', 'median'): self._toolbar.addAction(self._action['median'])
        if self._settings.getFieldValue('ToolbarIcons', 'gradient'): self._toolbar.addAction(self._action['gradient'])
        if self._settings.getFieldValue('ToolbarIcons', 'laplacian'): self._toolbar.addAction(self._action['laplacian'])
        if self._settings.getFieldValue('ToolbarIcons', 'aniso'): self._toolbar.addAction(self._action['aniso'])
        if self._settings.getFieldValue('ToolbarIcons', 'bias'): self._toolbar.addAction(self._action['bias'])
        if self._settings.getFieldValue('ToolbarIcons', 'algebra'): self._toolbar.addAction(self._action['algebra'])
        if self._settings.getFieldValue('ToolbarIcons', 'workflow'): self._toolbar.addAction(self._action['workflow'])
        if self._settings.getFieldValue('ToolbarIcons', 'lutedit'): self._toolbar.addAction(self._action['lutedit'])
        n = len(self._toolbar.actions())
        if n > 0 and not self._toolbar.actions()[n-1].isSeparator(): self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'frame'): self._toolbar.addAction(self._action['frame'])
        if self._settings.getFieldValue('ToolbarIcons', 'acpc'): self._toolbar.addAction(self._action['acpc'])
        if self._settings.getFieldValue('ToolbarIcons', 'orient'): self._toolbar.addAction(self._action['orient'])
        if self._settings.getFieldValue('ToolbarIcons', 'hand'): self._toolbar.addAction(self._action['hand'])
        if self._settings.getFieldValue('ToolbarIcons', 'rigid'): self._toolbar.addAction(self._action['rigid'])
        if self._settings.getFieldValue('ToolbarIcons', 'affine'): self._toolbar.addAction(self._action['affine'])
        if self._settings.getFieldValue('ToolbarIcons', 'field'): self._toolbar.addAction(self._action['field'])
        if self._settings.getFieldValue('ToolbarIcons', 'icbm'): self._toolbar.addAction(self._action['icbm'])
        if self._settings.getFieldValue('ToolbarIcons', 'asym'): self._toolbar.addAction(self._action['asym'])
        if self._settings.getFieldValue('ToolbarIcons', 'jac'): self._toolbar.addAction(self._action['jac'])
        n = len(self._toolbar.actions())
        if n > 0 and not self._toolbar.actions()[n-1].isSeparator(): self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'skull'): self._toolbar.addAction(self._action['skull'])
        if self._settings.getFieldValue('ToolbarIcons', 'seg'): self._toolbar.addAction(self._action['seg'])
        n = len(self._toolbar.actions())
        if n > 0 and not self._toolbar.actions()[n-1].isSeparator(): self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'fullscrn'): self._toolbar.addAction(self._action['fullscrn'])
        if self._settings.getFieldValue('ToolbarIcons', 'pref'): self._toolbar.addAction(self._action['pref'])
        if self._settings.getFieldValue('ToolbarIcons', 'exit'): self._toolbar.addAction(self._action['exit'])
        n = len(self._toolbar.actions())
        if n > 0 and self._toolbar.actions()[n-1].isSeparator(): self._toolbar.removeAction(self._toolbar.actions()[n-1])
        # noinspection PyTypeChecker
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)
        # noinspection PyTypeChecker
        self.addToolBarBreak(Qt.TopToolBarArea)
        self._toolbar.setStyleSheet('QToolButton:pressed {border-color: rgb(176, 176, 176); border-style: '
                                    'solid; border-width: 1px; border-radius: 6px;}')
        if n == 0: self._toolbar.setVisible(False)
        else:
            v = self._settings.getFieldValue('GUI', 'ToolbarVisibility')
            if v is None: v = True
            self._toolbar.setVisible(v)

    def _initTemplateMenu(self) -> None:
        path = join(self.getMainDirectory(), 'templates')
        if exists(path):
            p = Path(path)
            self._menu['template'].clear()
            # list of subdirectories
            dirs = list()
            buff = [d for d in p.iterdir() if d.is_dir()]
            while len(buff) > 0:
                current = buff.pop()
                dirs.append(current)
                p = Path(current)
                subdirs = [d for d in p.iterdir() if d.is_dir()]
                if len(subdirs) > 0:
                    buff += subdirs
            # tree of subdirectories
            tree = dict()
            n = len(Path(path).parts)
            for current in dirs:
                p = Path(current).parts
                n2 = len(p) - n
                buff = tree
                submenu = self._menu['template']
                if n2 > 1:
                    for i in range(-n2, -1):
                        submenu = buff[p[i]][1]
                        buff = buff[p[i]][0]
                files = list(Path(current).glob('*{}'.format(SisypheVolume.getFileExt())))
                if len(files) > 0 and p[-1][0] != '_':
                    newmenu = submenu.addMenu(p[-1])
                    buff[p[-1]] = (dict(), newmenu)
                    # Add templates
                    files.sort()
                    for f in files:
                        action = newmenu.addAction(basename(f))
                        action.setData(f)
                else: buff[p[-1]] = (dict(), submenu)
            # < Revision 17/06/2025
            # Open template folder
            self._menu['template'].addSeparator()
            self._menu['template'].addAction('Open template folder')
            # Revision 17/06/2025 >

    def _initStructMenu(self) -> None:
        path = join(self.getMainDirectory(), 'templates')
        if exists(path):
            p = Path(path)
            self._menu['regseg'].clear()
            # list of subdirectories
            dirs = list()
            buff = [d for d in p.iterdir() if d.is_dir()]
            while len(buff) > 0:
                current = buff.pop()
                dirs.append(current)
                p = Path(current)
                subdirs = [d for d in p.iterdir() if d.is_dir()]
                if len(subdirs) > 0:
                    buff += subdirs
            # tree of subdirectories
            tree = dict()
            n = len(Path(path).parts)
            for current in dirs:
                p = Path(current).parts
                n2 = len(p) - n
                buff = tree
                submenu = self._menu['regseg']
                if n2 > 1:
                    for i in range(-n2, -1):
                        submenu = buff[p[i]][1]
                        buff = buff[p[i]][0]
                files = list(Path(current).glob('*.xml'))
                if len(files) > 0 and p[-1][0] != '_':
                    newmenu = submenu.addMenu(p[-1].capitalize())
                    buff[p[-1]] = (dict(), newmenu)
                    # Add structs
                    files.sort()
                    for f in files:
                        action = newmenu.addAction(splitext(removeAllPrefixesFromFilename(basename(f)))[0])
                        action.setData(f)
                else: buff[p[-1]] = (dict(), submenu)

    def _updateRecentMenu(self) -> None:
        self._recent.updateQMenu(self._menu['recent'])

    def _updateWorkflowsMenu(self) -> None:
        path = join(self.getUserDirectory(), 'workflows')
        if not exists(path): mkdir(path)
        from Sisyphe.gui.dialogWorkflow import DialogWorkflow
        path = join(path, '*{}'.format(DialogWorkflow.getFileExt()))
        files = glob(path)
        if len(files) > 0:
            self._menu['workflows'].clear()
            for file in files:
                if exists(file):
                    action = self._menu['workflows'].addAction(splitext(basename(file))[0])
                    action.setData(file)
            self._menu['workflows'].addSeparator()
            self._menu['workflows'].addAction('Open workflow...')

    def _updatePluginsMenu(self) -> None:
        path = join(self.getMainDirectory(), 'plugins', '**')
        self._menu['plugins'].clear()
        self._menu['plugins'].setEnabled(False)
        self._action['delplugin'].setEnabled(False)
        for d in glob(path):
            name = basename(d)
            if isdir(d) and name != '__pycache__':
                self._menu['plugins'].addAction(name)
                self._menu['plugins'].setEnabled(True)
                self._action['delplugin'].setEnabled(True)

    def _updateStructsMenu(self) -> None:
        path = join(self.getUserDirectory(), 'segmentation')
        if not exists(path): mkdir(path)
        path = join(path, '*.xml')
        files = glob(path)
        if len(files) > 0:
            self._menu['userseg'].clear()
            for file in files:
                if exists(file):
                    action = self._menu['userseg'].addAction(splitext(basename(file))[0])
                    action.setData(file)

    def _updateModelsMenu(self) -> None:
        path = join(self.getUserDirectory(), 'models')
        if not exists(path): mkdir(path)
        path = join(path, '*{}'.format(SisypheDesign.geFileExt()))
        files = glob(path)
        if len(files) > 0:
            self._menu['model'].clear()
            for file in files:
                if exists(file):
                    action = self._menu['model'].addAction(splitext(basename(file))[0])
                    action.setData(file)
            self._menu['model'].addSeparator()
            self._menu['model'].addAction('Open model...')

    def _openRecent(self, action: QAction | None) -> None:
        file = action.text()
        if file == 'Clear':
            self._menu['recent'].clear()
            self._recent.clear()
            self._recent.save()
        else:
            file = str(action.data())
            if exists(file): self.open(file)

    def _openTemplate(self, action: QAction | None) -> None:
        file = str(action.data())
        if exists(file): self.open(file)
        # < Revision 17/06/2025
        elif action.text() == 'Open template folder':
            folder = join(self.getMainDirectory(), 'templates')
            if platform == 'win32':
                subprocess.Popen('explorer "{}"'.format(folder))
            elif platform == 'darwin':
                folder = '~' + folder
                subprocess.call(["open", folder])
        # Revision 17/06/2025 >

    def _openUser(self) -> None:
        folder = self.getUserDirectory()
        if platform == 'win32':
            subprocess.Popen('explorer "{}"'.format(folder))
        elif platform == 'darwin':
            folder = '~' + folder
            subprocess.call(["open", folder])

    def _openStruct(self, action: QAction | None) -> None:
        file = str(action.data())
        if exists(file):
            from Sisyphe.gui.dialogSegmentation import DialogRegistrationBasedSegmentation
            # < Revision 16/04/2025
            # self._dialog = DialogRegistrationBasedSegmentation(parent=self, filename=file)
            self._dialog = DialogRegistrationBasedSegmentation(filename=file)
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            # Revision 16/04/2025 >
            w1, w2 = self._dialog.getSelectionWidgets()
            w1.setToolbarThumbnail(self._thumbnail)
            w2.setToolbarThumbnail(self._thumbnail)
            self._dialog.exec()

    def _openModel(self, action: QAction | None) -> None:
        filename = action.text()
        if filename == 'Open model...':
            path = join(self.getUserDirectory(), 'models')
            if not exists(path): mkdir(path)
            filename = QFileDialog.getOpenFileName(self, 'Open model...', path,
                                                   filter=SisypheDesign.getFilterExt())[0]
        else: filename = str(action.data())
        if filename and exists(filename):
            filename = abspath(filename)
            chdir(dirname(filename))
            title = '{} model'.format(basename(filename)[0])
            design = SisypheDesign()
            design.load(filename)
            from Sisyphe.gui.dialogStatModel import DialogModel
            self._dialog = DialogModel(title, design, design.isfMRIDesign(), parent=self)
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            if self._dialog.exec():
                design = self._dialog.getModel()
                self._dialog.close()
                if design.isEstimated():
                    r = messageBox(self,
                                   self.windowTitle(),
                                   'Do you want to define a contrast ?',
                                   icon=QMessageBox.Question,
                                   buttons=QMessageBox.Yes | QMessageBox.No,
                                   default=QMessageBox.No)
                    if r == QMessageBox.Yes:
                        from Sisyphe.gui.dialogStatContrast import DialogContrast
                        self._dialog = DialogContrast(design, parent=self)
                        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
                        self._dialog.exec()

    def _openWorkflow(self, action: QAction | None) -> None:
        from Sisyphe.gui.dialogWorkflow import DialogWorkflow
        filename = action.text()
        if filename == 'Open workflow...':
            path = join(self.getUserDirectory(), 'workflows')
            if not exists(path): mkdir(path)
            filename = QFileDialog.getOpenFileName(self, 'Open workflow...', path,
                                                   filter=DialogWorkflow.getFilterExt())[0]
        else: filename = str(action.data())
        if exists(filename):
            filename = abspath(filename)
            chdir(dirname(filename))
            # < Revision 16/04/2025
            # self._dialog = DialogWorkflow(parent=self)
            self._dialog = DialogWorkflow()
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            # Revision 16/04/2025 >
            self._dialog.load(filename)
            self._dialog.exec()

    def _openPlugin(self, action: QAction | None) -> None:
        path = join(self.getMainDirectory(), 'plugins', action.text(), action.text() + '.py')
        if exists(path):
            m = ['Sisyphe', 'plugins', action.text(), action.text()]
            name = '.'.join(m)
            try: mod = importlib.import_module(name)
            except:
                messageBox(self,
                           'Plugin...',
                           '{} import failed.'.format(name))
                return
            try: mod.main(self)
            except: messageBox(self,
                               'Plugin...',
                               '{} failed to run.'.format(name))
        else: messageBox(self,
                         'Plugin...',
                         'No such file {}'.format(action.text() + '.py'))

    def _nextTab(self) -> None:
        i = self._tabview.currentIndex() + 1
        if i == self._tabview.count(): i = 0
        while not self._tabview.isTabVisible(i):
            i += 1
            if i == self._tabview.count(): i = 0
        self._tabview.setCurrentIndex(i)
        QApplication.processEvents()

    def _previousTab(self) -> None:
        i = self._tabview.currentIndex() - 1
        if i < 0: i = self._tabview.count()
        while not self._tabview.isTabVisible(i):
            i -= 1
            if i < 0: i = self._tabview.count()
        self._tabview.setCurrentIndex(i)
        QApplication.processEvents()

    def updateTimers(self, index: int | None = None) -> None:
        if index is None: index = self._tabview.currentIndex()
        # Timer update
        for i in range(0, 4):
            w = self._tabview.widget(i)
            if i == index:  w.timerEnabled()
            else: w.timerDisabled()
            self._menuView[i].setEnabled(self._tabview.isTabVisible(i))

    # Settings public methods

    def getDisplayScaleFactor(self) -> float:
        return self.screen().devicePixelRatio()

    def setToolbarSize(self, size: int = _TOOLBARICONSIZE) -> None:
        self._toolbar.setFixedHeight(size + 8)
        self._toolbar.setIconSize(QSize(size, size))

    def setThumbnailSize(self, size: int = _THUMBNAILSIZE) -> None:
        self._thumbnail.setSize(size)

    def setHelpZoomFactor(self, zoom: float = 1.0) -> None:
        self._tabHelp.setZoomFactor(zoom)

    def setDockIconSize(self, size: int = _ICONSIZE) -> None:
        # < Revision 15/03/205
        # replace size + 8 by size
        self._tabROIList.setIconSize(size)
        self._tabROITools.setIconSize(size)
        self._tabMeshList.setIconSize(size)
        self._tabTargetList.setIconSize(size)
        self._tabTrackingList.setIconSize(size)
        self._tabHelp.setIconSize(size)
        # Revision 15/03/205 >

    # < Revision 17/03/2025
    # add setIconBarSize method
    def setIconBarSize(self, size: int | None) -> None:
        self._sliceview.setIconSize(size)
        self._orthoview.setIconSize(size)
        self._synchroview.setIconSize(size)
        self._projview.setIconSize(size)
        self._compview.setIconSize(size)
    # Revision 17/03/2025 >

    def setApplicationFont(self, name: str | QFont | None,
                           pointsize: int = 12):
        if name is None: name = self.font().defaultFamily()
        database = QFontDatabase()
        families = database.families()
        if isinstance(name, QFont): name = name.family()
        if name in families:
            font = QFont(name, pointSize=pointsize)
            QApplication.setFont(font)
            self.setFont(font)
            # noinspection PyProtectedMember
            self._console.setFont(font)
            try: path = font_manager.findfont(name, fallback_to_default=False)
            except: path = 'Arial'
            # < Revision 17/03/2025
            self._sliceview().setFontProperties((path, pointsize, None))
            self._orthoview().setFontProperties((path, pointsize, None))
            self._synchroview().setFontProperties((path, pointsize, None))
            self._projview().setFontProperties((path, pointsize, None))
            self._compview().setFontProperties((path, pointsize, None))
            # Revision 17/03/2025 >

    def setViewportsFontSize(self, s: int) -> None:
        if isinstance(s, int):
            self._sliceview().setFontSize(s)
            self._orthoview().setFontSize(s)
            self._synchroview().setFontSize(s)
            self._projview().setFontSize(s)
            # < Revision 17/03/2025
            self._compview().setFontSize(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not int.'.format(type(s)))

    def setViewportsFontScale(self, s: float) -> None:
        if isinstance(s, float):
            self._sliceview().setFontScale(s)
            self._orthoview().setFontScale(s)
            self._synchroview().setFontScale(s)
            self._projview().setFontScale(s)
            # < Revision 17/03/2025
            self._compview().setFontScale(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not float.'.format(type(s)))

    def setViewportsFontSizeScale(self, s: tuple[int, float]) -> None:
        if isinstance(s, tuple):
            self._sliceview().setFontSizeScale(s)
            self._orthoview().setFontSizeScale(s)
            self._synchroview().setFontSizeScale(s)
            self._projview().setFontSizeScale(s)
            # < Revision 17/03/2025
            self._compview().setFontSizeScale(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not tuple.'.format(type(s)))

    def setViewportFontProperties(self, s: tuple[str, int, float]) -> None:
        if isinstance(s, tuple):
            self._sliceview().setFontProperties(s)
            self._orthoview().setFontProperties(s)
            self._synchroview().setFontProperties(s)
            self._projview().setFontProperties(s)
            # < Revision 17/03/2025
            self._compview().setFontProperties(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not tuple.'.format(type(s)))

    def setViewportsFontFamily(self, s: str) -> None:
        if isinstance(s, str):
            self._sliceview().setFontFamily(s)
            self._orthoview().setFontFamily(s)
            self._synchroview().setFontFamily(s)
            self._projview().setFontFamily(s)
            # < Revision 17/03/2025
            self._compview().setFontFamily(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsLineWidth(self, s: float) -> None:
        if isinstance(s, float):
            self._sliceview().setLineWidth(s)
            self._orthoview().setLineWidth(s)
            self._synchroview().setLineWidth(s)
            self._projview().setLineWidth(s)
            # < Revision 17/03/2025
            self._compview().setLineWidth(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not float.'.format(type(s)))

    def setViewportsLineColor(self, c: list[float] | tuple[float, ...]) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                self._sliceview().setLineColor(c)
                self._orthoview().setLineColor(c)
                self._synchroview().setLineColor(c)
                self._projview().setLineColor(c)
                # < Revision 17/03/2025
                self._compview().setLineColor(c)
                # Revision 17/03/2025 >
            else: raise TypeError('invalid element count.')
        else: raise TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def setViewportsLineSelectedColor(self, c: list[float] | tuple[float, ...]) -> None:
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                self._sliceview().setLineSelectedColor(c)
                self._orthoview().setLineSelectedColor(c)
                self._synchroview().setLineSelectedColor(c)
                self._projview().setLineSelectedColor(c)
                # < Revision 17/03/2025
                self._compview().setLineSelectedColor(c)
                # Revision 17/03/2025 >
            else: raise TypeError('invalid element count.')
        else: raise TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def setViewportsLineOpacity(self, s: float) -> None:
        if isinstance(s, float):
            self._sliceview().setLineOpacity(s)
            self._orthoview().setLineOpacity(s)
            self._synchroview().setLineOpacity(s)
            self._projview().setLineOpacity(s)
            # < Revision 17/03/2025
            self._compview().setLineOpacity(s)
            # Revision 17/03/2025 >
        else: raise TypeError('parameter type {} is not float.'.format(type(s)))

    def setViewportsAttributesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoIdentityVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoVolumeVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoAcquisitionVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsOrientationLabelsVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
            self._projview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoPositionVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativeACCoordinatesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativePCCoordinatesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativeACPCCoordinatesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsFrameCoordinatesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsICBMCoordinatesVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoValueVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsCursorVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRulerPosition(self, s: str) -> None:
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsRulerVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsTooltipVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsColorbarPosition(self, s: str) -> None:
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setColorbarPosition(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setColorbarPosition(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setColorbarPosition(s)
            self._projview.getViewWidget().getFirstViewWidget().setColorbarPosition(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsColorbarVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setColorbarVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setColorbarVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setColorbarVisibility(v)
            self._projview.getViewWidget().getFirstViewWidget().setColorbarVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsOrientationMarkerShape(self, s: str) -> None:
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsOrientationMarkerVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsAlign(self, v: bool) -> None:
        if isinstance(v, bool):
            self._sliceview.setAlignCenters(v)
            self._orthoview.setAlignCenters(v)
            self._synchroview.setAlignCenters(v)
            self._projview.setAlignCenters(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    # Public methods

    def getActions(self) -> dict[str, QAction]:
        return self._action

    def toggleFullscreen(self) -> None:
        if self.isFullScreen():
            self._action['fullscrn'].setChecked(False)
            self.showMaximized()
            self._toolbar.setVisible(self._action['toolbar'].isChecked())
            self._thumbnail.setVisible(self._action['thumb'].isChecked())
            self._dock.setVisible(self._action['dock'].isChecked())
            self._status.setVisible(self._action['status'].isChecked())
            if platform == 'win32':
                self._menubar.setVisible(True)
            # < Revision 16/03/2025
            self._sliceview.getButtons()['screen'].setChecked(False)
            self._orthoview.getButtons()['screen'].setChecked(False)
            self._synchroview.getButtons()['screen'].setChecked(False)
            self._projview.getButtons()['screen'].setChecked(False)
            self._compview.getButtons()['screen'].setChecked(False)
            # Revision 16/03/2025 >
        else:
            self._action['fullscrn'].setChecked(True)
            self._toolbar.setVisible(False)
            self._thumbnail.setVisible(False)
            self._dock.setVisible(False)
            self._status.setVisible(False)
            if platform == 'win32':
                self._menubar.setVisible(False)
            self.showFullScreen()
            # < Revision 16/03/2025
            self._sliceview.getButtons()['screen'].setChecked(True)
            self._orthoview.getButtons()['screen'].setChecked(True)
            self._synchroview.getButtons()['screen'].setChecked(True)
            self._projview.getButtons()['screen'].setChecked(True)
            self._compview.getButtons()['screen'].setChecked(True)
            # Revision 16/03/2025 >
        if platform == 'win32':
            if self._tabview.currentIndex() == 0: self._sliceview().updateRender()
            elif self._tabview.currentIndex() == 1: self._orthoview().updateRender()
            elif self._tabview.currentIndex() == 2: self._synchroview().updateRender()
            elif self._tabview.currentIndex() == 3: self._projview().updateRender()
            elif self._tabview.currentIndex() == 4: self._compview().updateRender()

    def getToolbar(self) -> QToolBar:
        return self._toolbar

    def showToolbar(self) -> None:
        self._toolbar.setVisible(True)
        self._action['toolbar'].setChecked(True)

    def hideToolbar(self) -> None:
        self._toolbar.setVisible(False)
        self._action['toolbar'].setChecked(False)

    def setToolbarVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._toolbar.setVisible(v)
            self._action['toolbar'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getToolbarVisibility(self) -> bool:
        return self._toolbar.isVisible()

    def getThumbnail(self) -> ToolBarThumbnail:
        return self._thumbnail

    def showThumbnail(self) -> None:
        self._thumbnail.setVisible(True)
        self._action['thumb'].setChecked(True)

    def hideThumbnail(self) -> None:
        self._thumbnail.setVisible(False)
        self._action['thumb'].setChecked(False)

    def setThumbnailVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._thumbnail.setVisible(v)
            self._action['thumb'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getThumbnailVisibility(self) -> bool:
        return self._thumbnail.isVisible()

    def getDock(self) -> QTabWidget:
        return self._dock

    def showDock(self) -> None:
        self.setDockVisibility(True)

    def hideDock(self) -> None:
        self.setDockVisibility(False)

    def setDockVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._dock.setVisible(v)
            # Qt bug, dock inaccessible after masking
            # masking then showing status bar fixes bug
            self._status.setVisible(False)
            QApplication.processEvents()
            self._status.setVisible(True)
            self._action['dock'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getDockVisibility(self) -> bool:
        return self._dock.isVisible()

    def getDatabase(self) -> DatabaseWidget:
        return self._database

    def getScreenshots(self) -> ScreenshotsGridWidget:
        return self._captures

    def getHelp(self) -> TabHelpWidget:
        return self._tabHelp

    def getROIListWidget(self) -> TabROIListWidget:
        return self._tabROIList

    def getROIToolsWidget(self) -> TabROIToolsWidget:
        return self._tabROITools

    def getMeshListWidget(self) -> TabMeshListWidget:
        return self._tabMeshList

    def getTargetListWidget(self) -> TabTargetListWidget:
        return self._tabTargetList

    def getTrackingListWidget(self) -> TabTrackingWidget:
        return self._tabTrackingList

    def clearDockListWidgets(self) -> None:
        self._tabROIList.getROIListWidget().removeAll()
        self._tabMeshList.getMeshListWidget().removeAll()
        self._tabTargetList.getToolListWidget().removeAll()
        self._tabTrackingList.clear()
        self._tabROIList.setEnabled(False)
        self._tabROITools.setEnabled(False)
        self._tabMeshList.setEnabled(False)
        self._tabTargetList.setEnabled(False)
        self._tabTrackingList.setEnabled(False)
        self._dock.setTabVisible(0, False)
        self._dock.setTabVisible(1, False)
        self._dock.setTabVisible(2, False)
        self._dock.setTabVisible(3, False)
        self._dock.setTabVisible(4, False)

    def getStatusBar(self) -> QStatusBar:
        return self._status

    def updateMemoryUsage(self) -> None:
        self._statuslabel.setText(self.getMemoryUsage())

    def setStatusBarMessage(self, txt: str) -> None:
        if isinstance(txt, str):
            self._status.showMessage(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def showStatusBar(self) -> None:
        self._status.show()
        self._action['status'].setChecked(True)

    def hideStatusBar(self) -> None:
        self._status.hide()
        self._action['status'].setChecked(False)

    def setStatusBarVisibility(self, v: bool) -> None:
        if isinstance(v, bool):
            self._status.setVisible(v)
            self._action['status'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getStatusBarVisibility(self) -> bool:
        return self._status.isVisible()

    def showSliceView(self) -> None:
        self._tabview.setTabVisible(0, True)
        self._tabview.setCurrentIndex(0)

    def hideSliceView(self) -> None:
        self._tabview.setTabVisible(0, False)

    def setSliceViewVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(0, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSliceViewVisibility(self) -> bool:
        return self._tabview.isTabVisible(0)

    def showOrthogonalView(self) -> None:
        self._tabview.setTabVisible(1, True)
        self._tabview.setCurrentIndex(1)

    def hideOrthogonalView(self) -> None:
        self._tabview.setTabVisible(1, False)

    def setOrthogonalViewVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(1, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getOrthogonalViewVisibility(self) -> bool:
        return self._tabview.isTabVisible(1)

    def showSynchronisedView(self) -> None:
        self._tabview.setTabVisible(2, True)
        self._tabview.setCurrentIndex(2)

    def hideSynchronisedView(self) -> None:
        self._tabview.setTabVisible(2, False)

    def setSynchronisedViewVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(2, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSynchronisedViewVisibility(self) -> bool:
        return self._tabview.isTabVisible(2)

    def showProjectionView(self) -> None:
        self._tabview.setTabVisible(3, True)
        self._tabview.setCurrentIndex(3)

    def hideProjectionView(self) -> None:
        self._tabview.setTabVisible(3, False)

    def setProjectionViewVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(3, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getProjectionViewVisibility(self) -> bool:
        return self._tabview.isTabVisible(3)

    def showComponentView(self) -> None:
        self._tabview.setTabVisible(4, True)
        self._tabview.setCurrentIndex(4)

    def hideComponentView(self) -> None:
        self._tabview.setTabVisible(4, False)

    def setComponentViewVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(4, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getComponentViewVisibility(self) -> bool:
        return self._tabview.isTabVisible(4)

    def hideViewWidgets(self) -> None:
        for i in range(5):
            self._tabview.setTabVisible(i, False)

    def showDatabase(self) -> None:
        self._tabview.setTabVisible(5, True)
        self._tabview.setCurrentIndex(5)

    def hideDatabase(self) -> None:
        self._tabview.setTabVisible(5, False)

    def setDatabaseVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(5, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getDatabaseVisibility(self) -> bool:
        return self._tabview.isTabVisible(5)

    def showCaptures(self) -> None:
        self._tabview.setTabVisible(6, True)
        self._tabview.setCurrentIndex(6)

    def hideCaptures(self) -> None:
        self._tabview.setTabVisible(6, False)

    def setCapturesVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(6, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getCapturesVisibility(self) -> bool:
        return self._tabview.isTabVisible(6)

    def showConsole(self) -> None:
        self._tabview.setTabVisible(7, True)
        self._tabview.setCurrentIndex(7)

    def hideConsole(self) -> None:
        self._tabview.setTabVisible(7, False)

    def setConsoleVisibility(self, v: bool) -> None:
        if isinstance(v, bool): self._tabview.setTabVisible(7, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getConsoleVisibility(self) -> bool:
        return self._tabview.isTabVisible(7)

    def setTabViewVisibility(self, index: int, v: bool) -> None:
        if isinstance(index, int):
            if isinstance(v, bool):
                self._tabview.setTabVisible(index, v)
            else: raise TypeError('second parameter type {} is not bool.'.format(type(v)))
        else: raise TypeError('first parameter type {} is not int.'.format(type(index)))

    def setCurrentTabView(self, index: int) -> None:
        if 0 <= index < 8:
            self._tabview.setTabVisible(index, True)
            self._tabview.setCurrentIndex(index)
        else: raise ValueError('index must be between 0 and 7.')

    def setDockEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabROIList.setEnabled(v)
            self._dock.setTabVisible(0, v)
            self._tabMeshList.setEnabled(v)
            self._dock.setTabVisible(2, v)
            self._tabTargetList.setEnabled(v)
            self._dock.setTabVisible(3, v)
            self._tabTrackingList.setEnabled(v)
            self._dock.setTabVisible(4, v)
            if v is True:
                self._tabROIList.setViewCollection(self._views)
                self._tabROITools.setViewCollection(self._views)
                self._tabMeshList.setViewCollection(self._views)
                self._tabTargetList.setViewCollection(self._views)
                self._tabTrackingList.setViewCollection(self._views)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isDockEnabled(self) -> bool:
        return self._tabROIList.isEnabled()

    def setROIListEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabROIList.setEnabled(v)
            self._dock.setTabVisible(0, v)
            if not v:
                self._tabROIList.getROIListWidget().removeAll()
                self.setROIToolsEnabled(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isROIListEnabled(self) -> bool:
        return self._dock.isTabVisible(0)

    def setROIToolsEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabROITools.setEnabled(v)
            self._dock.setTabVisible(1, v)
            if v: self._tabROITools.updateThresholdWidget()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isROIToolsEnabled(self) -> bool:
        return self._dock.isTabVisible(1)

    def setMeshListEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabMeshList.setEnabled(v)
            self._dock.setTabVisible(2, v)
            if not v: self._tabMeshList.getMeshListWidget().removeAll()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isMeshListEnabled(self) -> bool:
        return self._dock.isTabVisible(2)

    def setTargetListEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabTargetList.setEnabled(v)
            self._dock.setTabVisible(3, v)
            if not v: self._tabTargetList.getToolListWidget().removeAll()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isTargetListEnabled(self) -> bool:
        return self._dock.isTabVisible(3)

    def setTrackingListEnabled(self, v: bool) -> None:
        if isinstance(v, bool):
            self._tabTrackingList.setEnabled(v)
            self._dock.setTabVisible(4, v)
            if not v: self._tabTrackingList.clear()
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isTrackingListEnabled(self) -> bool:
        return self._dock.isTabVisible(4)

    def addRecent(self, filename: str) -> None:
        self._recent.append(filename)

    # Display methods

    def displayInSliceView(self) -> None:
        if not self._thumbnail.isEmpty():
            try:
                if self._thumbnail.hasReference(): w = self._thumbnail.getSelectedWidget()
                else: w = self._thumbnail.getWidgetFromIndex(0)
                if not w.isDisplayedInSliceView():
                    w.getActions()['slices'].setChecked(True)
                    w.displayInSliceView()
                else: self.showSliceView()
            except Exception as err:
                messageBox(self, 'Display in slice view error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else: messageBox(self,
                         'Display in slice view...',
                         'No volume loaded in thumbnail.')

    def displayInOrthogonalView(self) -> None:
        if not self._thumbnail.isEmpty():
            try:
                if self._thumbnail.hasReference(): w = self._thumbnail.getSelectedWidget()
                else: w = self._thumbnail.getWidgetFromIndex(0)
                if not w.isDisplayedInOrthogonalView():
                    w.getActions()['orthogonal'].setChecked(True)
                    w.displayInOrthogonalView()
                else: self.showOrthogonalView()
            except Exception as err:
                messageBox(self, 'Display in orthogonal view error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else: messageBox(self,
                         'Display in orthogonal view...',
                         'No volume loaded in thumbnail.')

    def displayInSynchronisedView(self) -> None:
        if not self._thumbnail.isEmpty():
            try:
                if self._thumbnail.hasReference(): w = self._thumbnail.getSelectedWidget()
                else: w = self._thumbnail.getWidgetFromIndex(0)
                if not w.isDisplayedInSynchronisedView():
                    w.getActions()['synchronised'].setChecked(True)
                    w.displayInSynchronisedView()
                else: self.showSynchronisedView()
            except Exception as err:
                messageBox(self, 'Display in synchronized view error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else: messageBox(self,
                         'Display in synchronised view...',
                         'No volume loaded in thumbnail.')

    def displayInProjectionView(self) -> None:
        if not self._thumbnail.isEmpty():
            try:
                if self._thumbnail.hasReference(): w = self._thumbnail.getSelectedWidget()
                else: w = self._thumbnail.getWidgetFromIndex(0)
                if not w.isDisplayedInProjectionView():
                    w.getActions()['projections'].setChecked(True)
                    w.displayInProjectionView()
                else: self.showProjectionView()
            except Exception as err:
                messageBox(self, 'Display in projection view error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else: messageBox(self,
                         'Display in projection view...',
                         'No volume loaded in thumbnail.')

    def displayInComponentView(self) -> None:
        if not self._thumbnail.isEmpty():
            try:
                if self._thumbnail.hasReference(): w = self._thumbnail.getSelectedWidget()
                else: w = self._thumbnail.getWidgetFromIndex(0)
                v = w.getVolume()
                if v.getNumberOfComponentsPerPixel() > 1:
                    if not w.isDisplayedInMultiComponentView():
                        w.getActions()['multi'].setChecked(True)
                        w.displayInMultiComponentView()
                    else: self.showComponentView()
                else:
                    messageBox(self,
                               'Display in multi-component view...',
                               '{} reference volume is single-component.'.format(v.getBasename()))
            except Exception as err:
                messageBox(self, 'Display in multi-component view error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            messageBox(self,
                       'Display in multi-component view...',
                       'No volume loaded in thumbnail.')

    # Application methods called from main menu

    def exit(self) -> None:
        self._recent.save()
        self.close()

    def about(self) -> None:
        from Sisyphe.gui.dialogSplash import DialogSplash
        self._dialog = DialogSplash()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        self._dialog.buttonVisibilityOn()
        self._dialog.progressBarVisibilityOff()
        try: self._dialog.exec()
        except Exception as err:
            messageBox(self, 'About dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def preferences(self) -> None:
        if self._dialogSettings is not None:
            try: self._dialogSettings.exec()
            except Exception as err:
                messageBox(self, 'Preferences dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    # File methods called from main menu

    def open(self, filenames: str | list[str] | None = None) -> None:
        try: self._thumbnail.open(filenames)
        except Exception as err:
            messageBox(self, 'Open xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def save(self) -> None:
        try: self._thumbnail.saveSelected()
        except Exception as err:
            messageBox(self, 'Save xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def saveall(self) -> None:
        try: self._thumbnail.saveAll()
        except Exception as err:
            messageBox(self, 'Save all xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def saveAs(self) -> None:
        try: self._thumbnail.saveSelectedAs()
        except Exception as err:
            messageBox(self, 'Save xvol as error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def remove(self) -> None:
        try: self._thumbnail.removeSelected()
        except Exception as err:
            messageBox(self, 'Remove selected xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def removeAll(self) -> None:
        try: self._thumbnail.removeAll()
        except Exception as err:
            messageBox(self, 'Remove all xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def loadNifti(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open Nifti...', getcwd(),
                                                     filter='Nifti (*.nii *.hdr *.img *.nia *.nii.gz *.img.gz)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Nifti...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromNIFTI(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open Nifti error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadMinc(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open Minc...', getcwd(), filter='Minc (*.mnc *.minc)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Minc...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromMINC(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open Minc error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadNrrd(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open Nrrd...', getcwd(), filter='Nrrd (*.nrrd *.nhdr)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Nrrd...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromNRRD(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open Nrrd error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadVtk(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open Vtk...', getcwd(), filter='Vtk (*.vti *.vtk)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Vtk...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromVTK(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open Vtk error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadSis(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open Sisyphe...', getcwd(), 'Sisyphe (*.vol)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Sisyphe...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromSisyphe(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open Sisyphe error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadVmr(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open BrainVoyager VMR...',
                                                     getcwd(), 'BrainVoyager VMR (*.vmr)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open BrainVoyager VMR...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromBrainVoyagerVMR(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open BrainVoyager VMR error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def loadMgh(self, filenames: str | list[str] | None = None) -> None:
        if filenames is None:
            filenames = QFileDialog.getOpenFileNames(self, 'Open FreeSurfer MGH...',
                                                     getcwd(), 'FreeSurfer MGH (*.mgh *.mgz)')[0]
            QApplication.processEvents()
        elif isinstance(filenames, str): filenames = [filenames]
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open FreeSurfer MGH...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, cancel=cancel)
            wait.open()
            try:
                for filename in filenames:
                    filename = abspath(filename)
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    self._logger.info('Open {}'.format(filename))
                    v = SisypheVolume()
                    v.loadFromFreeSurferMGH(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
                    self.setStatusBarMessage('Open {}'.format(basename(filename)))
            except Exception as err:
                messageBox(self, 'Open FreeSurfer MGH error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
            wait.close()

    def saveNifti(self) -> None:
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Nifti', vol.getFilename(),
                                                   filter='Nifti (*.nii)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try:
                    self._logger.info('Save {}'.format(filename))
                    vol.saveToNIFTI(filename)
                    self.setStatusBarMessage('{} saved'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Save Nifti error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
        else: messageBox(self, 'Save Nifti', 'No volume selected.')

    def saveMinc(self) -> None:
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Minc', vol.getFilename(),
                                                   filter='Minc (*.mnc)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try:
                    self._logger.info('Save {}'.format(filename))
                    vol.saveToMINC(filename)
                    self.setStatusBarMessage('{} saved'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Save Minc error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
        else: messageBox(self, 'Save Minc', 'No volume selected.')

    def saveNrrd(self) -> None:
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Nrrd', vol.getFilename(),
                                                   filter='Nrrd (*.nrrd)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try:
                    self._logger.info('Save {}'.format(filename))
                    vol.saveToNRRD(filename)
                    self.setStatusBarMessage('{} saved'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Save Nrrd error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
        else: messageBox(self, 'Save Nrrd', 'No volume selected.')

    def saveVtk(self) -> None:
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save VTK', vol.getFilename(),
                                                   filter='VTK (*.vti)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try:
                    self._logger.info('Save {}'.format(filename))
                    vol.saveToVTK(filename)
                    self.setStatusBarMessage('{} saved'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Save Vtk error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
        else: messageBox(self, 'Save VTK', 'No volume selected.')

    def saveNumpy(self) -> None:
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Numpy', vol.getFilename(),
                                                   filter='Numpy (*.npy)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try:
                    self._logger.info('Save {}'.format(filename))
                    vol.saveToNumpy(filename)
                    self.setStatusBarMessage('{} saved'.format(vol.getBasename()))
                except Exception as err:
                    messageBox(self, 'Save Numpy error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
        else: messageBox(self, 'Save Numpy', 'No volume selected.')

    def importNifti(self) -> None:
        from Sisyphe.gui.dialogImport import DialogImport
        self._dialog = DialogImport(io='Nifti', parent=self)
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogImport.DialogImport - Nifti]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Nifti dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importMinc(self) -> None:
        from Sisyphe.gui.dialogImport import DialogImport
        self._dialog = DialogImport(io='Minc', parent=self)
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogImport.DialogImport - Minc]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Minc dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importNrrd(self) -> None:
        from Sisyphe.gui.dialogImport import DialogImport
        self._dialog = DialogImport(io='Nrrd', parent=self)
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogImport.DialogImport - Nrrd]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Nrrd dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importVtk(self) -> None:
        from Sisyphe.gui.dialogImport import DialogImport
        self._dialog = DialogImport(io='Vtk', parent=self)
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogImport.DialogImport - Vtk]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Vtk dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importSis(self) -> None:
        from Sisyphe.gui.dialogOldSisypheImport import DialogOldSisypheImport
        # < Revision 16/04/2025
        # self._dialog = DialogOldSisypheImport(parent=self)
        self._dialog = DialogOldSisypheImport()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogOldSisypheImport.DialogOldSisypheImport - Sisyphe]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Sisyphe dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importDicom(self) -> None:
        from Sisyphe.gui.dialogDicomImport import DialogDicomImport
        # < Revision 16/04/2025
        # self._dialog = DialogDicomImport(parent=self)
        self._dialog = DialogDicomImport()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDicomImport.DialogDicomImport]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Dicom dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def importDicomRT(self) -> None:
        from Sisyphe.gui.dialogDicomRTimport import DialogRTimport
        # < Revision 16/04/2025
        # self._dialog = DialogRTimport(parent=self)
        self._dialog = DialogRTimport()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDicomRTimport.DialogRTimport]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Import Dicom RT dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportNifti(self) -> None:
        from Sisyphe.gui.dialogExport import DialogExport
        self._dialog = DialogExport(io='Nifti')
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogExport.DialogExport - Nifti]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Export Nifti dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportMinc(self) -> None:
        from Sisyphe.gui.dialogExport import DialogExport
        self._dialog = DialogExport(io='Minc')
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogExport.DialogExport - Minc]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Export Minc dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportNrrd(self) -> None:
        from Sisyphe.gui.dialogExport import DialogExport
        self._dialog = DialogExport(io='Nrrd')
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogExport.DialogExport - Nrrd]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Export Nrrd dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportVtk(self) -> None:
        from Sisyphe.gui.dialogExport import DialogExport
        self._dialog = DialogExport(io='Vtk')
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogExport.DialogExport - Vtk]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Export Vtk dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportNumpy(self) -> None:
        from Sisyphe.gui.dialogExport import DialogExport
        self._dialog = DialogExport(io='Numpy')
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogExport.DialogExport - Numpy]')
            self._dialog.show()
        except Exception as err:
            messageBox(self, 'Export Numpy dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def exportDicom(self) -> None:
        from Sisyphe.gui.dialogDicomExport import DialogDicomExport
        # < Revision 16/04/2025
        # self._dialog = DialogDicomExport(parent=self)
        self._dialog = DialogDicomExport()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDicomExport.DialogDicomExport]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'DICOM Export dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def datasetDicom(self) -> None:
        from Sisyphe.gui.dialogDicomDataset import DialogDicomDataset
        self._dialog = DialogDicomDataset()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDicomDataset.DialogDicomDataset]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'DICOM Dataset dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def xmlDicom(self) -> None:
        from Sisyphe.core.sisypheDicom import XmlDicom
        filename = QFileDialog.getOpenFileName(self, 'Open Xml Dicom...', getcwd(),
                                               filter=XmlDicom.getFilterExt())[0]
        if filename:
            chdir(dirname(filename))
            from Sisyphe.gui.dialogXmlDicom import DialogXmlDicom
            self._dialog = DialogXmlDicom(filename)
            if platform == 'win32':
                try: __main__.updateWindowTitleBarColor(self._dialog)
                except: pass
            try:
                self._logger.info('Dialog exec [gui.dialogXmlDicom.DialogXmlDicom]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Xml DICOM Attributes dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def editAttr(self) -> None:
        self._thumbnail.editAttributesSelected()

    def editID(self) -> None:
        from Sisyphe.gui.dialogDatatype import DialogEditID
        # < Revision 16/04/2025
        # dialog = DialogEditID(parent=self)
        self._dialog = DialogEditID()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDatatype.DialogEditID]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'ID replacement dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def anonymize(self) -> None:
        # < Revision 16/04/2025
        # self._dialog = DialogFilesSelection(parent=self)
        self._dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        self._dialog.setWindowTitle('Anonymize volume(s)')
        self._dialog.filterSisypheVolume()
        wait = None
        try:
            self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Anonymize]')
            if self._dialog.exec():
                filenames = self._dialog.getFilenames()
                n = len(filenames)
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Anonymize...')
                wait.setProgressRange(0, n-1)
                wait.setProgressVisibility(n > 1)
                for i in range(n):
                    if exists(filenames[i]):
                        wait.setInformationText('Anonymize {}...'.format(basename(filenames[i])))
                        wait.incCurrentProgressValue()
                        v = SisypheVolume()
                        v.load(filenames[i])
                        v.identity.anonymize()
                        v.save()
                wait.close()
        except Exception as err:
            messageBox(self, 'Anonymize error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())
            if wait is not None: wait.close()

    def editLabels(self, filename: str | SisypheVolume = '') -> None:
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
            if not v.acquisition.isLB():
                messageBox(self,
                           self.windowTitle(),
                           '{} is not a label volume.'.format(v.getBasename()))
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                # < Revision 16/04/2025
                # dialog = DialogFileSelection(parent=self)
                dialog = DialogFileSelection()
                # Revision 16/04/2025 >
                if platform == 'win32':
                    try: __main__.updateWindowTitleBarColor(dialog)
                    except: pass
                dialog.setWindowTitle('Edit labels')
                dialog.filterSisypheVolume()
                dialog.filterSameModality('LB')
                try:
                    self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFileSelection - Edit labels]')
                    if dialog.exec():
                        filename = dialog.getFilename()
                except Exception as err:
                    messageBox(self, 'File selection/Edit labels error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            from Sisyphe.gui.dialogEditLabels import DialogEditLabels
            self._dialog = DialogEditLabels()
            if platform == 'win32':
                try: __main__.updateWindowTitleBarColor(self._dialog)
                except: pass
            self._dialog.setVolume(v)
            try:
                self._logger.info('gui.dialogFileSelection.DialogFileSelection - Edit labels')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Edit labels dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def volToLabel(self) -> None:
        from Sisyphe.gui.dialogLabel import DialogVOLtoLabel
        self._dialog = DialogVOLtoLabel()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogLabel.DialogVOLtoLabel]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Volumes to label volume dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def roiToLabel(self) -> None:
        from Sisyphe.gui.dialogLabel import DialogROItoLabel
        self._dialog = DialogROItoLabel()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogLabel.DialogROItoLabel]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'ROIs to label volume dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def labelToRoi(self) -> None:
        from Sisyphe.gui.dialogLabel import DialogLabeltoROI
        self._dialog = DialogLabeltoROI()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogLabel.DialogLabeltoROI]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Label volume to ROIs dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def download(self) -> None:
        from Sisyphe.gui.dialogDownload import DialogDownload
        filename = join(DialogDownload.getSettingsFolder(), 'host.xml')
        if not exists(filename):
            wait = DialogWait()
            wait.open()
            wait.progressVisibilityOff()
            wait.setInformationText('Host connection...')
            QApplication.processEvents()
            # Connect to host as anonymous & Download version.xml
            from Sisyphe.version import getVersionFromHost
            v = getVersionFromHost()
            wait.close()
            if v == '':
                messageBox(self,
                           self.windowTitle(),
                           'Failed to connect to host.')
                return
        # < Revision 16/04/2025
        # self._dialog = DialogDownload(parent=self)
        self._dialog = DialogDownload()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogDownload.DialogDownload]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Download manager dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())
        self._updatePluginsMenu()

    def checkUpdate(self) -> None:
        from Sisyphe import version
        wait = DialogWait(progress=False)
        wait.open()
        wait.setInformationText('Check for update, connection to host...')
        QApplication.processEvents()
        try: v = version.getVersionFromHost()
        except:
            wait.close()
            messageBox(self,
                       'Check for update',
                       'Host connection failed.')
            return
        if version.isCurrentVersion(v):
            wait.close()
            messageBox(self,
                       'Check for update',
                       'PySisyphe is up-to-date'.format(version.__version__),
                       icon=QMessageBox.Information)
        elif version.isOlderThan(v):
            wait.hide()
            r = messageBox(self,
                           'Check for update',
                           'A more recent version of PySisyphe is available.'
                           '\nWould you like to install it ?',
                           icon=QMessageBox.Question,
                           buttons=QMessageBox.Yes | QMessageBox.No,
                           default=QMessageBox.No)
            if r == QMessageBox.Yes:
                from Sisyphe.core.sisypheDownload import updatePySisyphe
                wait.setInformationText('Update to version {}...'.format(v))
                wait.show()
                updatePySisyphe(wait)
            wait.close()

    def lutEdit(self) -> None:
        from Sisyphe.gui.dialogLutEdit import DialogLutEdit
        self._dialog = DialogLutEdit()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        try:
            self._logger.info('Dialog exec [gui.dialogLutEdit.DialogLutEdit]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'LUT Edit dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # Function methods called from main menu

    def join(self) -> None:
        title = 'Join single component volume(s)'
        # < Revision 16/05/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        dialog.setMaximumNumberOfFiles(300)
        # Revision 16/05/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 0:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=n,
                                  progresstxt=True, cancel=False)
                wait.open()
                wait.setInformationText(title)
                vols = list()
                for filename in filenames:
                    v = SisypheVolume()
                    v.load(filename)
                    vols.append(v)
                try: img = multiComponentSisypheVolumeFromList(vols)
                except Exception as err:
                    messageBox(self, 'Join error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                    img = None
                wait.close()
                if img is not None:
                    img.setFilename(filenames[0])
                    img.setFilenamePrefix('Multi_')
                    filename = QFileDialog.getSaveFileName(self, title, img.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        QApplication.processEvents()
                        if filename: img.saveAs(filename)

    def split(self) -> None:
        title = 'Split multi component volume(s)'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterMultiComponent()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 0:
                wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                                  progresstxt=True, cancel=False)
                wait.open()
                for filename in filenames:
                    wait.setInformationText('Split {}'.format(basename(filename)))
                    wait.incCurrentProgressValue()
                    img = SisypheVolume()
                    img.load(filename)
                    nb = img.getNumberOfComponentsPerPixel()
                    if nb > 1:
                        fix = len(str(nb))
                        for i in range(nb):
                            try:
                                cimg = img.copyComponent(i)
                                cimg.copyPropertiesFrom(img)
                                suffix = '#' + str(i).zfill(fix)
                                cimg.setFilename(img.getFilename())
                                cimg.setFilenameSuffix(suffix)
                                cimg.save()
                            except Exception as err:
                                messageBox(self, 'Split error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                    wait.close()

    def datatype(self) -> None:
        from Sisyphe.gui.dialogDatatype import DialogDatatype
        self._dialog = DialogDatatype()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        self._dialog.getFileSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDatatype.DialogDatatype]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Datatype conversion dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def attributes(self) -> None:
        from Sisyphe.gui.dialogDatatype import DialogAttributes
        self._dialog = DialogAttributes()
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        self._dialog.getFileSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDatatype.DialogAttributes]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Attributes conversion dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def flip(self,
             filenames: str | list[str] | None = None,
             params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFlipAxes import DialogFlipAxes
        # < Revision 16/04/2025
        # dialog = DialogFlipAxes(parent=self)
        self._dialog = DialogFlipAxes()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            self._dialog.accept()
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogFlipAxes.DialogFlipAxes]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Flip axis dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def swap(self,
             filenames: str | list[str] | None = None,
             params: dict | None = None) -> None:
        from Sisyphe.gui.dialogSwapAxes import DialogSwapAxes
        # < Revision 16/04/2025
        # dialog = DialogSwapAxes(parent=self)
        self._dialog = DialogSwapAxes()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            self._dialog.accept()
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogSwapAxes.DialogSwapAxes]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Permute axis dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def neck(self,
             filenames: str | list[str] | None = None,
             params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogRemoveNeckSlices
        # < Revision 16/04/2025
        # self._dialog = DialogRemoveNeckSlices(parent=self)
        self._dialog = DialogRemoveNeckSlices()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(self._dialog)
            except: pass
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogRemoveNeckSlices]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Remove neck slices dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogRemoveNeckSlices]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Remove neck slices dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def algmean(self) -> None:
        title = 'Mean volume calculation'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Mean volume]')
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, cancel=False)
                wait.open()
                wait.setInformationText(title)
                QApplication.processEvents()
                try:
                    l = list()
                    v = None
                    for filename in filenames:
                        v = SisypheVolume()
                        v.load(filename)
                        l.append(v.copyToNumpyArray())
                    a = stack(l)
                    r = nanmean(a, axis=0)
                    m = SisypheVolume()
                    m.copyFromNumpyArray(r, spacing=v.getSpacing())
                    m.copyAttributesFrom(v, display=False)
                    m.setFilename(filenames[0])
                    m.setFilenamePrefix('Mean')
                    wait.hide()
                    filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        m.updateArrayID()
                        m.saveAs(filename)
                        self._logger.info('Mean volume processing - Save {}'.format(filename))
                except Exception as err:
                    wait.hide()
                    messageBox(self, 'Mean volume error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                wait.close()

    def algmedian(self) -> None:
        title = 'Median volume calculation'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Median volume]')
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, cancel=False)
                wait.open()
                wait.setInformationText(title)
                QApplication.processEvents()
                try:
                    l = list()
                    v = None
                    for filename in filenames:
                        v = SisypheVolume()
                        v.load(filename)
                        l.append(v.copyToNumpyArray())
                    a = stack(l)
                    r = nanmedian(a, axis=0)
                    m = SisypheVolume()
                    m.copyFromNumpyArray(r, spacing=v.getSpacing())
                    m.copyAttributesFrom(v, display=False)
                    m.setFilename(filenames[0])
                    m.setFilenamePrefix('Median')
                    wait.hide()
                    filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        m.updateArrayID()
                        m.saveAs(filename)
                        self._logger.info('Median volume processing - Save {}'.format(filename))
                except Exception as err:
                    wait.hide()
                    messageBox(self, 'Median volume error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                wait.close()

    def algstd(self) -> None:
        title = 'Standard deviation volume calculation'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Standard deviation volume]')
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, cancel=False)
                wait.open()
                wait.setInformationText(title)
                QApplication.processEvents()
                try:
                    l = list()
                    v = None
                    for filename in filenames:
                        v = SisypheVolume()
                        v.load(filename)
                        l.append(v.copyToNumpyArray())
                    a = stack(l)
                    r = nanstd(a, axis=0)
                    m = SisypheVolume()
                    m.copyFromNumpyArray(r, spacing=v.getSpacing())
                    m.copyAttributesFrom(v, display=False)
                    m.setFilename(filenames[0])
                    m.setFilenamePrefix('Std')
                    wait.hide()
                    filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        m.updateArrayID()
                        m.saveAs(filename)
                        self._logger.info('Standard deviation volume processing - Save {}'.format(filename))
                except Exception as err:
                    wait.hide()
                    messageBox(self, 'Standard deviation volume error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                wait.close()

    def algmin(self) -> None:
        title = 'Minimum volume calculation'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32':
            try: __main__.updateWindowTitleBarColor(dialog)
            except: pass
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Minimum volume]')
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, cancel=False, parent=self)
                wait.open()
                wait.setInformationText(title)
                QApplication.processEvents()
                try:
                    l = list()
                    v = None
                    for filename in filenames:
                        v = SisypheVolume()
                        v.load(filename)
                        l.append(v.copyToNumpyArray())
                    a = stack(l)
                    r = nanmin(a, axis=0)
                    m = SisypheVolume()
                    m.copyFromNumpyArray(r, spacing=v.getSpacing())
                    m.copyAttributesFrom(v, display=False)
                    m.setFilename(filenames[0])
                    m.setFilenamePrefix('Min')
                    wait.hide()
                    filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        m.updateArrayID()
                        m.saveAs(filename)
                        self._logger.info('Minimum volume processing - Save {}'.format(filename))
                except Exception as err:
                    wait.hide()
                    messageBox(self, 'Minimum volume error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                wait.close()

    def algmax(self) -> None:
        title = 'Maximum volume calculation'
        # < Revision 16/04/2025
        # dialog = DialogFilesSelection(parent=self)
        dialog = DialogFilesSelection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(dialog)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogFilesSelection - Maximum volume]')
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, cancel=False, parent=self)
                wait.open()
                wait.setInformationText(title)
                QApplication.processEvents()
                try:
                    l = list()
                    v = None
                    for filename in filenames:
                        v = SisypheVolume()
                        v.load(filename)
                        l.append(v.copyToNumpyArray())
                    a = stack(l)
                    r = nanmax(a, axis=0)
                    m = SisypheVolume()
                    m.copyFromNumpyArray(r, spacing=v.getSpacing())
                    m.copyAttributesFrom(v, display=False)
                    m.setFilename(filenames[0])
                    m.setFilenamePrefix('Max')
                    wait.hide()
                    filename = QFileDialog.getSaveFileName(self, title, m.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    if filename:
                        chdir(dirname(filename))
                        m.updateArrayID()
                        m.saveAs(filename)
                        self._logger.info('Maximum volume processing - Save {}'.format(filename))
                except Exception as err:
                    wait.hide()
                    messageBox(self, 'Maximum volume error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                wait.close()

    def algmath(self) -> None:
        from Sisyphe.gui.dialogAlgebra import DialogAlgebra
        # < Revision 16/04/2025
        # self._dialog = DialogAlgebra(parent=self)
        self._dialog = DialogAlgebra()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogAlgebra.DialogAlgebra]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Algebra dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def texture(self,
                filenames: str | list[str] | None = None,
                params: dict | None = None) -> None:
        from Sisyphe.gui.dialogTexture import DialogTexture
        # < Revision 16/04/2025
        # self._dialog = DialogTexture(parent=self)
        self._dialog = DialogTexture()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogTexture.DialogTexture]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Texture feature maps dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogTexture.DialogTexture]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Texture feature maps dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def histmatch(self,
                  filenames: str | list[str] | None = None,
                  reference: str | None = None,
                  params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogHistogramIntensityMatching
        # < Revision 16/04/2025
        # self._dialog = DialogHistogramIntensityMatching(parent=self)
        self._dialog = DialogHistogramIntensityMatching()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            self._dialog.setReference(reference)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogHistogramIntensityMatching]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Histogram inensity matching dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogHistogramIntensityMatching]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Histogram inensity matching dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def regmatch(self,
                 filenames: str | list[str] | None = None,
                 reference: str | None = None,
                 params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogRegressionIntensityMatching
        # < Revision 16/04/2025
        # self._dialog = DialogRegressionIntensityMatching(parent=self)
        self._dialog = DialogRegressionIntensityMatching()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            self._dialog.setReference(reference)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogRegressionIntensityMatching]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Regression inensity matching dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogRegressionIntensityMatching]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Regression inensity matching dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def signalNorm(self,
                   filenames: str | list[str] | None = None,
                   params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogIntensityNormalization
        # < Revision 16/04/2025
        # self._dialog = DialogIntensityNormalization(parent=self)
        self._dialog = DialogIntensityNormalization()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogIntensityNormalization]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Signal normalization dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogIntensityNormalization]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Signal normalization dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterMean(self,
                   filenames: str | list[str] | None = None,
                   params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogMeanFilter
        # < Revision 16/04/2025
        # self._dialog = DialogMeanFilter(parent=self)
        self._dialog = DialogMeanFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogMeanFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Mean filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogMeanFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Mean filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterMedian(self,
                     filenames: str | list[str] | None = None,
                     params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogMedianFilter
        # < Revision 16/04/2025
        # self._dialog = DialogMedianFilter(parent=self)
        self._dialog = DialogMedianFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogMedianFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Median filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogMedianFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Median filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterGaussian(self,
                       filenames: str | list[str] | None = None,
                       params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogGaussianFilter
        # < Revision 16/04/2025
        # self._dialog = DialogGaussianFilter(parent=self)
        self._dialog = DialogGaussianFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogGaussianFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Gaussian filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogGaussianFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Gaussian filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterGradient(self,
                       filenames: str | list[str] | None = None,
                       params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogGradientFilter
        # < Revision 16/04/2025
        # self._dialog = DialogGradientFilter(parent=self)
        self._dialog = DialogGradientFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogGradientFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Gradient magnitude filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogGradientFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Gradient magnitude filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterLaplacian(self,
                        filenames: str | list[str] | None = None,
                        params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogLaplacianFilter
        # < Revision 16/04/2025
        # self._dialog = DialogLaplacianFilter(parent=self)
        self._dialog = DialogLaplacianFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogLaplacianFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Laplacian filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogLaplacianFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Laplacian filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterAniso(self,
                    filenames: str | list[str] | None = None,
                    params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogAnisotropicDiffusionFilter
        # < Revision 16/04/2025
        # self._dialog = DialogAnisotropicDiffusionFilter(parent=self)
        self._dialog = DialogAnisotropicDiffusionFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogAnisotropicDiffusionFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Anisotropic diffusion filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogAnisotropicDiffusionFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Anisotropic diffusion filter dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def filterBias(self,
                   filenames: str | list[str] | None = None,
                   params: dict | None = None) -> None:
        from Sisyphe.gui.dialogFunction import DialogBiasFieldCorrectionFilter
        # < Revision 16/04/2025
        # self._dialog = DialogBiasFieldCorrectionFilter(parent=self)
        self._dialog = DialogBiasFieldCorrectionFilter()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogBiasFieldCorrectionFilter]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Bias field correction dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogFunction.DialogBiasFieldCorrectionFilter]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Bias field correction dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def automate(self) -> None:
        from Sisyphe.gui.dialogWorkflow import DialogWorkflow
        # < Revision 16/04/2025
        # self._dialog = DialogWorkflow(parent=self)
        self._dialog = DialogWorkflow()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogWorkflow.DialogWorkflow]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Workflow processing dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def getPluginList(self) -> list[str]:
        path = join(self.getMainDirectory(), 'plugins', '**')
        r = list()
        for d in glob(path):
            if isdir(d): r.append(basename(d))
        return r

    def addPlugin(self, plugin: str = '') -> None:
        try:
            if plugin == '':
                plugin = QFileDialog.getOpenFileName(self, 'Select a plugin zip archive...', getcwd(),
                                                     filter='ZIP file (*.zip)')[0]
            if plugin:
                chdir(dirname(plugin))
                name = splitext(basename(plugin))[0]
                if name not in self.getPluginList():
                    if is_zipfile(plugin):
                        with ZipFile(plugin, 'r') as fzip:
                            flist = fzip.namelist()
                            r = join(name, '') in flist
                            r = r and (join(name, '__init__.py') in flist)
                            r = r and (join(name, '{}.py'.format(name)) in flist)
                            if r:
                                dst = join(self.getMainDirectory(), 'plugins')
                                fzip.extractall(dst)
                                path = join(dst, '__MACOSX')
                                if exists(path): rmtree(path)
                                self._updatePluginsMenu()
                                messageBox(self,
                                           'Install plugin',
                                           '{} plugin has been successfully installed.'.format(name),
                                           icon=QMessageBox.Information)
                                self._logger.info('Plugin {} installed.'.format(name))
                                self.setStatusBarMessage('Plugin {} installed.'.format(name))
                            else:
                                messageBox(self,
                                           'Install plugin',
                                           '{} is not a valid plugin archive.'.format(basename(plugin)))
                    else:
                        messageBox(self,
                                   'Install plugin',
                                   '{} is not a valid ZIP archive.'.format(basename(plugin)))
                else:
                    messageBox(self,
                               'Install plugin',
                               '{} plugin is already installed.'.format(basename(plugin)))
        except Exception as err:
            messageBox(self, 'Plugin installation error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def removePlugin(self, plugin: str = '') -> None:
        try:
            l = self.getPluginList()
            if len(l) > 0:
                if plugin != '' and plugin in l:
                    path = join(self.getMainDirectory(), 'plugins', plugin)
                    if exists(path):
                        rmtree(path)
                        self._updatePluginsMenu()
                        messageBox(self,
                                   'Remove plugin',
                                   '{} plugin has been successfully removed.'.format(plugin),
                                   icon=QMessageBox.Information)
                else:
                    path = join(self.getMainDirectory(), 'plugins')
                    plugin = QFileDialog.getExistingDirectory(self,
                                                              'Select plugin to remove...',
                                                              path, options=QFileDialog.ShowDirsOnly)
                    if plugin:
                        chdir(dirname(plugin))
                        if self.getMainDirectory() in plugin:
                            rmtree(plugin)
                            self._updatePluginsMenu()
                            name = splitext(basename(plugin))[0]
                            messageBox(self,
                                       'Remove plugin',
                                       '{} plugin has been successfully removed.'.format(name),
                                       icon=QMessageBox.Information)
                            self._logger.info('Plugin {} removed.'.format(name))
                            self.setStatusBarMessage('Plugin {} removed.'.format(name))
                        else:
                            messageBox(self,
                                       'Remove plugin',
                                       '{} is not a plugin directory.'.format(basename(plugin)))
            else: self._updatePluginsMenu()
        except Exception as err:
            messageBox(self, 'Remove plugin error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # Registration methods called from main menu

    def frameDetection(self, filename: str = '') -> None:
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                # < Revision 16/04/2025
                # dialog = DialogFileSelection(parent=self)
                dialog = DialogFileSelection()
                # Revision 16/04/2025 >
                if platform == 'win32': __main__.updateWindowTitleBarColor(dialog)
                dialog.setWindowTitle('Stereotactic frame detection')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            fid = SisypheFiducialBox()
            filename = v.getFilename()
            if fid.hasXML(filename):
                try:
                    fid.loadFromXML(filename)
                    fid.setVolume(v)
                    fid.calcTransform()
                    fid.calcErrors()
                except Exception as err:
                    messageBox(self, 'Stereotactic frame detection error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
                    return
            else:
                wait = DialogWait(title='Stereotactic frame detection')
                fid.ProgressTextChanged.connect(wait.setInformationText)
                fid.ProgressRangeChanged.connect(wait.setProgressRange)
                fid.ProgressValueChanged.connect(wait.setCurrentProgressValue)
                wait.open()
                wait.setInformationText('Geometric transformation calculation...')
                wait.setProgressVisibility(True)
                if fid.markersSearch(v):
                    fid.ProgressTextChanged.disconnect(wait.setInformationText)
                    fid.ProgressRangeChanged.disconnect(wait.setProgressRange)
                    fid.ProgressValueChanged.disconnect(wait.setCurrentProgressValue)
                    wait.progressVisibilityOff()
                    try:
                        fid.calcTransform()
                    except Exception as err:
                        wait.close()
                        messageBox(self, 'Stereotactic frame detection error', '{}\n{}'.format(type(err), str(err)))
                        self._logger.error(traceback.format_exc())
                        return
                    wait.close()
                else:
                    wait.close()
                    messageBox(self,
                               'Stereotactic frame detection',
                               'No frame or frame detection failed.')
                    return
            from Sisyphe.gui.dialogFiducialBox import DialogFiducialBox
            self._dialog = DialogFiducialBox(fid)
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            try:
                self._logger.info('Dialog exec [gui.dialogFiducialBox.DialogFiducialBox] {}'.format(v.getBasename()))
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Stereotactic frame detection dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
                return
            n = self._thumbnail.getVolumeIndex(v)
            if n is not None:
                widget = self._thumbnail.getWidgetFromIndex(n)
                widget.updateTooltip()
                self.setStatusBarMessage('{} stereotactic frame detected'.format(v.getBasename()))
                self._logger.info('{} stereotactic frame detected'.format(v.getFilename()))

    def acpcSelection(self, filename: str = '') -> None:
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                # < Revision 16/04/2025
                # dialog = DialogFileSelection(parent=self)
                dialog = DialogFileSelection()
                # Revision 16/04/2025 >
                if platform == 'win32': __main__.updateWindowTitleBarColor(dialog)
                dialog.setWindowTitle('AC-PC selection')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            from Sisyphe.gui.dialogACPC import DialogACPC
            # < Revision 16/04/2025
            # self._dialog = DialogACPC(parent=self)
            self._dialog = DialogACPC()
            # Revision 16/04/2025 >
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            self._dialog.setVolume(v)
            try:
                self._logger.info('Dialog exec [gui.dialogACPC.DialogACPC] {}'.format(v.getBasename()))
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'AC-PC selection dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
                return
            n = self._thumbnail.getVolumeIndex(v)
            if n is not None:
                v.load()
                widget = self._thumbnail.getWidgetFromIndex(n)
                widget.updateTooltip()
                self.setStatusBarMessage('{} AC-PC selected'.format(v.getBasename()))
                self._logger.info('{} AC-PC selected'.format(v.getFilename()))

    def reorient(self, filename: str = '') -> None:
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                # < Revision 16/04/2025
                # dialog = DialogFileSelection(parent=self)
                dialog = DialogFileSelection()
                # Revision 16/04/2025 >
                if platform == 'win32': __main__.updateWindowTitleBarColor(dialog)
                dialog.setWindowTitle('Volume reorientation')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            from Sisyphe.gui.dialogReorient import DialogReorient
            # < Revision 16/04/2025
            # self._dialog = DialogReorient(parent=self)
            self._dialog = DialogReorient()
            # Revision 16/04/2025 >
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            self._dialog.setVolume(v)
            try:
                self._logger.info('Dialog exec [gui.dialogReorient.DialogReorient] {}'.format(v.getBasename()))
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Volume reorientation dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
                return
            self.setStatusBarMessage('{} reoriented'.format(v.getBasename()))
            self._logger.info('{} reoriented'.format(v.getFilename()))

    def manualRegistration(self) -> None:
        from Sisyphe.gui.dialogManualRegistration import DialogManualRegistration
        from Sisyphe.gui.dialogFileSelection import DialogMultiFileSelection
        # < Revision 16/04/2025
        # self._dialog = DialogMultiFileSelection(parent=self)
        self._dialog = DialogMultiFileSelection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.setWindowTitle('Manual registration volumes selection')
        self._dialog.createFileSelectionWidget('Fixed', toolbar=self._thumbnail, current=True)
        self._dialog.createFileSelectionWidget('Moving', toolbar=self._thumbnail, current=True)
        self._logger.info('Dialog exec [gui.dialogFileSelection.DialogMultiFileSelection]')
        if self._dialog.exec():
            wait = DialogWait(title='Open volumes for manual registration', progress=False)
            wait.open()
            fixed = SisypheVolume()
            moving = SisypheVolume()
            wait.setInformationText('Open fixed volume {}...'.format(basename(self._dialog.getFilename('Fixed'))))
            QApplication.processEvents()
            fixed.load(self._dialog.getFilename('Fixed'))
            wait.setInformationText('Open moving volume {}...'.format(basename(self._dialog.getFilename('Moving'))))
            QApplication.processEvents()
            moving.load(self._dialog.getFilename('Moving'))
            self._dialog = DialogManualRegistration(fixed, moving, parent=self)
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            self._dialog.setDialogToResample()
            wait.close()
            try:
                self._logger.info('Dialog exec [gui.dialogManualRegistration.DialogManualRegistration]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Manual registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def rigidRegistration(self,
                          fixed: str | None = None,
                          moving: str | None = None,
                          params: dict | None = None) -> None:
        from Sisyphe.gui.dialogRegistration import DialogRegistration
        self._dialog = DialogRegistration(transform='Rigid', parent=self)
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        if fixed is not None and moving is not None:
            self._dialog.setFixed(fixed, editable=False)
            self._dialog.setMoving(moving, editable=False)
            if params is not None: self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Rigid registration]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Rigid registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Rigid registration]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Rigid registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def affineRegistration(self,
                           fixed: str | None = None,
                           moving: str | None = None,
                           params: dict | None = None) -> None:
        from Sisyphe.gui.dialogRegistration import DialogRegistration
        self._dialog = DialogRegistration(transform='Affine')
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        if fixed is not None and moving is not None:
            self._dialog.setFixed(fixed, editable=False)
            self._dialog.setMoving(moving, editable=False)
            if params is not None: self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Affine registration]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Affine registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Affine registration]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Affine registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def displacementFieldRegistration(self,
                                      fixed: str | None = None,
                                      moving: str | None = None,
                                      params: dict | None = None) -> None:
        from Sisyphe.gui.dialogRegistration import DialogRegistration
        self._dialog = DialogRegistration(transform='DisplacementField', parent=self)
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        if fixed is not None and moving is not None:
            self._dialog.setFixed(fixed, editable=False)
            self._dialog.setMoving(moving, editable=False)
            if params is not None: self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Displacement field registration]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Displacement field registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogRegistration - Displacement field registration]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Displacement field registration dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def normalize(self,
                  fixed: str | None = None,
                  moving: str | None = None,
                  params: dict | None = None) -> None:
        from Sisyphe.gui.dialogRegistration import DialogICBMNormalization
        # < Revision 16/04/2025
        # self._dialog = DialogICBMNormalization(parent=self)
        self._dialog = DialogICBMNormalization()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        if fixed is not None and moving is not None:
            self._dialog.setFixed(fixed, editable=False)
            self._dialog.setMoving(moving, editable=False)
            if params is not None: self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogICBMNormalization]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Spatial normalization dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            try:
                self._logger.info('Dialog exec [gui.dialogRegistration.DialogICBMNormalization]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Spatial normalization dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def batchRegistration(self) -> None:
        from Sisyphe.gui.dialogRegistration import DialogBatchRegistration
        # < Revision 16/04/2025
        # self._dialog = DialogBatchRegistration(parent=self)
        self._dialog = DialogBatchRegistration()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getBatchSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogRegistration.DialogBatchRegistration]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Batch registration dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def realignment(self) -> None:
        from Sisyphe.gui.dialogSeriesRealignment import DialogSeriesRealignment
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesRealignment(parent=self)
        self._dialog = DialogSeriesRealignment()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogSeriesRealignment.DialogSeriesRealignment]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Time series realignment dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def eddycurrent(self) -> None:
        from Sisyphe.gui.dialogRegistration import DialogEddyCurrentCorrection
        # < Revision 16/04/2025
        # self._dialog = DialogEddyCurrentCorrection(parent=self)
        self._dialog = DialogEddyCurrentCorrection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getBatchSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogRegistration.DialogEddyCurrentCorrection]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Eddy current correction dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def resample(self) -> None:
        from Sisyphe.gui.dialogResample import DialogResample
        # < Revision 16/04/2025
        # self._dialog = DialogResample(parent=self)
        self._dialog = DialogResample()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogResample.DialogResample]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Resample dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def jacobian(self) -> None:
        from Sisyphe.gui.dialogJacobian import DialogJacobian
        # < Revision 16/04/2025
        # self._dialog = DialogJacobian(parent=self)
        self._dialog = DialogJacobian()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogJacobian.DialogJacobian]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Displacement field jacobian determinant dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def asymmetry(self) -> None:
        from Sisyphe.gui.dialogRegistration import DialogAsymmetry
        # < Revision 16/04/2025
        # self._dialog = DialogAsymmetry(parent=self)
        self._dialog = DialogAsymmetry()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getBatchSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogRegistration.DialogAsymmetry]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Asymmetry displacement field dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # to do
    def fieldinv(self):
        pass

    # Segmentation methods called from main menu

    def skullStriping(self,
                      filenames: str | list[str] | None = None,
                      params: dict | None = None) -> None:
        from Sisyphe.gui.dialogSkullStripping import DialogSkullStripping
        # < Revision 16/04/2025
        # self._dialog = DialogSkullStripping(parent=self)
        self._dialog = DialogSkullStripping()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogSkullStripping.DialogSkullStripping]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Skull stripping dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogSkullStripping.DialogSkullStripping]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Skull stripping dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def kMeansClustering(self) -> None:
        from Sisyphe.gui.dialogSegmentation import DialogKMeansClustering
        # < Revision 16/04/2025
        # self._dialog = DialogKMeansClustering(parent=self)
        self._dialog = DialogKMeansClustering()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogSegmentation.DialogKMeansClustering]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'KMeans clustering dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def kMeansSegmentation(self) -> None:
        from Sisyphe.gui.dialogSegmentation import DialogKMeansSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogKMeansSegmentation(parent=self)
        self._dialog = DialogKMeansSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogSegmentation.DialogKMeansSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'KMeans segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def priorBasedSegmentation(self,
                               filenames: str | list[str] | None = None,
                               params: dict | None = None) -> None:
        from Sisyphe.gui.dialogSegmentation import DialogPriorBasedSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogPriorBasedSegmentation(parent=self)
        self._dialog = DialogPriorBasedSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        if filenames is not None:
            if isinstance(filenames, str): filenames = [filenames]
            self._dialog.setFilenames(filenames)
            if params is not None:
                self._dialog.setParametersFromDict(params)
            try:
                self._logger.info('Dialog exec [gui.dialogSegmentation.DialogPriorBasedSegmentation]')
                self._dialog.execute()
            except Exception as err:
                messageBox(self, 'Prior based tissue segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())
        else:
            self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
            try:
                self._logger.info('Dialog exec [gui.dialogSegmentation.DialogPriorBasedSegmentation]')
                self._dialog.exec()
            except Exception as err:
                messageBox(self, 'Prior based tissue segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
                self._logger.error(traceback.format_exc())

    def thickness(self) -> None:
        from Sisyphe.gui.dialogSegmentation import DialogCorticalThickness
        # < Revision 16/04/2025
        # self._dialog = DialogCorticalThickness(parent=self)
        self._dialog = DialogCorticalThickness()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogSegmentation.DialogCorticalThickness]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Cortical thickness dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def registrationSegmentation(self) -> None:
        from Sisyphe.gui.dialogSegmentation import DialogRegistrationBasedSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogRegistrationBasedSegmentation(parent=self)
        self._dialog = DialogRegistrationBasedSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w1, w2 = self._dialog.getSelectionWidgets()
        w1.setToolbarThumbnail(self._thumbnail)
        w2.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogSegmentation.DialogRegistrationBasedSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Registration based segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def hippocampusSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepHippocampusSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepHippocampusSegmentation(parent=self)
        self._dialog = DialogDeepHippocampusSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w = self._dialog.getSelectionWidget()
        w.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepHippocampusSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning hippocampus segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def temporalSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepMedialTemporalSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepMedialTemporalSegmentation(parent=self)
        self._dialog = DialogDeepMedialTemporalSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w1, w2 = self._dialog.getSelectionWidgets()
        w1.setToolbarThumbnail(self._thumbnail)
        w2.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepMedialTemporalSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning medial temporal segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def tumorSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepTumorSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepTumorSegmentation(parent=self)
        self._dialog = DialogDeepTumorSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w1, w2, w3, w4 = self._dialog.getSelectionWidgets()
        w1.setToolbarThumbnail(self._thumbnail)
        w2.setToolbarThumbnail(self._thumbnail)
        w3.setToolbarThumbnail(self._thumbnail)
        w4.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepTumorSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning tumor segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def lesionSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepLesionSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepLesionSegmentation(parent=self)
        self._dialog = DialogDeepLesionSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w = self._dialog.getSelectionWidget()
        w.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepLesionSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning T1-hypointensity lesion segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def wmhSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepWhiteMatterHyperIntensitiesSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepWhiteMatterHyperIntensitiesSegmentation(parent=self)
        self._dialog = DialogDeepWhiteMatterHyperIntensitiesSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w1, w2, w3, w4 = self._dialog.getSelectionWidgets()
        w1.setToolbarThumbnail(self._thumbnail)
        w2.setToolbarThumbnail(self._thumbnail)
        w3.setToolbarThumbnail(self._thumbnail)
        w4.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepWhiteMatterHyperIntensitiesSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning white matter hyperintensities segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def vesselSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepTOFVesselSegmentation
        # < Revision 16/04/2025
        # self._dialog = DialogDeepTOFVesselSegmentation(parent=self)
        self._dialog = DialogDeepTOFVesselSegmentation()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w = self._dialog.getSelectionWidget()
        w.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepTOFVesselSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning TOF vessels segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def tissueSegmentation(self) -> None:
        from Sisyphe.gui.dialogDeepSegmentation import DialogDeepTissueSegmentation
        self._dialog = DialogDeepTissueSegmentation()
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        w = self._dialog.getSelectionWidget()
        w.setToolbarThumbnail(self._thumbnail)
        try:
            self._logger.info('Dialog exec [gui.dialogDeepSegmentation.DialogDeepTissueSegmentation]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Deep learning tissue segmentation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # Map processing methods called from main menu

    def model(self, model: int = 10) -> None:
        if model == 0:
            title = 'fMRI condition model'
            groups = None
            subjects = None
            conditions = 0
        elif model == 1:
            title = 'fMRI subjects/conditions model'
            groups = None
            subjects = 0
            conditions = 0
        elif model == 2:
            title = 'fMRI groups/subjects/conditions model'
            groups = 0
            subjects = 0
            conditions = 0
        elif model == 3:
            title = 'One sample t-test model'
            groups = 1
            subjects = None
            conditions = None
        elif model == 4:
            title = 'Two sample t-test model'
            groups = 2
            subjects = None
            conditions = None
        elif model == 5:
            title = 'Paired t-test model'
            groups = None
            subjects = 0
            conditions = 2
        elif model == 6:
            title = 'GLM subjects/conditions model'
            groups = None
            subjects = 0
            conditions = 0
        elif model == 7:
            title = 'GLM groups/subjects/conditions model'
            groups = 0
            subjects = 0
            conditions = 0
        elif model == 8:
            title = 'GLM groups model'
            groups = 0
            subjects = None
            conditions = None
        else:
            title = 'GLM groups/subjects model'
            groups = 0
            subjects = 0
            conditions = None
        if model < 3:
            from Sisyphe.gui.dialogStatModel import DialogfMRIObs
            self._dialog = DialogfMRIObs(title, conditions, subjects, groups)
            self._logger.info('Dialog exec [gui.dialogStatModel.DialogfMRIObs]')
        else:
            from Sisyphe.gui.dialogStatModel import DialogObs
            self._dialog = DialogObs(title, conditions, subjects, groups)
            self._logger.info('Dialog exec [gui.dialogStatModel.DialogObs]')
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            if self._dialog.exec():
                r = self._dialog.getTreeObsCount()
                self._dialog.close()
                from Sisyphe.gui.dialogStatModel import DialogModel
                self._dialog = DialogModel(title, r, model < 3)
                if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
                if self._dialog.exec():
                    design = self._dialog.getModel()
                    self._dialog.close()
                    if design.isEstimated():
                        r = messageBox(self,
                                       self.windowTitle(),
                                       'Do you want to define a contrast ?',
                                       icon=QMessageBox.Question,
                                       buttons=QMessageBox.Yes | QMessageBox.No,
                                       default=QMessageBox.No)
                        if r == QMessageBox.Yes:
                            from Sisyphe.gui.dialogStatContrast import DialogContrast
                            self._dialog = DialogContrast(design)
                            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
                            try:
                                self._logger.info('Dialog exec [gui.dialogStatContrast.DialogContrast]')
                                self._dialog.exec()
                            except Exception as err:
                                messageBox(self, 'Contrast dialog error', '{}\n{}'.format(type(err), str(err)))
                                self._logger.error(traceback.format_exc())
        except Exception as err:
            messageBox(self, 'Model dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def contrast(self, filename: str = '') -> None:
        if not isinstance(filename, str): filename = ''
        if filename == '' or not exists(filename):
            filename = QFileDialog.getOpenFileName(self, 'Open model...', getcwd(),
                                                   filter=SisypheDesign.getFilterExt())[0]
        if filename and exists(filename):
            chdir(dirname(filename))
            from Sisyphe.gui.dialogStatContrast import DialogContrast
            wait = DialogWait()
            wait.open()
            design = SisypheDesign()
            design.load(filename, wait)
            wait.close()
            if design.isEstimated():
                self._dialog = DialogContrast(design)
                if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
                try:
                    self._logger.info('Dialog exec [gui.dialogStatContrast.DialogContrast]')
                    self._dialog.exec()
                except Exception as err:
                    messageBox(self, 'Contrast dialog error', '{}\n{}'.format(type(err), str(err)))
                    self._logger.error(traceback.format_exc())
            else: messageBox(self,
                             'Contrast',
                             '{} model is not estimated.'.format(basename(filename)))

    def result(self, filename: str = '') -> None:
        if not isinstance(filename, str): filename = ''
        if filename == '' or not exists(filename):
            # < Revision 16/04/2025
            # self._dialog = DialogFileSelection(parent=self)
            self._dialog = DialogFileSelection()
            # Revision 16/04/2025 >
            if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
            self._dialog.setWindowTitle('Open statistical map')
            self._dialog.filterSisypheVolume()
            self._dialog.filterSameSequence([SisypheAcquisition.TMAP, SisypheAcquisition.ZMAP])
            if self._dialog.exec(): filename = self._dialog.getFilename()
        if filename != '' and exists(filename):
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Load {}'.format(basename(filename)))
            v = SisypheVolume()
            v.load(filename)
            if v.acquisition.isStatisticalMap():
                from Sisyphe.gui.dialogStatResult import DialogResult
                # < Revision 16/04/2025
                # self._dialog = DialogResult(parent=self)
                self._dialog = DialogResult()
                # Revision 16/04/2025 >
                if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
                self._dialog.setMap(v, wait)
                wait.close()
                if platform == 'darwin':
                    # < Revision 29/11/2024
                    # Qt bug of modal dialog on darwin
                    # modal simulation to fix it
                    self.setEnabled(False)
                    self._menubar.setEnabled(False)
                    self.repaint()
                    self._dialog.setEnabled(True)
                    # noinspection PyTypeChecker
                    self._dialog.setAttribute(Qt.WA_DeleteOnClose)
                    # noinspection PyTypeChecker
                    self._dialog.setWindowFlag(Qt.WindowStaysOnTopHint)
                    # noinspection PyUnresolvedReferences
                    self._dialog.finished.connect(lambda: self.setEnabled(True))
                    # noinspection PyUnresolvedReferences
                    self._dialog.finished.connect(lambda: self._menubar.setEnabled(True))
                    # noinspection PyUnresolvedReferences
                    self._dialog.finished.connect(lambda: self._dialog.close())
                    self._dialog.show()
                    # Revision 29/11/2024 >
                else:
                    try:
                        self._logger.info('Dialog exec [gui.dialogStatResult.DialogResult]')
                        self._dialog.exec()
                    except Exception as err:
                        messageBox(self, 'Result dialog error', '{}\n{}'.format(type(err), str(err)))
                        self._logger.error(traceback.format_exc())
            else: wait.close()

    def conjunction(self) -> None:
        from Sisyphe.gui.dialogStatContrast import DialogConjunction
        # < Revision 16/04/2025
        # self._dialog = DialogConjunction(parent=self)
        self._dialog = DialogConjunction()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogStatContrast.DialogConjunction]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Conjunction dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def tmapTozmap(self) -> None:
        from Sisyphe.gui.dialogStatContrast import DialogTMapToZMap
        # < Revision 16/04/2025
        # self._dialog = DialogTMapToZMap(parent=self)
        self._dialog = DialogTMapToZMap()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogStatContrast.DialogTMapToZMap]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'T to Z-map dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def confounders(self) -> None:
        from Sisyphe.gui.dialogTimeSeries import DialogSeriesPreprocessing
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesPreprocessing(parent=self)
        self._dialog = DialogSeriesPreprocessing()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogTimeSeries.DialogSeriesPreprocessing]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Time series preprocessing dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def seedCorrelation(self) -> None:
        from Sisyphe.gui.dialogTimeSeries import DialogSeriesSeedToVoxel
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesSeedToVoxel(parent=self)
        self._dialog = DialogSeriesSeedToVoxel()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogTimeSeries.DialogSeriesSeedToVoxel]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Seed-to-voxel time series correlation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def matrixCorrelation(self) -> None:
        from Sisyphe.gui.dialogTimeSeries import DialogSeriesConnectivityMatrix
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesConnectivityMatrix(parent=self)
        self._dialog = DialogSeriesConnectivityMatrix()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.setScreenshotsWidget(self._captures)
        try:
            self._logger.info('Dialog exec [gui.dialogTimeSeries.DialogSeriesConnectivityMatrix]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Time series correlation matrix dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def fastICA(self) -> None:
        from Sisyphe.gui.dialogTimeSeries import DialogSeriesFastICA
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesFastICA(parent=self)
        self._dialog = DialogSeriesFastICA()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogTimeSeries.DialogSeriesFastICA]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Single-subject time series ICA dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def groupICA(self) -> None:
        from Sisyphe.gui.dialogTimeSeries import DialogSeriesCanICA
        # < Revision 16/04/2025
        # self._dialog = DialogSeriesCanICA(parent=self)
        self._dialog = DialogSeriesCanICA()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogTimeSeries.DialogSeriesCanICA]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Multi-subject time series ICA dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def perfusion(self) -> None:
        from Sisyphe.gui.dialogPerfusion import DialogPerfusion
        # < Revision 16/04/2025
        # self._dialog = DialogPerfusion(parent=self)
        self._dialog = DialogPerfusion()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogPerfusion.DialogPerfusion]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Perfusion dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # Diffusion methods called from main menu

    def diffusionGradients(self) -> None:
        from Sisyphe.gui.dialogDiffusionGradients import DialogDiffusionGradients
        # < Revision 16/04/2025
        # self._dialog = DialogDiffusionGradients(parent=self)
        self._dialog = DialogDiffusionGradients()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionGradients.DialogDiffusionGradients]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Diffusion gradients dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionPreprocessing(self) -> None:
        from Sisyphe.gui.dialogDiffusionPreprocessing import DialogDiffusionPreprocessing
        # < Revision 16/04/2025
        # self._dialog = DialogDiffusionPreprocessing(parent=self)
        self._dialog = DialogDiffusionPreprocessing()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionPreprocessing.DialogDiffusionPreprocessing]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Diffusion preporcessing dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionModel(self) -> None:
        from Sisyphe.gui.dialogDiffusionModel import DialogDiffusionModel
        # < Revision 16/04/2025
        # self._dialog = DialogDiffusionModel(parent=self)
        self._dialog = DialogDiffusionModel()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        # try:
        self._logger.info('Dialog exec [gui.dialogDiffusionModel.DialogDiffusionModel]')
        self._dialog.exec()
        # except Exception as err:
        # messageBox(self, 'Diffusion model dialog error', '{}\n{}'.format(type(err), str(err)))
        # self._logger.error(traceback.format_exc())

    def diffusionBundleROISelection(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleROISelection
        # < Revision 16/04/2025
        # self._dialog = DialogBundleROISelection(parent=self)
        self._dialog = DialogBundleROISelection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleROISelection]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'ROI based selection dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionBundleFilterSelection(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleFilteringSelection
        # < Revision 16/04/2025
        # self._dialog = DialogBundleROISelection(parent=self)
        self._dialog = DialogBundleFilteringSelection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleFilteringSelection]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Filter based selection dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionBundleAtlasSelection(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleAtlasSelection
        # < Revision 16/04/2025
        # self._dialog = DialogBundleROISelection(parent=self)
        self._dialog = DialogBundleAtlasSelection()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleAtlasSelection]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Template based selection dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionTractogram(self) -> None:
        from Sisyphe.gui.dialogDiffusionTracking import DialogDiffusionTracking
        # < Revision 16/04/2025
        # self._dialog = DialogDiffusionTracking(parent=self)
        self._dialog = DialogDiffusionTracking()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionTracking.DialogDiffusionTracking]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Tractogram generation dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionDensityMap(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleToDensityMap
        # < Revision 16/04/2025
        # self._dialog = DialogBundleToDensityMap(parent=self)
        self._dialog = DialogBundleToDensityMap()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleToDensityMap]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Density map dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionPathLengthMap(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleToPathLengthMap
        # < Revision 16/04/2025
        # self._dialog = DialogBundleToPathLengthMap(parent=self)
        self._dialog = DialogBundleToPathLengthMap()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleToPathLengthMap]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Path length map dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    def diffusionConnectivityMatrix(self) -> None:
        from Sisyphe.gui.dialogDiffusionBundle import DialogBundleConnectivityMatrix
        # < Revision 16/04/2025
        # self._dialog = DialogBundleConnectivityMatrix(parent=self)
        self._dialog = DialogBundleConnectivityMatrix()
        # Revision 16/04/2025 >
        if platform == 'win32': __main__.updateWindowTitleBarColor(self._dialog)
        self._dialog.setScreenshotsWidget(self._captures)
        try:
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogBundleConnectivityMatrix]')
            self._dialog.exec()
        except Exception as err:
            messageBox(self, 'Connectivity matrix dialog error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

        # Public command methods (generate exceptions)

    # CLI method

    def addVolume(self, vol: SisypheVolume) -> None:
        try:
            self._logger.info('Add {}'.format(vol.getFilename))
            self._thumbnail.addVolume(vol)
        except Exception as err:
            messageBox(self, 'Add xvol error', '{}\n{}'.format(type(err), str(err)))
            self._logger.error(traceback.format_exc())

    # Qt events

    def closeEvent(self, a0: QCloseEvent | None) -> None:
        import Sisyphe.settings
        dirname(abspath(Sisyphe.settings.__file__))
        filename = join(dirname(abspath(Sisyphe.settings.__file__)), 'host.xml')
        if exists(filename): remove(filename)
        # < Revision 10/03/2025
        # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
        if platform == 'win32':
            self._sliceview.finalize()
            self._orthoview.finalize()
            self._synchroview.finalize()
            self._projview.finalize()
            self._compview.finalize()
            self._tabROITools.finalize()
        # Revision 10/03/2025 >
        super().closeEvent(a0)

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        # win32 bug fix, lost shortcuts in fullscreen mode
        if platform == 'win32':
            if self.windowState() == Qt.WindowFullScreen:
                if a0.key() == Qt.Key_Escape: self.toggleFullscreen()
                elif a0.key() == Qt.Key_F11: self.toggleFullscreen()
                elif a0.matches(Qt.Quit): self.exit()
        super().keyPressEvent(a0)
