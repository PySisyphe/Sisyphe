"""
External packages/modules
-------------------------

    - PyQt5, Qt GUI, https://www.riverbankcomputing.com/software/pyqt/
"""

from sys import platform

from os.path import join
from os.path import exists
from os.path import abspath
from os.path import dirname
from os.path import basename

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QSizePolicy
from PyQt5.QtWidgets import QDialog
from PyQt5.QtWebEngineWidgets import QWebEnginePage
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QApplication

# noinspection PyCompatibility
from Sisyphe.core.sisypheTracts import SisypheStreamlines
from Sisyphe.core.sisypheROI import SisypheROI
from Sisyphe.core.sisypheROI import SisypheROICollection
from Sisyphe.widgets.basicWidgets import messageBox
from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.basicWidgets import LabeledLineEdit
from Sisyphe.widgets.selectFileWidgets import FileSelectionWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.widgets.iconBarViewWidgets import IconBarMultiSliceGridViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarSynchronisedGridViewWidget
from Sisyphe.widgets.attributesWidgets import ListROIAttributesWidget
from Sisyphe.widgets.attributesWidgets import ListMeshAttributesWidget
from Sisyphe.widgets.attributesWidgets import ListToolAttributesWidget
from Sisyphe.widgets.attributesWidgets import ListBundleAttributesWidget
from Sisyphe.widgets.thresholdWidgets import ThresholdViewWidget
from Sisyphe.widgets.functionsSettingsWidget import SettingsWidget
from Sisyphe.gui.dialogROIStatistics import DialogROIStatistics
from Sisyphe.gui.dialogDiffusionBundle import DialogStreamlinesROISelection
from Sisyphe.gui.dialogDiffusionBundle import DialogStreamlinesAtlasSelection
from Sisyphe.gui.dialogSettings import DialogFunctionSetting
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['TabROIListWidget',
           'TabROIToolsWidget',
           'TabMeshListWidget',
           'TabTargetListWidget',
           'TabTrackingWidget',
           'TabHelpWidget']

"""
Class hierarchy
~~~~~~~~~~~~~~~

    - QWidget -> TabWidget
              -> TabWidget -> TabROIListWidget
                           -> TabROIToolsWidget
                           -> TabMeshListWidget
                           -> TabTargetListWidget
                           -> TabTrackingWidget
                           -> TabHelpWidget
"""

class TabWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    Base class for all specialized QTabBar page widgets (ROI, Mesh, Target, Tracking, Help)

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabWidget
    """
    _VSIZE = 32

    # Class method

    @classmethod
    def getDefaultIconSize(cls):
        return cls._VSIZE

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(parent)
        # < Revision 07/07/2025
        self._logger = logging.getLogger(__name__)
        # Revision 07/07/2025 >

        self._views = views
        self._collection = None

        # Layout

        lyout = QVBoxLayout()
        if platform == 'darwin': lyout.setContentsMargins(0, 0, 10, 0)
        else: lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        self.setLayout(lyout)

    # Public methods

    def setViewCollection(self, views):
        if isinstance(views, IconBarViewWidgetCollection): self._views = views
        else: self._views = None

    def getViewCollection(self):
        return self._views

    def hasViewCollection(self):
        return self._views is not None

    def getCollection(self):
        return self._collection

    def hasCollection(self):
        return self._collection is not None


class TabROIListWidget(TabWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display ROIListWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabROIListWidget

    Last revision: 20/02/2025
    """

    # Special method

    """
    Private attributes
    
    _draw               SisypheROIDraw
    _list               ListROIAttributesWidget
    _collection         IconBarViewWidgetCollection
    _btunion            IconPushButton, ROIs union button
    _btinter            IconPushButton, ROIs intersection button
    _btsymdiff          IconPushButton, ROIs symmetric difference button
    _btdiff             IconPushButton, ROIs difference button
    """

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._draw = None
        self._list = ListROIAttributesWidget(parent=self)

        # Widgets

        self._btunion = IconPushButton('union.png', size=TabWidget._VSIZE)
        self._btinter = IconPushButton('intersection.png', size=TabWidget._VSIZE)
        self._btsymdiff = IconPushButton('differencesym.png', size=TabWidget._VSIZE)
        self._btdiff = IconPushButton('difference.png', size=TabWidget._VSIZE)

        # noinspection PyUnresolvedReferences
        self._btunion.clicked.connect(self.union)
        # noinspection PyUnresolvedReferences
        self._btinter.clicked.connect(self.intersection)
        # noinspection PyUnresolvedReferences
        self._btsymdiff.clicked.connect(self.symmetricDifference)
        # noinspection PyUnresolvedReferences
        self._btdiff.clicked.connect(self.difference)

        self._btunion.setToolTip('Selected and checked ROI union (OR)')
        self._btinter.setToolTip('Selected and checked ROI intersection (AND)')
        self._btsymdiff.setToolTip('Selected and checked ROI symmetric difference (XOR)')
        self._btdiff.setToolTip('Selected ROI - Checked ROI union (NAND)')

        groupbox = QGroupBox('Set operators')
        grouplyout = QHBoxLayout()
        grouplyout.setContentsMargins(5, 10, 5, 10)
        grouplyout.setSpacing(5)
        grouplyout.addStretch()
        grouplyout.addWidget(self._btunion)
        grouplyout.addWidget(self._btinter)
        grouplyout.addWidget(self._btsymdiff)
        grouplyout.addWidget(self._btdiff)
        grouplyout.addStretch()
        groupbox.setLayout(grouplyout)

        # Layout

        lyout = self.layout()
        lyout.addWidget(self._list)
        lyout.addWidget(groupbox)

        margins1 = self.contentsMargins()
        margins2 = lyout.contentsMargins()
        self.setMinimumWidth(self._list.minimumWidth() +
                             margins1.left() + margins1.right() +
                             margins2.left() + margins2.right())

    # Private method

    def _updateROIDisplay(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.updateROIDisplay()

    # Public methods

    def setIconSize(self, size=TabWidget._VSIZE):
        self._btunion.setIconSize(QSize(size - 8, size - 8))
        self._btunion.setFixedSize(size, size)
        self._btinter.setIconSize(QSize(size - 8, size - 8))
        self._btinter.setFixedSize(size, size)
        self._btsymdiff.setIconSize(QSize(size - 8, size - 8))
        self._btsymdiff.setFixedSize(size, size)
        self._btdiff.setIconSize(QSize(size - 8, size - 8))
        self._btdiff.setFixedSize(size, size)
        self._list.setIconSize(size)

    def getIconSize(self):
        return self._btunion.width()

    def setViewCollection(self, views):
        super().setViewCollection(views)

        if isinstance(views, IconBarViewWidgetCollection):
            self._collection = views.getROICollection()
            self._draw = views.getROIDraw()
            self._list.setViewCollection(views)
        else:
            self._draw = None
            self._collection = None

    # < Revision 02/11/2024
    # add setMaxCount method
    def setMaxCount(self, v):
        if self._list is not None:
            self._list.setMaxCount(v)
    # Revision 02/11/2024 >

    # < Revision 02/11/2024
    # add getMaxCount method
    def getMaxCount(self):
        if self._list is not None: return self._list.getMaxCount()
        else: raise AttributeError('_list attribute is None.')
    # Revision 02/11/2024 >

    def getROIListWidget(self):
        return self._list

    def union(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw.hasROI():
                if self._collection.count() > 1:
                    if self._list.count() < self._list.getMaxCount():
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'Union {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait()
                                wait.open()
                                wait.setInformationText('Union...')
                                self._draw.binaryOR(rois)
                                self._updateROIDisplay()
                                wait.close()
                                self._logger.info('ROI {}'.format(name))
                            else: messageBox(self, 'ROI Union', 'Less than two ROI checked.')
                    else:
                        messageBox(self, 'ROI union',
                                   text='Maximum number of ROIs reached.\n'
                                        'Close a ROI to add a new one.',
                                   icon=QMessageBox.Information)

    def intersection(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw.hasROI():
                if self._collection.count() > 1:
                    if self._list.count() < self._list.getMaxCount():
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'Intersection {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait()
                                wait.open()
                                wait.setInformationText('Intersection...')
                                self._draw.binaryAND(rois)
                                self._updateROIDisplay()
                                wait.close()
                                self._logger.info('ROI {}'.format(name))
                            else: messageBox(self, 'ROI Intersection', 'Less than two ROI checked.')
                    else:
                        messageBox(self,
                                   'ROI intersection',
                                   text='Maximum number of ROIs reached.\n'
                                        'Close a ROI to add a new one.',
                                   icon=QMessageBox.Information)

    def symmetricDifference(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw.hasROI():
                if self._collection.count() > 1:
                    if self._list.count() < self._list.getMaxCount():
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'SymmDiff {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait()
                                wait.open()
                                wait.setInformationText('Symmetric difference...')
                                self._draw.binaryXOR(rois)
                                self._updateROIDisplay()
                                wait.close()
                                self._logger.info('ROI {}'.format(name))
                            else: messageBox(self, 'ROI Symmetric difference', 'Less than two ROI checked.')
                    else:
                        messageBox(self,
                                   'ROI symmetric difference',
                                   text='Maximum number of ROIs reached.\n'
                                        'Close a ROI to add a new one.',
                                   icon=QMessageBox.Information)

    def difference(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw.hasROI():
                if self._collection.count() > 1:
                    if self._list.count() < self._list.getMaxCount():
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            # current selected ROI, inserted first in list
                            # diffrence = first - others
                            rois.insert(0, self._draw.getROI())
                            n = len(rois)
                            if n > 0:
                                name = '{} Diff'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait()
                                wait.open()
                                wait.setInformationText('Difference...')
                                self._draw.binaryNAND(rois)
                                self._updateROIDisplay()
                                wait.close()
                                self._logger.info('ROI {}'.format(name))
                            else: messageBox(self, 'ROI Difference', 'No ROI checked.')
                    else:
                        messageBox(self,
                                   'ROI difference',
                                   text='Maximum number of ROIs reached.\n'
                                        'Close a ROI to add a new one.',
                                   icon=QMessageBox.Information)

    def clear(self):
        self._list.removeAll()

    # < Revision 20/02/2025
    # add setEnabled method
    def setEnabled(self, v: bool) -> None:
        super().setEnabled(v)
        self._list.setEnabled(v)
    # Revision 20/02/2025 >

    # Method aliases

    getROICollection = TabWidget.getCollection
    hasROICollection = TabWidget.hasCollection


class TabROIToolsWidget(TabWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display ROIToolsWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabROIToolsWidget

    Last revision: 08/03/2025
    """

    # Special method

    """
    Private attributes
    
    _draw               SisypheROIDraw
    _threshold          ThresholdViewWidget, widget to select threshold value
    __contourdialog     DialogSettings, active contour settings dialog
    _athreshold         QWidgetAction, QAction of _threshold widget
    _menuThreshold      QMenu, displays QWidgetAction _athreshold
    _statistics         DialogROIStatistics, dialog box to display ROI statistics
    _btn                dict[str, QAction], buttons
    _btngroup           QButtonGroup, group of mutual exclusive buttons
    _brushtype          LabeledComboBox
    _brushsize          LabeledSlider
    _fill               QCheckBox, autofill holes
    _structsize         LabeledSlider, structuring element size
    _structtype         LabeledComboBox, structuring element shape
    _move               LabeledSpinBox, ROI displacement, in voxels, after move tools clicking
    _extent             LabeledSpinBox, Blob extent used as threshold to remove blobs
    _thick              LabeledDoubleSpinBox, value in mm used by expand/shrink tools
    _algo               LabeledComboBox, algorithm used for object/background segmentation tools
    _confidence         LabeledDoubleSpinBox, value used by confidence connected segmentation tools
    _menu2DRegion       QMenu, 2D region growing algorithm menu
    _menu2DBlobRegion   QMenu, 2D region growing algorithm menu
    _menu3DRegion       QMenu, 3D region growing algorithm menu
    _menu2DBlobRegion   QMenu, 3D region growing algorithm menu
    _menu3DHoles        QMenu, fill holes menu
    """

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._draw = None
        self._threshold = ThresholdViewWidget(None, size=384, parent=self)
        self._threshold.setThresholdFlagToTwo()
        self._threshold.setThresholdFlagButtonsVisibility(False)
        self._threshold.setAutoButtonVisibility(True)
        self._athreshold = QWidgetAction(self)
        self._athreshold.setDefaultWidget(self._threshold)
        self._statistics = None
        self._btn = dict()
        self._btngroup = QButtonGroup()
        self._btngroup.setExclusive(True)

        # < Revision 24/03/2025
        # active contour settings management
        self._contourdialog = DialogFunctionSetting('ActiveContour')
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._contourdialog, c)
        self._updateActiveContourParameters()
        # Revision 24/03/2025 >

        # Widgets

        self._brushtype = LabeledComboBox(title='Shape', fontsize=12)
        self._brushtype.addItem('Full disc')
        self._brushtype.addItem('Thresholded disc')
        self._brushtype.addItem('Full ball')
        self._brushtype.addItem('Thresholded ball')
        # Revision 20/03/2025
        # noinspection PyUnresolvedReferences
        self._brushtype.currentIndexChanged.connect(self._brushTypeChanged)
        self._brushtype.setToolTip('Brush shape and behavior.')

        # noinspection PyTypeChecker
        self._brushsize = LabeledSlider(Qt.Horizontal, title='Radius', fontsize=12)
        self._brushsize.setRange(1, 20)
        self._brushsize.setValue(10)
        # noinspection PyUnresolvedReferences
        self._brushsize.valueChanged.connect(self._brushSizeChanged)
        # noinspection PyUnresolvedReferences
        self._brushsize.sliderMoved.connect(self._brushSizeMoved)
        # noinspection PyUnresolvedReferences
        self._brushsize.sliderReleased.connect(self._brushSizeReleased)
        self._brushsize.setToolTip('Brush radius (voxel unit)')

        # ROI settings

        self._settings = SettingsWidget('ROI')
        self._settings.setIOButtonsVisibility(False)
        self._settings.setSettingsButtonText('Brush Settings')
        self._settings.settingsVisibilityOff()
        self._settings.setParameterVisibility('MaxCount', False)
        self._fill = self._settings.getParameterWidget('FillHoles')
        self._structsize = self._settings.getParameterWidget('StructSize')
        self._structtype = self._settings.getParameterWidget('StructShape')
        self._move = self._settings.getParameterWidget('MoveStep')
        self._extent = self._settings.getParameterWidget('BlobExtent')
        self._thick = self._settings.getParameterWidget('Thickness')
        self._algo = self._settings.getParameterWidget('Algo')
        self._confidence = self._settings.getParameterWidget('Confidence')
        self._iters = self._settings.getParameterWidget('ConfidenceIter')
        self._fill.stateChanged.connect(self._brushFillChanged)
        self._structsize.valueChanged.connect(self._structSizeChanged)
        self._structtype.currentIndexChanged.connect(self._structTypeChanged)
        self._move.valueChanged.connect(self._moveChanged)
        self._extent.valueChanged.connect(self._extentChanged)
        self._thick.valueChanged.connect(self._thicknessChanged)
        self._algo.currentIndexChanged.connect(self._algoChanged)
        self._confidence.valueChanged.connect(self._confidenceChanged)
        self._iters.valueChanged.connect(self._confidenceIterChanged)

        # Brush groupbox

        self._brushgroupbox = QGroupBox('Brush')
        self._initBrushGroupBox()

        # Slice groupbox

        self._slicegroupbox = QGroupBox('Slice tools')
        self._initSliceGroupBox()

        # Slice blob groupbox

        self._sliceblobgroupbox = QGroupBox('Slice blob tools')
        self._initSliceBlobGroupBox()

        # Volume groupbox

        self._volumegroupbox = QGroupBox('Volume tools')
        self._initVolumeGroupBox()

        # Volume blob groupbox

        self._volumeblobgroupbox = QGroupBox('Volume blob tools')
        self._initVolumeBlobGroupBox()

        self._brushFillChanged(None)
        self._structSizeChanged(None)
        self._structTypeChanged(None)
        self._moveChanged(None)
        self._extentChanged(None)
        self._thicknessChanged(None)
        self._algoChanged(None)

        # Popup menu

        self._menuThreshold = QMenu(self)
        # noinspection PyTypeChecker
        self._menuThreshold.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menuThreshold.setWindowFlag(Qt.FramelessWindowHint, True)
        # self._menuThreshold.setAttribute(Qt.WA_TranslucentBackground, True)
        self._menuThreshold.addAction(self._athreshold)
        # noinspection PyUnresolvedReferences
        self._menuThreshold.aboutToHide.connect(self._brushThresholdChanged)
        self._btn['threshold'].setMenu(self._menuThreshold)

        self._menu2DRegion = QMenu()
        # noinspection PyTypeChecker
        self._menu2DRegion.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menu2DRegion.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu2DRegion.setAttribute(Qt.WA_TranslucentBackground, True)
        self._rg2DRegion = self._menu2DRegion.addAction('Region growing')
        self._rg2DRegion.setCheckable(True)
        self._rg2DRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._rg2DRegion.triggered.connect(self.slcRegionGrowing)
        self._cc2DRegion = self._menu2DRegion.addAction('Confidence connected')
        self._cc2DRegion.setCheckable(True)
        self._cc2DRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._cc2DRegion.triggered.connect(self.slcRegionConfidence)
        self._btn['2Dregion'].setMenu(self._menu2DRegion)
        self._btn['2Dregion'].clicked.connect(self._2DregionClicked)

        self._menu2DBlobRegion = QMenu()
        # noinspection PyTypeChecker
        self._menu2DBlobRegion.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menu2DBlobRegion.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu2DBlobRegion.setAttribute(Qt.WA_TranslucentBackground, True)
        self._rg2DBlobRegion = self._menu2DBlobRegion.addAction('Region growing')
        self._rg2DBlobRegion.setCheckable(True)
        self._rg2DBlobRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._rg2DBlobRegion.triggered.connect(self.slcBlobRegionGrowing)
        self._cc2DBlobRegion = self._menu2DBlobRegion.addAction('Confidence connected')
        self._cc2DBlobRegion.setCheckable(True)
        self._cc2DBlobRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._cc2DBlobRegion.triggered.connect(self.slcBlobRegionConfidence)
        self._btn['2Dblobregion'].setMenu(self._menu2DBlobRegion)
        self._btn['2Dblobregion'].clicked.connect(self._2DBlobregionClicked)

        self._menu3DRegion = QMenu()
        # noinspection PyTypeChecker
        self._menu3DRegion.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menu3DRegion.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu3DRegion.setAttribute(Qt.WA_TranslucentBackground, True)
        self._rg3DRegion = self._menu3DRegion.addAction('Region growing')
        self._rg3DRegion.setCheckable(True)
        self._rg3DRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._rg3DRegion.triggered.connect(self.voiRegionGrowing)
        self._cc3DRegion = self._menu3DRegion.addAction('Confidence connected')
        self._cc3DRegion.setCheckable(True)
        self._cc3DRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._cc3DRegion.triggered.connect(self.voiRegionConfidence)
        self._menu3DRegion.addSeparator()
        self._ac3DRegion = self._menu3DRegion.addAction('Active contour')
        self._ac3DRegion.setCheckable(True)
        self._ac3DRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._ac3DRegion.triggered.connect(self.voiActiveContour)
        action = self._menu3DRegion.addAction('Active contour settings...')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(self._dialogActiveContour)
        self._btn['3Dregion'].setMenu(self._menu3DRegion)
        self._btn['3Dregion'].clicked.connect(self._3DregionClicked)

        self._menu3DBlobRegion = QMenu()
        # noinspection PyTypeChecker
        self._menu3DBlobRegion.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menu3DBlobRegion.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu3DBlobRegion.setAttribute(Qt.WA_TranslucentBackground, True)
        self._rg3DBlobRegion = self._menu3DBlobRegion.addAction('Region growing')
        self._rg3DBlobRegion.setCheckable(True)
        self._rg3DBlobRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._rg3DBlobRegion.triggered.connect(self.voiBlobRegionGrowing)
        self._cc3DBlobRegion = self._menu3DBlobRegion.addAction('Confidence connected')
        self._cc3DBlobRegion.setCheckable(True)
        self._cc3DBlobRegion.setChecked(False)
        # noinspection PyUnresolvedReferences
        self._cc3DBlobRegion.triggered.connect(self.voiBlobRegionConfidence)
        self._btn['3Dblobregion'].setMenu(self._menu3DBlobRegion)
        self._btn['3Dblobregion'].clicked.connect(self._3DBlobregionClicked)

        self._menu3DHoles = QMenu()
        # noinspection PyTypeChecker
        self._menu3DHoles.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._menu3DHoles.setWindowFlag(Qt.FramelessWindowHint, True)
        self._menu3DHoles.setAttribute(Qt.WA_TranslucentBackground, True)
        action = self._menu3DHoles.addAction('3D fill holes')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(self.voi3DHoles)
        action = self._menu3DHoles.addAction('2D axial fill holes')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda: self.voi2DHoles(0))
        action = self._menu3DHoles.addAction('2D coronal fill holes')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda: self.voi2DHoles(1))
        action = self._menu3DHoles.addAction('2D sagittal fill holes')
        # noinspection PyUnresolvedReferences
        action.triggered.connect(lambda: self.voi2DHoles(2))
        self._btn['3Dholes'].setMenu(self._menu3DHoles)

        # Layout

        lyout = self.layout()
        # noinspection PyUnresolvedReferences
        lyout.addStretch()
        lyout.addWidget(self._brushgroupbox)
        lyout.addWidget(self._slicegroupbox)
        lyout.addWidget(self._sliceblobgroupbox)
        lyout.addWidget(self._volumegroupbox)
        lyout.addWidget(self._volumeblobgroupbox)
        lyout.addWidget(self._settings)
        # noinspection PyUnresolvedReferences
        lyout.addStretch()

    # Private methods

    def _initBrushGroupBox(self):
        self._btn['dummy'] = IconPushButton(size=TabWidget._VSIZE)
        self._btn['brush'] = IconPushButton('brush.png', size=TabWidget._VSIZE)
        self._btn['threshold'] = IconPushButton('threshold.png', size=TabWidget._VSIZE)
        self._btn['interpolate'] = IconPushButton('layer.png', size=TabWidget._VSIZE)
        self._btn['undo'] = IconPushButton('undo.png', size=TabWidget._VSIZE)
        self._btn['redo'] = IconPushButton('redo.png', size=TabWidget._VSIZE)

        self._btngroup.addButton(self._btn['dummy'])
        self._btngroup.addButton(self._btn['brush'])
        self._btn['dummy'].setCheckable(True)
        self._btn['brush'].setCheckable(True)

        self._btn['brush'].setToolTip('Brush')
        self._btn['threshold'].setToolTip('Set voxel value threshold for all thresholding tools')
        self._btn['interpolate'].setToolTip('Interpolation between first\nand last displayed slice')
        self._btn['undo'].setToolTip('Undo')
        self._btn['redo'].setToolTip('Redo')

        self._btn['brush'].clicked.connect(self.brush)
        self._btn['interpolate'].pressed.connect(self.interpolate)
        self._btn['undo'].pressed.connect(self.undo)
        self._btn['redo'].pressed.connect(self.redo)

        vlyout = QVBoxLayout()
        vlyout.setContentsMargins(0, 0, 0, 10)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._brushtype)
        lyout.addWidget(self._brushsize)
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['brush'])
        lyout.addWidget(self._btn['threshold'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['interpolate'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['undo'])
        lyout.addWidget(self._btn['redo'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        self._brushgroupbox.setLayout(vlyout)

    def _initSliceGroupBox(self):
        self._btn['2Ddilate'] = IconPushButton('dilate.png', size=TabWidget._VSIZE)
        self._btn['2Derode'] = IconPushButton('erode.png', size=TabWidget._VSIZE)
        self._btn['2Dopen'] = IconPushButton('morphoopen.png', size=TabWidget._VSIZE)
        self._btn['2Dclose'] = IconPushButton('morphoclose.png', size=TabWidget._VSIZE)
        self._btn['2Dinvert'] = IconPushButton('invert.png', size=TabWidget._VSIZE)
        self._btn['2Dholes'] = IconPushButton('bucket.png', size=TabWidget._VSIZE)
        self._btn['2Dfill'] = IconPushButton('fill.png', size=TabWidget._VSIZE)
        self._btn['2Dobject'] = IconPushButton('head.png', size=TabWidget._VSIZE)
        self._btn['2Dback'] = IconPushButton('ihead.png', size=TabWidget._VSIZE)
        self._btn['2Dthreshold'] = IconPushButton('threshold2.png', size=TabWidget._VSIZE)
        self._btn['2Dregion'] = IconPushButton('magic.png', size=TabWidget._VSIZE)
        self._btn['2Dcopy'] = IconPushButton('copy.png', size=TabWidget._VSIZE)
        self._btn['2Dcut'] = IconPushButton('cut.png', size=TabWidget._VSIZE)
        self._btn['2Dpaste'] = IconPushButton('paste.png', size=TabWidget._VSIZE)
        self._btn['2Dclear'] = IconPushButton('cross.png', size=TabWidget._VSIZE)
        self._btn['2Dhflip'] = IconPushButton('flipx.png', size=TabWidget._VSIZE)
        self._btn['2Dvflip'] = IconPushButton('flipy.png', size=TabWidget._VSIZE)
        self._btn['2Dup'] = IconPushButton('up.png', size=TabWidget._VSIZE)
        self._btn['2Ddown'] = IconPushButton('down.png', size=TabWidget._VSIZE)
        self._btn['2Dleft'] = IconPushButton('left.png', size=TabWidget._VSIZE)
        self._btn['2Dright'] = IconPushButton('right.png', size=TabWidget._VSIZE)

        self._btngroup.addButton(self._btn['2Dregion'])
        self._btn['2Dregion'].setCheckable(True)
        self._btngroup.addButton(self._btn['2Dfill'])
        self._btn['2Dfill'].setCheckable(True)

        self._btn['2Ddilate'].setToolTip('Morphology dilate in current slice')
        self._btn['2Derode'].setToolTip('Morphology erode in current slice')
        self._btn['2Dopen'].setToolTip('Morphology opening in current slice')
        self._btn['2Dclose'].setToolTip('Morphology closing in current slice')
        self._btn['2Dinvert'].setToolTip('Invert current slice')
        self._btn['2Dholes'].setToolTip('Fill holes in current slice')
        self._btn['2Dfill'].setToolTip('Flood fill in current slice')
        self._btn['2Dobject'].setToolTip('Object segmentation in current slice')
        self._btn['2Dback'].setToolTip('Background segmentation in current slice')
        self._btn['2Dthreshold'].setToolTip('Thresholding current slice')
        self._btn['2Dregion'].setToolTip('Region segmentation in current slice')
        self._btn['2Dcopy'].setToolTip('Copy current slice')
        self._btn['2Dcut'].setToolTip('Cut current slice')
        self._btn['2Dpaste'].setToolTip('Paste current slice')
        self._btn['2Dclear'].setToolTip('Clear current slice')
        self._btn['2Dhflip'].setToolTip('Horizontal flip current slice')
        self._btn['2Dvflip'].setToolTip('Vertical flip current slice')
        self._btn['2Dup'].setToolTip('Move up current slice and orientation')
        self._btn['2Ddown'].setToolTip('Move down current slice and orientation')
        self._btn['2Dleft'].setToolTip('Move left current slice and orientation')
        self._btn['2Dright'].setToolTip('Move right current slice and orientation')

        self._btn['2Ddilate'].pressed.connect(self.slcDilate)
        self._btn['2Derode'].pressed.connect(self.slcErode)
        self._btn['2Dopen'].pressed.connect(self.slcOpening)
        self._btn['2Dclose'].pressed.connect(self.slcClosing)
        self._btn['2Dinvert'].pressed.connect(self.slcInvert)
        self._btn['2Dholes'].pressed.connect(self.slcHoles)
        self._btn['2Dfill'].pressed.connect(self.slcFill)
        self._btn['2Dobject'].pressed.connect(self.slcObject)
        self._btn['2Dback'].pressed.connect(self.slcBack)
        self._btn['2Dthreshold'].pressed.connect(self.slcThresholding)
        self._btn['2Dcopy'].pressed.connect(self.slcCopy)
        self._btn['2Dcut'].pressed.connect(self.slcCut)
        self._btn['2Dpaste'].pressed.connect(self.slcPaste)
        self._btn['2Dclear'].pressed.connect(self.slcClear)
        self._btn['2Dhflip'].pressed.connect(self.slcHFlip)
        self._btn['2Dvflip'].pressed.connect(self.slcVFlip)
        self._btn['2Dup'].pressed.connect(self.slcUp)
        self._btn['2Ddown'].pressed.connect(self.slcDown)
        self._btn['2Dleft'].pressed.connect(self.slcLeft)
        self._btn['2Dright'].pressed.connect(self.slcRight)

        vlyout = QVBoxLayout()
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['2Ddilate'])
        lyout.addWidget(self._btn['2Derode'])
        lyout.addWidget(self._btn['2Dopen'])
        lyout.addWidget(self._btn['2Dclose'])
        lyout.addWidget(self._btn['2Dinvert'])
        lyout.addWidget(self._btn['2Dholes'])
        lyout.addWidget(self._btn['2Dfill'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['2Dcopy'])
        lyout.addWidget(self._btn['2Dcut'])
        lyout.addWidget(self._btn['2Dpaste'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['2Dobject'])
        lyout.addWidget(self._btn['2Dback'])
        lyout.addWidget(self._btn['2Dthreshold'])
        lyout.addWidget(self._btn['2Dregion'])
        lyout.addWidget(self._btn['2Dclear'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['2Dhflip'])
        lyout.addWidget(self._btn['2Dvflip'])
        # lyout.addWidget(self._move)
        lyout.addWidget(self._btn['2Dup'])
        lyout.addWidget(self._btn['2Ddown'])
        lyout.addWidget(self._btn['2Dleft'])
        lyout.addWidget(self._btn['2Dright'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        self._slicegroupbox.setLayout(vlyout)

    def _initSliceBlobGroupBox(self):
        self._btn['2Dblobdilate'] = IconPushButton('dilate.png', size=TabWidget._VSIZE)
        self._btn['2Dbloberode'] = IconPushButton('erode.png', size=TabWidget._VSIZE)
        self._btn['2Dblobopen'] = IconPushButton('morphoopen.png', size=TabWidget._VSIZE)
        self._btn['2Dblobclose'] = IconPushButton('morphoclose.png', size=TabWidget._VSIZE)
        self._btn['2Dblobkeep'] = IconPushButton('select-keep.png', size=TabWidget._VSIZE)
        self._btn['2Dblobremove'] = IconPushButton('select-remove.png', size=TabWidget._VSIZE)
        self._btn['2Dblobextent'] = IconPushButton('extent.png', size=TabWidget._VSIZE)
        self._btn['2Dblobcopy'] = IconPushButton('copy.png', size=TabWidget._VSIZE)
        self._btn['2Dblobcut'] = IconPushButton('cut.png', size=TabWidget._VSIZE)
        self._btn['2Dblobpaste'] = IconPushButton('paste.png', size=TabWidget._VSIZE)
        self._btn['2Dblobthreshold'] = IconPushButton('threshold2.png', size=TabWidget._VSIZE)
        self._btn['2Dblobregion'] = IconPushButton('magic.png', size=TabWidget._VSIZE)

        self._btngroup.addButton(self._btn['2Dblobdilate'])
        self._btngroup.addButton(self._btn['2Dbloberode'])
        self._btngroup.addButton(self._btn['2Dblobopen'])
        self._btngroup.addButton(self._btn['2Dblobclose'])
        self._btngroup.addButton(self._btn['2Dblobkeep'])
        self._btngroup.addButton(self._btn['2Dblobremove'])
        self._btngroup.addButton(self._btn['2Dblobcopy'])
        self._btngroup.addButton(self._btn['2Dblobcut'])
        self._btngroup.addButton(self._btn['2Dblobpaste'])
        self._btngroup.addButton(self._btn['2Dblobthreshold'])
        self._btngroup.addButton(self._btn['2Dblobregion'])
        self._btn['2Dblobdilate'].setCheckable(True)
        self._btn['2Dbloberode'].setCheckable(True)
        self._btn['2Dblobopen'].setCheckable(True)
        self._btn['2Dblobclose'].setCheckable(True)
        self._btn['2Dblobkeep'].setCheckable(True)
        self._btn['2Dblobremove'].setCheckable(True)
        self._btn['2Dblobcopy'].setCheckable(True)
        self._btn['2Dblobcut'].setCheckable(True)
        self._btn['2Dblobpaste'].setCheckable(True)
        self._btn['2Dblobthreshold'].setCheckable(True)
        self._btn['2Dblobregion'].setCheckable(True)

        self._btn['2Dblobdilate'].setToolTip('Blob morphology dilate in current slice')
        self._btn['2Dbloberode'].setToolTip('Blob morphology erode in current slice')
        self._btn['2Dblobopen'].setToolTip('Blob morphology opening in current slice')
        self._btn['2Dblobclose'].setToolTip('Blob morphology closing in current slice')
        self._btn['2Dblobkeep'].setToolTip('Keep selected blob in current slice')
        self._btn['2Dblobremove'].setToolTip('Remove selected blob in current slice')
        self._btn['2Dblobextent'].setToolTip('Remove blob with number of voxels smaller\n'
                                             'than threshold in current slice')
        self._btn['2Dblobcopy'].setToolTip('Copy selected blob in current slice')
        self._btn['2Dblobcut'].setToolTip('Cut selected blob in current slice')
        self._btn['2Dblobpaste'].setToolTip('Paste blob in current slice')
        self._btn['2Dblobthreshold'].setToolTip('Blob thresholding in current slice')
        self._btn['2Dblobregion'].setToolTip('Region segmentation in blob, current slice')

        self._btn['2Dblobdilate'].pressed.connect(self.slcBlobDilate)
        self._btn['2Dbloberode'].pressed.connect(self.slcBlobErode)
        self._btn['2Dblobopen'].pressed.connect(self.slcBlobOpening)
        self._btn['2Dblobclose'].pressed.connect(self.slcBlobClosing)
        self._btn['2Dblobkeep'].pressed.connect(self.slcBlobKeep)
        self._btn['2Dblobremove'].pressed.connect(self.slcBlobRemove)
        self._btn['2Dblobextent'].pressed.connect(self.slcFilterExtent)
        self._btn['2Dblobcopy'].pressed.connect(self.slcBlobCopy)
        self._btn['2Dblobcut'].pressed.connect(self.slcBlobCut)
        self._btn['2Dblobpaste'].pressed.connect(self.slcBlobPaste)
        self._btn['2Dblobthreshold'].pressed.connect(self.slcBlobThresholding)

        vlyout = QVBoxLayout()
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['2Dblobdilate'])
        lyout.addWidget(self._btn['2Dbloberode'])
        lyout.addWidget(self._btn['2Dblobopen'])
        lyout.addWidget(self._btn['2Dblobclose'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['2Dblobcopy'])
        lyout.addWidget(self._btn['2Dblobcut'])
        lyout.addWidget(self._btn['2Dblobpaste'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['2Dblobkeep'])
        lyout.addWidget(self._btn['2Dblobremove'])
        lyout.addWidget(self._btn['2Dblobextent'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['2Dblobthreshold'])
        lyout.addWidget(self._btn['2Dblobregion'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        self._sliceblobgroupbox.setLayout(vlyout)

    def _initVolumeGroupBox(self):
        self._btn['3Ddilate'] = IconPushButton('dilate.png', size=TabWidget._VSIZE)
        self._btn['3Derode'] = IconPushButton('erode.png', size=TabWidget._VSIZE)
        self._btn['3Dopen'] = IconPushButton('morphoopen.png', size=TabWidget._VSIZE)
        self._btn['3Dclose'] = IconPushButton('morphoclose.png', size=TabWidget._VSIZE)
        self._btn['3Dinvert'] = IconPushButton('invert.png', size=TabWidget._VSIZE)
        self._btn['3Dholes'] = IconPushButton('bucket.png', size=TabWidget._VSIZE)
        self._btn['3Dfill'] = IconPushButton('fill.png', size=TabWidget._VSIZE)
        self._btn['3Dexpand'] = IconPushButton('expand2.png', size=TabWidget._VSIZE)
        self._btn['3Dshrink'] = IconPushButton('shrink2.png', size=TabWidget._VSIZE)
        self._btn['3Dobject'] = IconPushButton('head.png', size=TabWidget._VSIZE)
        self._btn['3Dback'] = IconPushButton('ihead.png', size=TabWidget._VSIZE)
        self._btn['3Dthreshold'] = IconPushButton('threshold2.png', size=TabWidget._VSIZE)
        self._btn['3Dregion'] = IconPushButton('magic.png', size=TabWidget._VSIZE)
        self._btn['3Dclear'] = IconPushButton('cross.png', size=TabWidget._VSIZE)
        self._btn['3Dhflip'] = IconPushButton('flipx.png', size=TabWidget._VSIZE)
        self._btn['3Dvflip'] = IconPushButton('flipy.png', size=TabWidget._VSIZE)
        self._btn['3Dup'] = IconPushButton('up.png', size=TabWidget._VSIZE)
        self._btn['3Ddown'] = IconPushButton('down.png', size=TabWidget._VSIZE)
        self._btn['3Dleft'] = IconPushButton('left.png', size=TabWidget._VSIZE)
        self._btn['3Dright'] = IconPushButton('right.png', size=TabWidget._VSIZE)
        self._btn['stats'] = IconPushButton('statistics.png', size=TabWidget._VSIZE)

        self._btngroup.addButton(self._btn['3Dregion'])
        self._btn['3Dregion'].setCheckable(True)
        self._btngroup.addButton(self._btn['3Dfill'])
        self._btn['3Dfill'].setCheckable(True)

        self._btn['3Ddilate'].setToolTip('Morphology dilate')
        self._btn['3Derode'].setToolTip('Morphology erode')
        self._btn['3Dopen'].setToolTip('Morphology opening')
        self._btn['3Dclose'].setToolTip('Morphology closing')
        self._btn['3Dinvert'].setToolTip('Invert')
        self._btn['3Dholes'].setToolTip('Fill holes')
        self._btn['3Dfill'].setToolTip('Flood fill')
        self._btn['3Dexpand'].setToolTip('Expand with an isotropic margin in mm')
        self._btn['3Dshrink'].setToolTip('Shrink with an isotropic margin in mm')
        self._btn['3Dobject'].setToolTip('Object segmentation')
        self._btn['3Dback'].setToolTip('Background segmentation')
        self._btn['3Dthreshold'].setToolTip('Thresholding')
        self._btn['3Dregion'].setToolTip('Region segmentation')
        self._btn['3Dclear'].setToolTip('Clear')
        self._btn['3Dhflip'].setToolTip('Horizontal flip in current orientation')
        self._btn['3Dvflip'].setToolTip('Vertical flip in current orientation')
        self._btn['3Dup'].setToolTip('Move up in current orientation')
        self._btn['3Ddown'].setToolTip('Move down in current orientation')
        self._btn['3Dleft'].setToolTip('Move left in current orientation')
        self._btn['3Dright'].setToolTip('Move right in current orientation')
        self._btn['stats'].setToolTip('Signal and shape statistics')

        self._btn['3Ddilate'].pressed.connect(self.voiDilate)
        self._btn['3Derode'].pressed.connect(self.voiErode)
        self._btn['3Dopen'].pressed.connect(self.voiOpening)
        self._btn['3Dclose'].pressed.connect(self.voiClosing)
        self._btn['3Dinvert'].pressed.connect(self.voiInvert)
        self._btn['3Dholes'].pressed.connect(self.voi3DHoles)
        self._btn['3Dfill'].pressed.connect(self.voiFill)
        self._btn['3Dexpand'].pressed.connect(self.voiEuclideanExpand)
        self._btn['3Dshrink'].pressed.connect(self.voiEuclideanShrink)
        self._btn['3Dobject'].pressed.connect(self.voiObject)
        self._btn['3Dback'].pressed.connect(self.voiBack)
        self._btn['3Dthreshold'].pressed.connect(self.voiThresholding)
        self._btn['3Dclear'].pressed.connect(self.voiClear)
        self._btn['3Dhflip'].pressed.connect(self.voiHFlip)
        self._btn['3Dvflip'].pressed.connect(self.voiVFlip)
        self._btn['3Dup'].pressed.connect(self.voiUp)
        self._btn['3Ddown'].pressed.connect(self.voiDown)
        self._btn['3Dleft'].pressed.connect(self.voiLeft)
        self._btn['3Dright'].pressed.connect(self.voiRight)
        self._btn['stats'].pressed.connect(self.statistics)

        vlyout = QVBoxLayout()
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['3Ddilate'])
        lyout.addWidget(self._btn['3Derode'])
        lyout.addWidget(self._btn['3Dopen'])
        lyout.addWidget(self._btn['3Dclose'])
        lyout.addWidget(self._btn['3Dinvert'])
        lyout.addWidget(self._btn['3Dholes'])
        lyout.addWidget(self._btn['3Dfill'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['3Dexpand'])
        lyout.addWidget(self._btn['3Dshrink'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['3Dobject'])
        lyout.addWidget(self._btn['3Dback'])
        lyout.addWidget(self._btn['3Dthreshold'])
        lyout.addWidget(self._btn['3Dregion'])
        lyout.addWidget(self._btn['3Dclear'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['stats'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['3Dhflip'])
        lyout.addWidget(self._btn['3Dvflip'])
        lyout.addWidget(self._btn['3Dup'])
        lyout.addWidget(self._btn['3Ddown'])
        lyout.addWidget(self._btn['3Dleft'])
        lyout.addWidget(self._btn['3Dright'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        self._volumegroupbox.setLayout(vlyout)

    def _initVolumeBlobGroupBox(self):
        self._btn['3Dblobdilate'] = IconPushButton('dilate.png', size=TabWidget._VSIZE)
        self._btn['3Dbloberode'] = IconPushButton('erode.png', size=TabWidget._VSIZE)
        self._btn['3Dblobopen'] = IconPushButton('morphoopen.png', size=TabWidget._VSIZE)
        self._btn['3Dblobclose'] = IconPushButton('morphoclose.png', size=TabWidget._VSIZE)
        self._btn['3Dblobexpand'] = IconPushButton('expand2.png', size=TabWidget._VSIZE)
        self._btn['3Dblobshrink'] = IconPushButton('shrink2.png', size=TabWidget._VSIZE)
        self._btn['3Dblobkeep'] = IconPushButton('select-keep.png', size=TabWidget._VSIZE)
        self._btn['3Dblobremove'] = IconPushButton('select-remove.png', size=TabWidget._VSIZE)
        self._btn['3Dblobextent'] = IconPushButton('extent.png', size=TabWidget._VSIZE)
        self._btn['3Dblobcopy'] = IconPushButton('copy.png', size=TabWidget._VSIZE)
        self._btn['3Dblobcut'] = IconPushButton('cut.png', size=TabWidget._VSIZE)
        self._btn['3Dblobpaste'] = IconPushButton('paste.png', size=TabWidget._VSIZE)
        self._btn['3Dblobthreshold'] = IconPushButton('threshold2.png', size=TabWidget._VSIZE)
        self._btn['3Dblobregion'] = IconPushButton('magic.png', size=TabWidget._VSIZE)

        self._btngroup.addButton(self._btn['3Dblobdilate'])
        self._btngroup.addButton(self._btn['3Dbloberode'])
        self._btngroup.addButton(self._btn['3Dblobopen'])
        self._btngroup.addButton(self._btn['3Dblobclose'])
        self._btngroup.addButton(self._btn['3Dblobexpand'])
        self._btngroup.addButton(self._btn['3Dblobshrink'])
        self._btngroup.addButton(self._btn['3Dblobkeep'])
        self._btngroup.addButton(self._btn['3Dblobremove'])
        self._btngroup.addButton(self._btn['3Dblobcopy'])
        self._btngroup.addButton(self._btn['3Dblobcut'])
        self._btngroup.addButton(self._btn['3Dblobpaste'])
        self._btngroup.addButton(self._btn['3Dblobthreshold'])
        self._btngroup.addButton(self._btn['3Dblobregion'])
        self._btn['3Dblobdilate'].setCheckable(True)
        self._btn['3Dbloberode'].setCheckable(True)
        self._btn['3Dblobopen'].setCheckable(True)
        self._btn['3Dblobclose'].setCheckable(True)
        self._btn['3Dblobexpand'].setCheckable(True)
        self._btn['3Dblobshrink'].setCheckable(True)
        self._btn['3Dblobkeep'].setCheckable(True)
        self._btn['3Dblobremove'].setCheckable(True)
        self._btn['3Dblobcopy'].setCheckable(True)
        self._btn['3Dblobcut'].setCheckable(True)
        self._btn['3Dblobpaste'].setCheckable(True)
        self._btn['3Dblobthreshold'].setCheckable(True)
        self._btn['3Dblobregion'].setCheckable(True)

        self._btn['3Dblobdilate'].setToolTip('Blob morphology dilate')
        self._btn['3Dbloberode'].setToolTip('Blob morphology erode')
        self._btn['3Dblobopen'].setToolTip('Blob morphology opening')
        self._btn['3Dblobclose'].setToolTip('Blob morphology closing')
        self._btn['3Dblobexpand'].setToolTip('Expand blob with an isotropic margin in mm')
        self._btn['3Dblobshrink'].setToolTip('Shrink blob with an isotropic margin in mm')
        self._btn['3Dblobkeep'].setToolTip('Keep selected blob, remove others')
        self._btn['3Dblobremove'].setToolTip('Remove selected blob')
        self._btn['3Dblobextent'].setToolTip('Remove blob smaller than threshold')
        self._btn['3Dblobcopy'].setToolTip('Copy selected blob')
        self._btn['3Dblobcut'].setToolTip('Cut selected blob')
        self._btn['3Dblobpaste'].setToolTip('Paste selected blob')
        self._btn['3Dblobthreshold'].setToolTip('Thresholding in blob')
        self._btn['3Dblobregion'].setToolTip('Region segmentation in blob')

        self._btn['3Dblobdilate'].pressed.connect(self.voiBlobDilate)
        self._btn['3Dbloberode'].pressed.connect(self.voiBlobErode)
        self._btn['3Dblobopen'].pressed.connect(self.voiBlobOpening)
        self._btn['3Dblobclose'].pressed.connect(self.voiBlobClosing)
        self._btn['3Dblobexpand'].pressed.connect(self.voiBlobExpand)
        self._btn['3Dblobshrink'].pressed.connect(self.voiBlobShrink)
        self._btn['3Dblobkeep'].pressed.connect(self.voiBlobKeep)
        self._btn['3Dblobremove'].pressed.connect(self.voiBlobRemove)
        self._btn['3Dblobextent'].pressed.connect(self.voiFilterExtent)
        self._btn['3Dblobcopy'].pressed.connect(self.voiBlobCopy)
        self._btn['3Dblobcut'].pressed.connect(self.voiBlobCut)
        self._btn['3Dblobpaste'].pressed.connect(self.voiBlobPaste)
        self._btn['3Dblobthreshold'].pressed.connect(self.voiBlobThresholding)

        vlyout = QVBoxLayout()
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['3Dblobdilate'])
        lyout.addWidget(self._btn['3Dbloberode'])
        lyout.addWidget(self._btn['3Dblobopen'])
        lyout.addWidget(self._btn['3Dblobclose'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['3Dblobcopy'])
        lyout.addWidget(self._btn['3Dblobcut'])
        lyout.addWidget(self._btn['3Dblobpaste'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._btn['3Dblobexpand'])
        lyout.addWidget(self._btn['3Dblobshrink'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['3Dblobkeep'])
        lyout.addWidget(self._btn['3Dblobremove'])
        lyout.addWidget(self._btn['3Dblobextent'])
        lyout.addSpacing(10)
        lyout.addWidget(self._btn['3Dblobthreshold'])
        lyout.addWidget(self._btn['3Dblobregion'])
        lyout.addStretch()
        vlyout.addLayout(lyout)
        self._volumeblobgroupbox.setLayout(vlyout)

    def _updateROIDisplay(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.updateROIDisplay()

    def _brushThresholdChanged(self):
        if self._draw is not None:
            vmin = self._threshold.getMinThreshold()
            vmax = self._threshold.getMaxThreshold()
            self._draw.setThresholds(vmin, vmax)
            if vmax < -1.0 or vmax > 1.0:
                info = '\nLower threshold {:.1f}, upper threshold {:.1f}'.format(vmin, vmax)
            else: info = '\nLower threshold {}, upper threshold {}'.format(vmin, vmax)
            self._btn['threshold'].setToolTip('Set voxel value threshold for all thresholding tools' + info)
            self._btn['2Dthreshold'].setToolTip('Thresholding current slice' + info)
            self._btn['2Dblobthreshold'].setToolTip('Blob thresholding in current slice' + info)
            self._btn['3Dthreshold'].setToolTip('Thresholding' + info)
            self._btn['3Dblobthreshold'].setToolTip('Thresholding in blob' + info)

    # noinspection PyUnusedLocal
    def _brushSizeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._views.setBrushRadiusROI(self._brushsize.value())

    # noinspection PyUnusedLocal
    def _brushSizeMoved(self, v):
        if self._draw is not None and self.hasViewCollection():
            for widget in self._views:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setBrushVisibilityOn()

    def _brushSizeReleased(self):
        if self._draw is not None and self.hasViewCollection():
            for widget in self._views:
                if isinstance(widget, (IconBarMultiSliceGridViewWidget, IconBarSynchronisedGridViewWidget)):
                    sliceview = widget().getFirstSliceViewWidget()
                    if sliceview is not None: sliceview.setBrushVisibilityOff()

    # noinspection PyUnusedLocal
    def _brushTypeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setBrushType(self._brushtype.currentIndex())
            self._brushtype.setToolTip('Brush shape and behavior\n' + self._brushtype.currentText())

    # noinspection PyUnusedLocal
    def _brushFillChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._views.setFillHolesROIFlag(self._fill.isChecked())

    # noinspection PyUnusedLocal
    def _structSizeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setMorphologyRadius(self._structsize.value())
        info = '\nStructuring element size {}, shape {}'.format(self._structsize.value(),
                                                                 self._structtype.currentText())
        self._btn['2Ddilate'].setToolTip('Morphology dilate in current slice' + info)
        self._btn['2Derode'].setToolTip('Morphology erode in current slice' + info)
        self._btn['2Dopen'].setToolTip('Morphology opening in current slice' + info)
        self._btn['2Dclose'].setToolTip('Morphology closing in current slice' + info)
        self._btn['2Dblobdilate'].setToolTip('Blob morphology dilate in current slice' + info)
        self._btn['2Dbloberode'].setToolTip('Blob morphology erode in current slice' + info)
        self._btn['2Dblobopen'].setToolTip('Blob morphology opening in current slice' + info)
        self._btn['2Dblobclose'].setToolTip('Blob morphology closing in current slice' + info)
        self._btn['3Ddilate'].setToolTip('Morphology dilate' + info)
        self._btn['3Derode'].setToolTip('Morphology erode' + info)
        self._btn['3Dopen'].setToolTip('Morphology opening' + info)
        self._btn['3Dclose'].setToolTip('Morphology closing' + info)
        self._btn['3Dblobdilate'].setToolTip('Blob morphology dilate' + info)
        self._btn['3Dbloberode'].setToolTip('Blob morphology erode' + info)
        self._btn['3Dblobopen'].setToolTip('Blob morphology opening' + info)
        self._btn['3Dblobclose'].setToolTip('Blob morphology closing' + info)

    # noinspection PyUnusedLocal
    def _structTypeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            struct = ('ball', 'box', 'cross', 'annulus')
            index = self._structtype.currentIndex()
            self._draw.setStructElement(struct[index])
        info = '\nStructuring element size {}, shape {}'.format(self._structsize.value(),
                                                                 self._structtype.currentText())
        self._btn['2Ddilate'].setToolTip('Morphology dilate in current slice' + info)
        self._btn['2Derode'].setToolTip('Morphology erode in current slice' + info)
        self._btn['2Dopen'].setToolTip('Morphology opening in current slice' + info)
        self._btn['2Dclose'].setToolTip('Morphology closing in current slice' + info)
        self._btn['2Dblobdilate'].setToolTip('Blob morphology dilate in current slice' + info)
        self._btn['2Dbloberode'].setToolTip('Blob morphology erode in current slice' + info)
        self._btn['2Dblobopen'].setToolTip('Blob morphology opening in current slice' + info)
        self._btn['2Dblobclose'].setToolTip('Blob morphology closing in current slice' + info)
        self._btn['3Ddilate'].setToolTip('Morphology dilate' + info)
        self._btn['3Derode'].setToolTip('Morphology erode' + info)
        self._btn['3Dopen'].setToolTip('Morphology opening' + info)
        self._btn['3Dclose'].setToolTip('Morphology closing' + info)
        self._btn['3Dblobdilate'].setToolTip('Blob morphology dilate' + info)
        self._btn['3Dbloberode'].setToolTip('Blob morphology erode' + info)
        self._btn['3Dblobopen'].setToolTip('Blob morphology opening' + info)
        self._btn['3Dblobclose'].setToolTip('Blob morphology closing' + info)

    # noinspection PyUnusedLocal
    def _moveChanged(self, v):
        info = '\n{} mm step'.format(self._move.value())
        self._btn['2Dup'].setToolTip('Move up current slice and orientation' + info)
        self._btn['2Ddown'].setToolTip('Move down current slice and orientation' + info)
        self._btn['2Dleft'].setToolTip('Move left current slice and orientation' + info)
        self._btn['2Dright'].setToolTip('Move right current slice and orientation' + info)
        self._btn['3Dup'].setToolTip('Move up in current orientation' + info)
        self._btn['3Ddown'].setToolTip('Move down in current orientation' + info)
        self._btn['3Dleft'].setToolTip('Move left in current orientation' + info)
        self._btn['3Dright'].setToolTip('Move right in current orientation' + info)

    # noinspection PyUnusedLocal
    def _extentChanged(self, v):
        info = '\nBlob size threshold {} voxels'.format(self._extent.value())
        self._btn['2Dblobextent'].setToolTip('Remove blob with number of voxels smaller\n'
                                             'than threshold in current slice' + info)
        self._btn['3Dblobextent'].setToolTip('Remove blob with number of voxels smaller then threshold' + info)

    # noinspection PyUnusedLocal
    def _thicknessChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setThickness(self._thick.value())
        info = '\nExpand/shrink thickness {} mm'.format(self._thick.value())
        self._btn['3Dexpand'].setToolTip('Euclidean distance expand' + info)
        self._btn['3Dshrink'].setToolTip('Euclidean distance shrink' + info)
        self._btn['3Dblobexpand'].setToolTip('Euclidean distance blob expand' + info)
        self._btn['3Dblobshrink'].setToolTip('Euclidean distance blob shrink' + info)

    # noinspection PyUnusedLocal
    def _algoChanged(self, v):
        info = '\n{} algorithm'.format(self._algo.currentText())
        self._btn['2Dobject'].setToolTip('Object segmentation in current slice' + info)
        self._btn['2Dback'].setToolTip('Background segmentation in current slice' + info)
        self._btn['3Dobject'].setToolTip('Object segmentation' + info)
        self._btn['3Dback'].setToolTip('Background segmentation' + info)

    # noinspection PyUnusedLocal
    def _confidenceChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setConfidenceConnectedSigma(self._confidence.value())

    # noinspection PyUnusedLocal
    def _confidenceIterChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setConfidenceConnectedIter(self._iters.value())

    def _2DregionClicked(self):
        if not self._btn['2Dregion'].isChecked():
            self._rg2Dregion.setChecked(False)
            self._cc2Dregion.setChecked(False)

    def _3DregionClicked(self):
        if not self._btn['3Dregion'].isChecked():
            self._rg3Dregion.setChecked(False)
            self._cc3Dregion.setChecked(False)
            self._ac3Dregion.setChecked(False)

    def _2DBlobregionClicked(self):
        if not self._btn['2Dblobregion'].isChecked():
            self._rg2DBlobRegion.setChecked(False)
            self._cc2DBlobRegion.setChecked(False)

    def _3DBlobregionClicked(self):
        if not self._btn['3Dblobregion'].isChecked():
            self._rg3DBlobRegion.setChecked(False)
            self._cc3DBlobRegion.setChecked(False)

    # < Revision 24/03/2025
    # add _updateActiveContourParameters method
    def _updateActiveContourParameters(self):
        if self._draw is not None:
            w = self._contourdialog.getSettingsWidget()
            v = w.getParameterValue('Radius')
            if v is None: v = 2.0
            self._draw.setActiveContourSeedRadius(v)
            v = w.getParameterValue('Curvature')
            if v is None: v = 1.0
            self._draw.setActiveContourCurvatureWeight(v)
            v = w.getParameterValue('Advection')
            if v is None: v = 1.0
            self._draw.setActiveContourAdvectionWeight(v)
            v = w.getParameterValue('Propagation')
            if v is None: v = 1.0
            self._draw.setActiveContourPropagationWeight(v)
            v = w.getParameterValue('Iter')
            if v is None: v = 1000
            self._draw.setActiveContourNumberOfIterations(v)
            v = w.getParameterValue('RMS')
            if v is None: v = 0.01
            self._draw.setActiveContourConvergence(v)
            v = w.getParameterValue('Sigma')
            if v is None: v = 1.0
            self._draw.setActiveContourSigma(v)
            v = w.getParameterValue('Factor')
            if v is None: v = 3.0
            self._draw.setActiveContourFactor(v)
            v = w.getParameterValue('Algorithm')
            if v is None: v = 'geodesic'
            else: v = v[0].split(' ')[0].lower()
            self._draw.setActiveContourAlgorithm(v)
            if self.hasViewCollection():
                vol = self._views.getVolume()
                if vol is not None:
                    r1 = vol.getRange()
                    r1 = (round(r1[0], 1), round(r1[1], 1))
                    r2 = self._threshold.getThresholds()
                    r2 = (round(r2[0], 1), round(r2[1], 1))
                    if r1 == r2: self._draw.setActiveContourThresholds(None)
                    else: self._draw.setActiveContourThresholds(self._threshold.getThresholds())
    # Revision 24/03/2025 >

    # < Revision 24/03/2025
    # add _dialogActiveContour method
    def _dialogActiveContour(self):
        if self._contourdialog.exec() == QDialog.Accepted:
            self._updateActiveContourParameters()
    # Revision 24/03/2025 >

    # Public methods

    # < Revision 10/03/2025
    # fix vtkWin32OpenGLRenderWindow error: wglMakeCurrent failed in MakeCurrent()
    # finalize method must be called before destruction
    def finalize(self):
        self._menuThreshold.removeAction(self._athreshold)
        self._athreshold.releaseWidget(self._threshold)
        self._threshold.finalize()
    # Revision 10/03/2025 >

    def setIconSize(self, size=TabWidget._VSIZE):
        for k in self._btn:
            self._btn[k].setIconSize(QSize(size - 8, size - 8))
            self._btn[k].setFixedSize(size, size)

    def getIconSize(self):
        return self._btn[0].width()

    def setEnabled(self, v):
        super().setEnabled(v)
        if self._draw is not None and self.hasViewCollection():
            # Brush size
            self._brushsize.setValue(self._draw.getBrushRadius())
            # Brush type
            brush = ('solid', 'threshold', 'solid3', 'threshold3')
            index = brush.index(self._draw.getBrushType())
            self._brushtype.setCurrentIndex(index)
            # Structuring element size
            self._structsize.setValue(self._draw.getMorphologyRadius())
            # Structuring element type
            struct = ('ball', 'box', 'cross', 'annulus')
            index = struct.index(self._draw.getStructElement())
            self._structtype.setCurrentIndex(index)
            # Fill holes
            self._fill.setChecked(self._views.getFillHolesROIFlag())

    def setViewCollection(self, views):
        super().setViewCollection(views)
        self._collection = self._views.getROICollection()
        self._draw = self._views.getROIDraw()

    # < Revision 09/03/2025
    # add updateThresholdWidget method, called by setROIToolsEnabled mainWindow method
    def updateThresholdWidget(self):
        vol = self._views.getVolume()
        if vol is not None:
            if self._threshold.getVolume() is None: self._threshold.setVolume(vol)
            elif vol != self._threshold.getVolume(): self._threshold.setVolume(vol)
    # Revision 09/03/2025 >

    # Public tools methods

    def brush(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._views.getBrushFlag() > 0:
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()
                self._logger.info('ROI tools - Brush tool selected')
            else: self._views.setBrushROIFlag(self._brushtype.currentIndex())

    def interpolate(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                view = self._views['slices']
                if view is not None:
                    first = view().getFirstVisibleSliceIndex()
                    last = view().getLastVisibleSliceIndex()
                    if last > first:
                        orient = self._views.getCurrentOrientation()
                        self._draw.interpolateBetweenSlices(first, last, orient)
                        self._updateROIDisplay()
                        self._logger.info('ROI tools - Interpolate slices')

    def undo(self):
        if self._draw:
            self._draw.popUndoLIFO()
            self._updateROIDisplay()
            self._logger.info('ROI tools - Undo')

    def redo(self):
        if self._draw:
            self._draw.popRedoLIFO()
            self._updateROIDisplay()
            self._logger.info('ROI tools - Redo')

    # Slice ROI actions

    def slcDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceDilate(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Binary dilate slice {}'.format(index))

    def slcErode(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceErode(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Binnary erode slice {}'.format(index))

    def slcOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceOpening(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Binary opening slice {}'.format(index))

    def slcClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceClosing(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Binary closing slice {}'.format(index))

    def slcInvert(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.binaryNotSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Binary not slice {}'.format(index))

    def slcHoles(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.fillHolesSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Fill holes slice {}'.format(index))

    def slcFill(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DFillROIFlag()
            self._logger.info('ROI tools - Slice fill tool selected')

    def slcObject(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    algo = self._algo.currentText().lower()
                    algo = algo.replace(' ', '')
                    if algo == 'morphology': algo = 'mean'
                    self._draw.objectSegmentSlice(index, orient, algo)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Object segmentation slice {}'.format(index))

    def slcBack(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    algo = self._algo.currentText().lower()
                    algo = algo.replace(' ', '')
                    if algo == 'morphology': algo = 'mean'
                    self._draw.backgroundSegmentSlice(index, orient, algo)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Background segmentation slice {}'.format(index))

    def slcThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.thresholdingSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Thresholding slice {}'.format(index))

    def slcCopy(self):
        if self._draw is not None:
            index = self._views.getSelectedSliceIndex()
            if index is not None:
                orient = self._views.getCurrentOrientation()
                self._draw.copySlice(index, orient)
                self._updateROIDisplay()
                self._logger.info('ROI tools - Copy slice {}'.format(index))

    def slcCut(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.cutSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Cut slice {}'.format(index))

    def slcPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.pasteSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Paste slice {}'.format(index))

    def slcClear(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.clearSlice(index, orient)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Clear slice {}'.format(index))

    def slcHFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.flipSlice(index, orient, True, False)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Horizontal flip slice {}'.format(index))

    def slcVFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.flipSlice(index, orient, False, True)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Vertical flip slice {}'.format(index))

    def slcUp(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, 0, self._move.value())
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Move up slice {}'.format(index))

    def slcDown(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, 0, -self._move.value())
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Move down slice {}'.format(index))

    def slcLeft(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, self._move.value(), 0)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Move left slice {}'.format(index))

    def slcRight(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, -self._move.value(), 0)
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Move right slice {}'.format(index))

    def slcFilterExtent(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    if self._extent.value() == -1: self._draw.majorBlobSelectSlice(index, orient)
                    else: self._draw.blobFilterExtentSlice(index, orient, self._extent.value())
                    self._updateROIDisplay()
                    self._logger.info('ROI tools - Blob filter extent {} slice {}'.format(self._extent.value(), index))

    def slcRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._rg2DRegion.isChecked():
                self._btn['2Dregion'].setChecked(True)
                self._rg2DRegion.setChecked(True)
                self._cc2DRegion.setChecked(False)
                self._views.set2DRegionGrowingROIFlag()
                self._logger.info('ROI tools - Slice region growing tool selected')
            else:
                self._btn['2Dregion'].setChecked(False)
                self._rg2DRegion.setChecked(False)
                self._cc2DRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def slcRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._cc2DRegion.isChecked():
                self._btn['2Dregion'].setChecked(True)
                self._rg2DRegion.setChecked(False)
                self._cc2DRegion.setChecked(True)
                self._views.set2DRegionConfidenceROIFlag()
                self._logger.info('ROI tools - Slice region confidence tool selected')
            else:
                self._btn['2Dregion'].setChecked(False)
                self._rg2DRegion.setChecked(False)
                self._cc2DRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    # Slice blob actions

    def slcBlobDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobDilateROIFlag()
            self._logger.info('ROI tools - Slice blob dilate tool selected')

    def slcBlobErode(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobErodeROIFlag()
            self._logger.info('ROI tools - Slice blob erode tool selected')

    def slcBlobOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobOpenROIFlag()
            self._logger.info('ROI tools - Slice blob opening tool selected')

    def slcBlobClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCloseROIFlag()
            self._logger.info('ROI tools - Slice blob closing tool selected')

    def slcBlobCopy(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCopyROIFlag()
            self._logger.info('ROI tools - Slice blob copy tool selected')

    def slcBlobCut(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCutROIFlag()
            self._logger.info('ROI tools - Slice blob cut tool selected')

    def slcBlobPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobPasteROIFlag()
            self._logger.info('ROI tools - Slice blob paste tool selected')

    def slcBlobRemove(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobRemoveROIFlag()
            self._logger.info('ROI tools - Slice blob remove tool selected')

    def slcBlobKeep(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobKeepROIFlag()
            self._logger.info('ROI tools - Slice blob keep tool selected')

    def slcBlobThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobThresholdROIFlag()
            self._logger.info('ROI tools - Slice blob thresholding tool selected')

    def slcBlobRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._rg2DBlobRegion.isChecked():
                self._btn['2Dblobregion'].setChecked(True)
                self._rg2DBlobRegion.setChecked(True)
                self._cc2DBlobRegion.setChecked(False)
                self._views.set2DBlobRegionGrowingROIFlag()
                self._logger.info('ROI tools - Slice blob region growing tool selected')
            else:
                self._btn['2Dblobregion'].setChecked(False)
                self._rg2DBlobRegion.setChecked(False)
                self._cc2DBlobRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def slcBlobRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._cc2DBlobRegion.isChecked():
                self._btn['2Dblobregion'].setChecked(True)
                self._rg2DBlobRegion.setChecked(False)
                self._cc2DBlobRegion.setChecked(True)
                self._views.set2DBlobRegionConfidenceROIFlag()
                self._logger.info('ROI tools - Slice blob region confidence tool selected')
            else:
                self._btn['2Dblobregion'].setChecked(False)
                self._rg2DBlobRegion.setChecked(False)
                self._cc2DBlobRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    # Volume ROI actions

    def voiEuclideanExpand(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if self._thick.value() > 0.0:
                    wait = DialogWait()
                    wait.open()
                    wait.setInformationText('Euclidean expand...')
                    QApplication.processEvents()
                    self._draw.euclideanDilate(self._thick.value())
                    self._updateROIDisplay()
                    wait.close()
                    self._logger.info('ROI tools - Expand {}'.format(self._thick.value()))

    def voiEuclideanShrink(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if self._thick.value() > 0.0:
                    wait = DialogWait()
                    wait.open()
                    wait.setInformationText('Euclidean shrink...')
                    QApplication.processEvents()
                    self._draw.euclideanErode(self._thick.value())
                    self._updateROIDisplay()
                    wait.close()
                    self._logger.info('ROI tools - Shrink {}'.format(self._thick.value()))

    def voiDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Morphology dilate...')
                QApplication.processEvents()
                self._draw.morphoDilate()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Binary dilate')

    def voiErode(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Morphology erode...')
                QApplication.processEvents()
                self._draw.morphoErode()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Binary erode')

    def voiOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Morphology opening...')
                QApplication.processEvents()
                self._draw.morphoOpening()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Binary opening')

    def voiClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Morphology closing...')
                QApplication.processEvents()
                self._draw.morphoClosing()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Binary closing')

    def voiInvert(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                self._draw.binaryNOT()
                self._updateROIDisplay()
                self._logger.info('ROI tools - Binary not')

    def voi3DHoles(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Fill holes...')
                QApplication.processEvents()
                self._draw.fillHoles()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Fill holes')

    def voi2DHoles(self, dim):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if dim == 0: info = '2D axial fill holes...'
                elif dim == 1: info = '2D coronal fill holes...'
                else: info = '2D sagittal fill holes...'
                wait = DialogWait()
                wait.open()
                wait.setInformationText(info)
                QApplication.processEvents()
                self._draw.fillHolesAllSlices(dim)
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Fill holes (by slices)')

    def voiFill(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DFillROIFlag()
            self._logger.info('ROI tools - Fill tool selected')

    def voiClear(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                self._draw.clear()
                self._updateROIDisplay()
                self._logger.info('ROI tools - Clear')

    def voiObject(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Object segmentation...')
                QApplication.processEvents()
                algo = self._algo.currentText().lower()
                algo = algo.replace(' ', '')
                if algo == 'morphology': self._draw.maskSegment2('huang')
                else: self._draw.objectSegment(algo)
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Object segmentation')

    def voiBack(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Background segmentation...')
                QApplication.processEvents()
                algo = self._algo.currentText().lower()
                algo = algo.replace(' ', '')
                if algo == 'morphology': self._draw.notMaskSegment2('huang')
                else: self._draw.backgroundSegment(algo)
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Background segmentation')

    def voiThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Thresholding...')
                self._draw.thresholding()
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Thresholding')

    def voiHFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.flip(True, False, False)
                elif orient == 1: self._draw.flip(True, False, False)
                else: self._draw.flip(False, True, False)
                self._updateROIDisplay()
                self._logger.info('ROI tools - Horizontal flip')

    def voiVFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.flip(False, True, False)
                elif orient == 1: self._draw.flip(False, False, True)
                else: self._draw.flip(False, False, True)
                self._updateROIDisplay()
                self._logger.info('ROI tools - Vertical flip')

    def voiUp(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(0, self._move.value(), 0)
                elif orient == 1: self._draw.shift(0, 0, self._move.value())
                else: self._draw.shif(0, 0, self._move.value())
                self._updateROIDisplay()
                self._logger.info('ROI tools - Move up')

    def voiDown(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(0, -self._move.value(), 0)
                elif orient == 1: self._draw.shift(0, 0, -self._move.value())
                else: self._draw.shif(0, 0, -self._move.value())
                self._updateROIDisplay()
                self._logger.info('ROI tools - Move down')

    def voiLeft(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(self._move.value(), 0, 0)
                elif orient == 1: self._draw.shift(self._move.value(), 0, 0)
                else: self._draw.shif(0, self._move.value(), 0)
                self._updateROIDisplay()
                self._logger.info('ROI tools - Move left')

    def voiRight(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(-self._move.value(), 0, 0)
                elif orient == 1: self._draw.shift(-self._move.value(), 0, 0)
                else: self._draw.shif(0, -self._move.value(), 0)
                self._updateROIDisplay()
                self._logger.info('ROI tools - Move right')

    def voiFilterExtent(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait()
                wait.open()
                wait.setInformationText('Blob filter extent...')
                QApplication.processEvents()
                if self._extent.value() == -1: self._draw.majorBlobSelect()
                else: self._draw.blobFilterExtent(self._extent.value())
                self._updateROIDisplay()
                wait.close()
                self._logger.info('ROI tools - Blob filter extent {}'.format(self._extent.value()))

    def voiRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._rg3DRegion.isChecked():
                self._btn['3Dregion'].setChecked(True)
                self._rg3DRegion.setChecked(True)
                self._cc3DRegion.setChecked(False)
                self._ac3DRegion.setChecked(False)
                self._views.set3DRegionGrowingROIFlag()
                self._logger.info('ROI tools - Region growing tool selected')
            else:
                self._btn['3Dregion'].setChecked(False)
                self._rg3DRegion.setChecked(False)
                self._cc3DRegion.setChecked(False)
                self._ac3DRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def voiRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._cc3DRegion.isChecked():
                self._btn['3Dregion'].setChecked(True)
                self._rg3DRegion.setChecked(False)
                self._cc3DRegion.setChecked(True)
                self._ac3DRegion.setChecked(False)
                self._views.set3DRegionConfidenceROIFlag()
                self._logger.info('ROI tools - Region confidence tool selected')
            else:
                self._btn['3Dregion'].setChecked(False)
                self._rg3DRegion.setChecked(False)
                self._cc3DRegion.setChecked(False)
                self._ac3DRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def voiActiveContour(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._ac3DRegion.isChecked():
                self._btn['3Dregion'].setChecked(True)
                self._rg3DRegion.setChecked(False)
                self._cc3DRegion.setChecked(False)
                self._ac3DRegion.setChecked(True)
                self._views.setActiveContourROIFlag()
                self._logger.info('ROI tools - Active contour tool selected')
            else:
                self._btn['3Dregion'].setChecked(False)
                self._rg3DRegion.setChecked(False)
                self._cc3DRegion.setChecked(False)
                self._ac3DRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def statistics(self):
        if self.hasViewCollection() and self.hasCollection():
            wait = DialogWait()
            wait.open()
            wait.setInformationText('ROI statistics processing...')
            wait.progressVisibilityOff()
            QApplication.processEvents()
            self._statistics = DialogROIStatistics()
            if platform == 'win32':
                import pywinstyles
                cl = self.palette().base().color()
                c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
                pywinstyles.change_header_color(self._statistics, c)
            self._statistics.setVolume(self._views.getVolume())
            self._statistics.setROICollection(self._collection)
            wait.close()
            self._logger.info('Dialog exec [gui.dialogROIStatistics.DialogROIStatistics]')
            self._statistics.exec()
            # < Reviosn 02/05/2025
            self._statistics.close()
            self._statistics = None
            # Reviosn 02/05/2025 >

    # Volume blob actions

    def voiBlobDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobDilateROIFlag()
            self._logger.info('ROI tools - Blob binary dilate tool selected')

    def voiBlobErode(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobErodeROIFlag()
            self._logger.info('ROI tools - Blob binary erode tool selected')

    def voiBlobOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobOpenROIFlag()
            self._logger.info('ROI tools - Blob binary opening tool selected')

    def voiBlobClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCloseROIFlag()
            self._logger.info('ROI tools - Blob binary closing tool selected')

    def voiBlobCopy(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCopyROIFlag()
            self._logger.info('ROI tools - Blob copy tool selected')

    def voiBlobCut(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCutROIFlag()
            self._logger.info('ROI tools - Blob cut tool selected')

    def voiBlobPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobPasteROIFlag()
            self._logger.info('ROI tools - Blob paste tool selected')

    def voiBlobRemove(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobRemoveROIFlag()
            self._logger.info('ROI tools - Blob remove tool selected')

    def voiBlobKeep(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobKeepROIFlag()
            self._logger.info('ROI tools - Blob keep tool selected')

    def voiBlobExpand(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobExpandFlagOn(self._thick.value())
            self._logger.info('ROI tools - Blob expand tool selected')

    def voiBlobShrink(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobShrinkFlagOn(self._thick.value())
            self._logger.info('ROI tools - Blob shrink tool selected')

    def voiBlobThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobThresholdROIFlag()
            self._logger.info('ROI tools - Blob thresholding tool selected')

    def voiBlobRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._rg3DBlobRegion.isChecked():
                self._btn['3Dblobregion'].setChecked(True)
                self._rg3DBlobRegion.setChecked(True)
                self._cc3DBlobRegion.setChecked(False)
                self._views.set3DBlobRegionGrowingROIFlag()
                self._logger.info('ROI tools - Blob region growing tool selected')
            else:
                self._btn['3Dblobregion'].setChecked(False)
                self._rg3DBlobRegion.setChecked(False)
                self._cc3DBlobRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    def voiBlobRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._cc3DBlobRegion.isChecked():
                self._btn['3Dblobregion'].setChecked(True)
                self._rg3DBlobRegion.setChecked(False)
                self._cc3DBlobRegion.setChecked(True)
                self._views.set3DBlobRegionConfidenceROIFlag()
                self._logger.info('ROI tools - Blob region confidence tool selected')
            else:
                self._btn['3Dblobregion'].setChecked(False)
                self._rg3DBlobRegion.setChecked(False)
                self._cc3DBlobRegion.setChecked(False)
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()

    # Method aliases

    getROICollection = TabWidget.getCollection
    hasROICollection = TabWidget.hasCollection


class TabMeshListWidget(TabWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display MeshListWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabMeshListWidget

    Last revision: 02/11/2024
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._list = ListMeshAttributesWidget(views=views, parent=self)
        self._action = dict()

        # Widgets

        self._btfilt = IconPushButton('filter.png', size=TabWidget._VSIZE)
        self._dilate = IconPushButton('meshexpand.png', size=TabWidget._VSIZE)
        self._erode = IconPushButton('meshshrink.png', size=TabWidget._VSIZE)
        self._btunion = IconPushButton('union.png', size=TabWidget._VSIZE)
        self._btinter = IconPushButton('intersection.png', size=TabWidget._VSIZE)
        self._btdiff = IconPushButton('difference.png', size=TabWidget._VSIZE)
        self._btfeatures = IconPushButton('cubefeature.png', size=TabWidget._VSIZE)

        # noinspection PyUnresolvedReferences
        self._btfilt.clicked.connect(self.filters)
        # noinspection PyUnresolvedReferences
        self._btunion.clicked.connect(self.union)
        # noinspection PyUnresolvedReferences
        self._btinter.clicked.connect(self.intersection)
        # noinspection PyUnresolvedReferences
        self._btdiff.clicked.connect(self.difference)
        # noinspection PyUnresolvedReferences
        self._btfeatures.clicked.connect(self.features)
        self._btfilt.setToolTip('Checked mesh(es) filtering (clean, decimate, fill holes, smooth)')
        self._dilate.setToolTip('Checked mesh(es) isotropic dilatation')
        self._erode.setToolTip('Checked mesh(es) isotropic shrinking')
        self._btunion.setToolTip('Checked mesh(es) union')
        self._btinter.setToolTip('Checked mesh(es) intersection')
        self._btdiff.setToolTip('Selected mesh - Checked mesh(es)')
        self._btfeatures.setToolTip('Checked mesh(es) features')

        groupbox = QGroupBox('Mesh tools')
        grouplyout = QHBoxLayout()
        grouplyout.setContentsMargins(5, 10, 5, 10)
        grouplyout.setSpacing(5)
        grouplyout.addStretch()
        grouplyout.addWidget(self._btfilt)
        grouplyout.addWidget(self._dilate)
        grouplyout.addWidget(self._erode)
        grouplyout.addSpacing(20)
        grouplyout.addWidget(self._btunion)
        grouplyout.addWidget(self._btinter)
        grouplyout.addWidget(self._btdiff)
        grouplyout.addSpacing(20)
        grouplyout.addWidget(self._btfeatures)
        grouplyout.addStretch()
        groupbox.setLayout(grouplyout)

        self._settings = SettingsWidget('Mesh')
        self._settings.setIOButtonsVisibility(False)
        self._settings.setSettingsButtonText('Mesh Settings')
        self._settings.settingsVisibilityOff()
        self._settings.setParameterVisibility('MaxCount', False)

        self._popupDilate = QMenu()
        # noinspection PyTypeChecker
        self._popupDilate.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupDilate.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupDilate.setAttribute(Qt.WA_TranslucentBackground, True)
        self._dmm = LabeledDoubleSpinBox()
        self._dmm.setTitle('Dilate')
        self._dmm.setFontSize(10)
        self._dmm.setDecimals(1)
        self._dmm.setSuffix(' mm')
        self._dmm.setSingleStep(1.0)
        self._dmm.setValue(1.0)
        self._dmm.setRange(0.1, 100.0)
        self._action['dmm'] = QWidgetAction(self)
        self._action['dmm'].setDefaultWidget(self._dmm)
        self._popupDilate.addAction(self._action['dmm'])
        self._action['dilate'] = QAction('Dilate mesh')
        # noinspection PyUnresolvedReferences
        self._action['dilate'].triggered.connect(self.dilate)
        self._popupDilate.addAction(self._action['dilate'])
        self._dilate.setMenu(self._popupDilate)

        self._popupErode = QMenu()
        # noinspection PyTypeChecker
        self._popupErode.setWindowFlag(Qt.NoDropShadowWindowHint, True)
        # noinspection PyTypeChecker
        self._popupErode.setWindowFlag(Qt.FramelessWindowHint, True)
        self._popupErode.setAttribute(Qt.WA_TranslucentBackground, True)
        self._emm = LabeledDoubleSpinBox()
        self._emm.setTitle('Erode')
        self._emm.setFontSize(10)
        self._emm.setDecimals(1)
        self._emm.setSuffix(' mm')
        self._emm.setSingleStep(1.0)
        self._emm.setValue(1.0)
        self._emm.setRange(0.1, 100.0)
        self._action['emm'] = QWidgetAction(self)
        self._action['emm'].setDefaultWidget(self._emm)
        self._popupErode.addAction(self._action['emm'])
        self._action['erode'] = QAction('Erode mesh')
        # noinspection PyUnresolvedReferences
        self._action['erode'].triggered.connect(self.erode)
        self._popupErode.addAction(self._action['erode'])
        self._erode.setMenu(self._popupErode)

        # Layout

        lyout = self.layout()
        lyout.addWidget(self._list)
        lyout.addWidget(groupbox)
        lyout.addWidget(self._settings)

        margins1 = self.contentsMargins()
        margins2 = lyout.contentsMargins()
        self.setMinimumWidth(self._list.minimumWidth() +
                             margins1.left() + margins1.right() +
                             margins2.left() + margins2.right())

    # Public methods

    def setIconSize(self, size=TabWidget._VSIZE):
        self._btfilt.setIconSize(QSize(size - 8, size - 8))
        self._btfilt.setFixedSize(size, size)
        self._dilate.setIconSize(QSize(size - 8, size - 8))
        self._dilate.setFixedSize(size, size)
        self._erode.setIconSize(QSize(size - 8, size - 8))
        self._erode.setFixedSize(size, size)
        self._btunion.setIconSize(QSize(size - 8, size - 8))
        self._btunion.setFixedSize(size, size)
        self._btinter.setIconSize(QSize(size - 8, size - 8))
        self._btinter.setFixedSize(size, size)
        self._btdiff.setIconSize(QSize(size - 8, size - 8))
        self._btdiff.setFixedSize(size, size)
        self._btfeatures.setIconSize(QSize(size - 8, size - 8))
        self._btfeatures.setFixedSize(size, size)
        self._list.setIconSize(size)

    def getIconSize(self):
        return self._btfilt.width()

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection):
            self._list.setViewCollection(views)
            self._collection = views.getMeshCollection()
        else: self._collection = None

    # < Revision 02/11/2024
    # add setMaxCount method
    def setMaxCount(self, v):
        if self._list is not None:
            self._list.setMaxCount(v)
    # Revision 02/11/2024 >

    # < Revision 02/11/2024
    # add getMaxCount method
    def getMaxCount(self):
        if self._list is not None: return self._list.getMaxCount()
        else: raise AttributeError('_list attribute is None.')
    # Revision 02/11/2024 >

    def getMeshListWidget(self):
        return self._list

    def getSettingsWidget(self):
        return self._settings

    def clear(self):
        self._list.removeAll()

    def filters(self):
        self._list.filter()

    def dilate(self):
        v = self._dmm.value()
        self._list.dilate(v)

    def erode(self):
        v = self._emm.value()
        self._list.erode(v)

    def union(self):
        self._list.union()

    def intersection(self):
        self._list.intersection()

    def difference(self):
        self._list.difference()

    def features(self):
        self._list.features()

    # < Revision 20/02/2025
    # add setEnabled method
    def setEnabled(self, v: bool) -> None:
        super().setEnabled(v)
        self._list.setEnabled(v)
    # Revision 20/02/2025 >

    # Method aliases

    getMeshCollection = TabWidget.getCollection
    hasMeshCollection = TabWidget.hasCollection


class TabTargetListWidget(TabWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display TargetListWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabTargetWidget

    Last revision: 20/02/2025
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._list = ListToolAttributesWidget(views=views, parent=self)

        # Layout

        lyout = self.layout()
        lyout.addWidget(self._list)

        margins1 = self.contentsMargins()
        margins2 = lyout.contentsMargins()
        self.setMinimumWidth(self._list.minimumWidth() +
                             margins1.left() + margins1.right() +
                             margins2.left() + margins2.right())

    # Public methods

    def setIconSize(self, size=TabWidget._VSIZE):
        self._list.setIconSize(size)

    def getIconSize(self):
        return self._list.getIconSize()

    def setViewCollection(self, views):
        super().setViewCollection(views)

        if isinstance(views, IconBarViewWidgetCollection):
            self._list.setViewCollection(views)
            self._collection = views.getMeshCollection()
        else:
            self._collection = None

    # < Revision 02/11/2024
    # add setMaxCount method
    def setMaxCount(self, v):
        if self._list is not None:
            self._list.setMaxCount(v)
    # Revision 02/11/2024 >

    # < Revision 02/11/2024
    # add getMaxCount method
    def getMaxCount(self):
        if self._list is not None: return self._list.getMaxCount()
        else: raise AttributeError('_list attribute is None.')
    # Revision 02/11/2024 >

    def getToolListWidget(self):
        return self._list

    def clear(self):
        self._list.removeAll()

    # < Revision 20/02/2025
    # add setEnabled method
    def setEnabled(self, v: bool) -> None:
        super().setEnabled(v)
        self._list.setEnabled(v)
    # Revision 20/02/2025 >

    # Method aliases

    getToolCollection = TabWidget.getCollection
    hasToolCollection = TabWidget.hasCollection


class TabTrackingWidget(TabWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display TrackingWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabTrackingWidget

    Last revision: 20/02/2025
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._list = ListBundleAttributesWidget(views=views, parent=self)
        self._tractogram: SisypheStreamlines | None = None

        # Widgets

        self._file = FileSelectionWidget()
        self._file.setTextLabel('Whole brain tractogram')
        self._file.setClearButtonVisibility(True)
        self._file.filterExtension(SisypheStreamlines.getFileExt())
        self._file.FieldChanged.connect(lambda _, filename: self._loadTractogram(filename))
        self._file.FieldCleared.connect(self._clearTractogram)

        self._dissection = IconPushButton('tracking.png', size=TabWidget._VSIZE)
        self._atlas = IconPushButton('tracking-atlas.png', size=TabWidget._VSIZE)
        self._dissection.setToolTip('Streamlines selection from ROI')
        self._atlas.setToolTip('Streamlines selection from Atlas')
        # noinspection PyUnresolvedReferences
        self._dissection.clicked.connect(self.dissection)
        # noinspection PyUnresolvedReferences
        self._atlas.clicked.connect(self.atlas)

        self._roidialog = DialogStreamlinesROISelection()
        self._atlasdialog = DialogStreamlinesAtlasSelection()
        if platform == 'win32':
            import pywinstyles
            cl = self.palette().base().color()
            c = '#{:02x}{:02x}{:02x}'.format(cl.red(), cl.green(), cl.blue())
            pywinstyles.change_header_color(self._roidialog, c)
            pywinstyles.change_header_color(self._atlasdialog, c)
        btlayout = QHBoxLayout()
        btlayout.setContentsMargins(5, 10, 5, 10)
        btlayout.setSpacing(5)
        # btlayout.addStretch()
        btlayout.addWidget(self._file)
        btlayout.addWidget(self._dissection)
        btlayout.addWidget(self._atlas)
        # btlayout.addStretch()
        # grp = QGroupBox()
        # grp.setTitle('Whole brain tractogram processing')
        # grp.setLayout(btlayout)

        # Layout

        lyout = self.layout()
        # lyout.addWidget(self._file)
        # lyout.addWidget(grp)
        # noinspection PyUnresolvedReferences
        lyout.addLayout(btlayout)
        lyout.addWidget(self._list)

        margins1 = self.contentsMargins()
        margins2 = lyout.contentsMargins()
        self.setMinimumWidth(self._list.minimumWidth() +
                             margins1.left() + margins1.right() +
                             margins2.left() + margins2.right())

    # Private methods

    def _loadTractogram(self, filename: str) -> None:
        if not self._file.isEmpty():
            wait = DialogWait()
            wait.open()
            wait.setInformationText('Open {}...'.format(basename(filename)))
            QApplication.processEvents()
            sl = SisypheStreamlines.openStreamlines(filename)
            wait.close()
            if sl.isWholeBrainTractogram():
                self._tractogram = sl
                self._file.setToolTip(str(self._tractogram)[:-1])
                self._list.removeAll()
                self._list.setReferenceID(self._tractogram.getReferenceID())
                self._atlas.setVisible(not self._tractogram.isAtlas())
            else:
                messageBox(self,
                           'Open tractogram',
                           text='{} is not a whole brain tractogram.'.format(basename(filename)))
                # < Revision 20/02/2025
                # clear tractogram
                self._file.clear()
                # Revision 20/02/2025 >

    def _clearTractogram(self) -> None:
        self._tractogram = None
        self._list.removeAll()
        self._list.setReferenceID('')

    # Public methods

    def setIconSize(self, size=TabWidget._VSIZE):
        self._list.setIconSize(size)
        self._dissection.setIconSize(QSize(size - 8, size - 8))
        self._dissection.setFixedSize(size, size)
        self._atlas.setIconSize(QSize(size - 8, size - 8))
        self._atlas.setFixedSize(size, size)

    def getIconSize(self):
        return self._list.getIconSize()

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection):
            self._list.setViewCollection(views)
            # self._collection =
        else:
            self._collection = None

    # < Revision 02/11/2024
    # add setMaxCount method
    def setMaxCount(self, v):
        if self._list is not None:
            self._list.setMaxCount(v)
    # Revision 02/11/2024 >

    # < Revision 02/11/2024
    # add getMaxCount method
    def getMaxCount(self):
        if self._list is not None: return self._list.getMaxCount()
        else: raise AttributeError('_list attribute is None.')
    # Revision 02/11/2024 >

    def getTrackingListWidget(self):
        return self._list

    def clear(self):
        self._clearTractogram()

    def hasTractogram(self):
        return self._tractogram is not None

    def getTractogram(self):
        return self._tractogram

    def atlas(self):
        if self.hasTractogram():
            slt = self.getTractogram()
            if not slt.isAtlas():
                self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesAtlasSelection]')
                if self._atlasdialog.exec() == QDialog.Accepted:
                    checked = self._atlasdialog.getAtlasBundlesChecked()
                    n = len(checked)
                    if n > 0:
                        wait = DialogWait()
                        wait.setInformationText('Streamlines atlas selection...')
                        wait.setProgressRange(0, n)
                        wait.setProgressVisibility(n > 1)
                        wait.open()
                        if not slt.isAtlasRegistered():
                            try:
                                wait.addInformationText('Atlas to {} coregistration...'.format(slt.getName()))
                                slt.atlasRegistration()
                                wait.addInformationText('Save {} tractogram...'.format(slt.getName()))
                                slt.save()
                            except Exception as err:
                                messageBox(self,
                                           title='Streamlines atlas selection',
                                           text='Atlas registration error\n{}'.format(err))
                                wait.close()
                                return
                        for name in checked:
                            filename = SisypheStreamlines.getAtlasBundleFilenameFromName(name)
                            if filename is not None and exists(filename):
                                slatlas = SisypheStreamlines()
                                slatlas.load(filename)
                                wait.addInformationText('{} streamlines selection...'.format(name))
                                try:
                                    sl = slt.streamlinesFromAtlas(slatlas,
                                                                  threshold=self._atlasdialog.getClusteringThreshold(),
                                                                  reduction=self._atlasdialog.getReductionThreshold(),
                                                                  pruning=self._atlasdialog.getPruningThreshold(),
                                                                  reductiondist=self._atlasdialog.getReductionMetric(),
                                                                  pruningdist=self._atlasdialog.getPruningMetric(),
                                                                  refine=self._atlasdialog.getRefine(),
                                                                  refinereduction=self._atlasdialog.getRefineReductionThreshold(),
                                                                  refinepruning=self._atlasdialog.getRefineReductionThreshold(),
                                                                  minlength=self._atlasdialog.getMinimalLength(),
                                                                  wait=wait)
                                except Exception as err:
                                    messageBox(self,
                                               title='Streamlines atlas selection',
                                               text='Atlas selection error\n{}'.format(err))
                                    wait.close()
                                    return
                                self._logger.info('Streamlines atlas selection - Tractogram {}'.format(slt.getFilename()))
                                # noinspection PyUnboundLocalVariable
                                self._list.addBundle(sl)
                            wait.incCurrentProgressValue()
                        wait.close()
            else:
                messageBox(self,
                           'Streamlines atlas selection',
                           '{} is an ICBM152 atlas tractogram.')
        else: messageBox(self,
                         'Streamlines atlas selection',
                         'No whole brain tractogram.')

    def dissection(self):
        if self.hasTractogram():
            slt = self.getTractogram()
            rois = None
            if self._list.hasListROIAttributeWidget():
                rois = self._list.getListROIAttributeWidget().getCollection()
                if rois.count() > 0:
                    if rois.getReferenceID() == slt.getReferenceID():
                        names = rois.getName()
                        self._roidialog.addROINames(names)
            self._roidialog.setReferenceID(slt.getReferenceID())
            self._roidialog.setReferenceFOV(slt.getDWIFOV(decimals=1))
            self._roidialog.inPlaceVisibilityOff()
            self._logger.info('Dialog exec [gui.dialogDiffusionBundle.DialogStreamlinesROISelection]')
            if self._roidialog.exec() == QDialog.Accepted:
                wait = DialogWait()
                wait.setInformationText('Streamlines ROI selection...')
                wait.open()
                # Minimal streamline length selection
                l = self._roidialog.getMinimalLength()
                if l > 0.0:
                    wait.addInformationText('Minimal length filtering...')
                    try: slt = slt.getSisypheStreamlinesLongerThan(l=l)
                    except Exception as err:
                        wait.close()
                        messageBox(self,
                                   title='Streamlines ROI selection',
                                   text='Length filtering error\n{}'.format(err))
                        return
                # virtual dissection
                incl = self._roidialog.getInclusionROINames()
                excl = self._roidialog.getExclusionROINames()
                include = list()
                rois2 = SisypheROICollection()
                if len(incl) > 0:
                    for name in incl:
                        if rois is not None and name in rois:
                            rois2.append(rois[name])
                            include.append(True)
                        elif exists(name):
                            roi = SisypheROI()
                            roi.load(name)
                            rois2.append(roi)
                            include.append(True)
                if len(excl) > 0:
                    for name in excl:
                        if rois is not None and name in rois:
                            rois2.append(rois[name])
                            include.append(False)
                        elif exists(name):
                            roi = SisypheROI()
                            roi.load(name)
                            rois2.append(roi)
                            include.append(False)
                if len(rois2) > 0:
                    wait.addInformationText('Streamlines ROI inclusion/exclusion...')
                    mode = self._roidialog.getSelectionMode()
                    try: sl = slt.streamlinesRoiSelection(rois2, include, mode, None, wait)
                    except Exception as err:
                        wait.close()
                        messageBox(self,
                                   title='Streamlines ROI inclusion/exclusion',
                                   text='Streamlines ROI selection error\n{}'.format(err))
                        return
                    sl.setName(self._roidialog.getBundleName())
                    if sl.count() > 0:
                        self._logger.info('Streamlines ROI selection - Tractogram {}'.format(slt.getFilename()))
                        self._list.addBundle(sl)
                    else: messageBox(self,
                                     'Streamlines ROI selection',
                                     'All streamlines removed, bundle is empty.')
                wait.close()
        else: messageBox(self,
                         'Streamlines ROI selection',
                         'No whole brain tractogram.')

    # < Revision 20/02/2025
    # add setEnabled method
    def setEnabled(self, v: bool) -> None:
        super().setEnabled(v)
        self._list.setEnabled(v)
    # Revision 20/02/2025 >

    # Method aliases

    getTrackingCollection = TabWidget.getCollection
    hasTrackingCollection = TabWidget.hasCollection


class TabHelpWidget(QWidget):
    """
    Description
    ~~~~~~~~~~~

    QTabBar page widget to display TabHelpWidget.

    Inheritance
    ~~~~~~~~~~~

    QWidget -> TabHelpWidget

    Last revision: 07/03/2025
    """

    # Class method

    @classmethod
    def getHome(cls):
        import Sisyphe.doc
        # < Revision 07/03/2025
        # return QUrl('file:' + join(dirname(abspath(Sisyphe.doc.__file__)), 'home.html'))
        return QUrl.fromLocalFile(join(dirname(abspath(Sisyphe.doc.__file__)), 'home.html'))
        # < Revision 07/03/2025

    @classmethod
    def getSearch(cls):
        import Sisyphe.doc
        # < Revision 07/03/2025
        # return QUrl('file:' + join(dirname(abspath(Sisyphe.doc.__file__)), 'search.html'))
        return QUrl.fromLocalFile(join(dirname(abspath(Sisyphe.doc.__file__)), 'search.html'))
        # < Revision 07/03/2025

    # Special method

    def __init__(self, parent=None):
        super().__init__(parent)

        # Widgets

        self._home = IconPushButton('home.png', size=TabWidget.getDefaultIconSize())
        self._home.setEnabled(True)
        # noinspection PyUnresolvedReferences
        self._home.clicked.connect(self.home)

        self._back = IconPushButton('backward.png', size=TabWidget.getDefaultIconSize())
        self._back.setEnabled(True)
        # noinspection PyUnresolvedReferences
        self._back.clicked.connect(self.backward)

        self._for = IconPushButton('forward.png', size=TabWidget.getDefaultIconSize())
        self._for.setEnabled(True)
        # noinspection PyUnresolvedReferences
        self._for.clicked.connect(self.forward)

        self._search = LabeledLineEdit('Search')
        self._search.returnPressed.connect(self.search)

        self._web = QWebEngineView()
        self._web.setUrl(self.getHome())
        # noinspection PyTypeChecker
        self._web.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # < Revision 07/03/2025
        # self._web.setZoomFactor(0.8)
        if platform == 'darwin': self._web.setZoomFactor(0.8)
        else: self._web.setZoomFactor(1.0)
        # Revision 07/03/2025 >
        dlyout = QHBoxLayout()
        dlyout.setContentsMargins(0, 0, 0, 0)
        dlyout.addWidget(self._web)

        # Layout

        btlyout = QHBoxLayout()
        btlyout.setContentsMargins(0, 0, 0, 0)
        btlyout.setSizeConstraint(QHBoxLayout.SetMinimumSize)
        btlyout.setSpacing(5)
        btlyout.addWidget(self._home)
        btlyout.addWidget(self._back)
        btlyout.addWidget(self._for)
        btlyout.addWidget(self._search)

        lyout = QVBoxLayout()
        if platform == 'darwin': lyout.setContentsMargins(0, 0, 10, 0)
        else: lyout.setContentsMargins(0, 0, 0, 0)
        lyout.setSpacing(5)
        lyout.addLayout(btlyout)
        lyout.addLayout(dlyout)
        self.setLayout(lyout)

    # Public method

    def setIconSize(self, size=TabWidget.getDefaultIconSize()):
        self._home.setIconSize(QSize(size - 8, size - 8))
        self._back.setIconSize(QSize(size - 8, size - 8))
        self._for.setIconSize(QSize(size - 8, size - 8))
        self._home.setFixedSize(size, size)
        self._back.setFixedSize(size, size)
        self._for.setFixedSize(size, size)

    def getIconSize(self):
        return self._home.width()

    def backward(self):
        self._web.page().triggerAction(QWebEnginePage.WebAction.Back)

    def forward(self):
        self._web.page().triggerAction(QWebEnginePage.WebAction.Forward)

    def home(self):
        self._web.setUrl(self.getHome())

    def search(self):
        filt = 'q={}'.format(self._search.getEditText())
        url = self.getSearch()
        url.setQuery(filt)
        self._web.setUrl(url)

    def setSearch(self, txt):
        self._search.setEditText(txt)
        self.search()

    def setZoomFactor(self, v):
        self._web.setZoomFactor(v)

    def getZoomFactor(self):
        return self._web.zoomFactor()
