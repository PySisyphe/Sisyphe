"""
    External packages/modules

        Name            Link                                                        Usage

        PyQt5           https://www.riverbankcomputing.com/software/pyqt/           Qt GUI
"""

from PyQt5.QtCore import Qt
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QMenu
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QButtonGroup
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QAction
from PyQt5.QtWidgets import QWidgetAction
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtWidgets import QApplication

from Sisyphe.widgets.basicWidgets import IconPushButton
from Sisyphe.widgets.basicWidgets import LabeledSlider
from Sisyphe.widgets.basicWidgets import LabeledSpinBox
from Sisyphe.widgets.basicWidgets import LabeledDoubleSpinBox
from Sisyphe.widgets.basicWidgets import LabeledComboBox
from Sisyphe.widgets.iconBarViewWidgets import IconBarViewWidgetCollection
from Sisyphe.widgets.iconBarViewWidgets import IconBarMultiSliceGridViewWidget
from Sisyphe.widgets.iconBarViewWidgets import IconBarSynchronisedGridViewWidget
from Sisyphe.widgets.attributesWidgets import ListROIAttributesWidget
from Sisyphe.widgets.attributesWidgets import ListMeshAttributesWidget
from Sisyphe.widgets.attributesWidgets import ListToolAttributesWidget
from Sisyphe.widgets.thresholdWidgets import ThresholdViewWidget
from Sisyphe.widgets.functionsSettingsWidget import SettingsWidget
from Sisyphe.gui.dialogROIStatistics import DialogROIStatistics
from Sisyphe.gui.dialogWait import DialogWait

__all__ = ['TabROIListWidget',
           'TabROIToolsWidget',
           'TabMeshListWidget',
           'TabTargetListWidget']

"""
    Class hierarchy

        QWidget -> TabWidget -> TabROIListWidget
                             -> TabROIToolsWidget
                             -> TabMeshListWidget
                             -> TabTargetListWidget
"""


class TabWidget(QWidget):
    """
        TabWidget class

        Description

            Base class for all specialized TabWidgets (ROI, Mesh, Target)

        Inheritance

            QWidget -> TabWidget

        Private Attributes

            _views      IconBarViewWidgetCollection

        Public methods

            setViewCollection(IconBarViewWidgetCollection)
            IconBarViewWidgetCollection = getViewCollection()
            bool = hasCollection()
            dynamic collection type = getCollection()
            bool = hasCollection()

            inherited QWidget methods
    """
    _VSIZE = 32

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(parent)

        self._views = views
        self._collection = None

        # Layout

        lyout = QVBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
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
        TabROIListWidget class

        Description

        Inheritance

            QWidget -> TabROIListWidget

        Private Attributes

            _draw       SisypheROIDraw
            _list       ListROIAttributesWidget
            _collection SisypheROICollection

        Public methods

            setIconSize(int)
            int = getIconSize()
            setViewCollection(IconBarViewWidgetCollection)  override
            getROIListWidget                                ListROIAttributesWidget
            union(list of SisypheROI)
            intersection(list of SisypheROI)
            symmetricDifference(list of SisypheROI)
            difference(list of SisypheROI)
            clear()

            inherited TabWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._draw = None
        self._list = ListROIAttributesWidget(parent=self)

        # GroupBox

        self._btunion = IconPushButton('union.png', size=TabWidget._VSIZE)
        self._btinter = IconPushButton('intersection.png', size=TabWidget._VSIZE)
        self._btsymdiff = IconPushButton('diffirencesym.png', size=TabWidget._VSIZE)
        self._btdiff = IconPushButton('difference.png', size=TabWidget._VSIZE)

        self._btunion.clicked.connect(self.union)
        self._btinter.clicked.connect(self.intersection)
        self._btsymdiff.clicked.connect(self.symmetricDifference)
        self._btdiff.clicked.connect(self.difference)

        self._btunion.setToolTip('Selected and checked ROI union (OR)')
        self._btinter.setToolTip('Selected and checked ROI intersection (AND)')
        self._btsymdiff.setToolTip('Selected and checked ROI symmetric difference (XOR)')
        self._btdiff.setToolTip('Selected ROI - Checked ROI union (NAND)')

        groupbox = QGroupBox('Set operators')
        grouplyout = QHBoxLayout()
        grouplyout.setContentsMargins(5, 0, 5, 0)
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

    def getROIListWidget(self):
        return self._list

    def union(self):
        if self.hasViewCollection():
            if self.hasCollection():
                if self._draw.hasROI():
                    if self._collection.count() > 1:
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'Union {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait(info='Union...', parent=self)
                                wait.open()
                                self._draw.binaryOR(rois)
                                self._updateROIDisplay()
                                wait.close()
                            else: QMessageBox.warning(self, 'ROI Union', 'Less than two ROI checked.')

    def intersection(self):
        if self.hasViewCollection():
            if self.hasCollection():
                if self._draw.hasROI():
                    if self._collection.count() > 1:
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'Intersection {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait(info='Intersection...', parent=self)
                                wait.open()
                                self._draw.binaryAND(rois)
                                self._updateROIDisplay()
                                wait.close()
                            else: QMessageBox.warning(self, 'ROI Intersection', 'Less than two ROI checked.')

    def symmetricDifference(self):
        if self.hasViewCollection():
            if self.hasCollection():
                if self._draw.hasROI():
                    if self._collection.count() > 1:
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            n = len(rois)
                            if n > 1:
                                name = 'SymmDiff {}'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait(info='Symmetric difference...', parent=self)
                                wait.open()
                                self._draw.binaryXOR(rois)
                                self._updateROIDisplay()
                                wait.close()
                            else: QMessageBox.warning(self, 'ROI Symmetric difference', 'Less than two ROI checked.')

    def difference(self):
        if self.hasViewCollection():
            if self.hasCollection():
                if self._draw.hasROI():
                    if self._collection.count() > 1:
                        rois = self._list.getCheckedROI()
                        if rois is not None:
                            rois.insert(0, self._draw.getROI())
                            n = len(rois)
                            if n > 0:
                                name = '{} Diff'.format(rois[0].getName())
                                for i in range(1, n): name += ' {}'.format(rois[i].getName())
                                self._list.new(name)
                                wait = DialogWait(info='Difference...', parent=self)
                                wait.open()
                                self._draw.binaryNAND(rois)
                                self._updateROIDisplay()
                                wait.close()
                            else: QMessageBox.warning(self, 'ROI Difference', 'Less than one ROI checked.')

    def clear(self):
        self._list.removeAll()

    # Method aliases

    getROICollection = TabWidget.getCollection
    hasROICollection = TabWidget.hasCollection


class TabROIToolsWidget(TabWidget):
    """
        TabROIToolsWidget class

        Description

        Inheritance

            QWidget -> TabROIToolsWidget

        Private Attributes

            _draw           IconBarViewWidgetCollection
            _collection     SisypheROICollection
            _threshold      ThresholdViewWidget
            _athreshold     QAction ThresholdViewWidget
            _statistics     DialogROIStatistics
            _btn            dict of IconPushButton
            _btngroup       QButtonGroup of _btn IconPushButton


        Public methods

            setIconSize(int)
            int = getIconSize()
            setEnabled(bool)
            setViewCollection(IconBarViewWidgetCollection)  override
            brush()
            interpolate()
            undo()
            redo()
            slcDilate()
            slcErode()
            slcOpening()
            slcClosing()
            slcInvert()
            slcHoles()
            slcFill()
            slcObject()
            slcBack()
            slcThresholding()
            slcCopy()
            slcCut()
            slcPaste()
            slcClear()
            slcHFlip()
            slcVFlip()
            slcUp()
            slcDown()
            slcRight()
            slcLeft()
            slcFilterExtent()
            slcRegionGrowing()
            slcRegionConfidence()
            slcBlobDilate()
            slcBlobErode()
            slcBlobOpening()
            slcBlobClosing()
            slcBlobCopy()
            slcBlobCut()
            slcBlobPaste()
            slcBlobRemove()
            slcBlobKeep()
            slcBlobThresholding()
            slcBlobRegionGrowing()
            slcBlobRegionConfidence()
            voiEuclideanExpand()
            voiEuclideanShrink()
            voiDilate()
            voiErode()
            voiOpening()
            voiClosing()
            voiInvert()
            voiHoles()
            voiFill()
            voiObject()
            voiBack()
            voiThresholding()
            voiClear()
            voiHFlip()
            voiVFlip()
            voiUp()
            voiDown()
            voiRight()
            voiLeft()
            voiFilterExtent()
            voiRegionGrowing()
            voiRegionConfidence()
            voiActiveContour()
            voiStatistics()
            voiBlobDilate()
            voiBlobErode()
            voiBlobOpening()
            voiBlobClosing()
            voiBlobCopy()
            voiBlobCut()
            voiBlobPaste()
            voiBlobRemove()
            voiBlobKeep()
            voiBlobExpand()
            voiBlobShrink()
            voiBlobThresholding()
            voiBlobRegionGrowing()
            voiBlobRegionConfidence()

            inherited TabWidget methods
            inherited QWidget methods

        Revision:

            12/08/2023  add interpolate() method
            11/11/2023  slcObject, slcBack, voiObject, voiBack methods bugfix
                        slcFilterExtent and voiFilterExtent bugfix
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._draw = None
        self._threshold = None
        self._athreshold = None
        self._statistics = None
        self._btn = dict()
        self._btngroup = QButtonGroup()
        self._btngroup.setExclusive(True)

        # QWidgets settings

        self._brushtype = LabeledComboBox(title='Shape', fontsize=10)
        self._brushtype.addItem('Full disk')
        self._brushtype.addItem('Thresholded disk')
        self._brushtype.addItem('Full ball')
        self._brushtype.addItem('Thresholded ball')
        self._brushtype.currentIndexChanged.connect(self._brushTypeChanged)
        self._brushtype.setToolTip('Brush shape and behavior.')

        self._brushsize = LabeledSlider(Qt.Horizontal, title='Radius', fontsize=10)
        self._brushsize.setMaximum(20)
        self._brushsize.setMinimum(1)
        self._brushsize.setValue(10)
        self._brushsize.valueChanged.connect(self._brushSizeChanged)
        self._brushsize.sliderMoved.connect(self._brushSizeMoved)
        self._brushsize.sliderReleased.connect(self._brushSizeReleased)
        self._brushsize.setToolTip('Brush radius (voxel unit)')

        self._fill = QCheckBox('Fill holes')
        self._fill.setStyleSheet('font-family: Arial; font-size: 10pt')
        self._fill.setChecked(False)
        self._fill.stateChanged.connect(self._brushFillChanged)
        self._fill.setToolTip('Automatic hole filling during drawing.')

        self._structsize = LabeledSlider(Qt.Horizontal, title='Radius', fontsize=10)
        self._structsize.setMinimum(1)
        self._structsize.setMaximum(10)
        self._structsize.setValue(1)
        self._structsize.valueChanged.connect(self._structSizeChanged)
        self._structsize.setToolTip('Structuring element radius used by\nmorphological tools (voxel unit).')

        self._structtype = LabeledComboBox(title='Struct. element type', fontsize=10)
        self._structtype.addItem('Ball')
        self._structtype.addItem('Box')
        self._structtype.addItem('Cross')
        self._structtype.addItem('Annulus')
        self._structtype.currentIndexChanged.connect(self._structTypeChanged)
        self._structtype.setToolTip('Structuring element used by morphological tools.')

        self._move = LabeledSpinBox(title='Move step', fontsize=10)
        self._move.setMinimum(1)
        self._move.setMaximum(20)
        self._move.setValue(1)
        self._move.setSuffix(' voxel(s)')
        self._move.setToolTip('ROI displacement, in voxels, after clicking move tools.')

        self._extent = LabeledSpinBox(title='Blob extent', fontsize=10)
        self._extent.setMinimum(-1)
        self._extent.setMaximum(65536)
        self._extent.setValue(0)
        self._extent.setSuffix(' voxel(s)')
        self._extent.setToolTip('Value used as threshold to remove blobs\n'
                                'with lesser number of voxels.\n'
                                'Only main blob is kept if value is -1.')

        self._thick = LabeledDoubleSpinBox(title='Thickness', fontsize=10)
        self._thick.setMinimum(0.0)
        self._thick.setMaximum(50.0)
        self._thick.setValue(1.0)
        self._thick.setSuffix(' mm')
        self._thick.valueChanged.connect(self._thicknessChanged)
        self._thick.setToolTip('Value in mm used by expand/shrink tools.')

        self._algo = LabeledComboBox(title='Obj./Back. algorithm', fontsize=10)
        self._algo.addItem('Huang')
        self._algo.addItem('Intermodes')
        self._algo.addItem('Isodata')
        self._algo.addItem('Otsu')
        self._algo.addItem('Kittler')
        self._algo.addItem('Li')
        self._algo.addItem('Maximum Entropy')
        self._algo.addItem('Mean')
        self._algo.addItem('Moments')
        self._algo.addItem('Renyi')
        self._algo.addItem('Shanbhag')
        self._algo.addItem('Triangle')
        self._algo.addItem('Yen')
        self._algo.addItem('Morphology')
        self._algo.setCurrentIndex(3)
        self._algo.setToolTip('Algorithm used for object/background segmentation tools.')

        self._confidence = LabeledDoubleSpinBox(title='Conf. connected', fontsize=10)
        self._confidence.setMinimum(1.0)
        self._confidence.setMaximum(5.0)
        self._confidence.setSingleStep(0.1)
        self._confidence.setValue(2.5)
        self._confidence.setSuffix(' sigma')
        self._confidence.setToolTip('Parameter used by confidence connected segmentation tools.')

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

        # Popup menu

        self._menuThreshold = QMenu(self)
        self._menuThreshold.aboutToShow.connect(self._showThresholdMenu)
        self._menuThreshold.aboutToHide.connect(self._hideThresholdMenu)
        self._btn['threshold'].setMenu(self._menuThreshold)

        self._menu2DRegion = QMenu()
        self._menu2DRegion.setStyleSheet('font-family: Arial; font-size: 12pt')
        action = self._menu2DRegion.addAction('Region growing')
        action.triggered.connect(self.slcRegionGrowing)
        action = self._menu2DRegion.addAction('Confidence connected')
        action.triggered.connect(self.slcRegionConfidence)
        self._btn['2Dregion'].setMenu(self._menu2DRegion)

        self._menu2DBlobRegion = QMenu()
        self._menu2DBlobRegion.setStyleSheet('font-family: Arial; font-size: 12pt')
        action = self._menu2DBlobRegion.addAction('Region growing')
        action.triggered.connect(self.slcBlobRegionGrowing)
        action = self._menu2DBlobRegion.addAction('Confidence connected')
        action.triggered.connect(self.slcBlobRegionConfidence)
        self._btn['2Dblobregion'].setMenu(self._menu2DBlobRegion)

        self._menu3DRegion = QMenu()
        self._menu3DRegion.setStyleSheet('font-family: Arial; font-size: 12pt')
        action = self._menu3DRegion.addAction('Region growing')
        action.triggered.connect(self.voiRegionGrowing)
        action = self._menu3DRegion.addAction('Confidence connected')
        action.triggered.connect(self.voiRegionConfidence)
        action = self._menu3DRegion.addAction('Active contour')
        action.triggered.connect(self.voiActiveContour)
        self._btn['3Dregion'].setMenu(self._menu3DRegion)

        self._menu3DBlobRegion = QMenu()
        self._menu3DBlobRegion.setStyleSheet('font-family: Arial; font-size: 12pt')
        action = self._menu3DBlobRegion.addAction('Region growing')
        action.triggered.connect(self.voiBlobRegionGrowing)
        action = self._menu3DBlobRegion.addAction('Confidence connected')
        action.triggered.connect(self.voiBlobRegionConfidence)
        self._btn['3Dblobregion'].setMenu(self._menu3DBlobRegion)

        self._menu3DHoles = QMenu()
        self._menu3DHoles.setStyleSheet('font-family: Arial; font-size: 12pt')
        action = self._menu3DHoles.addAction('3D fill holes')
        action.triggered.connect(self.voi3DHoles)
        action = self._menu3DHoles.addAction('2D axial fill holes')
        action.triggered.connect(lambda: self.voi2DHoles(0))
        action = self._menu3DHoles.addAction('2D coronal fill holes')
        action.triggered.connect(lambda: self.voi2DHoles(1))
        action = self._menu3DHoles.addAction('2D sagittal fill holes')
        action.triggered.connect(lambda: self.voi2DHoles(2))
        self._btn['3Dholes'].setMenu(self._menu3DHoles)

        # Layout

        lyout = self.layout()
        lyout.addStretch()
        lyout.addWidget(self._brushgroupbox)
        lyout.addWidget(self._slicegroupbox)
        lyout.addWidget(self._sliceblobgroupbox)
        lyout.addWidget(self._volumegroupbox)
        lyout.addWidget(self._volumeblobgroupbox)
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
        vlyout.setContentsMargins(0, 0, 0, 0)
        lyout = QHBoxLayout()
        lyout.setContentsMargins(5, 0, 5, 0)
        lyout.setSpacing(5)
        lyout.addStretch()
        lyout.addWidget(self._brushtype)
        lyout.addWidget(self._brushsize)
        lyout.addWidget(self._fill)
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
        self._btn['2Dfill'].setToolTip('Fill from seed pixel')
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
        lyout.addWidget(self._structtype)
        lyout.addWidget(self._structsize)
        lyout.addStretch()
        vlyout.addLayout(lyout)
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
        lyout.addWidget(self._algo)
        lyout.addWidget(self._confidence)
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
        lyout.addWidget(self._move)
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
        self._btn['2Dblobthreshold'].setToolTip('Thresholding in blob, current slice')
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
        lyout.addWidget(self._extent)
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
        self._btn['3Dfill'].setToolTip('Fill from seed voxel')
        self._btn['3Dexpand'].setToolTip('Euclidean distance expand')
        self._btn['3Dshrink'].setToolTip('Euclidean distance shrink')
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
        # self._btn['3Dholes'].pressed.connect(self.voi3DHoles)
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
        lyout.addWidget(self._thick)
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
        self._btn['3Dblobexpand'].setToolTip('Euclidean distance blob expand')
        self._btn['3Dblobshrink'].setToolTip('Euclidean distance blob shrink')
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

    def _showThresholdMenu(self):
        if self._views is not None:
            vol = self._views.getVolume()
            if vol is not None:
                if self._athreshold is not None:
                    self._menuThreshold.removeAction(self._athreshold)
                self._threshold = ThresholdViewWidget(vol, size=384)
                if self._draw is not None:
                    self._threshold.setThreshold(self._draw.getThresholdMin(), self._draw.getThresholdMax())
                self._athreshold = QWidgetAction(self)
                self._athreshold.setDefaultWidget(self._threshold)
                self._menuThreshold.addAction(self._athreshold)

    def _hideThresholdMenu(self):
        if self._draw is not None:
            self._draw.setThresholds(self._threshold.getMinThreshold(), self._threshold.getMaxThreshold())
            self._threshold = None

    def _brushSizeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._views.setBrushRadiusROI(self._brushsize.value())

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

    def _brushTypeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            brush = ('solid', 'threshold', 'solid3', 'threshold3')
            index = self._brushtype.currentIndex()
            self._draw.setBrushType(brush[index])

    def _brushFillChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._views.setFillHolesROIFlag(self._fill.isChecked())

    def _structSizeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setMorphologyRadius(self._structsize.value())

    def _structTypeChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            struct = ('ball', 'box', 'cross', 'annulus')
            index = self._structtype.currentIndex()
            self._draw.setStructElement(struct[index])

    def _thicknessChanged(self, v):
        if self._draw is not None and self.hasViewCollection():
            self._draw.setThickness(self._thick.value())

    # Public methods

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

    # Public tools methods

    def brush(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._views.getBrushFlag() > 0:
                self._btn['dummy'].setChecked(True)
                self._views.setNoROIFlag()
            else: self._views.setBrushROIFlag(self._brushtype.currentIndex())

    def interpolate(self):  # to do
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

    def undo(self):
        if self._draw:
            self._draw.popUndoLIFO()
            self._updateROIDisplay()

    def redo(self):
        if self._draw:
            self._draw.popRedoLIFO()
            self._updateROIDisplay()

    # Slice ROI actions

    def slcDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceDilate(index, orient)
                    self._updateROIDisplay()

    def slcErode(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceErode(index, orient)
                    self._updateROIDisplay()

    def slcOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceOpening(index, orient)
                    self._updateROIDisplay()

    def slcClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.morphoSliceClosing(index, orient)
                    self._updateROIDisplay()

    def slcInvert(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.binaryNotSlice(index, orient)
                    self._updateROIDisplay()

    def slcHoles(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.fillHolesSlice(index, orient)
                    self._updateROIDisplay()

    def slcFill(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DFillROIFlag()

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

    def slcThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.thresholdingSlice(index, orient)
                    self._updateROIDisplay()

    def slcCopy(self):
        if self._draw is not None:
            index = self._views.getSelectedSliceIndex()
            if index is not None:
                orient = self._views.getCurrentOrientation()
                self._draw.copySlice(index, orient)
                self._updateROIDisplay()

    def slcCut(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.cutSlice(index, orient)
                    self._updateROIDisplay()

    def slcPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.pasteSlice(index, orient)
                    self._updateROIDisplay()

    def slcClear(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.clearSlice(index, orient)
                    self._updateROIDisplay()

    def slcHFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.flipSlice(index, orient, True, False)
                    self._updateROIDisplay()

    def slcVFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.flipSlice(index, orient, False, True)
                    self._updateROIDisplay()

    def slcUp(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, 0, self._move.value())
                    self._updateROIDisplay()

    def slcDown(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, 0, -self._move.value())
                    self._updateROIDisplay()

    def slcLeft(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, self._move.value(), 0)
                    self._updateROIDisplay()

    def slcRight(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    self._draw.shiftSlice(index, orient, -self._move.value(), 0)
                    self._updateROIDisplay()

    def slcFilterExtent(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                index = self._views.getSelectedSliceIndex()
                if index is not None:
                    orient = self._views.getCurrentOrientation()
                    if self._extent.value() == -1: self._draw.majorBlobSelectSlice(index, orient)
                    else: self._draw.blobFilterExtentSlice(index, orient, self._extent.value())
                    self._updateROIDisplay()

    def slcRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['2Dregion'].setChecked(True)
            self._views.set2DRegionGrowingROIFlag()

    def slcRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['2Dregion'].setChecked(True)
            self._views.set2DRegionConfidenceROIFlag()

    # Slice blob actions

    def slcBlobDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobDilateROIFlag()

    def slcBlobErode(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobErodeROIFlag()

    def slcBlobOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobOpenROIFlag()

    def slcBlobClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCloseROIFlag()

    def slcBlobCopy(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCopyROIFlag()

    def slcBlobCut(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobCutROIFlag()

    def slcBlobPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobPasteROIFlag()

    def slcBlobRemove(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobRemoveROIFlag()

    def slcBlobKeep(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobKeepROIFlag()

    def slcBlobThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set2DBlobThresholdROIFlag()

    def slcBlobRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['2Dblobregion'].setChecked(True)
            self._views.set2DBlobRegionGrowingROIFlag()

    def slcBlobRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['2Dblobregion'].setChecked(True)
            self._views.set2DBlobRegionConfidenceROIFlag()

    # Volume ROI actions

    def voiEuclideanExpand(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if self._thick.value() > 0.0:
                    wait = DialogWait(info='Euclidean expand...', parent=self)
                    wait.open()
                    QApplication.processEvents()
                    self._draw.euclideanDilate(self._thick.value())
                    self._updateROIDisplay()
                    wait.close()

    def voiEuclideanShrink(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if self._thick.value() > 0.0:
                    wait = DialogWait(info='Euclidean shrink...', parent=self)
                    wait.open()
                    QApplication.processEvents()
                    self._draw.euclideanErode(self._thick.value())
                    self._updateROIDisplay()
                    wait.close()

    def voiDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Morphology dilate...', parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.morphoDilate()
                self._updateROIDisplay()
                wait.close()

    def voiErode(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Morphology erode...', parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.morphoErode()
                self._updateROIDisplay()
                wait.close()

    def voiOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Morphology opening...', parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.morphoOpening()
                self._updateROIDisplay()
                wait.close()

    def voiClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Morphology closing...', parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.morphoClosing()
                self._updateROIDisplay()
                wait.close()

    def voiInvert(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                self._draw.binaryNOT()
                self._updateROIDisplay()

    def voi3DHoles(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Fill holes...', parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.fillHoles()
                self._updateROIDisplay()
                wait.close()

    def voi2DHoles(self, dim):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                if dim == 0: info = '2D axial fill holes...'
                elif dim == 1: info = '2D coronal fill holes...'
                else: info = '2D sagittal fill holes...'
                wait = DialogWait(info=info, parent=self)
                wait.open()
                QApplication.processEvents()
                self._draw.fillHolesAllSlices(dim)
                self._updateROIDisplay()
                wait.close()

    def voiFill(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DFillROIFlag()

    def voiClear(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                self._draw.clear()
                self._updateROIDisplay()

    def voiObject(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Object segmentation...', parent=self)
                wait.open()
                QApplication.processEvents()
                algo = self._algo.currentText().lower()
                algo = algo.replace(' ', '')
                if algo == 'morphology': self._draw.maskSegment2('huang')
                else: self._draw.objectSegment(algo)
                self._updateROIDisplay()
                wait.close()

    def voiBack(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Background segmentation...', parent=self)
                wait.open()
                QApplication.processEvents()
                algo = self._algo.currentText().lower()
                algo = algo.replace(' ', '')
                if algo == 'morphology': self._draw.notMaskSegment2('huang')
                else: self._draw.backgroundSegment(algo)
                self._updateROIDisplay()
                wait.close()

    def voiThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Thresholding...', parent=self)
                wait.open()
                self._draw.thresholding()
                self._updateROIDisplay()
                wait.close()

    def voiHFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.flip(True, False, False)
                elif orient == 1: self._draw.flip(True, False, False)
                else: self._draw.flip(False, True, False)
                self._updateROIDisplay()

    def voiVFlip(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.flip(False, True, False)
                elif orient == 1: self._draw.flip(False, False, True)
                else: self._draw.flip(False, False, True)
                self._updateROIDisplay()

    def voiUp(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(0, self._move.value(), 0)
                elif orient == 1: self._draw.shift(0, 0, self._move.value())
                else: self._draw.shif(0, 0, self._move.value())
                self._updateROIDisplay()

    def voiDown(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(0, -self._move.value(), 0)
                elif orient == 1: self._draw.shift(0, 0, -self._move.value())
                else: self._draw.shif(0, 0, -self._move.value())
                self._updateROIDisplay()

    def voiLeft(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(self._move.value(), 0, 0)
                elif orient == 1: self._draw.shift(self._move.value(), 0, 0)
                else: self._draw.shif(0, self._move.value(), 0)
                self._updateROIDisplay()

    def voiRight(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                orient = self._views.getCurrentOrientation()
                if orient == 0: self._draw.shift(-self._move.value(), 0, 0)
                elif orient == 1: self._draw.shift(-self._move.value(), 0, 0)
                else: self._draw.shif(0, -self._move.value(), 0)
                self._updateROIDisplay()

    def voiFilterExtent(self):
        if self.hasViewCollection() and self.hasCollection():
            if self._draw is not None:
                wait = DialogWait(info='Blob filter extent...', parent=self)
                wait.open()
                QApplication.processEvents()
                if self._extent.value() == -1: self._draw.majorBlobSelect()
                else: self._draw.blobFilterExtent(self._extent.value())
                self._updateROIDisplay()
                wait.close()

    def voiRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['3Dregion'].setChecked(True)
            self._views.set3DRegionGrowingROIFlag()

    def voiRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['3Dregion'].setChecked(True)
            self._views.set3DRegionConfidenceROIFlag()

    def voiActiveContour(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['3Dregion'].setChecked(True)
            self._views.setActiveContourROIFlag()

    def statistics(self):
        if self.hasViewCollection() and self.hasCollection():
            self._statistics = DialogROIStatistics()
            self._statistics.setVolume(self._views.getVolume())
            self._statistics.setROICollection(self._collection)
            self._statistics.show()

    # Volume blob actions

    def voiBlobDilate(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobDilateROIFlag()

    def voiBlobErode(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobErodeROIFlag()

    def voiBlobOpening(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobOpenROIFlag()

    def voiBlobClosing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCloseROIFlag()

    def voiBlobCopy(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCopyROIFlag()

    def voiBlobCut(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobCutROIFlag()

    def voiBlobPaste(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobPasteROIFlag()

    def voiBlobRemove(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobRemoveROIFlag()

    def voiBlobKeep(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobKeepROIFlag()

    def voiBlobExpand(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobExpandFlagOn(self._thick.value())

    def voiBlobShrink(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobShrinkFlagOn(self._thick.value())

    def voiBlobThresholding(self):
        if self.hasViewCollection() and self.hasCollection():
            self._views.set3DBlobThresholdROIFlag()

    def voiBlobRegionGrowing(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['3Dblobregion'].setChecked(True)
            self._views.set3DBlobRegionGrowingROIFlag()

    def voiBlobRegionConfidence(self):
        if self.hasViewCollection() and self.hasCollection():
            self._btn['3Dblobregion'].setChecked(True)
            self._views.set3DBlobRegionConfidenceROIFlag()

    # Method aliases

    getROICollection = TabWidget.getCollection
    hasROICollection = TabWidget.hasCollection


class TabMeshListWidget(TabWidget):
    """
        TabMeshListWidget class

        Description

        Inheritance

            QWidget -> TabMeshListWidget

        Private Attributes

            _list       ListMeshAttributesWidget
            _collection SisypheMeshCollection

        Public methods

            setViewCollection(IconBarViewWidgetCollection)  override
            getMeshListWidget()                             ListMeshAttributesWidget
            clear()

            inherited TabWidget methods
            inherited QWidget methods
    """

    # Special method

    def __init__(self, views=None, parent=None):
        super().__init__(views, parent)

        self._list = ListMeshAttributesWidget(views=views, parent=self)
        self._action = dict()

        # GroupBox

        self._btfilt = IconPushButton('filter.png', size=TabWidget._VSIZE)
        self._dilate = IconPushButton('meshexpand.png', size=TabWidget._VSIZE)
        self._erode = IconPushButton('meshshrink.png', size=TabWidget._VSIZE)
        self._btunion = IconPushButton('union.png', size=TabWidget._VSIZE)
        self._btinter = IconPushButton('intersection.png', size=TabWidget._VSIZE)
        self._btdiff = IconPushButton('difference.png', size=TabWidget._VSIZE)
        self._btfeatures = IconPushButton('cubefeature.png', size=TabWidget._VSIZE)

        self._btfilt.clicked.connect(self.filters)
        self._btunion.clicked.connect(self.union)
        self._btinter.clicked.connect(self.intersection)
        self._btdiff.clicked.connect(self.difference)
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
        grouplyout.setContentsMargins(5, 0, 5, 0)
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
        self._settings.setSettingsButtonText('mesh filter settings')
        self._settings.settingsVisibilityOn()
        self._settings.setFontSize(10)

        self._popupDilate = QMenu()
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
        self._action['dilate'].triggered.connect(self.dilate)
        self._popupDilate.addAction(self._action['dilate'])
        self._dilate.setMenu(self._popupDilate)

        self._popupErode = QMenu()
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

    def getIconSize(self):
        return self._btfilt.width()

    def setViewCollection(self, views):
        super().setViewCollection(views)
        if isinstance(views, IconBarViewWidgetCollection):
            self._list.setViewCollection(views)
            self._collection = views.getMeshCollection()
        else: self._collection = None

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

    # Method aliases

    getMeshCollection = TabWidget.getCollection
    hasMeshCollection = TabWidget.hasCollection


class TabTargetListWidget(TabWidget):
    """
        TabTargetWidget class

        Description

        Inheritance

            QWidget -> TabTargetWidget

        Private Attributes

            _list       ListToolAttributesWidget
            _collection

        Public methods

            setViewCollection(IconBarViewWidgetCollection)  override
            getToolListWidget()                             ListToolAttributesWidget
            clear()

            inherited TabWidget methods
            inherited QWidget methods
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
        pass

    def getIconSize(self):
        pass

    def setViewCollection(self, views):
        super().setViewCollection(views)

        if isinstance(views, IconBarViewWidgetCollection):
            self._list.setViewCollection(views)
            self._collection = views.getMeshCollection()
        else:
            self._collection = None

    def getToolListWidget(self):
        return self._list

    def clear(self):
        self._list.removeAll()

    # Method aliases

    getToolCollection = TabWidget.getCollection
    hasTollCollection = TabWidget.hasCollection
