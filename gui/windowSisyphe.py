"""
    External packages/modules

        Name            Link                                                        Usage

        darkdetect      https://github.com/albertosottile/darkdetect                OS Dark Mode detection
        Numpy           https://numpy.org/                                          Scientific computing
        psutil          https://github.com/giampaolo/psutil                         System utilities
        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from sys import platform

from os import mkdir
from os import chdir
from os import getcwd
from os.path import join
from os.path import dirname
from os.path import abspath
from os.path import exists
from os.path import basename
from os.path import expanduser

from psutil import virtual_memory

from glob import glob

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
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QMenuBar
from PyQt5.QtWidgets import QToolBar
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QSplitter
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

import darkdetect

from Sisyphe import version
from Sisyphe.core.sisypheVolume import SisypheVolume
from Sisyphe.core.sisypheVolume import multiComponentSisypheVolumeFromList
from Sisyphe.core.sisypheRecent import SisypheRecent
from Sisyphe.core.sisypheStatistics import SisypheDesign
from Sisyphe.core.sisypheROI import SisypheROIDraw
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.core.sisypheSettings import initPySisypheUserPath
from Sisyphe.core.sisypheSettings import SisypheSettings
from Sisyphe.gui.dialogLutEdit import DialogLutEdit
from Sisyphe.gui.dialogFileSelection import DialogFileSelection
from Sisyphe.gui.dialogFileSelection import DialogMultiFileSelection
from Sisyphe.gui.dialogFileSelection import DialogFilesSelection
from Sisyphe.gui.dialogFiducialBox import DialogFiducialBox
from Sisyphe.gui.dialogDicomDataset import DialogDicomDataset
from Sisyphe.gui.dialogImport import DialogImport
from Sisyphe.gui.dialogExport import DialogExport
from Sisyphe.gui.dialogOldSisypheImport import DialogOldSisypheImport
from Sisyphe.gui.dialogDicomImport import DialogDicomImport
from Sisyphe.gui.dialogDicomExport import DialogDicomExport
from Sisyphe.gui.dialogDatatype import DialogDatatype
from Sisyphe.gui.dialogAlgebra import DialogAlgebra
from Sisyphe.gui.dialogTexture import DialogTexture
from Sisyphe.gui.dialogFunction import DialogMeanFilter
from Sisyphe.gui.dialogFunction import DialogMedianFilter
from Sisyphe.gui.dialogFunction import DialogGaussianFilter
from Sisyphe.gui.dialogFunction import DialogGradientFilter
from Sisyphe.gui.dialogFunction import DialogLaplacianFilter
from Sisyphe.gui.dialogFunction import DialogAnisotropicDiffusionFilter
from Sisyphe.gui.dialogFunction import DialogBiasFieldCorrectionFilter
from Sisyphe.gui.dialogFunction import DialogHistogramMatching
from Sisyphe.gui.dialogReorient import DialogReorient
from Sisyphe.gui.dialogACPC import DialogACPC
from Sisyphe.gui.dialogManualRegistration import DialogManualRegistration
from Sisyphe.gui.dialogRegistration import DialogRegistration
from Sisyphe.gui.dialogRegistration import DialogICBMNormalization
from Sisyphe.gui.dialogRegistration import DialogBatchRegistration
from Sisyphe.gui.dialogResample import DialogResample
from Sisyphe.gui.dialogSeriesRealignment import DialogSeriesRealignment
from Sisyphe.gui.dialogEddyCurrentCorrection import DialogEddyCurrentCorrection
from Sisyphe.gui.dialogJacobian import DialogJacobian
from Sisyphe.gui.dialogModel import DialogObs
from Sisyphe.gui.dialogModel import DialogfMRIObs
from Sisyphe.gui.dialogModel import DialogModel
from Sisyphe.gui.dialogContrast import DialogContrast
from Sisyphe.gui.dialogSplash import DialogSplash
from Sisyphe.gui.dialogSettings import DialogSettings
from Sisyphe.gui.dialogWait import DialogWait
from Sisyphe.widgets.consoleWidget import ConsoleWidget
from Sisyphe.widgets.databaseWidget import DatabaseWidget
from Sisyphe.widgets.screenshotsGridWidget import ScreenshotsGridWidget
from Sisyphe.widgets.toolBarThumbnail import ToolBarThumbnail
from Sisyphe.widgets.tabToolsWidgets import TabROIListWidget
from Sisyphe.widgets.tabToolsWidgets import TabMeshListWidget
from Sisyphe.widgets.tabToolsWidgets import TabTargetListWidget
from Sisyphe.widgets.tabToolsWidgets import TabROIToolsWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.widgets.iconBarViewWidgets import IconBarOrthogonalSliceTrajectoryViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarMultiSliceGridViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarSynchronisedGridViewWidget

"""
    Class hierarchy
    
        QMainWindow -> WindowSisyphe
        
    Description
    
        PySisyphe main window.
"""


class WindowSisyphe(QMainWindow):
    """
        WindowSisyphe

        Description

            Main window of the PySisyphe application.

        Inheritance

            QMainWindow ->   WindowSisyphe

        Private attributes

            _rois           Sisyphe.sisypheROI.SisypheROICollection
            _draw           Sisyphe.sisypheROI.SisypheROIDraw
            _recent         Sisyphe.sisypheRecent.SisypheRecent
            _action         dict of PyQt5.QtWidgets.QAction
            _menu           dict of PyQt5.QtWidgets.QMenu
            _toolbar        PyQt5.QtWidgets.QToolBar
            _thumbnail      Sisyphe.widgets.toolBarThumbnail.ToolBarThumbnail
            _dock           PyQt5.QtWidgets.QTabWidget
            _sliceview      Sisyphe.widgets.iconBarViewWidgets.IconBarMultiSliceGridViewWidget
            _orthoview      Sisyphe.widgets.iconBarViewWidgets.IconBarOrthogonalSliceTrajectoryViewWidget
            _synchroview    Sisyphe.widgets.iconBarViewWidgets.IconBarSynchronisedGridViewWidget
            _views          Sisyphe.widgets.iconBarViewWidgets.IconBarViewWidgetCollection
            _tabview        PyQt5.QtWidgets.QTabWidget
            _status         PyQt5.QtWidgets.QStatusBar
            _statuslabel    PyQt5.QtWidgets.QLabel
            _settings       Sisyphe.sisypheSettings.SisypheSettings

        Public class method

            isDarkMode() -> bool
            isLightMode() -> bool
            getVersion() -> str
            getMemoryUsage() -> str
            getMainDirectory() -> str
            getUserDirectory() -> str
            getDefaultIconDirectory() -> str

        Public action methods (Toolbar/Menu action connected methods)

            File :
                open() -> None
                save() -> None
                saveAs() -> None
                remove() -> None
                removeAll() -> None
                loadNifti() -> None
                saveNifti() -> None
                loadMinc() -> None
                loadNrrd() -> None
                loadVtk() -> None
                loadSis() -> None
                saveMinc() -> None
                saveNrrd() -> None
                saveVtk() -> None
                saveNumpy() -> None
                importNifti() -> None
                importMinc() -> None
                importNrrd() -> None
                importVtk() -> None
                importSis() -> None
                importDicom() -> None
                exportNifti() -> None
                exportMinc() -> None
                exportNrrd() -> None
                exportVtk() -> None
                exportNumpy() -> None
                exportDicom() -> None
                datasetDicom() -> None
                editAttr() -> None
                editLabels() -> None
                lutEdit() -> None
            Functions :
                join() -> None
                split() -> None
                datatype() -> None
                flip() -> None
                swap() -> None
                algmean() -> None
                algmedian() -> None
                algmin() -> None
                algmax() -> None
                algstd() -> None
                algmath() -> None
                texture() -> None
                histmatch() -> None
                filterMean() -> None
                filterMedian() -> None
                filterGaussian() -> None
                filterGradient() -> None
                filterLaplacian() -> None
                filterAniso() -> None
                filterBias() -> None
            Registration :
                frameDetection(None | str | SisypheVolume) -> None
                acpcSelection(None | str | SisypheVolume) -> None
                reorient(None | str | SisypheVolume) -> None
                manualRegistration() -> None
                rigidRegistration() -> None
                affineRegistration() -> None
                DisplacementFieldRegistration() -> None
                normalize() -> None
                batchRegistration() -> None
                realignment() -> None
                eddycurrent() -> None
                resample() -> None
                jacobian() -> None
            Segmentation :
                unsupervisedKMeans() -> None
                supervisedKMeans() -> None
            Statistical map:
                model() -> None
                contrast() -> None
                result() -> None
                population() -> None
                subjectVsPopulation() -> None
            Application :
                exit() -> None

            addVolume(SisypheVolume) -> None

        Public settings methods

            setToolbarSize(int) -> None
            setThumbnailSize(int) -> None
            setDockIconSize(int) -> None
            setViewportsFontSize(int) -> None
            setViewportsFontFamily(str) -> None
            setViewportsLineWidth(float) -> None
            setViewportsLineColor((float, float, float) | [float, float, float]) -> None
            setViewportsLineOpacity(float) -> None
            setViewportsAttributesVisibility(bool) -> None
            setViewportsCursorVisibility(bool) -> None
            setViewportsOrientationMarkerShape(str) -> None
            setViewportsOrientationMarkerVisibility(bool) -> None

        Public methods

            getActions() -> list[QAction]
            getToolbar() -> QToolBar
            showToolbar() -> None
            hideToolbar() -> None
            setToolbarVisibility(bool) -> None
            getToolbarVisibility() -> bool
            getThumbnail() -> Sisyphe.widgets.toolBarThumbnail.ToolBarThumbnail
            showThumbnail() -> None
            hideThumbnail() -> None
            setThumbnailVisibility(bool) -> None
            getThumbnailVisibility() -> bool
            getDock() -> QTabWidget
            showDock() -> None
            hideDock() -> None
            setDockVisibility(bool) -> None
            getDockVisibility() -> bool
            getStatusBar() -> QStatusBar
            setStatusBarMessage(str)  -> None
            showStatusBar() -> None
            hideStatusBar() -> None
            setStatusBarVisibility(bool) -> None
            getStatusBarVisibility() -> bool
            getDatabase() -> Sisyphe.widgets.databaseWidget.DatabaseWidget
            getScreenshots() -> Sisyphe.widgets.screenshotsGridWidget.ScreenshotsGridWidget
            getROIListWidget() -> Sisyphe.widgets.tabToolsWidgets.TabROIListWidget
            getROIToolsWidget() -> Sisyphe.widgets.tabToolsWidgets.TabROIToolsWidget
            getMeshListWidget() -> Sisyphe.widgets.tabToolsWidgets.TabMeshListWidget
            getTargetListWidget() -> Sisyphe.widgets.tabToolsWidgets.TabTargetListWidget
            updateMemoryUsage() -> str
            showSlicesView() -> None
            hideSlicesView() -> None
            setSliceViewVisibility(bool) -> None
            getSliceViewVisibility() -> bool
            showOrthogonalView() -> None
            hideOrthogonalView() -> None
            setOrthogonalViewVisibility(bool) -> None
            getOrthogonalViewVisibility() -> bool
            showSynchronisedView() -> None
            hideSynchronisedView() -> None
            setSynchronisedViewVisibility(bool) -> None
            getSynchronisedViewVisibility() -> bool
            setTabViewVisibility(int, bool) -> None
            setDockEnabled(bool) -> None
            isDockEnabled() -> bool
            setROIToolsEnabled(bool) -> None
            isROIToolsEnabled() -> bool
            addRecent(str) -> None

            inherited QMainWindow
    """

    _ICONSIZE = 32
    _THUMBNAILSIZE = 96
    _TOOLBARICONSIZE = 16

    # Class methods

    @classmethod
    def getVersion(cls):
        return version.__version__

    @classmethod
    def isDarkMode(cls):
        return darkdetect.isDark()

    @classmethod
    def isLightMode(cls):
        return darkdetect.isLight()

    @classmethod
    def getMemoryUsage(cls):
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
    def getMainDirectory(cls):
        import Sisyphe
        return dirname(abspath(Sisyphe.__file__))

    @classmethod
    def getDefaultIconDirectory(cls):
        import Sisyphe.gui
        if cls.isDarkMode(): return join(dirname(abspath(Sisyphe.gui.__file__)), 'darkicons')
        else: return join(dirname(abspath(Sisyphe.gui.__file__)), 'lighticons')

    @classmethod
    def getUserDirectory(cls):
        userdir = join(expanduser('~'), '.PySisyphe')
        if not exists(userdir): initPySisypheUserPath()
        return userdir

    # Special method

    def __init__(self):
        super().__init__()

        self._splitter = QSplitter()
        self.setCentralWidget(self._splitter)

        # Central widget

        self._settings = SisypheSettings()
        self._views = IconBarViewWidgetCollection()
        self._draw = SisypheROIDraw()
        self._rois = SisypheROICollection()
        self._sliceview = IconBarMultiSliceGridViewWidget(rois=self._rois, draw=self._draw)
        self._orthoview = IconBarOrthogonalSliceTrajectoryViewWidget()
        self._synchroview = IconBarSynchronisedGridViewWidget(rois=self._rois, draw=self._draw)
        self._sliceview.setName('slices')
        self._sliceview.setFullscreenButtonAvailability(True)
        self._orthoview.setName('orthogonal')
        self._orthoview.setFullscreenButtonAvailability(True)
        self._synchroview.setName('synchronised')
        self._synchroview.setFullscreenButtonAvailability(True)
        self._database = DatabaseWidget()
        self._database.setMainWindow(self)
        self._console = ConsoleWidget()
        self._console.setMainWindow(self)
        self._captures = ScreenshotsGridWidget()
        self._views.append(self._sliceview)
        self._views.append(self._orthoview)
        self._views.append(self._synchroview)
        self._tabview = QTabWidget()
        self._tabview.addTab(self._sliceview, 'Slices view')
        self._tabview.addTab(self._orthoview, 'Orthogonal view')
        self._tabview.addTab(self._synchroview, 'Synchronised view')
        self._tabview.addTab(self._database, 'Database')
        self._tabview.addTab(self._captures, 'Screenshots')
        self._tabview.addTab(self._console, 'IPython')
        self._tabview.setTabPosition(QTabWidget.South)
        self._tabview.currentChanged.connect(self.updateTimers)
        self._splitter.addWidget(self._tabview)

        self._dialog = None
        self._recent = SisypheRecent()
        self._recent.load()

        # Menu bar

        self._action = dict()
        self._menu = dict()
        self._menuView = list()
        self._menubar = QMenuBar()
        if platform[:3] == 'win':
            self.setMenuBar(self._menubar)
        self._menubar.setNativeMenuBar(True)
        self._initMenuBar()

        # Tool bar

        self._toolbar = QToolBar()
        self._initToolBar()

        self._action['toolbar'].toggled.connect(self._toolbar.setVisible)

        # Thumbnail dock widget

        v = self._settings.getFieldValue('GUI', 'ThumbnailSize')
        if v is None: v = self._THUMBNAILSIZE
        self._thumbnail = ToolBarThumbnail(size=v, mainwindow=self, views=self._views)
        self.addToolBar(Qt.TopToolBarArea, self._thumbnail)
        self._sliceview.setThumbnail(self._thumbnail)
        self._orthoview.setThumbnail(self._thumbnail)
        self._synchroview.setThumbnail(self._thumbnail)

        self._action['thumb'].toggled.connect(self._thumbnail.setVisible)

        # Tools dock widget

        v = self._settings.getFieldValue('GUI', 'IconSize')
        if v is None: v = self._ICONSIZE
        self._dock = QTabWidget()
        self._dock.setTabPosition(QTabWidget.West)
        self._splitter.addWidget(self._dock)

        self._tabROIList = TabROIListWidget(parent=self)
        self._tabROIList.setViewCollection(self._views)
        self._tabROIList.setEnabled(False)
        self._tabROIList.setIconSize(v)
        self._dock.addTab(self._tabROIList, 'ROI')

        self._tabROITools = TabROIToolsWidget(parent=self)
        self._tabROITools.setViewCollection(self._views)
        self._tabROITools.setEnabled(False)
        self._tabROITools.setIconSize(v)
        self._dock.addTab(self._tabROITools, 'Brush')
        self._tabROITools.setVisible(False)

        self._tabMeshList = TabMeshListWidget(parent=self)
        self._tabMeshList.setViewCollection(self._views)
        self._tabMeshList.setEnabled(False)
        self._dock.addTab(self._tabMeshList, 'Mesh')

        self._tabTargetList = TabTargetListWidget(parent=self)
        self._tabTargetList.setViewCollection(self._views)
        self._tabTargetList.getToolListWidget().setScreenshotsWidget(self._captures)
        self._tabTargetList.setEnabled(False)
        self._dock.addTab(self._tabTargetList, 'Target')

        roiListWidget = self._tabROIList.getROIListWidget()
        meshListWidget = self._tabMeshList.getMeshListWidget()
        roiListWidget.setListMeshAttributeWidget(meshListWidget)
        meshListWidget.setListROIAttributeWidget(roiListWidget)
        self._action['dock'].toggled.connect(self._dock.setVisible)
        self._dock.setTabVisible(1, False)

        # Status bar

        font = QFont('Arial', 10)
        self._status = self.statusBar()
        self._status.setFont(font)
        self._statuslabel = QLabel(self.getMemoryUsage())
        self._statuslabel.setFont(font)
        self._status.addPermanentWidget(self._statuslabel)
        self._action['status'].toggled.connect(self._status.setVisible)

        # Main window

        self.setWindowTitle('PySisyphe')
        self.setUnifiedTitleAndToolBarOnMac(True)
        self.setWindowState(Qt.WindowMaximized)
        self.show()
        s = self._splitter.sizes()
        self._splitter.setSizes([s[0] + s[1] - roiListWidget.minimumWidth(), roiListWidget.minimumWidth()])

    # Private methods

    def _initMenuBar(self):

        # Icons

        icpath = self.getDefaultIconDirectory()
        icquit = QIcon(join(icpath, 'exit.png'))
        icpref = QIcon(join(icpath, 'settings.png'))
        icabout = QIcon(join(icpath, 'about.png'))

        # Actions

        self._action['about'] = QAction(icabout, 'About')
        self._action['pref'] = QAction(icpref, 'Preferences...')
        self._action['exit'] = QAction(icquit, 'Quit')
        # Mac os
        if platform == 'darwin':
            self._action['about'].setMenuRole(QAction.AboutRole)
            self._action['pref'].setMenuRole(QAction.PreferencesRole)
            self._action['exit'].setMenuRole(QAction.QuitRole)

        # Init Menus

        self._initFileMenu()
        self._initFunctionsMenu()
        self._initROIMenu()
        self._initRegistrationMenu()
        self._initSegmentationMenu()
        self._initStatisticalMapMenu()
        self._initDiffusionMenu()
        self._initViewsMenu()
        self._initWindowMenu()

    def _initFileMenu(self):
        self._menu['file'] = self._menubar.addMenu('File')

        # Icons

        icpath = self.getDefaultIconDirectory()
        icload = QIcon(join(icpath, 'open.png'))
        icsave = QIcon(join(icpath, 'save.png'))
        icsaveall = QIcon(join(icpath, 'saveall.png'))
        icclose = QIcon(join(icpath, 'close.png'))
        iccloseall = QIcon(join(icpath, 'closeall.png'))
        icexport = QIcon(join(icpath, 'export.png'))
        icimport = QIcon(join(icpath, 'import.png'))
        icattr = QIcon(join(icpath, 'list.png'))
        iclabel = QIcon(join(icpath, 'labels.png'))
        iclut = QIcon(join(icpath, 'rgb.png'))
        icdown = QIcon(join(icpath, 'download.png'))
        icupdate = QIcon(join(icpath, 'update.png'))

        # Actions
        self._menu['file'].addAction(self._action['about'])
        self._menu['file'].addAction(self._action['pref'])

        self._menu['file'].addSeparator()
        self._action['open'] = self._menu['file'].addAction(icload, 'Open...')
        submenu = self._menu['file'].addMenu('Open from Format')
        self._action['loadnifti'] = submenu.addAction('Open Nifti...')
        self._action['loadminc'] = submenu.addAction('Open Minc...')
        self._action['loadnrrd'] = submenu.addAction('Open Nrrd...')
        self._action['loadvtk'] = submenu.addAction('Open VTK...')
        self._action['loadsis'] = submenu.addAction('Open Sisyphe...')
        self._action['loadvmr'] = submenu.addAction('Open BrainVoyager VMR...')
        self._menu['recent'] = self._menu['file'].addMenu('Recent files...')
        self._menu['recent'].aboutToShow.connect(self._updateRecentMenu)
        self._menu['recent'].triggered.connect(self._openRecent)

        self._menu['file'].addSeparator()
        self._action['save'] = self._menu['file'].addAction(icsave, 'Save')
        self._action['saveall'] = self._menu['file'].addAction(icsaveall, 'Save all')
        self._action['saveas'] = self._menu['file'].addAction(icsave, 'Save As...')
        submenu = self._menu['file'].addMenu('Save to Format')
        self._action['savenifti'] = submenu.addAction('Save Nifti...')
        self._action['saveminc'] = submenu.addAction('Save Minc...')
        self._action['savenrrd'] = submenu.addAction('Save Nrrd...')
        self._action['savevtk'] = submenu.addAction('Save VTK...')
        self._action['savenpy'] = submenu.addAction('Save Numpy...')
        self._action['close'] = self._menu['file'].addAction(icclose, 'Close')
        self._action['closeall'] = self._menu['file'].addAction(iccloseall, 'Close All')

        self._menu['file'].addSeparator()
        self._action['download'] = self._menu['file'].addAction(icdown, 'Download manager...')
        self._action['update'] = self._menu['file'].addAction(icupdate, 'Check for updates...')

        self._menu['file'].addSeparator()
        self._action['editattr'] = self._menu['file'].addAction(icattr, 'Edit Attributes...')
        self._action['editlabels'] = self._menu['file'].addAction(iclabel, 'Edit volume labels...')
        self._action['roi2label'] = self._menu['file'].addAction(iclabel, 'ROIs to label volume...')
        self._action['vol2label'] = self._menu['file'].addAction(iclabel, 'Volumes to label volume...')
        self._action['label2roi'] = self._menu['file'].addAction(iclabel, 'Label volume to ROIs...')

        self._menu['file'].addSeparator()
        submenu = self._menu['file'].addMenu('Import')
        self._action['importnifti'] = submenu.addAction(icimport, 'Import Nifti...')
        self._action['importminc'] = submenu.addAction(icimport, 'Import Minc...')
        self._action['importnrrd'] = submenu.addAction(icimport, 'Import Nrrd...')
        self._action['importvtk'] = submenu.addAction(icimport, 'Import Vtk...')
        self._action['importsis'] = submenu.addAction(icimport, 'Import Sisyphe (*.vol)...')
        submenu = self._menu['file'].addMenu('Export')
        self._action['exportnifti'] = submenu.addAction(icexport, 'Export Nifti...')
        self._action['exportminc'] = submenu.addAction(icexport, 'Export Minc...')
        self._action['exportnrrd'] = submenu.addAction(icexport, 'Export Nrrd...')
        self._action['exportvtk'] = submenu.addAction(icexport, 'Export Vtk...')
        self._action['exportnpy'] = submenu.addAction(icexport, 'Export Numpy...')
        submenu = self._menu['file'].addMenu('DICOM')
        self._action['dcmimport'] = submenu.addAction(icimport, 'DICOM Import...')
        self._action['dcmexport'] = submenu.addAction(icexport, 'DICOM Export...')
        submenu.addSeparator()
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
        self._action['close'].setShortcut(QKeySequence.Close)
        self._action['exit'].setShortcut(QKeySequence.Quit)
        self._action['pref'].setShortcut(QKeySequence.Preferences)

        # Connect

        self._action['open'].triggered.connect(lambda dummy: self.open())
        self._action['save'].triggered.connect(self.save)
        self._action['saveall'].triggered.connect(self.saveall)
        self._action['saveas'].triggered.connect(self.saveAs)
        self._action['close'].triggered.connect(self.remove)
        self._action['closeall'].triggered.connect(self.removeAll)
        self._action['download'].triggered.connect(self.download)
        self._action['update'].triggered.connect(self.checkUpdate)
        self._action['editattr'].triggered.connect(self.editAttr)
        self._action['editlabels'].triggered.connect(lambda dummy: self.editLabels())
        self._action['lutedit'].triggered.connect(self.lutEdit)
        self._action['loadnifti'].triggered.connect(self.loadNifti)
        self._action['savenifti'].triggered.connect(self.saveNifti)
        self._action['loadminc'].triggered.connect(self.loadMinc)
        self._action['loadnrrd'].triggered.connect(self.loadNrrd)
        self._action['loadvtk'].triggered.connect(self.loadVtk)
        self._action['loadsis'].triggered.connect(self.loadSis)
        self._action['loadvmr'].triggered.connect(self.loadVmr)
        self._action['saveminc'].triggered.connect(self.saveMinc)
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

    def _initFunctionsMenu(self):
        """
            Functions menu
                Join single component volume(s)
                Split multi component volume(s)
                --
                Flip axis
                Axis order
                Datatype conversion
                --
                Label volume
                    ROI(s) to label volume
                    Label volume to ROI(s)
                    Edit labels
                    Texture features of labels
                --
                Filters
                    Median
                    Mean
                    Gaussian
                    Anisotropic diffusion
                    Non-local means
                Texture features
                --
                Bias field correction
                --
                Histogram matching
                --
                Voxel-by-voxel processing
                    Mean volume
                    Median volume
                    Standard Deviation volume
                    Minimum volume
                    Maximum volume
                    Algebra
                --
                Automate processing
                Plugins
                    files in Sisyphe/plugins
        """
        self._menu['func'] = self._menubar.addMenu('Functions')

        # Icons

        icpath = self.getDefaultIconDirectory()
        icjoin = QIcon(join(icpath, 'join.png'))
        icsplit = QIcon(join(icpath, 'split.png'))
        icflip = QIcon(join(icpath, 'flip.png'))
        icaxis = QIcon(join(icpath, 'axis.png'))

        # Actions

        self._action['join'] = self._menu['func'].addAction(icjoin, 'Join single component volume(s)...')
        self._action['split'] = self._menu['func'].addAction(icsplit, 'Split multi component volume(s)...')

        self._menu['func'].addSeparator()
        self._action['flip'] = self._menu['func'].addAction(icflip, 'Flip axis...')
        self._action['axis'] = self._menu['func'].addAction(icaxis, 'Permute axis...')
        self._action['datatype'] = self._menu['func'].addAction('Datatype conversion...')

        self._menu['func'].addSeparator()
        submenu = self._menu['func'].addMenu('Filters')
        self._action['mean'] = submenu.addAction('Mean...')
        self._action['median'] = submenu.addAction('Median...')
        self._action['gaussian'] = submenu.addAction('Gaussian...')
        self._action['gradient'] = submenu.addAction('Gradient Magnitude...')
        self._action['laplacian'] = submenu.addAction('Laplacian...')
        self._action['aniso'] = submenu.addAction('Anisotropic diffusion...')
        self._action['nlm'] = submenu.addAction('Non local means...')
        self._action['texture'] = self._menu['func'].addAction('Texture feature maps...')

        self._menu['func'].addSeparator()
        self._action['bias'] = self._menu['func'].addAction('Bias field correction...')

        self._menu['func'].addSeparator()
        self._action['histmatch'] = self._menu['func'].addAction('Histogram matching...')

        self._menu['func'].addSeparator()
        submenu = self._menu['func'].addMenu('Voxel-by-voxel processing')
        self._action['algmean'] = submenu.addAction('Mean volume...')
        self._action['algmedian'] = submenu.addAction('Median volume...')
        self._action['algstd'] = submenu.addAction('Standard deviation volume...')
        self._action['algmin'] = submenu.addAction('Minimum volume...')
        self._action['algmax'] = submenu.addAction('Maximum volume...')
        self._action['algmath'] = submenu.addAction('Algebra...')

        self._menu['func'].addSeparator()
        self._action['auto'] = self._menu['func'].addAction('Automate processing...')

        # Connect

        self._action['join'].triggered.connect(self.join)
        self._action['split'].triggered.connect(self.split)
        self._action['flip'].triggered.connect(self.flip)
        self._action['axis'].triggered.connect(self.swap)
        self._action['datatype'].triggered.connect(self.datatype)
        self._action['algmean'].triggered.connect(self.algmean)
        self._action['algmedian'].triggered.connect(self.algmedian)
        self._action['algstd'].triggered.connect(self.algstd)
        self._action['algmin'].triggered.connect(self.algmin)
        self._action['algmax'].triggered.connect(self.algmax)
        self._action['algmath'].triggered.connect(self.algmath)
        self._action['texture'].triggered.connect(self.texture)
        self._action['mean'].triggered.connect(self.filterMean)
        self._action['median'].triggered.connect(self.filterMedian)
        self._action['gaussian'].triggered.connect(self.filterGaussian)
        self._action['gradient'].triggered.connect(self.filterGradient)
        self._action['laplacian'].triggered.connect(self.filterLaplacian)
        self._action['aniso'].triggered.connect(self.filterAniso)
        self._action['nlm'].triggered.connect(self.filterNonLocalMeans)
        self._action['bias'].triggered.connect(self.filterBias)
        self._action['histmatch'].triggered.connect(self.histmatch)

    def _initROIMenu(self):
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

    def _initRegistrationMenu(self):
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
                Asymmetry analysis
        """
        self._menu['reg'] = self._menubar.addMenu('Registration')
        self._action['frame'] = self._menu['reg'].addAction('Stereotactic frame detection...')
        self._action['acpc'] = self._menu['reg'].addAction('AC-PC selection...')
        self._action['orient'] = self._menu['reg'].addAction('Volume reorientation...')

        self._menu['reg'].addSeparator()
        self._action['hand'] = self._menu['reg'].addAction('Manual registration...')
        self._action['rigid'] = self._menu['reg'].addAction('Rigid registration...')
        self._action['affine'] = self._menu['reg'].addAction('Affine registration...')
        self._action['field'] = self._menu['reg'].addAction('Displacement field registration...')
        self._action['normalize'] = self._menu['reg'].addAction('ICBM normalization...')
        self._action['batchreg'] = self._menu['reg'].addAction('Batch registration...')

        self._menu['reg'].addSeparator()
        self._action['series'] = self._menu['reg'].addAction('Time series realignment...')
        self._action['eddy'] = self._menu['reg'].addAction('Eddy current correction...')

        self._menu['reg'].addSeparator()
        self._action['resample'] = self._menu['reg'].addAction('Resample...')

        self._menu['reg'].addSeparator()
        self._action['jac'] = self._menu['reg'].addAction('Displacement field jacobian determinant...')
        self._action['asym'] = self._menu['reg'].addAction('Asymmetry analysis...')

        # Connect

        self._action['frame'].triggered.connect(lambda dummy: self.frameDetection())
        self._action['acpc'].triggered.connect(lambda dummy: self.acpcSelection())
        self._action['orient'].triggered.connect(lambda dummy: self.reorient())
        self._action['hand'].triggered.connect(self.manualRegistration)
        self._action['rigid'].triggered.connect(self.rigidRegistration)
        self._action['affine'].triggered.connect(self.affineRegistration)
        self._action['field'].triggered.connect(self.displacementFieldRegistration)
        self._action['normalize'].triggered.connect(self.normalize)
        self._action['series'].triggered.connect(self.realignment)
        self._action['eddy'].triggered.connect(self.eddycurrent)
        self._action['batchreg'].triggered.connect(self.batchRegistration)
        self._action['resample'].triggered.connect(self.resample)
        self._action['jac'].triggered.connect(self.jacobian)

    def _initSegmentationMenu(self):
        """
            Segmentation menu
                Unsupervised KMeans
                Supervised KMeans
                Finite mixture model
                Cortical thickness
                ---
                Deep learning based segmentation
                    Skull striping
                    White matter hyper-intensities
                    Hippocampus
                ---
                Registration based segmentation
        """
        self._menu['seg'] = self._menubar.addMenu('Segmentation')

        self._action['kmeans1'] = self._menu['seg'].addAction('Unsupervised KMeans...')
        self._action['kmeans2'] = self._menu['seg'].addAction('Supervised KMeans...')
        self._action['atropos'] = self._menu['seg'].addAction('Finite mixture model...')
        self._action['thickness'] = self._menu['seg'].addAction('Cortical thickness...')

        self._menu['seg'].addSeparator()
        self._action['skull'] = self._menu['seg'].addAction('Skull stripping...')
        self._action['wmh'] = self._menu['seg'].addAction('White matter hyper-intensities...')
        self._action['hipp'] = self._menu['seg'].addAction('Hippocampus...')

        self._menu['seg'].addSeparator()
        self._action['rseg'] = self._menu['seg'].addAction('Registration based segmentation...')
        self._menu['rseg'] = self._menu['seg'].addMenu('Structs')
        self._menu['rseg'].aboutToShow.connect(self._updateStructsMenu)
        self._menu['rseg'].triggered.connect(self._openStruct)

        # Connect

        self._action['skull'].triggered.connect(self.skullStriping)
        self._action['kmeans1'].triggered.connect(self.unsupervisedKMeans)
        self._action['kmeans2'].triggered.connect(self.supervisedKMeans)

    def _initStatisticalMapMenu(self):
        """
            Statistical map
                Model
                    fMRI conditions
                    fMRI subjects/conditions
                    fMRI groups/subjects/conditions
                    ---
                    Images conditions
                    Images subjects/conditions
                    Images groups/subjects/conditions
                    Images groups
                    ---
                    Open model
                        files in user/.Sisyphe/models
                        ---
                        Load model
                ---
                New contrast
                Open contrast
                Result
                Conjunctions
                ---
                Population mean/std
                Subject Z-score versus population
        """
        # Actions

        self._menu['statmap'] = self._menubar.addMenu('Statistical Map')

        submenu = self._menu['statmap'].addMenu('Model')
        self._action['fmricnd'] = submenu.addAction('fMRI conditions...')
        self._action['fmrisbj'] = submenu.addAction('fMRI subjects/conditions...')
        self._action['fmrigrp'] = submenu.addAction('fMRI groups/subjects/conditions...')
        submenu.addSeparator()
        self._action['cnd'] = submenu.addAction('Images conditions...')
        self._action['sbj'] = submenu.addAction('Images subjects/conditions...')
        self._action['grp'] = submenu.addAction('Images groups/subjects/conditions...')
        self._action['grp2'] = submenu.addAction('Images groups...')
        submenu.addSeparator()
        self._menu['model'] = submenu.addMenu('Open model')
        self._menu['model'].aboutToShow.connect(self._updateModelsMenu)
        self._menu['model'].triggered.connect(self._openModel)

        self._action['contrast'] = self._menu['statmap'].addAction('Contrast...')
        self._action['result'] = self._menu['statmap'].addAction('Statistical map result...')

        self._menu['statmap'].addSeparator()
        self._action['population'] = self._menu['statmap'].addAction('Population Z-score map...')
        self._action['subject'] = self._menu['statmap'].addAction('Subject versus population Z map...')

        # Connect

        self._action['fmricnd'].triggered.connect(lambda dummy: self.model(groups=False, subjects=False,
                                                                           conditions=True, fmri=True))
        self._action['fmrisbj'].triggered.connect(lambda dummy: self.model(groups=False, subjects=True,
                                                                           conditions=True, fmri=True))
        self._action['fmrigrp'].triggered.connect(lambda dummy: self.model(groups=True, subjects=True,
                                                                           conditions=True, fmri=True))
        self._action['cnd'].triggered.connect(lambda dummy: self.model(groups=False, subjects=False,
                                                                       conditions=True, fmri=False))
        self._action['sbj'].triggered.connect(lambda dummy: self.model(groups=False, subjects=True,
                                                                       conditions=True, fmri=False))
        self._action['grp'].triggered.connect(lambda dummy: self.model(groups=True, subjects=True,
                                                                       conditions=True, fmri=False))
        self._action['grp2'].triggered.connect(lambda dummy: self.model(groups=True, subjects=False,
                                                                        conditions=False, fmri=False))
        self._action['contrast'].triggered.connect(self.contrast)
        self._action['result'].triggered.connect(self.result)
        self._action['population'].triggered.connect(self.population)
        self._action['subject'].triggered.connect(self.subjectVsPopulation)

    def _initDiffusionMenu(self):
        """
            Diffusion
                Gradients...
                Preprocessing...
                Diffusion model...
                Tractogram generation...
                Bundle
                    Load...
                    Save...
                    ---
                    ROI based tracks selection...
                    Filter based tracks selection...
                    Template based tracks selection...
                    Density map...
                    Path length map...
                    Connectivity matrix...
        """

        # Actions

        self._menu['diffusion'] = self._menubar.addMenu('Diffusion')
        self._action['grad'] = self._menu['diffusion'].addAction('Gradients...')
        self._action['prepoc'] = self._menu['diffusion'].addAction('Preprocessing...')
        self._action['fit'] = self._menu['diffusion'].addAction('Diffusion model...')
        self._action['tracto'] = self._menu['diffusion'].addAction('Tractogram generation...')
        submenu = self._menu['diffusion'].addMenu('Bundle')
        self._action['trkload'] = submenu.addAction('Load...')
        self._action['trksave'] = submenu.addAction('Save...')
        submenu.addSeparator()
        self._action['roisel'] = submenu.addAction('ROI based tracks selection...')
        self._action['filtsel'] = submenu.addAction('Filter based tracks selection...')
        self._action['tplsel'] = submenu.addAction('Template based tracks selection...')
        submenu.addSeparator()
        self._action['density'] = submenu.addAction('Density map...')
        self._action['length'] = submenu.addAction('Path length map...')
        self._action['conn'] = submenu.addAction('Connectivity matrix...')

        # Connect

        self._action['grad'].triggered.connect(lambda _: self.diffusionGradients())
        self._action['prepoc'].triggered.connect(lambda _: self.diffusionPreprocessing())
        self._action['fit'].triggered.connect(lambda _: self.diffusionModel())
        self._action['tracto'].triggered.connect(lambda _: self.diffusionTractogram())

    def _initViewsMenu(self):
        self._menu['views'] = self._menubar.addMenu('Views')
        sliceview = self._sliceview()[0, 0].getPopup()
        orthoview = self._orthoview()[0, 0].getPopup()
        synchroview = self._synchroview()[0, 0].getPopup()
        sliceview.setTitle(self._tabview.tabText(0))
        orthoview.setTitle(self._tabview.tabText(1))
        synchroview.setTitle(self._tabview.tabText(2))
        self._menuView.append(self._menu['views'].addMenu(sliceview))
        self._menuView.append(self._menu['views'].addMenu(orthoview))
        self._menuView.append(self._menu['views'].addMenu(synchroview))
        self._menuView[0].setVisible(False)
        self._menuView[1].setVisible(False)
        self._menuView[2].setVisible(False)
        database = self._database.getPopup()
        database.setTitle(self._tabview.tabText(3))
        self._menu['views'].addMenu(database)
        capview = self._captures.getPopup()
        capview.setTitle(self._tabview.tabText(4))
        self._menu['views'].addMenu(capview)
        console = self._console.getPopup()
        console.setTitle(self._tabview.tabText(5))
        self._menu['views'].addMenu(console)

    def _initWindowMenu(self):
        """
            Window menu
                Minimize/Maximize
                Tool bar Hide/Show
                Thumbnail Hide/Show
                Toolbox Hide/Show
                ---
                Slices view
                Orthogonal view
                Synchronised view
                Database view
                Screenshots view
                IPython view
        """
        self._menu['window'] = self._menubar.addMenu('Window')

        # Actions

        self._action['wmin'] = self._menu['window'].addAction('Minimize')
        self._action['wmax'] = self._menu['window'].addAction('Maximize')
        self._action['wfull'] = self._menu['window'].addAction('Full screen')
        self._action['wfull'].setCheckable(True)

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
        self._action['slice'] = self._menu['window'].addAction('Slice View')
        self._action['ortho'] = self._menu['window'].addAction('Orthogonal View')
        self._action['synchro'] = self._menu['window'].addAction('Synchronised View')
        self._action['database'] = self._menu['window'].addAction('Database')
        self._action['scrshots'] = self._menu['window'].addAction('Screenshots')
        self._action['ipython'] = self._menu['window'].addAction('IPython')

        # Shortcuts

        self._action['wmin'].setShortcut(QKeySequence(Qt.CTRL | Qt.SHIFT | Qt.Key_M))
        self._action['wmax'].setShortcut(QKeySequence(Qt.CTRL | Qt.Key_M))
        self._action['wfull'].setShortcut(QKeySequence.FullScreen)
        self._action['slice'].setShortcut(QKeySequence('Ctrl+à'))
        self._action['ortho'].setShortcut(QKeySequence('Ctrl+&'))
        self._action['synchro'].setShortcut(QKeySequence('Ctrl+é'))
        self._action['database'].setShortcut(QKeySequence('Ctrl+\"'))
        self._action['scrshots'].setShortcut(QKeySequence('Ctrl+\''))
        self._action['ipython'].setShortcut(QKeySequence('Ctrl+('))

        # Connect

        self._action['wmin'].triggered.connect(lambda dummy: self.setWindowState(Qt.WindowMinimized))
        self._action['wmax'].triggered.connect(lambda dummy: self.setWindowState(Qt.WindowMaximized))
        self._action['wfull'].triggered.connect(lambda dummy: self.toggleFullscreen())
        self._action['slice'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(0))
        self._action['ortho'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(1))
        self._action['synchro'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(2))
        self._action['database'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(3))
        self._action['scrshots'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(4))
        self._action['ipython'].triggered.connect(lambda dummy: self._tabview.setCurrentIndex(5))

    def _initToolBar(self):
        policy = QSizePolicy()
        policy.setVerticalPolicy(QSizePolicy.Fixed)
        policy.setHorizontalPolicy(QSizePolicy.Expanding)
        self._toolbar.clear()
        self._toolbar.setMovable(False)
        self._toolbar.setSizePolicy(policy)
        size = self._settings.getFieldValue('GUI', 'ToolbarSize')
        if size is None: size = self._TOOLBARICONSIZE
        self._toolbar.setFixedHeight(size + 8)
        self._toolbar.setIconSize(QSize(size, size))
        if self._settings.getFieldValue('ToolbarIcons', 'open'): self._toolbar.addAction(self._action['open'])
        if self._settings.getFieldValue('ToolbarIcons', 'save'): self._toolbar.addAction(self._action['save'])
        if self._settings.getFieldValue('ToolbarIcons', 'saveall'): self._toolbar.addAction(self._action['saveall'])
        if self._settings.getFieldValue('ToolbarIcons', 'close'): self._toolbar.addAction(self._action['close'])
        if self._settings.getFieldValue('ToolbarIcons', 'closeall'): self._toolbar.addAction(self._action['closeall'])
        if self._settings.getFieldValue('ToolbarIcons', 'editattr'): self._toolbar.addAction(self._action['editattr'])
        if self._settings.getFieldValue('ToolbarIcons', 'dcmimport'): self._toolbar.addAction(self._action['dcmimport'])
        if len(self._toolbar.actions()) > 0: self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'join'): self._toolbar.addAction(self._action['join'])
        if self._settings.getFieldValue('ToolbarIcons', 'split'): self._toolbar.addAction(self._action['split'])
        if self._settings.getFieldValue('ToolbarIcons', 'flip'): self._toolbar.addAction(self._action['flip'])
        if self._settings.getFieldValue('ToolbarIcons', 'axis'): self._toolbar.addAction(self._action['axis'])
        if self._settings.getFieldValue('ToolbarIcons', 'lutedit'): self._toolbar.addAction(self._action['lutedit'])
        n = len(self._toolbar.actions())
        if n > 0 and not self._toolbar.actions()[n-1].isSeparator(): self._toolbar.addSeparator()
        if self._settings.getFieldValue('ToolbarIcons', 'pref'): self._toolbar.addAction(self._action['pref'])
        if self._settings.getFieldValue('ToolbarIcons', 'exit'): self._toolbar.addAction(self._action['exit'])
        n = len(self._toolbar.actions())
        if n > 0 and self._toolbar.actions()[n-1].isSeparator(): self._toolbar.removeAction(self._toolbar.actions()[n-1])
        self.addToolBar(Qt.TopToolBarArea, self._toolbar)
        self.addToolBarBreak(Qt.TopToolBarArea)
        self._toolbar.setStyleSheet('QToolButton:pressed {border-color: rgb(176, 176, 176); border-style: '
                                    'solid; border-width: 1px; border-radius: 6px;}')
        if n == 0: self._toolbar.setVisible(False)
        else:
            v = self._settings.getFieldValue('GUI', 'ToolbarVisibility')
            if v is None: v = True
            self._toolbar.setVisible(v)

    def _updateRecentMenu(self):
        self._recent.updateQMenu(self._menu['recent'])

    def _updateStructsMenu(self):
        path = join(self.getUserDirectory(), 'segmentation')
        if not exists(path): mkdir(path)
        path = join(path, '*.xml')
        files = glob(path)
        if len(files) > 0:
            self._menu['rseg'].clear()
            for file in files:
                if exists(file):
                    action = self._menu['rseg'].addAction(splitext(basename(file))[0])
                    action.setData(file)

    def _updateModelsMenu(self):
        path = join(self.getUserDirectory(), 'models')
        if not exists(path): mkdir(path)
        path = join(path, '*{}'.format(SisypheDesign.geModelExt()))
        files = glob(path)
        if len(files) > 0:
            self._menu['model'].clear()
            for file in files:
                if exists(file):
                    action = self._menu['model'].addAction(splitext(basename(file))[0])
                    action.setData(file)
                self._menu['model'].addSeparator()
            self._menu['model'].addAction('Load model...')

    def _openRecent(self, action):
        file = action.text()
        if file == 'Clear':
            self._menu['recent'].clear()
            self._recent.clear()
            self._recent.save()
        else:
            file = str(action.data())
            if exists(file): self.open(file)

    def _openStruct(self, action):
        file = join(self.getUserDirectory(), 'segmentation', action.text())
        if exists(file):
            from Sisyphe.gui.dialogSegmentation import DialogRegistrationBasedSegmentation
            self._dialog = DialogRegistrationBasedSegmentation(filename=file)
            self._dialog.exec()

    def _openModel(self, action):
        file = action.text()
        if file == 'Load model...':
            file = QFileDialog.getOpenFileName(self, 'Open Model...', getcwd(),
                                               filter='Model (*{})'.format(SisypheDesign.geModelExt()))[0]
        else: file = str(action.data())
        if file and exists(file): pass

    def updateTimers(self, index):
        if index is None: index = self._tabview.currentIndex()
        # Timer update
        for i in range(0, 3):
            w = self._tabview.widget(i)
            if i == index:
                w.timerEnabled()
                self._menuView[i].setVisible(w.hasVolume())
            else:
                w.timerDisabled()
                self._menuView[i].setVisible(False)

    # Settings public methods

    def getDisplayScaleFactor(self):
        return self.screen().devicePixelRatio()

    def setToolbarSize(self, size=_TOOLBARICONSIZE):
        self._toolbar.setFixedHeight(size + 8)
        self._toolbar.setIconSize(QSize(size, size))

    def setThumbnailSize(self, size=_THUMBNAILSIZE):
        self._thumbnail.setSize(size)

    def setDockIconSize(self, size=_ICONSIZE):
        self._tabROIList.setIconSize(size + 8)
        self._tabROITools.setIconSize(size + 8)

    def setViewportsFontSize(self, s):
        if isinstance(s, int):
            self._sliceview.getViewWidget().getFirstViewWidget().setFontSize(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setFontSize(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setFontSize(s)
        else: raise TypeError('parameter type {} is not int.'.format(type(s)))

    def setViewportsFontFamily(self, s):
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setFontFamily(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setFontFamily(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setFontFamily(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsLineWidth(self, s):
        if isinstance(s, float):
            self._sliceview.getViewWidget().getFirstViewWidget().setLineWidth(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setLineWidth(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setLineWidth(s)
        else: raise TypeError('parameter type {} is not int.'.format(type(s)))

    def setViewportsLineColor(self, c):
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                self._sliceview.getViewWidget().getFirstViewWidget().setLineColor(c)
                self._orthoview.getViewWidget().getFirstViewWidget().setLineColor(c)
                self._synchroview.getViewWidget().getFirstViewWidget().setLineColor(c)
            else: raise TypeError('invalid element count.')
        else: raise TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def setViewportsLineSelectedColor(self, c):
        if isinstance(c, (list, tuple)):
            if len(c) == 3:
                self._sliceview.getViewWidget().getFirstViewWidget().setLineSelectedColor(c)
                self._orthoview.getViewWidget().getFirstViewWidget().setLineSelectedColor(c)
                self._synchroview.getViewWidget().getFirstViewWidget().setLineSelectedColor(c)
            else: raise TypeError('invalid element count.')
        else: raise TypeError('parameter type {} is not tuple or list.'.format(type(c)))

    def setViewportsLineOpacity(self, s):
        if isinstance(s, float):
            self._sliceview.getViewWidget().getFirstViewWidget().setLineOpacity(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setLineOpacity(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setLineOpacity(s)
        else: raise TypeError('parameter type {} is not float.'.format(type(s)))

    def setViewportsAttributesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoIdentityVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoIdentityVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoVolumeVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoVolumeVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoAcquisitionVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setInfoAcquisitionVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsOrientationLabelsVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setOrientationLabelsVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoPositionVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setInfoPositionVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativeACCoordinatesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativeACCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativePCCoordinatesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativePCCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRelativeACPCCoordinatesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setRelativeACPCCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsFrameCoordinatesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setFrameCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsICBMCoordinatesVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setICBMCoordinatesVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsInfoValueVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
            self._orthoview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
            self._synchroview.getViewWidget().getFirstSliceViewWidget().setInfoValueVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsCursorVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setCursorVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsRulerPosition(self, s):
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsRulerVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsTooltipVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setTooltipVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsColorbarPosition(self, s):
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerPosition(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsColorbarVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setRulerVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def setViewportsOrientationMarkerShape(self, s):
        if isinstance(s, str):
            self._sliceview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
            self._orthoview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
            self._synchroview.getViewWidget().getFirstViewWidget().setOrientationMarker(s)
        else: raise TypeError('parameter type {} is not str.'.format(type(s)))

    def setViewportsOrientationMarkerVisibility(self, v):
        if isinstance(v, bool):
            self._sliceview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
            self._orthoview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
            self._synchroview.getViewWidget().getFirstViewWidget().setOrientationMakerVisibility(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    # Public methods

    def getActions(self):
        return self._action

    def toggleFullscreen(self):
        if self.isFullScreen():
            self._action['wfull'].setChecked(False)
            self.showMaximized()
            self._toolbar.setVisible(self._action['toolbar'].isChecked())
            self._thumbnail.setVisible(self._action['thumb'].isChecked())
            self._dock.setVisible(self._action['dock'].isChecked())
            self._status.setVisible(self._action['status'].isChecked())
        else:
            self._action['wfull'].setChecked(True)
            self.showFullScreen()
            self._toolbar.setVisible(False)
            self._thumbnail.setVisible(False)
            self._dock.setVisible(False)
            self._status.setVisible(False)

    def getToolbar(self):
        return self._toolbar

    def showToolbar(self):
        self._toolbar.setVisible(True)
        self._action['toolbar'].setChecked(True)

    def hideToolbar(self):
        self._toolbar.setVisible(False)
        self._action['toolbar'].setChecked(False)

    def setToolbarVisibility(self, v):
        if isinstance(v, bool):
            self._toolbar.setVisible(v)
            self._action['toolbar'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getToolbarVisibility(self):
        return self._toolbar.isVisible()

    def getThumbnail(self):
        return self._thumbnail

    def showThumbnail(self):
        self._thumbnail.setVisible(True)
        self._action['thumb'].setChecked(True)

    def hideThumbnail(self):
        self._thumbnail.setVisible(False)
        self._action['thumb'].setChecked(False)

    def setThumbnailVisibility(self, v):
        if isinstance(v, bool):
            self._thumbnail.setVisible(v)
            self._action['thumb'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getThumbnailVisibility(self):
        return self._thumbnail.isVisible()

    def getDock(self):
        return self._dock

    def showDock(self):
        self._dock.setVisible(True)
        self._action['dock'].setChecked(True)

    def hideDock(self):
        self._dock.setVisible(False)
        self._action['dock'].setChecked(False)

    def setDockVisibility(self, v):
        if isinstance(v, bool):
            self._dock.setVisible(v)
            self._action['dock'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getDockVisibility(self):
        return self._dock.isVisible()

    def getDatabase(self):
        return self._database

    def getScreenshots(self):
        return self._captures

    def getROIListWidget(self):
        return self._tabROIList

    def getROIToolsWidget(self):
        return self._tabROITools

    def getMeshListWidget(self):
        return self._tabMeshList

    def getTargetListWidget(self):
        return self._tabTargetList

    def clearDockListWidgets(self):
        self._tabROIList.getROIListWidget().removeAll()
        self._tabMeshList.getMeshListWidget().removeAll()
        self._tabTargetList.getToolListWidget().removeAll()
        self._tabROITools.setEnabled(False)
        self._tabROITools.setVisible(False)
        self._dock.setTabVisible(1, False)

    def getStatusBar(self):
        return self._status

    def updateMemoryUsage(self):
        self._statuslabel.setText(self.getMemoryUsage())

    def setStatusBarMessage(self, txt):
        if isinstance(txt, str):
            self._status.showMessage(txt)
        else: raise TypeError('parameter type {} is not str.'.format(type(txt)))

    def showStatusBar(self):
        self._status.show()
        self._action['status'].setChecked(True)

    def hideStatusBar(self):
        self._status.hide()
        self._action['status'].setChecked(False)

    def setStatusBarVisibility(self, v):
        if isinstance(v, bool):
            self._status.setVisible(v)
            self._action['status'].setChecked(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getStatusBarVisibility(self):
        return self._status.isVisible()

    def showSlicesView(self):
        self._tabview.setTabVisible(0, True)

    def hideSlicesView(self):
        self._tabview.setTabVisible(0, False)

    def setSliceViewVisibility(self, v):
        if isinstance(v, bool): self._tabview.setTabVisible(0, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSliceViewVisibility(self):
        return self._tabview.isTabVisible(0)

    def showOrthogonalView(self):
        self._tabview.setTabVisible(1, True)

    def hideOrthogonalView(self):
        self._tabview.setTabVisible(1, False)

    def setOrthogonalViewVisibility(self, v):
        if isinstance(v, bool): self._tabview.setTabVisible(1, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getOrthogonalViewVisibility(self):
        return self._tabview.isTabVisible(1)

    def showSynchronisedView(self):
        self._tabview.setTabVisible(2, True)

    def hideSynchronisedView(self):
        self._tabview.setTabVisible(2, False)

    def setSynchronisedViewVisibility(self, v):
        if isinstance(v, bool): self._tabview.setTabVisible(2, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getSynchronisedViewVisibility(self):
        return self._tabview.isTabVisible(1)

    def setTabViewVisibility(self, index, v):
        if isinstance(index, int):
            if isinstance(v, bool):
                self._tabview.setTabVisible(index, v)
            else: raise TypeError('second parameter type {} is not bool.'.format(type(v)))
        else: raise TypeError('first parameter type {} is not int.'.format(type(index)))

    def setDockEnabled(self, v):
        if isinstance(v, bool):
            self._tabROIList.setEnabled(v)
            self._tabMeshList.setEnabled(v)
            self._tabTargetList.setEnabled(v)
            if v is True:
                self._tabROIList.setViewCollection(self._views)
                self._tabROITools.setViewCollection(self._views)
                self._tabMeshList.setViewCollection(self._views)
                self._tabTargetList.setViewCollection(self._views)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isDockEnabled(self):
        return self._tabROIList.isEnabled()

    def setROIToolsEnabled(self, v):
        if isinstance(v, bool): self._tabROITools.setEnabled(v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def isROIToolsEnabled(self):
        return self._tabROITools.isEnabled()

    def setROIToolsVisibility(self, v):
        if isinstance(v, bool):
            self._tabROITools.setVisible(v)
            self._dock.setTabVisible(1, v)
        else: raise TypeError('parameter type {} is not bool.'.format(type(v)))

    def getROIToolsVisibility(self):
        return self._dock.isTabVisible(1)

    def addRecent(self, filename):
        self._recent.append(filename)

    # Application menu methods

    def exit(self):
        self._recent.save()
        self.close()

    def about(self):
        self._dialog = DialogSplash()
        self._dialog.buttonVisibilityOn()
        self._dialog.progressBarVisibilityOff()
        self._dialog.exec()

    def preferences(self):
        self._dialog = DialogSettings()
        self._dialog.setMainWindow(self)
        self._dialog.exec()

    # File menu methods

    def open(self, filenames=None):
        self._thumbnail.open(filenames)

    def save(self):
        self._thumbnail.saveSelected()

    def saveall(self):
        self._thumbnail.saveAll()

    def saveAs(self):
        self._thumbnail.saveSelectedAs()

    def remove(self):
        self._thumbnail.removeSelected()

    def removeAll(self):
        self._thumbnail.removeAll()

    def loadNifti(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open Nifti...', getcwd(),
                                                 filter='Nifti (*.nii *.hdr *.img *.nia *.nii.gz *.img.gz)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Nifti...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromNIFTI(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open Nifti...', '{}'.format(err))
            wait.close()

    def saveNifti(self):
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Nifti', vol.getFilename(),
                                                   filter='Nifti (*.nii)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: vol.saveToNIFTI(filename)
                except Exception as err: QMessageBox.warning(self, 'Save Nifti', '{}'.format(err))
                self.setStatusBarMessage('Volume {} saved.'.format(vol.getBasename()))
        else: QMessageBox.warning(self, 'Save Nifti', 'No volume selected.')

    def loadMinc(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open Minc...', getcwd(), filter='Minc (*.mnc *.minc)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Minc...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromMINC(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open Minc...', '{}'.format(err))
            wait.close()

    def loadNrrd(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open Nrrd...', getcwd(), filter='Nrrd (*.nrrd *.nhdr)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Nrrd...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromNRRD(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open Nrrd...', '{}'.format(err))
            wait.close()

    def loadVtk(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open Vtk...', getcwd(), filter='Vtk (*.vti *.vtk)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Vtk...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromVTK(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open Vtk...', '{}'.format(err))
            wait.close()

    def loadSis(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open Sisyphe...', getcwd(), 'Sisyphe (*.vol)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open Sisyphe...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromSisyphe(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open Sisyphe...', '{}'.format(err))
            wait.close()

    def loadVmr(self):
        filenames = QFileDialog.getOpenFileNames(self, 'Open BrainVoyager VMR...',
                                                 getcwd(), 'BrainVoyager VMR (*.vmr)')[0]
        QApplication.processEvents()
        n = len(filenames)
        if n > 0:
            chdir(dirname(filenames[0]))
            if n == 1: progress, cancel = False, False
            else: progress, cancel = True, True
            wait = DialogWait(title='Open BrainVoyager VMR...', progress=progress, progressmin=0, progressmax=n,
                              progresstxt=True, anim=False, cancel=cancel, parent=self)
            wait.open()
            try:
                for filename in filenames:
                    wait.setInformationText('Open {}...'.format(basename(filename)))
                    v = SisypheVolume()
                    v.loadFromBrainVoyagerVMR(filename)
                    self.addVolume(v)
                    v.save()
                    wait.incCurrentProgressValue()
                    if wait.getStopped(): break
            except Exception as err:
                QMessageBox.warning(self, 'Open BrainVoyager VMR...', '{}'.format(err))
            wait.close()

    def saveMinc(self):
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Minc', vol.getFilename(),
                                                   filter='Minc (*.mnc)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: vol.saveToMINC(filename)
                except Exception as err: QMessageBox.warning(self, 'Save Minc', '{}'.format(err))
                self.setStatusBarMessage('Volume {} saved.'.format(vol.getBasename()))
        else: QMessageBox.warning(self, 'Save Minc', 'No volume selected.')

    def saveNrrd(self):
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Nrrd', vol.getFilename(),
                                                   filter='Nrrd (*.nrrd)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: vol.saveToNRRD(filename)
                except Exception as err: QMessageBox.warning(self, 'Save Nrrd', '{}'.format(err))
                self.setStatusBarMessage('Volume {} saved.'.format(vol.getBasename()))
        else: QMessageBox.warning(self, 'Save Nrrd', 'No volume selected.')

    def saveVtk(self):
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save VTK', vol.getFilename(),
                                                   filter='VTK (*.vti)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: vol.saveToVTK(filename)
                except Exception as err: QMessageBox.warning(self, 'Save VTK', '{}'.format(err))
                self.setStatusBarMessage('Volume {} saved.'.format(vol.getBasename()))
        else: QMessageBox.warning(self, 'Save VTK', 'No volume selected.')

    def saveNumpy(self):
        vol = self._thumbnail.getSelectedVolume()
        if vol is not None:
            filename = QFileDialog.getSaveFileName(self, 'Save Numpy', vol.getFilename(),
                                                   filter='Numpy (*.npy)')[0]
            QApplication.processEvents()
            if filename:
                chdir(dirname(filename))
                try: vol.saveToNumpy(filename)
                except Exception as err: QMessageBox.warning(self, 'Save Numpy', '{}'.format(err))
                self.setStatusBarMessage('Volume {} saved.'.format(vol.getBasename()))
        else: QMessageBox.warning(self, 'Save Numpy', 'No volume selected.')

    def importNifti(self):
        self._dialog = DialogImport(io='Nifti', parent=self)
        self._dialog.exec()

    def importMinc(self):
        self._dialog = DialogImport(io='Minc', parent=self)
        self._dialog.exec()

    def importNrrd(self):
        self._dialog = DialogImport(io='Nrrd', parent=self)
        self._dialog.exec()

    def importVtk(self):
        self._dialog = DialogImport(io='Vtk', parent=self)
        self._dialog.exec()

    def importSis(self):
        self._dialog = DialogOldSisypheImport(parent=self)
        self._dialog.exec()

    def importDicom(self):
        self._dialog = DialogDicomImport(parent=self)
        self._dialog.exec()

    def exportNifti(self):
        self._dialog = DialogExport(io='Nifti', parent=self)
        self._dialog.exec()

    def exportMinc(self):
        self._dialog = DialogExport(io='Minc', parent=self)
        self._dialog.exec()

    def exportNrrd(self):
        self._dialog = DialogExport(io='Nrrd', parent=self)
        self._dialog.exec()

    def exportVtk(self):
        self._dialog = DialogExport(io='Vtk', parent=self)
        self._dialog.exec()

    def exportNumpy(self):
        self._dialog = DialogExport(io='Numpy', parent=self)
        self._dialog.show()

    def exportDicom(self):
        self._dialog = DialogDicomExport(parent=self)
        self._dialog.exec()

    def datasetDicom(self):
        self._dialog = DialogDicomDataset()
        self._dialog.exec()

    def xmlDicom(self):
        from Sisyphe.core.sisypheDicom import XmlDicom
        filename = QFileDialog.getOpenFileName(self, 'Open Xml Dicom...', getcwd(),
                                               filter=XmlDicom.getFilterExt())[0]
        if filename:
            from Sisyphe.gui.dialogXmlDicom import DialogXmlDicom
            self._dialog = DialogXmlDicom(filename)
            self._dialog.exec()

    def editAttr(self):
        self._thumbnail.editAttributesSelected()

    def editLabels(self, filename=''):
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                dialog = DialogFileSelection(parent=self)
                dialog.setWindowTitle('Edit labels')
                dialog.filterSisypheVolume()
                dialog.filterSameModality('LB')
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            from Sisyphe.gui.dialogEditLabels import DialogEditLabels
            self._dialog = DialogEditLabels()
            self._dialog.setVolume(v)
            self._dialog.exec()

    def volToLabel(self):
        from Sisyphe.gui.dialogLabel import DialogVOLtoLabel
        self._dialog = DialogVOLtoLabel()
        self._dialog.exec()

    def roiToLabel(self):
        from Sisyphe.gui.dialogLabel import DialogROItoLabel
        self._dialog = DialogROItoLabel()
        self._dialog.exec()

    def labelToRoi(self):
        from Sisyphe.gui.dialogLabel import DialogLabeltoROI
        self._dialog = DialogLabeltoROI()
        self._dialog.exec()

    def download(self):
        from Sisyphe.gui.dialogDownload import DialogDownload
        self._dialog = DialogDownload()
        self._dialog.exec()

    def checkUpdate(self):
        from Sisyphe import version
        wait = DialogWait(progress=False, parent=self)
        wait.setInformationText('Check for update, connection to host...')
        wait.open()
        try: v = version.getVersionFromHost()
        except:
            wait.close()
            QMessageBox.warning(self, 'Check for update', 'Host connection failed.')
            return None
        if version.isCurrentVersion(v):
            wait.close()
            QMessageBox.information(self,
                                    'Check for update',
                                    'PySisyphe version {} is up-to-date'.format(version.__version__))
        elif version.isOlderThan(v):
            wait.hide()
            r = QMessageBox.question(self,
                                     'Check for update',
                                     'A more recent version of PySisyphe is available.'
                                     ' Would you like to install it ?')
            if r == QMessageBox.Yes:
                from Sisyphe.core.sisypheDownload import updatePySisypheToNewerVersion
                wait.setInformationText('Updating to {} version...'.format(v))
                wait.show()
                updatePySisypheToNewerVersion(wait)
            wait.close()

    def lutEdit(self):
        self._dialog = DialogLutEdit()
        self._dialog.exec()

    # Functions menu methods

    def join(self):
        title = 'Join single component volume(s)'
        dialog = DialogFilesSelection(parent=self)
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
                                  progresstxt=True, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                vols = list()
                for filename in filenames:
                    v = SisypheVolume()
                    v.load(filename)
                    vols.append(v)
                try: img = multiComponentSisypheVolumeFromList(vols)
                except Exception as err:
                    QMessageBox.warning(self, title, '{}'.format(err))
                    img = None
                wait.close()
                if img is not None:
                    img.setFilename(filenames[0])
                    img.setFilenamePrefix('Multi_')
                    filename = QFileDialog.getSaveFileName(self, title, img.getFilename(),
                                                           filter='PySisyphe volume (*.xvol)')[0]
                    QApplication.processEvents()
                    if filename: img.saveAs(filename)

    def split(self):
        title = 'Split multi component volume(s)'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterMultiComponent()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 0:
                wait = DialogWait(title=title, progress=True, progressmin=0, progressmax=n,
                                  progresstxt=True, anim=False, cancel=False, parent=self)
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
                                QMessageBox.warning(self, title, '{}'.format(err))
                    wait.close()

    def datatype(self):
        self._dialog = DialogDatatype()
        self._dialog.exec()

    def flip(self):
        from Sisyphe.gui.dialogFlipAxes import DialogFlipAxes
        dialog = DialogFlipAxes(parent=self)
        dialog.exec()

    def swap(self):
        from Sisyphe.gui.dialogSwapAxes import DialogSwapAxes
        dialog = DialogSwapAxes(parent=self)
        dialog.exec()

    def algmean(self):
        title = 'Mean volume calculation'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                QApplication.processEvents()
                try:
                    l = list()
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
                except Exception as err:
                    wait.hide()
                    QMessageBox.warning(self, title, '{}'.format(err))
                wait.close()

    def algmedian(self):
        title = 'Median volume calculation'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                QApplication.processEvents()
                try:
                    l = list()
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
                except Exception as err:
                    wait.hide()
                    QMessageBox.warning(self, title, '{}'.format(err))
                wait.close()

    def algstd(self):
        title = 'Standard deviation volume calculation'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                QApplication.processEvents()
                try:
                    l = list()
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
                except Exception as err:
                    wait.hide()
                    QMessageBox.warning(self, title, '{}'.format(err))
                wait.close()

    def algmin(self):
        title = 'Minimum volume calculation'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                QApplication.processEvents()
                try:
                    l = list()
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
                except Exception as err:
                    wait.hide()
                    QMessageBox.warning(self, title, '{}'.format(err))
                wait.close()

    def algmax(self):
        title = 'Maximum volume calculation'
        dialog = DialogFilesSelection(parent=self)
        dialog.setWindowTitle(title)
        dialog.filterSisypheVolume()
        dialog.filterSingleComponent()
        dialog.filterSameSize()
        dialog.setCurrentVolumeButtonVisibility(False)
        if dialog.exec():
            filenames = dialog.getFilenames()
            n = len(filenames)
            if n > 1:
                wait = DialogWait(title=title, progress=False, progressmin=0, progressmax=0,
                                  progresstxt=False, anim=False, cancel=False, parent=self)
                wait.setInformationText(title)
                wait.open()
                QApplication.processEvents()
                try:
                    l = list()
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
                except Exception as err:
                    wait.hide()
                    QMessageBox.warning(self, title, '{}'.format(err))
                wait.close()

    def algmath(self):
        self._dialog = DialogAlgebra()
        self._dialog.exec()

    def texture(self):
        self._dialog = DialogTexture()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def histmatch(self):
        self._dialog = DialogHistogramMatching()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterMean(self):
        self._dialog = DialogMeanFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterMedian(self):
        self._dialog = DialogMedianFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterGaussian(self):
        self._dialog = DialogGaussianFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterGradient(self):
        self._dialog = DialogGradientFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterLaplacian(self):
        self._dialog = DialogLaplacianFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterAniso(self):
        self._dialog = DialogAnisotropicDiffusionFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterNonLocalMeans(self):
        from Sisyphe.gui.dialogFunction import DialogNonLocalMeansFilter
        self._dialog = DialogNonLocalMeansFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def filterBias(self):
        self._dialog = DialogBiasFieldCorrectionFilter()
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    # Registration menu methods

    def frameDetection(self, filename=''):
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                dialog = DialogFileSelection(parent=self)
                dialog.setWindowTitle('Stereotactic frame detection')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            self._dialog = DialogFiducialBox(parent=self)
            self._dialog.setVolume(v)
            self._dialog.exec()
            n = self._thumbnail.getVolumeIndex(v)
            if n is not None:
                widget = self._thumbnail.getWidgetFromIndex(n)
                widget.updateTooltip()

    def acpcSelection(self, filename=''):
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                dialog = DialogFileSelection(parent=self)
                dialog.setWindowTitle('AC-PC selection')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            self._dialog = DialogACPC(parent=self)
            self._dialog.setVolume(v)
            self._dialog.exec()
            n = self._thumbnail.getVolumeIndex(v)
            if n is not None:
                v.load()
                widget = self._thumbnail.getWidgetFromIndex(n)
                widget.updateTooltip()

    def reorient(self, filename=''):
        v = None
        if isinstance(filename, SisypheVolume):
            v = filename
        elif isinstance(filename, str):
            if filename == '' or not exists(filename):
                dialog = DialogFileSelection(parent=self)
                dialog.setWindowTitle('Volume reorientation')
                dialog.filterSisypheVolume()
                dialog.setToolBarThumbnail(self._thumbnail)
                if dialog.exec():
                    filename = dialog.getFilename()
            if filename != '' and exists(filename):
                v = SisypheVolume()
                v.load(filename)
        if v is not None and isinstance(v, SisypheVolume):
            self._dialog = DialogReorient(parent=self)
            self._dialog.setVolume(v)
            self._dialog.exec()

    def manualRegistration(self):
        self._dialog = DialogMultiFileSelection(parent=self)
        self._dialog.setWindowTitle('Manual registration volumes selection')
        self._dialog.createFileSelectionWidget('Fixed', toolbar=self._thumbnail, current=True)
        self._dialog.createFileSelectionWidget('Moving', toolbar=self._thumbnail, current=True)
        if self._dialog.exec():
            wait = DialogWait(title='Open volumes for manual registration', progress=False, parent=self)
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
            self._dialog.setDialogToResample()
            wait.close()
            self._dialog.exec()

    def rigidRegistration(self, fixed=None, moving=None):
        self._dialog = DialogRegistration(transform='Rigid', parent=self)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        if fixed is not None: self._dialog.setFixed(fixed, editable=False)
        if moving is not None: self._dialog.setMoving(moving, editable=False)
        self._dialog.exec()

    def affineRegistration(self):
        self._dialog = DialogRegistration(transform='Affine', parent=self)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def displacementFieldRegistration(self):
        self._dialog = DialogRegistration(transform='DisplacementField', parent=self)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def normalize(self):
        self._dialog = DialogICBMNormalization(parent=self)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getApplyToSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def batchRegistration(self):
        self._dialog = DialogBatchRegistration(parent=self)
        self._dialog.getFixedSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getBatchSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def realignment(self):
        self._dialog = DialogSeriesRealignment(parent=self)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def eddycurrent(self):
        self._dialog = DialogEddyCurrentCorrection(parent=self)
        self._dialog.getB0SelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.getDWISelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def resample(self):
        self._dialog = DialogResample(parent=self)
        self._dialog.getMovingSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def jacobian(self):
        self._dialog = DialogJacobian(parent=self)
        self._dialog.getSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    # Segmentation menu methods

    def skullStriping(self):
        from Sisyphe.gui.dialogSkullStripping import DialogSkullStripping
        self._dialog = DialogSkullStripping(parent=self)
        self._dialog.getFilesSelectionWidget().setToolbarThumbnail(self._thumbnail)
        self._dialog.exec()

    def unsupervisedKMeans(self):  # to do
        pass

    def supervisedKMeans(self):  # to do
        pass

    # Statistical map menu methods

    def model(self, groups, subjects, conditions, fmri):
        print('condition(s) {} subject(s) {} group(s) {}'.format(conditions, subjects, groups))
        if fmri: self._dialog = DialogfMRIObs(conditions, subjects, groups, parent=self)
        else: self._dialog = DialogObs(conditions, subjects, groups, parent=self)
        if self._dialog.exec():
            cnd = self._dialog.getConditionCount()
            sbj = self._dialog.getSubjectCount()
            grp = self._dialog.getGroupCount()
            if fmri:
                obscnd = self._dialog.getConditionsBoxCar()
                obsgrp = None
            else:
                obscnd = self._dialog.getConditionsObsCount()
                obsgrp = self._dialog.getGroupsObsCount()
            print('condition(s) {} subject(s) {} group(s) {}'.format(cnd, sbj, grp))
            self._dialog = DialogModel(cnd, sbj, grp, obscnd, obsgrp, fmri, parent=self)
            self._dialog.exec()

    def contrast(self, filename=''):  # to do
        if filename == '' or not exists(filename):
            pass
        self._dialog = DialogContrast(filename)

    def result(self):  # to do
        pass

    def population(self):  # to do
        pass

    def subjectVsPopulation(self):  # to do
        pass

    # Diffusion methods

    def diffusionGradients(self):
        from Sisyphe.gui.dialogDiffusionGradients import DialogDiffusionGradients
        self._dialog = DialogDiffusionGradients(parent=self)
        self._dialog.exec()

    def diffusionPreprocessing(self):
        from Sisyphe.gui.dialogDiffusionPreprocessing import DialogDiffusionPreprocessing
        self._dialog = DialogDiffusionPreprocessing(parent=self)
        self._dialog.exec()

    def diffusionModel(self):
        from Sisyphe.gui.dialogDiffusionModel import DialogDiffusionModel
        self._dialog = DialogDiffusionModel(parent=self)
        self._dialog.exec()

    def diffusionTractorgram(self):
        pass

    # Public command methods (generate exceptions)

    def addVolume(self, vol):
        self._thumbnail.addVolume(vol)
